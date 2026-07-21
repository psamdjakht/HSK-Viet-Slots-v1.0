import { primaryMeaning } from './data.js';
import { isDue } from './srs.js';

export const MODES = {
  'hanzi-vi': { label: 'Chữ Hán → nghĩa Việt', prompt: w => w.simplified, answer: w => primaryMeaning(w), promptType: 'hanzi' },
  'vi-hanzi': { label: 'Nghĩa Việt → chữ Hán', prompt: w => primaryMeaning(w), answer: w => w.simplified, promptType: 'text' },
  'hanzi-pinyin': { label: 'Chữ Hán → pinyin', prompt: w => w.simplified, answer: w => w.pinyin, promptType: 'hanzi' },
  'pinyin-hanzi': { label: 'Pinyin → chữ Hán', prompt: w => w.pinyin, answer: w => w.simplified, promptType: 'text' }
};

export function cardKey(wordId, mode) {
  return `${wordId}::${mode}`;
}

export function buildStudyQueue(words, slot, mode, limit = 20, now = Date.now()) {
  const due = [];
  const fresh = [];
  const learned = [];
  for (const word of words) {
    const state = slot.cards[cardKey(word.id, mode)];
    if (!state) fresh.push(word);
    else if (isDue(state, now)) due.push(word);
    else learned.push(word);
  }
  shuffle(due);
  shuffle(fresh);
  shuffle(learned);
  const queue = [...due, ...fresh, ...learned].slice(0, Math.max(1, limit));
  return { queue, dueCount: due.length, newCount: fresh.length };
}

export function makeQuestion(word, words, mode, optionCount = 4) {
  const config = MODES[mode] || MODES['hanzi-vi'];
  const correct = config.answer(word);
  const pool = words.filter(w => w.id !== word.id && config.answer(w) !== correct);
  shuffle(pool);
  const distractors = [];
  for (const candidate of pool) {
    const value = config.answer(candidate);
    if (!distractors.includes(value)) distractors.push(value);
    if (distractors.length >= optionCount - 1) break;
  }
  const options = shuffle([correct, ...distractors]);
  return {
    word,
    mode,
    prompt: config.prompt(word),
    promptType: config.promptType,
    correct,
    options
  };
}

export function shuffle(array) {
  for (let i = array.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}
