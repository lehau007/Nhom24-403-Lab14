import asyncio
import os
from typing import Any, Dict, List

from datasets import Dataset
from dotenv import load_dotenv
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import _answer_relevancy, _faithfulness

load_dotenv(override=True)


class RetrievalEvaluator:
    def __init__(self):
        # 1. Chuẩn bị cấu hình model từ .env
        judge_provider = os.getenv("JUDGE_1_PROVIDER", "openai")
        judge_model = os.getenv("JUDGE_1_MODEL", "gpt-4o-mini")

        embed_provider = os.getenv("RETRIEVAL_PROVIDER", "gemini")
        embed_model = os.getenv("RETRIEVAL_MODEL", "gemini-embedding-2-preview")

        self.llm_path = f"{judge_provider}/{judge_model}" if "/" not in judge_model else judge_model
        self.emb_path = f"{embed_provider}/{embed_model}" if "/" not in embed_model else embed_model

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        if not expected_ids or not retrieved_ids:
            return 0.0
        return 1.0 if any(doc_id in retrieved_ids[:top_k] for doc_id in expected_ids) else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        if not expected_ids or not retrieved_ids:
            return 0.0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    async def score(self, case: Dict[str, Any], resp: Dict[str, Any]) -> Dict[str, Any]:
        """
        Đánh giá an toàn luồng sử dụng Ragas.
        """
        retrieved_ids = resp.get("retrieved_ids", [])
        expected_ids = case.get("expected_retrieval_ids", [])

        hit_rate = self.calculate_hit_rate(expected_ids, retrieved_ids)
        mrr = self.calculate_mrr(expected_ids, retrieved_ids)

        # 1. Chuẩn bị Dataset (Ragas yêu cầu list cho mỗi field)
        data = {
            "question": [case["question"]],
            "answer": [resp["answer"]],
            "contexts": [[c for c in resp.get("contexts", [])]],
            "ground_truth": [case.get("expected_answer", "")],
        }
        dataset = Dataset.from_dict(data)

        try:
            from langchain_litellm import ChatLiteLLM, LiteLLMEmbeddings

            # 2. Khởi tạo đối tượng LLM và Embeddings ĐỘC LẬP cho mỗi request
            llm_obj = ChatLiteLLM(model=self.llm_path, temperature=0)
            emb_obj = LiteLLMEmbeddings(model=self.emb_path)

            ragas_llm = LangchainLLMWrapper(llm_obj)
            ragas_emb = LangchainEmbeddingsWrapper(emb_obj)

            # 3. Khởi tạo mới các Metric để tránh 'llm must be set' error

            loop = asyncio.get_event_loop()
            # Thực thi Ragas trong thread pool
            result = await loop.run_in_executor(
                None,
                lambda: evaluate(
                    dataset, metrics=[_faithfulness, _answer_relevancy], llm=ragas_llm, embeddings=ragas_emb
                ),
            )

            # 4. Trích xuất kết quả an toàn
            res_df = result.to_pandas()
            faith_score = float(res_df["faithfulness"].iloc[0])
            relevancy_score = float(res_df["answer_relevancy"].iloc[0])

            # Xử lý trường hợp Ragas trả về NaN
            import math

            if math.isnan(faith_score):
                faith_score = 0.0
            if math.isnan(relevancy_score):
                relevancy_score = 0.0

        except Exception as e:
            print(f"!!! Ragas Evaluation Error: {e}")
            faith_score = 0.0
            relevancy_score = 0.0

        return {
            "faithfulness": faith_score,
            "relevancy": relevancy_score,
            "retrieval": {"hit_rate": hit_rate, "mrr": mrr},
        }
