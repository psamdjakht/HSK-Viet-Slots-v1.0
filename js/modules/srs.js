export const GRADES = {
  AGAIN: 0,
  HARD: 1,
  GOOD: 2,
  EASY: 3
};

const MINUTE = 60 * 1000;
const DAY = 24 * 60 * MINUTE;

export function newCardState() {
  return {
    repetitions: 0,
    lapses: 0,
    difficulty: 5,
    stability: 0,
    due: 0,
    lastReview: null,
    correct: 0,
    total: 0,
    lastGrade: null
  };
}

export function reviewCard(previous, grade, now = Date.now()) {
  const card = { ...newCardState(), ...(previous || {}) };
  const g = Math.max(0, Math.min(3, Number(grade)));
  card.total += 1;
  card.lastReview = now;
  card.lastGrade = g;

  if (g === GRADES.AGAIN) {
    card.lapses += 1;
    card.difficulty = clamp(card.difficulty + 1.2, 1, 10);
    card.stability = Math.max(0.15, card.stability * 0.25);
    card.due = now + 10 * MINUTE;
    return card;
  }

  card.correct += 1;
  card.repetitions += 1;
  card.difficulty = clamp(card.difficulty + (g === GRADES.HARD ? 0.35 : g === GRADES.EASY ? -0.45 : -0.12), 1, 10);

  if (card.repetitions === 1) {
    card.stability = g === GRADES.HARD ? 1 : g === GRADES.GOOD ? 3 : 7;
  } else {
    const multiplier = g === GRADES.HARD ? 1.25 : g === GRADES.GOOD ? 1.95 : 2.85;
    const difficultyPenalty = 1 - Math.max(0, card.difficulty - 5) * 0.045;
    card.stability = Math.max(1, card.stability * multiplier * difficultyPenalty);
  }

  card.due = now + Math.round(card.stability) * DAY;
  return card;
}

export function isDue(card, now = Date.now()) {
  return Boolean(card) && (!card.due || card.due <= now);
}

export function dueLabel(card, now = Date.now()) {
  if (!card?.due) return 'mới';
  const diff = card.due - now;
  if (diff <= 0) return 'đến hạn';
  if (diff < DAY) return `${Math.max(1, Math.ceil(diff / MINUTE))} phút`;
  return `${Math.ceil(diff / DAY)} ngày`;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}
