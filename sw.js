const CACHE_VERSION = 'hsk-viet-slots-v5.0.0';
const CORE = [
  './','./index.html','./css/app.css','./js/app.js','./js/config.js',
  './js/modules/storage.js','./js/modules/data.js','./js/modules/srs.js','./js/modules/quiz.js',
  './js/modules/audio.js','./js/modules/ui.js','./js/modules/activities.js','./js/modules/weak.js',
  './js/modules/plan.js','./js/modules/stats.js','./js/modules/exam.js','./js/modules/sync.js',
  './js/modules/content.js','./js/modules/admin.js',
  './manifest.webmanifest','./data/meta.json','./data/examples.json',
  './data/hsk1-quality.json','./data/hsk1-grammar.json','./data/hsk2-quality.json','./data/hsk2-grammar.json',
  './data/hsk3-quality.json','./data/hsk3-grammar.json','./data/hsk4-quality.json','./data/hsk4-grammar.json',
  './data/hsk5-quality.json','./data/hsk5-grammar.json','./data/hsk6-quality.json','./data/hsk6-grammar.json',
  './data/hsk7-quality.json','./data/hsk7-grammar.json',
  './assets/icons/icon-192.png','./assets/icons/icon-512.png'
];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_VERSION).then(cache => cache.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_VERSION).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (event.request.mode === 'navigate' || url.pathname.endsWith('/js/config.js')) {
    event.respondWith(caches.open(CACHE_VERSION).then(async cache => {
      try {
        const response = await fetch(event.request, { cache: 'no-store' });
        if (response.ok) await cache.put(event.request, response.clone());
        return response;
      } catch {
        return (await cache.match(event.request)) || (await cache.match('./index.html'));
      }
    }));
    return;
  }
  if (url.pathname.includes('/data/levels/')) {
    event.respondWith(caches.open(CACHE_VERSION).then(async cache => {
      const cached = await cache.match(event.request);
      if (cached) return cached;
      const response = await fetch(event.request);
      if (response.ok) await cache.put(event.request, response.clone());
      return response;
    }));
    return;
  }
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
    if (response.ok) caches.open(CACHE_VERSION).then(cache => cache.put(event.request, response.clone()));
    return response;
  }).catch(() => caches.match('./index.html'))));
});
