import { SUPABASE_CONFIG } from '../config.js';

const CDN = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';
let client = null;
let user = null;
let status = { enabled: false, connected: false, message: 'Chưa cấu hình Supabase' };
const timers = new Map();
const pending = new Map();
const operationChains = new Map();

export function getCloudStatus() { return { ...status }; }

export async function initCloudSync() {
  const cfg = SUPABASE_CONFIG || {};
  if (!cfg.enabled || !isValidUrl(cfg.url) || !cfg.anonKey) {
    status = { enabled: false, connected: false, message: 'Đang lưu cục bộ' };
    return { status: getCloudStatus(), rows: [], adapter: null };
  }
  status = { enabled: true, connected: false, message: 'Đang kết nối Supabase…' };
  try {
    const { createClient } = await import(CDN);
    client = createClient(cfg.url, cfg.anonKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: false }
    });
    let { data: sessionData, error: sessionError } = await client.auth.getSession();
    if (sessionError) throw sessionError;
    if (!sessionData.session) {
      const result = await client.auth.signInAnonymously({ options: { data: { app: 'hsk-viet-slots' } } });
      if (result.error) throw result.error;
      sessionData = { session: result.data.session };
    }
    user = sessionData.session?.user || null;
    if (!user) throw new Error('Không tạo được phiên ẩn danh.');
    const rows = await fetchRemoteSlots();
    status = { enabled: true, connected: true, message: 'Đã đồng bộ Supabase', userId: user.id };
    return { status: getCloudStatus(), rows, adapter: buildAdapter() };
  } catch (error) {
    console.error('Supabase init:', error);
    status = { enabled: true, connected: false, message: `Không kết nối được: ${error.message || error}` };
    return { status: getCloudStatus(), rows: [], adapter: null };
  }
}

async function fetchRemoteSlots() {
  const table = SUPABASE_CONFIG.table || 'hsk_slots';
  const { data, error } = await client.from(table).select('slot_id,data,updated_at').order('slot_id');
  if (error) throw error;
  return Array.isArray(data) ? data : [];
}

function buildAdapter() {
  return {
    saveSlot(slot) {
      pending.set(slot.id, slot);
      clearTimeout(timers.get(slot.id));
      timers.set(slot.id, setTimeout(() => flushSlot(slot.id), 700));
    },
    deleteSlot(slotId) {
      clearTimeout(timers.get(slotId));
      pending.delete(slotId);
      return enqueueOperation(slotId, () => deleteRemoteSlotNow(slotId));
    },
    flushSlot,
    flushAll
  };
}

export async function syncNow(slot) {
  if (!status.connected || !slot) return false;
  pending.set(slot.id, slot);
  return flushSlot(slot.id);
}

export async function flushSlot(slotId) {
  if (!status.connected || !client || !user) return false;
  clearTimeout(timers.get(slotId));
  timers.delete(slotId);
  const slot = pending.get(slotId);
  if (!slot) return true;
  pending.delete(slotId);
  return enqueueOperation(slotId, async () => {
    const table = SUPABASE_CONFIG.table || 'hsk_slots';
    const row = {
      user_id: user.id,
      slot_id: Number(slot.id),
      data: slot,
      updated_at: slot.profile?.updatedAt || new Date().toISOString()
    };
    const { error } = await client.from(table).upsert(row, { onConflict: 'user_id,slot_id' });
    if (error) {
      console.error('Supabase save:', error);
      pending.set(slotId, slot);
      status = { ...status, connected: false, message: 'Mất kết nối; dữ liệu vẫn lưu trên máy' };
      return false;
    }
    status = { ...status, connected: true, message: 'Đã đồng bộ Supabase' };
    return true;
  });
}

export async function flushAll() {
  const ids = [...pending.keys()];
  return Promise.all(ids.map(flushSlot));
}

async function deleteRemoteSlotNow(slotId) {
  if (!status.connected || !client || !user) return false;
  const table = SUPABASE_CONFIG.table || 'hsk_slots';
  const { error } = await client.from(table).delete().eq('slot_id', Number(slotId)).eq('user_id', user.id);
  if (error) {
    console.error('Supabase delete:', error);
    return false;
  }
  return true;
}

export async function retryCloudConnection() {
  return initCloudSync();
}


function enqueueOperation(slotId, task) {
  const previous = operationChains.get(slotId) || Promise.resolve();
  const next = previous.catch(() => undefined).then(task);
  const tracked = next.finally(() => {
    if (operationChains.get(slotId) === tracked) operationChains.delete(slotId);
  });
  operationChains.set(slotId, tracked);
  return tracked;
}

function isValidUrl(value) {
  try { return /^https:$/.test(new URL(value).protocol); }
  catch { return false; }
}
