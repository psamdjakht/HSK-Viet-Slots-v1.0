const STANDARD_LEVELS = ['1', '2', '3', '4', '5', '6', '7'];
const QUALITY_URLS = Object.fromEntries(STANDARD_LEVELS.map(level => [level, `./data/hsk${level}-quality.json`]));
const GRAMMAR_URLS = Object.fromEntries(STANDARD_LEVELS.map(level => [level, `./data/hsk${level}-grammar.json`]));
const LOCAL_KEY = 'hsk_content_overrides_v1';
const qualityCache = new Map();
const grammarCache = new Map();
let overrides = {};

export function standardizedLevels() { return [...STANDARD_LEVELS]; }
export function isStandardizedLevel(level) { return STANDARD_LEVELS.includes(String(level)); }

export async function initContentSystem(remoteRows = []) {
  await Promise.all(STANDARD_LEVELS.flatMap(level => [loadQuality(level), loadGrammar(level)]));
  overrides = readLocalOverrides();
  for (const row of remoteRows || []) {
    if (!row?.word_id || !row.patch) continue;
    const local = overrides[row.word_id];
    const remoteTime = new Date(row.updated_at || row.patch.updatedAt || 0).getTime();
    const localTime = new Date(local?.updatedAt || 0).getTime();
    if (!local || remoteTime > localTime) overrides[row.word_id] = { ...row.patch, updatedAt: row.updated_at || row.patch.updatedAt };
  }
  writeLocalOverrides();
  return {
    quality: Object.fromEntries(STANDARD_LEVELS.map(level => [level, qualityCache.get(level)?.meta || null])),
    grammar: Object.fromEntries(STANDARD_LEVELS.map(level => [level, grammarCache.get(level)?.meta || null])),
    overrideCount: Object.keys(overrides).length
  };
}

export async function loadQuality(level = '1') {
  const key = String(level);
  if (!isStandardizedLevel(key)) return { meta: { level: key, wordCount: 0 }, words: {} };
  if (qualityCache.has(key)) return qualityCache.get(key);
  const response = await fetch(QUALITY_URLS[key]);
  if (!response.ok) throw new Error(`Không tải được gói chuẩn hóa HSK ${key}.`);
  const payload = await response.json();
  qualityCache.set(key, payload);
  return payload;
}

export async function loadGrammar(level = '1') {
  const key = String(level);
  if (!isStandardizedLevel(key)) return { meta: { level: key, itemCount: 0 }, items: [] };
  if (grammarCache.has(key)) return grammarCache.get(key);
  const response = await fetch(GRAMMAR_URLS[key]);
  if (!response.ok) throw new Error(`Không tải được ngữ pháp HSK ${key}.`);
  const payload = await response.json();
  grammarCache.set(key, payload);
  return payload;
}

export function applyContentToWords(words) {
  return (words || []).map(word => {
    const level = String(word.level);
    if (!isStandardizedLevel(level)) return { ...word };
    const pack = qualityCache.get(level)?.words?.[word.id] || {};
    const patch = overrides[word.id] || {};
    const normalizedSenses = arrayValue(patch.senses, pack.normalizedSenses, word.senses?.map(s => s.vi));
    const meaning = textValue(patch.primaryMeaning, pack.primaryMeaning, word.meaning, normalizedSenses[0], 'Chưa có nghĩa');
    const example = mergeExample(pack.example || word.example, patch.example);
    return {
      ...word,
      meaning,
      senses: normalizedSenses.map((vi, index) => ({ id: `${word.id.toLowerCase()}-q${String(index + 1).padStart(2, '0')}`, vi })),
      pos: arrayValue(patch.pos, pack.pos, word.pos),
      topic: textValue(patch.topic, pack.topic, 'Từ vựng tổng hợp'),
      measureWords: arrayValue(patch.measureWords, pack.measureWords),
      usageNote: textValue(patch.usageNote, pack.usageNote),
      collocations: arrayValue(patch.collocations, pack.collocations),
      confusables: arrayValue(patch.confusables, pack.confusables),
      example,
      verification: patch.updatedAt ? 'admin_da_sua' : `chuan_hoa_hsk${level}`,
      contentUpdatedAt: patch.updatedAt || pack.standardization?.updatedAt || null,
      contentSource: patch.updatedAt ? 'admin' : 'quality-pack'
    };
  });
}

export function buildEffectiveExamples(baseExamples, words) {
  const map = new Map((baseExamples || []).map(item => [item.wordId, { ...item }]));
  for (const word of words || []) {
    if (!isStandardizedLevel(word.level) || !word.example?.exerciseEligible) continue;
    map.set(word.id, {
      id: map.get(word.id)?.id || `EX-${word.id}`,
      wordId: word.id,
      level: String(word.level),
      target: word.simplified,
      traditional: word.traditional,
      pinyin: word.pinyin,
      meaning: word.meaning,
      zh: word.example.zh,
      sentencePinyin: word.example.pinyin,
      vi: word.example.vi,
      status: word.example.status || 'admin_da_sua'
    });
  }
  return [...map.values()];
}

export function getContentOverride(wordId) { return overrides[wordId] ? structuredCloneSafe(overrides[wordId]) : null; }
export function getAllContentOverrides() { return structuredCloneSafe(overrides); }

export function saveLocalContentOverride(wordId, patch) {
  if (!wordId) throw new Error('Thiếu ID từ.');
  const normalized = normalizePatch(patch);
  normalized.updatedAt = new Date().toISOString();
  overrides[wordId] = normalized;
  writeLocalOverrides();
  return structuredCloneSafe(normalized);
}

export function deleteLocalContentOverride(wordId) {
  delete overrides[wordId];
  writeLocalOverrides();
}

export function exportContentOverrides() {
  return JSON.stringify({ app: 'HSK Việt', type: 'content-overrides', version: 2, standardizedLevels: STANDARD_LEVELS, exportedAt: new Date().toISOString(), overrides }, null, 2);
}

export function importContentOverrides(payload) {
  const parsed = typeof payload === 'string' ? JSON.parse(payload) : payload;
  if (!parsed?.overrides || typeof parsed.overrides !== 'object') throw new Error('Tệp chỉnh sửa nội dung không hợp lệ.');
  for (const [wordId, patch] of Object.entries(parsed.overrides)) overrides[wordId] = normalizePatch(patch);
  writeLocalOverrides();
  return Object.keys(parsed.overrides).length;
}

export function qualitySummary(words, level = null) {
  const rows = (words || []).filter(word => !level || String(word.level) === String(level));
  return {
    words: rows.length,
    withUsageNote: rows.filter(word => word.usageNote).length,
    withTopic: rows.filter(word => word.topic).length,
    withExample: rows.filter(word => word.example).length,
    exerciseExamples: rows.filter(word => word.example?.exerciseEligible).length,
    withCollocations: rows.filter(word => word.collocations?.length).length,
    overridden: rows.filter(word => word.contentSource === 'admin').length
  };
}

function normalizePatch(patch = {}) {
  return {
    primaryMeaning: String(patch.primaryMeaning || '').trim(),
    senses: normalizeArray(patch.senses),
    pos: normalizeArray(patch.pos),
    topic: String(patch.topic || '').trim(),
    measureWords: normalizeArray(patch.measureWords),
    usageNote: String(patch.usageNote || '').trim(),
    collocations: normalizeArray(patch.collocations),
    confusables: normalizeArray(patch.confusables),
    example: patch.example ? {
      zh: String(patch.example.zh || '').trim(),
      pinyin: String(patch.example.pinyin || '').trim(),
      vi: String(patch.example.vi || '').trim(),
      status: 'admin_da_sua', kind: 'usage', exerciseEligible: Boolean(patch.example.exerciseEligible)
    } : null,
    updatedAt: patch.updatedAt || new Date().toISOString()
  };
}

function mergeExample(base, patch) {
  if (!patch) return base ? { ...base } : null;
  const merged = { ...(base || {}), ...patch };
  if (!merged.zh) return null;
  return merged;
}
function textValue(...values) { return values.find(value => typeof value === 'string' && value.trim())?.trim() || ''; }
function arrayValue(...values) { for (const value of values) { const arr = normalizeArray(value); if (arr.length) return arr; } return []; }
function normalizeArray(value) {
  if (Array.isArray(value)) return [...new Set(value.map(item => String(item).trim()).filter(Boolean))];
  if (typeof value === 'string') return [...new Set(value.split(/[\n,;]+/).map(item => item.trim()).filter(Boolean))];
  return [];
}
function readLocalOverrides() { try { const value = JSON.parse(localStorage.getItem(LOCAL_KEY) || '{}'); return value && typeof value === 'object' ? value : {}; } catch { return {}; } }
function writeLocalOverrides() { localStorage.setItem(LOCAL_KEY, JSON.stringify(overrides)); }
function structuredCloneSafe(value) { return typeof structuredClone === 'function' ? structuredClone(value) : JSON.parse(JSON.stringify(value)); }
