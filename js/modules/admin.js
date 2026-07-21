const DEFAULT_PASSWORD_HASH = 'aec5e5957476612d59cb95c72fce4eda4305342cc5aa73265e318d4070053351';
const LOCAL_PASSWORD_KEY = 'hsk_admin_password_hash_v1';
let unlocked = false;
let activePassword = '';
let source = '';

export async function unlockAdmin(password, remoteVerifier) {
  const candidate = String(password || '');
  if (!candidate) return { ok: false, message: 'Hãy nhập mật khẩu.' };
  if (typeof remoteVerifier === 'function') {
    const remote = await remoteVerifier(candidate);
    if (remote === true) { unlocked = true; activePassword = candidate; source = 'supabase'; return { ok: true, source }; }
    if (remote === false) return { ok: false, message: 'Mật khẩu không đúng.' };
  }
  const expected = localStorage.getItem(LOCAL_PASSWORD_KEY) || DEFAULT_PASSWORD_HASH;
  const actual = await hashPassword(candidate);
  if (actual !== expected) return { ok: false, message: 'Mật khẩu không đúng.' };
  unlocked = true; activePassword = candidate; source = 'local';
  return { ok: true, source };
}

export function lockAdmin() { unlocked = false; activePassword = ''; source = ''; }
export function isAdminUnlocked() { return unlocked; }
export function getAdminPassword() { return unlocked ? activePassword : ''; }
export function getAdminSource() { return source; }

export async function setLocalAdminPassword(newPassword) {
  if (String(newPassword || '').length < 8) throw new Error('Mật khẩu mới phải có ít nhất 8 ký tự.');
  localStorage.setItem(LOCAL_PASSWORD_KEY, await hashPassword(newPassword));
  activePassword = String(newPassword);
  return true;
}

export async function changeLocalAdminPassword(currentPassword, newPassword) {
  const expected = localStorage.getItem(LOCAL_PASSWORD_KEY) || DEFAULT_PASSWORD_HASH;
  if (await hashPassword(currentPassword) !== expected) return false;
  if (String(newPassword || '').length < 8) throw new Error('Mật khẩu mới phải có ít nhất 8 ký tự.');
  localStorage.setItem(LOCAL_PASSWORD_KEY, await hashPassword(newPassword));
  activePassword = String(newPassword);
  return true;
}

export async function hashPassword(value) {
  const bytes = new TextEncoder().encode(String(value || ''));
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('');
}
