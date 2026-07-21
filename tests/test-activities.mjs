import assert from 'node:assert/strict';
import { buildDictationQuestion, checkDictation, buildFillQuestion, buildOrderQuestion, checkOrder, normalizeChinese } from '../js/modules/activities.js';
const word = { id:'L1-X', simplified:'学习', traditional:'學習', pinyin:'xuéxí', meaning:'học tập' };
const dictation = buildDictationQuestion(word);
assert.equal(checkDictation('学习', dictation), true);
assert.equal(checkDictation('學習', dictation), true);
assert.equal(checkDictation('学生', dictation), false);
const examples = [
  {id:'E1',wordId:'L1-X',target:'学习',zh:'我每天学习中文。',sentencePinyin:'Wǒ měitiān xuéxí Zhōngwén.',vi:'Tôi học tiếng Trung mỗi ngày.'},
  {id:'E2',wordId:'L1-Y',target:'工作',zh:'他在公司工作。',sentencePinyin:'',vi:'Anh ấy làm việc ở công ty.'},
  {id:'E3',wordId:'L1-Z',target:'喜欢',zh:'我喜欢喝茶。',sentencePinyin:'',vi:'Tôi thích uống trà.'},
  {id:'E4',wordId:'L1-A',target:'回家',zh:'我下午回家。',sentencePinyin:'',vi:'Chiều tôi về nhà.'}
];
const fill = buildFillQuestion(examples[0], examples);
assert.ok(fill.prompt.includes('______'));
assert.ok(fill.options.includes('学习'));
const order = buildOrderQuestion(examples[0]);
assert.equal(checkOrder(order.tokens, order), true);
assert.equal(normalizeChinese('我 每天学习中文。'), normalizeChinese('我每天学习中文'));
console.log('✓ P2: chính tả, điền từ và sắp xếp câu.');
