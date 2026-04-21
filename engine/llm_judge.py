import asyncio
import os
import re
from typing import Dict, Any, List, Tuple
from google import genai
from dotenv import load_dotenv

load_dotenv()

class LLMJudge:
    def __init__(self, model_a: str = "gemini-1.5-flash", model_b: str = "gemini-1.5-pro"):
        """
        Initialize the Multi-Judge Engine with two models for consensus.
        """
        # Using stable model names for reliability
        self.model_a_name = f"models/{model_a}"
        self.model_b_name = f"models/{model_b}"
        
        # Initialize Google GenAI client
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        
        self.rubrics = {
            "accuracy": "Chấm điểm từ 1-5 dựa trên độ chính xác so với Ground Truth. 5: Hoàn hảo, 1: Hoàn toàn sai.",
            "professionalism": "Chấm điểm từ 1-5 dựa trên sự chuyên nghiệp và tone giọng của ngôn ngữ.",
        }
        
        # Pricing per 1M tokens (USD) - Approximate values for Gemini 1.5
        self.pricing = {
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
            "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
        }
        self.total_cost = 0.0

    def _extract_score(self, text: str) -> int:
        """Extracts the first number from 1 to 5 in the text."""
        # Look for a digit 1-5, often models might wrap it in markdown or text
        match = re.search(r'\b[1-5]\b', text)
        if match:
            return int(match.group())
        return 3 # Default to neutral if no clear score found

    async def _get_model_score(self, model_id: str, question: str, answer: str, ground_truth: str) -> Tuple[int, float]:
        """Helper to call LLM and extract a numeric score and track cost."""
        prompt = f"""
        Bạn là một chuyên gia đánh giá AI. Hãy chấm điểm câu trả lời sau đây dựa trên tiêu chí Accuracy.
        
        Câu hỏi: {question}
        Câu trả lời của AI: {answer}
        Ground Truth: {ground_truth}
        
        Tiêu chí chấm điểm: {self.rubrics['accuracy']}
        
        Chỉ trả về duy nhất 1 con số từ 1 đến 5 đại diện cho số điểm. Không giải thích gì thêm.
        """
        
        model_key = model_id.replace("models/", "")
        
        try:
            # Note: The SDK usage might vary, here we assume response has usage_metadata
            response = self.client.models.generate_content(
                model=model_id,
                contents=prompt
            )
            
            score = self._extract_score(response.text.strip())
            
            # Cost Calculation
            cost = 0.0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                in_tokens = usage.prompt_token_count or 0
                out_tokens = usage.candidates_token_count or 0
                
                if model_key in self.pricing:
                    cost = (in_tokens / 1_000_000 * self.pricing[model_key]["input"]) + \
                           (out_tokens / 1_000_000 * self.pricing[model_key]["output"])
            
            return score, cost
            
        except Exception as e:
            print(f"Error calling {model_id}: {e}")
            return 3, 0.0

    async def evaluate_multi_judge(
        self, question: str, answer: str, ground_truth: str
    ) -> Dict[str, Any]:
        """
        Calls 2 models in parallel and calculates consensus.
        """
        tasks = [
            self._get_model_score(self.model_a_name, question, answer, ground_truth),
            self._get_model_score(self.model_b_name, question, answer, ground_truth)
        ]
        
        results = await asyncio.gather(*tasks)
        (score_a, cost_a), (score_b, cost_b) = results
        
        iteration_cost = cost_a + cost_b
        self.total_cost += iteration_cost

        # Consensus Logic
        diff = abs(score_a - score_b)
        
        # If models disagree significantly (diff > 1), we might take the conservative approach or average
        avg_score = (score_a + score_b) / 2
        
        # Agreement rate: 1.0 if identical, 0.75 if diff is 1, 0.0 if diff > 1
        agreement = 1.0 if diff == 0 else (0.75 if diff == 1 else 0.0)
        
        return {
            "final_score": avg_score,
            "agreement_rate": agreement,
            "individual_scores": {
                self.model_a_name: score_a,
                self.model_b_name: score_b,
            },
            "discrepancy": diff,
            "cost": iteration_cost
        }

    def get_total_cost(self) -> float:
        return self.total_cost
