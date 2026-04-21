import json
import os
import re
import shutil
from collections import defaultdict
from typing import Dict, List

import chromadb
from dotenv import load_dotenv

from engine.ingestion import ingest_documents


def _first_sentence(text: str, max_len: int = 260) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    candidate = parts[0] if parts else cleaned
    return candidate[:max_len]


def _strip_source_ext(source: str) -> str:
    return source.rsplit(".", 1)[0]


def _build_single_chunk_case(chunk: Dict) -> Dict:
    source = chunk["metadata"].get("source", "unknown.txt")
    text = chunk["document"]
    answer = _first_sentence(text)
    return {
        "question": f"Theo tài liệu {_strip_source_ext(source)}, thông tin cốt lõi ở đoạn liên quan là gì?",
        "expected_answer": answer,
        "context": text[:500],
        "metadata": {
            "difficulty": "easy",
            "type": "fact-check",
            "source": source,
        },
        "expected_chunk_ids": [chunk["id"]],
        "expected_retrieval_ids": [chunk["id"]],
    }


def _build_edge_cases(source_to_chunks: Dict[str, List[Dict]]) -> List[Dict]:
    edge_cases: List[Dict] = []
    ordered_sources = sorted(source_to_chunks.keys())
    if len(ordered_sources) < 2:
        return edge_cases

    for i in range(len(ordered_sources) - 1):
        a = ordered_sources[i]
        b = ordered_sources[i + 1]
        chunk_a = source_to_chunks[a][0]
        chunk_b = source_to_chunks[b][0]
        answer_a = _first_sentence(chunk_a["document"])
        answer_b = _first_sentence(chunk_b["document"])

        edge_cases.append(
            {
                "question": (
                    f"Kết hợp chính sách từ {_strip_source_ext(a)} và {_strip_source_ext(b)}, "
                    "điều kiện chính cần lưu ý là gì?"
                ),
                "expected_answer": f"{answer_a} Đồng thời: {answer_b}",
                "context": f"{chunk_a['document'][:250]}\n---\n{chunk_b['document'][:250]}",
                "metadata": {
                    "difficulty": "hard",
                    "type": "multi-hop",
                    "source": f"{a}, {b}",
                },
                "expected_chunk_ids": [chunk_a["id"], chunk_b["id"]],
                "expected_retrieval_ids": [chunk_a["id"], chunk_b["id"]],
            }
        )

        edge_cases.append(
            {
                "question": (
                    f"Có ngoại lệ hoặc trường hợp KHÔNG áp dụng nào trong {_strip_source_ext(a)} không? "
                    "Nếu không thấy rõ, hãy nói thiếu dữ liệu."
                ),
                "expected_answer": (
                    "Chỉ xác nhận ngoại lệ khi có bằng chứng trong tài liệu; "
                    f"đoạn liên quan hiện có: {answer_a}"
                ),
                "context": chunk_a["document"][:500],
                "metadata": {
                    "difficulty": "hard",
                    "type": "edge-case",
                    "source": a,
                },
                "expected_chunk_ids": [chunk_a["id"]],
                "expected_retrieval_ids": [chunk_a["id"]],
            }
        )

    return edge_cases


def generate_golden_set(target_count: int = 50) -> List[Dict]:
    load_dotenv(override=True)

    if os.getenv("SKIP_INGEST", "0") != "1":
        ingest_documents(
            docs_dir="data/docs",
            chroma_dir=os.getenv("CHROMA_DB_PATH", "data/chroma_db"),
            collection_name=os.getenv("CHROMA_COLLECTION", "policy_chunks"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "gemini-embedding-2-preview"),
        )

    chroma = chromadb.PersistentClient(path=os.getenv("CHROMA_DB_PATH", "data/chroma_db"))
    collection = chroma.get_or_create_collection(name=os.getenv("CHROMA_COLLECTION", "policy_chunks"))
    data = collection.get(include=["documents", "metadatas"])

    ids = data.get("ids", [])
    docs = data.get("documents", [])
    metadatas = data.get("metadatas", [])

    chunk_rows: List[Dict] = []
    for chunk_id, document, metadata in zip(ids, docs, metadatas):
        chunk_rows.append({"id": chunk_id, "document": document, "metadata": metadata or {}})

    source_to_chunks: Dict[str, List[Dict]] = defaultdict(list)
    for row in chunk_rows:
        source = row["metadata"].get("source", "unknown.txt")
        source_to_chunks[source].append(row)

    cases: List[Dict] = []
    for chunks in source_to_chunks.values():
        for chunk in chunks:
            cases.append(_build_single_chunk_case(chunk))

    cases.extend(_build_edge_cases(source_to_chunks))

    # Upsample deterministically if corpus is small.
    idx = 0
    while cases and len(cases) < target_count:
        base = cases[idx % len(cases)]
        duplicated = dict(base)
        duplicated["question"] = f"[Biến thể {idx+1}] {base['question']}"
        duplicated["metadata"] = dict(base["metadata"])
        duplicated["metadata"]["difficulty"] = "medium" if base["metadata"].get("difficulty") == "easy" else base["metadata"].get("difficulty")
        cases.append(duplicated)
        idx += 1

    return cases[:target_count]


def main() -> None:
    os.makedirs("data", exist_ok=True)
    output_path = "data/golden_set.jsonl"
    backup_path = "data/golden_set.backup.jsonl"

    if os.path.exists(output_path):
        shutil.copyfile(output_path, backup_path)
        print(f"Backed up existing golden set to {backup_path}")

    cases = generate_golden_set(target_count=50)
    with open(output_path, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"Generated {len(cases)} cases to {output_path}")


if __name__ == "__main__":
    main()
