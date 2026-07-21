# HSK Việt – 10 Slot Học P0–P4

Ứng dụng web tĩnh tiếng Việt chạy trên GitHub Pages. Không có màn hình đăng nhập người học. Mỗi trình duyệt có 10 slot độc lập để lưu tiến độ, SRS, sổ từ yếu, kế hoạch, thống kê và lịch sử đề thi.

## P4 – HSK 1 chuẩn hóa

- Phủ đủ 500 mục từ HSK 1 của bộ dữ liệu hiện tại.
- Mỗi mục có nghĩa chính rút gọn, các nghĩa phụ, từ loại, chủ đề, lượng từ khi có, ghi chú cách dùng, cụm từ thường gặp, từ dễ nhầm và ví dụ.
- 30 cấu trúc ngữ pháp nền tảng kèm công thức, giải thích, ví dụ và lỗi thường gặp.
- Phương án nhiễu ưu tiên từ cùng chủ đề, cùng từ loại, gần pinyin hoặc nằm trong nhóm dễ nhầm.
- Các ví dụ chỉ dùng để tạo bài điền từ/sắp xếp khi trường `exerciseEligible` được bật. Ví dụ đọc từ tự động không được đưa vào đề.
- Màn hình “Thư viện HSK 1” cho phép tra chữ Hán, pinyin, nghĩa và chủ đề.

> “Chuẩn hóa” trong bản này nghĩa là dữ liệu đã được làm sạch và đưa về cấu trúc học tập thống nhất. Không nên hiểu rằng toàn bộ 500 mục đã được một hội đồng giáo viên kiểm duyệt học thuật. Vì vậy ứng dụng có chức năng quản trị sửa trực tiếp.

## Quản trị học liệu ngay trên giao diện

- Nút `✎` ở thanh trên hoặc nút `Quản trị học liệu` tại trang chọn slot.
- Mật khẩu mặc định được đặt theo yêu cầu của chủ ứng dụng và không ghi chữ rõ trong repository.
- Có thể sửa nghĩa chính, nghĩa phụ, từ loại, chủ đề, lượng từ, ghi chú cách dùng, cụm từ, từ dễ nhầm và câu ví dụ.
- Nội dung mới được dùng ngay trong thẻ học, đáp án, sổ từ yếu, giải thích và ngân hàng đề.
- Có thể khôi phục riêng từng từ về bản chuẩn hóa ban đầu.
- Có thể xuất/nhập toàn bộ nội dung đã chỉnh bằng JSON.
- Có thể đổi mật khẩu quản trị trong giao diện.

### Phạm vi bảo mật

Đây là ứng dụng GitHub Pages dùng trong gia đình, không phải hệ thống quản trị doanh nghiệp. Khi chưa có Supabase, việc kiểm tra mật khẩu diễn ra ở trình duyệt và chỉ phù hợp để ngăn sửa nhầm. Khi đã chạy SQL P4 trên Supabase, việc xác minh và ghi học liệu dùng chung được thực hiện bằng hàm PostgreSQL `SECURITY DEFINER`; mật khẩu lưu dưới dạng bcrypt trong cơ sở dữ liệu.

Không đưa `service_role` key vào GitHub.

## Tính năng P0–P3

- 10 slot học, đổi tên và xóa riêng từng slot.
- 11.092 mục từ HSK 3.0; 30.431 nghĩa có ID riêng.
- Bốn hướng trắc nghiệm: Hán → Việt, Việt → Hán, Hán → pinyin, pinyin → Hán.
- SRS bốn mức Quên, Khó, Nhớ, Dễ.
- Nghe chép chính tả, điền từ, sắp xếp câu và sổ từ yếu.
- Kế hoạch học và thống kê chuyên sâu 30 ngày.
- Đề mô phỏng 20, 30 hoặc 50 câu, đồng hồ, chấm điểm, giải thích và lịch sử thi.
- PWA, lưu cục bộ, Supabase Anonymous Auth tùy chọn.

> Đề mô phỏng là bài luyện nội bộ theo dữ liệu ứng dụng, không phải đề thi HSK chính thức.

## Cập nhật Supabase từ v2 lên v3

1. Mở Supabase `SQL Editor`.
2. Chạy toàn bộ `supabase/upgrade_v3.sql` hoặc chạy lại `supabase/schema.sql`.
3. Đảm bảo `Authentication → Providers → Anonymous Sign-Ins` đang bật.
4. Không cần xóa bảng `hsk_slots`; script dùng `create table if not exists` và không xóa tiến độ.
5. Sau khi mở ứng dụng, đăng nhập quản trị bằng mật khẩu mặc định rồi đổi mật khẩu.

Cấu hình `js/config.js`:

```js
export const SUPABASE_CONFIG = {
  enabled: true,
  url: 'https://PROJECT_REF.supabase.co',
  anonKey: 'PUBLISHABLE_OR_ANON_KEY',
  table: 'hsk_slots'
};
```

## Cách lưu nội dung đã sửa

- Không có Supabase: lưu trong `localStorage` của trình duyệt.
- Có Supabase: lưu cục bộ trước, sau đó gọi RPC để lưu vào bảng `hsk_content_overrides` dùng chung cho các thành viên gia đình.
- Tiến độ người học vẫn nằm trong bảng `hsk_slots`, tách biệt hoàn toàn với học liệu.
- Xóa/reset slot không xóa học liệu do admin sửa.

## Đưa lên GitHub Pages

1. Sao lưu repository hiện tại.
2. Chép toàn bộ nội dung thư mục này vào repository và chọn Replace.
3. Commit và Push bằng GitHub Desktop.
4. GitHub → `Settings → Pages`.
5. Chọn `Deploy from a branch`, nhánh `main`, thư mục `/(root)`.
6. Không chạy `npm build`.

Do service worker có cache, sau khi cập nhật nên đóng tab cũ, mở lại trang và nhấn `Ctrl+F5` một lần.

## Kiểm thử

```bash
npm test
```

Không cần cài package npm. Node.js 18 trở lên là đủ.

## Cấu trúc bổ sung P4

```text
data/hsk1-quality.json
 data/hsk1-grammar.json
js/modules/content.js
js/modules/admin.js
supabase/upgrade_v3.sql
tools/build_hsk1_quality.py
tests/test-p4-quality-admin.mjs
```

## Nguồn và giấy phép

Xem `DATA_SOURCES.md` và `NOTICE.md`. Mã ứng dụng theo MIT. Dữ liệu nghĩa tiếng Việt có nguồn CVDICT và điều kiện CC BY-SA 4.0.
