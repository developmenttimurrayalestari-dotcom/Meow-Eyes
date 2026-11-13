const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const user = { user_id: 'qa-lens-summary', name: 'Customer QA', role: 'customer', has_pin: true, points_balance: 0 };
const index = { id: 'thin', name: '1.67 Super Thin', additional_price: 350000 };
const frame = { id: 'frame', quantity: 1, frame_price: 449000, product: { name: 'Frame QA', product_type: 'frame', main_image: '/logo-meow.jpg' }, variant: { sku: 'FRAME-QA' } };
const pack = { id: 'package', quantity: 1, frame_price: 449000, product: { name: 'Paket QA', product_type: 'package', main_image: '/logo-meow.jpg' }, variant: { sku: 'PAKET-QA' } };
const items = [frame, pack];
const priced = item => {
  const lens_price = item.product.product_type === 'frame' ? item.lens_index?.additional_price || 0 : 0;
  const unit_price = item.frame_price + lens_price;
  return { ...item, lens_price, unit_price, subtotal: unit_price * item.quantity };
};
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const errors = [], consoleErrors = []; let confirmations = 0;
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 1000 }, serviceWorkers: 'block' });
    await page.addInitScript(() => {
      localStorage.setItem('meow_token', 'qa-only');
      if (!sessionStorage.getItem('meow_checkout_items_qa-lens-summary')) sessionStorage.setItem('meow_checkout_items_qa-lens-summary', JSON.stringify(['frame']));
    });
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
    await page.route('**/api/**', async route => {
      const req = route.request(), endpoint = new URL(req.url()).pathname.replace(/^\/api/, '');
      let data = { items: [], pages: [], spins: [], events: [], count: 0 };
      if (endpoint === '/auth/me') data = { user };
      else if (endpoint === '/settings/whatsapp') data = { enabled: false };
      else if (endpoint === '/cart') data = { items: items.map(priced), count: 2 };
      else if (endpoint === '/addresses') data = { addresses: [{ id: 'address', label: 'Rumah', recipient: 'Customer QA', street: 'Alamat QA', city: 'Bandung', province: 'Jawa Barat', postal_code: '40111', is_default: true }] };
      else if (endpoint === '/integrations/status') data = { payment: { ready: true, provider: 'doku' }, shipping: { ready: true, provider: 'everpro' } };
      else if (/\/cart\/[^/]+\/lens-options$/.test(endpoint)) data = { items: [index], lens_types: [{ id: 'sv', name: 'Single Vision' }] };
      else if (/\/cart\/[^/]+\/prescription$/.test(endpoint)) {
        const item = items.find(row => endpoint === `/cart/${row.id}/prescription`);
        const prescription = req.postDataJSON(); item.prescription = prescription;
        item.lens_index = prescription.lens_index_id ? index : null;
        data = { ok: true, prescription, cart_item: priced(item) };
      } else if (endpoint === '/checkout/shipping-options') data = { options: [{ quote_id: 'same-quote', courier_code: 'jne', courier_name: 'JNE', service_code: 'REG', service_label: 'Reguler', cost: 8000, expires_at: '2099-01-01T00:00:00Z' }] };
      else if (endpoint === '/checkout/preview') {
        const selected = req.postDataJSON().selected_item_ids;
        const rows = items.filter(item => selected.includes(item.id)).map(priced);
        const subtotal = rows.reduce((sum, row) => sum + row.subtotal, 0);
        const lens_subtotal = rows.reduce((sum, row) => sum + row.lens_price * row.quantity, 0);
        data = { subtotal, lens_subtotal, product_subtotal: subtotal - lens_subtotal, total: subtotal + 8000, shipping: { cost: 8000 } };
      } else if (endpoint === '/checkout/confirm') { confirmations++; throw new Error('QA must not create orders'); }
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(data) });
    });
    const amount = async (id, expected) => {
      await page.waitForFunction(({ id, expected }) => document.querySelector(`[data-testid="${id}"]`)?.textContent.replace(/\D/g, '') === String(expected), { id, expected });
    };
    const saveLens = async id => {
      await page.getByTestId(`rx-lens-${id}`).selectOption('thin');
      await page.getByTestId(`prescription-${id}`).getByRole('button', { name: 'Simpan Resep', exact: true }).click();
    };
    await page.goto('http://localhost:3000/checkout');
    await amount('checkout-total', 457000);
    await saveLens('frame');
    await amount('checkout-product-subtotal', 449000); await amount('checkout-lens-subtotal', 350000); await amount('checkout-total', 807000);
    assert.ok((await page.getByTestId('checkout-item-pricing-frame').textContent()).includes('350.000'));
    await page.getByTestId('checkout-page').screenshot({ path: path.join(__dirname, 'lens-summary-frame-regular-desktop.png'), style: 'header {visibility:hidden;}' });
    frame.frame_price = 99000; frame.flash_sale_active = true;
    await page.reload();
    await amount('checkout-product-subtotal', 99000); await amount('checkout-lens-subtotal', 350000); await amount('checkout-total', 457000);
    assert.ok((await page.getByTestId('checkout-item-pricing-frame').textContent()).includes('Flash Sale'));
    await page.getByTestId('checkout-page').screenshot({ path: path.join(__dirname, 'lens-summary-frame-flash-desktop.png'), style: 'header {visibility:hidden;}' });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    await page.getByTestId('checkout-page').screenshot({ path: path.join(__dirname, 'lens-summary-frame-mobile.png'), style: 'header {visibility:hidden;}' });
    await page.evaluate(() => sessionStorage.setItem('meow_checkout_items_qa-lens-summary', JSON.stringify(['package'])));
    await page.reload(); await amount('checkout-total', 457000);
    await saveLens('package');
    await amount('checkout-product-subtotal', 449000); await amount('checkout-lens-subtotal', 0); await amount('checkout-total', 457000);
    assert.ok((await page.getByTestId('checkout-item-pricing-package').textContent()).includes('termasuk harga paket'));
    await page.getByTestId('checkout-page').screenshot({ path: path.join(__dirname, 'lens-summary-package-mobile.png'), style: 'header {visibility:hidden;}' });
    frame.quantity = 2;
    await page.evaluate(() => sessionStorage.setItem('meow_checkout_items_qa-lens-summary', JSON.stringify(['frame', 'package'])));
    await page.reload();
    await amount('checkout-product-subtotal', 647000); await amount('checkout-lens-subtotal', 700000); await amount('checkout-total', 1355000);
    assert.deepEqual(errors, []);
    assert.equal(consoleErrors.filter(message => /hydration error|cannot be a child of <option>/i.test(message)).length, 0);
    assert.equal(confirmations, 0);
    const report = { ok: true, api: 'mocked; no store writes or orders', frameLensCosts350000: true,
      regularTotal807000: true, flashSaleTotal457000: true, packageLensCostsZero: true,
      twoFramesCountTwice: true, sameShippingQuoteRefreshesTotals: true, desktopAndMobile: true, errors };
    await fs.writeFile(path.join(__dirname, 'lens-summary-browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
