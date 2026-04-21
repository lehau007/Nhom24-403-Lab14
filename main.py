import asyncio
import json
import os
import time

import litellm

from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from engine.runner import BenchmarkRunner

# Tắt toàn bộ log nhiễu của LiteLLM
litellm.set_verbose = False
litellm.suppress_debug_info = True


async def run_benchmark_with_results(agent_version: str):
    print(f"🚀 Khởi động Benchmark cho {agent_version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("❌ Thiếu data/golden_set.jsonl.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("❌ File data/golden_set.jsonl rỗng. Hãy tạo ít nhất 1 test case.")
        return None, None

    agent = MainAgent()
    judge = LLMJudge()
    evaluator = RetrievalEvaluator()

    runner = BenchmarkRunner(agent, evaluator, judge)
    results = await runner.run_all(dataset)

    total = len(results)
    if total == 0:
        return None, None

    summary = {
        "avg_score": sum(r["judge"]["final_score"] for r in results) / total,
        "hit_rate": sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total,
        "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results) / total,
    }
    return results, summary


async def main():
    try:
        # Chạy bản V1
        v1_results, v1_summary = await run_benchmark_with_results("Agent_V1")

        # Giả lập thay đổi cấu hình cho V2 để so sánh (Ví dụ: tăng Top-K)
        os.environ["RETRIEVAL_TOP_K"] = "10"
        v2_results, v2_summary = await run_benchmark_with_results("Agent_V2")

        if not v1_summary or not v2_summary:
            print("❌ Không thể chạy Benchmark. Kiểm tra lại data/golden_set.jsonl.")
            return

        print("\n📊 --- KẾT QUẢ SO SÁNH (REGRESSION) ---")
        delta = v2_summary["avg_score"] - v1_summary["avg_score"]
        print(f"V1 Score: {v1_summary['avg_score']:.2f}")
        print(f"V2 Score: {v2_summary['avg_score']:.2f}")
        print(f"Delta: {'+' if delta >= 0 else ''}{delta:.2f}")

        # Cấu trúc Summary theo format samples_results/summary.json
        final_summary = {
            "metadata": {
                "total": len(v1_results),
                "version": "BASELINE (V1)",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "versions_compared": ["V1", "V2"],
            },
            "metrics": {
                "avg_score": v2_summary["avg_score"],
                "hit_rate": v2_summary["hit_rate"],
                "agreement_rate": v2_summary["agreement_rate"],
            },
            "regression": {
                "v1": {
                    "score": v1_summary["avg_score"],
                    "hit_rate": v1_summary["hit_rate"],
                    "judge_agreement": v1_summary["agreement_rate"],
                },
                "v2": {
                    "score": v2_summary["avg_score"],
                    "hit_rate": v2_summary["hit_rate"],
                    "judge_agreement": v2_summary["agreement_rate"],
                },
                "decision": "APPROVE" if delta > 0 else "BLOCK",
            },
        }

        # Cấu trúc Results theo format samples_results/benchmark_results.json
        final_results = {"v1": v1_results, "v2": v2_results}

        os.makedirs("reports", exist_ok=True)
        with open("reports/summary.json", "w", encoding="utf-8") as f:
            json.dump(final_summary, f, ensure_ascii=False, indent=2)
        with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)

        if delta > 0:
            print("✅ QUYẾT ĐỊNH: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)")
        else:
            print("❌ QUYẾT ĐỊNH: TỪ CHỐI (BLOCK RELEASE)")

    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
