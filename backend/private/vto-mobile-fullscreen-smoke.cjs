const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const root = path.resolve(__dirname, '../../frontend/build');
const glasses = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 120"><rect width="240" height="120" fill="#fbe9e5"/><g fill="#4d6479" fill-opacity=".8" stroke="#14263e" stroke-width="6"><rect x="24" y="32" width="78" height="60" rx="28"/><rect x="138" y="32" width="78" height="60" rx="28"/><path d="M102 52Q120 38 138 52" fill="none"/></g></svg>';
const products = Array.from({ length: 12 }, (_, i) => ({ id: `frame-${i + 1}`, name: `Frame ${String(i + 1).padStart(2, '0')} Meow Eyes`, sku: `MEOW-FRAME-${i + 1}-LONG-PRODUCT-CODE`, description: 'Frame ringan dengan lensa nyaman untuk aktivitas sehari-hari.', price: 350000 + i * 10000, main_image: '/qa-frame.svg',
  variants: [{ id: `variant-${i + 1}`, sku: `FRAME-${i + 1}-BLACK-EDITION-LONG`, label: 'Hitam', stock: 5, reserved: 0 }, { id: `other-${i + 1}`, label: 'Cokelat', stock: 5, reserved: 0 }],
  try_on_assets: [{ id: `asset-${i + 1}`, asset_type: 'image', source_url: '/qa-frame.svg', scale: 1 }],
}));
(async () => {
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      if (pathname === '/qa-frame.svg') { res.setHeader('Content-Type', 'image/svg+xml'); res.end(glasses); return; }
      let file = path.resolve(root, '.' + decodeURIComponent(pathname));
      if (!file.startsWith(root + path.sep)) file = path.join(root, 'index.html');
      try { if (!(await fs.stat(file)).isFile()) file = path.join(root, 'index.html'); } catch { file = path.join(root, 'index.html'); }
      const types = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.wasm': 'application/wasm' };
      res.setHeader('Content-Type', types[path.extname(file)] || 'application/octet-stream'); res.end(await fs.readFile(file));
    } catch { res.writeHead(500); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser; const calls = [], errors = [], report = {};
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    page.on('pageerror', e => errors.push(e.message));
    await page.addInitScript(() => {
      window.cameraCalls = 0; window.stoppedTracks = 0;
      Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: async () => {
        window.cameraCalls++;
        const canvas = document.createElement('canvas'); canvas.width = 480; canvas.height = 640;
        const context = canvas.getContext('2d');
        const gradient = context.createLinearGradient(0, 0, 480, 640); gradient.addColorStop(0, '#d6e5eb'); gradient.addColorStop(1, '#8daeba');
        const draw = () => {
          context.fillStyle = gradient; context.fillRect(0, 0, 480, 640);
          context.fillStyle = '#466273'; context.beginPath(); context.ellipse(240, 640, 170, 190, 0, 0, Math.PI * 2); context.fill();
          context.fillStyle = '#e9bfa1'; context.beginPath(); context.ellipse(240, 285, 90, 120, 0, 0, Math.PI * 2); context.fill();
          context.fillStyle = '#283742'; context.beginPath(); context.ellipse(240, 196, 90, 50, 0, Math.PI, Math.PI * 2); context.fill();
          for (const x of [206, 274]) { context.beginPath(); context.ellipse(x, 275, 7, 5, 0, 0, Math.PI * 2); context.fill(); }
          context.strokeStyle = '#9e6755'; context.lineWidth = 3; context.beginPath(); context.arc(240, 330, 28, .2, Math.PI - .2); context.stroke();
        };
        draw(); window.qaCameraTimer = setInterval(draw, 100);
        const stream = canvas.captureStream(10);
        stream.getTracks().forEach(track => { const original = track.stop.bind(track); track.stop = () => { window.stoppedTracks++; clearInterval(window.qaCameraTimer); original(); }; });
        return stream;
      } } });
    });
    await page.route('**/api/**', async route => {
      const request = route.request(), url = new URL(request.url()), endpoint = url.pathname.replace(/^\/api/, '');
      let data = { ok: true, pages: [], categories: [], brands: [], products: [], items: [], count: 0, total: 0, assets: [] };
      if (endpoint === '/auth/me') data = { user: { user_id: 'qa-customer', name: 'QA Customer', email: 'qa@example.com', role: 'customer' } };
      if (endpoint === '/settings/whatsapp') data = { enabled: true, phone_number: '6281234567890' };
      if (endpoint === '/try-on/catalog') data = { products: products.filter(p => p.name.toLowerCase().includes((url.searchParams.get('q') || '').toLowerCase())), next_offset: null };
      if (request.method() === 'POST') calls.push({ endpoint, body: request.postDataJSON() });
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(data) });
    });
    const origin = `http://127.0.0.1:${server.address().port}`;
    await page.goto(origin + '/virtual-try-on');
    await page.getByTestId('try-on-camera').click();
    await page.waitForFunction(() => !!document.querySelector('video')?.srcObject);
    const checkFullscreen = async (width, height) => {
      const measured = await page.getByTestId('try-on-stage').evaluate(stage => {
        const rect = stage.getBoundingClientRect(), catalog = document.querySelector('.vto-catalog').getBoundingClientRect();
        const card = document.querySelector('.vto-product-card').getBoundingClientRect();
        return { x: rect.x, y: rect.y, w: rect.width, h: rect.height, fit: getComputedStyle(stage.querySelector('video')).objectFit, catalog: { x: catalog.x, right: catalog.right, y: catalog.y, bottom: catalog.bottom }, card: { x: card.x, right: card.right, y: card.y, bottom: card.bottom }, overflow: document.documentElement.scrollWidth > innerWidth };
      });
      assert.equal(measured.x, 0); assert.equal(measured.y, 0); assert.equal(measured.w, width); assert.equal(measured.h, height);
      assert.equal(measured.fit, 'cover'); assert(!measured.overflow);
      assert(measured.catalog.x > 0 && measured.catalog.right < width && measured.catalog.bottom < height);
      assert(measured.card.x >= 10 && measured.card.right <= width - 10 && measured.card.bottom <= height);
      assert(measured.card.right - measured.card.x <= 260 && measured.card.right >= width - 16);
      assert(!(await page.getByTestId('main-header').isVisible())); assert(!(await page.getByTestId('bottom-nav').isVisible())); assert(!(await page.getByTestId('floating-whatsapp').isVisible()));
      return measured;
    };
    report.portrait = await checkFullscreen(390, 844);
    await page.getByRole('button', { name: 'Frame 02 Meow Eyes', exact: false }).click();
    assert.equal(await page.evaluate(() => window.cameraCalls), 1); assert.equal(await page.evaluate(() => window.stoppedTracks), 0);
    await Promise.all([
      page.waitForResponse(response => new URL(response.url()).pathname.endsWith('/api/cart') && response.request().method() === 'POST'),
      page.getByRole('button', { name: 'Beli', exact: true }).click(),
    ]);
    assert.deepEqual(calls.find(call => call.endpoint === '/cart').body, { product_id: 'frame-2', variant_id: 'variant-2', quantity: 1 });
    await page.screenshot({ path: path.join(__dirname, 'vto-mobile-fullscreen-portrait.png') });
    await page.getByRole('button', { name: 'Sembunyikan detail produk' }).click();
    assert(!(await page.getByRole('region', { name: 'Detail produk terpilih' }).isVisible()));
    const reveal = page.getByRole('button', { name: 'Tampilkan detail produk' });
    assert(await reveal.isVisible());
    await page.screenshot({ path: path.join(__dirname, 'vto-product-details-hidden-mobile.png') });
    await page.getByRole('button', { name: 'Frame 03 Meow Eyes', exact: false }).click();
    assert(!(await page.getByRole('region', { name: 'Detail produk terpilih' }).isVisible()));
    await reveal.click();
    assert(await page.getByRole('region', { name: 'Detail produk terpilih' }).isVisible());
    assert.equal(await page.evaluate(() => window.cameraCalls), 1);
    assert.equal(await page.evaluate(() => window.stoppedTracks), 0);
    report.details_toggle_preserves_camera_and_hidden_preference = true;
    await page.getByRole('button', { name: 'Panduan kamera', exact: true }).click();
    await page.getByRole('region', { name: 'Panduan kamera' }).waitFor();
    await page.getByRole('button', { name: 'Tutup panduan' }).click();
    await page.getByRole('button', { name: 'Cari frame', exact: true }).click();
    await Promise.all([
      page.waitForResponse(response => response.url().includes('/try-on/catalog') && new URL(response.url()).searchParams.get('q') === 'Frame 03'),
      page.getByLabel('Cari frame berdasarkan nama atau kode').fill('Frame 03'),
    ]);
    await page.getByRole('button', { name: 'Frame 03 Meow Eyes', exact: false }).click();
    await page.setViewportSize({ width: 844, height: 390 });
    await page.waitForTimeout(200); report.landscape = await checkFullscreen(844, 390);
    await page.screenshot({ path: path.join(__dirname, 'vto-mobile-fullscreen-landscape.png') });
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.waitForFunction(() => !document.documentElement.classList.contains('vto-mobile-active'));
    assert(await page.getByTestId('main-header').isVisible());
    assert.equal(await page.locator('video').evaluate(video => getComputedStyle(video).objectFit), 'contain');
    const desktopDetails = await page.getByTestId('try-on-stage').evaluate(stage => {
      const preview = stage.getBoundingClientRect(), card = document.querySelector('.vto-product-card').getBoundingClientRect();
      return { width: card.width, rightInset: preview.right - card.right, bottomInset: preview.bottom - card.bottom, cameraWidth: preview.width };
    });
    assert.equal(desktopDetails.width, 300); assert.equal(desktopDetails.rightInset, 12); assert.equal(desktopDetails.bottomInset, 12);
    assert(desktopDetails.width < desktopDetails.cameraWidth / 2);
    report.desktop_details = desktopDetails;
    await page.screenshot({ path: path.join(__dirname, 'vto-product-details-desktop.png') });
    await page.getByRole('button', { name: 'Sembunyikan detail produk' }).click();
    assert(!(await page.getByRole('region', { name: 'Detail produk terpilih' }).isVisible()));
    await page.getByRole('button', { name: 'Tampilkan detail produk' }).click();
    assert.equal(await page.evaluate(() => window.cameraCalls), 1); assert.equal(await page.evaluate(() => window.stoppedTracks), 0);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('link', { name: 'Kembali ke toko' }).click();
    await page.waitForFunction(() => !document.documentElement.classList.contains('vto-mobile-active'));
    assert(await page.getByTestId('main-header').isVisible()); assert(await page.getByTestId('bottom-nav').isVisible()); assert(await page.getByTestId('floating-whatsapp').isVisible());
    assert.equal(await page.evaluate(() => window.stoppedTracks), 1);
    assert.deepEqual(errors, []);
    report.stream_preserved = true; report.cart_variant_correct = true; report.search_and_tips = true; report.desktop_and_exit_restore_layout = true; report.page_errors = errors; report.ok = true;
    await fs.writeFile(path.join(__dirname, 'vto-mobile-fullscreen-report.json'), JSON.stringify(report, null, 2)); console.log(JSON.stringify(report));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
