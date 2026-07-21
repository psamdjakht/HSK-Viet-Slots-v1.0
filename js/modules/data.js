const levelCache = new Map();
let metaCache = null;
let examplesCache = null;

export async function loadMeta() {
  if (metaCache) return metaCache;
  const res = await fetch('./data/meta.json');
  if (!res.ok) throw new Error('Không tải được thông tin dữ liệu.');
  metaCache = await res.json();
  return metaCache;
}

export async function loadLevel(level) {
  const key = String(level);
  if (levelCache.has(key)) return levelCache.get(key);
  const res = await fetch(`./data/levels/hsk${key}.json`);
  if (!res.ok) throw new Error(`Không tải được dữ liệu HSK ${key}.`);
  const payload = await res.json();
  const words = payload.words || [];
  levelCache.set(key, words);
  return words;
}

export async function loadLevelsUpTo(level) {
  const max = Math.max(1, Math.min(7, Number(level)));
  const groups = await Promise.all(Array.from({ length: max }, (_, i) => loadLevel(i + 1)));
  return groups.flat();
}

export async function loadExamples() {
  if (examplesCache) return examplesCache;
  const res = await fetch('./data/examples.json');
  if (!res.ok) throw new Error('Không tải được câu ví dụ.');
  const payload = await res.json();
  examplesCache = payload.examples || [];
  return examplesCache;
}

export function primaryMeaning(word) {
  return word?.meaning || word?.senses?.[0]?.vi || 'Chưa có nghĩa';
}

export function verificationLabel(status) {
  return {
    doi_chieu_chinh_xac: 'Đối chiếu đúng chữ và pinyin',
    kiem_tra_thu_cong: 'Đã kiểm tra thủ công',
    chuan_hoa_hsk1: 'HSK 1 chuẩn hóa ban đầu',
    chuan_hoa_hsk2: 'HSK 2 chuẩn hóa hệ thống',
    chuan_hoa_hsk3: 'HSK 3 chuẩn hóa hệ thống',
    chuan_hoa_hsk4: 'HSK 4 chuẩn hóa hệ thống',
    chuan_hoa_hsk5: 'HSK 5 chuẩn hóa hệ thống',
    chuan_hoa_hsk6: 'HSK 6 chuẩn hóa hệ thống',
    chuan_hoa_hsk7: 'HSK 7–9 chuẩn hóa hệ thống',
    admin_da_sua: 'Đã được quản trị viên sửa',
    can_ra_soat: 'Cần rà soát thêm'
  }[status] || 'Chưa xác định';
}
