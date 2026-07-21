# Báo cáo P7 – Câu ví dụ chuẩn hóa và đọc hiểu HSK 1–5

## Phạm vi

P7 chỉ bổ sung lớp câu ví dụ và đọc hiểu. Các gói từ vựng, nghĩa, ngữ pháp HSK 1–7–9, ID từ, SRS, 10 slot, lịch sử thi, Supabase và quyền admin được giữ nguyên.

## Câu ví dụ

- 11.092/11.092 từ có `examples[]`.
- 33.276 mục, đúng 3 mục/từ.
- Trường bắt buộc: `id`, `zh`, `pinyin`, `vi`, `difficulty`, `kind`, `status`, `exerciseEligible`.
- Câu sử dụng đủ điều kiện được giữ làm câu chính.
- Từ chưa có câu dùng thực tế nhận mẫu học an toàn có nhãn riêng và bị khóa khỏi bài thi.
- Câu admin sửa được đưa lên đầu và có trạng thái `admin_da_sua`.

## Đọc hiểu

- HSK 1: 5 bài, 45–50 chữ Hán.
- HSK 2: 5 bài, 90–101 chữ Hán.
- HSK 3: 5 bài, 170–180 chữ Hán.
- HSK 4: 5 bài, 275–297 chữ Hán.
- HSK 5: 5 bài, 540–557 chữ Hán.

Độ dài nằm trong khoảng 90–120% mục tiêu cấp. Mỗi câu có pinyin và bản dịch Việt riêng.

## Giao diện

- Thêm thẻ `Đọc hiểu HSK 1–5` tại trang chính.
- Có danh sách bài, bộ chọn cấp, bật/tắt pinyin và dịch.
- Tokenizer ưu tiên từ dài nhất để highlight.
- Bấm từ mở bảng chi tiết.
- Phát âm từng câu hoặc toàn bài.
- Thư viện từ hiển thị toàn bộ danh sách câu ví dụ của từ.

## Bảo toàn

`BAO_TOAN_PHAN_CU_V5_V6_SHA256.txt` xác nhận 37 tệp dữ liệu và module lõi của v5 không đổi SHA-256.

## Kiểm thử

- Toàn bộ test P0–P6 cũ đạt.
- Test P7 kiểm tra đủ 33.276 mục câu học.
- Kiểm tra 25 bài đọc và độ dài từng cấp.
- Kiểm tra pinyin và dịch từng câu.
- Kiểm tra runtime gắn câu, highlight, thống kê từ và ưu tiên câu admin.
