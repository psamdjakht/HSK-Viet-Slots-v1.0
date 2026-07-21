const QUALITY_URL = './data/hsk1-quality.json';
const GRAMMAR_URL = './data/hsk1-grammar.json';
const LOCAL_KEY = 'hsk_content_overrides_v1';
let qualityCache = null;
let grammarCache = null;
let overrides = {};

export async function initContentSystem(remoteRows = []) {
  const [quality, grammar] = await Promise.all([loadQuality(), loadGrammar()]);
  overrides = readLocalOverrides();
  for (const row of remoteRows || []) {
    if (!row?.word_id || !row.patch) continue;
    const local = overrides[row.word_id];
    const remoteTime = new Date(row.updated_at || row.patch.updatedAt || 0).getTime();
    const localTime = new Date(local?.updatedAt || 0).getTime();
    if (!local || remoteTime > localTime) overrides[row.word_id] = { ...row.patch, updatedAt: row.updated_at || row.patch.updatedAt };
  }
  writeLocalOverrides();
  return { quality: quality.meta, grammar: grammar.meta, overrideCount: Object.keys(overrides).length };
}

export async function loadQuality() {
  if (qualityCache) return qualityCache;
  const response = await fetch(QUALITY_URL);
  if (!response.ok) throw new Error('Không tải được gói chuẩn hóa HSK 1.');
  qualityCache = await response.json();
  return qualityCache;
}

export async function loadGrammar() {
  if (grammarCache) return grammarCache;
  const response = await fetch(GRAMMAR_URL);
  if (!response.ok) throw new Error('Không tải được ngữ pháp HSK 1.');
  grammarCache = await response.json();
  return grammarCache;
}

export function applyContentToWords(words) {
  const qualityWords = qualityCache?.words || {};
  return (words || []).map(word => {
    if (String(word.level) !== '1') return { ...word };
    const pack = qualityWords[word.id] || {};
    const patch = overrides[word.id] || {};
    const normalizedSenses = arrayValue(patch.senses, pack.normalizedSenses, word.senses?.map(s => s.vi));
    const meaning = textValue(patch.primaryMeaning, pack.primaryMeaning, word.meaning, normalizedSenses[0], 'Chưa có nghĩa');
    const example = mergeExample(pack.example || word.example, patch.example);
    return {
      ...word,
      meaning,
      senses: normalizedSenses.map((vi, index) => ({ id: `${word.id.toLowerCase()}-q${String(index + 1).padStart(2, '0')}`, vi })),
      pos: arrayValue(patch.pos, pack.pos, word.pos),
      topic: textValue(patch.topic, pack.topic, 'Từ vựng cơ bản'),
      measureWords: arrayValue(patch.measureWords, pack.measureWords),
      usageNote: textValue(patch.usageNote, pack.usageNote),
      collocations: arrayValue(patch.collocations, pack.collocations),
      confusables: arrayValue(patch.confusables, pack.confusables),
      example,
      verification: patch.updatedAt ? 'admin_da_sua' : 'chuan_hoa_hsk1',
      contentUpdatedAt: patch.updatedAt || pack.standardization?.updatedAt || null,
      contentSource: patch.updatedAt ? 'admin' : 'quality-pack'
    };
  });
}

export function buildEffectiveExamples(baseExamples, words) {
  const map = new Map((baseExamples || []).map(item => [item.wordId, { ...item }]));
  for (const word of words || []) {
    if (String(word.level) !== '1' || !word.example?.exerciseEligible) continue;
    map.set(word.id, {
      id: map.get(word.id)?.id || `EX-${word.id}`,
      wordId: word.id,
      level: '1',
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
  return JSON.stringify({ app: 'HSK Việt', type: 'content-overrides', version: 1, exportedAt: new Date().toISOString(), overrides }, null, 2);
}

export function importContentOverrides(payload) {
  const parsed = typeof payload === 'string' ? JSON.parse(payload) : payload;
  if (!parsed?.overrides || typeof parsed.overrides !== 'object') throw new Error('Tệp chỉnh sửa nội dung không hợp lệ.');
  for (const [wordId, patch] of Object.entries(parsed.overrides)) overrides[wordId] = normalizePatch(patch);
  writeLocalOverrides();
  return Object.keys(parsed.overrides).length;
}

export function qualitySummary(words) {
  const rows = (words || []).filter(word => String(word.level) === '1');
  return {
    words: rows.length,
    withUsageNote: rows.filter(word => word.usageNote).length,
    withTopic: rows.filter(word => word.topic).length,
    withExample: rows.filter(word => word.example).length,
    exerciseExamples: rows.filter(word => word.example?.exerciseEligible).length,
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
