import assert from 'node:assert/strict';
import fs from 'node:fs';
const memory = new Map();
globalThis.localStorage = {
  getItem:key=>memory.has(key)?memory.get(key):null,
  setItem:(key,value)=>memory.set(key,String(value)),
  removeItem:key=>memory.delete(key)
};
const root = new URL('../', import.meta.url);
globalThis.fetch = async url => {
  const relative = String(url).replace(/^\.\//,'');
  const text = fs.readFileSync(new URL(relative, root),'utf8');
  return new Response(text,{status:200,headers:{'content-type':'application/json'}});
};
const content = await import(`../js/modules/content.js?p5=${Date.now()}`);
await content.initContentSystem([]);
assert.deepEqual(content.standardizedLevels().slice(0,4), ['1','2','3','4']);
for (const level of ['2','3','4']) {
  const raw = JSON.parse(fs.readFileSync(new URL(`../data/levels/hsk${level}.json`,import.meta.url),'utf8')).words;
  let words = content.applyContentToWords(raw);
  assert.equal(words.length, raw.length);
  assert.ok(words[0].topic && words[0].usageNote);
  assert.equal(words[0].verification, `chuan_hoa_hsk${level}`);
}
content.saveLocalContentOverride('L4-0001', {
  primaryMeaning:'dì; cô lớn tuổi', senses:['dì','cô lớn tuổi'], pos:['danh từ'], topic:'gia đình & quan hệ',
  usageNote:'Cách xưng hô với phụ nữ lớn tuổi tương đương thế hệ bố mẹ.', collocations:['张阿姨'], confusables:['姑姑'],
  example:{zh:'阿姨，您好。',pinyin:'Āyí, nín hǎo.',vi:'Chào cô ạ.',exerciseEligible:true}
});
const hsk4 = JSON.parse(fs.readFileSync(new URL('../data/levels/hsk4.json',import.meta.url),'utf8')).words;
const updated = content.applyContentToWords(hsk4);
assert.equal(updated[0].meaning,'dì; cô lớn tuổi');
assert.equal(updated[0].contentSource,'admin');
assert.equal(updated[0].example.exerciseEligible,true);
console.log('✓ P5 runtime: áp dụng chuẩn hóa và override quản trị cho HSK 2–4.');
