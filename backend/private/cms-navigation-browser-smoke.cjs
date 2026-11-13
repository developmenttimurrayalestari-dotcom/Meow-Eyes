const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const build = path.resolve(__dirname, '../../frontend/build');
const pages = [
  ['tentang-meow-eyes', 'Tentang Meow Eyes', 'about'], ['kebijakan-pengiriman', 'Kebijakan Pengiriman', 'shipping_policy'],
  ['kebijakan-privasi', 'Kebijakan Privasi', 'privacy_policy'], ['kebijakan-refund', 'Kebijakan Refund', 'refund_policy'],
  ['syarat-ketentuan', 'Syarat & Ketentuan', 'terms_conditions'],
].map(([slug, title, page_type]) => ({ id: slug, slug, title, page_type, status: 'published', content: `<p>Isi ${title}</p>`, version: 1 }));
(async () => {
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      const filename = pathname.startsWith('/static/') ? path.resolve(build, '.' + pathname) : path.join(build, 'index.html');
      if (!filename.startsWith(build + path.sep)) { res.writeHead(404); res.end(); return; }
      res.setHeader('Content-Type', filename.endsWith('.js') ? 'application/javascript' : filename.endsWith('.css') ? 'text/css' : 'text/html');
      res.end(await fs.readFile(filename));
    } catch { res.writeHead(404); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    const page = await browser.newPage(); const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const pathname = new URL(route.request().url()).pathname;
      let data = {}, status = 200;
      if (pathname === '/api/auth/me') data = { user: { user_id: 'test-admin', name: 'Admin', role: 'admin' } };
      else if (pathname === '/api/cart') data = { items: [], count: 0 };
      else if (pathname === '/api/pages') data = { pages: pages.map(({ id, slug, title, page_type }) => ({ id, slug, title, page_type })) };
      else if (pathname.startsWith('/api/pages/')) {
        const found = pages.find(row => row.slug === pathname.split('/').pop());
        if (found) data = { page: found };
        else { data = { detail: 'Halaman tidak ditemukan' }; status = 404; }
      } else if (pathname === '/api/admin/pages') data = { pages: [...pages, { id: 'draft', title: 'Draft', slug: 'draft', content: '<p>Private</p>', status: 'draft', page_type: 'custom' }] };
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) });
    });
    const origin = `http://127.0.0.1:${server.address().port}`;
    await page.goto(origin + '/pages/tentang-meow-eyes');
    for (const record of pages) {
      const link = page.getByTestId('main-footer').getByRole('link', { name: record.title, exact: true });
      assert.equal(await link.getAttribute('href'), `/pages/${record.slug}`);
      await link.click();
      await page.getByTestId('page-title').filter({ hasText: record.title }).waitFor();
      await page.getByTestId('page-content').filter({ hasText: `Isi ${record.title}` }).waitFor();
    }
    await page.goto(origin + '/admin/pages');
    for (const record of pages) assert.equal(await page.getByTestId(`open-page-${record.slug}`).getAttribute('href'), `/pages/${record.slug}`);
    assert.equal(await page.getByTestId('open-page-draft').count(), 0);
    await page.goto(origin + '/pages/draft');
    await page.getByTestId('static-notfound').waitFor();
    assert.equal(await page.getByTestId('main-footer').locator('a[href="/pages/draft"]').count(), 0);
    assert.equal(errors.length, 0, errors.join('\n'));
    const report = { ok: true, footerPagesOpened: pages.length, adminPublicLinks: true, draftsNotPublic: true,
      browserErrors: errors, note: 'Production build with mocked APIs. No live CMS content changed.' };
    await fs.writeFile(path.join(__dirname, 'cms-navigation-browser-report.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
