# HSK Việt – 10 Slot Học P0–P8

Ứng dụng web tĩnh tiếng Việt chạy trực tiếp trên GitHub Pages. Không có đăng nhập người học; mỗi trình duyệt có 10 slot riêng để lưu SRS, sổ từ yếu, kế hoạch, thống kê và lịch sử đề thi. Supabase vẫn là tùy chọn để đồng bộ slot và nội dung quản trị.


## P8 – Đọc hiểu HSK 6 và HSK 7–9

Bản v7.0 chỉ mở rộng mô-đun đọc hiểu, giữ nguyên toàn bộ phần đã chuẩn hóa và tiến độ cũ.

- HSK 6: 5 bài, khoảng 1.000 chữ Hán/bài.
- HSK 7–9: 5 bài, khoảng 1.500 chữ Hán/bài.
- Tổng toàn app: 35 bài đọc từ HSK 1 đến HSK 7–9.
- Mỗi câu có chữ Hán, pinyin, dịch Việt riêng và nút phát âm.
- Từ HSK được highlight; bấm từ để xem nghĩa và cách dùng.

## P7 – Câu ví dụ chuẩn hóa và đọc hiểu HSK 1–5

Bản v6.0 bổ sung hai lớp học liệu mới, không thay đổi danh sách từ, ID từ, nghĩa đã chuẩn hóa, ngữ pháp HSK 1–7–9, SRS, 10 slot hoặc schema Supabase.

### Thư viện câu ví dụ

- 11.092 từ đều có cấu trúc `examples[]` thống nhất.
- Tổng cộng 33.276 mục câu học: 3 mục cho mỗi từ.
- Mỗi mục có chữ Hán, pinyin, dịch Việt, độ khó, loại câu, trạng thái và cờ `exerciseEligible`.
- Câu do admin sửa được ưu tiên hiển thị ngay.
- Chỉ câu có `exerciseEligible: true` được đưa vào điền từ, sắp xếp câu và đề mô phỏng.
- Các mẫu `guided_context`, `active_recall` và `production_prompt` giúp học nghĩa, vị trí, cách dùng và tự đặt câu; chúng không bị dùng như câu hỏi thi.

> Lưu ý chất lượng: không tuyên bố toàn bộ 33.276 mục là câu ngữ cảnh do giáo viên duyệt thủ công. Câu dùng để tạo bài tập vẫn bị giới hạn ở nhóm đủ điều kiện. Các mẫu học an toàn được ghi nhãn rõ để tránh đánh đồng với câu dùng thực tế.

### Đọc hiểu tích hợp HSK 1–7–9 (P7 + P8)

Có 35 bài đọc, 5 bài cho mỗi cấp:

- HSK 1: khoảng 50 chữ Hán/bài.
- HSK 2: khoảng 100 chữ Hán/bài.
- HSK 3: khoảng 180 chữ Hán/bài.
- HSK 4: khoảng 300 chữ Hán/bài.
- HSK 5: khoảng 600 chữ Hán/bài.
- HSK 6: khoảng 1.000 chữ Hán/bài.
- HSK 7–9: khoảng 1.500 chữ Hán/bài.

Mỗi bài có:

- Tách riêng từng câu.
- Pinyin từng câu, có thể bật/tắt.
- Dịch tiếng Việt ngay dưới từng câu, mặc định bật.
- Highlight từ vựng HSK 1 đến cấp đang đọc.
- Bấm từ được highlight để xem pinyin, nghĩa, từ loại, chủ đề, cách dùng và ví dụ.
- Phát âm từng câu hoặc toàn bài bằng giọng tiếng Trung của thiết bị.

## Dữ liệu chuẩn hóa hiện có

- HSK 1: 500 từ, 30 điểm ngữ pháp.
- HSK 2: 772 từ, 25 điểm ngữ pháp.
- HSK 3: 973 từ, 30 điểm ngữ pháp.
- HSK 4: 1.000 từ, 42 điểm ngữ pháp.
- HSK 5: 1.071 từ, 45 điểm ngữ pháp.
- HSK 6: 1.140 từ, 50 điểm ngữ pháp.
- HSK 7–9: 5.636 từ, 60 điểm ngữ pháp.
- Tổng: 11.092 từ, 30.431 nghĩa có ID và 282 điểm ngữ pháp.

## Quản trị học liệu

- Mật khẩu và cơ chế quản trị giữ nguyên bản trước.
- Admin sửa nghĩa, từ loại, chủ đề, ghi chú, cụm từ, từ dễ nhầm và câu ví dụ chính.
- Câu admin sửa được ưu tiên trong danh sách câu ví dụ và trong các bài tập nếu được bật `exerciseEligible`.
- Không cần SQL Supabase mới.
- Reset slot không xóa nội dung admin đã sửa.

## Cập nhật GitHub

1. Tạo commit hoặc sao lưu repository hiện tại.
2. Sao chép riêng `js/config.js` nếu đã điền Supabase URL và anon key.
3. Giải nén ZIP.
4. Chép toàn bộ nội dung bên trong `HSK-Viet-Slots-v7.0` vào repository cũ và chọn Replace.
5. Chép lại cấu hình Supabase vào `js/config.js` nếu cần.
6. Commit và Push.
7. Không chạy `npm build`.
8. Không chạy lại `schema.sql` hoặc `upgrade_v3.sql`.
9. Sau khi GitHub Pages deploy xong, mở trang và nhấn `Ctrl+F5` một lần.

## Kiểm thử

```bash
npm test
```

Bộ test P0–P8 kiểm tra dữ liệu, SRS, bài tập, Supabase, DOM, PWA, 33.276 mục câu học, 35 bài đọc, độ dài bài, dịch từng câu và runtime highlight từ.

## Tệp mới P7

```text
js/modules/reading.js
data/standardized-examples.json
data/reading/meta.json
data/reading/hsk1.json ... hsk5.json
tools/build_examples_reading.py
tests/test-p7-examples-reading.mjs
tests/test-p7-runtime.mjs
BAO_CAO_P7_CAU_VI_DU_DOC_HIEU.md
BAO_TOAN_PHAN_CU_V5_V6_SHA256.txt
```

Nguồn và giới hạn học liệu được mô tả trong `DATA_SOURCES.md`.

## Tệp mới P8

```text
data/reading/hsk6.json
data/reading/hsk7.json
tools/build_reading_hsk6_7.py
tests/test-p8-reading-hsk6-7.mjs
tests/test-p8-runtime.mjs
BAO_CAO_P8_DOC_HIEU_HSK6_7.md
BAO_TOAN_PHAN_CU_V6_V7_SHA256.txt
```
