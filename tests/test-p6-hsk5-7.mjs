import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';

const expected = { 5: 1071, 6: 1140, 7: 5636 };
const grammarMin = { 5: 45, 6: 50, 7: 60 };
const exerciseMin = { 5: 30, 6: 35, 7: 70 };
for (const [level, count] of Object.entries(expected)) {
  const base = JSON.parse(fs.readFileSync(new URL(`../data/levels/hsk${level}.json`, import.meta.url), 'utf8'));
  const quality = JSON.parse(fs.readFileSync(new URL(`../data/hsk${level}-quality.json`, import.meta.url), 'utf8'));
  const grammar = JSON.parse(fs.readFileSync(new URL(`../data/hsk${level}-grammar.json`, import.meta.url), 'utf8'));
  assert.equal(base.words.length, count, `Sai số từ HSK ${level}`);
  assert.equal(Object.keys(quality.words).length, count, `Thiếu gói chuẩn hóa HSK ${level}`);
  let eligible = 0;
  for (const word of base.words) {
    const row = quality.words[word.id];
    assert.ok(row, `Thiếu chuẩn hóa ${word.id}`);
    assert.ok(row.primaryMeaning && row.topic && row.usageNote, `Thiếu trường lõi ${word.id}`);
    assert.ok(Array.isArray(row.normalizedSenses) && row.normalizedSenses.length, `Thiếu nghĩa ${word.id}`);
    assert.ok(Array.isArray(row.confusables), `Sai từ dễ nhầm ${word.id}`);
    assert.ok(row.example?.zh && row.example?.pinyin && row.example?.vi, `Thiếu ví dụ ${word.id}`);
    if (row.example.exerciseEligible) {
      eligible += 1;
      assert.ok(['da_duyet','bien_soan_ngu_phap','bien_soan_he_thong','admin_da_sua'].includes(row.example.status), `Trạng thái ví dụ chưa hợp lệ ${word.id}`);
    }
  }
  assert.ok(eligible >= exerciseMin[level], `Quá ít ví dụ luyện tập HSK ${level}: ${eligible}`);
  assert.ok(grammar.items.length >= grammarMin[level], `Thiếu ngữ pháp HSK ${level}`);
  assert.ok(grammar.items.every(item => item.id && item.title && item.formula && item.explanation && item.examples?.[0]?.zh && item.examples?.[0]?.pinyin && item.examples?.[0]?.vi && item.mistake));
}

const immutable = {
  'data/levels/hsk1.json':'96b1c4a85316138738fa0f4e79112c7f9358f6dbcb21bb78c88e5fbdc8b54e7a',
  'data/hsk1-quality.json':'5df6470187b210a8b6751f0bd9e41ef841bccea1bd341de8d4bcecf7dac26e5c',
  'data/hsk1-grammar.json':'c44521f835069dac411bb41cdbdb77e37cc666c1d326cabd6f4a76180782236d',
  'data/levels/hsk2.json':'cbd51b30689baaf906f8de74e61e09942a705cc59d3d131754ca996c650daa0b',
  'data/hsk2-quality.json':'2ef5187b5da984e433d0292f0a3d3a08b8b8b57a6c73b4db664c515a1809584c',
  'data/hsk2-grammar.json':'50108061da5e1f62f87c79bfa0c733f17ed800b1030acfa74e6f52f7dd4d5f81',
  'data/levels/hsk3.json':'402d389b4d5a1bb07a2f22087744cd61252dfcf1cc64cb82d35969184f5e4b87',
  'data/hsk3-quality.json':'0c8e6c07cd03eaa0befd45a4d6ba41114454524954137c9305189716a09d81d6',
  'data/hsk3-grammar.json':'97379622d26a55aa8936a99fddd0a8d636e0a87cebe70fe349e6467ee9b9a7b3',
  'data/levels/hsk4.json':'e4a14f11501813a6e08e1064965274828e0c2c9aae5408878279466ebfac20ba',
  'data/hsk4-quality.json':'f960c0213903a3dc4bcf424394757e0f38fcaa5810d45212b3292b653ffcce8d',
  'data/hsk4-grammar.json':'351231820fade0cb51ab6fd35762f0a2c4e4d6c1a04c9b7f827b300a31a7ba08'
};
for (const [file, expectedHash] of Object.entries(immutable)) {
  const actual = crypto.createHash('sha256').update(fs.readFileSync(new URL(`../${file}`, import.meta.url))).digest('hex');
  assert.equal(actual, expectedHash, `Phần chuẩn hóa cũ bị thay đổi: ${file}`);
}

const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
for (const value of ['5','6','7']) assert.ok(html.includes(`<option value="${value}">`));
assert.ok(html.includes('HSK 7–9'));
const sw = fs.readFileSync(new URL('../sw.js', import.meta.url), 'utf8');
for (const level of [5,6,7]) {
  assert.ok(sw.includes(`hsk${level}-quality.json`));
  assert.ok(sw.includes(`hsk${level}-grammar.json`));
}
console.log('✓ P6: chuẩn hóa HSK 5, HSK 6, HSK 7–9 và bảo toàn nguyên vẹn HSK 1–4.');
