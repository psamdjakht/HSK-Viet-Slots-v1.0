# Nguồn dữ liệu

## Danh sách HSK 3.0

- Dự án: `ivankra/hsk30`
- Địa chỉ: https://github.com/ivankra/hsk30
- Tệp dùng: `hsk30.csv`
- Vai trò: ID HSK, cấp độ, chữ giản thể/phồn thể, pinyin, từ loại, biến thể và khóa CC-CEDICT.
- Dữ liệu đã được tác giả dự án đối chiếu từ nhiều nguồn. Xem giấy phép và ghi chú nguồn trong repository gốc.

## Nghĩa tiếng Việt

- Dự án: `ph0ngp/CVDICT`
- Địa chỉ: https://github.com/ph0ngp/CVDICT
- Tệp dùng: `CVDICT.u8`
- Vai trò: nghĩa tiếng Việt được ghép bằng khóa **chữ giản thể + pinyin đánh số**, tránh lỗi lấy nhầm âm đầu tiên của chữ đa âm.
- Giấy phép: Creative Commons Attribution-ShareAlike 4.0 International.
- CVDICT có cảnh báo rằng một số bản dịch vẫn có thể còn lỗi. Ứng dụng vì vậy giữ trường `verification` và không coi toàn bộ dữ liệu là đã duyệt học thuật.

## Câu ví dụ

84 câu ví dụ khởi đầu được biên soạn riêng cho dự án, ưu tiên cấu trúc đơn giản và nghĩa thông dụng. Chưa có câu ví dụ cho toàn bộ 11.092 mục.

## Quy trình làm sạch

`tools/build_data.py` thực hiện:

1. Đọc đầy đủ 11.092 mục HSK 3.0.
2. Giữ ID gốc thay vì loại trùng theo chữ Hán.
3. Ghép nghĩa Việt theo khóa phồn thể + giản thể + pinyin chính xác; ưu tiên pinyin viết thường để tránh trộn tên riêng.
4. Kế thừa nghĩa từ mục gốc cho các từ chỉ ghi “biến thể/xem…”.
5. Gắn ID riêng cho từng nghĩa.
6. Gắn trạng thái kiểm chứng.
7. Chia dữ liệu thành bảy tệp để tải theo cấp.
