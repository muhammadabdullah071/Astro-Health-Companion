// Minimal offline support: network-first for pages, cache-first for static assets and fonts.
const V = 'ahc-v1', PAGES = ['/', '/dashboard', '/alerts', '/assistant', '/status', '/manifest.webmanifest', '/icon.svg']
self.addEventListener('install', (e) => { e.waitUntil(caches.open(V).then((c) => c.addAll(PAGES)).then(() => self.skipWaiting())) })
self.addEventListener('activate', (e) => { e.waitUntil(caches.keys().then((k) => Promise.all(k.filter((x) => x !== V).map((x) => caches.delete(x)))).then(() => self.clients.claim())) })
self.addEventListener('fetch', (e) => {
  const r = e.request, u = new URL(r.url)
  if (r.method !== 'GET' || u.pathname.startsWith('/api/')) return
  const put = (res) => { if (res.ok) { const cp = res.clone(); caches.open(V).then((c) => c.put(r, cp)) } return res }
  if (r.mode === 'navigate') { e.respondWith(fetch(r).then(put).catch(() => caches.match(r).then((m) => m || caches.match('/')))); return }
  if (u.pathname.startsWith('/_next/static') || u.hostname.includes('fonts.g')) e.respondWith(caches.match(r).then((m) => m || fetch(r).then(put)))
})
