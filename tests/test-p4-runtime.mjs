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
const content = await import(`../js/modules/content.js?runtime=${Date.now()}`);
await content.initContentSystem([]);
const raw = JSON.parse(fs.readFileSync(new URL('../data/levels/hsk1.json',import.meta.url),'utf8')).words;
let words = content.applyContentToWords(raw);
assert.equal(words.length,500);
assert.equal(words[0].id,'L1-0001');
assert.ok(words[0].topic && words[0].usageNote);
content.saveLocalContentOverride('L1-0001',{primaryMeaning:'yêu; yêu thích',senses:['yêu','yêu thích'],pos:['động từ'],topic:'cảm xúc',usageNote:'Nghĩa đã sửa.',collocations:['爱家人'],confusables:['喜欢'],example:{zh:'我爱家人。',pinyin:'Wǒ ài jiārén.',vi:'Tôi yêu gia đình.',exerciseEligible:true}});
words = content.applyContentToWords(raw);
assert.equal(words[0].meaning,'yêu; yêu thích');
assert.equal(words[0].contentSource,'admin');
assert.equal(words[0].example.exerciseEligible,true);
const admin = await import(`../js/modules/admin.js?runtime=${Date.now()}`);
localStorage.setItem('hsk_admin_password_hash_v1', await admin.hashPassword('test-admin-123'));
const ok = await admin.unlockAdmin('test-admin-123',null);
assert.equal(ok.ok,true);
assert.equal(admin.isAdminUnlocked(),true);
admin.lockAdmin();
assert.equal(admin.isAdminUnlocked(),false);
console.log('✓ P4 runtime: áp dụng override và mở/khóa admin bằng cơ chế mật khẩu.');
