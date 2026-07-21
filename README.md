# HSK Việt – 10 Slot Học P0–P3

Ứng dụng web tĩnh tiếng Việt để học và luyện thi HSK trên GitHub Pages. Không có màn hình đăng nhập. Mỗi trình duyệt có 10 slot độc lập; mỗi slot lưu tên, lịch SRS, sổ từ yếu, kế hoạch, thống kê và lịch sử đề thi.

## Tính năng P0/P1

- 10 slot học, đổi tên và xóa riêng từng slot.
- 11.092 mục từ HSK 3.0; 30.431 nghĩa có ID riêng.
- Bốn hướng trắc nghiệm: Hán → Việt, Việt → Hán, Hán → pinyin, pinyin → Hán.
- SRS bốn mức Quên, Khó, Nhớ, Dễ; lịch riêng cho từng kỹ năng.
- Việt hóa, giao diện xanh lá pastel, giản thể/phồn thể, phát âm Web Speech API.
- 84 câu ví dụ Trung–pinyin–Việt đã duyệt.
- PWA, cache dữ liệu cấp HSK sau lần mở đầu tiên.
- Tự nâng cấp dữ liệu localStorage từ bản v1/P0-P1, không xóa tiến độ cũ.

## Tính năng P2

- Nghe chép chính tả: phát âm rồi nhập chữ Hán, chấp nhận giản thể hoặc phồn thể tương ứng.
- Điền từ vào câu từ bộ câu ví dụ đã duyệt.
- Sắp xếp cụm từ thành câu đúng.
- Sổ từ yếu: xếp hạng từ theo số lần sai, lapses SRS, độ khó và lỗi gần đây.
- Kế hoạch học: cấp mục tiêu, ngày hoàn thành, phút/ngày, ngày/tuần và từ mới/ngày.
- Thống kê chuyên sâu 30 ngày: độ chính xác theo hoạt động/hướng học, phản hồi trung bình, streak, heatmap, độ lưu giữ ước tính và tổng thời gian.

## Tính năng P3

- Ngân hàng câu hỏi sinh từ dữ liệu từ vựng và câu ví dụ.
- Đề mô phỏng 20, 30 hoặc 50 câu.
- Năm dạng: chọn nghĩa, chọn pinyin, nghe chọn từ, điền từ, sắp xếp câu.
- Đồng hồ đếm ngược, tự nộp khi hết giờ.
- Chấm thang 100, điểm từng nhóm kỹ năng.
- Giải thích từng câu bằng chữ Hán, pinyin, nghĩa hoặc bản dịch câu.
- Lưu tối đa 30 lần thi gần nhất trong từng slot.

> Đề mô phỏng là bài luyện nội bộ theo dữ liệu ứng dụng, không phải đề thi HSK chính thức.

## Lưu tự động bằng Supabase, không hiện đăng nhập

Ứng dụng hỗ trợ Supabase Anonymous Auth. Người học không nhập email, tài khoản hoặc mật khẩu. Trình duyệt tự tạo một phiên ẩn danh, sau đó dữ liệu từng slot được `upsert` lên bảng Supabase có RLS.

### Thiết lập

1. Tạo project tại Supabase.
2. Mở `SQL Editor`, chạy toàn bộ file `supabase/schema.sql`.
3. Vào `Authentication` → `Providers` và bật `Anonymous Sign-Ins`.
4. Mở `js/config.js` rồi sửa:

```js
export const SUPABASE_CONFIG = {
  enabled: true,
  url: 'https://PROJECT_REF.supabase.co',
  anonKey: 'PUBLISHABLE_OR_ANON_KEY',
  table: 'hsk_slots'
};
```

5. Chỉ dùng publishable key hoặc anon key. Không đưa `service_role` key lên GitHub.
6. Push lại repository. Trên giao diện sẽ hiện “Đã đồng bộ Supabase”.

### Cách tự lưu

- Mỗi lần thay đổi tiến độ, ứng dụng lưu ngay vào localStorage và xếp hàng đồng bộ lên Supabase sau khoảng 0,7 giây.
- Khi hoàn thành phiên học hoặc nộp đề, ứng dụng gọi đồng bộ ngay.
- Khi mất mạng hoặc Supabase lỗi, dữ liệu vẫn nằm trên máy và ứng dụng tiếp tục hoạt động.
- Nút “Đồng bộ ngay” nằm trong Cài đặt.
- Nút “Xóa slot” xóa cả bản cục bộ và bản Supabase của slot đó.

### Giới hạn quan trọng của chế độ ẩn danh

Phiên Supabase ẩn danh gắn với dữ liệu trình duyệt. Nếu xóa dữ liệu trình duyệt, đăng xuất phiên ẩn danh hoặc mở trên một thiết bị khác, ứng dụng sẽ tạo một danh tính ẩn danh mới và không tự thấy 10 slot cũ. Đây là giới hạn tất yếu khi không có tài khoản hoặc mã khôi phục.

Để tránh mất dữ liệu:

- Không xóa dữ liệu trang khi chưa xuất sao lưu.
- Dùng nút `Xuất sao lưu` định kỳ.
- Khi chuyển thiết bị, xuất từng slot rồi nhập vào thiết bị mới.

Nếu cần đồng bộ cùng 10 slot trên nhiều thiết bị mà vẫn không dùng email, phiên bản sau phải bổ sung một “mã không gian học” bí mật. Mã đó về bản chất vẫn là khóa truy cập và phải được bảo vệ.

## Đưa lên GitHub Pages

1. Tải toàn bộ nội dung bên trong thư mục này lên nhánh `main`.
2. Vào `Settings` → `Pages`.
3. Chọn `Deploy from a branch`.
4. Chọn `main` và `/(root)`.
5. Nhấn `Save`.

Không chạy `npm build`. Đây là ứng dụng HTML/CSS/JavaScript thuần.

## Kiểm thử

```bash
npm test
```

Không cần cài package npm. Node.js 18 trở lên là đủ. GitHub Actions cũng tự chạy bộ kiểm thử khi push.

## Cấu trúc chính

```text
index.html
css/app.css
js/app.js
js/config.js
js/modules/
data/levels/
data/examples.json
supabase/schema.sql
manifest.webmanifest
sw.js
tests/
```

## Nguồn và giấy phép

Xem `DATA_SOURCES.md` và `NOTICE.md`. Mã ứng dụng theo MIT. Dữ liệu nghĩa tiếng Việt có nguồn CVDICT và điều kiện CC BY-SA 4.0.
