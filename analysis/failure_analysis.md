# Báo cáo Phân tích Thất bại & Quyết định Release (Failure Analysis & Release Gate)

## 1. Tổng quan Benchmark (Phiên bản Pure RAG)
- **Tổng số cases:** 50
- **Tỉ lệ Pass/Fail:** 45/5
- **Điểm RAGAS trung bình:**
    - Faithfulness: 0.90
    - Relevancy: 0.85
- **Điểm LLM-Judge trung bình:** 4.2 / 5.0
- **Trạng thái:** ✅ **APPROVE (RELEASED)** - Delta score +0.5 so với bản Multi-Agent cũ.

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Hallucination | 2 | Context chứa thông tin cũ và mới gây nhầm lẫn (v3 vs v4) |
| Incomplete | 2 | Tài liệu gốc bị thiếu thông tin chi tiết về trường hợp ngoại lệ |
| Retrieval Miss | 1 | Câu hỏi quá ngắn, Vector search không đạt độ tương đồng cao |

## 3. Phân tích 5 Whys (Case tệ nhất: Phân biệt Refund v3 và v4)
1. **Symptom:** Agent lấy nhầm ngày hiệu lực của bản v3 thay vì v4.
2. **Why 1:** Cả hai văn bản đều có trong Top-K retrieval kết quả.
3. **Why 2:** LLM ưu tiên thông tin xuất hiện ở chunk đầu tiên.
4. **Why 3:** Vector DB tìm thấy v3 có độ tương đồng keyword cao hơn câu hỏi.
5. **Why 4:** Không có logic lọc metadata theo phiên bản mới nhất.
6. **Root Cause:** Thiếu bước Metadata Filtering hoặc Reranking để ưu tiên tài liệu mới nhất.

## 4. Kế hoạch cải tiến (Action Plan)
- [x] Chuyển đổi từ Multi-Agent phức tạp sang Pure RAG để giảm độ trễ (Latency).
- [ ] Triển khai Cohere Reranker để cải thiện độ chính xác bước Retrieval.
- [ ] Thêm logic phân loại câu hỏi (Classification) để lọc tài liệu theo Metadata Version.
