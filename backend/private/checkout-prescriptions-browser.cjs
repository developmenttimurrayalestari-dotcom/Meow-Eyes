const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const build = path.resolve(__dirname, '../../frontend/build');
const user = { user_id: 'qa-prescriptions', name: 'Customer QA', role: 'customer', has_pin: true, points_balance: 0 };
const items = [
  { id: 'frame', quantity: 2, unit_price: 100000, subtotal: 200000, product: { name: 'Frame QA', main_image: '/logo-meow.jpg' }, variant: { sku: 'FRAME-QA' } },
  { id: 'package', quantity: 1, unit_price: 200000, subtotal: 200000, product: { name: 'Paket QA', main_image: '/logo-meow.jpg' } },
  { id: 'unselected', quantity: 1, product: { name: 'Tidak dipilih' } },
];
(async () => {
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      const file = path.resolve(build, '.' + (pathname.startsWith('/static/') || pathname.endsWith('.jpg') ? pathname : '/index.html'));
      if (!file.startsWith(build + path.sep)) throw new Error('Invalid path');
      res.setHeader('Content-Type', file.endsWith('.js') ? 'application/javascript' : file.endsWith('.css') ? 'text/css' : file.endsWith('.jpg') ? 'image/jpeg' : 'text/html');
      res.end(await fs.readFile(file));
    } catch { res.writeHead(404); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, serviceWorkers: 'block' });
    await context.addInitScript(() => {
      localStorage.setItem('meow_token', 'qa-only');
      sessionStorage.setItem('meow_checkout_items_qa-prescriptions', JSON.stringify(['frame', 'package']));
    });
    const page = await context.newPage(), errors = [], saves = [];
    let uploadCount = 0, confirmations = 0;
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const req = route.request(), pathname = new URL(req.url()).pathname;
      let data = {};
      if (pathname.endsWith('/auth/me')) data = { user };
      else if (pathname === '/api/cart') data = { items, count: 3 };
      else if (pathname === '/api/addresses') data = { addresses: [{ id: 'address', label: 'Rumah', recipient: 'Customer QA', street: 'Alamat QA', city: 'Bandung', province: 'Jawa Barat', postal_code: '40111', is_default: true }] };
      else if (pathname === '/api/integrations/status') data = { payment: { provider: 'doku', ready: true }, shipping: { provider: 'everpro', ready: true } };
      else if (pathname === '/api/roulette/my-rewards') data = { spins: [] };
      else if (pathname === '/api/pages') data = { pages: [] };
      else if (pathname === '/api/checkout/shipping-options') data = { options: [{ quote_id: 'quote', courier_code: 'jne', courier_name: 'JNE', service_code: 'REG', service_label: 'Reguler', cost: 10000, expires_at: '2099-01-01T00:00:00Z' }] };
      else if (pathname === '/api/checkout/preview') data = { subtotal: 400000, total: 410000, shipping: { cost: 10000 } };
      else if (pathname === '/api/uploads/prescription') data = { id: `photo-${++uploadCount}` };
      else if (/\/cart\/[^/]+\/prescription$/.test(pathname) && req.method() === 'PATCH') {
        const id = pathname.split('/')[3], prescription = req.postDataJSON();
        saves.push({ id, prescription }); items.find(item => item.id === id).prescription = prescription;
        data = { ok: true, prescription };
      } else if (pathname === '/api/checkout/confirm') { confirmations += 1; data = { detail: 'QA must not place orders' }; }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    });
    await page.goto(`http://127.0.0.1:${server.address().port}/checkout`);
    const section = page.getByTestId('checkout-prescriptions');
    await section.waitFor();
    assert.equal(await section.locator('form').count(), 2);
    assert.equal(await page.getByTestId('prescription-unselected').count(), 0);
    assert.equal(await section.locator('input[type=number]').count(), 0);
    assert.ok((await page.getByTestId('prescription-frame').textContent()).includes('seluruh 2 produk'));
    for (const [index, id] of ['frame', 'package'].entries()) {
      const form = page.getByTestId(`prescription-${id}`);
      await form.getByRole('textbox').fill(`Catatan ${id}`);
      await page.getByTestId(`rx-upload-${id}`).setInputFiles({ name: `${id}.png`, mimeType: 'image/png', buffer: Buffer.from('QA upload stub') });
      await form.getByRole('button', { name: `${id}.png`, exact: true }).waitFor();
    }
    const submit = page.getByTestId('submit-order-btn');
    assert.equal(await submit.isDisabled(), true);
    await page.getByTestId('prescription-frame').getByRole('button', { name: 'Simpan Resep' }).click();
    await page.getByTestId('prescription-frame').getByText('Resep tersimpan.', { exact: true }).waitFor();
    assert.equal(await submit.isDisabled(), true);
    await page.getByTestId('prescription-package').getByRole('button', { name: 'Simpan Resep' }).click();
    await page.getByTestId('prescription-package').getByText('Resep tersimpan.', { exact: true }).waitFor();
    await page.waitForFunction(() => !document.querySelector('[data-testid="submit-order-btn"]').disabled);
    assert.deepEqual(saves.map(row => [row.id, row.prescription.notes, row.prescription.attachment_upload_id]), [
      ['frame', 'Catatan frame', 'photo-1'], ['package', 'Catatan package', 'photo-2'],
    ]);
    await section.screenshot({ path: path.join(__dirname, 'checkout-prescriptions-desktop.png'), style: 'header {visibility:hidden;}' });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await section.screenshot({ path: path.join(__dirname, 'checkout-prescriptions-mobile.png'), style: 'header {visibility:hidden;}' });
    await page.reload();
    await page.getByTestId('prescription-frame').waitFor();
    assert.equal(await page.getByTestId('prescription-frame').getByRole('textbox').inputValue(), 'Catatan frame');
    assert.equal(await page.getByTestId('prescription-package').getByRole('textbox').inputValue(), 'Catatan package');
    assert.equal(await section.getByRole('button', { name: 'Foto resep tersimpan', exact: true }).count(), 2);
    assert.equal(confirmations, 0);
    assert.deepEqual(errors, []);
    const report = { api: 'mocked; no store writes or orders', onePrescriptionPerCartLine: true, selectedOnly: true,
      independentPhotosAndNotes: true, unsavedChangesBlockCheckout: true, reloadRestoresBoth: true, desktopAndMobile: true, errors };
    await fs.writeFile(path.join(__dirname, 'checkout-prescriptions-browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error); process.exitCode = 1; });
