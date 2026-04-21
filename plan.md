👥 Phân chia vai trò (Roles & Responsibilities)

   * Thành viên 1: Data Engineer (Tập trung vào Dữ liệu & Tìm kiếm)
       * Nhiệm vụ: Chịu trách nhiệm phần Retrieval & SDG.
       * File làm việc chính: data/synthetic_gen.py, engine/retrieval_eval.py.
       * Mục tiêu: Tạo ra Golden Dataset chất lượng (ít nhất 50 test cases kèm Ground Truth IDs) và xây dựng logic tính toán Hit Rate & MRR để đánh giá độ chính xác của bước Retrieval.

   * Thành viên 2: AI/Backend Engineer (Tập trung vào Đánh giá & Xử lý logic)
       * Nhiệm vụ: Phát triển Multi-Judge Consensus Engine.
       * File làm việc chính: engine/llm_judge.py, engine/runner.py.
       * Mục tiêu: Tích hợp ít nhất 2 model LLM làm Giám khảo (Judge), xây dựng logic đồng thuận (Consensus), xử lý các trường hợp giám khảo chấm lệch điểm nhau và tối ưu hóa thời gian chạy với Async Runner.

   * Thành viên 3: DevOps/Analyst Engineer (Tập trung vào Cổng kiểm duyệt & Phân tích)
       * Nhiệm vụ: Xây dựng Regression Release Gate & Phân tích nguyên nhân.
       * File làm việc chính: main.py, analysis/failure_analysis.md.
       * Mục tiêu: Viết logic tự động quyết định xem Agent có được "Release" hay "Rollback" dựa trên delta của các chỉ số (Chất lượng, Chi phí, Hiệu năng) so với phiên bản trước. Dẫn dắt quá trình phân tích "5 Whys" và xử lý lỗi ở cuối lab.

  ---

  🕒 Kế hoạch triển khai chi tiết (Timeline 4 Tiếng)

  Giai đoạn 1: Chuẩn bị & Dữ liệu (45 phút)
   * Thành viên 1 (Data): Bắt tay ngay vào viết script tạo dữ liệu trong data/synthetic_gen.py. Đảm bảo sinh ra
     file data/golden_set.jsonl đúng format và đủ 50 cases. 
   * Thành viên 2 (AI): Cài đặt các thư viện cần thiết (requirements.txt), setup API Keys (nhớ đưa vào .env và
     không commit file này). Khởi tạo prompt và framework cơ bản cho engine/llm_judge.py.
   * Thành viên 3 (DevOps): Khởi tạo Repository trên GitHub/GitLab, thêm các thành viên vào repo. Chỉnh sửa
     main.py để chuẩn bị pipeline gọi các module. Tìm hiểu định dạng đầu ra mong muốn của check_lab.py.

  Giai đoạn 2: Phát triển Core Engine (90 phút)
   * Thành viên 1 (Data): Sau khi có dữ liệu, chuyển sang code engine/retrieval_eval.py để tính toán các metrics
     (Hit Rate, MRR). Đảm bảo module này có thể nhận input từ Agent và trả ra con số chính xác.
   * Thành viên 2 (AI): Code logic Multi-Judge. Test thử một vài case xem 2 model có chấm điểm giống nhau không.
     Tối ưu code bằng Async trong engine/runner.py để hệ thống chạy cực nhanh. Cần tracking chi phí (giá tiền/lần
     eval).
   * Thành viên 3 (DevOps): Viết logic Auto-Gate trong main.py. So sánh kết quả của Agent (phiên bản hiện tại) so
     với một baseline cố định (phiên bản cũ) để quyết định Release. Hỗ trợ Thành viên 2 ghép nối runner.py vào
     main.py.

  Giai đoạn 3: Chạy Benchmark & Phân tích lỗi (60 phút)
   * Cả nhóm: Cùng nhau chạy python main.py từ đầu đến cuối. Đảm bảo hệ thống xuất ra được 2 file
     reports/summary.json và reports/benchmark_results.json.
   * Thành viên 3 (DevOps): Dẫn dắt việc phân cụm lỗi (Failure Clustering). Thu thập các câu trả lời sai/điểm thấp
     từ file kết quả.
   * Thành viên 1 & 2: Cùng Thành viên 3 phân tích "5 Whys" để tìm ra Root Cause (Lỗi do Chunking? Do Retrieval
     tệ? Hay do Prompt của Agent?). Cả nhóm cùng hoàn thiện file analysis/failure_analysis.md.

  Giai đoạn 4: Tối ưu & Nộp bài (45 phút)
   * Thành viên 1 & 2: Thử nghiệm thay đổi prompt của Agent (trong agent/main_agent.py nếu có) hoặc điều chỉnh cấu
     hình Retrieval/Judge để xem điểm số có cải thiện và vượt qua được Release Gate của Thành viên 3 hay không.
   * Cả nhóm: Tự viết báo cáo reflection cá nhân (analysis/reflections/reflection_[Tên_SV].md).
   * Thành viên 3 (DevOps): Chạy python check_lab.py lần cuối để đảm bảo mọi định dạng đều đúng. Kiểm tra
     .gitignore xem đã bỏ .env và data/golden_set.jsonl ra chưa, sau đó commit và push toàn bộ code lên
     repository.

  ---

  💡 Lời khuyên cho nhóm để lấy điểm tối đa (Expert Tips)
   1. Code song song (Git): Đừng chờ người này làm xong rồi người kia mới làm. Dùng Git Branch để code độc lập
      (feature/data-gen, feature/llm-judge, feature/release-gate), sau đó merge lại với nhau thông qua Pull
      Request để tránh conflict.
   2. Mock Data: Trong 45 phút đầu tiên khi Thành viên 1 đang tạo 50 test cases, Thành viên 2 và 3 có thể tự tạo
      tay một file .jsonl gồm 3-5 cases "fake" (Mock Data) để test luồng code trước, tránh bị nghẽn (block) tiến
      độ.
   3. Tập trung vào chi phí và hiệu năng: Nhóm nên bàn bạc cách chạy Async hoặc dùng Model nhỏ hơn/rẻ hơn cho một
      số tác vụ không đòi hỏi suy luận quá sâu để "giảm 30% chi phí" như yêu cầu điểm cộng.