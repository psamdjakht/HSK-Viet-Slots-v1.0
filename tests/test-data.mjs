import assert from 'node:assert/strict';
import fs from 'node:fs';
const meta = JSON.parse(fs.readFileSync(new URL('../data/meta.json', import.meta.url),'utf8'));
let total = 0;
const wordIds = new Set();
const senseIds = new Set();
for (const level of ['1','2','3','4','5','6','7']) {
  const payload = JSON.parse(fs.readFileSync(new URL(`../data/levels/hsk${level}.json`, import.meta.url),'utf8'));
  assert.equal(payload.words.length, meta.levels[level]);
  for (const word of payload.words) {
    assert.ok(word.id && word.simplified && word.pinyin && word.meaning);
    assert.ok(!wordIds.has(word.id), `Trùng ID từ: ${word.id}`);
    wordIds.add(word.id);
    assert.ok(Array.isArray(word.senses) && word.senses.length > 0);
    for (const sense of word.senses) {
      assert.ok(!senseIds.has(sense.id), `Trùng ID nghĩa: ${sense.id}`);
      senseIds.add(sense.id);
      assert.ok(sense.vi.trim());
    }
  }
  total += payload.words.length;
}
assert.equal(total, 11092);
assert.equal(total, meta.totalWords);
assert.equal(Object.values(meta.verification).reduce((a,b)=>a+b,0), total);
assert.equal(meta.verification.can_ra_soat ?? 0, 0);

// Các trường hợp từng bị nhầm tên riêng/đồng hình phải giữ nghĩa HSK thông dụng.
const allWords = [];
for (const level of ['1','2','3','4','5','6','7']) {
  const payload = JSON.parse(fs.readFileSync(new URL(`../data/levels/hsk${level}.json`, import.meta.url),'utf8'));
  allWords.push(...payload.words);
}
const byId = new Map(allWords.map(word => [word.id, word]));
assert.match(byId.get('L1-0212').meaning, /lạnh/i);
assert.match(byId.get('L1-0266').meaning, /phía nam/i);
assert.match(byId.get('L3-0291').meaning, /hòa bình/i);
assert.match(byId.get('L1-0147').meaning, /phía sau|đằng sau/i);
assert.match(byId.get('L1-0017').meaning, /cốc|ly/i);
console.log(`✓ Dữ liệu: ${total} từ, ${senseIds.size} nghĩa có ID duy nhất.`);
