/** Generate a versioned, strictly enumerated app-shell cache after CRA build. */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..'), build = path.join(root, 'build');
const manifest = JSON.parse(fs.readFileSync(path.join(build, 'asset-manifest.json'), 'utf8'));
const staticPaths = Object.values(manifest.files).filter(p => /^\/(static\/|logo-meow\.jpg$)/.test(p) && !p.endsWith('.map'));
staticPaths.push('/logo-meow.jpg', '/meowsurement/manifest.webmanifest', '/meowsurement/fonts/DejaVuSans.ttf', '/meowsurement/fonts/DejaVuSans-Bold.ttf');
const assets = [...new Set(staticPaths)].sort();
for (const item of assets) if (!fs.existsSync(path.join(build, item))) throw new Error('Missing offline asset: ' + item);
const hash = crypto.createHash('sha256');
for (const item of [...assets, '/index.html']) hash.update(item).update(fs.readFileSync(path.join(build, item)));
const version = hash.digest('hex').slice(0, 20);
const script = `'use strict';
const CACHE = 'optifit-shell-${version}';
const NAVIGATION = '/meowsurement/';
const ASSETS = ${JSON.stringify(assets)};
const ALLOWED = new Set(ASSETS);
self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    try {
      for (const url of [NAVIGATION, ...ASSETS]) {
        const response = await fetch(new Request(url, {cache:'reload', credentials:'omit', redirect:'error'}));
        if (!response.ok || response.type === 'opaque') throw new Error('Offline asset unavailable');
        const type = response.headers.get('content-type') || '';
        if (url.endsWith('.js') && !/javascript/.test(type)) throw new Error('Invalid script response');
        if (url.endsWith('.css') && !/text\\/css/.test(type)) throw new Error('Invalid style response');
        await cache.put(url, response);
      }
    } catch (error) { await caches.delete(CACHE); throw error; }
  })());
  // Updates wait for existing tabs to close; never force a reload with patient data open.
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) if (key.startsWith('optifit-shell-') && key !== CACHE) await caches.delete(key);
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin || url.search || url.pathname.startsWith('/api/')) return;
  if (event.request.mode === 'navigate' && (url.pathname === '/meowsurement/' || url.pathname.startsWith('/meowsurement/'))) {
    event.respondWith(caches.open(CACHE).then(async cache => (await cache.match(NAVIGATION)) || fetch(event.request))); return;
  }
  if (ALLOWED.has(url.pathname)) event.respondWith(caches.open(CACHE).then(async cache => (await cache.match(url.pathname)) || fetch(event.request)));
});
`;
fs.mkdirSync(path.join(build, 'meowsurement'), { recursive: true });
fs.writeFileSync(path.join(build, 'meowsurement/sw.js'), script);
console.log(`OptiFit offline shell: ${assets.length} static assets, version ${version}. Patient/API data excluded.`);
