from typing import List, Dict

class RetrievalEvaluator:
    def __init__(self):
        pass

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        """
        TODO: Tính toán xem ít nhất 1 trong expected_ids có nằm trong top_k của retrieved_ids không.
        """
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        TODO: Tính Mean Reciprocal Rank.
        Tìm vị trí đầu tiên của một expected_id trong retrieved_ids.
        MRR = 1 / position (vị trí 1-indexed). Nếu không thấy thì là 0.
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    def score(self, case: Dict, response: Dict, top_k: int = 3) -> Dict:
        expected_ids = case.get("expected_chunk_ids") or case.get("expected_retrieval_ids") or []
        retrieved_ids = response.get("retrieved_ids") or []

        hit_rate = self.calculate_hit_rate(expected_ids=expected_ids, retrieved_ids=retrieved_ids, top_k=top_k)
        mrr = self.calculate_mrr(expected_ids=expected_ids, retrieved_ids=retrieved_ids)

        overlap = len(set(expected_ids).intersection(set(retrieved_ids[:top_k])))
        faithfulness = 1.0 if response.get("contexts") else 0.0
        relevancy = min(1.0, overlap / max(1, min(top_k, len(expected_ids) or 1)))

        return {
            "faithfulness": faithfulness,
            "relevancy": relevancy,
            "retrieval": {
                "hit_rate": hit_rate,
                "mrr": mrr,
                "expected_ids": expected_ids,
                "retrieved_ids": retrieved_ids,
                "matched_ids": list(set(expected_ids).intersection(set(retrieved_ids))),
            },
        }

    async def evaluate_batch(self, dataset: List[Dict]) -> Dict:
        """
        Dataset cần có response.retrieved_ids và case.expected_chunk_ids.
        """
        if not dataset:
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0}

        hit_rates = []
        mrr_scores = []

        for item in dataset:
            expected = item.get("expected_chunk_ids") or item.get("expected_retrieval_ids") or []
            retrieved = item.get("retrieved_ids") or []
            hit_rates.append(self.calculate_hit_rate(expected, retrieved))
            mrr_scores.append(self.calculate_mrr(expected, retrieved))

        return {
            "avg_hit_rate": sum(hit_rates) / len(hit_rates),
            "avg_mrr": sum(mrr_scores) / len(mrr_scores),
        }
