import assert from 'node:assert/strict';
import fs from 'node:fs';
const root = new URL('../', import.meta.url);
globalThis.fetch = async url => {
  const relative = String(url).replace(/^\.\//,'');
  const text = fs.readFileSync(new URL(relative, root), 'utf8');
  return new Response(text, { status: 200, headers: { 'content-type': 'application/json' } });
};
const reading = await import(`../js/modules/reading.js?p8=${Date.now()}`);
for (const level of ['6','7']) {
  const pack = await reading.loadReadingLevel(level);
  assert.ok(pack.passages.length >= 5);
  const words = [];
  for (let current = 1; current <= Number(level); current++) {
    const base = JSON.parse(fs.readFileSync(new URL(`../data/hsk${current}-quality.json`, import.meta.url), 'utf8')).words;
    const source = JSON.parse(fs.readFileSync(new URL(`../data/levels/hsk${current}.json`, import.meta.url), 'utf8')).words;
    for (const item of source.slice(0, current === Number(level) ? 1000 : 100)) {
      const q = base[item.id] || {};
      words.push({ ...item, ...q, simplified:item.simplified, meaning:q.primaryMeaning || item.meaning, pinyin:item.pinyin });
    }
  }
  const matcher = reading.buildVocabularyMatcher(words);
  const tokens = reading.tokenizeChinese(pack.passages[0].sentences[0].zh, matcher);
  assert.ok(tokens.some(token => token.type === 'word'), `Không highlight được từ HSK ${level}`);
  const stats = reading.passageVocabularyStats(pack.passages[0], matcher);
  assert.ok(stats.uniqueWords > 0, `Không thống kê được từ HSK ${level}`);
}
await assert.rejects(() => reading.loadReadingLevel('8'), /hỗ trợ/);
console.log('✓ P8 runtime: tải HSK 6/7–9, tạo matcher, highlight và chặn cấp không hỗ trợ.');
