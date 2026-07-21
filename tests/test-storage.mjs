import assert from 'node:assert/strict';
const map = new Map();
globalThis.localStorage = {
  getItem:key=>map.has(key)?map.get(key):null,
  setItem:(key,value)=>map.set(key,String(value)),
  removeItem:key=>map.delete(key)
};
map.set('hsk_viet_slot_v2_1', JSON.stringify({
  schemaVersion:2,id:1,profile:{name:'Cũ',createdAt:'2026-01-01',updatedAt:'2026-01-02'},
  settings:{level:'2',mode:'hanzi-vi',dailyNew:30,audio:true,showTraditional:false},
  cards:{},history:{},stats:{answered:5,correct:4,sessions:1,lastStudyDate:null}
}));
map.set('hsk_viet_active_slot_v2','1');
const storage = await import(`../js/modules/storage.js?test=${Date.now()}`);
const slot = storage.loadSlot(1);
assert.equal(slot.schemaVersion,3);
assert.equal(slot.settings.sessionSize,30);
assert.equal(slot.profile.name,'Cũ');
assert.ok(map.has('hsk_viet_slot_v3_1'));
assert.equal(storage.getActiveSlotId(),1);
storage.resetSlot(1,{remote:false});
assert.equal(storage.loadSlot(1),null);
assert.ok(storage.getDeletedSlots()['1']);
const fresh = storage.ensureSlot(1,'Mới');
assert.equal(fresh.profile.name,'Mới');
assert.equal(storage.getDeletedSlots()['1'],undefined);
console.log('✓ Storage: tự nâng schema v2 → v3 và reset sạch slot.');
