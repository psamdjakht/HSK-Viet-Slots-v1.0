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
const content = await import(`../js/modules/content.js?p6=${Date.now()}`);
await content.initContentSystem([]);
assert.deepEqual(content.standardizedLevels(), ['1','2','3','4','5','6','7']);
for (const level of ['5','6','7']) {
  const raw = JSON.parse(fs.readFileSync(new URL(`../data/levels/hsk${level}.json`,import.meta.url),'utf8')).words;
  const words = content.applyContentToWords(raw);
  assert.equal(words.length, raw.length);
  assert.ok(words[0].topic && words[0].usageNote && words[0].example);
  assert.equal(words[0].verification, `chuan_hoa_hsk${level}`);
}
content.saveLocalContentOverride('L7-0001', {
  primaryMeaning:'tiếng Ả Rập', senses:['tiếng Ả Rập'], pos:['danh từ'], topic:'học tập & ngôn ngữ',
  usageNote:'Tên một ngôn ngữ.', collocations:['学习阿拉伯语'], confusables:['阿拉伯文'],
  example:{zh:'她正在学习阿拉伯语。',pinyin:'Tā zhèngzài xuéxí Ālābóyǔ.',vi:'Cô ấy đang học tiếng Ả Rập.',exerciseEligible:true}
});
const raw7 = JSON.parse(fs.readFileSync(new URL('../data/levels/hsk7.json',import.meta.url),'utf8')).words;
const updated = content.applyContentToWords(raw7);
assert.equal(updated[0].meaning,'tiếng Ả Rập');
assert.equal(updated[0].contentSource,'admin');
console.log('✓ P6 runtime: nạp, học và sửa nội dung HSK 5–7–9 qua cùng hệ thống quản trị.');
