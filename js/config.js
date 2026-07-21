/**
 * CẤU HÌNH SUPABASE TÙY CHỌN
 * 1) Tạo project Supabase.
 * 2) Chạy supabase/schema.sql trong SQL Editor.
 * 3) Bật Anonymous Sign-Ins trong Authentication > Providers.
 * 4) Điền Project URL và publishable/anon key bên dưới.
 *
 * Không bao giờ đặt service_role key vào mã nguồn GitHub.
 */
export const SUPABASE_CONFIG = {
  enabled: false,
  url: '',
  anonKey: '',
  table: 'hsk_slots'
};
