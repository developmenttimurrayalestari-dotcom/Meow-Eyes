from pathlib import Path
p=Path('private/brand-master-browser-smoke.cjs').read_text(encoding='utf-8')
a=p.index('const product =');b=p.index('(async()=>{',a)
p=p[:a]+"""const assets=[];
const pkg={id:'pkg',slug:'package-qa',name:'Paket QA',sku:'PKG-001',product_type:'package',description:'<p>Paket frame dan lensa</p>',price:400000,main_image:'/logo-meow.jpg',gallery:[],badges:[],category_ids:[],is_active:true,variants:[{id:'v-pkg',sku:'PKG-001-BLK',color:'Hitam',stock:2,reserved:0,is_active:true}]};
const frame={...pkg,id:'frame',sku:'FRAME-001',name:'Frame QA',product_type:'frame'};
const lens={...pkg,id:'lens',sku:'LENS-001',name:'Lensa QA',product_type:'lens'};
"""+p[b:]
p=p.replace("if(endpoint==='/admin/products'||endpoint==='/products') data={products:[product],total:1,page:1};", """if(endpoint==='/admin/products') data={products:[frame,pkg,lens],total:3};
   if(endpoint==='/admin/try-on-assets'){
    if(req.method()==='POST'){
     const body=req.postDataJSON();assets.push({...body,id:'asset-pkg',product_name:pkg.name,product_slug:pkg.slug});
     data={ok:true,asset:assets[0]};
    }else data={assets};
   }
   if(endpoint==='/products/package-qa')data={product:{...pkg,supports_try_on:true},reviews:[],related:[],breadcrumb:[]};
   if(endpoint==='/products/pkg/try-on')data={assets:assets.filter(a=>a.status==='published')};
   if(endpoint==='/try-on/catalog')data={products:assets.length?[{...pkg,try_on_assets:assets}]:[],next_offset:null};""")
a=p.index("  await page.goto(origin+");b=p.index('  assert.deepEqual(errors,[]);',a)
p=p[:a]+"""  await page.goto(origin+'/admin/try-on');
  await page.getByRole('button',{name:'Tambah aset',exact:true}).click();
  const choice=page.getByLabel('Produk Frame / Paket',{exact:true});
  await page.waitForFunction(()=>Array.from(document.querySelectorAll('select option')).some(o=>o.value==='pkg'));
  assert.deepEqual(await choice.locator('option').evaluateAll(options=>options.map(o=>o.value)),['','frame','pkg']);
  await choice.selectOption('pkg');report.adminIncludesFrameAndPackage=true;report.lensesExcluded=true;
  await page.getByLabel('Status',{exact:true}).selectOption('published');
  await page.getByTestId('tryon-image-open').click();await page.getByTestId('tryon-image-tab-url').click();
  await page.getByTestId('tryon-image-url-input').fill('/games/space-war/meow-pilot.png');
  await page.getByTestId('tryon-image-url-apply').click();
  await page.screenshot({path:path.join(__dirname,'vto-package-admin-form.png')});
  await page.getByRole('button',{name:'Simpan aset',exact:true}).click();
  await page.getByTestId('try-on-asset-asset-pkg').waitFor();
  const saved=writes.find(w=>w.endpoint==='/admin/try-on-assets');assert.equal(saved.body.product_id,'pkg');assert.equal(saved.body.status,'published');report.packageAssetSaved=true;
  await page.goto(origin+'/products/package-qa');
  await page.getByTestId('open-virtual-try-on').waitFor();report.packageDetailTryOnButton=true;
  await page.goto(origin+'/virtual-try-on');await page.getByRole('button',{name:/Paket QA/}).waitFor();
  await page.getByRole('button',{name:'Beli',exact:true}).click();
  assert.deepEqual(writes.find(w=>w.endpoint==='/cart').body,{product_id:'pkg',variant_id:'v-pkg',quantity:1});report.packageCatalogAndCart=true;
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(__dirname,'vto-package-mobile.png')});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));report.mobilePackageCatalog=true;
"""+p[b:]
p=p.replace('brand-master-browser-report','vto-package-browser-report')
Path('private/vto-package-browser-smoke.cjs').write_text(p,encoding='utf-8')
print('Frame/Package browser checks prepared')
