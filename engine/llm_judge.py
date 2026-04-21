import asyncio
import os
import re
from typing import Dict, Any, List, Tuple
from google import genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMJudge:
    def __init__(self, model_a: str = "gemma-4-31b-it", model_b: str = "gpt-4o"):
        """
        Multi-Judge Engine:
        - Model A: Gemma (Google GenAI) - Fake Pricing
        - Model B: GPT-4o (OpenAI) - Real Pricing
        """
        # Note: Using 'models/' prefix for Google SDK
        self.model_a_name = f"models/{model_a}"
        self.model_b_name = model_b

        # Clients
        self.google_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.rubrics = {
            "accuracy": "Chấm điểm từ 1-5 dựa trên độ chính xác so với Ground Truth. 5: Hoàn hảo, 1: Hoàn toàn sai.",
        }

        # Pricing per 1M tokens (USD)
        self.pricing = {
            "gemma-4-31b-it": {
                "input": 0.1,
                "output": 0.3,
            },  # Fake pricing as requested
            "gpt-4o": {"input": 5.00, "output": 15.00},  # OpenAI pricing
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},  # OpenAI pricing
        }
        self.total_cost = 0.0

    def _extract_score(self, text: str) -> int:
        """Extracts the first number from 1 to 5 in the text."""
        match = re.search(r"\b[1-5]\b", text)
        if match:
            return int(match.group())
        return 3  # Default

    async def _get_google_score(self, model_id: str, prompt: str) -> Tuple[int, float]:
        """Calls Google Model (Gemma) and calculates fake/simulated cost."""
        try:
            # We wrap in a thread because genai client might be sync-only for some versions
            # or we just use it directly if it supports async (here assuming standard usage)
            response = self.google_client.models.generate_content(
                model=model_id, contents=prompt
            )

            score = self._extract_score(response.text.strip())

            # Simulated/Fake Cost Calculation for Gemma
            cost = 0.0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = response.usage_metadata
                model_key = model_id.replace("models/", "")
                if model_key in self.pricing:
                    cost = (
                        usage.prompt_token_count
                        / 1_000_000
                        * self.pricing[model_key]["input"]
                    ) + (
                        usage.candidates_token_count
                        / 1_000_000
                        * self.pricing[model_key]["output"]
                    )

            return score, cost

        except Exception as e:
            print(f"Error calling Google Model ({model_id}): {e}")
            return 3, 0.0

    async def _get_openai_score(self, model_id: str, prompt: str) -> Tuple[int, float]:
        """Calls OpenAI Model (GPT) and calculates real cost."""
        try:
            # Run OpenAI call in a separate thread if using sync client
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                ),
            )

            score = self._extract_score(response.choices[0].message.content)

            # Real Cost Calculation for OpenAI
            usage = response.usage
            cost = 0.0
            if model_id in self.pricing:
                cost = (
                    usage.prompt_tokens / 1_000_000 * self.pricing[model_id]["input"]
                ) + (
                    usage.completion_tokens
                    / 1_000_000
                    * self.pricing[model_id]["output"]
                )

            return score, cost

        except Exception as e:
            print(f"Error calling OpenAI Model ({model_id}): {e}")
            return 3, 0.0

    async def evaluate_multi_judge(
        self, question: str, answer: str, ground_truth: str
    ) -> Dict[str, Any]:
        """
        Consensus between Gemma and GPT.
        """
        prompt = f"""
        Bạn là một chuyên gia đánh giá AI. Hãy chấm điểm câu trả lời sau đây dựa trên tiêu chí Accuracy.
        
        Câu hỏi: {question}
        Câu trả lời của AI: {answer}
        Ground Truth: {ground_truth}
        
        Tiêu chí chấm điểm: {self.rubrics['accuracy']}
        
        Chỉ trả về duy nhất 1 con số từ 1 đến 5 đại diện cho số điểm. Không giải thích gì thêm.
        """

        tasks = [
            self._get_google_score(self.model_a_name, prompt),
            self._get_openai_score(self.model_b_name, prompt),
        ]

        results = await asyncio.gather(*tasks)
        (score_a, cost_a), (score_b, cost_b) = results

        iteration_cost = cost_a + cost_b
        self.total_cost += iteration_cost

        diff = abs(score_a - score_b)
        avg_score = (score_a + score_b) / 2
        agreement = 1.0 if diff <= 1 else 0.0

        return {
            "final_score": avg_score,
            "agreement_rate": agreement,
            "individual_scores": {
                self.model_a_name: score_a,
                self.model_b_name: score_b,
            },
            "cost": iteration_cost,
        }

    def get_total_cost(self) -> float:
        return self.total_cost
