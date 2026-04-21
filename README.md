# 🚀 Lab Day 14: AI Evaluation Factory (Team Edition)

## 🎯 Tổng quan
"Nếu bạn không thể đo lường nó, bạn không thể cải thiện nó." — Nhiệm vụ của nhóm bạn là xây dựng một **Hệ thống đánh giá tự động** chuyên nghiệp để benchmark AI Agent. Hệ thống này phải chứng minh được bằng con số cụ thể: Agent đang tốt ở đâu và tệ ở đâu.

## 🔧 Hướng dẫn chạy nhanh (Quick Start)

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Cấu hình môi trường (Copy API Key vào file .env)
cp .env.example .env

# 3. Chạy toàn bộ Pipeline (Ingestion -> Benchmark -> Report)
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUNBUFFERED="1"; .\.venv\Scripts\python.exe main.py

# 4. Kiểm tra định dạng trước khi nộp
python check_lab.py
```

> [!IMPORTANT]
> **Cơ chế Xử lý Lỗi (Fault Tolerance):** Hệ thống đã được tích hợp logic tự động bỏ qua (skip) và trả về giá trị 0/Error khi gặp sự cố Server Disconnected hoặc API bị rate limit/lock quá lâu. Điều này đảm bảo pipeline benchmark không bị treo và vẫn xuất được báo cáo cuối cùng cho các case thành công.

---

## 📤 Danh mục nộp bài (Submission Checklist)
Nhóm nộp 1 đường dẫn Repository (GitHub/GitLab) chứa:
1. [x] **Source Code**: Toàn bộ mã nguồn hoàn chỉnh.
2. [x] **Reports**: File `reports/summary.json` và `reports/benchmark_results.json` (đã tạo thành công).
3. [x] **Group Report**: File `analysis/failure_analysis.md` (đã cập nhật số liệu thực tế).
4. [x] **Individual Reports**: Các file `analysis/reflections/reflection_2A202600110_LeVanHau.md` (đã hoàn thiện).

---

## 🏆 Bí kíp đạt điểm tuyệt đối (Expert Tips)

### ✅ Đánh giá Retrieval (15%)
Nhóm nào chỉ đánh giá câu trả lời mà bỏ qua bước Retrieval sẽ không thể đạt điểm tối đa. Bạn cần biết chính xác chunk nào đang gây ra lỗi Hallucination.

### ✅ Multi-Judge Reliability (20%)
Việc chỉ tin vào một Judge (ví dụ GPT-4o) là một sai lầm trong sản phẩm thực tế. Hãy chứng minh hệ thống của bạn khách quan bằng cách so sánh nhiều Judge model và tính toán độ tin cậy của chúng.

### ✅ Tối ưu hiệu năng & Chi phí (15%)
Hệ thống Expert phải chạy cực nhanh (Async) và phải có báo cáo chi tiết về "Giá tiền cho mỗi lần Eval". Hãy đề xuất cách giảm 30% chi phí eval mà không giảm độ chính xác.

### ✅ Phân tích nguyên nhân gốc rễ (Root Cause) (20%)
Báo cáo 5 Whys phải chỉ ra được lỗi nằm ở đâu: Ingestion pipeline, Chunking strategy, Retrieval, hay Prompting.

---

## ⚠️ Lưu ý
- **Không bắt buộc** chạy `python data/synthetic_gen.py` trước để tạo file `data/golden_set.jsonl`. File này đã được tạo sẵn trong repo. 
