from __future__ import annotations

import argparse
import glob
import importlib
import os
from typing import Dict, Iterable, List

import chromadb
from dotenv import load_dotenv

genai = importlib.import_module("google.genai")

from engine.chunking import semantic_chunk_corpus


def load_documents(docs_dir: str = "data/docs") -> Dict[str, str]:
    docs: Dict[str, str] = {}
    for file_path in glob.glob(os.path.join(docs_dir, "*.txt")):
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            docs[filename] = f.read()
    if not docs:
        raise FileNotFoundError(f"No .txt files found in {docs_dir}")
    return docs


def _batch(items: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def embed_texts(client: genai.Client, model: str, texts: List[str], batch_size: int = 32) -> List[List[float]]:
    vectors: List[List[float]] = []
    for text in texts:
        response = client.models.embed_content(model=model, contents=text)
        vectors.append(response.embeddings[0].values)
    return vectors


def ingest_documents(
    docs_dir: str = "data/docs",
    chroma_dir: str = "data/chroma_db",
    collection_name: str = "policy_chunks",
    embedding_model: str = "gemini-embedding-2-preview",
    max_chars: int = 1000,
    overlap_paragraphs: int = 1,
) -> Dict[str, int]:
    load_dotenv(override=True)

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) in environment")

    docs = load_documents(docs_dir)
    chunks = semantic_chunk_corpus(
        docs=docs,
        max_chars=max_chars,
        overlap_paragraphs=overlap_paragraphs,
    )
    if not chunks:
        raise ValueError("Chunking produced zero chunks")

    os.makedirs(chroma_dir, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=chroma_dir)
    collection = chroma_client.get_or_create_collection(name=collection_name)

    ids = [chunk["chunk_id"] for chunk in chunks]
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "source": chunk["source"],
            "source_stem": chunk["source_stem"],
            "chunk_index": chunk["chunk_index"],
            "char_length": chunk["char_length"],
        }
        for chunk in chunks
    ]

    # Reset old index for deterministic benchmark runs.
    existing = collection.get(include=[])
    existing_ids = existing.get("ids", []) if isinstance(existing, dict) else []
    if existing_ids:
        collection.delete(ids=existing_ids)

    genai_client = genai.Client(api_key=api_key)
    embeddings = embed_texts(genai_client, embedding_model, texts)

    collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    source_counts: Dict[str, int] = {}
    for chunk in chunks:
        source_counts[chunk["source"]] = source_counts.get(chunk["source"], 0) + 1

    return {
        "documents": len(docs),
        "chunks": len(chunks),
        "sources": len(source_counts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic chunk + Gemini embedding ingestion into Chroma")
    parser.add_argument("--docs-dir", default="data/docs")
    parser.add_argument("--chroma-dir", default="data/chroma_db")
    parser.add_argument("--collection", default="policy_chunks")
    parser.add_argument("--embedding-model", default="gemini-embedding-2-preview")
    parser.add_argument("--max-chars", type=int, default=1000)
    parser.add_argument("--overlap-paragraphs", type=int, default=1)
    args = parser.parse_args()

    stats = ingest_documents(
        docs_dir=args.docs_dir,
        chroma_dir=args.chroma_dir,
        collection_name=args.collection,
        embedding_model=args.embedding_model,
        max_chars=args.max_chars,
        overlap_paragraphs=args.overlap_paragraphs,
    )
    print(f"Ingestion complete: {stats}")


if __name__ == "__main__":
    main()
