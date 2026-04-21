import asyncio
import os
from typing import Dict, Any, List
from google import genai
from dotenv import load_dotenv

load_dotenv()

class LLMJudge:
    def __init__(self, model_a: str = "gemma-3-27b-it", model_b: str = "gemma-4-31b-it"):
        # Use valid Gemini model names
        self.model_a_name = model_a
        self.model_b_name = model_b
        
        # Initialize Google GenAI client
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("⚠️ WARNING: GOOGLE_API_KEY not found in environment variables.")
        self.client = genai.Client(api_key=api_key)
        
        self.rubrics = {
            "accuracy": "Chấm điểm từ 1-5 dựa trên độ chính xác so với Ground Truth. 5: Hoàn hảo, 1: Hoàn toàn sai.",
            "professionalism": "Chấm điểm từ 1-5 dựa trên sự chuyên nghiệp và tone giọng của ngôn ngữ.",
        }

    async def _get_model_score(self, model: str, question: str, answer: str, ground_truth: str) -> int:
        """Helper to call LLM and extract a numeric score."""
        prompt = f"""
        Bạn là một chuyên gia đánh giá AI. Hãy chấm điểm câu trả lời sau đây dựa trên tiêu chí Accuracy.
        
        Câu hỏi: {question}
        Câu trả lời của AI: {answer}
        Ground Truth: {ground_truth}
        
        Tiêu chí chấm điểm: {self.rubrics['accuracy']}
        
        Chỉ trả về duy nhất 1 con số từ 1 đến 5 đại diện cho số điểm. Không giải thích gì thêm.
        """
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt
            )
            score_str = response.text.strip()
            # Extract first number found
            import re
            match = re.search(r'\d', score_str)
            if match:
                return int(match.group())
            return 3 # Default if failed to parse
        except Exception as e:
            print(f"Error calling {model}: {e}")
            return 3

    async def evaluate_multi_judge(
        self, question: str, answer: str, ground_truth: str
    ) -> Dict[str, Any]:
        """
        EXPERT TASK: Gọi 2 model (Gemini 3.1 and Gemma 4).
        Tính toán sự sai lệch và đồng thuận.
        """
        # Run calls in parallel
        tasks = [
            self._get_model_score(self.model_a_name, question, answer, ground_truth),
            self._get_model_score(self.model_b_name, question, answer, ground_truth)
        ]
        
        scores = await asyncio.gather(*tasks)
        score_a, score_b = scores[0], scores[1]

        avg_score = (score_a + score_b) / 2
        agreement = 1.0 if abs(score_a - score_b) <= 1 else 0.5 # Consensus logic: close enough is agreement

        return {
            "final_score": avg_score,
            "agreement_rate": agreement,
            "individual_scores": {
                self.model_a_name: score_a,
                self.model_b_name: score_b,
            },
        }

    async def check_position_bias(self, response_a: str, response_b: str):
        """
        Nâng cao: Thực hiện đổi chỗ response A và B để xem Judge có thiên vị vị trí không.
        """
        pass
