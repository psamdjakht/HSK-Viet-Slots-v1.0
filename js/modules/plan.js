export function planSummary(slot, meta, now = new Date()) {
  const plan = slot.plan || {};
  const target = Math.max(1, Math.min(7, Number(plan.targetLevel || 1)));
  const totalTarget = Object.entries(meta?.levels || {})
    .filter(([level]) => Number(level) <= target)
    .reduce((sum, [, count]) => sum + Number(count || 0), 0);
  const learnedIds = new Set(Object.keys(slot.cards || {}).map(key => key.split('::')[0]));
  const learned = learnedIds.size;
  const remaining = Math.max(0, totalTarget - learned);
  const studyDays = countStudyDays(now, plan.targetDate, Number(plan.daysPerWeek || 6));
  const requiredPerStudyDay = studyDays > 0 ? Math.ceil(remaining / studyDays) : remaining;
  const recent = recentPerformance(slot, 14, now);
  const projectedDays = recent.wordsPerStudyDay > 0 ? Math.ceil(remaining / recent.wordsPerStudyDay) : null;
  return {
    target, totalTarget, learned, remaining, studyDays, requiredPerStudyDay,
    recentWordsPerDay: recent.wordsPerStudyDay, projectedDays,
    onTrack: studyDays > 0 && recent.wordsPerStudyDay >= requiredPerStudyDay,
    completionPct: totalTarget ? Math.min(100, Math.round(learned / totalTarget * 100)) : 0
  };
}

export function updateStreak(slot, date = new Date()) {
  const today = dateKey(date);
  const yesterday = dateKey(new Date(date.getTime() - 86400000));
  const previous = slot.stats.lastStudyDate ? dateKey(new Date(slot.stats.lastStudyDate)) : null;
  if (previous === today) return;
  slot.stats.currentStreak = previous === yesterday ? Number(slot.stats.currentStreak || 0) + 1 : 1;
  slot.stats.longestStreak = Math.max(Number(slot.stats.longestStreak || 0), slot.stats.currentStreak);
}

export function todayPlan(slot, dueCount = 0) {
  const newTarget = Math.max(1, Number(slot.plan?.newWordsPerDay || slot.settings?.sessionSize || 20));
  const minutes = Math.max(5, Number(slot.plan?.minutesPerDay || 20));
  return { newTarget, reviewTarget: Math.min(Math.max(0, dueCount), Math.max(10, newTarget * 2)), minutes };
}

function countStudyDays(startDate, endDateText, daysPerWeek) {
  const end = endDateText ? new Date(`${endDateText}T23:59:59`) : null;
  if (!end || Number.isNaN(end.getTime()) || end <= startDate) return 0;
  const totalDays = Math.ceil((end - startDate) / 86400000);
  return Math.max(1, Math.floor(totalDays * Math.max(1, Math.min(7, daysPerWeek)) / 7));
}

function recentPerformance(slot, dayCount, now) {
  let totalWords = 0;
  let activeDays = 0;
  for (let i = 0; i < dayCount; i += 1) {
    const date = dateKey(new Date(now.getTime() - i * 86400000));
    const h = slot.history?.[date];
    if (h?.words?.length) {
      activeDays += 1;
      totalWords += h.words.length;
    }
  }
  return { wordsPerStudyDay: activeDays ? Math.round(totalWords / activeDays) : 0, activeDays };
}

function dateKey(date) { return date.toISOString().slice(0, 10); }
