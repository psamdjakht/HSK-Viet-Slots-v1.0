export function speakChinese(text, enabled = true, rate = 0.88) {
  if (!enabled || !text || !('speechSynthesis' in window)) return false;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'zh-CN';
  utterance.rate = rate;
  const voices = window.speechSynthesis.getVoices();
  const voice = voices.find(v => /^zh(-|_)/i.test(v.lang));
  if (voice) utterance.voice = voice;
  window.speechSynthesis.speak(utterance);
  return true;
}
