import assert from 'node:assert/strict';
import { makeQuestion, cardKey, MODES } from '../js/modules/quiz.js';
const words = [
  {id:'A', simplified:'爱', pinyin:'ài', meaning:'yêu'},
  {id:'B', simplified:'好', pinyin:'hǎo', meaning:'tốt'},
  {id:'C', simplified:'人', pinyin:'rén', meaning:'người'},
  {id:'D', simplified:'水', pinyin:'shuǐ', meaning:'nước'},
  {id:'E', simplified:'茶', pinyin:'chá', meaning:'trà'}
];
for (const mode of Object.keys(MODES)) {
  const q = makeQuestion(words[0], words, mode);
  assert.equal(q.options.length, 4);
  assert.ok(q.options.includes(q.correct));
}
assert.equal(cardKey('L1-0001','hanzi-vi'),'L1-0001::hanzi-vi');
console.log('✓ Quiz: bốn hướng hỏi và phương án trả lời.');
