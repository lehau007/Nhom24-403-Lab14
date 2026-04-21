import asyncio
import os
import sys
from agent.main_agent import MainAgent
from engine.retrieval_eval import RetrievalEvaluator

# Fix for Windows asyncio SSL issue
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def debug_retrieval():
    print("🔍 Đang kiểm tra chi tiết Retrieval...")
    agent = MainAgent()
    evaluator = RetrievalEvaluator()
    
    # Lấy thử 1 câu hỏi từ Golden Set
    question = "Chính sách hoàn tiền phiên bản 4 có hiệu lực từ ngày nào?"
    expected_ids = ["policy_refund_v4_0"]
    
    print(f"\nCâu hỏi: {question}")
    print(f"ID mong đợi: {expected_ids}")
    
    # Chạy query qua Agent
    resp = await agent.query(question)
    
    retrieved_chunks = resp.get("retrieved_ids", [])
    print(f"ID tìm được: {retrieved_chunks}")
    
    # Tính toán thủ công để kiểm tra logic
    hit = any(doc_id in retrieved_chunks[:3] for doc_id in expected_ids)
    print(f"Kết quả Hit Rate (Top 3): {'✅ PASS' if hit else '❌ FAIL'}")
    
    if not retrieved_chunks:
        print("\n⚠️ CẢNH BÁO: Agent không tìm thấy bất kỳ chunk nào. Có thể Database trống hoặc Collection name sai.")
    elif not hit:
        print("\n⚠️ CẢNH BÁO: Tìm thấy chunk nhưng không khớp ID. Có thể do ID trong DB được đánh số khác với Golden Set.")

if __name__ == "__main__":
    asyncio.run(debug_retrieval())
