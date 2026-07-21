const SLOT_PREFIX = 'hsk_viet_slot_v3_';
const LEGACY_SLOT_PREFIX = 'hsk_viet_slot_v2_';
const ACTIVE_SLOT_KEY = 'hsk_viet_active_slot_v3';
const LEGACY_ACTIVE_SLOT_KEY = 'hsk_viet_active_slot_v2';
const DELETED_SLOTS_KEY = 'hsk_viet_deleted_slots_v3';
export const SLOT_COUNT = 10;
let cloudAdapter = null;

export function configureCloudStorage(adapter) {
  cloudAdapter = adapter || null;
}

export function createEmptySlot(id, name = '') {
  const now = new Date().toISOString();
  return {
    schemaVersion: 3,
    id,
    profile: { name: name.trim(), createdAt: now, updatedAt: now },
    settings: {
      level: '1', mode: 'hanzi-vi', sessionSize: 20, audio: true,
      showTraditional: false, defaultActivity: 'quiz'
    },
    plan: {
      targetLevel: '4', targetDate: '', minutesPerDay: 20, daysPerWeek: 6,
      newWordsPerDay: 20, createdAt: now
    },
    cards: {},
    history: {},
    attemptLog: [],
    sessions: [],
    examAttempts: [],
    stats: {
      answered: 0, correct: 0, sessions: 0, studySeconds: 0,
      lastStudyDate: null, currentStreak: 0, longestStreak: 0
    }
  };
}

export function loadSlot(id) {
  const raw = localStorage.getItem(SLOT_PREFIX + id) || localStorage.getItem(LEGACY_SLOT_PREFIX + id);
  if (!raw) return null;
  try {
    const slot = migrateSlot(JSON.parse(raw), id);
    if (!localStorage.getItem(SLOT_PREFIX + id)) localStorage.setItem(SLOT_PREFIX + id, JSON.stringify(slot));
    return slot;
  }
  catch { return null; }
}

export function saveSlot(slot, options = {}) {
  clearDeletedSlot(slot.id);
  slot.profile.updatedAt = new Date().toISOString();
  localStorage.setItem(SLOT_PREFIX + slot.id, JSON.stringify(slot));
  if (options.remote !== false && cloudAdapter?.saveSlot) cloudAdapter.saveSlot(structuredCloneSafe(slot));
  return slot;
}

export function saveSlotLocalOnly(slot) {
  return saveSlot(slot, { remote: false });
}

export function ensureSlot(id, name = '') {
  let slot = loadSlot(id);
  if (!slot) slot = createEmptySlot(id, name);
  if (name.trim()) slot.profile.name = name.trim();
  return saveSlot(slot);
}

export function resetSlot(id, options = {}) {
  localStorage.removeItem(SLOT_PREFIX + id);
  localStorage.removeItem(LEGACY_SLOT_PREFIX + id);
  if (getActiveSlotId() === id) { localStorage.removeItem(ACTIVE_SLOT_KEY); localStorage.removeItem(LEGACY_ACTIVE_SLOT_KEY); }
  markDeletedSlot(id);
  if (options.remote !== false && cloudAdapter?.deleteSlot) {
    Promise.resolve(cloudAdapter.deleteSlot(id)).then(ok => { if (ok) clearDeletedSlot(id); }).catch(() => undefined);
  }
}

export function getDeletedSlots() {
  try {
    const parsed = JSON.parse(localStorage.getItem(DELETED_SLOTS_KEY) || '{}');
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch { return {}; }
}

export function clearDeletedSlot(id) {
  const deleted = getDeletedSlots();
  if (!(String(id) in deleted)) return;
  delete deleted[String(id)];
  localStorage.setItem(DELETED_SLOTS_KEY, JSON.stringify(deleted));
}

function markDeletedSlot(id) {
  const deleted = getDeletedSlots();
  deleted[String(id)] = new Date().toISOString();
  localStorage.setItem(DELETED_SLOTS_KEY, JSON.stringify(deleted));
}

export function listSlots() {
  return Array.from({ length: SLOT_COUNT }, (_, i) => {
    const id = i + 1;
    const data = loadSlot(id);
    return {
      id,
      name: data?.profile?.name || '',
      answered: data?.stats?.answered || 0,
      lastStudyDate: data?.stats?.lastStudyDate || null,
      level: data?.settings?.level || '1',
      cloudUpdatedAt: data?.profile?.updatedAt || null
    };
  });
}

export function setActiveSlotId(id) {
  localStorage.setItem(ACTIVE_SLOT_KEY, String(id));
}

export function getActiveSlotId() {
  const value = Number(localStorage.getItem(ACTIVE_SLOT_KEY) || localStorage.getItem(LEGACY_ACTIVE_SLOT_KEY));
  return value >= 1 && value <= SLOT_COUNT ? value : null;
}

export function exportSlot(slot) {
  return JSON.stringify({ app: 'HSK Viet Slots', schemaVersion: 3, exportedAt: new Date().toISOString(), slot }, null, 2);
}

export function importSlot(id, payload) {
  const parsed = typeof payload === 'string' ? JSON.parse(payload) : payload;
  if (!parsed?.slot || typeof parsed.slot !== 'object') throw new Error('Tệp không đúng định dạng sao lưu.');
  const slot = migrateSlot(parsed.slot, id);
  slot.id = id;
  return saveSlot(slot);
}

export function allLocalSlots() {
  return Array.from({ length: SLOT_COUNT }, (_, i) => loadSlot(i + 1)).filter(Boolean);
}

export function migrateSlot(input, id) {
  const base = createEmptySlot(id, input?.profile?.name || '');
  const oldDaily = Number(input?.settings?.dailyNew);
  const slot = {
    ...base,
    ...input,
    id,
    profile: { ...base.profile, ...(input?.profile || {}) },
    settings: {
      ...base.settings,
      ...(input?.settings || {}),
      sessionSize: Number(input?.settings?.sessionSize || oldDaily || base.settings.sessionSize)
    },
    plan: { ...base.plan, ...(input?.plan || {}) },
    cards: input?.cards && typeof input.cards === 'object' ? input.cards : {},
    history: input?.history && typeof input.history === 'object' ? input.history : {},
    attemptLog: Array.isArray(input?.attemptLog) ? input.attemptLog.slice(-2000) : [],
    sessions: Array.isArray(input?.sessions) ? input.sessions.slice(-180) : [],
    examAttempts: Array.isArray(input?.examAttempts) ? input.examAttempts.slice(-30) : [],
    stats: { ...base.stats, ...(input?.stats || {}) }
  };
  delete slot.settings.dailyNew;
  slot.schemaVersion = 3;
  return slot;
}

function structuredCloneSafe(value) {
  return typeof structuredClone === 'function' ? structuredClone(value) : JSON.parse(JSON.stringify(value));
}
