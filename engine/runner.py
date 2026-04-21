import asyncio
import time
from typing import List, Dict, Any
from tqdm.asyncio import tqdm

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        """
        Initializes the runner with an agent, an evaluator (for retrieval metrics), 
        and a judge (for LLM consensus).
        """
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        self.total_cost = 0.0

    async def run_single_test(self, test_case: Dict) -> Dict:
        """
        Executes a single test case through the full pipeline.
        """
        start_time = time.perf_counter()
        
        try:
            # 1. Gọi Agent để lấy câu trả lời
            response = await self.agent.query(test_case["question"])
            latency = time.perf_counter() - start_time
            
            # 2. Chạy Retrieval Evaluation (Hit Rate, MRR) & RAGAS
            ragas_scores = await self.evaluator.score(test_case, response)
            
            # 3. Chạy Multi-Judge Consensus
            judge_result = await self.judge.evaluate_multi_judge(
                test_case["question"], 
                response["answer"], 
                test_case["expected_answer"]
            )
            
            # Accumulate cost
            self.total_cost += judge_result.get("cost", 0.0)
            
            return {
                "question": test_case["question"],
                "agent_response": response["answer"],
                "latency": latency,
                "ragas": ragas_scores,
                "judge": judge_result,
                "status": "pass" if judge_result["final_score"] >= 3.5 else "fail"
            }
        except Exception as e:
            print(f"Error in test case '{test_case.get('question', 'Unknown')}': {e}")
            return {
                "question": test_case.get("question", "Unknown"),
                "error": str(e),
                "status": "error"
            }

    async def run_all(self, dataset: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Runs all test cases in parallel batches to optimize speed while respecting rate limits.
        """
        results = []
        self.total_cost = 0.0 # Reset cost for the run
        
        # Use tqdm for progress tracking in async environment
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            tasks = [self.run_single_test(case) for case in batch]
            
            # Run the batch
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Optional: Small delay between batches if needed for aggressive rate limits
            # await asyncio.sleep(1) 
            
        return results

    def get_summary_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """
        Aggregates results into high-level metrics.
        """
        valid_results = [r for r in results if "error" not in r]
        if not valid_results:
            return {"error": "No valid results to aggregate"}
            
        total = len(valid_results)
        
        avg_latency = sum(r["latency"] for r in valid_results) / total
        avg_judge_score = sum(r["judge"]["final_score"] for r in valid_results) / total
        avg_agreement = sum(r["judge"]["agreement_rate"] for r in valid_results) / total
        
        # Retrieval metrics
        avg_hit_rate = sum(r["ragas"]["retrieval"]["hit_rate"] for r in valid_results) / total
        avg_mrr = sum(r["ragas"]["retrieval"]["mrr"] for r in valid_results) / total
        
        return {
            "avg_latency": avg_latency,
            "avg_judge_score": avg_judge_score,
            "avg_agreement": avg_agreement,
            "avg_hit_rate": avg_hit_rate,
            "avg_mrr": avg_mrr,
            "total_cost": self.total_cost,
            "pass_rate": sum(1 for r in valid_results if r["status"] == "pass") / total
        }
