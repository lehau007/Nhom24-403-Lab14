# Báo cáo Cá nhân (Reflection)
**Họ và tên:** Ngô Anh Tú
**MSSV:** 2A202600128
**Vai trò:** Thành viên 1 - Data Engineer (Retrieval & SDG)

## 1. Công việc đã thực hiện
- **Xây dựng bộ dữ liệu Golden Set:**
    - Sử dụng kỹ thuật **Synthetic Data Generation (SDG)** với phương pháp Multi-Provider (kết hợp GPT-4o-mini và Gemini-1.5-Flash) để tạo ra 50 cặp Question-Answer.
    - Thiết kế các loại câu hỏi đa dạng: 20 câu **Standard** (factual) và 30 câu **Hard/Adversarial** (Multi-hop, Temporal Conflict, Ambiguous).
    - Đảm bảo mỗi case đều có `expected_retrieval_ids` (Ground Truth) để phục vụ việc đánh giá bước tìm kiếm.
- **Xây dựng hệ thống đánh giá Retrieval:**
    - Code module `engine/retrieval_eval.py` để tính toán **Hit Rate** (đánh giá khả năng tìm thấy tài liệu đúng trong Top-k) và **MRR (Mean Reciprocal Rank)** (đánh giá vị trí của tài liệu đúng trong danh sách trả về).
    - Tích hợp framework **Ragas** để đo lường thêm độ trung thực (Faithfulness) và mức độ liên quan (Answer Relevancy) của câu trả lời.

## 2. Thách thức và Giải pháp
- **Thách thức:** Các câu hỏi Multi-hop yêu cầu thông tin từ nhiều file khác nhau khiến Retriever thường chỉ tìm được một phần thông tin.
- **Giải pháp:** Tôi đã đề xuất với nhóm tăng `RETRIEVAL_TOP_K` lên 5 và bổ sung trường metadata `source` vào dữ liệu để giúp Agent dễ dàng định vị tài liệu hơn.

## 3. Bài học kinh nghiệm
- Hiểu rõ sự khác biệt giữa các metrics đánh giá Retrieval (Hit Rate/MRR) và Generation (Ragas/LLM Judge).
- Kỹ thuật viết prompt cho SDG cực kỳ quan trọng để tạo ra được các "Hard cases" thực sự chất lượng, tránh việc LLM sinh ra các câu hỏi quá dễ hoặc không sát thực tế.

## 4. Tự đánh giá
- Hoàn thành 100% khối lượng công việc được giao trong Plan.
- Bộ dữ liệu Golden Set đạt chất lượng tốt, giúp nhóm phát hiện ra điểm yếu của hệ thống RAG hiện tại ở các case tìm kiếm phức tạp.
