import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator

# Lớp cầu nối để tính toán Retrieval metrics
class ExpertEvaluator:
    def __init__(self):
        self.evaluator = RetrievalEvaluator()

    async def score(self, case, resp): 
        expected_ids = case.get("expected_retrieval_ids", [])
        retrieved_ids = resp.get("retrieved_ids", []) 
        
        hit_rate = self.evaluator.calculate_hit_rate(expected_ids, retrieved_ids)
        mrr = self.evaluator.calculate_mrr(expected_ids, retrieved_ids)
        
        return {
            "retrieval": {"hit_rate": hit_rate, "mrr": mrr}
        }

async def run_test():
    print("🧪 Đang chạy thử Sprint 2 (5 cases)...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("❌ Lỗi: Không tìm thấy data/golden_set.jsonl")
        return

    # 1. Load 5 cases đầu tiên
    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()][:5]

    print(f"✅ Đã load {len(dataset)} test cases.")

    # 2. Khởi tạo Engine (Sử dụng gpt-4o-mini để tiết kiệm)
    judge = LLMJudge(model_b="gpt-4o-mini")
    runner = BenchmarkRunner(MainAgent(), ExpertEvaluator(), judge)

    # 3. Chạy Benchmark
    start_run = time.perf_counter()
    results = await runner.run_all(dataset, batch_size=2)
    duration = time.perf_counter() - start_run

    # 4. Tổng hợp kết quả
    metrics = runner.get_summary_metrics(results)

    print("\n📊 --- KẾT QUẢ TEST NHANH ---")
    print(f"Tổng thời gian: {duration:.2f}s")
    print(f"Điểm trung bình (Judge): {metrics['avg_judge_score']:.2f}/5.0")
    print(f"Tỉ lệ đồng thuận: {metrics['avg_agreement']*100:.1f}%")
    print(f"Tỉ lệ tìm kiếm đúng (Hit Rate): {metrics['avg_hit_rate']*100:.1f}%")
    print(f"Tổng chi phí ước tính: ${metrics['total_cost']:.5f}")

    # 5. Lưu log tạm thời để xem chi tiết
    with open("reports/test_sprint2_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n📂 Chi tiết từng case đã được lưu tại reports/test_sprint2_results.json")

if __name__ == "__main__":
    asyncio.run(run_test())
