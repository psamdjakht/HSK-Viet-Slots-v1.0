import assert from 'node:assert/strict';
import fs from 'node:fs';
const quality = JSON.parse(fs.readFileSync(new URL('../data/hsk1-quality.json', import.meta.url),'utf8'));
const grammar = JSON.parse(fs.readFileSync(new URL('../data/hsk1-grammar.json', import.meta.url),'utf8'));
const hsk1 = JSON.parse(fs.readFileSync(new URL('../data/levels/hsk1.json', import.meta.url),'utf8'));
assert.equal(Object.keys(quality.words).length, 500);
assert.equal(hsk1.words.length, 500);
for (const word of hsk1.words) {
  const row = quality.words[word.id];
  assert.ok(row, `Thiếu chuẩn hóa ${word.id}`);
  assert.ok(row.primaryMeaning && row.topic && row.usageNote);
  assert.ok(Array.isArray(row.normalizedSenses) && row.normalizedSenses.length);
  assert.ok(row.example?.zh && row.example?.pinyin && row.example?.vi);
}
assert.equal(grammar.items.length, 30);
assert.ok(grammar.items.every(item => item.title && item.formula && item.examples?.length));
const sql = fs.readFileSync(new URL('../supabase/schema.sql', import.meta.url),'utf8');
assert.match(sql,/hsk_content_overrides/i);
assert.match(sql,/admin_verify_hsk_password/i);
assert.match(sql,/admin_save_hsk_content/i);
assert.match(sql,/admin_change_hsk_password/i);
assert.match(sql,/\$2a\$12\$/i);
assert.doesNotMatch(sql,/values\s*\(\s*'main'\s*,\s*crypt\(/i);
const html = fs.readFileSync(new URL('../index.html', import.meta.url),'utf8');
assert.ok(html.includes('admin-primary-meaning'));
assert.ok(html.includes('hsk1-grammar-list'));
console.log('✓ P4: chuẩn hóa đủ 500 từ HSK 1, 30 điểm ngữ pháp và quản trị học liệu.');
