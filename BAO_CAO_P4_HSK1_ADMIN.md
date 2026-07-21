# Báo cáo P4 – HSK 1 chuẩn hóa và quản trị học liệu

## Đã thực hiện
- 500/500 từ HSK 1 có bản ghi chuẩn hóa.
- Mỗi bản ghi có nghĩa chính, nghĩa phụ, từ loại, chủ đề, ghi chú, lượng từ, cụm từ, từ dễ nhầm và ví dụ.
- 30 điểm ngữ pháp nền tảng.
- Thư viện tra cứu HSK 1.
- Quản trị sửa học liệu trực tiếp trên giao diện.
- Mật khẩu mặc định không lưu chữ rõ; JS chỉ chứa SHA-256 cho chế độ cục bộ và SQL chứa bcrypt.
- Supabase lưu mật khẩu bằng bcrypt và ghi học liệu qua RPC.
- Nội dung sửa dùng chung cho toàn bộ 10 slot nhưng không trộn với tiến độ slot.
- Khôi phục từng từ, đổi mật khẩu, xuất/nhập JSON.
- Phương án nhiễu ưu tiên từ dễ nhầm/cùng chủ đề/cùng từ loại.

## Giới hạn được kiểm soát
- Các ví dụ phát âm tự động không đủ điều kiện tạo câu hỏi.
- Chỉ ví dụ đã có hoặc được admin bật `exerciseEligible` mới vào bài điền từ/sắp xếp.
- Gói chuẩn hóa là nền biên tập, không được gắn nhãn giáo viên duyệt toàn bộ.
- Mật khẩu tĩnh phù hợp dùng gia đình, không phù hợp mở quyền quản trị công khai quy mô lớn.
