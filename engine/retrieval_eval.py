from typing import List

class RetrievalEvaluator:
    def __init__(self):
        pass

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        Hit Rate: 1 if at least one expected_id is in retrieved_ids, else 0.
        """
        if not expected_ids:
            return 1.0
        
        # Ensure we are comparing strings
        expected_ids = [str(x) for x in expected_ids]
        retrieved_ids = [str(x) for x in retrieved_ids]
        
        hits = any(eid in retrieved_ids for eid in expected_ids)
        return 1.0 if hits else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        Mean Reciprocal Rank: 1/rank of the first correct retrieval.
        """
        if not expected_ids:
            return 1.0
            
        expected_ids = [str(x) for x in expected_ids]
        retrieved_ids = [str(x) for x in retrieved_ids]
        
        for i, rid in enumerate(retrieved_ids):
            if rid in expected_ids:
                return 1.0 / (i + 1)
        return 0.0
