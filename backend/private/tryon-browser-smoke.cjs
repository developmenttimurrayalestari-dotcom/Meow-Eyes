const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const frontend = path.resolve(__dirname, '../../frontend');
(async () => {
  const sample = await fetch('https://storage.googleapis.com/mediapipe-assets/portrait.jpg');
  if (!sample.ok) throw new Error('Could not fetch official test portrait');
  const portrait = Buffer.from(await sample.arrayBuffer());
  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      if (url.pathname === '/') { res.setHeader('Content-Type', 'text/html'); res.end('<!doctype html><title>Local face tracking smoke test</title>'); return; }
      if (url.pathname === '/portrait.jpg') { res.setHeader('Content-Type', 'image/jpeg'); res.end(portrait); return; }
      let filename;
      if (url.pathname === '/vision.mjs') filename = path.join(frontend, 'node_modules/@mediapipe/tasks-vision/vision_bundle.mjs');
      else if (url.pathname === '/faceTracking.js') filename = path.join(frontend, 'src/lib/faceTracking.js');
      else if (/^\/try-on\/vision\/(face_landmarker\.task|wasm\/vision_wasm_(module_)?internal\.(js|wasm))$/.test(url.pathname)) filename = path.join(frontend, 'public', url.pathname);
      else if (url.pathname.startsWith('/static/')) filename = path.join(frontend, 'build', url.pathname);
      else if (url.pathname.startsWith('/products/')) filename = path.join(frontend, 'build/index.html');
      else { res.writeHead(404); res.end(); return; }
      res.setHeader('Content-Type', filename.endsWith('.wasm') ? 'application/wasm' : /\.(js|mjs)$/.test(filename) ? 'application/javascript' : filename.endsWith('.html') ? 'text/html' : filename.endsWith('.css') ? 'text/css' : 'application/octet-stream');
      res.end(await fs.readFile(filename));
    } catch { res.writeHead(500); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    const page = await browser.newPage();
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    const result = await page.evaluate(async () => {
      const { FaceLandmarker, FilesetResolver } = await import('/vision.mjs');
      const { faceFrameFit } = await import('/faceTracking.js');
      const files = await FilesetResolver.forVisionTasks('/try-on/vision/wasm');
      const detector = await FaceLandmarker.createFromOptions(files, { baseOptions: {
        modelAssetPath: '/try-on/vision/face_landmarker.task', delegate: 'CPU' }, runningMode: 'IMAGE', numFaces: 1 });
      try {
        const image = new Image(); image.src = '/portrait.jpg'; await image.decode();
        const detected = detector.detect(image);
        const fit = faceFrameFit(detected.faceLandmarks[0], { width: image.naturalWidth, height: image.naturalHeight }, { width: 800, height: 600 }, false);
        const blank = document.createElement('canvas'); blank.width = 640; blank.height = 480;
        const empty = detector.detect(blank);
        await detector.setOptions({ runningMode: 'VIDEO' });
        const video = detector.detectForVideo(image, 100);
        return { faces: detected.faceLandmarks.length, landmarks: detected.faceLandmarks[0]?.length,
          fit, blankFaces: empty.faceLandmarks.length, videoFaces: video.faceLandmarks.length };
      } finally { detector.close(); }
    });
    if (result.faces !== 1 || result.landmarks !== 478 || !result.fit || result.blankFaces !== 0 || result.videoFaces !== 1) throw new Error('Face detection smoke assertions failed: ' + JSON.stringify(result));
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const pathname = new URL(route.request().url()).pathname;
      let data = { categories: [], brands: [], lens_products: [], lens_indexes: [], picks: [], assets: [] };
      if (pathname === '/api/auth/me') data = { user: null };
      if (pathname === '/api/products/auto-frame') data = { product: { id: 'auto-frame', slug: 'auto-frame', name: 'Automatic Try-On Test', product_type: 'frame', price: 420000, main_image: '/portrait.jpg', variants: [{ id: 'variant', sku: 'TEST', stock: 10, color: 'Black' }] }, related: [], breadcrumb: [], reviews: [] };
      if (pathname.endsWith('/try-on')) data = { assets: [{ id: 'test-image', asset_type: 'image', scale: 1, source_url: 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 70"><g fill="none" stroke="black" stroke-width="6"><rect x="7" y="10" rx="20" width="85" height="50"/><rect x="128" y="10" rx="20" width="85" height="50"/><path d="M92 25Q110 10 128 25"/></g></svg>') }] };
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    });
    await page.goto(`http://127.0.0.1:${server.address().port}/products/auto-frame`);
    await page.getByTestId('open-virtual-try-on').click();
    await page.getByTestId('try-on-photo').setInputFiles({ name: 'official-test-portrait.jpg', mimeType: 'image/jpeg', buffer: portrait });
    await page.waitForFunction(() => document.querySelector('[data-testid="try-on-tracking-status"]')?.textContent.includes('Wajah terdeteksi'), { timeout: 30000 });
    if (await page.locator('input[type="range"]').count()) throw new Error('Manual fitting controls are still present');
    if (await page.getByTestId('try-on-tracked-frame').getAttribute('aria-hidden') !== 'false') throw new Error('Tracked frame is hidden');
    await page.screenshot({ path: path.join(__dirname, 'tryon-automatic-preview.png') });
    result.productionUiTracking = true;
    await page.evaluate(async () => {
      const image = new Image(); image.src = '/portrait.jpg'; await image.decode();
      const canvas = document.createElement('canvas'); canvas.width = 640; canvas.height = 480;
      const context = canvas.getContext('2d');
      window.syntheticFace = { angle: 0, blank: false };
      const draw = () => {
        context.setTransform(1, 0, 0, 1, 0, 0); context.fillStyle = '#fff'; context.fillRect(0, 0, 640, 480);
        if (window.syntheticFace.blank) return;
        context.translate(320, 240); context.rotate(window.syntheticFace.angle);
        context.drawImage(image, -192, -240, 384, 480);
      };
      draw(); window.syntheticTimer = setInterval(draw, 100);
      window.syntheticStream = canvas.captureStream(10);
      navigator.mediaDevices.getUserMedia = async () => window.syntheticStream;
    });
    await page.getByTestId('try-on-camera').click();
    await page.waitForFunction(() => document.querySelector('video')?.srcObject && document.querySelector('[data-testid="try-on-tracking-status"]')?.textContent.includes('Wajah terdeteksi'));
    const overlay = page.locator('img[alt="Pratinjau frame Automatic Try-On Test"]');
    const before = await overlay.getAttribute('style');
    await page.evaluate(() => { window.syntheticFace.angle = .18; });
    await page.waitForFunction(original => document.querySelector('img[alt="Pratinjau frame Automatic Try-On Test"]')?.getAttribute('style') !== original, before);
    result.liveVideoTracking = true;
    await page.evaluate(() => { window.syntheticFace.blank = true; });
    await page.waitForFunction(() => document.querySelector('[data-testid="try-on-tracked-frame"]')?.getAttribute('aria-hidden') === 'true');
    result.frameHiddenWhenFaceLost = true;
    await page.keyboard.press('Escape');
    result.streamStoppedOnClose = await page.evaluate(() => { clearInterval(window.syntheticTimer); return window.syntheticStream.getTracks().every(track => track.readyState === 'ended'); });
    if (!result.streamStoppedOnClose) throw new Error('Camera stream leaked after closing');
    result.browserErrors = errors;
    if (errors.length) throw new Error('Production browser errors: ' + JSON.stringify(errors));
    await page.keyboard.press('Escape');
    await fs.writeFile(path.join(__dirname, 'tryon-browser-smoke-report.json'), JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result, null, 2));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
