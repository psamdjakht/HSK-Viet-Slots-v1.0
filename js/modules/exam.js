import { primaryMeaning } from './data.js';
import { segmentChinese, normalizeChinese } from './activities.js';

export const EXAM_TYPES = {
  meaning: 'Chọn nghĩa',
  pinyin: 'Chọn pinyin',
  listening: 'Nghe chọn từ',
  fill: 'Điền từ',
  order: 'Sắp xếp câu'
};

export function questionBankSummary(words, examples) {
  return {
    meaning: words.length,
    pinyin: words.length,
    listening: words.length,
    fill: examples.length,
    order: examples.length,
    total: words.length * 3 + examples.length * 2
  };
}

export function buildMockExam({ words, examples, level, seed = Date.now(), size = 30 }) {
  if (!Array.isArray(words) || words.length < 12) throw new Error('Chưa đủ dữ liệu từ vựng để tạo đề.');
  const rng = mulberry32(hashSeed(seed));
  const usableExamples = (examples || []).filter(ex => Number(ex.level) <= Number(level));
  const distribution = distributeSize(size, usableExamples.length > 4);
  const questions = [];
  const chosen = new Set();

  for (let i = 0; i < distribution.meaning; i += 1) questions.push(makeWordChoice('meaning', pickUnique(words, chosen, rng), words, rng));
  for (let i = 0; i < distribution.pinyin; i += 1) questions.push(makeWordChoice('pinyin', pickUnique(words, chosen, rng), words, rng));
  for (let i = 0; i < distribution.listening; i += 1) questions.push(makeWordChoice('listening', pickUnique(words, chosen, rng), words, rng));

  const examplePool = sample(usableExamples, distribution.fill + distribution.order, rng);
  for (let i = 0; i < distribution.fill; i += 1) questions.push(makeFill(examplePool[i], usableExamples, rng));
  for (let i = 0; i < distribution.order; i += 1) questions.push(makeOrder(examplePool[distribution.fill + i] || examplePool[i], rng));

  while (questions.length < size) questions.push(makeWordChoice('meaning', pickUnique(words, chosen, rng), words, rng));
  shuffleRng(questions, rng);
  return {
    id: `MOCK-L${level}-${String(seed)}`,
    level: String(level),
    title: `Đề mô phỏng HSK ${level}`,
    disclaimer: 'Đề luyện nội bộ theo dữ liệu ứng dụng, không phải đề thi HSK chính thức.',
    durationMinutes: Math.max(15, Math.ceil(size * 0.9)),
    createdAt: new Date().toISOString(),
    seed: String(seed),
    questions: questions.slice(0, size)
  };
}

export function scoreExam(exam, answers) {
  const details = exam.questions.map((question, index) => {
    const answer = answers[index];
    const correct = evaluateAnswer(question, answer);
    return {
      index, id: question.id, type: question.type, correct,
      answer: answer ?? '', correctAnswer: question.correct,
      prompt: question.prompt, explanation: question.explanation
    };
  });
  const correctCount = details.filter(item => item.correct).length;
  const byType = {};
  for (const type of Object.keys(EXAM_TYPES)) {
    const rows = details.filter(item => item.type === type);
    if (!rows.length) continue;
    const correct = rows.filter(item => item.correct).length;
    byType[type] = { total: rows.length, correct, score: Math.round(correct / rows.length * 100) };
  }
  return {
    score: Math.round(correctCount / Math.max(1, details.length) * 100),
    correct: correctCount,
    total: details.length,
    byType,
    details
  };
}

export function evaluateAnswer(question, answer) {
  if (question.type === 'order') {
    const value = Array.isArray(answer) ? answer.join('') : String(answer || '');
    return normalizeChinese(value) === normalizeChinese(question.correct);
  }
  return String(answer ?? '') === String(question.correct ?? '');
}

function makeWordChoice(type, word, words, rng) {
  const answerFn = type === 'meaning' ? primaryMeaning : type === 'pinyin' ? w => w.pinyin : w => w.simplified;
  const correct = answerFn(word);
  const pool = sample(words.filter(item => item.id !== word.id && answerFn(item) !== correct), 24, rng);
  const options = [correct];
  for (const item of pool) {
    const value = answerFn(item);
    if (!options.includes(value)) options.push(value);
    if (options.length === 4) break;
  }
  shuffleRng(options, rng);
  return {
    id: `${type}-${word.id}-${Math.floor(rng() * 1e8)}`,
    type,
    wordId: word.id,
    audioText: type === 'listening' ? word.simplified : '',
    prompt: type === 'listening' ? 'Nghe và chọn chữ Hán đúng' : word.simplified,
    correct,
    options,
    explanation: `${word.simplified} · ${word.pinyin} · ${word.senses?.map(s => s.vi).slice(0, 3).join('; ') || primaryMeaning(word)}`
  };
}

function makeFill(example, examples, rng) {
  const source = example || examples[Math.floor(rng() * examples.length)];
  const blanked = source.zh.includes(source.target) ? source.zh.replace(source.target, '______') : `______：${source.zh}`;
  const candidates = sample(examples.filter(item => item.target !== source.target), 20, rng);
  const options = [source.target];
  for (const item of candidates) {
    if (!options.includes(item.target)) options.push(item.target);
    if (options.length === 4) break;
  }
  shuffleRng(options, rng);
  return {
    id: `fill-${source.id}-${Math.floor(rng() * 1e8)}`,
    type: 'fill', wordId: source.wordId, prompt: blanked,
    correct: source.target, options,
    explanation: `${source.zh}\n${source.sentencePinyin}\n${source.vi}`
  };
}

function makeOrder(example, rng) {
  const tokens = segmentChinese(example.zh);
  const shuffled = [...tokens];
  shuffleRng(shuffled, rng);
  if (shuffled.join('') === tokens.join('') && shuffled.length > 1) [shuffled[0], shuffled[1]] = [shuffled[1], shuffled[0]];
  return {
    id: `order-${example.id}-${Math.floor(rng() * 1e8)}`,
    type: 'order', wordId: example.wordId, prompt: example.vi,
    correct: example.zh, tokens, shuffled,
    explanation: `${example.zh}\n${example.sentencePinyin}\n${example.vi}`
  };
}

function distributeSize(size, hasSentences) {
  if (!hasSentences) return { meaning: Math.ceil(size * .5), pinyin: Math.floor(size * .25), listening: Math.floor(size * .25), fill: 0, order: 0 };
  const base = { meaning: Math.round(size / 3), pinyin: Math.round(size / 6), listening: Math.round(size / 6), fill: Math.round(size / 6), order: Math.round(size / 6) };
  let total = Object.values(base).reduce((a, b) => a + b, 0);
  while (total > size) { base.meaning -= 1; total -= 1; }
  while (total < size) { base.meaning += 1; total += 1; }
  return base;
}

function pickUnique(items, used, rng) {
  for (let i = 0; i < 100; i += 1) {
    const item = items[Math.floor(rng() * items.length)];
    if (!used.has(item.id)) { used.add(item.id); return item; }
  }
  return items[Math.floor(rng() * items.length)];
}

function sample(items, count, rng) {
  const copy = [...items];
  shuffleRng(copy, rng);
  return copy.slice(0, Math.min(count, copy.length));
}

function shuffleRng(array, rng) {
  for (let i = array.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rng() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

function hashSeed(seed) {
  const text = String(seed);
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function mulberry32(a) {
  return function rng() {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
