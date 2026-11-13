const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const errors = [], categoryWrites = [], productWrites = [], catalogRequests = [];
  let categories = ['frame','lens','package'].map((code, index) => ({id:code,code,name:['Frame','Lensa','Paket'][index],group_type:'product_type',is_active:true}));
  const product_types = [...categories.map(({code,name}) => ({code,name})),{code:'accessories',name:'Aksesoris'}];
  let products = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1366, height: 1000 }, serviceWorkers: 'block' });
    await page.addInitScript(() => localStorage.setItem('meow_token','qa-admin-token'));
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const request = route.request(), url = new URL(request.url()), endpoint = url.pathname.replace(/^\/api/,'');
      let data = {items:[],pages:[],orders:[],count:0};
      if (endpoint === '/auth/me') data = {user:{user_id:'qa-admin',name:'Admin QA',email:'qa@example.com',role:'super_admin',has_pin:true,permissions:[],points_balance:0}};
      else if (endpoint === '/admin/categories' && request.method() === 'POST') {
        const body = request.postDataJSON(); categoryWrites.push(body);
        assert.equal(body.code,'accessories'); assert.equal(body.group_type,'product_type');
        const category = {...body,id:'accessories',slug:'product-type-aksesoris'};
        categories.push(category); data = {ok:true,category};
      } else if (endpoint === '/categories' || endpoint === '/admin/categories') data = {categories,product_types};
      else if (endpoint === '/brands' || endpoint === '/admin/brands') data = {brands:[]};
      else if (endpoint === '/admin/products' && request.method() === 'POST') {
        const body = request.postDataJSON(); productWrites.push(body);
        assert.equal(body.product_type,'accessories'); assert.deepEqual(body.category_ids,['accessories']);
        const product = {...body,id:'qa-case',sku:'QA-CASE',slug:'qa-case',main_image:'/logo-meow.jpg',variants:body.variants.map((v,i)=>({...v,id:'qa-variant-'+i}))};
        products.push(product); data = {ok:true,product};
      } else if (endpoint === '/admin/products' || endpoint === '/products') {
        if (endpoint === '/products') catalogRequests.push(url.searchParams.get('category_ids'));
        data = {products,total:products.length,page:1,limit:15};
      } else if (endpoint === '/settings/whatsapp') data = {enabled:false};
      await route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
    });
    await page.goto('http://localhost:3000/admin/categories');
    await page.getByRole('button',{name:'Tambah Jenis Produk',exact:true}).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByLabel('Nama',{exact:true}).fill('Aksesoris');
    await dialog.getByLabel('Jenis produk sistem').selectOption('accessories');
    assert.equal(await dialog.locator('option span').count(),0);
    await dialog.screenshot({path:path.join(__dirname,'accessories-category-form.png')});
    await dialog.getByRole('button',{name:'Simpan',exact:true}).click();
    await page.getByTestId('master-category-table').getByText('Aksesoris',{exact:true}).waitFor();
    assert.equal(categoryWrites.length,1);
    await page.goto('http://localhost:3000/admin/products');
    await page.getByTestId('new-product-btn').click();
    const form = page.getByTestId('product-form');
    await form.getByTestId('pf-name').fill('Kotak Kacamata QA');
    await form.getByTestId('pf-price').fill('15000');
    await form.getByTestId('pf-desc').locator('[contenteditable="true"]').fill('Kotak untuk melindungi kacamata.');
    await form.getByTestId('product-master-product_type').getByLabel('Aksesoris',{exact:true}).check();
    await form.getByRole('button',{name:'Simpan',exact:true}).click();
    await page.waitForFunction(() => !document.querySelector('[data-testid="product-form"]'));
    assert.equal(productWrites.length,1);
    await page.goto('http://localhost:3000/products');
    await page.getByTestId('filter-master-accessories').check();
    await page.waitForFunction(() => new URL(location.href).searchParams.get('category_ids') === 'accessories');
    await page.getByText('Kotak Kacamata QA',{exact:true}).waitFor();
    assert.ok(catalogRequests.includes('accessories')); assert.deepEqual(errors,[]);
    const report = {ok:true,api:'mocked; no real category/product/stock writes',categoryCreation:true,productCreation:true,publicCatalogFilter:true,nativeOptionMarkup:true,errors};
    await fs.writeFile(path.join(__dirname,'accessories-browser-report.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify(report));
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
