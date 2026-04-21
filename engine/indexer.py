import asyncio
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import chromadb
import litellm
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv(override=True)

# =============================================================================
# CONFIGURATION
# =============================================================================
DOCS_DIR = Path("data/docs")
CHROMA_DB_DIR = Path(os.getenv("CHROMA_DB_PATH", "./data/chroma_db"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "rag_lab")

# Embedding Profile (Đồng bộ với Retrieval Worker)
EMBEDDING_MODEL = (
    f"{os.getenv('RETRIEVAL_PROVIDER', 'openai')}/{os.getenv('RETRIEVAL_MODEL', 'text-embedding-3-small')}"
)

# =============================================================================
# CORE LOGIC
# =============================================================================


def preprocess_document(raw_text: str, filepath: str) -> Dict[str, Any]:
    """Trích xuất metadata và làm sạch nội dung."""
    lines = raw_text.strip().split("\n")
    metadata = {
        "source": filepath,
        "department": "unknown",
        "effective_date": "unknown",
        "access": "internal",
    }
    content_lines = []
    header_done = False

    for line in lines:
        if not header_done:
            if line.startswith("Source:"):
                metadata["source"] = line.replace("Source:", "").strip()
            elif line.startswith("Department:"):
                metadata["department"] = line.replace("Department:", "").strip()
            elif line.startswith("Effective Date:"):
                metadata["effective_date"] = line.replace("Effective Date:", "").strip()
            elif line.startswith("==="):
                header_done = True
                content_lines.append(line)
        else:
            content_lines.append(line)

    return {"text": "\n".join(content_lines), "metadata": metadata}


def chunk_document(doc: Dict[str, Any], chunk_size: int = 500) -> List[Dict[str, Any]]:
    """Chia nhỏ tài liệu theo section hoặc kích thước cố định."""
    text = doc["text"]
    base_meta = doc["metadata"]
    chunks = []

    # Chia theo dấu hiệu Section
    sections = re.split(r"(===.*?===)", text)
    current_section = "General"

    for part in sections:
        if re.match(r"===.*?===", part):
            current_section = part.strip("= ")
        elif part.strip():
            # Nếu nội dung section quá dài, chia nhỏ tiếp theo độ dài
            sub_chunks = [part[i : i + chunk_size * 4] for i in range(0, len(part), chunk_size * 4)]
            for sc in sub_chunks:
                chunks.append({"text": sc.strip(), "metadata": {**base_meta, "section": current_section}})
    return chunks


async def get_embedding(text: str) -> List[float]:
    """Tạo embedding sử dụng LiteLLM (Multi-provider)."""
    try:
        response = await litellm.aembedding(model=EMBEDDING_MODEL, input=[text])
        return response.data[0]["embedding"]
    except Exception as e:
        print(f"Embedding error with {EMBEDDING_MODEL}: {e}")
        # Fallback random cho lab
        import random

        return [random.random() for _ in range(1536)]


async def build_index():
    """Quy trình Ingestion hoàn chỉnh."""
    print(f"🚀 Khởi động Indexer sử dụng model: {EMBEDDING_MODEL}")

    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    doc_files = list(DOCS_DIR.glob("*.txt"))
    if not doc_files:
        print(f"❌ Không tìm thấy tài liệu trong {DOCS_DIR}")
        return

    for filepath in tqdm(doc_files, desc="Indexing"):
        raw_text = filepath.read_text(encoding="utf-8")
        doc = preprocess_document(raw_text, filepath.name)
        chunks = chunk_document(doc)

        ids, embeddings, documents, metadatas = [], [], [], []

        for i, chunk in enumerate(chunks):
            emb = await get_embedding(chunk["text"])
            ids.append(f"{filepath.stem}_{i}")
            embeddings.append(emb)
            documents.append(chunk["text"])
            metadatas.append(chunk["metadata"])

        if ids:
            collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    print(f"✅ Đã nạp thành công {len(doc_files)} tài liệu vào ChromaDB.")


if __name__ == "__main__":
    asyncio.run(build_index())
