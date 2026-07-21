# Báo cáo P8 – Đọc hiểu HSK 6 và HSK 7–9

## Phạm vi

P8 chỉ bổ sung dữ liệu và lựa chọn giao diện cho đọc hiểu cấp cao. Không thay đổi danh sách từ, nghĩa chuẩn hóa, câu ví dụ P7, ngữ pháp, SRS, 10 slot, lịch sử học, quản trị nội dung hoặc schema Supabase.

## Dữ liệu mới

- `data/reading/hsk6.json`: 5 bài, mục tiêu khoảng 1.000 chữ Hán mỗi bài.
- `data/reading/hsk7.json`: 5 bài HSK 7–9, mục tiêu khoảng 1.500 chữ Hán mỗi bài.
- Tổng số bài đọc toàn ứng dụng tăng từ 25 lên 35.

Độ dài thực tế:

- HSK 6: 1.127, 1.072, 1.012, 1.056 và 944 chữ Hán.
- HSK 7–9: 1.682, 1.555, 1.536, 1.492 và 1.511 chữ Hán.

## Tính năng giữ nguyên

- Highlight từ HSK theo nguyên tắc ưu tiên từ dài nhất.
- Bấm từ để xem pinyin, nghĩa, từ loại, chủ đề, cách dùng và câu ví dụ.
- Pinyin từng câu có thể bật hoặc tắt.
- Dịch tiếng Việt riêng dưới từng câu, mặc định bật.
- Phát âm từng câu và toàn bài bằng giọng tiếng Trung trên thiết bị.

## Bảo toàn phần cũ

Đối chiếu SHA-256 với bản v6.0:

- 85 tệp cũ giữ nguyên byte.
- Không thiếu tệp cũ nào.
- Có 11 tệp cũ được chỉnh có chủ đích: 7 tệp giao diện/PWA/phiên bản để mở thêm hai cấp và 4 tệp kiểm thử/tài liệu. Không có thay đổi ngoài danh sách này.
- Toàn bộ `data/reading/hsk1.json` đến `hsk5.json`, `data/standardized-examples.json`, dữ liệu từ vựng, ngữ pháp, SRS và Supabase không đổi.

## Kiểm thử

P8 bổ sung kiểm tra:

- Đủ 5 bài mỗi cấp.
- Độ dài nằm trong khoảng 90%–120% mục tiêu.
- Mỗi câu có chữ Hán, pinyin và bản dịch Việt.
- Không trùng ID bài hoặc ID câu.
- Runtime tải được HSK 6 và HSK 7–9.
- Matcher có thể highlight từ trong bài.
- Service worker cache hai gói dữ liệu mới.

Toàn bộ kiểm thử P0–P8 đạt.
