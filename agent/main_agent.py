import asyncio
import importlib
import os
from typing import Any, Dict, List

import chromadb
from dotenv import load_dotenv
from openai import AsyncOpenAI  # FIX 1: Use AsyncOpenAI instead of OpenAI

genai = importlib.import_module("google.genai")


class MainAgent:
    """RAG agent with Chroma retrieval + Google GenAI generation."""

    def __init__(
        self,
        collection_name: str = "policy_chunks",
        chroma_dir: str = "data/chroma_db",
        embedding_model: str = "gemini-embedding-2-preview",
        generation_model: str = "gemma-4-31b-it",
        top_k: int = 4,
    ):
        load_dotenv(override=True)
        self.name = "SupportAgent-RAG"
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.generation_model = generation_model
        self.top_k = top_k

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) in environment")

        self.llm_client = genai.Client(api_key=api_key)
        if generation_model != "gemma-4-31b-it":
            # FIX 1: AsyncOpenAI supports awaiting directly without asyncio.to_thread
            self.llm_client = AsyncOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("GROQ_API_KEY"),
            )

        self.client = genai.Client(api_key=api_key)
        self.chroma = chromadb.PersistentClient(path=chroma_dir)
        self.collection = self.chroma.get_or_create_collection(name=collection_name)

    def _embed_query(self, query: str) -> List[float]:
        response = self.client.models.embed_content(
            model=self.embedding_model,
            contents=[query],
        )
        return response.embeddings[0].values

    def _retrieve(self, question: str) -> Dict:
        def _first_row(value: Any) -> List[Any]:
            if isinstance(value, list) and value:
                first = value[0]
                if isinstance(first, list):
                    return first
            return []

        query_embedding = self._embed_query(question)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=self.top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = _first_row(results.get("documents"))
        metadatas = _first_row(results.get("metadatas"))
        ids = _first_row(results.get("ids"))
        distances = _first_row(results.get("distances"))

        source_set = {
            str(md.get("source"))
            for md in metadatas
            if isinstance(md, dict) and md.get("source") is not None
        }
        sources = sorted(source_set)

        return {
            "contexts": documents,
            "retrieved_ids": ids,
            "sources": sources,
            "distances": distances,
        }

    async def _generate_answer_async(self, question: str, contexts: List[str]) -> str:
        context_block = "\n\n".join([f"[{i+1}] {ctx}" for i, ctx in enumerate(contexts)])
        prompt = (
            "Bạn là trợ lý hỗ trợ nội bộ. Chỉ trả lời dựa trên context đã truy xuất. "
            "Nếu context không đủ, nói rõ là chưa đủ dữ liệu và nêu cần bổ sung gì.\n\n"
            f"Câu hỏi:\n{question}\n\n"
            f"Context:\n{context_block}\n\n"
            "Yêu cầu: Trả lời ngắn gọn, chính xác, nêu rõ điều kiện/ngoại lệ nếu có."
        )

        try:
            if self.generation_model == "gemma-4-31b-it":
                response = await self.llm_client.aio.models.generate_content(
                    model=self.generation_model,
                    contents=prompt,
                )
                return (response.text or "").strip()
            else:
                # FIX 2: Use chat.completions.create (not responses.create)
                # FIX 3: Access response via choices[0].message.content (not .text)
                response = await self.llm_client.chat.completions.create(
                    model=self.generation_model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"[Agent Generation Error]: {e}")
            return f"Error: {e}"

    async def query(self, question: str) -> Dict:
        print(f"[{question[:15]}] -> Start _retrieve...")
        retrieval = await asyncio.to_thread(self._retrieve, question)
        print(f"[{question[:15]}] -> Finished _retrieve, starting _generate_answer...")
        answer = await self._generate_answer_async(question, retrieval["contexts"])
        print(f"[{question[:15]}] -> Finished _generate_answer.")

        return {
            "answer": answer,
            "contexts": retrieval["contexts"],
            "retrieved_ids": retrieval["retrieved_ids"],
            "metadata": {
                "model": self.generation_model,
                "embedding_model": self.embedding_model,
                "tokens_used": None,
                "sources": retrieval["sources"],
                "retrieval_distances": retrieval["distances"],
            },
        }

if __name__ == "__main__":
    agent = MainAgent()

    async def test():
        resp = await agent.query("Làm thế nào để đổi mật khẩu?")
        print(resp)

    asyncio.run(test())