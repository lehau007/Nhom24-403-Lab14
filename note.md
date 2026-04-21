1. Source Code: Toàn bộ mã nguồn hoàn chỉnh của hệ thống đánh giá.
2. Reports (Báo cáo kết quả):
    - File reports/summary.json
    - File reports/benchmark_results.json
    (Các file này được tự động tạo ra sau khi bạn chạy script main.py)
3. Group Report (Báo cáo nhóm): File analysis/failure_analysis.md đã được điền đầy đủ các thông tin phân tích
    lỗi.
4. Individual Reports (Báo cáo cá nhân): Các file analysis/reflections/reflection_[Tên_SV].md của từng thành
    viên trong nhóm.

Lưu ý quan trọng trước khi nộp bài:
- Bạn phải chạy python data/synthetic_gen.py trước để tạo file data/golden_set.jsonl (file này không được
    commit sẵn trong repo).
- Cần chạy python check_lab.py để đảm bảo định dạng dữ liệu đã chuẩn (nếu sai định dạng sẽ bị trừ 5 điểm).
- Tuyệt đối KHÔNG push file .env chứa API Key lên GitHub/GitLab.