const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const build = path.resolve(__dirname, '../../frontend/build');
const user = { user_id: 'qa-address', name: 'Customer QA', role: 'customer', has_pin: true, points_balance: 0 };
let addresses = [{ id: 'old', label: 'Rumah', recipient: 'Customer QA', phone: '081234567890', street: 'Jl. QA No. 1', province: 'Jawa Barat', city: 'Bandung', postal_code: '40111', is_default: true }];
const regions = {
  provinces: [{ id: 'p+/=', name: 'JAWA BARAT' }, { id: 'p2', name: 'BALI' }], cities: [{ id: 'c1', name: 'KOTA BANDUNG' }],
  districts: [{ id: 'd1', name: 'BANDUNG WETAN' }], subdistricts: [{ id: 'v1', name: 'CITARUM', postal_code: '40115' }],
};
const quotes = [{ quote_id: 'quote-reg', courier_code: 'JNE', courier_name: 'JNE', service_code: 'REG', service_label: 'Reguler', cost: 12000, expires_at: '2099-01-01T00:00:00Z' },
  { quote_id: 'quote-express', courier_code: 'JNT', courier_name: 'J&T', service_code: 'EZ', service_label: 'Express', cost: 15000, expires_at: '2099-01-01T00:00:00Z' }];

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
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: 'block' });
    await context.addInitScript(() => { localStorage.setItem('meow_token', 'qa-only'); sessionStorage.setItem('meow_checkout_items_qa-address', JSON.stringify(['cart-qa'])); });
    const page = await context.newPage(), errors = [], saves = []; let shippingRequests = 0;
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const req = route.request(), url = new URL(req.url()), pathname = url.pathname;
      let data = {}, status = 200;
      if (pathname.endsWith('/auth/me')) data = { user };
      else if (pathname === '/api/cart') data = { items: [{ id: 'cart-qa', quantity: 1, unit_price: 100000, subtotal: 100000, product: { name: 'Frame QA', main_image: '/logo-meow.jpg' } }], count: 1 };
      else if (pathname === '/api/integrations/status') data = { payment: { provider: 'doku', ready: true }, shipping: { provider: 'everpro', ready: true } };
      else if (pathname === '/api/addresses' && req.method() === 'GET') data = { addresses };
      else if ((pathname === '/api/addresses' && req.method() === 'POST') || (pathname.startsWith('/api/addresses/') && req.method() === 'PATCH')) {
        const input = req.postDataJSON(); saves.push({ method: req.method(), input });
        assert.deepEqual(input.everpro_location, { province_id: 'p+/=', city_id: 'c1', district_id: 'd1', subdistrict_id: 'v1' });
        const address = { ...input, id: req.method() === 'POST' ? 'new' : pathname.split('/').pop() };
        addresses = [...addresses.filter(row => row.id !== address.id), address]; data = { address };
      } else if (pathname.startsWith('/api/shipping/locations/')) {
        const level = pathname.split('/').pop();
        data = { locations: level === 'cities' && url.searchParams.get('province_id') === 'p2' ? [{ id: 'c2', name: 'DENPASAR' }] : regions[level] || [] };
      } else if (pathname === '/api/checkout/shipping-options') {
        shippingRequests += 1;
        const address = addresses.find(row => row.id === req.postDataJSON().address_id);
        if (!address?.subdistrict) { status = 422; data = { detail: 'Wilayah alamat belum sesuai data EVERPRO. Klik Ubah pada alamat.' }; }
        else data = { options: quotes };
      } else if (pathname === '/api/checkout/preview') data = { subtotal: 100000, total: 112000, shipping: { cost: 12000 } };
      else if (pathname === '/api/roulette/my-rewards') data = { spins: [] };
      else if (pathname === '/api/pages') data = { pages: [] };
      else if (pathname === '/api/checkout/confirm') throw new Error('QA must not place orders');
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) });
    });
    const origin = `http://127.0.0.1:${server.address().port}`;
    const selectAll = async () => { for (const [name, value] of [['province', 'p+/='], ['city', 'c1'], ['district', 'd1'], ['subdistrict', 'v1']]) await page.getByTestId('addr-' + name).selectOption(value); };
    await page.goto(origin + '/checkout');
    await page.getByTestId('checkout-edit-address-old').click();
    await selectAll();
    assert.equal(await page.getByTestId('addr-postal_code').inputValue(), '40115');
    assert.equal(await page.getByTestId('addr-postal_code').getAttribute('readonly'), '');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.equal(await page.getByTestId('address-form').evaluate(node => node.checkValidity()), true);
    await page.getByTestId('address-form').screenshot({ path: path.join(__dirname, 'everpro-address-mobile.png'), style: 'header {visibility:hidden;}' });
    await page.getByTestId('addr-save').click();
    await page.getByTestId('shipping-section').getByText('JNE', { exact: false }).waitFor();
    assert.ok(shippingRequests >= 2, 'Saving the same address must refetch rates');
    assert.ok((await page.getByTestId('address-section').textContent()).includes('CITARUM'));
    await page.getByTestId('shipping-section').screenshot({ path: path.join(__dirname, 'everpro-shipping-options-mobile.png'), style: 'header {visibility:hidden;}' });
    await page.getByTestId('address-section').getByRole('button', { name: 'Tambah', exact: true }).click();
    await selectAll();
    await page.getByTestId('addr-province').selectOption('p2');
    assert.equal(await page.getByTestId('addr-postal_code').inputValue(), '');
    assert.equal(await page.getByTestId('addr-save').isDisabled(), true);
    await selectAll();
    await page.getByTestId('addr-recipient').fill('Customer QA Dua'); await page.getByTestId('addr-phone').fill('081234567891'); await page.getByTestId('addr-street').fill('Jl. QA No. 2');
    assert.equal(await page.getByTestId('address-form').evaluate(node => node.checkValidity()), true);
    await page.getByTestId('addr-save').click();
    await page.getByTestId('shipping-section').getByText('JNE', { exact: false }).waitFor();
    assert.equal(saves.filter(row => row.method === 'POST').length, 1);
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(origin + '/addresses'); await page.getByTestId('edit-address-old').click();
    await page.waitForFunction(() => document.querySelector('[data-testid="addr-subdistrict"]')?.value === 'v1');
    assert.equal(await page.getByTestId('addr-postal_code').inputValue(), '40115');
    await page.getByTestId('address-form').screenshot({ path: path.join(__dirname, 'everpro-address-desktop.png'), style: 'header {visibility:hidden;}' });
    assert.deepEqual(errors, []);
    const report = { api: 'mocked; no store writes or orders', nativeCascade: true, autoPostcode: true, clearsChildren: true, sameAddressRefreshesQuote: true,
      createAndEdit: true, editPrefillsOfficialNames: true, mobileAndDesktop: true, shippingRequests, errors };
    await fs.writeFile(path.join(__dirname, 'everpro-address-browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error); process.exitCode = 1; });
