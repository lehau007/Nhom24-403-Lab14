# Reflection - Le Van Hau (Member 3 - DevOps & Analyst)

## 1. Role & Contribution
Trong dự án này, tôi đảm nhiệm vai trò **Thành viên 3 (DevOps & Analyst)**, chịu trách nhiệm điều phối kỹ thuật và đảm bảo tính ổn định của pipeline đánh giá. Các đóng góp chính bao gồm:

- **Lập kế hoạch & Điều phối (Group Planning):** Trực tiếp xây dựng lộ trình thực hiện 4 giai đoạn, phân chia vai trò cụ thể cho các thành viên (Data Engineer, AI Engineer) và quản lý tiến độ chung của nhóm.
- **DevOps & Repository Management:** Khởi tạo cấu trúc dự án, quản lý Repository trên GitHub, thiết lập môi trường phát triển chung và đảm bảo các file nhạy cảm (.env) không bị commit.
- **Xử lý API Rate Limit & Fault Tolerance:** Trực tiếp triển khai logic tự động bỏ qua (skip) và trả về giá trị lỗi khi gặp sự cố Server Disconnected hoặc API bị rate limit/lock quá lâu. Điều này giúp Pipeline benchmark chạy xuyên suốt 50+ cases mà không bị treo giữa chừng.
- **Thiết lập Regression Release Gate:** Xây dựng logic tự động so sánh kết quả giữa các phiên bản Agent (V1 vs V2), quyết định "Release" hoặc "Rollback" dựa trên các chỉ số Delta Analysis (Chất lượng/Chi phí/Hiệu năng).
- **Phân tích Failure Clustering:** Dẫn dắt buổi phân tích lỗi, thu thập dữ liệu từ `benchmark_results.json` để thực hiện "5 Whys", chỉ ra các vấn đề về "Ground Truth Mismatch" và chiến lược chunking.
- **Tài liệu hóa (Documentation):** Hoàn thiện tài liệu cuối cùng, file `plan.md` và các báo cáo tổng hợp để đảm bảo tính chuyên nghiệp của sản phẩm.

## 2. Key Learnings
- **Quản lý rủi ro API:** Việc làm việc với LLMs ở quy mô lớn (50+ cases song song) đòi hỏi cơ chế xử lý lỗi và giới hạn tốc độ (rate limiting) cực kỳ chặt chẽ để đảm bảo hệ thống không bị đổ vỡ.
- **Tầm quan trọng của Release Gate:** Hiểu rõ cách sử dụng con số (Metrics) để đưa ra quyết định kỹ thuật thay vì cảm tính. Việc tự động hóa quy trình so sánh giúp đẩy nhanh tốc độ iteration của nhóm.
- **Phối hợp nhóm:** Vai trò DevOps không chỉ là kỹ thuật mà còn là cầu nối, đảm bảo module của Data Engineer và AI Engineer khớp nối hoàn hảo trong `main.py`.

## 3. Future Improvements
- **CI/CD Integration:** Tích hợp pipeline đánh giá này vào GitHub Actions để tự động benchmark mỗi khi có Pull Request mới.
- **Dynamic Rate Limiting:** Phát triển cơ chế tự động điều chỉnh số lượng worker dựa trên phản hồi `429 Too Many Requests` từ Server thay vì chỉ sử dụng logic retry/skip đơn giản.
- **Cost Dashboard:** Xây dựng một dashboard trực quan để theo dõi chi phí và hiệu năng theo thời gian thực thay vì chỉ xuất file JSON.
