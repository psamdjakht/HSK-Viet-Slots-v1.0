# Báo cáo P6 – Mở rộng chuẩn hóa HSK 5, HSK 6 và HSK 7–9

## Phạm vi bổ sung

- HSK 5: 1.071/1.071 từ; 45 điểm ngữ pháp; 36 câu được phép dùng luyện tập.
- HSK 6: 1.140/1.140 từ; 50 điểm ngữ pháp; 41 câu được phép dùng luyện tập.
- HSK 7–9: 5.636/5.636 từ; 60 điểm ngữ pháp; 79 câu được phép dùng luyện tập.
- HSK 1–4 giữ nguyên: 3.245 từ và 127 điểm ngữ pháp.
- Tổng toàn hệ thống: 11.092 từ và 282 điểm ngữ pháp.

## Quy trình chuẩn hóa

1. Giữ nguyên ID, chữ giản thể/phồn thể, pinyin và cấp độ gốc.
2. Loại ghi chú lượng từ, biến thể hoặc tham chiếu khỏi nghĩa chính khi không phải nghĩa độc lập.
3. Ưu tiên nghĩa thông dụng cho một số mục dễ bị từ điển chọn nghĩa phụ.
4. Phân loại chủ đề từ nghĩa tiếng Việt và từ loại.
5. Tạo ghi chú cách dùng theo loại từ và cấp độ.
6. Tạo từ dễ nhầm bằng chỉ mục chữ Hán, pinyin, chủ đề và từ loại.
7. Tạo cụm từ và câu ví dụ tuyển chọn cho nhóm từ quan trọng.
8. Các từ chưa có câu dùng thực tế nhận mẫu đọc từ với `exerciseEligible: false`.

## Tối ưu HSK 7–9

Gói HSK 7–9 có 5.636 từ. Quy trình P6 không so sánh toàn bộ từng cặp từ. Ứng viên dễ nhầm được lấy từ các chỉ mục:

- chữ Hán chung;
- pinyin gần hoặc giống;
- chủ đề;
- từ loại;
- vị trí lân cận trong danh sách.

Cách này giữ chất lượng phương án nhiễu nhưng giảm đáng kể thời gian xây dữ liệu.

## Quản trị đa cấp

- Thư viện và admin có HSK 5, HSK 6, HSK 7–9.
- Admin sửa nội dung bằng cùng schema và RPC Supabase hiện tại.
- ID HSK 5–7 không xung đột với HSK 1–4.
- Không cần migration SQL.

## Bảo toàn phần cũ

Đã kiểm tra SHA-256 và xác nhận không đổi các tệp sau của HSK 1–4:

- `data/levels/hsk1.json` đến `hsk4.json`
- `data/hsk1-quality.json` đến `hsk4-quality.json`
- `data/hsk1-grammar.json` đến `hsk4-grammar.json`

Không thay schema slot, lịch SRS, dữ liệu thi, cấu trúc Supabase hoặc ID nội dung cũ.

## Giới hạn cần hiểu đúng

- Toàn bộ từ được chuẩn hóa về schema và làm sạch tự động có kiểm soát; không phải tất cả đã được giáo viên duyệt thủ công.
- Cụm từ và câu ví dụ tuyển chọn mới phủ một phần từ trọng tâm.
- HSK 7 của app là gói HSK 7–9 theo dữ liệu nguồn hiện tại.
- Admin nên sửa ngay khi phát hiện nghĩa, từ loại hoặc ví dụ chưa phù hợp.

## Kiểm thử

- Đủ số lượng từ từng cấp.
- Không thiếu nghĩa chính, chủ đề, ghi chú và ví dụ.
- Ngữ pháp có đủ công thức, giải thích, ví dụ và lỗi thường gặp.
- Ví dụ được phép luyện tập có trạng thái hợp lệ.
- Runtime nạp và áp dụng override cho HSK 5–7–9.
- PWA cache đủ các gói mới.
- SHA-256 HSK 1–4 không đổi.
- Chạy lại toàn bộ kiểm thử P0–P5 để phát hiện hồi quy.
