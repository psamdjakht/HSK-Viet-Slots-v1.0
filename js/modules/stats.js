export function buildAdvancedStats(slot, days = 30, now = Date.now()) {
  const cutoff = now - days * 86400000;
  const attempts = (slot.attemptLog || []).filter(item => Number(item.at || 0) >= cutoff);
  const byActivity = groupAttempts(attempts, item => item.activity || 'quiz');
  const byMode = groupAttempts(attempts, item => item.mode || item.activity || 'khác');
  const responseTimes = attempts.map(item => Number(item.responseMs || 0)).filter(value => value > 0);
  const cards = Object.values(slot.cards || {});
  const retentionEligible = cards.filter(card => Number(card.total || 0) >= 2);
  const retention = retentionEligible.length
    ? Math.round(retentionEligible.reduce((sum, card) => sum + Number(card.correct || 0) / Math.max(1, Number(card.total || 0)), 0) / retentionEligible.length * 100)
    : 0;
  const daily = [];
  for (let i = days - 1; i >= 0; i -= 1) {
    const date = new Date(now - i * 86400000).toISOString().slice(0, 10);
    const row = slot.history?.[date] || {};
    daily.push({ date, answered: Number(row.answered || 0), correct: Number(row.correct || 0), seconds: Number(row.seconds || 0) });
  }
  return {
    attempts: attempts.length,
    accuracy: attempts.length ? Math.round(attempts.filter(a => a.correct).length / attempts.length * 100) : 0,
    averageResponseMs: responseTimes.length ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length) : 0,
    retention,
    byActivity,
    byMode,
    daily,
    currentStreak: Number(slot.stats?.currentStreak || 0),
    longestStreak: Number(slot.stats?.longestStreak || 0),
    totalMinutes: Math.round(Number(slot.stats?.studySeconds || 0) / 60)
  };
}

function groupAttempts(attempts, keyFn) {
  const map = new Map();
  for (const item of attempts) {
    const key = keyFn(item);
    const row = map.get(key) || { key, total: 0, correct: 0, responseMs: 0 };
    row.total += 1;
    if (item.correct) row.correct += 1;
    row.responseMs += Number(item.responseMs || 0);
    map.set(key, row);
  }
  return [...map.values()].map(row => ({
    ...row,
    accuracy: row.total ? Math.round(row.correct / row.total * 100) : 0,
    averageResponseMs: row.total ? Math.round(row.responseMs / row.total) : 0
  })).sort((a, b) => b.total - a.total);
}
