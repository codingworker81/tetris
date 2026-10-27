/* Tetris PWA 서비스워커 — 오프라인 캐시 (앱처럼 인터넷 없이도 실행) */
const CACHE = 'tetris-v1.1.8';
const ASSETS = [
  './',
  './index.html',
  './style.css',
  './tetris.js',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())
  );
});

// 코드 자산(HTML/CSS/JS)은 network-first: 온라인이면 항상 최신, 오프라인이면 캐시 폴백.
// 그 외(아이콘 등)는 cache-first(빠름).
function isCodeAsset(req) {
  if (req.mode === 'navigate') return true;
  return /\.(?:html|css|js)(?:\?|$)/.test(new URL(req.url).pathname + (new URL(req.url).search || ''));
}

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  if (isCodeAsset(e.request)) {
    e.respondWith(
      fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match(e.request).then((cached) => cached || caches.match('./index.html')))
    );
    return;
  }
  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
      return res;
    }).catch(() => cached))
  );
});
