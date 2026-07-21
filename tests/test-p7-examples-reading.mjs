import assert from 'node:assert/strict';
import fs from 'node:fs';

const examples = JSON.parse(fs.readFileSync(new URL('../data/standardized-examples.json', import.meta.url), 'utf8'));
const allWords = [];
for (let level = 1; level <= 7; level++) {
  const base = JSON.parse(fs.readFileSync(new URL(`../data/levels/hsk${level}.json`, import.meta.url), 'utf8')).words;
  allWords.push(...base);
  for (const word of base) {
    const rows = examples.words[word.id];
    assert.ok(Array.isArray(rows), `Thiếu danh sách câu ví dụ ${word.id}`);
    assert.ok(rows.length >= (level <= 5 ? 3 : 2), `Quá ít câu ví dụ ${word.id}`);
    for (const row of rows) {
      assert.ok(row.id && row.zh && row.pinyin && row.vi, `Thiếu trường câu ví dụ ${word.id}`);
      assert.ok(Number(row.difficulty) >= 1 && Number(row.difficulty) <= 7, `Sai độ khó ${row.id}`);
      assert.equal(typeof row.exerciseEligible, 'boolean', `Thiếu trạng thái luyện tập ${row.id}`);
    }
  }
}
assert.equal(Object.keys(examples.words).length, allWords.length, 'Số từ trong thư viện câu ví dụ không khớp');

const targets = { 1: 50, 2: 100, 3: 180, 4: 300, 5: 600 };
for (const [level, target] of Object.entries(targets)) {
  const payload = JSON.parse(fs.readFileSync(new URL(`../data/reading/hsk${level}.json`, import.meta.url), 'utf8'));
  assert.ok(payload.passages.length >= 5, `Quá ít bài đọc HSK ${level}`);
  for (const passage of payload.passages) {
    assert.ok(passage.id && passage.title && passage.topic, `Thiếu metadata bài đọc HSK ${level}`);
    assert.ok(passage.actualCharacters >= Math.floor(target * 0.9), `Bài ${passage.id} ngắn hơn 90% mục tiêu`);
    assert.ok(passage.actualCharacters <= Math.ceil(target * 1.2), `Bài ${passage.id} dài vượt 120% mục tiêu`);
    assert.ok(passage.sentences.length >= 3, `Bài ${passage.id} quá ít câu`);
    for (const sentence of passage.sentences) {
      assert.ok(sentence.id && sentence.zh && sentence.pinyin && sentence.vi, `Thiếu dịch từng câu ${passage.id}`);
    }
  }
}

const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
for (const id of ['open-reading-btn','reading-view','reading-level-select','reading-sentences','reading-word-detail']) {
  assert.ok(html.includes(`id="${id}"`), `Thiếu giao diện đọc hiểu: ${id}`);
}
const sw = fs.readFileSync(new URL('../sw.js', import.meta.url), 'utf8');
for (const file of ['standardized-examples.json','reading/hsk1.json','reading/hsk5.json','modules/reading.js']) assert.ok(sw.includes(file));
console.log('✓ P7: câu ví dụ chuẩn hóa toàn bộ từ và 25 bài đọc HSK 1–5 đúng độ dài mục tiêu.');
