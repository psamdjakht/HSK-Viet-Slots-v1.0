const tests = [
  './test-srs.mjs','./test-quiz.mjs','./test-data.mjs','./test-activities.mjs',
  './test-plan-stats.mjs','./test-exam.mjs','./test-supabase.mjs','./test-static.mjs',
  './test-dom-contract.mjs','./test-p4-quality-admin.mjs','./test-storage.mjs','./test-p4-runtime.mjs'
];
for (const test of tests) await import(test);
console.log('\n✓ Toàn bộ kiểm thử P0–P4 đã đạt.');
