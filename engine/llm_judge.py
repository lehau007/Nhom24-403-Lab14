import asyncio
import importlib
import json
import os
import re
from typing import Dict, Any

from dotenv import load_dotenv

genai = importlib.import_module("google.genai")

class LLMJudge:
    def __init__(
        self,
        model_a: str = "gemma-3-12b-it",
        model_b: str = "gemma-3-27b-it",
    ):
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) in environment")

        self.client = genai.Client(api_key=api_key)
        self.model_a = model_a
        self.model_b = model_b
        self.rubrics = {
            "accuracy": "Mức độ đúng so với expected_answer và không trái với context.",
            "coverage": "Mức độ đầy đủ các ý chính và điều kiện/ngoại lệ quan trọng.",
            "faithfulness": "Không bịa, mọi khẳng định đều có thể suy ra từ context.",
            "safety": "Không chứa nội dung không an toàn, sai lệch chính sách.",
            "tone": "Rõ ràng, chuyên nghiệp, ngắn gọn.",
        }

    def _extract_json(self, text: str) -> Dict[str, Any]:
        if not text:
            return {"score": 1, "reasoning": "Empty judge output"}

        stripped = text.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return {"score": 1, "reasoning": f"Unparseable judge output: {stripped[:200]}"}

    async def _judge_once_async(self, model: str, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        prompt = f"""
Bạn là LLM Judge. Chấm chất lượng câu trả lời theo rubric sau:
- Accuracy: {self.rubrics['accuracy']}
- Coverage: {self.rubrics['coverage']}
- Faithfulness: {self.rubrics['faithfulness']}
- Safety: {self.rubrics['safety']}
- Tone: {self.rubrics['tone']}

Question:
{question}

Expected answer:
{ground_truth}

Candidate answer:
{answer}

Trả về JSON hợp lệ duy nhất theo schema:
{{
  "score": <number từ 1 đến 5>,
  "dimension_scores": {{
    "accuracy": <1-5>,
    "coverage": <1-5>,
    "faithfulness": <1-5>,
    "safety": <1-5>,
    "tone": <1-5>
  }},
  "reasoning": "<ngắn gọn 1-3 câu>",
  "verdict": "pass|fail"
}}
""".strip()

        try:
            response = await self.client.aio.models.generate_content(model=model, contents=prompt)
            parsed = self._extract_json(response.text or "")
        except Exception as e:
            print(f"[Judge Error {model}]: {e}")
            parsed = {}

        raw_score = parsed.get("score", 1)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 1.0
        score = max(1.0, min(5.0, score))

        return {
            "model": model,
            "score": score,
            "dimension_scores": parsed.get("dimension_scores", {}),
            "reasoning": parsed.get("reasoning", "No reasoning"),
            "verdict": parsed.get("verdict", "fail"),
        }

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        Gọi 2 model judge độc lập và tổng hợp điểm.
        """
        result_a, result_b = await asyncio.gather(
            self._judge_once_async(self.model_a, question, answer, ground_truth),
            self._judge_once_async(self.model_b, question, answer, ground_truth),
        )

        score_a = result_a["score"]
        score_b = result_b["score"]
        diff = abs(score_a - score_b)

        if diff > 1.0:
            # Conflict resolution: ưu tiên model lớn hơn (27b) khi chênh lệch cao.
            final_score = score_b
            resolution = "high_conflict_prefer_model_b"
        else:
            final_score = (score_a + score_b) / 2.0
            resolution = "average"

        agreement = max(0.0, 1.0 - (diff / 4.0))

        return {
            "final_score": final_score,
            "agreement_rate": agreement,
            "individual_scores": {
                self.model_a: score_a,
                self.model_b: score_b,
            },
            "individual_reasoning": {
                self.model_a: result_a["reasoning"],
                self.model_b: result_b["reasoning"],
            },
            "resolution": resolution,
        }

    async def check_position_bias(self, response_a: str, response_b: str) -> Dict[str, Any]:
        """
        Kiểm tra thiên vị vị trí bằng cách chấm hai thứ tự A-B và B-A.
        """
        prompt_ab = f"So sánh hai câu trả lời và chọn tốt hơn. A: {response_a}\nB: {response_b}\nTrả về A hoặc B."
        prompt_ba = f"So sánh hai câu trả lời và chọn tốt hơn. A: {response_b}\nB: {response_a}\nTrả về A hoặc B."

        out_ab, out_ba = await asyncio.gather(
            asyncio.to_thread(self.client.models.generate_content, self.model_b, prompt_ab),
            asyncio.to_thread(self.client.models.generate_content, self.model_b, prompt_ba),
        )

        pick_ab = (out_ab.text or "").strip().upper()[:1]
        pick_ba = (out_ba.text or "").strip().upper()[:1]
        consistent = (pick_ab == "A" and pick_ba == "B") or (pick_ab == "B" and pick_ba == "A")

        return {
            "pick_ab": pick_ab,
            "pick_ba": pick_ba,
            "position_bias_detected": not consistent,
        }
