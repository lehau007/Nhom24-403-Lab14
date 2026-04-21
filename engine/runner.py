import asyncio
import time
from typing import List, Dict

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    async def run_single_test(self, test_case: Dict) -> Dict:
        start_time = time.perf_counter()
        try:
            print(f"[{test_case['question'][:15]}] Gọi agent.query...")
            response = await self.agent.query(test_case["question"])
            print(f"[{test_case['question'][:15]}] Agent trả lời xong.")
            latency = time.perf_counter() - start_time

            print(f"[{test_case['question'][:15]}] Tính điểm RAGAS...")
            ragas_scores = self.evaluator.score(test_case, response)
            
            print(f"[{test_case['question'][:15]}] Bắt đầu judge...")
            judge_result = await self.judge.evaluate_multi_judge(
                test_case["question"],
                response["answer"],
                test_case["expected_answer"],
            )
            print(f"[{test_case['question'][:15]}] Judge xong.")

            return {
                "test_case": test_case["question"],
                "agent_response": response["answer"],
                "retrieved_ids": response.get("retrieved_ids", []),
                "latency": latency,
                "ragas": ragas_scores,
                "judge": judge_result,
                "status": "fail" if judge_result["final_score"] < 3 else "pass",
            }
        except Exception as exc:
            latency = time.perf_counter() - start_time
            return {
                "test_case": test_case.get("question", "<missing_question>"),
                "agent_response": "",
                "retrieved_ids": [],
                "latency": latency,
                "ragas": {
                    "faithfulness": 0.0,
                    "relevancy": 0.0,
                    "retrieval": {"hit_rate": 0.0, "mrr": 0.0},
                },
                "judge": {
                    "final_score": 1.0,
                    "agreement_rate": 0.0,
                    "individual_scores": {},
                    "error": str(exc),
                },
                "status": "error",
            }

    async def run_all(self, dataset: List[Dict], batch_size: int = 1) -> List[Dict]:
        """
        Chạy bằng asyncio nhưng set batch_size=1 và thêm sleep để an toàn với rate limits.
        """
        results = []
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            tasks = [self.run_single_test(case) for case in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            await asyncio.sleep(2)  # Delay between batches
        return results
