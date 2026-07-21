import assert from 'node:assert/strict';
import fs from 'node:fs';

const payload = JSON.parse(fs.readFileSync(new URL('../data/reading/hsk7.json', import.meta.url), 'utf8'));
assert.equal(payload.meta.version, '7.1.0');
assert.equal(payload.meta.passageCount, 10, 'HSK 7–9 phải có 10 bài đọc');
assert.equal(payload.passages.length, 10, 'Thiếu bài đọc HSK 7–9');

const newIds = [
  'READ-L7-attention-autonomy',
  'READ-L7-university-purpose',
  'READ-L7-food-system-resilience',
  'READ-L7-cultural-translation',
  'READ-L7-heritage-repatriation',
];
const byId = new Map(payload.passages.map(p => [p.id, p]));
for (const id of newIds) {
  const passage = byId.get(id);
  assert.ok(passage, `Thiếu ${id}`);
  assert.ok(passage.actualCharacters >= 1350 && passage.actualCharacters <= 1750, `${id} không gần 1.500 chữ`);
  assert.ok(passage.sentences.length >= 35, `${id} quá ít câu`);
  for (const sentence of passage.sentences) {
    assert.ok(sentence.zh && sentence.pinyin && sentence.vi, `${sentence.id} thiếu chữ Hán, pinyin hoặc dịch Việt`);
  }
}

const meta = JSON.parse(fs.readFileSync(new URL('../data/reading/meta.json', import.meta.url), 'utf8'));
assert.equal(meta.version, '7.1.0');
assert.equal(meta.levels['7'].passages, 10);
assert.equal(meta.levels['7'].lengths.length, 10);

console.log('✓ P9: thêm 5 bài HSK 7–9 khoảng 1.500 chữ, đủ pinyin, highlight nền và dịch từng câu.');
