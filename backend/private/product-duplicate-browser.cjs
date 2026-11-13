const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const root = path.resolve(__dirname, '../../frontend/build');
const categories = [['frame', 'Frame', 'product_type', 'frame'], ['male', 'Pria', 'gender', 'pria'], ['round', 'Round', 'frame_shape', 'round']]
  .map(([id, name, group_type, code]) => ({ id, name, group_type, code, is_active: true }));
const source = { id: 'source', name: 'Frame contoh', slug: 'frame-contoh', sku: 'FRAME-01', product_type: 'frame',
  description: '<h2>Frame pilihan</h2><p><strong>Nyaman</strong> digunakan.</p>', price: 350000, weight_gram: 100,
  category_ids: ['frame', 'male', 'round'], brand_id: 'brand', segments: ['Pria'], main_image: '/logo-meow.jpg',
  gallery: [], badges: [], is_active: true, variants: [{ id: 'source-variant', sku: 'FRAME-01-BLK', color: 'Hitam', size: 'M', stock: 10, reserved: 2, is_active: true }] };
const products = [source];
(async () => {
  const server = http.createServer(async (req, res) => {
    try {
      let file = path.resolve(root, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
      if (!file.startsWith(root + path.sep)) file = path.join(root, 'index.html');
      try { if (!(await fs.stat(file)).isFile()) file = path.join(root, 'index.html'); } catch { file = path.join(root, 'index.html'); }
      res.setHeader('Content-Type', ({ '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.jpg': 'image/jpeg', '.png': 'image/png' })[path.extname(file)] || 'application/octet-stream');
      res.end(await fs.readFile(file));
    } catch { res.writeHead(500); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  const errors = [], writes = [];
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, serviceWorkers: 'block' });
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const req = route.request(), url = new URL(req.url()), endpoint = url.pathname.replace(/^\/api/, '');
      let data = { items: [], count: 0, pages: [] };
      if (endpoint === '/auth/me') data = { user: { user_id: 'admin', name: 'Admin QA', email: 'qa@example.com', role: 'admin' } };
      if (endpoint === '/settings/whatsapp') data = { enabled: false };
      if (endpoint === '/admin/categories') data = { categories };
      if (endpoint === '/admin/brands') data = { brands: [{ id: 'brand', name: 'Leinz', is_active: true }] };
      if (endpoint === '/admin/products') {
        const query = (url.searchParams.get('q') || '').toLowerCase();
        const rows = products.filter(product => product.name.toLowerCase().includes(query));
        data = { products: rows, total: rows.length };
      }
      if (endpoint === '/admin/products/source/duplicate' && req.method() === 'POST') {
        const copy = structuredClone(source);
        Object.assign(copy, { id: 'copy', name: source.name + ' (Salinan)', slug: 'frame-contoh-salinan-123', sku: 'FRAME-01-COPY-123', is_active: false });
        copy.variants = source.variants.map(variant => ({ ...variant, id: 'copy-variant', product_id: 'copy', sku: 'FRAME-01-BLK-COPY-123', stock: 0, reserved: 0 }));
        products.unshift(copy); data = { ok: true, product: copy }; writes.push({ endpoint });
      }
      if (endpoint === '/admin/products/copy' && req.method() === 'PUT') {
        const body = req.postDataJSON(); writes.push({ endpoint, body }); Object.assign(products[0], body); data = { ok: true };
      }
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(data) });
    });
    await page.goto(`http://127.0.0.1:${server.address().port}/admin/products`);
    await page.getByTestId('duplicate-source').click();
    const form = page.getByTestId('product-form'); await form.waitFor();
    assert.equal(await page.getByTestId('pf-name').inputValue(), 'Frame contoh (Salinan)');
    assert.equal(await page.getByLabel('SKU produk', { exact: true }).inputValue(), 'FRAME-01-COPY-123');
    assert.equal(await page.getByTestId('pf-active').isChecked(), false);
    assert.equal(await page.getByTestId('pf-desc').locator('h2').textContent(), 'Frame pilihan');
    assert.equal(await page.getByTestId('product-master-brand').getByLabel('Leinz', { exact: true }).isChecked(), true);
    assert.equal(await page.getByPlaceholder('Stok', { exact: true }).inputValue(), '0');
    await form.screenshot({ path: path.join(__dirname, 'product-duplicate-desktop.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    await form.screenshot({ path: path.join(__dirname, 'product-duplicate-mobile.png') });
    await page.getByTestId('pf-name').fill('Frame baru hasil duplikat');
    await page.getByTestId('pf-save').click(); await form.waitFor({ state: 'hidden' });
    assert.equal(writes.length, 2);
    assert.equal(writes[1].endpoint, '/admin/products/copy');
    assert.equal(writes[1].body.variants[0].id, 'copy-variant');
    assert.equal(writes[1].body.variants[0].stock, 0);
    assert.equal(source.name, 'Frame contoh');
    assert.equal(source.variants[0].stock, 10); assert.equal(source.variants[0].reserved, 2);
    assert.deepEqual(errors, []);
    const report = { ok: true, api: 'mocked; no store product writes', editOpensForNewProduct: true,
      newSku: true, inactive: true, zeroStock: true, categoryAndBrandPreserved: true,
      originalPreserved: true, desktopAndMobile: true, errors };
    await fs.writeFile(path.join(__dirname, 'product-duplicate-browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
