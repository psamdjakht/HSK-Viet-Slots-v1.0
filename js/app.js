import {
  SLOT_COUNT, listSlots, ensureSlot, saveSlot, saveSlotLocalOnly, resetSlot,
  setActiveSlotId, getActiveSlotId, loadSlot, exportSlot, importSlot,
  configureCloudStorage, allLocalSlots, migrateSlot, getDeletedSlots, clearDeletedSlot
} from './modules/storage.js';
import { loadLevel, loadLevelsUpTo, loadMeta, loadExamples, verificationLabel } from './modules/data.js';
import { initContentSystem, loadGrammar, applyContentToWords, buildEffectiveExamples, getContentOverride, saveLocalContentOverride, deleteLocalContentOverride, exportContentOverrides, importContentOverrides, qualitySummary, standardizedLevels, isStandardizedLevel } from './modules/content.js';
import { unlockAdmin, lockAdmin, isAdminUnlocked, getAdminPassword, getAdminSource, changeLocalAdminPassword, setLocalAdminPassword } from './modules/admin.js';
import { MODES, buildStudyQueue, makeQuestion, cardKey, shuffle } from './modules/quiz.js';
import { reviewCard, GRADES, isDue } from './modules/srs.js';
import { speakChinese } from './modules/audio.js';
import { ACTIVITIES, buildDictationQuestion, checkDictation, buildFillQuestion, buildOrderQuestion, checkOrder } from './modules/activities.js';
import { computeWeakWords } from './modules/weak.js';
import { planSummary, todayPlan, updateStreak } from './modules/plan.js';
import { buildAdvancedStats } from './modules/stats.js';
import { EXAM_TYPES, questionBankSummary, buildMockExam, scoreExam } from './modules/exam.js';
import { initCloudSync, getCloudStatus, syncNow, verifyAdminPassword, saveRemoteContentOverride, deleteRemoteContentOverride, changeRemoteAdminPassword } from './modules/sync.js';
import { loadStandardizedExamples, attachStandardizedExamples, loadReadingLevel, buildVocabularyMatcher, tokenizeChinese, passageVocabularyStats } from './modules/reading.js';
import { $, $$, showScreen, toast, formatDate, downloadText } from './modules/ui.js';

function levelDisplay(level) { return String(level) === '7' ? '7–9' : String(level); }

const state = {
  meta: null,
  baseExamples: [],
  standardizedExamples: null,
  examples: [],
  readingLevel: '1',
  readingPack: null,
  readingPassageId: null,
  readingMatcher: new Map(),
  grammar: [],
  grammarByLevel: new Map(),
  qualityWordsByLevel: new Map(),
  hsk1Words: [],
  libraryLevel: '1',
  adminLevel: '1',
  contentMeta: null,
  adminSelectedWordId: null,
  slot: null,
  words: [],
  wordIndex: new Map(),
  activity: 'quiz',
  queue: [],
  index: 0,
  question: null,
  pendingCorrect: null,
  selectedAnswer: null,
  answeredThisQuestion: false,
  ratingLocked: false,
  answerStartedAt: 0,
  orderAvailable: [],
  orderSelected: [],
  weakRows: [],
  session: emptySession(),
  cloudAdapter: null,
  exam: null,
  examTimer: null
};

async function boot() {
  bindStaticEvents();
  registerServiceWorker();
  try {
    [state.meta, state.baseExamples, state.standardizedExamples] = await Promise.all([loadMeta(), loadExamples(), loadStandardizedExamples()]);
    $('#data-summary').textContent = `${state.meta.totalWords.toLocaleString('vi-VN')} từ HSK 3.0 • đang nạp gói chuẩn hóa HSK 1–6 và HSK 7–9`;
  } catch (error) {
    console.error(error);
    toast('Không tải được dữ liệu nền. Hãy tải lại trang.', 'error');
  }
  await setupCloud();
  const standardizedCount = [...state.qualityWordsByLevel.values()].reduce((sum, rows) => sum + rows.length, 0);
  const grammarCount = [...state.grammarByLevel.values()].reduce((sum, rows) => sum + rows.length, 0);
  const standardizedExampleCount = Object.values(state.standardizedExamples?.meta?.counts || {}).reduce((sum, row) => sum + Number(row.examples || 0), 0);
  $('#data-summary').textContent = `${state.meta.totalWords.toLocaleString('vi-VN')} từ HSK 3.0 • ${standardizedExampleCount.toLocaleString('vi-VN')} câu ví dụ chuẩn hóa • 35 bài đọc HSK 1–7–9 • ${grammarCount} điểm ngữ pháp`;
  renderSlots();
  const activeId = getActiveSlotId();
  if (activeId && loadSlot(activeId)?.profile?.name) await openSlot(activeId);
  else showScreen('slot-screen');
}

async function setupCloud() {
  const result = await initCloudSync();
  state.contentMeta = await initContentSystem(result.contentRows || []);
  for (const level of standardizedLevels()) {
    const words = attachStandardizedExamples(applyContentToWords(await loadLevel(level)), state.standardizedExamples);
    const grammar = (await loadGrammar(level)).items || [];
    state.qualityWordsByLevel.set(level, words);
    state.grammarByLevel.set(level, grammar);
  }
  state.hsk1Words = state.qualityWordsByLevel.get('1') || [];
  state.grammar = state.grammarByLevel.get('1') || [];
  state.examples = buildEffectiveExamples(state.baseExamples, [...state.qualityWordsByLevel.values()].flat());
  if (result.adapter) await reconcileDeletedSlots(result.adapter);
  const deleted = getDeletedSlots();
  const usableRows = (result.rows || []).filter(row => !(String(row.slot_id) in deleted));
  mergeRemoteRows(usableRows);
  state.cloudAdapter = result.adapter;
  configureCloudStorage(result.adapter);
  if (result.adapter) pushNewerLocalSlots(usableRows, result.adapter);
  renderCloudStatus();
}

async function reconcileDeletedSlots(adapter) {
  const deleted = getDeletedSlots();
  for (const id of Object.keys(deleted)) {
    try {
      const ok = await adapter.deleteSlot(Number(id));
      if (ok) clearDeletedSlot(Number(id));
    } catch {}
  }
}

function mergeRemoteRows(rows) {
  for (const row of rows) {
    const id = Number(row.slot_id);
    if (id < 1 || id > SLOT_COUNT || !row.data) continue;
    const remote = migrateSlot(row.data, id);
    const local = loadSlot(id);
    const remoteTime = new Date(remote.profile?.updatedAt || row.updated_at || 0).getTime();
    const localTime = new Date(local?.profile?.updatedAt || 0).getTime();
    if (!local || remoteTime > localTime) saveSlotLocalOnly(remote);
  }
}

function pushNewerLocalSlots(rows, adapter) {
  const remoteMap = new Map(rows.map(row => [Number(row.slot_id), row]));
  for (const local of allLocalSlots()) {
    const remote = remoteMap.get(Number(local.id));
    const localTime = new Date(local.profile?.updatedAt || 0).getTime();
    const remoteTime = new Date(remote?.data?.profile?.updatedAt || remote?.updated_at || 0).getTime();
    if (!remote || localTime > remoteTime) adapter.saveSlot(local);
  }
}

function bindStaticEvents() {
  $('#switch-slot-btn').addEventListener('click', () => { finishSpeech(); clearExamTimer(); renderSlots(); showScreen('slot-screen'); });
  $('#start-study-btn').addEventListener('click', () => startActivity('quiz'));
  $('#start-dictation-btn').addEventListener('click', () => startActivity('dictation'));
  $('#start-fill-btn').addEventListener('click', () => startActivity('fill'));
  $('#start-order-btn').addEventListener('click', () => startActivity('order'));
  $('#review-due-btn').addEventListener('click', () => startActivity('quiz', { dueOnly: true }));
  $('#weak-book-btn').addEventListener('click', openWeakBook);
  $('#start-weak-btn').addEventListener('click', () => { closeModal($('#weak-modal')); startActivity('weak'); });
  $('#back-dashboard-btn').addEventListener('click', () => { if (state.session.answered && !confirm('Dừng phiên học hiện tại? Tiến độ các câu đã làm vẫn được lưu.')) return; showDashboard(); });
  $('#speak-word-btn').addEventListener('click', () => speakCurrentQuestion());
  $('#speak-example-btn').addEventListener('click', () => {
    const text = currentExample()?.zh;
    if (text) speakChinese(text, state.slot?.settings?.audio, 0.78);
  });
  $('#next-word-btn').addEventListener('click', () => applyRating(GRADES.GOOD));
  $$('.rating-btn').forEach(btn => btn.addEventListener('click', () => applyRating(Number(btn.dataset.grade))));
  $('#check-text-answer-btn').addEventListener('click', checkTextAnswer);
  $('#text-answer-input').addEventListener('keydown', event => { if (event.key === 'Enter') checkTextAnswer(); });
  $('#check-order-btn').addEventListener('click', checkOrderAnswer);
  $('#reset-order-btn').addEventListener('click', resetOrderBuilder);

  $('#settings-btn').addEventListener('click', () => { hydrateSettings(); renderCloudStatus(); openModal('settings-modal'); });
  $('#stats-btn').addEventListener('click', () => { renderStats(); openModal('stats-modal'); });
  $('#edit-plan-btn').addEventListener('click', openPlanModal);
  $('#save-plan-btn').addEventListener('click', savePlan);
  ['plan-target-level','plan-target-date','plan-minutes','plan-days','plan-new-words'].forEach(id => $(`#${id}`).addEventListener('input', renderPlanPreview));
  $('#export-btn').addEventListener('click', exportCurrentSlot);
  $('#import-btn').addEventListener('click', () => $('#import-file').click());
  $('#import-file').addEventListener('change', handleImport);
  $('#reset-current-slot-btn').addEventListener('click', resetCurrentSlot);
  $('#sync-now-btn').addEventListener('click', manualSync);

  $('#open-exam-btn').addEventListener('click', openExamModal);
  $('#start-exam-btn').addEventListener('click', startExam);
  $('#exam-history-btn').addEventListener('click', openExamHistory);
  $('#exam-result-history-btn').addEventListener('click', openExamHistory);
  $('#exam-result-home-btn').addEventListener('click', showDashboard);
  $('#quit-exam-btn').addEventListener('click', quitExam);
  $('#exam-next-btn').addEventListener('click', nextExamQuestion);
  $('#exam-speak-btn').addEventListener('click', () => {
    const q = currentExamQuestion();
    if (q?.audioText) speakChinese(q.audioText, state.slot.settings.audio);
  });

  $('#hsk1-library-btn').addEventListener('click', openHsk1Library);
  $('#open-hsk1-library-btn').addEventListener('click', openHsk1Library);
  $('#open-reading-btn').addEventListener('click', openReadingView);
  $('#back-reading-dashboard-btn').addEventListener('click', showDashboard);
  $('#reading-level-select').addEventListener('change', event => loadReadingView(event.target.value));
  $('#reading-pinyin-toggle').addEventListener('change', renderReadingPassage);
  $('#reading-translation-toggle').addEventListener('change', renderReadingPassage);
  $('#reading-speak-all-btn').addEventListener('click', speakReadingPassage);
  $('#hsk1-library-search').addEventListener('input', renderHsk1LibraryWords);
  $('#hsk1-library-topic').addEventListener('change', renderHsk1LibraryWords);
  $('#quality-library-level').addEventListener('change', event => { state.libraryLevel = event.target.value; prepareLibraryLevel(); });
  $('#admin-btn').addEventListener('click', openAdminEntry);
  $('#admin-home-btn').addEventListener('click', openAdminEntry);
  $('#admin-login-submit').addEventListener('click', submitAdminLogin);
  $('#admin-password-input').addEventListener('keydown', event => { if (event.key === 'Enter') submitAdminLogin(); });
  $('#admin-word-search').addEventListener('input', renderAdminWordList);
  $('#admin-level-select').addEventListener('change', event => { state.adminLevel = event.target.value; state.adminSelectedWordId = null; renderAdminWordList(); $('#admin-editor').hidden = true; $('#admin-editor-empty').hidden = false; });
  $('#admin-editor').addEventListener('submit', saveAdminWord);
  $('#admin-reset-word-btn').addEventListener('click', resetAdminWord);
  $('#admin-lock-btn').addEventListener('click', lockAdminUi);
  $('#admin-change-password-btn').addEventListener('click', () => openModal('admin-password-modal'));
  $('#admin-change-password-submit').addEventListener('click', submitAdminPasswordChange);
  $('#admin-export-content-btn').addEventListener('click', () => downloadText(`hsk1-7-9-noi-dung-sua-${new Date().toISOString().slice(0,10)}.json`, exportContentOverrides()));
  $('#admin-import-content-btn').addEventListener('click', () => $('#admin-import-content-file').click());
  $('#admin-import-content-file').addEventListener('change', importAdminContentFile);
  $('#admin-edit-current-btn').addEventListener('click', () => { const id = $('#admin-edit-current-btn').dataset.wordId; if (id) { state.adminSelectedWordId = id; openAdminPanel(); } });

  $$('.modal-close').forEach(btn => btn.addEventListener('click', () => closeModal(btn.closest('.modal-overlay'))));
  $$('.modal-overlay').forEach(modal => modal.addEventListener('click', event => { if (event.target === modal) closeModal(modal); }));
  document.addEventListener('keydown', handleKeyboard);
}

async function loadEffectiveLevel(level) {
  const key = String(level);
  const words = attachStandardizedExamples(applyContentToWords(await loadLevel(key)), state.standardizedExamples);
  if (isStandardizedLevel(key)) state.qualityWordsByLevel.set(key, words);
  if (key === '1') state.hsk1Words = words;
  return words;
}

async function refreshContentState() {
  for (const level of standardizedLevels()) {
    state.qualityWordsByLevel.set(level, attachStandardizedExamples(applyContentToWords(await loadLevel(level)), state.standardizedExamples));
  }
  state.hsk1Words = state.qualityWordsByLevel.get('1') || [];
  state.examples = buildEffectiveExamples(state.baseExamples, [...state.qualityWordsByLevel.values()].flat());
  if (state.slot && isStandardizedLevel(state.slot.settings.level)) {
    state.words = state.qualityWordsByLevel.get(String(state.slot.settings.level)) || [];
    state.wordIndex = new Map(state.words.map(word => [word.id, word]));
    renderDashboard();
  }
}

function renderSlots() {
  const slots = listSlots();
  $('#slot-grid').innerHTML = slots.map(slot => `
    <article class="slot-card ${slot.name ? 'has-data' : ''}" data-slot="${slot.id}">
      <div class="slot-number">${slot.id}</div>
      <label for="slot-name-${slot.id}">Tên người học</label>
      <input id="slot-name-${slot.id}" class="slot-name" maxlength="28" value="${escapeHtml(slot.name)}" placeholder="Ví dụ: Bạn Linh">
      <div class="slot-meta"><span>HSK ${slot.level}</span><span>${slot.answered.toLocaleString('vi-VN')} lượt</span><span>${formatDate(slot.lastStudyDate)}</span></div>
      <div class="slot-actions"><button class="btn primary slot-open" data-id="${slot.id}">${slot.name ? 'Vào học' : 'Tạo slot'}</button><button class="btn ghost slot-reset" data-id="${slot.id}" ${slot.name ? '' : 'disabled'}>Xóa slot</button></div>
    </article>`).join('');
  $$('.slot-open').forEach(btn => btn.addEventListener('click', async () => {
    const id = Number(btn.dataset.id);
    const name = $(`#slot-name-${id}`).value.trim();
    if (!name) return toast('Hãy nhập tên người học cho slot này.', 'warn');
    ensureSlot(id, name);
    await openSlot(id);
  }));
  $$('.slot-reset').forEach(btn => btn.addEventListener('click', () => {
    const id = Number(btn.dataset.id);
    const slot = loadSlot(id);
    if (!slot || !confirm(`Xóa toàn bộ dữ liệu Slot ${id} – ${slot.profile.name}, gồm cả bản trên Supabase?`)) return;
    resetSlot(id);
    renderSlots();
    toast(`Đã xóa Slot ${id}.`);
  }));
  renderCloudStatus();
}

async function openSlot(id) {
  state.slot = loadSlot(id);
  if (!state.slot) return;
  setActiveSlotId(id);
  state.words = await loadEffectiveLevel(state.slot.settings.level);
  state.wordIndex = new Map(state.words.map(word => [word.id, word]));
  $('#slot-badge').textContent = `Slot ${id}`;
  $('#learner-name').textContent = state.slot.profile.name;
  hydrateSettings();
  renderDashboard();
  showScreen('app-screen');
  showDashboard();
}

function hydrateSettings() {
  if (!state.slot) return;
  $('#level-select').value = state.slot.settings.level;
  $('#mode-select').value = state.slot.settings.mode;
  $('#session-size-select').value = String(state.slot.settings.sessionSize);
  $('#audio-toggle').checked = state.slot.settings.audio;
  $('#traditional-toggle').checked = state.slot.settings.showTraditional;
  $('#level-select').onchange = async event => {
    state.slot.settings.level = event.target.value;
    saveSlot(state.slot);
    state.words = await loadEffectiveLevel(event.target.value);
    state.wordIndex = new Map(state.words.map(word => [word.id, word]));
    renderDashboard();
  };
  $('#mode-select').onchange = event => { state.slot.settings.mode = event.target.value; saveSlot(state.slot); renderDashboard(); };
  $('#session-size-select').onchange = event => { state.slot.settings.sessionSize = Number(event.target.value); saveSlot(state.slot); renderDashboard(); };
  $('#audio-toggle').onchange = event => { state.slot.settings.audio = event.target.checked; saveSlot(state.slot); };
  $('#traditional-toggle').onchange = event => { state.slot.settings.showTraditional = event.target.checked; saveSlot(state.slot); };
}

function renderDashboard() {
  if (!state.slot) return;
  const mode = state.slot.settings.mode;
  const info = buildStudyQueue(state.words, state.slot, mode, state.slot.settings.sessionSize);
  const learnedIds = new Set(Object.keys(state.slot.cards).filter(key => key.endsWith(`::${mode}`)).map(key => key.split('::')[0]));
  const accuracy = state.slot.stats.answered ? Math.round(state.slot.stats.correct / state.slot.stats.answered * 100) : 0;
  state.weakRows = computeWeakWords(state.words, state.slot, 100);
  $('#dash-level').textContent = `HSK ${state.slot.settings.level}`;
  $('#dash-mode').textContent = MODES[mode].label;
  $('#due-count').textContent = info.dueCount.toLocaleString('vi-VN');
  $('#new-count').textContent = info.newCount.toLocaleString('vi-VN');
  $('#learned-count').textContent = learnedIds.size.toLocaleString('vi-VN');
  $('#weak-count').textContent = state.weakRows.length.toLocaleString('vi-VN');
  $('#accuracy-count').textContent = `${accuracy}%`;
  $('#review-due-btn').disabled = info.dueCount === 0;
  $('#review-due-note').textContent = info.dueCount ? `${info.dueCount} thẻ đang đến hạn theo hướng học hiện tại.` : 'Chưa có từ đến hạn.';
  const pct = Math.min(100, Math.round(learnedIds.size / Math.max(1, state.words.length) * 100));
  $('#level-progress-fill').style.width = `${pct}%`;
  $('#level-progress-text').textContent = `${learnedIds.size}/${state.words.length} từ (${pct}%)`;
  const levelKey = String(state.slot.settings.level);
  const qualityWords = state.qualityWordsByLevel.get(levelKey) || [];
  const quality = qualitySummary(qualityWords, levelKey);
  const grammarCount = (state.grammarByLevel.get(levelKey) || []).length;
  const standardizedExampleCount = qualityWords.reduce((sum, word) => sum + (word.examples?.length || 0), 0);
  $('#data-quality-note').textContent = isStandardizedLevel(levelKey)
    ? `HSK ${levelDisplay(levelKey)} có ${quality.words} từ, ${standardizedExampleCount.toLocaleString('vi-VN')} câu ví dụ theo cấu trúc thống nhất và ${grammarCount} điểm ngữ pháp. ${quality.overridden} từ đã được quản trị viên chỉnh.`
    : `Dữ liệu HSK 3.0 đã làm sạch; gói chuẩn hóa chuyên sâu hiện áp dụng cho HSK 1–6 và HSK 7–9.`;
  const examples = state.examples.filter(ex => Number(ex.level) <= Number(state.slot.settings.level));
  const bank = questionBankSummary(state.words, examples);
  $('#bank-summary').textContent = `Ngân hàng có thể tạo ${bank.total.toLocaleString('vi-VN')} biến thể câu hỏi ở cấp hiện tại: nghĩa, pinyin, nghe, điền từ và sắp xếp câu.`;
  renderPlanCard(info.dueCount);
  renderCloudStatus();
}

function renderPlanCard(dueCount) {
  const summary = planSummary(state.slot, state.meta);
  const today = todayPlan(state.slot, dueCount);
  $('#plan-title').textContent = `Mục tiêu HSK ${summary.target} · ${summary.completionPct}%`;
  $('#plan-summary').textContent = `Còn khoảng ${summary.remaining.toLocaleString('vi-VN')} từ. Hôm nay: ${today.newTarget} từ mới, tối đa ${today.reviewTarget} thẻ ôn, ${today.minutes} phút.`;
  $('#plan-required').textContent = summary.studyDays ? `${summary.requiredPerStudyDay} từ/ngày học` : 'Chưa đặt ngày hoàn thành';
  const track = $('#plan-track');
  track.classList.toggle('warn', !summary.onTrack);
  track.textContent = !summary.studyDays ? 'Cần đặt ngày' : summary.recentWordsPerDay === 0 ? 'Chưa đủ dữ liệu' : summary.onTrack ? 'Đang đúng tiến độ' : `Tốc độ gần đây ${summary.recentWordsPerDay} từ/ngày`;
}

function showDashboard() {
  finishSpeech();
  clearExamTimer();
  $('#dashboard-view').hidden = false;
  $('#study-view').hidden = true;
  $('#reading-view').hidden = true;
  $('#exam-view').hidden = true;
  $('#exam-result-view').hidden = true;
  renderDashboard();
}

function startActivity(activity, options = {}) {
  if (!state.slot) return;
  const limit = state.slot.settings.sessionSize;
  const mode = activity === 'dictation' ? 'dictation-hanzi' : state.slot.settings.mode;
  let queue = [];
  if (activity === 'quiz') {
    const info = buildStudyQueue(state.words, state.slot, mode, limit);
    queue = options.dueOnly ? state.words.filter(word => isDue(state.slot.cards[cardKey(word.id, mode)])).slice(0, limit) : info.queue;
  } else if (activity === 'dictation') {
    queue = buildStudyQueue(state.words, state.slot, mode, limit).queue;
  } else if (activity === 'weak') {
    state.weakRows = computeWeakWords(state.words, state.slot, limit);
    queue = state.weakRows.map(row => row.word);
  } else if (activity === 'fill' || activity === 'order') {
    const examples = state.examples.filter(ex => Number(ex.level) <= Number(state.slot.settings.level));
    queue = buildExampleQueue(examples, state.slot, activity === 'fill' ? 'fill-sentence' : 'order-sentence', limit);
  }
  if (!queue.length) return toast(activity === 'weak' ? 'Chưa có từ yếu. Hãy học thêm để hệ thống phân tích.' : 'Không có dữ liệu phù hợp cho bài luyện này.', 'warn');
  state.activity = activity;
  state.queue = queue;
  state.index = 0;
  state.session = { ...emptySession(), activity, startedAt: Date.now() };
  $('#dashboard-view').hidden = true;
  $('#reading-view').hidden = true;
  $('#exam-view').hidden = true;
  $('#exam-result-view').hidden = true;
  $('#study-view').hidden = false;
  renderQuestion();
}

function buildExampleQueue(examples, slot, mode, limit) {
  const due = [], fresh = [], learned = [];
  for (const example of examples) {
    const card = slot.cards[cardKey(example.wordId, mode)];
    if (!card) fresh.push(example);
    else if (isDue(card)) due.push(example);
    else learned.push(example);
  }
  shuffle(due); shuffle(fresh); shuffle(learned);
  return [...due, ...fresh, ...learned].slice(0, limit);
}

function renderQuestion() {
  if (state.index >= state.queue.length) return finishSession();
  const item = state.queue[state.index];
  state.pendingCorrect = null;
  state.selectedAnswer = null;
  state.answeredThisQuestion = false;
  state.ratingLocked = false;
  state.answerStartedAt = Date.now();
  state.orderAvailable = [];
  state.orderSelected = [];
  resetStudyUI();
  $('#study-position').textContent = `${state.index + 1}/${state.queue.length}`;
  $('#study-progress-fill').style.width = `${Math.round(state.index / state.queue.length * 100)}%`;
  $('#activity-label').textContent = ACTIVITIES[state.activity]?.label || 'Bài luyện';

  if (state.activity === 'quiz' || state.activity === 'weak') {
    state.question = makeQuestion(item, state.words, state.slot.settings.mode);
    $('#question-instruction').textContent = MODES[state.slot.settings.mode].label;
    const prompt = $('#question-prompt');
    prompt.textContent = state.question.prompt;
    prompt.className = state.question.promptType === 'hanzi' ? 'question-prompt hanzi' : 'question-prompt';
    $('#traditional-text').textContent = state.slot.settings.showTraditional && item.traditional !== item.simplified ? item.traditional : '';
    $('#pinyin-hint').textContent = state.slot.settings.mode === 'hanzi-vi' ? item.pinyin : '';
    renderOptions(state.question.options);
  } else if (state.activity === 'dictation') {
    state.question = buildDictationQuestion(item);
    $('#question-instruction').textContent = state.question.prompt;
    $('#question-prompt').textContent = '🔊';
    $('#question-prompt').className = 'question-prompt';
    $('#text-answer-area').hidden = false;
    setTimeout(() => speakCurrentQuestion(), 200);
    setTimeout(() => $('#text-answer-input').focus(), 260);
  } else if (state.activity === 'fill') {
    const pool = state.examples.filter(ex => Number(ex.level) <= Number(state.slot.settings.level));
    state.question = buildFillQuestion(item, pool);
    $('#question-instruction').textContent = 'Chọn từ phù hợp với chỗ trống';
    $('#question-prompt').textContent = state.question.prompt;
    $('#question-prompt').className = 'question-prompt sentence-prompt';
    renderOptions(state.question.options);
  } else if (state.activity === 'order') {
    state.question = buildOrderQuestion(item);
    $('#question-instruction').textContent = 'Sắp xếp thành câu có nghĩa tiếng Việt bên dưới';
    $('#question-prompt').textContent = state.question.prompt;
    $('#question-prompt').className = 'question-prompt sentence-prompt';
    state.orderAvailable = state.question.shuffled.map((text, index) => ({ id: `${index}-${text}`, text }));
    $('#order-area').hidden = false;
    renderOrderBuilder();
  }
  $('#speak-word-btn').disabled = !state.slot.settings.audio;
}

function resetStudyUI() {
  $('#option-grid').innerHTML = '';
  $('#text-answer-area').hidden = true;
  $('#text-answer-input').value = '';
  $('#order-area').hidden = true;
  $('#answer-panel').hidden = true;
  $('#rating-row').hidden = true;
  $('#next-word-btn').hidden = true;
  $('#example-card').hidden = true;
  $('#answer-extra').hidden = true;
  $('#answer-extra').innerHTML = '';
  $('#admin-edit-current-btn').hidden = true;
  $('#traditional-text').textContent = '';
  $('#pinyin-hint').textContent = '';
}

function renderOptions(options) {
  $('#option-grid').innerHTML = options.map((option, index) => `<button class="option-btn" data-index="${index}"><span>${index + 1}</span>${escapeHtml(option)}</button>`).join('');
  $$('.option-btn').forEach(btn => btn.addEventListener('click', () => answerOption(Number(btn.dataset.index), btn)));
}

function answerOption(index, button) {
  if (state.answeredThisQuestion) return;
  const selected = state.question.options[index];
  const isCorrect = selected === state.question.correct;
  $$('.option-btn').forEach((btn, i) => {
    btn.disabled = true;
    if (state.question.options[i] === state.question.correct) btn.classList.add('correct');
  });
  if (!isCorrect) button.classList.add('wrong');
  completeQuestion(isCorrect, selected);
}

function checkTextAnswer() {
  if (state.answeredThisQuestion || state.activity !== 'dictation') return;
  const answer = $('#text-answer-input').value.trim();
  if (!answer) return toast('Hãy nhập chữ Hán bạn nghe được.', 'warn');
  $('#text-answer-input').disabled = true;
  $('#check-text-answer-btn').disabled = true;
  completeQuestion(checkDictation(answer, state.question), answer);
}

function renderOrderBuilder() {
  $('#order-answer').innerHTML = state.orderSelected.length
    ? state.orderSelected.map(item => `<button class="token-btn selected" data-order-id="${escapeHtml(item.id)}" data-source="selected">${escapeHtml(item.text)}</button>`).join('')
    : '<span class="empty-note">Bấm các cụm bên dưới để xếp câu</span>';
  $('#order-bank').innerHTML = state.orderAvailable.map(item => `<button class="token-btn" data-order-id="${escapeHtml(item.id)}" data-source="available">${escapeHtml(item.text)}</button>`).join('');
  $$('#order-area .token-btn').forEach(btn => btn.addEventListener('click', () => moveOrderToken(btn.dataset.orderId, btn.dataset.source)));
}

function moveOrderToken(id, source) {
  if (state.answeredThisQuestion) return;
  if (source === 'available') {
    const index = state.orderAvailable.findIndex(item => item.id === id);
    if (index >= 0) state.orderSelected.push(state.orderAvailable.splice(index, 1)[0]);
  } else {
    const index = state.orderSelected.findIndex(item => item.id === id);
    if (index >= 0) state.orderAvailable.push(state.orderSelected.splice(index, 1)[0]);
  }
  renderOrderBuilder();
}

function resetOrderBuilder() {
  if (state.answeredThisQuestion) return;
  state.orderAvailable.push(...state.orderSelected.splice(0));
  shuffle(state.orderAvailable);
  renderOrderBuilder();
}

function checkOrderAnswer() {
  if (state.answeredThisQuestion || state.activity !== 'order') return;
  if (!state.orderSelected.length) return toast('Hãy xếp câu trước khi kiểm tra.', 'warn');
  const answer = state.orderSelected.map(item => item.text);
  completeQuestion(checkOrder(answer, state.question), answer.join(''));
  $$('#order-area button').forEach(btn => { btn.disabled = true; });
}

function completeQuestion(isCorrect, selected) {
  state.answeredThisQuestion = true;
  state.pendingCorrect = isCorrect;
  state.selectedAnswer = selected;
  const detail = questionDetail();
  $('#answer-result').textContent = isCorrect ? 'Đúng rồi' : 'Chưa đúng';
  $('#answer-result').className = isCorrect ? 'result ok' : 'result error';
  $('#answer-main').textContent = detail.main;
  $('#answer-meaning').textContent = detail.meaning;
  $('#verification-badge').textContent = detail.verification;
  $('#verification-badge').dataset.status = detail.verificationStatus;
  $('#answer-panel').hidden = false;
  renderAnswerExtra(detail);
  const editableWord = detail.word && isStandardizedLevel(detail.word.level);
  $('#admin-edit-current-btn').hidden = !(editableWord && isAdminUnlocked());
  if (editableWord) $('#admin-edit-current-btn').dataset.wordId = detail.word.id;
  $('#rating-row').hidden = false;
  $('#next-word-btn').hidden = false;
  if (detail.example) {
    $('#example-zh').textContent = detail.example.zh;
    $('#example-pinyin').textContent = detail.example.pinyin;
    $('#example-vi').textContent = detail.example.vi;
    $('#example-card').hidden = false;
  }
  if (state.slot.settings.audio && state.activity !== 'dictation') speakCurrentQuestion();
}

function questionDetail() {
  if (state.activity === 'quiz' || state.activity === 'weak' || state.activity === 'dictation') {
    const word = state.question.word;
    return {
      main: `${word.simplified} · ${word.pinyin}`,
      meaning: word.senses.map(s => s.vi).slice(0, 4).join('; '),
      verification: verificationLabel(word.verification), verificationStatus: word.verification,
      example: word.example ? { zh: word.example.zh, pinyin: word.example.pinyin, vi: word.example.vi } : null,
      word
    };
  }
  const ex = state.question.example;
  return {
    main: `${ex.target} · ${ex.pinyin}`,
    meaning: ex.meaning,
    verification: 'Câu ví dụ đã duyệt', verificationStatus: 'kiem_tra_thu_cong',
    example: { zh: ex.zh, pinyin: ex.sentencePinyin, vi: ex.vi },
    word: state.wordIndex.get(ex.wordId) || null
  };
}

function currentWordId() {
  return (state.activity === 'fill' || state.activity === 'order') ? state.question.example.wordId : state.question.word.id;
}

function currentSrsMode() {
  return ACTIVITIES[state.activity]?.srsMode(state.slot) || state.slot.settings.mode;
}

function applyRating(grade) {
  if (!state.answeredThisQuestion || state.ratingLocked) return;
  state.ratingLocked = true;
  const wordId = currentWordId();
  const mode = currentSrsMode();
  const key = cardKey(wordId, mode);
  const effectiveGrade = state.pendingCorrect ? grade : GRADES.AGAIN;
  state.slot.cards[key] = reviewCard(state.slot.cards[key], effectiveGrade);
  const responseMs = Math.max(0, Date.now() - state.answerStartedAt);
  recordAttempt(wordId, state.pendingCorrect, responseMs);
  updateStreak(state.slot);
  state.slot.stats.answered += 1;
  if (state.pendingCorrect) state.slot.stats.correct += 1;
  state.slot.stats.lastStudyDate = new Date().toISOString();
  saveSlot(state.slot);
  state.session.answered += 1;
  if (state.pendingCorrect) state.session.correct += 1;
  state.session.responseMs += responseMs;
  state.index += 1;
  renderQuestion();
}

function recordAttempt(wordId, correct, responseMs) {
  const at = Date.now();
  state.slot.attemptLog.push({
    at, wordId, correct: Boolean(correct), activity: state.activity,
    mode: currentSrsMode(), responseMs, selected: serializeAnswer(state.selectedAnswer),
    correctAnswer: serializeAnswer(state.question.correct)
  });
  state.slot.attemptLog = state.slot.attemptLog.slice(-2000);
  const date = new Date(at).toISOString().slice(0, 10);
  const entry = state.slot.history[date] || { answered: 0, correct: 0, words: [], seconds: 0, activities: {} };
  entry.answered += 1;
  if (correct) entry.correct += 1;
  if (!entry.words.includes(wordId)) entry.words.push(wordId);
  entry.seconds = Number(entry.seconds || 0) + Math.round(responseMs / 1000);
  entry.activities[state.activity] = Number(entry.activities[state.activity] || 0) + 1;
  state.slot.history[date] = entry;
}

async function finishSession() {
  $('#study-progress-fill').style.width = '100%';
  const durationSec = Math.max(1, Math.round((Date.now() - state.session.startedAt) / 1000));
  const accuracy = state.session.answered ? Math.round(state.session.correct / state.session.answered * 100) : 0;
  state.slot.stats.sessions += 1;
  state.slot.stats.studySeconds += durationSec;
  state.slot.sessions.push({
    id: `S-${Date.now()}`, activity: state.activity, level: state.slot.settings.level,
    mode: currentSrsMode(), answered: state.session.answered, correct: state.session.correct,
    accuracy, durationSec, finishedAt: new Date().toISOString()
  });
  state.slot.sessions = state.slot.sessions.slice(-180);
  saveSlot(state.slot);
  await syncNow(state.slot);
  renderCloudStatus();
  $('#session-result-title').textContent = 'Hoàn thành phiên học';
  $('#session-result-body').textContent = `Đúng ${state.session.correct}/${state.session.answered} câu • Chính xác ${accuracy}% • ${Math.ceil(durationSec / 60)} phút`;
  showDashboard();
  openModal('session-modal');
}

function openWeakBook() {
  state.weakRows = computeWeakWords(state.words, state.slot, 100);
  $('#start-weak-btn').disabled = state.weakRows.length === 0;
  $('#weak-content').innerHTML = state.weakRows.length
    ? `<p>Điểm yếu kết hợp số lần sai, lapses SRS, độ khó và thời điểm sai gần nhất.</p><div class="weak-list">${state.weakRows.slice(0, 50).map(row => `<div class="weak-row"><span class="hanzi-small">${escapeHtml(row.word.simplified)}</span><div><strong>${escapeHtml(row.word.pinyin)} · ${escapeHtml(row.word.meaning)}</strong><p>${escapeHtml(row.reason)} · Chính xác ${row.accuracy}%</p></div><b>${Math.round(row.score)}</b></div>`).join('')}</div>`
    : '<div class="info-card">Chưa có đủ câu sai để tạo sổ từ yếu.</div>';
  openModal('weak-modal');
}

function openPlanModal() {
  const plan = state.slot.plan;
  $('#plan-target-level').value = plan.targetLevel;
  if (!plan.targetDate) {
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 120);
    $('#plan-target-date').value = defaultDate.toISOString().slice(0, 10);
  } else $('#plan-target-date').value = plan.targetDate;
  $('#plan-minutes').value = plan.minutesPerDay;
  $('#plan-days').value = plan.daysPerWeek;
  $('#plan-new-words').value = plan.newWordsPerDay;
  renderPlanPreview();
  openModal('plan-modal');
}

function renderPlanPreview() {
  const temp = structuredCloneSafe(state.slot);
  temp.plan = readPlanForm();
  const summary = planSummary(temp, state.meta);
  $('#plan-preview').innerHTML = `<h3>Dự kiến</h3><p>Còn ${summary.remaining.toLocaleString('vi-VN')} từ trong mục tiêu. Có khoảng ${summary.studyDays} ngày học; cần trung bình <b>${summary.requiredPerStudyDay} từ/ngày học</b>.</p>`;
}

function readPlanForm() {
  return {
    ...state.slot.plan,
    targetLevel: $('#plan-target-level').value,
    targetDate: $('#plan-target-date').value,
    minutesPerDay: clamp(Number($('#plan-minutes').value), 5, 180),
    daysPerWeek: clamp(Number($('#plan-days').value), 1, 7),
    newWordsPerDay: clamp(Number($('#plan-new-words').value), 5, 200)
  };
}

function savePlan() {
  state.slot.plan = readPlanForm();
  saveSlot(state.slot);
  closeModal($('#plan-modal'));
  renderDashboard();
  toast('Đã lưu kế hoạch học.');
}

function renderStats() {
  const stats = buildAdvancedStats(state.slot, 30);
  const labels = { quiz: 'Trắc nghiệm', weak: 'Sổ từ yếu', dictation: 'Chính tả', fill: 'Điền từ', order: 'Sắp xếp câu', 'hanzi-vi': 'Hán → Việt', 'vi-hanzi': 'Việt → Hán', 'hanzi-pinyin': 'Hán → pinyin', 'pinyin-hanzi': 'Pinyin → Hán' };
  $('#stats-content').innerHTML = `
    <div class="stats-grid"><div><strong>${state.slot.stats.answered.toLocaleString('vi-VN')}</strong><span>Tổng lượt trả lời</span></div><div><strong>${stats.accuracy}%</strong><span>Chính xác 30 ngày</span></div><div><strong>${stats.retention}%</strong><span>Độ lưu giữ ước tính</span></div><div><strong>${stats.averageResponseMs ? (stats.averageResponseMs / 1000).toFixed(1) : 0}s</strong><span>Phản hồi trung bình</span></div><div><strong>${stats.currentStreak}</strong><span>Chuỗi ngày hiện tại</span></div><div><strong>${stats.totalMinutes}</strong><span>Tổng phút học</span></div></div>
    <h3>Hoạt động 30 ngày</h3>${renderBars(stats.byActivity, labels)}
    <h3>Hướng học</h3>${renderBars(stats.byMode, labels)}
    <h3>30 ngày gần nhất</h3><div class="heatmap">${stats.daily.map(day => `<div class="heat-cell" data-level="${heatLevel(day.answered)}" title="${day.date}: ${day.answered} câu"></div>`).join('')}</div>
    <p class="muted-note">Chuỗi dài nhất: ${stats.longestStreak} ngày. Độ lưu giữ là ước tính từ lịch sử đúng/sai của các thẻ đã được ôn ít nhất hai lần.</p>`;
}

function renderBars(rows, labels) {
  if (!rows.length) return '<p>Chưa có dữ liệu.</p>';
  return `<div class="bar-list">${rows.map(row => `<div class="bar-row"><span>${escapeHtml(labels[row.key] || row.key)} · ${row.total} câu</span><div class="bar-track"><div class="bar-fill" style="width:${row.accuracy}%"></div></div><strong>${row.accuracy}%</strong></div>`).join('')}</div>`;
}

function openExamModal() {
  $('#exam-level-select').value = state.slot.settings.level;
  const examples = state.examples.filter(ex => Number(ex.level) <= Number(state.slot.settings.level));
  const bank = questionBankSummary(state.words, examples);
  $('#exam-bank-detail').textContent = `Cấp hiện tại có ${state.words.length.toLocaleString('vi-VN')} từ và ${examples.length} câu ví dụ, tạo được khoảng ${bank.total.toLocaleString('vi-VN')} biến thể.`;
  openModal('exam-modal');
}

async function startExam() {
  const level = $('#exam-level-select').value;
  const size = Number($('#exam-size-select').value);
  $('#start-exam-btn').disabled = true;
  $('#start-exam-btn').textContent = 'Đang tạo đề…';
  try {
    const words = applyContentToWords(await loadLevelsUpTo(level));
    const examples = state.examples.filter(ex => Number(ex.level) <= Number(level));
    const definition = buildMockExam({ words, examples, level, size, seed: `${Date.now()}-${state.slot.id}` });
    state.exam = {
      definition, index: 0, answers: [], currentAnswer: null,
      orderAvailable: [], orderSelected: [], startedAt: Date.now(),
      endsAt: Date.now() + definition.durationMinutes * 60000
    };
    closeModal($('#exam-modal'));
    $('#dashboard-view').hidden = true;
    $('#reading-view').hidden = true;
    $('#study-view').hidden = true;
    $('#exam-result-view').hidden = true;
    $('#exam-view').hidden = false;
    startExamTimer();
    renderExamQuestion();
  } catch (error) {
    console.error(error);
    toast(error.message || 'Không tạo được đề.', 'error');
  } finally {
    $('#start-exam-btn').disabled = false;
    $('#start-exam-btn').textContent = 'Bắt đầu làm đề';
  }
}

function renderExamQuestion() {
  const q = currentExamQuestion();
  if (!q) return finishExam();
  state.exam.currentAnswer = null;
  state.exam.orderAvailable = [];
  state.exam.orderSelected = [];
  $('#exam-position').textContent = `${state.exam.index + 1}/${state.exam.definition.questions.length}`;
  $('#exam-progress-fill').style.width = `${Math.round(state.exam.index / state.exam.definition.questions.length * 100)}%`;
  $('#exam-type-label').textContent = EXAM_TYPES[q.type];
  $('#exam-prompt').textContent = q.prompt;
  $('#exam-prompt').className = ['meaning','pinyin'].includes(q.type) ? 'question-prompt hanzi' : 'question-prompt sentence-prompt';
  $('#exam-option-grid').innerHTML = '';
  $('#exam-order-area').hidden = true;
  $('#exam-speak-btn').hidden = q.type !== 'listening';
  $('#exam-next-btn').disabled = true;
  $('#exam-next-btn').textContent = state.exam.index === state.exam.definition.questions.length - 1 ? 'Nộp bài' : 'Câu tiếp theo';
  if (q.type === 'listening') {
    $('#exam-prompt').textContent = '🔊';
    setTimeout(() => speakChinese(q.audioText, state.slot.settings.audio), 180);
  }
  if (q.type === 'order') {
    $('#exam-order-area').hidden = false;
    state.exam.orderAvailable = q.shuffled.map((text, index) => ({ id: `${index}-${text}`, text }));
    renderExamOrder();
  } else {
    $('#exam-option-grid').innerHTML = q.options.map((option, index) => `<button class="option-btn exam-option" data-index="${index}"><span>${index + 1}</span>${escapeHtml(option)}</button>`).join('');
    $$('.exam-option').forEach(btn => btn.addEventListener('click', () => selectExamOption(Number(btn.dataset.index), btn)));
  }
}

function selectExamOption(index, button) {
  $$('.exam-option').forEach(btn => btn.classList.remove('selected'));
  button.classList.add('selected');
  state.exam.currentAnswer = currentExamQuestion().options[index];
  $('#exam-next-btn').disabled = false;
}

function renderExamOrder() {
  $('#exam-order-answer').innerHTML = state.exam.orderSelected.length ? state.exam.orderSelected.map(item => `<button class="token-btn selected" data-id="${escapeHtml(item.id)}" data-source="selected">${escapeHtml(item.text)}</button>`).join('') : '<span class="empty-note">Xếp câu tại đây</span>';
  $('#exam-order-bank').innerHTML = state.exam.orderAvailable.map(item => `<button class="token-btn" data-id="${escapeHtml(item.id)}" data-source="available">${escapeHtml(item.text)}</button>`).join('');
  $$('#exam-order-area .token-btn').forEach(btn => btn.addEventListener('click', () => moveExamToken(btn.dataset.id, btn.dataset.source)));
  state.exam.currentAnswer = state.exam.orderSelected.map(item => item.text);
  $('#exam-next-btn').disabled = state.exam.orderSelected.length === 0;
}

function moveExamToken(id, source) {
  if (source === 'available') {
    const index = state.exam.orderAvailable.findIndex(item => item.id === id);
    if (index >= 0) state.exam.orderSelected.push(state.exam.orderAvailable.splice(index, 1)[0]);
  } else {
    const index = state.exam.orderSelected.findIndex(item => item.id === id);
    if (index >= 0) state.exam.orderAvailable.push(state.exam.orderSelected.splice(index, 1)[0]);
  }
  renderExamOrder();
}

function nextExamQuestion() {
  if (!state.exam || state.exam.currentAnswer == null) return;
  state.exam.answers[state.exam.index] = structuredCloneSafe(state.exam.currentAnswer);
  if (state.exam.index >= state.exam.definition.questions.length - 1) return finishExam();
  state.exam.index += 1;
  renderExamQuestion();
}

async function finishExam() {
  if (!state.exam || state.exam.submitting) return;
  state.exam.submitting = true;
  clearExamTimer();
  const result = scoreExam(state.exam.definition, state.exam.answers);
  const durationSec = Math.max(1, Math.round((Date.now() - state.exam.startedAt) / 1000));
  const attempt = {
    id: `E-${Date.now()}`, examId: state.exam.definition.id, level: state.exam.definition.level,
    title: state.exam.definition.title, score: result.score, correct: result.correct, total: result.total,
    byType: result.byType, details: result.details, durationSec, finishedAt: new Date().toISOString()
  };
  state.slot.examAttempts.push(attempt);
  state.slot.examAttempts = state.slot.examAttempts.slice(-30);
  state.slot.stats.studySeconds += durationSec;
  saveSlot(state.slot);
  await syncNow(state.slot);
  renderExamResult(attempt);
  $('#exam-view').hidden = true;
  $('#exam-result-view').hidden = false;
  state.exam = null;
}

function renderExamResult(attempt) {
  $('#exam-score').textContent = attempt.score;
  $('.score-ring').style.setProperty('--score-angle', `${attempt.score * 3.6}deg`);
  $('#exam-result-title').textContent = attempt.score >= 80 ? 'Kết quả tốt' : attempt.score >= 60 ? 'Đã đạt mức khá' : 'Cần ôn thêm';
  $('#exam-result-summary').textContent = `Đúng ${attempt.correct}/${attempt.total} câu trong ${Math.ceil(attempt.durationSec / 60)} phút.`;
  $('#exam-type-scores').innerHTML = Object.entries(attempt.byType).map(([type, row]) => `<div><strong>${row.score}%</strong><span>${EXAM_TYPES[type]} · ${row.correct}/${row.total}</span></div>`).join('');
  $('#exam-review-list').innerHTML = attempt.details.map((row, index) => `<article class="review-item ${row.correct ? '' : 'wrong'}"><h4>Câu ${index + 1} · ${EXAM_TYPES[row.type]} · ${row.correct ? 'Đúng' : 'Sai'}</h4><p><b>Đề:</b> ${escapeHtml(row.prompt)}\n<b>Đáp án của bạn:</b> ${escapeHtml(serializeAnswer(row.answer) || 'Bỏ trống')}\n<b>Đáp án đúng:</b> ${escapeHtml(serializeAnswer(row.correctAnswer))}</p><p>${escapeHtml(row.explanation)}</p></article>`).join('');
}

function openExamHistory() {
  const attempts = [...(state.slot.examAttempts || [])].reverse();
  $('#exam-history-content').innerHTML = attempts.length ? attempts.map(attempt => `
    <details><summary class="history-exam-row"><span><b>${escapeHtml(attempt.title)}</b><br><small>${formatDate(attempt.finishedAt)} · ${Math.ceil(attempt.durationSec / 60)} phút</small></span><strong>${attempt.score} điểm</strong><span>${attempt.correct}/${attempt.total} câu</span></summary>
    <div class="bar-list">${Object.entries(attempt.byType || {}).map(([type,row]) => `<div class="bar-row"><span>${EXAM_TYPES[type]}</span><div class="bar-track"><div class="bar-fill" style="width:${row.score}%"></div></div><strong>${row.score}%</strong></div>`).join('')}</div></details>`).join('') : '<div class="info-card">Chưa có lần làm đề nào.</div>';
  openModal('exam-history-modal');
}

function startExamTimer() {
  clearExamTimer();
  updateExamTimer();
  state.examTimer = setInterval(updateExamTimer, 1000);
}

function updateExamTimer() {
  if (!state.exam) return;
  const remaining = Math.max(0, state.exam.endsAt - Date.now());
  $('#exam-timer').textContent = formatClock(Math.ceil(remaining / 1000));
  if (remaining <= 0) {
    toast('Hết giờ, hệ thống tự nộp bài.', 'warn');
    finishExam();
  }
}

function quitExam() {
  if (!confirm('Thoát đề hiện tại? Kết quả chưa nộp sẽ không được lưu.')) return;
  clearExamTimer();
  state.exam = null;
  showDashboard();
}

function currentExamQuestion() { return state.exam?.definition?.questions?.[state.exam.index] || null; }

function exportCurrentSlot() {
  const safeName = state.slot.profile.name.replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-|-$/g, '') || `slot-${state.slot.id}`;
  downloadText(`hsk-${safeName}-${new Date().toISOString().slice(0,10)}.json`, exportSlot(state.slot));
  toast('Đã xuất tệp sao lưu slot.');
}

async function handleImport(event) {
  const file = event.target.files?.[0];
  event.target.value = '';
  if (!file) return;
  try {
    state.slot = importSlot(state.slot.id, await file.text());
    state.words = await loadEffectiveLevel(state.slot.settings.level);
    state.wordIndex = new Map(state.words.map(word => [word.id, word]));
    hydrateSettings();
    renderDashboard();
    closeModal($('#settings-modal'));
    toast('Đã nhập dữ liệu và xếp hàng đồng bộ.');
  } catch (error) { toast(error.message || 'Không nhập được tệp.', 'error'); }
}

function resetCurrentSlot() {
  if (!confirm(`Xóa toàn bộ tiến độ của ${state.slot.profile.name} trong Slot ${state.slot.id}, gồm cả dữ liệu Supabase?`)) return;
  const id = state.slot.id;
  resetSlot(id);
  state.slot = null;
  closeModal($('#settings-modal'));
  renderSlots();
  showScreen('slot-screen');
  toast(`Đã xóa Slot ${id}.`);
}

async function manualSync() {
  let status = getCloudStatus();
  if (!status.enabled) return toast('Supabase chưa được cấu hình trong js/config.js.', 'warn');
  $('#sync-now-btn').disabled = true;
  if (!status.connected) {
    await setupCloud();
    status = getCloudStatus();
  }
  if (!status.connected) {
    $('#sync-now-btn').disabled = false;
    renderCloudStatus();
    return toast('Chưa kết nối được Supabase. Dữ liệu vẫn đang lưu cục bộ.', 'warn');
  }
  const ok = await syncNow(state.slot);
  $('#sync-now-btn').disabled = false;
  renderCloudStatus();
  toast(ok ? 'Đã đồng bộ slot hiện tại.' : 'Chưa đồng bộ được; dữ liệu cục bộ vẫn an toàn.', ok ? 'ok' : 'warn');
}

function renderCloudStatus() {
  const status = getCloudStatus();
  const text = status.message || (status.connected ? 'Đã đồng bộ Supabase' : 'Đang lưu cục bộ');
  if ($('#cloud-status')) $('#cloud-status').textContent = text;
  if ($('#top-cloud-status')) $('#top-cloud-status').textContent = text;
  if ($('#settings-cloud-status')) $('#settings-cloud-status').textContent = text;
  const dot = $('#cloud-dot');
  if (dot) {
    dot.classList.toggle('connected', Boolean(status.connected));
    dot.classList.toggle('error', Boolean(status.enabled && !status.connected));
  }
}

function speakCurrentQuestion() {
  const text = state.activity === 'fill' || state.activity === 'order'
    ? state.question?.example?.zh
    : state.question?.word?.simplified;
  if (text) speakChinese(text, state.slot?.settings?.audio);
}

function currentExample() {
  if (state.activity === 'fill' || state.activity === 'order') return { zh: state.question.example.zh };
  const ex = state.question?.word?.example;
  return ex ? { zh: ex.zh } : null;
}

function currentQualityWords(level = state.libraryLevel) {
  return state.qualityWordsByLevel.get(String(level)) || [];
}

function openHsk1Library() {
  const preferred = String(state.slot?.settings?.level || '1');
  state.libraryLevel = isStandardizedLevel(preferred) ? preferred : '1';
  $('#quality-library-level').value = state.libraryLevel;
  prepareLibraryLevel();
  openModal('hsk1-library-modal');
}

function prepareLibraryLevel() {
  const words = currentQualityWords();
  $('#quality-library-eyebrow').textContent = `Gói chất lượng HSK ${levelDisplay(state.libraryLevel)}`;
  $('#quality-library-title').textContent = `Thư viện HSK ${levelDisplay(state.libraryLevel)}: từ vựng, câu ví dụ và ngữ pháp`;
  renderHsk1QualitySummary();
  const topics = [...new Set(words.map(word => word.topic).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'vi'));
  $('#hsk1-library-topic').innerHTML = '<option value="">Tất cả chủ đề</option>' + topics.map(topic => `<option value="${escapeHtml(topic)}">${escapeHtml(topic)}</option>`).join('');
  $('#hsk1-library-search').value = '';
  renderHsk1LibraryWords();
  renderGrammarLibrary();
}

function renderHsk1QualitySummary() {
  const words = currentQualityWords();
  const q = qualitySummary(words, state.libraryLevel);
  const exampleCount = words.reduce((sum, word) => sum + (word.examples?.length || 0), 0);
  $('#hsk1-quality-summary').innerHTML = [
    [q.words,'Từ chuẩn hóa'],[exampleCount,'Câu ví dụ chuẩn hóa'],[q.exerciseExamples,'Câu dùng luyện tập'],[q.withCollocations,'Có cụm từ'],[q.overridden,'Admin đã sửa']
  ].map(([value,label])=>`<div><strong>${value}</strong><span>${label}</span></div>`).join('');
}

function filteredQualityWords(searchId, topicId = null, level = state.libraryLevel) {
  const query = ($(searchId)?.value || '').trim().toLowerCase();
  const topic = topicId ? ($(topicId)?.value || '') : '';
  return currentQualityWords(level).filter(word => {
    const haystack = `${word.simplified} ${word.traditional} ${word.pinyin} ${word.meaning} ${word.topic} ${(word.senses||[]).map(s=>s.vi).join(' ')}`.toLowerCase();
    return (!query || haystack.includes(query)) && (!topic || word.topic === topic);
  });
}

function renderHsk1LibraryWords() {
  const rows = filteredQualityWords('#hsk1-library-search','#hsk1-library-topic').slice(0,500);
  $('#hsk1-word-list').innerHTML = rows.length ? rows.map(word => `<button class="word-library-row" data-word-id="${word.id}"><span class="hanzi-small">${escapeHtml(word.simplified)}</span><span><strong>${escapeHtml(word.pinyin)} · ${escapeHtml(word.meaning)}</strong><small>${escapeHtml((word.pos || []).join(', ') || 'chưa phân loại')}</small></span><span class="word-topic">${escapeHtml(word.topic || '')}</span></button>`).join('') : '<div class="info-card">Không tìm thấy từ phù hợp.</div>';
  $$('#hsk1-word-list .word-library-row').forEach(btn => btn.addEventListener('click', () => renderHsk1WordDetail(btn.dataset.wordId)));
  if (rows[0]) renderHsk1WordDetail(rows[0].id);
  else $('#hsk1-word-detail').textContent = 'Không có từ phù hợp để hiển thị.';
}

function renderHsk1WordDetail(wordId) {
  const word = currentQualityWords().find(item => item.id === wordId);
  if (!word) return;
  $('#hsk1-word-detail').innerHTML = `<h2>${escapeHtml(word.simplified)}</h2><strong>${escapeHtml(word.pinyin)} · ${escapeHtml(word.meaning)}</strong><div class="tag-row">${[...(word.pos||[]),word.topic,...(word.measureWords||[]).map(x=>`LT ${x}`)].filter(Boolean).map(x=>`<span class="tag">${escapeHtml(x)}</span>`).join('')}</div><section><b>Các nghĩa</b>${listHtml((word.senses||[]).map(s=>s.vi))}</section><section><b>Cách dùng</b><p>${escapeHtml(word.usageNote || 'Chưa có ghi chú.')}</p></section><section><b>Cụm thường gặp</b>${listHtml(word.collocations)}</section><section><b>Từ dễ nhầm</b>${listHtml(word.confusables)}</section>${word.examples?.length?`<section><b>Câu ví dụ chuẩn hóa</b><div class="standard-example-list">${word.examples.map((example,index)=>`<div class="grammar-example standardized-example"><div class="example-level-row"><span class="pill">Mức ${example.difficulty || word.level}</span><small>${example.exerciseEligible?'Được dùng luyện tập':'Chỉ dùng học/ngữ cảnh'}</small></div><strong>${escapeHtml(example.zh)}</strong><span>${escapeHtml(example.pinyin)}</span><p>${escapeHtml(example.vi)}</p>${example.note?`<small>${escapeHtml(example.note)}</small>`:''}</div>`).join('')}</div></section>`:''}`;
}

function renderGrammarLibrary() {
  const grammar = state.grammarByLevel.get(String(state.libraryLevel)) || [];
  $('#hsk1-grammar-list').innerHTML = grammar.map(item => `<details class="grammar-item"><summary>${escapeHtml(item.title)}</summary><p><span class="grammar-formula">${escapeHtml(item.formula)}</span></p><p>${escapeHtml(item.explanation)}</p>${(item.examples||[]).map(ex=>`<div class="grammar-example"><strong>${escapeHtml(ex.zh)}</strong><span>${escapeHtml(ex.pinyin)}</span><p>${escapeHtml(ex.vi)}</p></div>`).join('')}<p><b>Lỗi thường gặp:</b> ${escapeHtml(item.mistake || '')}</p></details>`).join('') || '<div class="info-card">Chưa có gói ngữ pháp cho cấp này.</div>';
}

function listHtml(items) { return items?.length ? `<ul>${items.map(item=>`<li>${escapeHtml(item)}</li>`).join('')}</ul>` : '<p>Chưa bổ sung.</p>'; }


async function openReadingView() {
  const preferred = Math.min(7, Math.max(1, Number(state.slot?.settings?.level || 1)));
  $('#dashboard-view').hidden = true;
  $('#study-view').hidden = true;
  $('#exam-view').hidden = true;
  $('#exam-result-view').hidden = true;
  $('#reading-view').hidden = false;
  $('#reading-level-select').value = String(preferred);
  await loadReadingView(String(preferred));
}

async function loadReadingView(level) {
  try {
    state.readingLevel = String(level);
    state.readingPack = await loadReadingLevel(state.readingLevel);
    const words = standardizedLevels()
      .filter(item => Number(item) <= Number(state.readingLevel))
      .flatMap(item => state.qualityWordsByLevel.get(item) || []);
    state.readingMatcher = buildVocabularyMatcher(words);
    const passages = state.readingPack.passages || [];
    if (!passages.some(item => item.id === state.readingPassageId)) state.readingPassageId = passages[0]?.id || null;
    const displayLevel = state.readingLevel === '7' ? '7–9' : state.readingLevel;
    $('#reading-title').textContent = `Đọc hiểu HSK ${displayLevel}`;
    $('#reading-progress-label').textContent = `Đọc hiểu HSK ${displayLevel}`;
    $('#reading-meta').textContent = `${passages.length} bài · độ dài mục tiêu khoảng ${state.readingPack.meta?.targetCharacters || ''} chữ Hán · highlight từ HSK 1–${displayLevel}`;
    renderReadingPassageList();
    renderReadingPassage();
  } catch (error) {
    console.error(error);
    toast(error.message || 'Không tải được bài đọc.', 'error');
  }
}

function currentReadingPassage() {
  return state.readingPack?.passages?.find(item => item.id === state.readingPassageId) || state.readingPack?.passages?.[0] || null;
}

function renderReadingPassageList() {
  const rows = state.readingPack?.passages || [];
  $('#reading-passage-list').innerHTML = rows.map((item, index) => `
    <button class="reading-passage-row ${item.id === state.readingPassageId ? 'active' : ''}" data-reading-id="${item.id}">
      <span>${index + 1}</span><div><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.topic)} · ${item.actualCharacters} chữ</small></div>
    </button>`).join('');
  $$('#reading-passage-list .reading-passage-row').forEach(button => button.addEventListener('click', () => {
    state.readingPassageId = button.dataset.readingId;
    renderReadingPassageList();
    renderReadingPassage();
  }));
}

function renderReadingPassage() {
  const passage = currentReadingPassage();
  if (!passage) {
    $('#reading-sentences').innerHTML = '<div class="info-card">Chưa có bài đọc.</div>';
    return;
  }
  const showPinyin = $('#reading-pinyin-toggle').checked;
  const showTranslation = $('#reading-translation-toggle').checked;
  const stats = passageVocabularyStats(passage, state.readingMatcher);
  $('#reading-topic').textContent = passage.topic;
  $('#reading-passage-title').textContent = passage.title;
  $('#reading-length').textContent = `${passage.actualCharacters} chữ Hán · ${passage.sentences.length} câu · ${stats.uniqueWords} từ HSK được highlight`;
  $('#reading-sentences').innerHTML = passage.sentences.map((sentence, index) => {
    const tokens = tokenizeChinese(sentence.zh, state.readingMatcher).map(token => token.type === 'word'
      ? `<button class="reading-word" data-word-id="${token.word.id}" title="${escapeHtml(token.word.pinyin)} · ${escapeHtml(token.word.meaning)}">${escapeHtml(token.text)}</button>`
      : escapeHtml(token.text)).join('');
    return `<section class="reading-sentence" data-sentence="${index + 1}">
      <div class="reading-sentence-number">${index + 1}</div>
      <div><p class="reading-zh">${tokens}</p>${showPinyin ? `<p class="reading-pinyin">${escapeHtml(sentence.pinyin)}</p>` : ''}${showTranslation ? `<p class="reading-vi">${escapeHtml(sentence.vi)}</p>` : ''}</div>
      <button class="reading-speak-sentence" data-sentence-id="${sentence.id}" aria-label="Nghe câu ${index + 1}">🔊</button>
    </section>`;
  }).join('');
  $$('#reading-sentences .reading-word').forEach(button => button.addEventListener('click', () => renderReadingWordDetail(button.dataset.wordId)));
  $$('#reading-sentences .reading-speak-sentence').forEach(button => button.addEventListener('click', () => {
    const sentence = passage.sentences.find(item => item.id === button.dataset.sentenceId);
    if (sentence) speakChinese(sentence.zh, true, 0.78);
  }));
}

function renderReadingWordDetail(wordId) {
  const word = [...state.qualityWordsByLevel.values()].flat().find(item => item.id === wordId);
  if (!word) return;
  const examples = (word.examples || []).filter(item => item.kind === 'usage' || item.exerciseEligible).slice(0, 2);
  $('#reading-word-detail').innerHTML = `<div class="reading-word-title"><strong>${escapeHtml(word.simplified)}</strong><button id="reading-word-speak" class="speaker small-speaker">🔊</button></div><p class="reading-word-pinyin">${escapeHtml(word.pinyin)}</p><h3>${escapeHtml(word.meaning)}</h3><div class="tag-row">${[...(word.pos || []), word.topic].filter(Boolean).map(item => `<span class="tag">${escapeHtml(item)}</span>`).join('')}</div>${word.usageNote ? `<p><b>Cách dùng:</b> ${escapeHtml(word.usageNote)}</p>` : ''}${examples.length ? `<div class="reading-mini-examples">${examples.map(item => `<div><strong>${escapeHtml(item.zh)}</strong><span>${escapeHtml(item.vi)}</span></div>`).join('')}</div>` : ''}`;
  document.querySelector('#reading-word-detail #reading-word-speak')?.addEventListener('click', () => speakChinese(word.simplified, true, 0.78));
}

function speakReadingPassage() {
  const passage = currentReadingPassage();
  if (!passage) return;
  speakChinese(passage.sentences.map(item => item.zh).join(''), true, 0.78);
}

function openAdminEntry() {
  if (isAdminUnlocked()) return openAdminPanel();
  $('#admin-password-input').value = '';
  openModal('admin-login-modal');
  setTimeout(()=>$('#admin-password-input').focus(),80);
}

async function submitAdminLogin() {
  const button = $('#admin-login-submit'); button.disabled = true;
  try {
    const result = await unlockAdmin($('#admin-password-input').value, getCloudStatus().connected ? verifyAdminPassword : null);
    if (!result.ok) return toast(result.message,'error');
    closeModal($('#admin-login-modal'));
    toast('Đã mở quyền quản trị.');
    openAdminPanel();
  } catch (error) { toast(error.message || 'Không mở được quản trị.','error'); }
  finally { button.disabled = false; }
}

function openAdminPanel() {
  if (!isAdminUnlocked()) return openAdminEntry();
  $('#admin-source-badge').textContent = getAdminSource() === 'supabase' ? 'Mật khẩu Supabase' : 'Mật khẩu cục bộ';
  const selectedLevel = state.adminSelectedWordId?.match(/^L([1-7])-/)?.[1];
  const preferred = selectedLevel || String(state.slot?.settings?.level || state.adminLevel || '1');
  state.adminLevel = isStandardizedLevel(preferred) ? preferred : '1';
  $('#admin-level-select').value = state.adminLevel;
  $('#admin-panel-eyebrow').textContent = `Quản trị học liệu HSK ${levelDisplay(state.adminLevel)}`;
  renderAdminWordList();
  if (state.adminSelectedWordId) selectAdminWord(state.adminSelectedWordId);
  openModal('admin-modal');
}

function renderAdminWordList() {
  $('#admin-panel-eyebrow').textContent = `Quản trị học liệu HSK ${levelDisplay(state.adminLevel)}`;
  const rows = filteredQualityWords('#admin-word-search', null, state.adminLevel).slice(0,1000);
  $('#admin-word-list').innerHTML = rows.map(word => `<button class="admin-word-row ${word.id===state.adminSelectedWordId?'active':''}" data-word-id="${word.id}"><b>${escapeHtml(word.simplified)}</b><span><strong>${escapeHtml(word.pinyin)}</strong><small>${escapeHtml(word.meaning)}</small></span></button>`).join('') || '<div class="info-card">Không tìm thấy từ.</div>';
  $$('#admin-word-list .admin-word-row').forEach(btn=>btn.addEventListener('click',()=>selectAdminWord(btn.dataset.wordId)));
}

function selectAdminWord(wordId) {
  const level = wordId?.match(/^L([1-7])-/)?.[1] || state.adminLevel;
  if (isStandardizedLevel(level) && level !== state.adminLevel) {
    state.adminLevel = level;
    $('#admin-level-select').value = level;
  }
  const word = currentQualityWords(state.adminLevel).find(item=>item.id===wordId); if (!word) return;
  state.adminSelectedWordId = wordId; renderAdminWordList();
  $('#admin-editor-empty').hidden = true; $('#admin-editor').hidden = false;
  $('#admin-edit-hanzi').textContent = word.simplified; $('#admin-edit-pinyin').textContent = word.pinyin; $('#admin-edit-id').textContent = `${word.id} · HSK ${levelDisplay(word.level)} · ${word.contentSource==='admin'?'đã sửa':'bản chuẩn hóa'}`;
  $('#admin-primary-meaning').value = word.meaning || '';
  $('#admin-senses').value = (word.senses||[]).map(s=>s.vi).join('\n');
  $('#admin-pos').value = (word.pos||[]).join(', '); $('#admin-topic').value = word.topic || '';
  $('#admin-measure-words').value = (word.measureWords||[]).join(', '); $('#admin-usage-note').value = word.usageNote || '';
  $('#admin-collocations').value = (word.collocations||[]).join('\n'); $('#admin-confusables').value = (word.confusables||[]).join('\n');
  $('#admin-example-zh').value = word.example?.zh || ''; $('#admin-example-pinyin').value = word.example?.pinyin || ''; $('#admin-example-vi').value = word.example?.vi || ''; $('#admin-example-eligible').checked = Boolean(word.example?.exerciseEligible);
}

function adminPatchFromForm() {
  return { primaryMeaning:$('#admin-primary-meaning').value, senses:splitLines($('#admin-senses').value), pos:splitLines($('#admin-pos').value), topic:$('#admin-topic').value, measureWords:splitLines($('#admin-measure-words').value), usageNote:$('#admin-usage-note').value, collocations:splitLines($('#admin-collocations').value), confusables:splitLines($('#admin-confusables').value), example:{zh:$('#admin-example-zh').value,pinyin:$('#admin-example-pinyin').value,vi:$('#admin-example-vi').value,exerciseEligible:$('#admin-example-eligible').checked} };
}

async function saveAdminWord(event) {
  event.preventDefault(); if (!state.adminSelectedWordId || !isAdminUnlocked()) return;
  const patch = saveLocalContentOverride(state.adminSelectedWordId, adminPatchFromForm());
  let remoteOk = false;
  if (getCloudStatus().connected && getAdminPassword()) {
    try { remoteOk = await saveRemoteContentOverride(getAdminPassword(), state.adminSelectedWordId, patch); }
    catch (error) { toast(error.message || 'Đã lưu trên máy nhưng chưa lưu được Supabase.','warn'); }
  }
  await refreshContentState(); selectAdminWord(state.adminSelectedWordId); renderHsk1QualitySummary();
  toast(remoteOk ? 'Đã lưu nội dung dùng chung lên Supabase.' : 'Đã lưu nội dung trên trình duyệt.');
}

async function resetAdminWord() {
  const id=state.adminSelectedWordId; if (!id || !confirm('Khôi phục từ này về bản chuẩn hóa ban đầu?')) return;
  deleteLocalContentOverride(id);
  if (getCloudStatus().connected && getAdminPassword()) { try { await deleteRemoteContentOverride(getAdminPassword(),id); } catch(error){ toast(error.message || 'Chưa xóa được bản Supabase.','warn'); } }
  await refreshContentState(); selectAdminWord(id); renderHsk1QualitySummary(); toast('Đã khôi phục bản chuẩn hóa.');
}

function lockAdminUi() { lockAdmin(); closeModal($('#admin-modal')); $('#admin-edit-current-btn').hidden=true; toast('Đã khóa quyền quản trị.'); }

async function submitAdminPasswordChange() {
  const current=$('#admin-current-password').value, next=$('#admin-new-password').value, confirmValue=$('#admin-confirm-password').value;
  if (next.length<8) return toast('Mật khẩu mới phải có ít nhất 8 ký tự.','warn');
  if (next!==confirmValue) return toast('Hai lần nhập mật khẩu mới không khớp.','warn');
  try {
    let ok=false;
    if (getCloudStatus().connected) ok=await changeRemoteAdminPassword(current,next);
    if (ok) await setLocalAdminPassword(next); else ok=await changeLocalAdminPassword(current,next);
    if (!ok) return toast('Mật khẩu hiện tại không đúng.','error');
    closeModal($('#admin-password-modal')); $('#admin-current-password').value=''; $('#admin-new-password').value=''; $('#admin-confirm-password').value='';
    toast('Đã đổi mật khẩu quản trị.');
  } catch(error){ toast(error.message || 'Không đổi được mật khẩu.','error'); }
}

async function importAdminContentFile(event) {
  const file=event.target.files?.[0]; event.target.value=''; if(!file)return;
  try { const count=importContentOverrides(await file.text()); await refreshContentState(); renderAdminWordList(); toast(`Đã nhập ${count} nội dung chỉnh sửa trên máy.`); }
  catch(error){ toast(error.message || 'Không nhập được tệp.','error'); }
}

function renderAnswerExtra(detail) {
  const word=detail.word;
  if (!word || !isStandardizedLevel(word.level)) return;
  const html=[];
  const tags=[...(word.pos||[]),word.topic,...(word.measureWords||[]).map(x=>`Lượng từ: ${x}`)].filter(Boolean);
  if(tags.length)html.push(`<div class="tag-row">${tags.map(x=>`<span class="tag">${escapeHtml(x)}</span>`).join('')}</div>`);
  if(word.usageNote)html.push(`<p><b>Cách dùng:</b> ${escapeHtml(word.usageNote)}</p>`);
  if(word.collocations?.length)html.push(`<p><b>Cụm thường gặp:</b> ${escapeHtml(word.collocations.join(' · '))}</p>`);
  if(word.confusables?.length)html.push(`<p><b>Dễ nhầm:</b> ${escapeHtml(word.confusables.join(' · '))}</p>`);
  if(!html.length)return;
  $('#answer-extra').innerHTML=html.join(''); $('#answer-extra').hidden=false;
}

function splitLines(value) { return [...new Set(String(value||'').split(/[\n,;]+/).map(x=>x.trim()).filter(Boolean))]; }

function handleKeyboard(event) {
  if (event.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(closeModal);
    return;
  }
  if ($('#study-view')?.hidden || state.answeredThisQuestion || !['quiz','weak','fill'].includes(state.activity)) return;
  const number = Number(event.key);
  if (number >= 1 && number <= 4) $$('.option-btn')[number - 1]?.click();
}

function openModal(id) { (typeof id === 'string' ? document.getElementById(id) : id)?.classList.add('open'); }
function closeModal(el) { el?.classList.remove('open'); }
function finishSpeech() { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); }
function clearExamTimer() { if (state.examTimer) clearInterval(state.examTimer); state.examTimer = null; }
function emptySession() { return { answered: 0, correct: 0, responseMs: 0, startedAt: null, activity: 'quiz' }; }
function heatLevel(value) { return value <= 0 ? 0 : value < 10 ? 1 : value < 25 ? 2 : value < 50 ? 3 : 4; }
function formatClock(seconds) { const m = Math.floor(seconds / 60); const s = seconds % 60; return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`; }
function clamp(value, min, max) { return Math.max(min, Math.min(max, Number.isFinite(value) ? value : min)); }
function serializeAnswer(value) { return Array.isArray(value) ? value.join('') : String(value ?? ''); }
function structuredCloneSafe(value) { return typeof structuredClone === 'function' ? structuredClone(value) : JSON.parse(JSON.stringify(value)); }
function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, char => ({ '&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;' }[char])); }
function registerServiceWorker() { if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('./sw.js').catch(console.warn)); }

boot();
