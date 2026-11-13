from pathlib import Path
p=Path('private/flat-master-browser-smoke.cjs').read_text(encoding='utf-8')
p=p.replace("description:'Frame untuk pengujian.'", "description:'<h2>Frame pilihan</h2><p><strong>Nyaman</strong> digunakan.</p>'")
p=p.replace("const product =", "categories.push({id:'legacy',name:'Koleksi lama',group_type:'collection',is_active:true});\nconst product =")
p=p.replace("category_ids:['frame','male','round']", "category_ids:['frame','male','round','legacy']")
p=p.replace("await page.goto(origin+'/admin/categories');", "await page.goto(origin+'/admin/categories');\n  assert.equal(await page.getByRole('tab',{name:'Koleksi',exact:true}).count(),0);")
p=p.replace("await page.goto(origin+'/admin/products'); await page.getByTestId('edit-p').click();", """await page.goto(origin+'/admin/products'); await page.getByTestId('edit-p').click();
  assert.equal(await page.getByTestId('product-master-collection').count(),0);
  await page.getByTestId('pf-desc').getByRole('textbox').waitFor();
  assert.equal(await page.getByTestId('pf-desc').locator('h2').textContent(),'Frame pilihan');
  assert.equal(await page.getByRole('button',{name:'Sisipkan gambar',exact:true}).count(),1);
  assert.equal(await page.getByRole('button',{name:'Sisipkan tabel',exact:true}).count(),1);""")
p=p.replace("report.editProductMasterGroups=true;", "report.editProductMasterGroups=true; assert(writes.at(-1).body.description.includes('<h2>')); assert(writes.at(-1).body.description.includes('<strong>')); report.richDescriptionEdit=true;")
p=p.replace("page.getByTestId('pf-desc').fill('Deskripsi frame')", "page.getByTestId('pf-desc').getByRole('textbox').fill('Deskripsi frame')")
p=p.replace("await page.getByTestId('product-master-gender')", "await page.getByLabel('Gaya paragraf',{exact:true}).selectOption('h2');\n  await page.getByTestId('product-master-gender')")
p=p.replace("report.createProductMasterGroups=true;", "report.createProductMasterGroups=true; assert(writes.at(-1).body.description.includes('<h2')); report.richDescriptionCreate=true;")
p=p.replace('flat-master-', 'product-editor-')
p=p.replace("getByRole('textbox')", "getByRole('textbox',{name:'Deskripsi produk',exact:true})")
Path('private/product-editor-browser-smoke.cjs').write_text(p,encoding='utf-8')
print('Product editor browser checks prepared')
