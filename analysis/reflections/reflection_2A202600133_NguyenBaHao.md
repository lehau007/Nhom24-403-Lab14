# BÁO CÁO CÁ NHÂN (REFLECTION) - LAB 14
**Vị trí:** AI/Backend Engineer

**Họ và tên:** Nguyễn Bá Hào - 2A202600133

## 1. Công việc đã thực hiện
Trong Sprint này, tôi chịu trách nhiệm chính về phần Core Logic cho việc đánh giá hệ thống:
*   **Xây dựng Multi-Judge Engine (`engine/llm_judge.py`):** Triển khai thành công việc gọi song song 2 mô hình (Gemma 3 và GPT-4o-mini) để chấm điểm câu trả lời. Thiết lập logic tính toán độ đồng thuận (Consensus) và theo dõi chi phí (Cost Tracking) thực tế cho từng lượt chạy.
*   **Phát triển Async Runner (`engine/runner.py`):** Tối ưu hóa hiệu năng hệ thống bằng lập trình bất đồng bộ (`asyncio`), cho phép chạy nhiều test case cùng lúc theo từng Batch để tiết kiệm thời gian mà vẫn tránh được lỗi Rate Limit.
*   **Tích hợp & Chạy thử nghiệm:** Kết nối thành công luồng dữ liệu từ Agent -> Evaluator -> Judge. Đã tiến hành chạy thử nghiệm 5 cases mẫu.
*   **Tương thích hệ thống:** Trực tiếp sửa lỗi phiên bản Python bằng cách thay thế `datetime.UTC` thành `datetime.now(timezone.utc)` trong các module lõi để đảm bảo hệ thống vận hành trơn tru trên Python 3.10.

## 2. Thách thức và Giải pháp
*   **Thách thức 1: Giới hạn Rate Limit (429 Error):** Khi chạy song song nhiều yêu cầu API đến Google/OpenAI, hệ thống dễ bị từ chối do vượt ngưỡng.
    *   *Giải pháp:* Triển khai cơ chế Batching kết hợp `asyncio.sleep(10)` giữa các đợt gọi, giúp duy trì tốc độ ổn định mà không làm gián đoạn pipeline.
*   **Thách thức 2: Bias của mô hình chấm điểm:** Một model đơn lẻ thường có xu hướng chấm điểm "hiền" hoặc bị ảnh hưởng bởi vị trí thông tin (Position Bias).
    *   *Giải pháp:* Sử dụng Multi-Judge Consensus. Yêu cầu Judge cung cấp `reasoning` (giải trình) trước khi đưa ra `score` để ép model suy luận logic, đồng thời tính toán `agreement_rate` để phát hiện các trường hợp chấm điểm mâu thuẫn.

## 3. Bài học kinh nghiệm
*   **Định lượng thay vì định tính:** Không nên chỉ tin vào một câu trả lời của AI chỉ vì nó trôi chảy. Các chỉ số như **MRR (Mean Reciprocal Rank)** là bằng chứng khách quan để đánh giá một hệ thống RAG có đang hoạt động thực sự hay không.
*   **Quản lý phụ thuộc:** Cần kiểm soát chặt chẽ `requirements.txt` ngay từ đầu. Việc thiếu thư viện khi deploy là bài học lớn về việc quản lý môi trường nhất quán giữa các thành viên.

## 4. Tự đánh giá
*   **Mức độ hoàn thành công việc:** đã hoàn thành công việc được giao trong plan(Mã nguồn cho Judge và Runner đã hoàn thiện, hoạt động đúng logic và xuất được báo cáo thực tế).
*   **Kỹ năng kỹ thuật:** Làm quen với kỹ thuật `asyncio` và tích hợp đa nền tảng API (Google, OpenAI). Hiểu biết các chỉ số đánh giá nâng cao (Cohen's Kappa, Position Bias).
*   **Đóng góp cho nhóm:** Đã cung cấp công cụ "thước đo" chuẩn xác để nhóm nhìn thấy lỗ hổng trong phần dữ liệu (Retrieval), giúp định hướng lại công việc cho giai đoạn tối ưu.
*   **Điểm tự chấm:** 35/40 (Trừ 5 điểm do chưa hoàn thiện "reasoning" trong llm_judge.py được thành viên trong nhóm hỗ trợ góp ý).

---
**Người báo cáo:** Nguyễn Bá Hào
