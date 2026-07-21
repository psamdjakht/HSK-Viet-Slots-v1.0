export function computeWeakWords(words, slot, limit = 50) {
  const attemptsByWord = new Map();
  for (const attempt of slot.attemptLog || []) {
    if (!attempt.wordId) continue;
    const row = attemptsByWord.get(attempt.wordId) || { total: 0, wrong: 0, lastWrongAt: 0, activities: new Set() };
    row.total += 1;
    if (!attempt.correct) {
      row.wrong += 1;
      row.lastWrongAt = Math.max(row.lastWrongAt, Number(attempt.at || 0));
      row.activities.add(attempt.activity || attempt.mode || 'quiz');
    }
    attemptsByWord.set(attempt.wordId, row);
  }
  const wordMap = new Map(words.map(word => [word.id, word]));
  const scores = [];
  for (const [wordId, aggregate] of attemptsByWord.entries()) {
    const word = wordMap.get(wordId);
    if (!word) continue;
    const relatedCards = Object.entries(slot.cards || {}).filter(([key]) => key.startsWith(`${wordId}::`)).map(([, card]) => card);
    const lapses = relatedCards.reduce((sum, card) => sum + Number(card.lapses || 0), 0);
    const difficulty = relatedCards.length ? Math.max(...relatedCards.map(card => Number(card.difficulty || 5))) : 5;
    const accuracy = aggregate.total ? (aggregate.total - aggregate.wrong) / aggregate.total : 1;
    const recency = aggregate.lastWrongAt ? Math.max(0, 7 - (Date.now() - aggregate.lastWrongAt) / 86400000) : 0;
    const score = aggregate.wrong * 6 + lapses * 4 + (1 - accuracy) * 10 + Math.max(0, difficulty - 5) * 2 + recency;
    if (score <= 0) continue;
    scores.push({
      word, score, wrong: aggregate.wrong, total: aggregate.total,
      accuracy: Math.round(accuracy * 100), lapses,
      reason: aggregate.wrong ? `Sai ${aggregate.wrong}/${aggregate.total} lần` : `Độ khó ${difficulty.toFixed(1)}`
    });
  }
  return scores.sort((a, b) => b.score - a.score).slice(0, limit);
}
