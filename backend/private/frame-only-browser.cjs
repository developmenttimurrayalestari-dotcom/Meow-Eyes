const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const user = { user_id: 'qa-frame-only', name: 'Customer QA', role: 'customer', has_pin: true, points_balance: 0 };
const index = { id: 'thin', name: '1.67 Super Thin', additional_price: 350000 };
let item = { id: 'frame', quantity: 1, frame_price: 449000, lens_index: null, lens_product: null, prescription: null,
  product: { name: 'Frame QA', product_type: 'frame', main_image: '/logo-meow.jpg' }, variant: { sku: 'FRAME-QA' } };
const priced = () => {
  const lens_price = (item.lens_product ? 50000 : 0) + (item.lens_index?.additional_price || 0);
  return { ...item, lens_price, unit_price: item.frame_price + lens_price, subtotal: (item.frame_price + lens_price) * item.quantity };
};
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const errors = [], saves = []; let uploads = 0, confirmations = 0;
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 1000 }, serviceWorkers: 'block' });
    await page.addInitScript(() => {
      localStorage.setItem('meow_token', 'qa-only');
      sessionStorage.setItem('meow_checkout_items_qa-frame-only', JSON.stringify(['frame']));
    });
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const req = route.request(), endpoint = new URL(req.url()).pathname.replace(/^\/api/, '');
      let data = { items: [], pages: [], spins: [], events: [], count: 0 };
      if (endpoint === '/auth/me') data = { user };
      else if (endpoint === '/settings/whatsapp') data = { enabled: false };
      else if (endpoint === '/cart') data = { items: [priced()], count: 1 };
      else if (endpoint === '/addresses') data = { addresses: [{ id: 'address', label: 'Rumah', recipient: 'Customer QA', street: 'Alamat QA', city: 'Bandung', province: 'Jawa Barat', postal_code: '40111', is_default: true }] };
      else if (endpoint === '/integrations/status') data = { payment: { ready: true, provider: 'doku' }, shipping: { ready: true, provider: 'everpro' } };
      else if (endpoint === '/cart/frame/lens-options') data = { items: [index], lens_types: [] };
      else if (endpoint === '/cart/frame/prescription') {
        const body = req.postDataJSON(); saves.push(body);
        if (body.frame_only) item.lens_product = null;
        item.lens_index = body.lens_index_id ? index : null;
        item.prescription = body.notes || body.attachment_upload_id ? body : null;
        data = { ok: true, prescription: item.prescription, cart_item: priced() };
      } else if (endpoint === '/checkout/shipping-options') data = { options: [{ quote_id: 'quote', courier_code: 'jne', courier_name: 'JNE', service_code: 'REG', service_label: 'Reguler', cost: 8000, expires_at: '2099-01-01T00:00:00Z' }] };
      else if (endpoint === '/checkout/preview') {
        const row = priced();
        data = { subtotal: row.subtotal, product_subtotal: row.frame_price * row.quantity,
          lens_subtotal: row.lens_price * row.quantity, total: row.subtotal + 8000, shipping: { cost: 8000 } };
      } else if (endpoint === '/uploads/prescription') { uploads++; throw new Error('Optional flow must not upload'); }
      else if (endpoint === '/checkout/confirm') { confirmations++; throw new Error('QA must not create orders'); }
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(data) });
    });
    const amount = async expected => page.waitForFunction(expected => document.querySelector('[data-testid="checkout-total"]')?.textContent.replace(/\D/g, '') === String(expected), expected);
    const ready = async () => page.waitForFunction(() => !document.querySelector('[data-testid="submit-order-btn"]')?.disabled);
    const select = page.getByTestId('rx-lens-frame'), form = page.getByTestId('prescription-frame');
    const save = () => form.getByRole('button', { name: 'Simpan Resep', exact: true }).click();
    await page.goto('http://localhost:3000/checkout'); await amount(457000); await ready();
    assert.equal(await select.inputValue(), '');
    assert.ok((await select.locator('option:checked').textContent()).includes('Beli frame saja'));
    assert.equal(await form.locator('[required]').count(), 0);
    assert.equal(await form.getByRole('button', { name: 'Simpan Resep', exact: true }).isDisabled(), true);
    await select.selectOption('thin');
    assert.equal(await page.getByTestId('submit-order-btn').isDisabled(), true);
    await select.selectOption(''); await ready();
    await form.getByRole('textbox').fill('Catatan sementara');
    assert.equal(await page.getByTestId('submit-order-btn').isDisabled(), true);
    await form.getByRole('textbox').fill(''); await ready();
    assert.equal(saves.length, 0); assert.equal(uploads, 0);
    await page.getByTestId('checkout-page').screenshot({ path: path.join(__dirname, 'frame-only-desktop.png'), style: 'header {visibility:hidden;}' });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    await page.getByTestId('checkout-page').screenshot({ path: path.join(__dirname, 'frame-only-mobile.png'), style: 'header {visibility:hidden;}' });
    await select.selectOption('thin'); await save(); await amount(807000); await ready();
    assert.equal(item.prescription, null);
    await select.selectOption(''); await save(); await amount(457000); await ready();
    item.lens_product = { id: 'lens', name: 'Blue Cut' };
    await page.reload(); await amount(507000);
    assert.ok((await select.locator('option:checked').textContent()).includes('Blue Cut'));
    await select.selectOption(''); await save(); await amount(457000); await ready();
    assert.equal(saves.at(-1).frame_only, true); assert.equal(item.lens_product, null);
    assert.equal(item.prescription, null); assert.equal(confirmations, 0); assert.deepEqual(errors, []);
    const report = { ok: true, api: 'mocked; no store writes or orders', emptyLensAndRecipeAllowCheckout: true,
      revertingOptionalEditsAllowsCheckout: true, noSaveOrUploadRequired: true,
      frameOnlyRemovesIndexAndBundleCharges: true, desktopAndMobile: true, errors };
    await fs.writeFile(path.join(__dirname, 'frame-only-browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
