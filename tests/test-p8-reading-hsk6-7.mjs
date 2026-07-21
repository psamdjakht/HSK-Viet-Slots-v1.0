import assert from 'node:assert/strict';
import fs from 'node:fs';

const targets = { 6: 1000, 7: 1500 };
for (const [level, target] of Object.entries(targets)) {
  const payload = JSON.parse(fs.readFileSync(new URL(`../data/reading/hsk${level}.json`, import.meta.url), 'utf8'));
  assert.equal(payload.meta.targetCharacters, target, `Sai độ dài mục tiêu HSK ${level}`);
  assert.ok(payload.passages.length >= 5, `Quá ít bài đọc HSK ${level}`);
  const ids = new Set();
  for (const passage of payload.passages) {
    assert.ok(passage.id && passage.title && passage.topic, `Thiếu metadata ${passage.id}`);
    assert.ok(!ids.has(passage.id), `Trùng ID bài đọc ${passage.id}`);
    ids.add(passage.id);
    assert.ok(passage.actualCharacters >= Math.floor(target * 0.9), `${passage.id} ngắn hơn 90% mục tiêu`);
    assert.ok(passage.actualCharacters <= Math.ceil(target * 1.2), `${passage.id} dài vượt 120% mục tiêu`);
    assert.ok(passage.sentences.length >= 20, `${passage.id} quá ít câu`);
    const sentenceIds = new Set();
    for (const sentence of passage.sentences) {
      assert.ok(sentence.id && sentence.zh && sentence.pinyin && sentence.vi, `Thiếu dữ liệu dịch từng câu ${passage.id}`);
      assert.ok(!sentenceIds.has(sentence.id), `Trùng ID câu ${sentence.id}`);
      sentenceIds.add(sentence.id);
    }
  }
}

const meta = JSON.parse(fs.readFileSync(new URL('../data/reading/meta.json', import.meta.url), 'utf8'));
assert.ok(['7.0.0','7.1.0'].includes(meta.version));
assert.equal(meta.levels['6'].passages, 5);
assert.ok(meta.levels['7'].passages >= 5);

const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
assert.ok(html.includes('value="6"'), 'Thiếu lựa chọn HSK 6');
assert.ok(html.includes('value="7"'), 'Thiếu lựa chọn HSK 7–9');
assert.ok(html.includes('Hiện dịch từng câu'), 'Mất nút dịch từng câu');

const readingModule = fs.readFileSync(new URL('../js/modules/reading.js', import.meta.url), 'utf8');
assert.ok(readingModule.includes("'6','7'"), 'Module chưa cho phép tải HSK 6–7');
const sw = fs.readFileSync(new URL('../sw.js', import.meta.url), 'utf8');
for (const file of ['reading/hsk6.json','reading/hsk7.json']) assert.ok(sw.includes(file), `PWA thiếu ${file}`);

console.log('✓ P8: 10 bài đọc HSK 6 và HSK 7–9 đúng độ dài, có pinyin, highlight và dịch từng câu.');
