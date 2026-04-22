# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Mục tiêu và phạm vi
- So sánh 2 phiên bản agent trên cùng bộ 50 test cases:
    - **V1 (Baseline):** retrieve `top_k=1`
    - **V2 (Optimized):** retrieve `top_k=3`
- Nguồn dữ liệu: `reports/summary.json` và `reports/benchmark_results.json` (kết quả mới nhất).

## 2. Kết quả tổng quan so sánh V1 vs V2

| Chỉ số | V1 (`top_k=1`) | V2 (`top_k=3`) | Delta (V2 - V1) |
|---|---:|---:|---:|
| Tổng số cases | 50 | 50 | 0 |
| Pass | 34 | 38 | **+4** |
| Fail | 16 | 12 | **-4** |
| Error | 0 | 0 | 0 |
| Avg LLM-Judge Score | 3.74 | 4.07 | **+0.33** |
| Judge Agreement Rate | 0.91 | 0.88 | -0.03 |
| Retrieval Hit Rate | 0.46 | 0.94 | **+0.48** |
| Retrieval MRR | 0.46 | 0.66 | **+0.20** |
| RAGAS Faithfulness | 1.00 | 1.00 | 0.00 |
| RAGAS Relevancy | 0.40 | 0.87 | **+0.47** |
| Avg Latency (s) | 1.78 | 2.48 | +0.69 |

### Kết luận nhanh
- V2 cải thiện rõ rệt về **retrieval quality** (Hit Rate/MRR) và **answer quality** (Judge score, Relevancy).
- Trade-off: **latency tăng** và **agreement giữa judge giảm nhẹ**.
- Theo regression hiện tại: **APPROVE**.

## 3. Failure Clustering (theo dữ liệu mới)

### 3.1. Phân bố fail theo nhóm tài liệu

**V1 (`top_k=1`) - 16 fail**
- access_control_sop: 4
- hr_leave_policy: 4
- sla_p1_2026: 4
- it_helpdesk_faq: 2
- policy_refund_v4: 2

**V2 (`top_k=3`) - 12 fail**
- hr_leave_policy: 4
- policy_refund_v4: 4
- it_helpdesk_faq: 2
- access_control_sop: 2

### 3.2. Phân loại nguyên nhân lỗi chính

**V1 (`top_k=1`)**
- Retrieval miss (`hit_rate=0`): **16/16 fail**
- Off-target answer (trả lời lệch đoạn được hỏi): **10/16 fail**
- Missing detail (thiếu ý quan trọng): **9/16 fail**

**V2 (`top_k=3`)**
- Retrieval miss (`hit_rate=0`): **1/12 fail**
- Off-target answer: **5/12 fail**
- Missing detail: **4/12 fail**

### 3.3. Diễn giải
- Khi tăng `top_k` từ 1 lên 3, lỗi do retrieval miss gần như được triệt tiêu (16 -> 1).
- Phần fail còn lại của V2 tập trung nhiều hơn vào **generation grounding**: trả lời rộng nhưng lệch focus câu hỏi hoặc thiếu chi tiết yêu cầu.

## 4. Phân tích chuyển trạng thái giữa 2 version

- Pairwise theo cùng index test case:
    - **Improved (điểm tăng):** 23 cases
    - **Worsened (điểm giảm):** 12 cases
    - **Giữ nguyên:** 15 cases

### 4.1. Mẫu cải thiện tiêu biểu (V1 fail -> V2 pass)
- Các case index: 2, 3, 9, 12, 14 có mức tăng điểm lần lượt: +2.0, +3.0, +3.0, +2.5, +2.0.
- Đặc điểm chung: câu hỏi cần đúng đoạn/chủ đề nhỏ trong tài liệu; V1 thường lấy nhầm chunk, V2 lấy đủ ngữ cảnh hơn nên trả lời trúng ý hơn.

### 4.2. Mẫu thoái lui tiêu biểu (V1 pass -> V2 fail)
- Các case index: 7, 10, 25, 31, 34 có mức giảm điểm lần lượt: -3.0, -1.5, -3.0, -3.0, -1.0.
- Đặc điểm chung: V2 đôi lúc “mở rộng” nội dung quá mức (do nhiều chunk hơn), làm giảm tính tập trung vào đoạn được yêu cầu cụ thể.

## 5. 5 Whys (theo lỗi còn lại của V2)

### Case A: Trả lời lệch đoạn được hỏi (Off-target)
1. **Symptom:** Câu trả lời đúng về mặt nội dung chung nhưng không đúng “đoạn liên quan” của câu hỏi.
2. **Why 1:** Với `top_k=3`, context rộng hơn nên model có nhiều hướng trả lời.
3. **Why 2:** Prompt chưa ép đủ mạnh việc ưu tiên đúng section/intent trong câu hỏi.
4. **Why 3:** Chưa có bước chọn evidence theo cấp độ section-level trước khi generate.
5. **Why 4:** Chưa có post-check bắt buộc kiểm tra “answer-to-question focus”.
6. **Root Cause:** Thiếu cơ chế grounding theo intent/section, khiến câu trả lời có thể đúng nhưng không đúng trọng tâm.

### Case B: Thiếu chi tiết bắt buộc (Missing detail)
1. **Symptom:** Trả lời đúng khung chính nhưng thiếu điều kiện/ngoại lệ quan trọng.
2. **Why 1:** Model tóm tắt quá mạnh khi context dài.
3. **Why 2:** Chưa có checklist các slot thông tin bắt buộc theo loại câu hỏi.
4. **Why 3:** Không có bước self-critique trước khi trả lời final.
5. **Why 4:** Expected answer trong golden set một số nơi nhấn mạnh chi tiết nhỏ nhưng prompt hiện tại chưa match chiến lược chấm.
6. **Root Cause:** Thiếu schema trả lời theo yêu cầu thông tin và thiếu bước tự kiểm tra độ bao phủ trước khi output.

### Case C: Disagreement giữa judge tăng nhẹ
1. **Symptom:** Agreement Rate giảm từ 0.91 xuống 0.88.
2. **Why 1:** V2 cho câu trả lời dài hơn và giàu thông tin hơn, tạo biên độ diễn giải lớn hơn giữa các judge.
3. **Why 2:** Một số câu trả lời “đúng nhưng thừa” dễ bị judge đánh giá khác nhau (coverage vs strictness).
4. **Why 3:** Rubric judge chưa chuẩn hóa đủ mức phạt cho nội dung dư hoặc lệch nhẹ trọng tâm.
5. **Why 4:** Thiếu calibration định kỳ giữa các model judge.
6. **Root Cause:** Độ mở trong tiêu chí chấm khiến variance tăng khi câu trả lời nhiều thông tin.

## 6. Kế hoạch cải tiến (Action Plan)

- [x] Nâng retrieve từ `top_k=1` lên `top_k=3` để tăng recall retrieval.
- [ ] Thêm reranking (cross-encoder) để ưu tiên chunk đúng section/intent thay vì chỉ semantic gần nghĩa.
- [ ] Bổ sung prompt ràng buộc: trả lời đúng đoạn được hỏi trước, sau đó mới mở rộng nếu cần.
- [ ] Thêm bước answer validation: kiểm tra đủ các slot thông tin bắt buộc (điều kiện, ngoại lệ, timeline, owner).
- [ ] Chuẩn hóa rubric judge cho các trường hợp “đúng nhưng dư” để giảm disagreement.
- [ ] Rà soát lại golden set ở các case có ambiguity cao để giảm nhiễu khi đánh giá regression.

## 7. Kết luận
- So với baseline `top_k=1`, phiên bản `top_k=3` cho hiệu năng tốt hơn rõ rệt ở cả retrieval và chất lượng trả lời tổng thể.
- Failure hiện tại không còn chủ yếu ở retrieval, mà chuyển sang bài toán **focus và coverage trong generation**.
- Hướng tối ưu tiếp theo nên tập trung vào **reranking + grounding theo intent + self-check trước khi trả lời**.
