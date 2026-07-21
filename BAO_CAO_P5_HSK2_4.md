# Báo cáo P5 – Mở rộng chuẩn hóa HSK 2–4

## Phạm vi bổ sung

- HSK 2: 772/772 từ có bản ghi chuẩn hóa; 25 điểm ngữ pháp.
- HSK 3: 973/973 từ có bản ghi chuẩn hóa; 30 điểm ngữ pháp.
- HSK 4: 1.000/1.000 từ có bản ghi chuẩn hóa; 42 điểm ngữ pháp.
- HSK 1 giữ nguyên 500 từ và 30 điểm ngữ pháp.
- Tổng HSK 1–4: 3.245 từ và 127 điểm ngữ pháp.

## Trường dữ liệu mỗi từ

- Nghĩa chính làm sạch.
- Danh sách nghĩa phụ có ID ổn định khi đưa vào runtime.
- Từ loại.
- Chủ đề.
- Lượng từ trích xuất khi dữ liệu nguồn có ghi nhận.
- Ghi chú cách dùng theo loại từ/cấu trúc.
- Cụm từ thường gặp cho nhóm từ đã tuyển chọn.
- Từ dễ nhầm dựa trên pinyin, chữ Hán, từ loại, chủ đề và nghĩa gần.
- Câu ví dụ hoặc mẫu hỗ trợ đọc từ.
- Trạng thái chuẩn hóa và khả năng được dùng tạo bài tập.

## Kiểm soát câu ví dụ

- Ví dụ có sẵn trong dữ liệu được giữ và cho phép luyện tập.
- Một số ví dụ từ thư viện ngữ pháp được gắn cho đúng từ mục tiêu và cho phép luyện tập.
- Mẫu `请读这个词…` chỉ hỗ trợ phát âm, không được dùng trong điền từ, sắp xếp câu hoặc đề thi.
- Admin có thể thay câu ví dụ và bật/tắt `exerciseEligible` ngay trên giao diện.

## Quản trị đa cấp

- Màn hình admin có bộ chọn HSK 1–4.
- Bản sửa lưu bằng ID từ nên không xung đột giữa các cấp.
- Supabase sử dụng lại bảng và RPC v3.0, không cần migration SQL.
- Nội dung HSK 1 đã sửa trước đây vẫn được áp dụng vì khóa lưu không đổi.

## Bảo toàn phần cũ

Đã đối chiếu SHA-256 và giữ nguyên các tệp nền quan trọng:

- `data/hsk1-quality.json`
- `data/hsk1-grammar.json`
- `data/levels/hsk1.json`
- `js/modules/storage.js`
- `js/modules/srs.js`
- `js/modules/quiz.js`
- `supabase/schema.sql`
- `supabase/upgrade_v3.sql`

Không thay schema slot, không reset tiến độ, không thay thuật toán SRS và không thay cơ chế mật khẩu/Supabase.

## Giới hạn cần hiểu đúng

- Gói chuẩn hóa HSK 2–4 là lớp làm sạch và nền biên tập có hệ thống; chưa phải toàn bộ từ đã được giáo viên duyệt từng mục.
- Cụm từ tuyển chọn mới phủ một phần các từ quan trọng.
- Câu ví dụ luyện tập HSK 2–4 mới gồm ví dụ nguồn và ví dụ ngữ pháp được biên soạn; phần còn lại dùng mẫu đọc từ an toàn.
- Khi phát hiện nghĩa hoặc cách dùng chưa phù hợp, admin có thể sửa ngay mà không cần sửa mã nguồn.

## Kiểm thử

- Kiểm tra đủ số lượng bản ghi từng cấp.
- Kiểm tra không thiếu nghĩa, chủ đề, ghi chú và ví dụ.
- Kiểm tra các ví dụ được phép tạo bài có trạng thái hợp lệ.
- Kiểm tra runtime áp dụng override cho HSK 2–4.
- Kiểm tra giao diện thư viện và admin có bộ chọn cấp.
- Kiểm tra PWA cache đủ gói HSK 2–4.
- Chạy lại toàn bộ kiểm thử P0–P4 để phát hiện hồi quy.
