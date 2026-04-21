import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator

# Real evaluator wrapping our logic
class ExpertEvaluator:
    def __init__(self):
        self.evaluator = RetrievalEvaluator()

    async def score(self, case, resp): 
        # Integration logic: extract ids from case and response
        expected_ids = case.get("expected_retrieval_ids", [])
        retrieved_ids = resp.get("metadata", {}).get("sources", []) # Simplified for now
        
        hit_rate = self.evaluator.calculate_hit_rate(expected_ids, retrieved_ids)
        mrr = self.evaluator.calculate_mrr(expected_ids, retrieved_ids)
        
        return {
            "faithfulness": 0.9, # Mock for now
            "relevancy": 0.8,    # Mock for now
            "retrieval": {"hit_rate": hit_rate, "mrr": mrr}
        }

async def run_benchmark_with_results(agent_version: str):
    print(f"🚀 Khởi động Benchmark cho {agent_version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("❌ Thiếu data/golden_set.jsonl. Hãy chạy 'python data/synthetic_gen.py' trước.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("❌ File data/golden_set.jsonl rỗng. Hãy tạo ít nhất 1 test case.")
        return None, None

    # Initialize Judge (GPT-4o-mini for 30% cost saving)
    judge = LLMJudge(model_b="gpt-4o-mini") 
    runner = BenchmarkRunner(MainAgent(), ExpertEvaluator(), judge)
    results = await runner.run_all(dataset)
    
    # Use the new aggregation method
    metrics = runner.get_summary_metrics(results)
    
    summary = {
        "metadata": {
            "version": agent_version, 
            "total": len(results), 
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "metrics": metrics
    }
    return results, summary

async def run_benchmark(version):
    _, summary = await run_benchmark_with_results(version)
    return summary

async def main():
    v1_summary = await run_benchmark("Agent_V1_Base")
    
    # Giả lập V2 có cải tiến (để test logic)
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")
    
    if not v1_summary or not v2_summary:
        print("❌ Không thể chạy Benchmark. Kiểm tra lại data/golden_set.jsonl.")
        return

    print("\n📊 --- KẾT QUẢ SO SÁNH (REGRESSION) ---")
    
    m1 = v1_summary["metrics"]
    m2 = v2_summary["metrics"]
    
    delta = m2["avg_judge_score"] - m1["avg_judge_score"]
    
    print(f"V1 Score: {m1['avg_judge_score']:.2f} | Cost: ${m1['total_cost']:.4f}")
    print(f"V2 Score: {m2['avg_judge_score']:.2f} | Cost: ${m2['total_cost']:.4f}")
    print(f"Delta Score: {'+' if delta >= 0 else ''}{delta:.2f}")
    print(f"Avg Latency: {m2['avg_latency']:.2f}s")
    print(f"Agreement Rate: {m2['avg_agreement']*100:.1f}%")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    if delta >= 0:
        print("✅ QUYẾT ĐỊNH: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)")
    else:
        print("❌ QUYẾT ĐỊNH: TỪ CHỐI (BLOCK RELEASE)")

if __name__ == "__main__":
    asyncio.run(main())
