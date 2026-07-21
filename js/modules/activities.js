import { primaryMeaning } from './data.js';
import { shuffle } from './quiz.js';

export const ACTIVITIES = {
  quiz: { label: 'Trắc nghiệm từ vựng', srsMode: slot => slot.settings.mode },
  dictation: { label: 'Nghe chép chính tả', srsMode: () => 'dictation-hanzi' },
  fill: { label: 'Điền từ vào câu', srsMode: () => 'fill-sentence' },
  order: { label: 'Sắp xếp câu', srsMode: () => 'order-sentence' },
  weak: { label: 'Ôn sổ từ yếu', srsMode: slot => slot.settings.mode }
};

export function buildDictationQuestion(word) {
  return {
    type: 'dictation', word,
    prompt: 'Nghe và nhập chữ Hán bạn nghe được',
    correct: word.simplified,
    accepted: [word.simplified, word.traditional].filter(Boolean),
    explanation: `${word.simplified} · ${word.pinyin} · ${primaryMeaning(word)}`
  };
}

export function checkDictation(answer, question) {
  const normalized = normalizeChinese(answer);
  return question.accepted.some(value => normalizeChinese(value) === normalized);
}

export function buildFillQuestion(example, examples, optionCount = 4) {
  const blanked = replaceFirst(example.zh, example.target, '______');
  const pool = examples.filter(item => item.id !== example.id && item.target !== example.target);
  shuffle(pool);
  const distractors = [];
  for (const item of pool) {
    if (!distractors.includes(item.target)) distractors.push(item.target);
    if (distractors.length >= optionCount - 1) break;
  }
  return {
    type: 'fill', example, word: example,
    prompt: blanked === example.zh ? `______：${example.zh}` : blanked,
    correct: example.target,
    options: shuffle([example.target, ...distractors]),
    explanation: `${example.zh}\n${example.sentencePinyin}\n${example.vi}`
  };
}

export function buildOrderQuestion(example) {
  let tokens = segmentChinese(example.zh);
  if (tokens.length < 3) tokens = [...example.zh].filter(char => !isPunctuation(char));
  const shuffled = shuffle([...tokens]);
  if (shuffled.join('') === tokens.join('') && shuffled.length > 1) [shuffled[0], shuffled[1]] = [shuffled[1], shuffled[0]];
  return {
    type: 'order', example, word: example,
    prompt: example.vi,
    tokens,
    shuffled,
    correct: normalizeChinese(example.zh),
    explanation: `${example.zh}\n${example.sentencePinyin}\n${example.vi}`
  };
}

export function checkOrder(tokens, question) {
  return normalizeChinese(tokens.join('')) === question.correct;
}

export function segmentChinese(sentence) {
  const clean = String(sentence || '').trim();
  if (!clean) return [];
  try {
    if (typeof Intl !== 'undefined' && Intl.Segmenter) {
      const seg = new Intl.Segmenter('zh', { granularity: 'word' });
      return [...seg.segment(clean)]
        .map(item => item.segment.trim())
        .filter(item => item && ![...item].every(isPunctuation));
    }
  } catch {}
  return [...clean].filter(char => char.trim() && !isPunctuation(char));
}

export function normalizeChinese(value) {
  return String(value || '')
    .normalize('NFKC')
    .replace(/[\s\u3000，。！？；：、“”‘’（）《》〈〉…—,.!?;:'"()\-]/g, '')
    .toLowerCase();
}

export function normalizePinyin(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, '').toLowerCase();
}

function replaceFirst(text, search, replacement) {
  const index = String(text).indexOf(search);
  if (index < 0) return String(text);
  return text.slice(0, index) + replacement + text.slice(index + search.length);
}

function isPunctuation(char) {
  return /[，。！？；：、“”‘’（）《》〈〉…—,.!?;:'"()\-]/u.test(char);
}
