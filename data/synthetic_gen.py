import json
import asyncio
import os
import glob
from typing import List, Dict
import litellm
from dotenv import load_dotenv
import random

load_dotenv(override=True)

class SyntheticGenerator:
    def __init__(self):
        self.docs = self._load_docs()
        # Multi-provider setup
        self.providers = []
        
        # Provider 1: Lấy từ JUDGE_1 hoặc fallback về SYNTHESIS
        p1 = os.getenv("JUDGE_1_PROVIDER", os.getenv("SYNTHESIS_PROVIDER", "openai"))
        m1 = os.getenv("JUDGE_1_MODEL", os.getenv("SYNTHESIS_MODEL", "gpt-4o-mini"))
        self.providers.append(f"{p1}/{m1}" if "/" not in m1 else m1)
        
        # Provider 2: Lấy từ JUDGE_2 (thường là Gemini/Anthropic để đa dạng)
        p2 = os.getenv("JUDGE_2_PROVIDER")
        m2 = os.getenv("JUDGE_2_MODEL")
        if p2 and m2:
            self.providers.append(f"{p2}/{m2}" if "/" not in m2 else m2)
        else:
            # Nếu không có JUDGE_2, dùng lại Provider 1
            self.providers.append(self.providers[0])

    def _load_docs(self) -> Dict[str, str]:
        docs = {}
        for file_path in glob.glob("data/docs/*.txt"):
            filename = os.path.basename(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                docs[filename] = f.read()
        return docs

    async def generate_standard_qa(self, doc_name: str, text: str, provider_idx: int = 0, num_pairs: int = 1) -> List[Dict]:
        """Tạo các câu hỏi factual đơn giản."""
        model_path = self.providers[provider_idx % len(self.providers)]
        prompt = f"""Dựa trên tài liệu '{doc_name}' dưới đây, hãy tạo {num_pairs} cặp Câu hỏi và Câu trả lời.
Tài liệu:
{text[:3000]}

Yêu cầu format JSON:
{{
  "qa_pairs": [
    {{
      "question": "...", 
      "expected_answer": "...", 
      "context": "Trích đoạn ngắn từ tài liệu chứa câu trả lời", 
      "expected_retrieval_ids": ["{doc_name}"],
      "metadata": {{"difficulty": "easy", "type": "fact-check", "source": "{doc_name}"}}
    }}
  ]
}}
"""
        try:
            response = await litellm.acompletion(
                model=model_path,
                messages=[{"role": "system", "content": f"You are AI Provider {provider_idx + 1} generating factual QA pairs."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("qa_pairs", [])
        except Exception as e:
            print(f"Error generating standard QA (Provider {model_path}) for {doc_name}: {e}")
            return []

    async def generate_hard_qa(self, doc_name: str, text: str, all_docs: Dict[str, str], provider_idx: int = 1, num_pairs: int = 2) -> List[Dict]:
        """Tạo các câu hỏi lừa, khó, multi-hop."""
        model_path = self.providers[provider_idx % len(self.providers)]
        # Chọn ngẫu nhiên một tài liệu khác để làm multi-hop
        other_doc_name = random.choice([k for k in all_docs.keys() if k != doc_name])
        other_text = all_docs[other_doc_name]

        prompt = f"""Bạn là một chuyên gia kiểm thử AI (QA Engineer). Nhiệm vụ của bạn là tạo ra các câu hỏi CỰC KHÓ và LỪA để đánh giá hệ thống RAG.

Sử dụng thông tin từ hai tài liệu sau:
Tài liệu 1 ({doc_name}):
{text[:2000]}

Tài liệu 2 ({other_doc_name}):
{other_text[:2000]}

Hãy tạo {num_pairs} câu hỏi thuộc các loại sau:
1. Multi-hop: Cần kết hợp thông tin từ cả 2 tài liệu mới trả lời được.
2. Temporal/Version Conflict: Hỏi về các mâu thuẫn giữa phiên bản cũ và mới (ví dụ Refund v3 vs v4).
3. Negative Constraint: Hỏi về những gì KHÔNG được phép hoặc các ngoại lệ (Exceptions).
4. Ambiguous/Edge Case: Câu hỏi mập mờ hoặc ở biên của chính sách.
5. Hallucination Check: Đưa ra một giả định sai trong câu hỏi để xem AI có bị lừa không.

Yêu cầu format JSON:
{{
  "qa_pairs": [
    {{
      "question": "...", 
      "expected_answer": "...", 
      "context": "Đoạn text chứa thông tin từ cả hai tài liệu hoặc logic bắc cầu", 
      "expected_retrieval_ids": ["{doc_name}", "{other_doc_name}"],
      "metadata": {{
        "difficulty": "hard", 
        "type": "multi-hop|adversarial|edge-case",
        "source": "{doc_name}, {other_doc_name}"
      }}
    }}
  ]
}}
"""
        try:
            response = await litellm.acompletion(
                model=model_path,
                messages=[{"role": "system", "content": f"You are AI Provider {provider_idx + 1} acting as an adversarial evaluator."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("qa_pairs", [])
        except Exception as e:
            print(f"Error generating hard QA (Provider {model_path}) for {doc_name}: {e}")
            return []

async def main():
    gen = SyntheticGenerator()
    all_qa = []
    
    print(f"Starting synthetic generation using Multi-Provider setup...")
    print(f"Active Providers: {gen.providers}")
    
    tasks = []
    # Lặp qua các tài liệu và phân bổ provider luân phiên
    for i, (doc_name, text) in enumerate(gen.docs.items()):
        # Mỗi document tạo 4 câu dễ và 6 câu khó (Tổng 10 câu/doc)
        # Với 5 docs hiện có, tổng cộng sẽ là 50 câu.
        tasks.append(gen.generate_standard_qa(doc_name, text, provider_idx=i, num_pairs=4))
        tasks.append(gen.generate_hard_qa(doc_name, text, gen.docs, provider_idx=i+1, num_pairs=6))
    
    print(f"Running {len(tasks)} generation tasks concurrently...")
    results = await asyncio.gather(*tasks)
    
    for batch in results:
        if batch:
            all_qa.extend(batch)

    # Đảm bảo thư mục tồn tại
    os.makedirs("data", exist_ok=True)
    
    output_path = "data/golden_set.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for pair in all_qa:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
            
    print(f"Done! Generated {len(all_qa)} QA pairs to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
