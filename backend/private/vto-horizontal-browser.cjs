const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const root = path.resolve(__dirname, '../../frontend/build');
const products = Array.from({ length: 18 }, (_, i) => ({
  id: `frame-${i}`, name: `Frame QA ${i + 1}`, sku: `FRAME-${i + 1}`, product_type: 'frame',
  description: 'Frame untuk mencoba tampilan Virtual Try-On', price: 300000 + i * 10000, main_image: '/qa-frame.svg',
  variants: [{ id: `variant-${i}`, sku: `FRAME-${i + 1}-BLK`, stock: 5, reserved: 0 }],
  try_on_assets: [{ id: `asset-${i}`, product_id: `frame-${i}`, asset_type: 'image', source_url: '/qa-frame.svg', scale: 1 }],
}));
(async () => {
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      if (pathname === '/qa-frame.svg') {
        res.setHeader('Content-Type', 'image/svg+xml');
        res.end('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 180"><rect width="240" height="180" fill="#fbf7f0"/><g fill="#d8ecec" stroke="#11223a" stroke-width="4"><ellipse cx="65" cy="90" rx="40" ry="32"/><ellipse cx="175" cy="90" rx="40" ry="32"/><path d="M105 83Q120 75 135 83M25 84L10 70M215 84L230 70" fill="none"/></g></svg>');
        return;
      }
      let file = path.resolve(root, '.' + pathname);
      if (!file.startsWith(root + path.sep)) file = path.join(root, 'index.html');
      try { if (!(await fs.stat(file)).isFile()) file = path.join(root, 'index.html'); }
      catch { file = path.join(root, 'index.html'); }
      res.setHeader('Content-Type', ({ '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.jpg': 'image/jpeg', '.png': 'image/png', '.wasm': 'application/wasm' })[path.extname(file)] || 'application/octet-stream');
      res.end(await fs.readFile(file));
    } catch { res.writeHead(500); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  const errors = [], writes = [], report = {};
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    const page = await browser.newPage({ viewport: { width: 1280, height: 1000 }, hasTouch: true, serviceWorkers: 'block' });
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => {
      window.qaCameraCalls = 0; window.qaStopped = 0;
      Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: async () => {
        window.qaCameraCalls++;
        const canvas = document.createElement('canvas'); canvas.width = 640; canvas.height = 480;
        canvas.getContext('2d').fillRect(0, 0, 640, 480);
        const stream = canvas.captureStream(10);
        stream.getTracks().forEach(track => { const stop = track.stop.bind(track); track.stop = () => { window.qaStopped++; stop(); }; });
        return stream;
      } } });
    });
    await page.route('**/api/**', async route => {
      const req = route.request(), url = new URL(req.url()), endpoint = url.pathname.replace(/^\/api/, '');
      if (req.method() !== 'GET') writes.push(endpoint);
      let data = { pages: [], items: [], count: 0 };
      if (endpoint === '/auth/me') data = { user: { user_id: 'qa', name: 'Customer QA', role: 'customer' } };
      if (endpoint === '/settings/whatsapp') data = { enabled: false };
      if (endpoint === '/try-on/catalog') {
        const query = (url.searchParams.get('q') || '').toLowerCase();
        data = { products: products.filter(product => product.name.toLowerCase().includes(query)), next_offset: null };
      }
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(data) });
    });
    await page.goto(`http://127.0.0.1:${server.address().port}/virtual-try-on`);
    await page.getByTestId('try-on-stage').waitFor();
    for (const width of [768, 1280, 1920, 2560]) {
      await page.setViewportSize({ width, height: 1000 });
      const bounds = await page.evaluate(() => {
        const rect = selector => { const r = document.querySelector(selector).getBoundingClientRect(); return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width }; };
        const list = document.querySelector('.vto-product-list');
        return { viewport: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth,
          stage: rect('[data-testid="try-on-stage"]'), controls: rect('.vto-camera-controls'), catalog: rect('.vto-catalog'),
          first: rect('.vto-frame-option'), second: rect('.vto-frame-option:nth-child(2)'),
          direction: getComputedStyle(list).flexDirection, overflows: list.scrollWidth > list.clientWidth,
          nestedInStage: !!document.querySelector('[data-testid="try-on-stage"] .vto-catalog') };
      });
      assert(Math.abs(bounds.stage.left) < 1 && Math.abs(bounds.stage.width - bounds.viewport) < 1);
      assert(bounds.controls.bottom <= bounds.stage.top, 'Camera/photo controls must be above the canvas');
      assert(bounds.catalog.top >= bounds.stage.bottom, 'Frame catalog must be below the canvas');
      assert.equal(bounds.nestedInStage, false);
      assert.equal(bounds.direction, 'row'); assert.equal(bounds.overflows, true);
      assert(Math.abs(bounds.first.top - bounds.second.top) < 1 && bounds.second.left > bounds.first.left);
      assert(bounds.scroll <= bounds.viewport + 1);
      report['desktop' + width] = true;
    }
    await page.setViewportSize({ width: 1280, height: 1000 });
    await page.getByRole('button', { name: 'Geser pilihan frame ke kanan' }).click();
    await page.waitForFunction(() => document.querySelector('.vto-product-list').scrollLeft > 0);
    report.horizontalArrowWorks = true;
    await page.getByTestId('try-on-camera').click();
    await page.waitForFunction(() => !!document.querySelector('video')?.srcObject);
    await page.evaluate(() => { window.qaVideo = document.querySelector('video'); });
    await page.locator('.vto-frame-option').nth(2).click();
    assert(await page.evaluate(() => window.qaVideo === document.querySelector('video')));
    assert.equal(await page.evaluate(() => window.qaCameraCalls), 1);
    assert.equal(await page.evaluate(() => window.qaStopped), 0);
    report.cameraPreserved = true;
    await page.getByRole('button', { name: 'Hentikan Kamera' }).click();
    await page.getByTestId('try-on-camera').waitFor();
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(__dirname, 'vto-horizontal-desktop.png'), fullPage: true });
    await page.getByRole('textbox', { name: 'Cari frame berdasarkan nama atau kode' }).fill('Frame QA 18');
    await page.waitForFunction(() => document.querySelectorAll('.vto-frame-option').length === 1);
    assert.ok((await page.locator('.vto-frame-option').textContent()).includes('Frame QA 18'));
    report.searchWorks = true;
    await page.getByRole('textbox', { name: 'Cari frame berdasarkan nama atau kode' }).fill('');
    await page.waitForFunction(() => document.querySelectorAll('.vto-frame-option').length === 18);
    for (const size of [{ width: 390, height: 844 }, { width: 844, height: 390 }]) {
      await page.setViewportSize(size);
      const mobile = await page.getByTestId('try-on-stage').boundingBox();
      const catalog = await page.locator('.vto-catalog').boundingBox();
      assert(Math.abs(mobile.x) < 1 && Math.abs(mobile.width - size.width) < 1 && Math.abs(mobile.height - size.height) < 1);
      assert(catalog.x >= 0 && catalog.x + catalog.width <= mobile.width + 1 && catalog.y < mobile.height);
      assert.equal(await page.locator('.vto-product-list').evaluate(el => getComputedStyle(el).flexDirection), 'column');
      assert.equal(await page.getByRole('button', { name: 'Geser pilihan frame ke kanan' }).isVisible(), false);
      await page.screenshot({ path: path.join(__dirname, size.width > 767 ? 'vto-horizontal-mobile-landscape.png' : 'vto-horizontal-mobile.png') });
    }
    report.mobileFullscreenAndFloatingCatalog = true;
    assert.deepEqual(writes, []); assert.deepEqual(errors, []);
    report.errors = errors; report.api = 'mocked; no backend or store writes';
    await fs.writeFile(path.join(__dirname, 'vto-horizontal-browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
