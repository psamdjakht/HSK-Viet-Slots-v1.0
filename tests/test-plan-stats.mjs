import assert from 'node:assert/strict';
import { planSummary, updateStreak } from '../js/modules/plan.js';
import { buildAdvancedStats } from '../js/modules/stats.js';
const now = new Date('2026-07-21T08:00:00+07:00');
const slot = {
  plan:{targetLevel:'2',targetDate:'2026-08-21',daysPerWeek:7,newWordsPerDay:20,minutesPerDay:20},
  cards:{'L1-1::hanzi-vi':{total:2,correct:2},'L1-2::hanzi-vi':{total:2,correct:1}},
  history:{}, attemptLog:[
    {at:now.getTime()-1000,correct:true,activity:'quiz',mode:'hanzi-vi',responseMs:1000},
    {at:now.getTime()-500,correct:false,activity:'dictation',mode:'dictation-hanzi',responseMs:3000}
  ], stats:{lastStudyDate:'2026-07-20T08:00:00+07:00',currentStreak:2,longestStreak:2,studySeconds:600}
};
const summary = planSummary(slot,{levels:{1:500,2:772}},now);
assert.equal(summary.totalTarget,1272);
assert.equal(summary.learned,2);
updateStreak(slot,now);
assert.equal(slot.stats.currentStreak,3);
const stats = buildAdvancedStats(slot,30,now.getTime());
assert.equal(stats.accuracy,50);
assert.equal(stats.averageResponseMs,2000);
assert.equal(stats.retention,75);
console.log('✓ P2: kế hoạch, streak và thống kê chuyên sâu.');
