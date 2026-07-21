let standardizedExamplesCache = null;
const readingCache = new Map();

export async function loadStandardizedExamples() {
  if (standardizedExamplesCache) return standardizedExamplesCache;
  const response = await fetch('./data/standardized-examples.json');
  if (!response.ok) throw new Error('Không tải được thư viện câu ví dụ chuẩn hóa.');
  standardizedExamplesCache = await response.json();
  return standardizedExamplesCache;
}

export function attachStandardizedExamples(words, payload = standardizedExamplesCache) {
  const map = payload?.words || {};
  return (words || []).map(word => {
    const bank = (map[word.id] || []).map(item => ({ ...item }));
    let examples = bank;
    if (word.contentSource === 'admin' && word.example?.zh) {
      const adminExample = {
        id: `SE-${word.id}-ADMIN`,
        zh: word.example.zh,
        pinyin: word.example.pinyin || '',
        vi: word.example.vi || '',
        difficulty: Number(word.level) || 1,
        kind: 'usage',
        status: 'admin_da_sua',
        exerciseEligible: Boolean(word.example.exerciseEligible),
        note: 'Câu do quản trị viên chỉnh sửa.'
      };
      examples = [adminExample, ...bank.filter(item => item.kind !== 'usage')];
    }
    const primary = examples.find(item => item.exerciseEligible) || examples[0] || word.example || null;
    return { ...word, examples, example: primary };
  });
}

export async function loadReadingLevel(level) {
  const key = String(level);
  if (!['1','2','3','4','5','6','7'].includes(key)) throw new Error('Đọc hiểu hiện hỗ trợ HSK 1–6 và HSK 7–9.');
  if (readingCache.has(key)) return readingCache.get(key);
  const response = await fetch(`./data/reading/hsk${key}.json`);
  if (!response.ok) throw new Error(`Không tải được bài đọc HSK ${key}.`);
  const payload = await response.json();
  readingCache.set(key, payload);
  return payload;
}

export function buildVocabularyMatcher(words) {
  const entries = (words || [])
    .filter(word => word?.simplified)
    .map(word => ({ text: word.simplified, word }))
    .sort((a, b) => b.text.length - a.text.length || a.text.localeCompare(b.text, 'zh'));
  const byFirst = new Map();
  for (const entry of entries) {
    const first = entry.text[0];
    if (!byFirst.has(first)) byFirst.set(first, []);
    byFirst.get(first).push(entry);
  }
  return byFirst;
}

export function tokenizeChinese(text, matcher) {
  const tokens = [];
  let index = 0;
  while (index < text.length) {
    const candidates = matcher.get(text[index]) || [];
    const match = candidates.find(entry => text.startsWith(entry.text, index));
    if (match) {
      tokens.push({ type: 'word', text: match.text, word: match.word });
      index += match.text.length;
      continue;
    }
    tokens.push({ type: 'text', text: text[index] });
    index += 1;
  }
  return mergePlainTokens(tokens);
}

export function passageVocabularyStats(passage, matcher) {
  const ids = new Set();
  let matchedCharacters = 0;
  for (const sentence of passage?.sentences || []) {
    for (const token of tokenizeChinese(sentence.zh, matcher)) {
      if (token.type === 'word') {
        ids.add(token.word.id);
        matchedCharacters += token.text.length;
      }
    }
  }
  return { uniqueWords: ids.size, matchedCharacters };
}

function mergePlainTokens(tokens) {
  const output = [];
  for (const token of tokens) {
    const last = output[output.length - 1];
    if (token.type === 'text' && last?.type === 'text') last.text += token.text;
    else output.push(token);
  }
  return output;
}
