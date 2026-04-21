# Project Plan: AI Evaluation Factory

## 🕒 Lịch trình thực hiện (4 Tiếng)

- **Giai đoạn 1: Chuẩn bị & Dữ liệu (45 phút)**
    *   **Thành viên 1 (Data):** Bắt tay ngay vào viết script tạo dữ liệu trong `data/synthetic_gen.py`. Đảm bảo sinh ra file `data/golden_set.jsonl` đúng format và đủ 50 cases. 
    *   **Thành viên 2 (AI):** Cài đặt các thư viện cần thiết (`requirements.txt`), setup API Keys (nhớ đưa vào `.env` và không commit file này). Khởi tạo prompt và framework cơ bản cho `engine/llm_judge.py`.
    *   **Thành viên 3 (DevOps):** Khởi tạo Repository trên GitHub/GitLab, thêm các thành viên vào repo. Chỉnh sửa `main.py` để chuẩn bị pipeline gọi các module. Tìm hiểu định dạng đầu ra mong muốn của `check_lab.py`.

- **Giai đoạn 2: Phát triển Eval Engine (90 phút)**
    *   Phát triển các module RAGAS, Custom Judge và Async Runner để xử lý song song.

- **Giai đoạn 3: Chạy Benchmark & Phân tích lỗi (60 phút)**
    *   **Cả nhóm:** Cùng nhau chạy `python main.py` từ đầu đến cuối. Đảm bảo hệ thống xuất ra được 2 file `reports/summary.json` và `reports/benchmark_results.json`.
    *   **Thành viên 3 (DevOps):** Dẫn dắt việc phân cụm lỗi (Failure Clustering). Thu thập các câu trả lời sai/điểm thấp để phân tích "5 Whys".

- **Giai đoạn 4: Tối ưu & Nộp bài (45 phút)**
    *   **Thành viên 1 & 2:** Thử nghiệm thay đổi prompt của Agent (trong `agent/main_agent.py` nếu có) hoặc điều chỉnh cấu hình Retrieval/Judge để xem điểm số có cải thiện và vượt qua được Release Gate của Thành viên 3 hay không.
    *   **Cả nhóm:** Tự viết báo cáo reflection cá nhân (`analysis/reflections/reflection_[Tên_SV].md`).
    *   **Thành viên 3 (DevOps):** Chạy `python check_lab.py` lần cuối trước khi nộp bài.

---

## 🛠️ Các nhiệm vụ chính (Expert Mission)

### 1. Retrieval & SDG (Nhóm Data)
- **Retrieval Eval:** Tính toán Hit Rate và MRR cho Vector DB. Bạn phải chứng minh được Retrieval stage hoạt động tốt trước khi đánh giá Generation.
- **SDG:** Tạo 50+ cases, bao gồm cả Ground Truth IDs của tài liệu để tính Hit Rate.

### 2. Multi-Judge Consensus Engine (Nhóm AI/Backend)
- **Consensus logic:** Sử dụng ít nhất 2 model Judge khác nhau. 
- **Calibration:** Tính toán hệ số đồng thuận (Agreement Rate) và xử lý xung đột điểm số tự động.

### 3. Regression Release Gate (Nhóm DevOps/Analyst)
- **Delta Analysis:** So sánh kết quả của Agent phiên bản mới với phiên bản cũ.
- **Auto-Gate:** Viết logic tự động quyết định "Release" hoặc "Rollback" dựa trên các chỉ số Chất lượng/Chi phí/Hiệu năng.

---

## 👥 Phân chia vai trò (Roles & Responsibilities)

*   **Thành viên 1: Data Engineer (Tập trung vào Dữ liệu & Tìm kiếm)**
    *   **Nhiệm vụ:** Chịu trách nhiệm phần Retrieval & SDG.
    *   **File làm việc chính:** `data/synthetic_gen.py`, `engine/retrieval_eval.py`.
    *   **Mục tiêu:** Tạo ra Golden Dataset chất lượng cao (50+ cases) và tối ưu hóa Hit Rate/MRR cho Vector DB.

*   **Thành viên 2: AI Engineer (Tập trung vào Logic Đánh giá)**
    *   **Nhiệm vụ:** Phát triển Multi-Judge Consensus Engine và Async Runner.
    *   **File làm việc chính:** `engine/llm_judge.py`, `engine/runner.py`.
    *   **Mục tiêu:** Xây dựng hệ thống đánh giá khách quan, xử lý xung đột điểm số tự động.

*   **Thành viên 3: DevOps & Analyst (Tập trung vào Pipeline & Release Gate)**
    *   **Nhiệm vụ:** Quản lý Repo, thiết lập Regression Release Gate và phân tích Failure Clustering.
    *   **File làm việc chính:** `main.py`, `check_lab.py`, `analysis/failure_analysis.md`.
    *   **Mục tiêu:** Đảm bảo pipeline chạy mượt mà, tự động hóa quyết định Release/Rollback dựa trên metrics.
