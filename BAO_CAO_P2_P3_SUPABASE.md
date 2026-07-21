# Báo cáo nâng cấp P2/P3 và Supabase

## Phiên bản

- Tên: HSK Việt – 10 Slot Học
- Phiên bản: 2.0.0
- Kiến trúc: HTML/CSS/JavaScript modules, GitHub Pages, PWA, Supabase tùy chọn
- Schema slot: v3; có migration tự động từ schema v2

## P2 đã hoàn thành

- Nghe chép chính tả.
- Điền từ theo câu ví dụ.
- Sắp xếp câu bằng token.
- Sổ từ yếu có điểm xếp hạng.
- Kế hoạch học và dự báo tốc độ cần thiết.
- Thống kê 30 ngày theo hoạt động, hướng học, tốc độ, streak, retention và heatmap.

## P3 đã hoàn thành

- Ngân hàng câu hỏi sinh động từ 11.092 từ và 84 câu ví dụ.
- Đề mô phỏng 20/30/50 câu.
- Năm dạng câu hỏi.
- Đồng hồ và tự nộp.
- Chấm điểm toàn bài và từng dạng.
- Giải thích từng câu.
- Lịch sử tối đa 30 lần thi/slot.

## Supabase

- Dùng Anonymous Auth, không hiển thị form đăng nhập.
- Bảng `public.hsk_slots` có khóa chính `(user_id, slot_id)`.
- RLS giới hạn SELECT/INSERT/UPDATE/DELETE theo `auth.uid()`.
- Chỉ role `authenticated` được truy cập bảng; role `anon` bị revoke.
- Auto-save có debounce 700 ms và đồng bộ ngay khi kết thúc phiên/nộp đề.
- Local-first: Supabase lỗi không làm mất tiến độ trên trình duyệt.
- Reset slot xóa cả local và cloud.

## Kiểm thử

- SRS.
- Bốn hướng quiz.
- 11.092 từ và 30.431 nghĩa có ID duy nhất.
- Chính tả, điền từ, sắp xếp câu.
- Kế hoạch, streak, thống kê.
- Tạo đề, chấm điểm, giải thích.
- Anonymous Auth, RLS, upsert.
- PWA/static files.

## Giới hạn còn lại

- 84 câu ví dụ chưa phủ toàn bộ từ vựng; các bài điền/sắp xếp dùng câu từ cấp bằng hoặc thấp hơn mục tiêu.
- Web Speech API phụ thuộc giọng tiếng Trung của thiết bị.
- Đề mô phỏng không tuân theo toàn bộ cấu trúc, thời lượng và audio chuẩn của kỳ thi HSK chính thức.
- Anonymous Auth không khôi phục được danh tính sau khi xóa dữ liệu trình duyệt và không tự dùng chung giữa nhiều thiết bị.
- Chưa có trang quản trị để nhập ngân hàng đề thủ công.
