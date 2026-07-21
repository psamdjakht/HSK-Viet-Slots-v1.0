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

## Lớp chuẩn hóa HSK 1 P4

`data/hsk1-quality.json` được tạo từ dữ liệu HSK 1 hiện có bằng `tools/build_hsk1_quality.py`. Lớp này làm sạch nghĩa chính, tách lượng từ, gắn chủ đề/từ loại, tạo ghi chú sử dụng và nhóm từ dễ nhầm. Ví dụ dạng “Tôi có thể đọc từ…” chỉ là mẫu hỗ trợ phát âm và có `exerciseEligible: false`, không được dùng để tạo đề.

`data/hsk1-grammar.json` là thư viện 30 cấu trúc nền tảng được biên soạn riêng cho ứng dụng. Nội dung vẫn nên được rà soát trong quá trình sử dụng; quản trị viên có thể sửa học liệu từ vựng trực tiếp trên giao diện.

## Lớp chuẩn hóa HSK 2–4 P5

Các tệp `data/hsk2-quality.json`, `data/hsk3-quality.json` và `data/hsk4-quality.json` được tạo bằng `tools/build_hsk2_4_quality.py` từ các tệp cấp độ đã có. Quy trình chỉ bổ sung lớp học liệu, không sửa danh sách từ gốc:

1. Giữ nguyên ID, chữ giản thể/phồn thể và pinyin.
2. Loại ghi chú lượng từ/biến thể khỏi nghĩa chính khi chúng không phải nghĩa độc lập.
3. Ưu tiên một số nghĩa thông dụng đã xác định cho các mục dễ bị chọn nhầm nghĩa phụ.
4. Phân loại chủ đề dựa trên nghĩa tiếng Việt và từ loại.
5. Sinh ghi chú cách dùng an toàn theo loại từ, đồng thời bổ sung ghi chú riêng cho các từ chức năng quan trọng.
6. Xếp từ dễ nhầm bằng độ gần pinyin, chữ Hán, từ loại, chủ đề và nghĩa.
7. Chỉ cho phép câu gốc hoặc câu biên soạn trong gói ngữ pháp tham gia bài tập; mẫu đọc từ tự động bị khóa khỏi ngân hàng đề.

Các tệp `data/hsk2-grammar.json`, `data/hsk3-grammar.json` và `data/hsk4-grammar.json` là thư viện cấu trúc trọng tâm được biên soạn riêng cho ứng dụng. Đây là tài liệu học hỗ trợ, không tuyên bố thay thế giáo trình hay danh mục ngữ pháp chính thức.

## Lớp chuẩn hóa HSK 5–7–9 P6

Các tệp `data/hsk5-quality.json`, `data/hsk6-quality.json` và `data/hsk7-quality.json` được tạo bằng `tools/build_hsk5_7_quality.py`. Cấp `7` trong app tương ứng gói HSK 7–9 của dữ liệu HSK 3.0 hiện tại.

Quy trình giữ nguyên ID từ gốc, làm sạch nghĩa, phân loại chủ đề, thêm ghi chú cách dùng, cụm từ tuyển chọn và câu ví dụ an toàn. Từ dễ nhầm được tìm bằng chỉ mục chữ Hán, pinyin, chủ đề và từ loại để xử lý hiệu quả tập dữ liệu 5.636 từ.

Các tệp `data/hsk5-grammar.json`, `data/hsk6-grammar.json` và `data/hsk7-grammar.json` là thư viện cấu trúc trọng tâm được biên soạn riêng cho ứng dụng. Pinyin câu ví dụ được tạo bằng thư viện `pypinyin` trong công cụ xây dữ liệu và vẫn nên được rà soát khi sử dụng thực tế.

## P7 – Câu ví dụ chuẩn hóa và đọc hiểu

`data/standardized-examples.json` được tạo bằng `tools/build_examples_reading.py` trên nền các gói chất lượng P4–P6. Mỗi từ có ba mục học theo schema thống nhất:

1. Câu dùng thực tế hiện có, nếu gói chất lượng đã có câu `kind: usage`.
2. Mẫu ngữ cảnh có kiểm soát theo từ loại.
3. Mẫu gợi nhớ chủ động hoặc gợi ý tự đặt câu.

Các mẫu số 2–3 được đánh dấu `exerciseEligible: false`. Chúng hỗ trợ việc học và không được coi là bằng chứng rằng cách dùng thực tế của mọi từ đã được giáo viên duyệt.

25 bài đọc trong `data/reading/` được biên soạn riêng cho ứng dụng, chia câu và dịch tiếng Việt từng câu. Pinyin được tạo bằng `pypinyin`; với tên riêng, từ đa âm hoặc hiện tượng biến điệu, người quản trị vẫn nên rà soát khi phát hiện điểm chưa tự nhiên.


## P8 – Đọc hiểu HSK 6 và HSK 7–9

Mười bài đọc mới trong `data/reading/hsk6.json` và `data/reading/hsk7.json` được biên soạn riêng cho ứng dụng. Mỗi cấp có năm chủ đề, câu được tách riêng và dịch sang tiếng Việt. Pinyin được tạo bằng `pypinyin`; tên riêng, từ đa âm và biến điệu vẫn nên được quản trị viên rà soát khi sử dụng thực tế.

P8 không tạo lại hoặc chỉnh nội dung các tệp đọc HSK 1–5. Báo cáo SHA-256 xác nhận toàn bộ năm gói cũ và dữ liệu học lõi được giữ nguyên.
