import { contentUrl, hasRichContent, sanitizeRichContent } from './richContent';
jest.mock('./api', () => ({ imageSrc: url => url.startsWith('/api/') ? `http://backend.test${url}` : url }));
const parse = html => { const element = document.createElement('div'); element.innerHTML = html; return element; };

test('published content retains supported headings, formatting, typography and table structure', () => {
  const element = parse(sanitizeRichContent('<h1>Judul</h1><p style="text-align:center;color:#ff0000;font-size:24px"><strong>Teks</strong><em>miring</em><u>garis</u><mark style="background-color:#fff0a6">sorot</mark></p><table><tbody><tr><th>Nama</th><td colspan="2">Isi</td></tr></tbody></table>'));
  expect(element.querySelector('h1').textContent).toBe('Judul');
  expect(element.querySelector('p').style.textAlign).toBe('center');
  expect(element.querySelector('p').style.fontSize).toBe('24px');
  expect(element.querySelector('mark').style.backgroundColor).not.toBe('');
  expect(element.querySelector('td').getAttribute('colspan')).toBe('2');
});
test('executable markup and page-covering CSS are removed while harmless typography survives', () => {
  const element = parse(sanitizeRichContent('<script>alert(1)</script><iframe src="https://bad.test"></iframe><form><input /></form><p style="position:fixed;inset:0;z-index:99999;background-image:url(https://bad.test/pixel);color:red">A</p><img src="https://test.invalid/photo.jpg" onerror="alert(1)"/><a href="javascript:alert(1)">B</a>'));
  expect(element.querySelector('script,iframe,form,input,[onerror]')).toBeNull();
  expect(element.querySelector('a').hasAttribute('href')).toBe(false);
  expect(element.querySelector('p').style.position).toBe('');
  expect(element.querySelector('p').style.backgroundImage).toBe('');
  expect(element.querySelector('p').style.color).toBe('red');
});
test('upload image URLs remain portable in storage and resolve to backend only for display', () => {
  const html = '<img src="/api/uploads-files/content/image.jpg" alt="Frame" width="50%">';
  expect(parse(sanitizeRichContent(html)).querySelector('img').getAttribute('src')).toBe('/api/uploads-files/content/image.jpg');
  const displayed = parse(sanitizeRichContent(html, { resolveImages: true })).querySelector('img');
  expect(displayed.src).toBe('http://backend.test/api/uploads-files/content/image.jpg');
  expect(displayed.getAttribute('width')).toBe('50%');
});
test('invalid links and private prescription images cannot be inserted into public content', () => {
  for (const value of ['javascript:alert(1)', 'data:text/html,test', '//bad.test/img', 'https://user:pass@bad.test/photo', 'https://bad.test/\\x']) expect(contentUrl(value)).toBeNull();
  expect(contentUrl('/api/prescriptions/uploads/private', true)).toBeNull();
  expect(contentUrl('/articles/hello')).toBe('/articles/hello');
  expect(contentUrl('mailto:admin@example.test')).toBe('mailto:admin@example.test');
  expect(parse(sanitizeRichContent('<img src="/api/prescriptions/uploads/private">')).querySelector('img')).toBeNull();
});
test('required visual content rejects blank paragraphs but accepts images and tables', () => {
  expect(hasRichContent('<p><br></p>')).toBe(false);
  expect(hasRichContent('<script>bad()</script>')).toBe(false);
  expect(hasRichContent('<p>Isi</p>')).toBe(true);
  expect(hasRichContent('<img src="/api/uploads-files/image.jpg">')).toBe(true);
  expect(hasRichContent('<table><tr><td></td></tr></table>')).toBe(true);
});

test('responsive image width and alignment survive sanitization without arbitrary layout styles', () => {
  const image = parse(sanitizeRichContent('<img src="/api/uploads-files/image.jpg" data-align="center" style="width:42.5%;position:fixed;left:0">')).querySelector('img');
  expect(image.style.width).toBe('42.5%'); expect(image.style.position).toBe('');
  expect(image.getAttribute('data-align')).toBe('center');
  const invalid = parse(sanitizeRichContent('<img src="/api/uploads-files/image.jpg" data-align="other">')).querySelector('img');
  expect(invalid.hasAttribute('data-align')).toBe(false);
});
