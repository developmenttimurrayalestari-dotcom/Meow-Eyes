const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const root = path.resolve(__dirname, '../../frontend/build');
const rules = { cooldown_seconds: 86400, expiry_days: 30, max_duration_seconds: 10, max_points: 0, points_per_unit: 1 };
const games = [['space-war', 'Meow Space War', 'space_war'], ['matching', 'Match Meow Pairs', 'matching'], ['slide-puzzle', 'Meow Puzzle Geser', 'slide_puzzle'], ['roulette', 'Roulette', 'roulette']].map(([key, name, engine]) => ({ id: key, key, name, is_active: true, description: '', rule: { ...rules, game_key: key, engine } }));
const products = ['A', 'B'].map((key, i) => ({ id: key, slug: key, name: `Frame ${key}`, description: 'Frame pilihan Meow Eyes', main_image: '/logo-meow.jpg', sku: key, price: 400000 + i * 10000, variants: [{ id: `v-${key}`, sku: `SKU-${key}`, stock: 3, reserved: 0, color: 'Black', price_override: 500000 + i * 10000 }], try_on_assets: [{ id: `asset-${key}`, product_id: key, asset_type: 'image', source_url: '/games/space-war/meow-pilot.png', scale: 1 }] }));
(async () => {
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      let file = path.resolve(root, '.' + decodeURIComponent(pathname));
      if (!file.startsWith(root + path.sep)) file = path.join(root, 'index.html');
      try { if (!(await fs.stat(file)).isFile()) file = path.join(root, 'index.html'); } catch { file = path.join(root, 'index.html'); }
      const types = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.wasm': 'application/wasm' };
      res.setHeader('Content-Type', types[path.extname(file)] || 'application/octet-stream'); res.end(await fs.readFile(file));
    } catch { res.writeHead(500); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser; const report = {}, calls = [], errors = [];
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    page.on('pageerror', e => errors.push(e.message));
    await page.addInitScript(() => {
      window.cameraCalls = 0; window.stoppedTracks = 0;
      Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: async () => {
        window.cameraCalls++; const canvas = document.createElement('canvas'); canvas.width = 640; canvas.height = 480; const ctx = canvas.getContext('2d'); ctx.fillStyle = '#ddd'; ctx.fillRect(0, 0, 640, 480);
        const stream = canvas.captureStream(10); stream.getTracks().forEach(track => { const original = track.stop.bind(track); track.stop = () => { window.stoppedTracks++; original(); }; }); return stream;
      } } });
    });
    await page.route('**/api/**', async route => {
      const req = route.request(), url = new URL(req.url()), endpoint = url.pathname.replace(/^\/api/, '');
      const body = req.method() === 'GET' ? null : req.postDataJSON(); if (body) calls.push({ endpoint, body });
      let data = { ok: true, pages: [], categories: [], brands: [], assets: [], items: [], count: 0 };
      if (endpoint === '/auth/me') data = { user: { user_id: 'customer', name: 'QA Admin', email: 'qa@example.com', role: 'admin', points_balance: 100 } };
      if (endpoint === '/settings/whatsapp') data = { enabled: false };
      if (endpoint === '/games' || endpoint === '/admin/games') data = { games };
      if (endpoint === '/games/puzzle-levels') data = { levels: [] };
      if (endpoint === '/games/space-war/start') data = { id: 'round-1', seed: 1, started_at: new Date().toISOString(), snapshot: { ...rules, engine: 'space_war' } };
      if (endpoint === '/game-sessions/round-1/finish') data = { ok: true, score: 0, points_awarded: 0 };
      if (endpoint === '/try-on/catalog') data = { products, next_offset: null };
      if (endpoint === '/points/logs' || endpoint === '/admin/points/customers/customer') data = { balance: 100, value: 37500, lots: [{ id: 'lot', remaining: 100, rate_snapshot: 375, source: 'earn_game' }], logs: [] };
      if (endpoint === '/admin/points/settings') data = { id: 'global', rate: body?.rate || 100, version: body ? 2 : 1, cashback_valuation: 'locked' };
      if (endpoint === '/admin/points/customers') data = { customers: [{ user_id: 'customer', name: 'Customer QA', email: 'qa@example.com', earned: 150, spent: 30, expired: 20, balance: 100 }], next_offset: null };
      if (endpoint === '/admin/returns') data = { cases: [], next_offset: null };
      if (endpoint === '/admin/returns/policy') data = { window_days: 7, return_days: 7, recipient: '', phone: '', address: '', notes: '' };
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(data) });
    });
    const origin = `http://127.0.0.1:${server.address().port}`;
    await page.goto(origin + '/virtual-try-on'); await page.getByTestId('try-on-camera').click();
    await page.waitForFunction(() => !!document.querySelector('video')?.srcObject);
    await page.getByRole('button', { name: /Frame B/ }).click();
    await page.getByRole('button', { name: 'Beli', exact: true }).click();
    assert.equal(await page.evaluate(() => window.cameraCalls), 1); assert.equal(await page.evaluate(() => window.stoppedTracks), 0);
    assert.deepEqual(calls.find(c => c.endpoint === '/cart').body, { product_id: 'B', variant_id: 'v-B', quantity: 1 });
    await page.screenshot({ path: path.join(__dirname, 'loyalty-vto-desktop.png') }); report.vtoCameraPreserved = true; report.vtoCorrectCartVariant = true;
    await page.goto(origin + '/admin/games/space-war'); const cooldown = page.getByLabel('Jeda bermain (jam)'); await cooldown.fill('3'); await page.getByRole('button', { name: 'Simpan Konfigurasi' }).click();
    await page.getByRole('status').filter({ hasText: 'Konfigurasi tersimpan' }).waitFor();
    assert.equal(calls.find(c => c.endpoint === '/admin/games/space-war').body.cooldown_seconds, 10800); report.gameAdminCooldown = true;
    assert.equal(await page.locator('a[href="/admin/games/roulette"]').count(), 1); report.dynamicGamesSubmenus = true;
    await page.goto(origin + '/points'); await page.getByText('Nilai potongan Rp 37.500').waitFor(); report.walletUsesFrozenValue = true;
    await page.setViewportSize({ width: 390, height: 844 }); await page.goto(origin + '/games/space-war'); await page.getByRole('button', { name: 'Mulai Bermain' }).click();
    await page.getByTestId('space-war-stage').waitFor(); await page.getByRole('button', { name: 'Atas', exact: true }).dispatchEvent('pointerdown', { pointerId: 1 });
    await page.waitForTimeout(400); await page.getByRole('button', { name: 'Atas', exact: true }).dispatchEvent('pointerup', { pointerId: 1 });
    await page.screenshot({ path: path.join(__dirname, 'loyalty-space-war-mobile.png') });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1));
    await page.getByText('Ronde selesai!', { exact: true }).waitFor({ timeout: 20000 });
    const transcript = calls.find(c => c.endpoint.includes('/finish')).body; assert.equal(transcript.ticks, 300); assert(!Object.hasOwn(transcript, 'score')); report.spaceWarRealTimeRound = true; report.mobileControls = true;
    assert.deepEqual(errors, []); report.browserErrors = errors; report.ok = true;
    await fs.writeFile(path.join(__dirname, 'loyalty-browser-report.json'), JSON.stringify(report, null, 2)); console.log(JSON.stringify(report));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
