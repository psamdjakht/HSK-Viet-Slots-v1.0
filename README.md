# HSK Việt – 10 Slot Học P0–P6

Ứng dụng web tĩnh tiếng Việt chạy trên GitHub Pages. Không có màn hình đăng nhập người học. Mỗi trình duyệt có 10 slot độc lập để lưu tiến độ, SRS, sổ từ yếu, kế hoạch, thống kê và lịch sử đề thi.

## P6 – Mở rộng chuẩn hóa HSK 5, HSK 6 và HSK 7–9

Bản v5.0 là bản full. Phần chuẩn hóa HSK 1–4, dữ liệu tiến độ, SRS, 10 slot, Supabase và quyền quản trị cũ được giữ nguyên.

- HSK 1: 500 từ, 30 điểm ngữ pháp.
- HSK 2: 772 từ, 25 điểm ngữ pháp.
- HSK 3: 973 từ, 30 điểm ngữ pháp.
- HSK 4: 1.000 từ, 42 điểm ngữ pháp.
- HSK 5: 1.071 từ, 45 điểm ngữ pháp.
- HSK 6: 1.140 từ, 50 điểm ngữ pháp.
- Cấp `7` của ứng dụng là gói HSK 7–9: 5.636 từ, 60 điểm ngữ pháp.
- Tổng lớp chuẩn hóa: 11.092 từ và 282 điểm ngữ pháp trọng tâm.
- Thư viện và quản trị học liệu cho phép chọn HSK 1–6 hoặc HSK 7–9.
- Các bản sửa admin cũ tiếp tục dùng nguyên `word_id`, không cần chuyển đổi.

> “Chuẩn hóa” nghĩa là dữ liệu được làm sạch, phân loại và đưa về schema học tập thống nhất. Đây là nền biên tập có kiểm soát, không phải tuyên bố toàn bộ 11.092 mục đã được giáo viên duyệt thủ công từng từ.

## Dữ liệu mỗi từ chuẩn hóa

- Nghĩa chính và các nghĩa phụ.
- Từ loại, chủ đề và lượng từ khi có.
- Ghi chú cách dùng.
- Cụm từ thường gặp cho nhóm từ được tuyển chọn.
- Từ dễ nhầm theo chữ Hán, pinyin, từ loại và chủ đề.
- Câu ví dụ sử dụng hoặc mẫu hỗ trợ đọc từ.
- Chỉ câu có `exerciseEligible: true` mới được dùng cho điền từ, sắp xếp câu và đề thi.

## Quản trị học liệu

- Mở bằng nút `✎` trong slot hoặc nút `Quản trị học liệu` ở trang chọn slot.
- Chọn cấp HSK 1–6 hoặc HSK 7–9.
- Sửa nghĩa, từ loại, chủ đề, ghi chú, cụm từ, từ dễ nhầm và câu ví dụ.
- Nội dung mới được dùng ngay trong thẻ học, đáp án, sổ từ yếu, giải thích và ngân hàng đề.
- Có thể khôi phục từng từ về bản chuẩn hóa ban đầu.
- Có thể xuất/nhập toàn bộ nội dung chỉnh sửa bằng JSON.
- Reset hoặc xóa slot không xóa học liệu admin đã sửa.

## Supabase

Bản v5.0 không cần chạy SQL mới. Giữ nguyên:

- `supabase/schema.sql`
- `supabase/upgrade_v3.sql`
- `js/config.js` đã điền Project URL và anon key
- các bảng và RPC đang hoạt động ở bản trước

Nội dung sửa HSK 5–7–9 sử dụng cùng bảng `hsk_content_overrides` với ID `L5-...`, `L6-...`, `L7-...`.

## Tính năng P0–P5 được giữ nguyên

- 10 slot học độc lập.
- Bốn hướng trắc nghiệm và SRS bốn mức.
- Nghe chép chính tả, điền từ, sắp xếp câu, sổ từ yếu.
- Kế hoạch học và thống kê 30 ngày.
- Ngân hàng câu hỏi, đề mô phỏng, chấm điểm, giải thích và lịch sử thi.
- PWA, localStorage và Supabase Anonymous Auth tùy chọn.
- Quản trị học liệu bằng mật khẩu.

## Cập nhật repository

1. Sao lưu repository hoặc tạo commit hiện trạng.
2. Sao chép riêng `js/config.js` nếu đã có URL và anon key Supabase.
3. Giải nén ZIP.
4. Chép toàn bộ nội dung thư mục `HSK-Viet-Slots-v5.0` vào repository cũ và chọn Replace.
5. Chép lại cấu hình Supabase cũ vào `js/config.js` nếu cần.
6. Commit và Push.
7. Không chạy `npm build`.
8. Sau khi GitHub Pages deploy, mở trang và nhấn `Ctrl+F5` một lần.

## Kiểm thử

```bash
npm test
```

Không cần cài package npm. Node.js 18 trở lên là đủ để chạy test.

## Tệp bổ sung P6

```text
data/hsk5-quality.json
data/hsk5-grammar.json
data/hsk6-quality.json
data/hsk6-grammar.json
data/hsk7-quality.json
data/hsk7-grammar.json
tools/build_hsk5_7_quality.py
tests/test-p6-hsk5-7.mjs
tests/test-p6-runtime.mjs
BAO_CAO_P6_HSK5_7.md
```

## Nguồn và giấy phép

Xem `DATA_SOURCES.md` và `NOTICE.md`. Mã ứng dụng theo MIT. Dữ liệu nghĩa tiếng Việt sử dụng CVDICT theo CC BY-SA 4.0.
