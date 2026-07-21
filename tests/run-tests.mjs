const tests = [
  './test-srs.mjs','./test-quiz.mjs','./test-data.mjs','./test-activities.mjs',
  './test-plan-stats.mjs','./test-exam.mjs','./test-supabase.mjs','./test-static.mjs',
  './test-dom-contract.mjs','./test-p4-quality-admin.mjs','./test-storage.mjs','./test-p4-runtime.mjs',
  './test-p5-hsk2-4.mjs','./test-p5-runtime.mjs','./test-p6-hsk5-7.mjs','./test-p6-runtime.mjs'
];
for (const test of tests) await import(test);
console.log('\n✓ Toàn bộ kiểm thử P0–P6 đã đạt.');
