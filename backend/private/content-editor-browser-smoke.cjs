const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const frontend = path.resolve(__dirname, '../../frontend');
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j5WYAAAAASUVORK5CYII=', 'base64');
const article = { id: 'article', slug: 'guide', title: 'Panduan Frame', content: '<h2>Judul lama</h2><p>Konten lama tetap tersedia.</p>', status: 'draft', tags: [], category_id: null };
const knowledge = { id: 'knowledge', slug: 'knowledge', knowledge_type: 'frame_shape', title: 'Pengetahuan Frame', content: '<p>Pengetahuan lama.</p>', status: 'draft', is_published: false, pros: [], cons: [] };
const cms = { id: 'page', slug: 'terms', page_type: 'terms_conditions', title: 'Syarat', content: '<p>Halaman lama.</p>', status: 'draft', version: 1 };
const writes = [], errors = [];
(async () => {
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      const buildRoot = path.join(frontend, 'build');
      const filename = pathname.startsWith('/static/') ? path.resolve(buildRoot, '.' + pathname) : path.join(buildRoot, 'index.html');
      if (!filename.startsWith(buildRoot + path.sep)) { res.writeHead(404); res.end(); return; }
      res.setHeader('Content-Type', filename.endsWith('.js') ? 'application/javascript' : filename.endsWith('.css') ? 'text/css' : 'text/html');
      res.end(await fs.readFile(filename));
    } catch { res.writeHead(404); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    const page = await browser.newPage({ viewport: { width: 1360, height: 1000 } });
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const request = route.request(), pathname = new URL(request.url()).pathname;
      let data = {};
      if (pathname.startsWith('/api/uploads-files/')) { await route.fulfill({ contentType: 'image/png', body: png }); return; }
      if (pathname === '/api/auth/me') data = { user: { user_id: 'admin', email: 'admin@example.test', name: 'Admin', role: 'admin', permissions: [] } };
      else if (pathname === '/api/cart') data = { count: 0, items: [] };
      else if (pathname === '/api/admin/articles') data = { articles: [article] };
      else if (pathname === '/api/admin/articles/article') {
        if (request.method() === 'PUT') { Object.assign(article, request.postDataJSON()); writes.push({ resource: 'articles', content: article.content }); }
        data = { article };
      } else if (pathname === '/api/admin/knowledge') data = { items: [knowledge] };
      else if (pathname === '/api/admin/knowledge/knowledge') {
        if (request.method() === 'PUT') { Object.assign(knowledge, request.postDataJSON()); writes.push({ resource: 'knowledge', content: knowledge.content }); }
        data = { item: knowledge };
      } else if (pathname === '/api/admin/pages') data = { pages: [cms] };
      else if (pathname === '/api/admin/pages/page') {
        if (request.method() === 'PUT') { Object.assign(cms, request.postDataJSON()); writes.push({ resource: 'pages', content: cms.content }); }
        data = { page: cms };
      } else if (pathname === '/api/uploads') data = request.method() === 'POST' ? { url: '/api/uploads-files/content/editor-test.png' } : { items: [{ id: 'test', url: '/api/uploads-files/content/gallery.png', filename: 'gallery.png' }] };
      else if (pathname === '/api/articles/guide') data = { article, related: [] };
      else if (pathname === '/api/pages/terms') data = { page: cms };
      else if (pathname === '/api/admin/article-categories' || pathname === '/api/categories') data = { categories: [] };
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    });

    await page.goto(origin + '/admin/articles');
    await page.getByTestId('edit-article-guide').click();
    const form = page.getByTestId('article-form');
    const rich = page.getByTestId('art-content');
    const box = rich.locator('[contenteditable=true]');
    await box.waitFor(); assert.match(await box.innerHTML(), /Judul lama/);
    await box.click(); await box.press('Control+A'); await box.pressSequentially('Panduan memilih frame');
    await rich.getByLabel('Gaya paragraf').selectOption('h2');
    await box.press('Control+A'); await rich.getByRole('button', { name: 'Tebal', exact: true }).click();
    await rich.getByLabel('Ukuran teks').selectOption('24px');
    await rich.getByLabel('Warna teks', { exact: true }).fill('#cc3333');
    await rich.getByRole('button', { name: 'Rata tengah', exact: true }).click();
    await rich.getByRole('button', { name: 'Sisipkan tautan', exact: true }).click();
    await rich.getByLabel('URL tautan', { exact: true }).fill('/articles/guide');
    await rich.getByRole('button', { name: 'Terapkan tautan', exact: true }).click();
    await box.press('ArrowRight'); await box.press('End'); await box.press('Enter');
    await rich.getByLabel('Gaya paragraf').selectOption('p');
    await box.pressSequentially('Paragraf yang dapat diedit tanpa kehilangan posisi kursor.');
    await rich.getByRole('button', { name: 'Sisipkan tabel', exact: true }).click();
    await rich.getByRole('button', { name: 'Tambahkan tabel', exact: true }).click();
    await box.locator('td').first().click();
    await rich.getByRole('button', { name: 'Tambah baris', exact: true }).click();
    assert.equal(await box.locator('tr').count(), 4);
    await rich.getByRole('button', { name: 'Tambah kolom', exact: true }).click();
    assert.equal(await box.locator('tr').first().locator('th,td').count(), 4);
    await rich.getByRole('button', { name: 'Sisipkan gambar', exact: true }).click();
    await page.getByTestId('art-content-image-open').click();
    await page.getByTestId('art-content-image-modal').locator('input[type=file]').setInputFiles({ name: 'editor-test.png', mimeType: 'image/png', buffer: png });
    await page.getByTestId('art-content-image-modal').waitFor({ state: 'hidden' });
    await rich.getByLabel('Teks alternatif gambar').fill('Contoh frame pilihan');
    await rich.getByRole('button', { name: 'Tambahkan gambar ke konten', exact: true }).click();
    assert.equal(await box.locator('img').count(), 1);
    await rich.getByLabel('Lebar gambar', { exact: true }).selectOption('50%');
    const imageNode = box.locator('.rte-image-node');
    const handle = imageNode.locator('[data-resize-handle="se"]');
    await handle.scrollIntoViewIfNeeded();
    const handleBox = await handle.boundingBox();
    await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(handleBox.x + handleBox.width / 2 + 35, handleBox.y + handleBox.height / 2 + 20, { steps: 8 });
    await page.mouse.up();
    const resizedWidth = await imageNode.evaluate(element => element.style.width);
    assert.ok(parseFloat(resizedWidth) > 50 && parseFloat(resizedWidth) <= 100, 'Cursor did not resize the image');
    for (const alignment of ['kanan', 'kiri']) {
      await rich.getByRole('button', { name: `Gambar rata ${alignment}`, exact: true }).click();
      assert.equal(await imageNode.getAttribute('data-align'), alignment === 'kanan' ? 'right' : 'left');
    }
    await rich.getByRole('button', { name: 'Rata tengah', exact: true }).click();
    assert.equal(await imageNode.getAttribute('data-align'), 'center');
    await page.screenshot({ path: path.join(__dirname, 'content-editor-preview.png') });
    await form.getByRole('button', { name: 'Simpan', exact: true }).click();
    await form.waitFor({ state: 'hidden' });
    for (const expression of [/<h2/, /<strong>/, /<table/, /<img/, /font-size: 24px/, /text-align: center/, /Contoh frame pilihan/, /Paragraf yang dapat diedit tanpa kehilangan posisi kursor\./]) assert.match(article.content, expression);
    assert.match(article.content, /src="\/api\/uploads-files\/content\/editor-test.png"/);
    await page.getByTestId('edit-article-guide').click(); await box.waitFor();
    assert.equal(await box.locator('table').count(), 1); assert.equal(await box.locator('img').count(), 1);
    assert.equal(await imageNode.evaluate(element => element.style.width), resizedWidth);
    assert.equal(await imageNode.getAttribute('data-align'), 'center');
    assert.ok(!article.content.includes('rte-image-handle'), 'Editing handles leaked into saved content');
    await page.setViewportSize({ width: 390, height: 844 });
    assert.ok(await form.evaluate(element => element.scrollWidth <= element.clientWidth + 1), 'Editor form overflows on mobile');
    await page.setViewportSize({ width: 1360, height: 1000 });
    await page.goto(origin + '/articles/guide');
    const published = page.getByTestId('article-content'); await published.waitFor();
    assert.equal(await published.locator('h2').evaluate(el => getComputedStyle(el).textAlign), 'center');
    assert.equal(await published.locator('table').count(), 1);
    assert.match(await published.locator('img').getAttribute('src'), /\/api\/uploads-files\//);
    assert.equal(await published.locator('img').getAttribute('data-align'), 'center');
    await page.setViewportSize({ width: 390, height: 844 });
    const imageFits = await published.locator('img').evaluate(element => {
      const image = element.getBoundingClientRect(), parent = element.parentElement.getBoundingClientRect();
      return image.width <= parent.width + 1 && image.right <= parent.right + 1;
    });
    assert.ok(imageFits, 'Published image overflows on mobile');
    await page.setViewportSize({ width: 1360, height: 1000 });

    for (const [route, rowId, formId, editorId] of [['knowledge', 'kn-row-knowledge', 'knowledge-form', 'knowledge-content'], ['pages', 'page-row-terms', 'page-form', 'page-content-editor']]) {
      await page.goto(`${origin}/admin/${route}`);
      const row = page.getByTestId(rowId);
      if (route === 'knowledge') await row.locator('td').last().locator('button').first().click();
      else await row.getByRole('button', { name: 'Edit', exact: true }).click();
      const current = page.getByTestId(editorId), textbox = current.locator('[contenteditable=true]');
      await textbox.click(); await textbox.press('Control+A'); await textbox.pressSequentially(`Konten visual ${route}`);
      await current.getByLabel('Gaya paragraf').selectOption('h3');
      if (route === 'knowledge') {
        await textbox.press('ArrowRight'); await textbox.press('End'); await textbox.press('Enter');
        await current.getByRole('button', { name: 'Sisipkan gambar', exact: true }).click();
        await page.getByTestId('knowledge-content-image-open').click();
        await page.getByTestId('knowledge-content-image-tab-gallery').click();
        await page.getByTestId('knowledge-content-image-gallery-item-test').click();
        await current.getByRole('button', { name: 'Tambahkan gambar ke konten', exact: true }).click();
      }
      await page.getByTestId(formId).getByRole('button', { name: 'Simpan', exact: true }).click();
      await page.getByTestId(formId).waitFor({ state: 'hidden' });
    }
    assert.match(knowledge.content, /<h3>Konten visual knowledge<\/h3>/);
    assert.match(cms.content, /<h3>Konten visual pages<\/h3>/);
    assert.match(knowledge.content, /\/api\/uploads-files\/content\/gallery.png/);
    assert.equal(errors.length, 0, errors.join('\n'));
    const report = { ok: true, savedResources: writes.map(item => item.resource), headings: true, textStyles: true,
      editableTables: true, imageUpload: true, portableImagePaths: true, reopenPreservesContent: true,
      publishedFormatting: true, mobileLayout: true, imageGallery: true, imageSizing: true, cursorResize: true,
      imageAlignment: true, responsivePublishedImage: true, browserErrors: errors, note: 'Production build with mocked APIs; no live CMS records were modified.' };
    await fs.writeFile(path.join(__dirname, 'content-editor-browser-report.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
  } finally { await browser?.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
