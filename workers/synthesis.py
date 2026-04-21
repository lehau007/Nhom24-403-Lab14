from datetime import datetime, timezone

import litellm
from dotenv import load_dotenv

load_dotenv(override=True)

WORKER_NAME = "synthesis_worker"

SYSTEM_PROMPT = """Bạn là trợ lý nội bộ chuyên nghiệp.
Nhiệm vụ: trả lời CHỈ dựa trên bằng chứng được cung cấp trong context.

QUY TẮC CỐT LÕI (Contract Constraints):
1. Phải có trích dẫn nguồn bằng định dạng [tên_nguồn] ngay sau thông tin sử dụng.
2. Nếu không có context hoặc context trống -> Trả lời rõ: "Tôi không tìm thấy đủ thông tin trong tài liệu nội bộ để trả lời câu hỏi này."
3. Tuyệt đối không sử dụng kiến thức bên ngoài (hallucination).
4. Nếu có Policy Exceptions, hãy liệt kê chúng ở đầu câu trả lời với biểu tượng ⚠️.
"""


def _build_context(chunks: list, policy_result: dict) -> str:
    parts = []
    if chunks:
        parts.append("=== BẰNG CHỨNG TRUY XUẤT ===")
        for i, chunk in enumerate(chunks):
            parts.append(f"[{i + 1}] Nguồn: {chunk['source']} (Relevance: {chunk['score']})\n{chunk['text']}")

    if policy_result and policy_result.get("exceptions_found"):
        parts.append("=== CẢNH BÁO CHÍNH SÁCH ===")
        for exc in policy_result["exceptions_found"]:
            parts.append(f"- {exc['rule']} [Nguồn: {exc['source']}]")

    return "\n\n".join(parts) if parts else "(Không có ngữ cảnh)"


def _estimate_confidence(chunks: list, answer: str) -> float:
    if not chunks or "không tìm thấy đủ thông tin" in answer.lower():
        return 0.2
    avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks)
    return round(max(0.1, min(0.95, avg_score)), 2)


async def run(state: dict) -> dict:
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})
    profile = state.get("llm_profiles", {}).get("synthesis", {})

    state.setdefault("workers_called", [])
    state.setdefault("worker_io_logs", [])
    state["workers_called"].append(WORKER_NAME)

    worker_input = {"task": task, "chunks_count": len(chunks), "profile": profile}

    try:
        context = _build_context(chunks, policy_result)
        model_path = (
            f"{profile.get('provider')}/{profile.get('model')}"
            if "/" not in profile.get("model", "")
            else profile.get("model")
        )

        prompt = f"CÂU HỎI: {task}\n\n{context}\n\nCÂU TRẢ LỜI ĐƯỢC GROUNDED:"

        # Gọi LLM qua LiteLLM
        response = await litellm.acompletion(
            model=model_path,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=0,
        )

        final_answer = response.choices[0].message.content
        sources = list(set(c["source"] for c in chunks))
        if policy_result.get("exceptions_found"):
            for e in policy_result["exceptions_found"]:
                sources.append(e["source"])

        confidence = _estimate_confidence(chunks, final_answer)

        state["final_answer"] = final_answer
        state["sources"] = list(set(sources))
        state["confidence"] = confidence

        # Log I/O
        state["worker_io_logs"].append(
            {
                "worker": WORKER_NAME,
                "input": worker_input,
                "output": {
                    "answer_length": len(final_answer),
                    "confidence": confidence,
                    "sources_count": len(state["sources"]),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        state["history"].append(f"[{WORKER_NAME}] synthesis complete (conf={confidence})")

    except Exception as e:
        state["final_answer"] = f"SYNTHESIS_ERROR: {str(e)}"
        state["confidence"] = 0.0
        state["worker_io_logs"].append(
            {
                "worker": WORKER_NAME,
                "input": worker_input,
                "error": {"code": "SYNTHESIS_FAILED", "reason": str(e)},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    return state
