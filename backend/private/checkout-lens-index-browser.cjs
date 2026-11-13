const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const build = path.resolve(__dirname, '../../frontend/build');
const user = { user_id: 'qa-prescriptions', name: 'Customer QA', role: 'admin', has_pin: true, points_balance: 0 };
const items = [
  { id: 'frame', quantity: 2, unit_price: 100000, subtotal: 200000, frame_price: 100000, product: { name: 'Frame QA', product_type: 'frame', main_image: '/logo-meow.jpg' }, variant: { sku: 'FRAME-QA' } },
  { id: 'package', quantity: 1, unit_price: 200000, subtotal: 200000, frame_price: 200000, product: { name: 'Paket QA', product_type: 'package', main_image: '/logo-meow.jpg' } },
  { id: 'unselected', quantity: 1, product: { name: 'Tidak dipilih' } },
];
const lensTypes = [{ id: 'sv', name: 'Single Vision', group_type: 'lens_type', is_active: true }, { id: 'photo-type', name: 'Photochromic', group_type: 'lens_type', is_active: true }];
const indexes = [{ id: 'standard', name: '1.50 Standard', index_value: '1.50', additional_price: 50000, is_active: true, lens_type_ids: ['sv'], lens_types: [lensTypes[0]] }, { id: 'photo', name: '1.56 Photochromic', index_value: '1.56', additional_price: 75000, is_active: true, lens_type_ids: ['photo-type'], lens_types: [lensTypes[1]] }, { id: 'generic', name: '1.60 Thin', index_value: '1.60', additional_price: 100000, is_active: true, lens_type_ids: [], lens_types: [] }];
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
      else if (pathname === '/api/cart/frame/lens-options') data = { items: indexes, included_in_package: false, lens_types: [] };
      else if (pathname === '/api/cart/package/lens-options') data = { items: [indexes[0]], included_in_package: true, lens_types: [lensTypes[0]] };
      else if (pathname === '/api/admin/lens/indexes') data = { items: indexes };
      else if (pathname === '/api/admin/categories') data = { categories: lensTypes };
      else if (pathname.startsWith('/api/admin/lens/indexes/') && req.method() === 'PUT') {
        const input = req.postDataJSON(), item = indexes.find(index => index.id === pathname.split('/').pop());
        Object.assign(item, input, { lens_types: lensTypes.filter(type => input.lens_type_ids.includes(type.id)) }); data = { ok: true };
      }
      else if (pathname === '/api/cart') data = { items, count: 3 };
      else if (pathname === '/api/addresses') data = { addresses: [{ id: 'address', label: 'Rumah', recipient: 'Customer QA', street: 'Alamat QA', city: 'Bandung', province: 'Jawa Barat', postal_code: '40111', is_default: true }] };
      else if (pathname === '/api/integrations/status') data = { payment: { provider: 'doku', ready: true }, shipping: { provider: 'everpro', ready: true } };
      else if (pathname === '/api/roulette/my-rewards') data = { spins: [] };
      else if (pathname === '/api/pages') data = { pages: [] };
      else if (pathname === '/api/checkout/shipping-options') data = { options: [{ quote_id: 'quote', courier_code: 'jne', courier_name: 'JNE', service_code: 'REG', service_label: 'Reguler', cost: 10000, expires_at: '2099-01-01T00:00:00Z' }] };
      else if (pathname === '/api/checkout/preview') { const subtotal = items.filter(row => row.id !== 'unselected').reduce((total, row) => total + row.subtotal, 0); data = { subtotal, total: subtotal + 10000, shipping: { cost: 10000 } }; }
      else if (pathname === '/api/uploads/prescription') data = { id: `photo-${++uploadCount}` };
      else if (/\/cart\/[^/]+\/prescription$/.test(pathname) && req.method() === 'PATCH') {
        const id = pathname.split('/')[3], prescription = req.postDataJSON();
        saves.push({ id, prescription }); const item = items.find(item => item.id === id); item.prescription = prescription;
        item.lens_index = indexes.find(index => index.id === prescription.lens_index_id) || null;
        item.unit_price = item.frame_price + (item.product.product_type === 'frame' ? item.lens_index?.additional_price || 0 : 0);
        item.subtotal = item.unit_price * item.quantity; data = { ok: true, prescription, cart_item: item };
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
    assert.equal(await page.getByTestId('rx-lens-frame').locator('option').count(), 4);
    assert.equal(await page.getByTestId('rx-lens-package').locator('option').count(), 2);
    await page.getByTestId('rx-lens-frame').selectOption('photo');
    await page.getByTestId('rx-lens-package').selectOption('standard');
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
    assert.equal((await page.getByTestId('checkout-total').textContent()).replace(/\D/g, ''), '560000');
    await section.screenshot({ path: path.join(__dirname, 'checkout-lens-index-desktop.png'), style: 'header {visibility:hidden;}' });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await section.screenshot({ path: path.join(__dirname, 'checkout-lens-index-mobile.png'), style: 'header {visibility:hidden;}' });
    await page.reload();
    await page.getByTestId('prescription-frame').waitFor();
    assert.equal(await page.getByTestId('prescription-frame').getByRole('textbox').inputValue(), 'Catatan frame');
    assert.equal(await page.getByTestId('prescription-package').getByRole('textbox').inputValue(), 'Catatan package');
    assert.equal(await section.getByRole('button', { name: 'Foto resep tersimpan', exact: true }).count(), 2);
    assert.equal(await page.getByTestId('rx-lens-frame').inputValue(), 'photo');
    assert.equal(await page.getByTestId('rx-lens-package').inputValue(), 'standard');
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`http://127.0.0.1:${server.address().port}/admin/lens-indexes`);
    await page.getByTestId('admin-lens-indexes').waitFor();
    await page.getByRole('button', { name: 'Edit Lens Index 1.50 Standard', exact: true }).click();
    const editor = page.getByRole('form', { name: 'Form Lens Index' });
    await editor.getByLabel('Photochromic', { exact: true }).check();
    await editor.screenshot({ path: path.join(__dirname, 'lens-index-admin-edit-desktop.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await editor.screenshot({ path: path.join(__dirname, 'lens-index-admin-edit-mobile.png') });
    await editor.getByRole('button', { name: 'Simpan', exact: true }).click();
    await editor.waitFor({ state: 'hidden' });
    assert.deepEqual(indexes[0].lens_type_ids, ['sv', 'photo-type']);
    assert.equal(confirmations, 0);
    assert.deepEqual(errors, []);
    const report = { api: 'mocked; no store writes or orders', onePrescriptionPerCartLine: true, selectedOnly: true,
      independentPhotosAndNotes: true, unsavedChangesBlockCheckout: true, reloadRestoresBoth: true, lensSelectionPerItem: true, frameCostsPerUnit: true, packageCostsZero: true, adminEditMultipleTypes: true, desktopAndMobile: true, errors };
    await fs.writeFile(path.join(__dirname, 'checkout-lens-index-browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error); process.exitCode = 1; });
