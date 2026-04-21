import asyncio
import json
import os
import re
from typing import Any, Dict, List

import litellm
from dotenv import load_dotenv

load_dotenv(override=True)


class LLMJudge:
    def __init__(self, judge_profiles: List[Dict[str, str]] = None):
        if judge_profiles:
            self.judge_profiles = judge_profiles
        else:
            self.judge_profiles = [
                {
                    "provider": os.getenv("JUDGE_1_PROVIDER", "openai"),
                    "model": os.getenv("JUDGE_1_MODEL", "gpt-4o-mini"),
                },
                {
                    "provider": os.getenv("JUDGE_2_PROVIDER", "gemini"),
                    "model": os.getenv("JUDGE_2_MODEL", "gemini-1.5-flash-latest"),
                },
            ]

    async def _call_single_judge(
        self, profile: Dict[str, str], question: str, answer: str, ground_truth: str
    ) -> Dict[str, Any]:
        provider = profile.get("provider", "openai")
        model = profile.get("model", "gpt-4o-mini")
        full_model_path = f"{provider}/{model}" if "/" not in model else model

        prompt = f"""
        Hãy đóng vai giám khảo AI. Chấm điểm câu trả lời của Agent dựa trên Ground Truth.
        Câu hỏi: {question}
        Câu trả lời của Agent: {answer}
        Ground Truth (Đáp án đúng): {ground_truth}

        Hãy chấm điểm Accuracy từ 1 đến 5.
        Trả về kết quả theo định dạng JSON duy nhất như sau:
        {{
            "score": <con số từ 1-5>,
            "reasoning": "<giải thích lý do chấm điểm này ngắn gọn bằng tiếng Việt>"
        }}
        """

        # Cơ chế Retry cho lỗi 503 hoặc 429
        for attempt in range(3):
            try:
                response = await litellm.acompletion(
                    model=full_model_path,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2000,
                )
                content = response.choices[0].message.content or ""

                # Trích xuất JSON từ content
                try:
                    json_str = content
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0].strip()

                    # Clean potential invisible characters
                    json_str = json_str.strip()

                    data = json.loads(json_str)
                    return {
                        "score": int(data.get("score", 3)),
                        "reasoning": data.get("reasoning", "Không có giải thích."),
                    }
                except:
                    # Fallback dùng Regex nếu JSON bị lỗi nhẹ
                    score_match = re.search(r'"score":\s*(\d)', content)
                    reasoning_match = re.search(r'"reasoning":\s*"([^"]+)"', content)
                    return {
                        "score": int(score_match.group(1)) if score_match else 3,
                        "reasoning": reasoning_match.group(1) if reasoning_match else "Lỗi parse JSON từ Judge.",
                    }

            except Exception as e:
                if "503" in str(e) or "429" in str(e):
                    await asyncio.sleep(2**attempt)
                    continue
                return {"score": 0, "reasoning": f"Error {provider.upper()}: {str(e)}"}
        return {"score": 3, "reasoning": "Judge không phản hồi sau nhiều lần thử."}

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        tasks = [self._call_single_judge(p, question, answer, ground_truth) for p in self.judge_profiles]
        judge_results = await asyncio.gather(*tasks)

        scores = [r["score"] for r in judge_results]
        avg_score = sum(scores) / len(scores)

        # Tính agreement_rate đơn giản (khoảng cách điểm)
        if len(scores) >= 2:
            diff = abs(scores[0] - scores[1])
            agreement = max(0, 1.0 - (diff / 4.0))  # 1.0 nếu bằng nhau, 0.0 nếu lệch tối đa (1 vs 5)
        else:
            agreement = 1.0

        # Build individual_results theo format mẫu
        individual_results = {}
        for i, p in enumerate(self.judge_profiles):
            # Lấy tên model ngắn gọn làm key
            model_key = p["model"].split("/")[-1]
            individual_results[model_key] = judge_results[i]

        return {
            "final_score": avg_score,
            "agreement_rate": agreement,
            "individual_results": individual_results,
            "status": "consensus" if agreement >= 0.75 else "conflict",
        }
