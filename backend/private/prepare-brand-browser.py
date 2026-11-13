from pathlib import Path
p=Path('private/product-editor-browser-smoke.cjs').read_text(encoding='utf-8')
p=p.replace("if(endpoint==='/admin/products'||endpoint==='/products')", "if(endpoint==='/admin/brands') data={brands:[{id:'brand',name:'Leinz',slug:'leinz',is_active:true}]};\n   if(endpoint==='/admin/products'||endpoint==='/products')")
p=p.replace("report.flatMasterTabsAndCreate=true;", """report.flatMasterTabsAndCreate=true;
  await page.getByRole('tab',{name:'Brand',exact:true}).click();
  await page.getByRole('cell',{name:'Leinz',exact:true}).waitFor();
  await page.getByRole('button',{name:'Edit Leinz',exact:true}).click();
  await page.getByRole('dialog').getByLabel('Nama',{exact:true}).fill('Leinz premium');
  await page.getByRole('button',{name:'Simpan',exact:true}).click();
  assert.equal(writes.at(-1).endpoint,'/admin/brands/brand');
  assert.equal(writes.at(-1).body.name,'Leinz premium');
  assert(!Object.hasOwn(writes.at(-1).body,'group_type'));report.brandTab=true;""")
p=p.replace("await page.getByTestId('product-master-material').getByLabel('Titanium',{exact:true}).check();", """await page.getByTestId('product-master-material').getByLabel('Titanium',{exact:true}).check();
  assert.equal(await page.getByTestId('pf-brand').count(),0);
  await page.getByTestId('product-master-brand').getByLabel('Leinz',{exact:true}).check();""")
p=p.replace("report.editProductMasterGroups=true;", "report.editProductMasterGroups=true; assert.equal(writes.at(-1).body.brand_id,'brand'); report.brandEdit=true;")
p=p.replace("await page.getByTestId('product-master-gender')", "await page.getByTestId('product-master-brand').getByLabel('Leinz',{exact:true}).check();\n  await page.getByTestId('product-master-gender')")
p=p.replace("report.createProductMasterGroups=true;", "report.createProductMasterGroups=true; assert.equal(writes.at(-1).body.brand_id,'brand'); report.brandCreate=true;")
p=p.replace('product-editor-','brand-master-')
Path('private/brand-master-browser-smoke.cjs').write_text(p,encoding='utf-8')
print('Brand browser checks prepared')
