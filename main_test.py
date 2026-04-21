import asyncio
import json
import os
import time
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from agent.main_agent import MainAgent
from engine.ingestion import ingest_documents
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from engine.runner import BenchmarkRunner


def _load_dataset(path: str = "data/golden_set_test.jsonl") -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]
    return dataset


async def run_benchmark_with_results(agent_version: str, top_k: int) -> Tuple[Optional[List[Dict]], Optional[Dict]]:
    print(f"🚀 Khởi động Benchmark cho {agent_version}...")

    if not os.path.exists("data/golden_set_test.jsonl"):
        print("❌ Thiếu data/golden_set_test.jsonl. Hãy chạy 'python data/synthetic_gen.py' trước.")
        return None, None

    dataset = _load_dataset("data/golden_set_test.jsonl")

    if not dataset:
        print("❌ File data/golden_set_test.jsonl rỗng. Hãy tạo ít nhất 1 test case.")
        return None, None

    runner = BenchmarkRunner(
        MainAgent(
            top_k=top_k,
            generation_model=os.getenv("GENERATION_MODEL", "gemma-4-31b-it"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "gemini-embedding-2-preview"),
            collection_name=os.getenv("CHROMA_COLLECTION", "policy_chunks"),
            chroma_dir=os.getenv("CHROMA_DB_PATH", "data/chroma_db"),
        ),
        RetrievalEvaluator(),
        LLMJudge(
            model_a=os.getenv("JUDGE_MODEL_A", "gemma-3-12b-it"),
            model_b=os.getenv("JUDGE_MODEL_B", "gemma-3-27b-it"),
        ),
    )
    results = await runner.run_all(dataset)

    total = len(results)
    avg_score = sum(r["judge"]["final_score"] for r in results) / total if total else 0.0
    hit_rate = sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total if total else 0.0
    avg_mrr = sum(r["ragas"]["retrieval"]["mrr"] for r in results) / total if total else 0.0
    agreement_rate = sum(r["judge"]["agreement_rate"] for r in results) / total if total else 0.0
    avg_latency = sum(r["latency"] for r in results) / total if total else 0.0

    summary = {
        "metadata": {"version": agent_version, "total": total, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")},
        "metrics": {
            "avg_score": avg_score,
            "hit_rate": hit_rate,
            "avg_mrr": avg_mrr,
            "agreement_rate": agreement_rate,
            "avg_latency": avg_latency,
        },
    }
    return results, summary


async def run_benchmark(version: str, top_k: int):
    _, summary = await run_benchmark_with_results(version, top_k)
    return summary


async def main():
    load_dotenv(override=True)

    if os.getenv("SKIP_INGEST", "0") != "1":
        print("🔄 Đang index tài liệu vào Chroma...")
        stats = ingest_documents(
            docs_dir="data/docs",
            chroma_dir=os.getenv("CHROMA_DB_PATH", "data/chroma_db"),
            collection_name=os.getenv("CHROMA_COLLECTION", "policy_chunks"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "gemini-embedding-2-preview"),
        )
        print(f"✅ Ingestion stats: {stats}")

    v1_summary = await run_benchmark("Agent_V1_Base", top_k=1)
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized", top_k=3)

    if not v1_summary or not v2_summary:
        print("❌ Không thể chạy Benchmark. Kiểm tra lại data/golden_set.jsonl.")
        return

    print("\n📊 --- KẾT QUẢ SO SÁNH (REGRESSION) ---")
    delta = v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"]
    print(f"V1 Score: {v1_summary['metrics']['avg_score']}")
    print(f"V2 Score: {v2_summary['metrics']['avg_score']}")
    print(f"Delta: {'+' if delta >= 0 else ''}{delta:.2f}")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    min_delta = float(os.getenv("RELEASE_MIN_DELTA", "0.05"))
    min_hit_rate = float(os.getenv("RELEASE_MIN_HIT_RATE", "0.55"))

    if delta >= min_delta and v2_summary["metrics"]["hit_rate"] >= min_hit_rate:
        print("✅ QUYẾT ĐỊNH: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)")
    else:
        print("❌ QUYẾT ĐỊNH: TỪ CHỐI (BLOCK RELEASE)")

if __name__ == "__main__":
    asyncio.run(main())
