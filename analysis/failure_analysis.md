# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark
- **Tổng số cases:** 50
- **Tỉ lệ Pass/Fail/Error:** 38/10/2 (Fail status: 10, Error status: 2)
- **Điểm RAGAS trung bình:**
    - Faithfulness: 0.96
    - Relevancy: 0.83
- **Chỉ số Retrieval:**
    - Hit Rate: 0.90
    - Average MRR: 0.62
- **Điểm LLM-Judge trung bình:** 3.96 / 5.0
- **Agreement Rate (Giữa các Judge):** 88.5%
- **Latency trung bình:** 5.81s
- **Token usage ước tính (Total 50 cases):** ~185,000 tokens
- **Chi phí ước tính:** ~$0.02 (Dựa trên Gemma-3 pricing. Thực ra là nhóm em đang dùng API free, nên cũng chưa rõ giá thực tế)
- **Tốc độ thực thi:** Toàn bộ benchmark hoàn thành trong < 2 phút (Async mode enabled)

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Evaluation Bias / GT Mismatch | 7 | Golden Set có expected_answer quá hẹp (chỉ lấy 1 chunk) trong khi Agent trả lời đầy đủ dựa trên 3-5 chunks, dẫn đến Judge chấm "Inaccurate" sai. |
| Hallucination (Real) | 3 | Agent suy diễn thông tin không có trong tài liệu hoặc trộn lẫn thông tin giữa các phiên bản policy khác nhau. |
| System Error | 2 | Server API (Google GenAI) bị ngắt kết nối giữa chừng (Server disconnected). |

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)

### Case #1: Hỏi về ngoại lệ chính sách không áp dụng
1. **Symptom:** Agent trả lời không có ngoại lệ, trong khi thực tế có.
2. **Why 1:** LLM không thấy thông tin ngoại lệ trong context truyền vào.
3. **Why 2:** Vector DB không đưa đoạn văn chứa ngoại lệ vào top danh sách search.
4. **Why 3:** Từ khóa câu hỏi có "ngoại lệ" nhưng văn bản lại ghi "lưu ý khác" hoặc "trường hợp loại trừ", khoảng cách ngữ nghĩa (semantic distance) khá xa.
5. **Why 4:** Chưa có công đoạn re-ranking bằng cross-encoder để cải thiện và đối chiếu sự tương đồng ngữ nghĩa một cách tỉ mỉ.
6. **Root Cause:** Quá phụ thuộc vào cơ chế Vector Search thuần tuý (dense embedding đôi lúc gặp nhược điểm với lexical gap).

### Case #2: Kết hợp thông tin 2 điều kiện từ 2 quy định khác nhau
1. **Symptom:** Khách hàng hỏi điều kiện vay kép, Agent chỉ trả lời đúng 1 điều kiện.
2. **Why 1:** Agent chỉ focus (hội tụ) thông tin vào chunk đầu tiên.
3. **Why 2:** LLM judge đánh giá relevancy thấp với câu hỏi do thiếu vế sau.
4. **Why 3:** Ingestion chunking không liên kết tốt các đoạn dài. Khả năng kết nối multi-hop suy yếu khi một chunk lấn át các chunk còn lại.
5. **Why 4:** Context dồn dập khiến mô hình sinh gặp tình trạng "lost in the middle" (quên ý).
6. **Root Cause:** Nhược điểm của RAG cơ bản thiếu quy trình Multi-hop traversal, không có agent chuyên trách tổng hợp ý.

### Case #3: Trả lời sai thông tin tính toán chỉ số
1. **Symptom:** Agent cung cấp mức tính toán sai cho chính sách ưu đãi tích luỹ.
2. **Why 1:** Generation Model không thực sự giỏi suy luận toán học/logic tổng hợp thuần túy bằng prompt text.
3. **Why 2:** Hệ thống không cung cấp Tool Calling cho phép thực hiện phép tính.
4. **Why 3:** Design RAG hiện tại chỉ chuyên về QA tài liệu văn bản, chưa có module function calling chuyên việt.
5. **Why 4:** Agent base chỉ feed context dạng string vào cho một LLM.
6. **Root Cause:** Kiến trúc thiếu vắng Tool-use/ReAct agent nhằm thực thi các thao tác operation (tính toán, cross-check).

## 4. Kế hoạch cải tiến (Action Plan)
- [x] Thay đổi Chunking strategy từ Fixed-size sang Semantic Chunking kết hợp overlapping.
- [x] Nối rộng top_k = 3 lên top_k = 5 cho v2 agent để bao phủ ngữ cảnh lớn hơn.
- [ ] Tích hợp Reranking Layer (Cohere Rerank / BGE-M3 Reranker) giữa bước Retrieve và Generate.
- [ ] **Cải thiện Golden Set:** Cập nhật expected_answer để bao quát toàn bộ thông tin tài liệu thay vì chỉ focus vào 1 chunk duy nhất.
- [ ] Cập nhật System Prompt với chain-of-thought instructions: "Suy nghĩ từng bước, chỉ trả lời dựa vào context cung cấp, nếu có tính toán hãy phân tích cẩn thận".
- [ ] Nghiên cứu áp dụng quy trình Agentic RAG / ReAct để model có năng lực gọi function call.
