import os
import asyncio
from dotenv import load_dotenv
from typing import List, Dict, Any
import litellm
from datetime import datetime, timezone
from pathlib import Path

load_dotenv(override=True)

WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K = 5

_CHROMA_CLIENT = None

def _get_chroma_client():
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        import chromadb
        # Đảm bảo dùng đường dẫn tuyệt đối tới database
        base_dir = Path(__file__).resolve().parent.parent
        db_path = str(base_dir / "data" / "chroma_db")
        print(f"DEBUG Worker: Connecting to ChromaDB at {db_path}")
        _CHROMA_CLIENT = chromadb.PersistentClient(path=db_path)
    return _CHROMA_CLIENT

async def _get_embedding(text: str, profile: dict) -> List[float]:
    provider = profile.get("provider", "openai")
    model = profile.get("model", "text-embedding-3-small")
    full_model_path = f"{provider}/{model}" if "/" not in model else model
    
    try:
        response = await litellm.aembedding(model=full_model_path, input=[text])
        return response.data[0]["embedding"]
    except Exception as e:
        print(f"!!! Retrieval Embedding Error: {e}")
        import random
        return [random.random() for _ in range(1536)]

async def run(state: dict) -> dict:
    task = state.get("task", "")
    profile = state.get("llm_profiles", {}).get("retrieval", {})
    top_k = state.get("retrieval_top_k", DEFAULT_TOP_K)
    
    state.setdefault("workers_called", [])
    state.setdefault("worker_io_logs", [])
    state["workers_called"].append(WORKER_NAME)

    try:
        client = _get_chroma_client()
        col_name = os.getenv("COLLECTION_NAME", "rag_lab")
        collection = client.get_collection(col_name)
        
        query_embedding = await _get_embedding(task, profile)
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, 
            lambda: collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
        )
        
        chunks = []
        sources = set()
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                source = results["metadatas"][0][i].get("source", "unknown")
                score = round(max(0.0, min(1.0, 1 - results["distances"][0][i])), 4)
                doc_id = results["ids"][0][i]
                
                chunks.append({
                    "text": results["documents"][0][i],
                    "source": source,
                    "score": score,
                    "metadata": results["metadatas"][0][i],
                    "id": doc_id
                })
                sources.add(source)
        
        print(f"DEBUG Worker: Task='{task[:30]}' -> Found {len(chunks)} chunks")
        state["retrieved_chunks"] = chunks
        state["retrieved_sources"] = list(sources)
        state["history"].append(f"[{WORKER_NAME}] retrieved {len(chunks)} chunks")
        
    except Exception as e:
        print(f"!!! Retrieval Worker Error: {e}")
        state["retrieved_chunks"] = []
        state["retrieved_sources"] = []
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")
    
    return state
