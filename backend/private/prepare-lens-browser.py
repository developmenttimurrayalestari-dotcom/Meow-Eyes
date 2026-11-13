from pathlib import Path

root = Path(__file__).resolve().parent
source = (root/'checkout-prescriptions-browser.cjs').read_text(encoding='utf-8')
source = source.replace("role: 'customer'", "role: 'admin'")
source = source.replace("product: { name: 'Frame QA',", "frame_price: 100000, product: { name: 'Frame QA', product_type: 'frame',")
source = source.replace("product: { name: 'Paket QA',", "frame_price: 200000, product: { name: 'Paket QA', product_type: 'package',")
marker = '(async () => {'
fixtures = """const lensTypes = [{ id: 'sv', name: 'Single Vision', group_type: 'lens_type', is_active: true }, { id: 'photo-type', name: 'Photochromic', group_type: 'lens_type', is_active: true }];
const indexes = [{ id: 'standard', name: '1.50 Standard', index_value: '1.50', additional_price: 50000, is_active: true, lens_type_ids: ['sv'], lens_types: [lensTypes[0]] }, { id: 'photo', name: '1.56 Photochromic', index_value: '1.56', additional_price: 75000, is_active: true, lens_type_ids: ['photo-type'], lens_types: [lensTypes[1]] }, { id: 'generic', name: '1.60 Thin', index_value: '1.60', additional_price: 100000, is_active: true, lens_type_ids: [], lens_types: [] }];
"""
source = source.replace(marker, fixtures + marker, 1)
source = source.replace("if (pathname.endsWith('/auth/me')) data = { user };", """if (pathname.endsWith('/auth/me')) data = { user };
      else if (pathname === '/api/cart/frame/lens-options') data = { items: indexes, included_in_package: false, lens_types: [] };
      else if (pathname === '/api/cart/package/lens-options') data = { items: [indexes[0]], included_in_package: true, lens_types: [lensTypes[0]] };
      else if (pathname === '/api/admin/lens/indexes') data = { items: indexes };
      else if (pathname === '/api/admin/categories') data = { categories: lensTypes };
      else if (pathname.startsWith('/api/admin/lens/indexes/') && req.method() === 'PUT') {
        const input = req.postDataJSON(), item = indexes.find(index => index.id === pathname.split('/').pop());
        Object.assign(item, input, { lens_types: lensTypes.filter(type => input.lens_type_ids.includes(type.id)) }); data = { ok: true };
      }""")
source = source.replace("data = { subtotal: 400000, total: 410000, shipping: { cost: 10000 } };", "{ const subtotal = items.filter(row => row.id !== 'unselected').reduce((total, row) => total + row.subtotal, 0); data = { subtotal, total: subtotal + 10000, shipping: { cost: 10000 } }; }")
source = source.replace("saves.push({ id, prescription }); items.find(item => item.id === id).prescription = prescription;\n        data = { ok: true, prescription };", """saves.push({ id, prescription }); const item = items.find(item => item.id === id); item.prescription = prescription;
        item.lens_index = indexes.find(index => index.id === prescription.lens_index_id) || null;
        item.unit_price = item.frame_price + (item.product.product_type === 'frame' ? item.lens_index?.additional_price || 0 : 0);
        item.subtotal = item.unit_price * item.quantity; data = { ok: true, prescription, cart_item: item };""")
source = source.replace("for (const [index, id] of ['frame', 'package'].entries()) {", """assert.equal(await page.getByTestId('rx-lens-frame').locator('option').count(), 4);
    assert.equal(await page.getByTestId('rx-lens-package').locator('option').count(), 2);
    await page.getByTestId('rx-lens-frame').selectOption('photo');
    await page.getByTestId('rx-lens-package').selectOption('standard');
    for (const [index, id] of ['frame', 'package'].entries()) {""")
source = source.replace("await section.screenshot({ path:", "assert.equal((await page.getByTestId('checkout-total').textContent()).replace(/\\D/g, ''), '560000');\n    await section.screenshot({ path:", 1)
source = source.replace("assert.equal(confirmations, 0);", """assert.equal(await page.getByTestId('rx-lens-frame').inputValue(), 'photo');
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
    assert.equal(confirmations, 0);""")
source = source.replace('checkout-prescriptions-desktop.png', 'checkout-lens-index-desktop.png').replace('checkout-prescriptions-mobile.png', 'checkout-lens-index-mobile.png')
source = source.replace("reloadRestoresBoth: true, desktopAndMobile: true, errors", "reloadRestoresBoth: true, lensSelectionPerItem: true, frameCostsPerUnit: true, packageCostsZero: true, adminEditMultipleTypes: true, desktopAndMobile: true, errors")
source = source.replace('checkout-prescriptions-browser-report.json', 'checkout-lens-index-browser-report.json')
(root/'checkout-lens-index-browser.cjs').write_text(source, encoding='utf-8')
print('Prepared browser scenarios with mocked APIs; no live checkout mutations')
