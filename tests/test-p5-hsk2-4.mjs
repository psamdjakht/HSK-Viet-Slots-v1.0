import assert from 'node:assert/strict';
import fs from 'node:fs';

const expected = { 2: 772, 3: 973, 4: 1000 };
const grammarMin = { 2: 25, 3: 30, 4: 42 };
for (const [level, count] of Object.entries(expected)) {
  const base = JSON.parse(fs.readFileSync(new URL(`../data/levels/hsk${level}.json`, import.meta.url), 'utf8'));
  const quality = JSON.parse(fs.readFileSync(new URL(`../data/hsk${level}-quality.json`, import.meta.url), 'utf8'));
  const grammar = JSON.parse(fs.readFileSync(new URL(`../data/hsk${level}-grammar.json`, import.meta.url), 'utf8'));
  assert.equal(base.words.length, count, `Sai số từ HSK ${level}`);
  assert.equal(Object.keys(quality.words).length, count, `Thiếu gói chuẩn hóa HSK ${level}`);
  for (const word of base.words) {
    const row = quality.words[word.id];
    assert.ok(row, `Thiếu chuẩn hóa ${word.id}`);
    assert.ok(row.primaryMeaning && row.topic && row.usageNote, `Thiếu trường lõi ${word.id}`);
    assert.ok(Array.isArray(row.normalizedSenses) && row.normalizedSenses.length, `Thiếu nghĩa ${word.id}`);
    assert.ok(row.example?.zh && row.example?.pinyin && row.example?.vi, `Thiếu ví dụ ${word.id}`);
    if (word.example) assert.equal(row.example.exerciseEligible, true, `Ví dụ gốc phải được dùng luyện tập ${word.id}`);
    if (row.example.exerciseEligible) assert.ok(['da_duyet','bien_soan_ngu_phap','admin_da_sua'].includes(row.example.status), `Ví dụ luyện tập chưa đủ trạng thái ${word.id}`);
  }
  assert.ok(grammar.items.length >= grammarMin[level], `Thiếu ngữ pháp HSK ${level}`);
  assert.ok(grammar.items.every(item => item.title && item.formula && item.explanation && item.examples?.[0]?.zh && item.examples?.[0]?.pinyin && item.examples?.[0]?.vi));
}

const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
assert.ok(html.includes('quality-library-level'));
assert.ok(html.includes('admin-level-select'));
assert.ok(html.includes('HSK 1–6 và HSK 7–9 chuẩn hóa')); // UI mở rộng nhưng gói HSK 2–4 vẫn phải tồn tại nguyên vẹn
const sw = fs.readFileSync(new URL('../sw.js', import.meta.url), 'utf8');
for (const level of [2,3,4]) {
  assert.ok(sw.includes(`hsk${level}-quality.json`));
  assert.ok(sw.includes(`hsk${level}-grammar.json`));
}
console.log('✓ P5: chuẩn hóa bổ sung HSK 2–4, ngữ pháp đa cấp và giao diện quản trị đa cấp.');
