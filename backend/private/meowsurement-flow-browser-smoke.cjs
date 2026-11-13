const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const build = path.resolve(__dirname, '../../frontend/build');
const profile = { user_id: 'qa-customer', name: 'Customer QA', phone: '081234567890', birth_date: '1995-01-01', version: 4,
  prescription: { date: '2026-01-01', od: { sph: 0, cyl: 0 }, os: { sph: -1, cyl: 0 } } };
const spec = { a: 52, b: 40, dbl: 18, ed: null, enabled: true, version: 3 };
const frame = { id: 'p1', name: 'Frame QA', specification_version: 3, frame_specification: spec,
  variants: [{ id: 'v1', color: 'Hitam', size: '52', effective_specification: spec }] };
(async () => {
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      const filename = path.resolve(build, '.' + (pathname.startsWith('/static/') || pathname.endsWith('.jpg') ? pathname : '/index.html'));
      if (!filename.startsWith(build + path.sep)) throw new Error('Invalid path');
      res.setHeader('Content-Type', filename.endsWith('.js') ? 'application/javascript' : filename.endsWith('.css') ? 'text/css' : filename.endsWith('.jpg') ? 'image/jpeg' : 'text/html');
      res.end(await fs.readFile(filename));
    } catch { res.writeHead(404); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: 'block' });
    await context.addInitScript(() => {
      localStorage.setItem('meow_token', 'qa-only');
      Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: {
        enumerateDevices: async () => [], getUserMedia: async () => {
          const canvas = document.createElement('canvas'); canvas.width = 640; canvas.height = 480;
          const ctx = canvas.getContext('2d');
          const draw = () => { ctx.fillStyle = '#ddd'; ctx.fillRect(0, 0, 640, 480); ctx.fillStyle = '#234';
            for (let x = 0; x < 640; x += 20) for (let y = 0; y < 480; y += 20) ctx.fillRect(x, y, 8, 8);
            ctx.fillStyle = '#f54'; ctx.fillRect((Date.now() / 10) % 500, 200, 80, 80); };
          draw(); setInterval(draw, 30); return canvas.captureStream(30);
        },
      } });
    });
    let detail, counter = 0; const payloads = []; const errors = [];
    const page = await context.newPage(); page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const req = route.request(), pathname = new URL(req.url()).pathname; let data = {};
      if (pathname.endsWith('/bootstrap')) data = { ready: true, user: { user_id: profile.user_id, name: profile.name, role: 'customer' }, profile };
      else if (pathname.endsWith('/auth/me')) data = { user: { user_id: profile.user_id, name: profile.name, role: 'customer' } };
      else if (pathname.endsWith('/frames')) data = { products: [frame], page: 1, total: 1, total_pages: 1 };
      else if (pathname.endsWith('/sessions') && req.method() === 'GET') data = { sessions: [], page: 1, total_pages: 1 };
      else if (pathname.endsWith('/sessions') && req.method() === 'POST') {
        const input = req.postDataJSON(); payloads.push(input); counter += 1;
        const id = 'ms_qa_' + counter, revisionId = 'mr_qa_' + counter;
        const geometry = input.manual_frame || spec;
        const sessionData = { frame: { ...geometry, model: input.manual_frame ? 'Frame ukuran manual' : frame.name, sourceScope: input.manual_frame ? 'manual' : 'product', symmetric: false, pdReference: 'facial_midline' },
          prescription: profile.prescription, requiredParameters: input.required_parameters, workingDistanceCm: input.working_distance_cm,
          examinationDate: input.examination_date, mode: input.mode, captures: [], results: {}, preparation: [], consents: {}, notes: '' };
        detail = { session: { id, createdBy: profile.user_id, patientId: profile.user_id, currentRevisionId: revisionId, status: 'draft', examinationDate: input.examination_date },
          revisions: [{ id: revisionId, sessionId: id, data: sessionData }], patient: { id: profile.user_id, fullName: profile.name }, photos: [], reviews: [] };
        data = detail;
      } else if (pathname.endsWith('/revisions') && req.method() === 'POST') {
        detail.revisions[0].data = req.postDataJSON().data; data = {};
      } else if (pathname.includes('/sessions/ms_qa_')) data = detail;
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    });
    const origin = `http://127.0.0.1:${server.address().port}`;
    await page.goto(origin + '/meowsurement/');
    await page.getByTestId('measurement-dashboard').waitFor();
    assert.equal(await page.locator('[data-testid^="measurement-card-"]').count(), 5);
    assert.equal(await page.locator('form').count(), 0);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: path.join(__dirname, 'meowsurement-menu-mobile.png'), fullPage: true });
    await page.getByTestId('measurement-card-near_pd').click();
    await page.getByLabel('Lebar lensa (A)', { exact: true }).fill('52');
    await page.getByLabel('Tinggi lensa (B)', { exact: true }).fill('40');
    await page.getByLabel('Jarak antar lensa (DBL)', { exact: true }).fill('18');
    await page.getByLabel('Jarak membaca', { exact: true }).fill('35');
    await page.screenshot({ path: path.join(__dirname, 'meowsurement-manual-mobile.png'), fullPage: true });
    await page.getByRole('button', { name: 'Mulai pengukuran', exact: true }).click();
    await page.getByTestId('customer-preparation').waitFor();
    const prepGuide = page.getByTestId('customer-preparation').getByTestId('measurement-illustration-guide');
    await prepGuide.getByTestId('guide-drawing-near_pd').waitFor();
    await prepGuide.getByRole('button', { name: /Tandai titik/ }).click();
    assert.equal(await prepGuide.locator('[data-illustration-point]').count(), 6);
    assert.equal(await prepGuide.locator('[data-guide-point="markerTL"]').count(), 0);
    await prepGuide.locator('[data-guide-point="rightPupil"]').click();
    assert.ok((await prepGuide.locator('.of-illustration-detail').textContent()).includes('bukan pantulan lampu'));
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await prepGuide.screenshot({ path: path.join(__dirname, 'meowsurement-guide-pd-mobile.png'), style: '.of-customer-header { visibility: hidden; }' });
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.getByRole('button', { name: 'Gunakan tema gelap' }).click();
    await prepGuide.screenshot({ path: path.join(__dirname, 'meowsurement-guide-pd-desktop-dark.png'), style: '.of-customer-header { visibility: hidden; }' });
    await page.getByRole('button', { name: 'Gunakan tema terang' }).click();
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(payloads[0].manual_frame.ed, null); assert.equal(payloads[0].product_id, undefined);
    assert.deepEqual(payloads[0].required_parameters, ['near_pd']);
    const checks = page.getByTestId('customer-preparation').locator('input[type=checkbox]');
    await checks.nth(0).check(); await checks.nth(1).check();
    await page.getByRole('button', { name: 'Lanjut ke kamera', exact: true }).click();
    await page.getByRole('button', { name: 'Buka kamera', exact: true }).click();
    await page.getByTestId('optifit-camera-start').click();
    await page.getByTestId('optifit-camera-capture').waitFor();
    const station = page.getByTestId('optifit-camera-station');
    const preview = await station.locator(':scope > div').nth(0).boundingBox();
    const controls = await page.getByTestId('optifit-camera-controls').boundingBox();
    assert.ok(Math.abs(controls.y - preview.y - preview.height) <= 1, 'Capture must directly follow preview');
    assert.ok(controls.height >= 48);
    await station.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(__dirname, 'meowsurement-camera-mobile.png'), fullPage: true });
    await page.getByTestId('optifit-camera-capture').click();
    await page.getByRole('button', { name: 'Tandai titik & acuan frame', exact: true }).first().waitFor();
    assert.equal(detail.revisions[0].data.captures[0].calibrationSpec.method, 'frame');
    assert.equal(detail.revisions[0].data.captures[0].calibrationSpec.lengthMm, 52);
    assert.equal(detail.revisions[0].data.captures[0].device.mainCameraVerifiedByOperator, false);
    await page.getByRole('button', { name: 'Tandai titik & acuan frame', exact: true }).first().click();
    await page.getByTestId('customer-photo-scale').waitFor();
    const annotationGuide = page.locator('.of-modal').getByTestId('measurement-illustration-guide');
    await annotationGuide.locator('summary').click();
    assert.equal(await annotationGuide.locator('[data-guide-point="rightPupil"]').count(), 1);
    assert.deepEqual(detail.revisions[0].data.captures[0].points, {});
    assert.equal(await page.getByTestId('customer-photo-scale').locator('select').count(), 0);
    assert.equal(await page.getByTestId('customer-photo-scale').locator('input[type=number]').count(), 0);
    assert.ok((await page.getByTestId('customer-frame-reference').textContent()).includes('52 mm'));
    assert.equal(await page.locator('[data-testid="landmark-point-markerTL"]').count(), 0);
    assert.equal(await annotationGuide.locator('[data-guide-point="markerTL"]').count(), 0);
    assert.equal(await annotationGuide.locator('[data-guide-point="scaleStart"]').count(), 1);
    assert.equal(await page.getByRole('heading', { name: 'Pemeriksaan operator' }).count(), 0);
    assert.equal(await page.getByLabel('Head pitch terukur').count(), 0);
    await page.getByRole('button', { name: 'Batal', exact: true }).click();
    await page.getByRole('button', { name: 'Pengukuran baru', exact: true }).click();
    await page.getByTestId('measurement-card-vertex').click();
    assert.equal(await page.getByLabel('Jarak membaca', { exact: true }).count(), 0);
    await page.getByRole('radio', { name: 'Pilih frame dari toko' }).check();
    await page.getByTestId('select-frame-p1').click();
    await page.getByRole('button', { name: 'Mulai pengukuran', exact: true }).click();
    await page.getByTestId('customer-preparation').waitFor();
    assert.equal(payloads[1].product_id, 'p1'); assert.equal(payloads[1].variant_id, 'v1'); assert.equal(payloads[1].manual_frame, undefined);
    assert.deepEqual(payloads[1].required_parameters, ['vertex_right', 'vertex_left']);
    const vertexGuide = page.getByTestId('customer-preparation').getByTestId('measurement-illustration-guide');
    await vertexGuide.getByRole('button', { name: /Tandai titik/ }).click();
    await vertexGuide.locator('[data-guide-point="backLens"]').click();
    await vertexGuide.screenshot({ path: path.join(__dirname, 'meowsurement-guide-vertex-mobile.png'), style: '.of-customer-header { visibility: hidden; }' });
    const sideChecks = page.getByTestId('customer-preparation').locator('input[type=checkbox]');
    await sideChecks.nth(0).check(); await sideChecks.nth(1).check();
    await page.getByRole('button', { name: 'Lanjut ke kamera', exact: true }).click();
    await page.getByRole('button', { name: 'Buka kamera', exact: true }).click();
    await page.getByTestId('optifit-camera-start').click();
    await page.getByTestId('optifit-camera-capture').click();
    await page.getByRole('button', { name: 'Tandai titik & acuan frame', exact: true }).first().waitFor();
    assert.equal(detail.revisions[0].data.captures[0].calibrationSpec.frameDimension, 'b');
    assert.equal(detail.revisions[0].data.captures[0].calibrationSpec.lengthMm, 40);
    await page.getByRole('button', { name: 'Tandai titik & acuan frame', exact: true }).first().click();
    await page.getByTestId('customer-frame-reference').waitFor();
    assert.ok((await page.getByTestId('customer-frame-reference').textContent()).includes('40 mm'));
    assert.equal(await page.getByTestId('customer-photo-scale').locator('input[type=number],select').count(), 0);
    await page.getByRole('button', { name: 'Batal', exact: true }).click();
    for (const kind of ['distance_pd', 'pantoscopic', 'wrap']) {
      await page.getByRole('button', { name: 'Pengukuran baru', exact: true }).click();
      await page.getByTestId('measurement-card-' + kind).click();
      for (const [label, value] of [['Lebar lensa (A)', '52'], ['Tinggi lensa (B)', '40'], ['Jarak antar lensa (DBL)', '18']]) await page.getByLabel(label, { exact: true }).fill(value);
      await page.getByRole('button', { name: 'Mulai pengukuran', exact: true }).click();
      const guide = page.getByTestId('customer-preparation').getByTestId('measurement-illustration-guide');
      await guide.getByTestId('guide-drawing-' + kind).waitFor();
      if (kind === 'wrap') {
        assert.equal(await guide.getByRole('button', { name: /Tandai titik/ }).count(), 0);
        await guide.getByRole('button', { name: /Catat & simpan/ }).click();
        assert.equal(await guide.locator('[data-guide-point]').count(), 0);
      } else {
        await guide.getByRole('button', { name: /Tandai titik/ }).click();
        if (kind === 'pantoscopic') {
          assert.equal(await guide.locator('[data-guide-point="cornea"]').count(), 0);
          await guide.locator('[data-guide-point="verticalTop"]').click();
        }
      }
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await guide.screenshot({ path: path.join(__dirname, `meowsurement-guide-${kind}-mobile.png`), style: '.of-customer-header { visibility: hidden; }' });
    }
    assert.deepEqual(errors, []);
    const report = { api: 'mocked; no store database writes', viewport: '390x844', cards: 5, manualWithoutProductAndED: true, catalogWithoutED: true, fieldsScoped: true,
      cameraControlsAttached: true, customerCaptureDoesNotClaimOperatorVerification: true, captureAndAnnotation: true,
      illustratedGuides: { allFiveTypes: true, mobileAndDesktop: true, darkTheme: true, frameOnly: true, autoAForFront: true, autoBForSide: true, noExtraScaleInput: true, guideDoesNotInsertPhotoPoints: true }, errors };
    await fs.writeFile(path.join(__dirname, 'meowsurement-flow-browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error); process.exitCode = 1; });
