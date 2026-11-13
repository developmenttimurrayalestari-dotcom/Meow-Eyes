const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
const root = path.resolve(__dirname,'../../frontend/build');
const categories = [
 ['frame','Frame','product_type','frame'],['lens','Lensa','product_type','lens'],['package','Paket','product_type','package'],
 ['male','Pria','gender','pria'],['female','Wanita','gender','wanita'],['round','Round','frame_shape','round'],
 ['titanium','Titanium','material','titanium'],['single','Single Vision','lens_type','single-vision'],
].map(([id,name,group_type,code])=>({id,name,group_type,code,is_active:true}));
const product = {id:'p',name:'Frame contoh',slug:'contoh',sku:'FRAME-01',description:'Frame untuk pengujian.',product_type:'frame',price:350000,
 category_ids:['frame','male','round'],segments:['Pria'],variants:[],main_image:'/logo-meow.jpg',gallery:[],badges:[],is_active:true,weight_gram:100};
(async()=>{
 const server=http.createServer(async(req,res)=>{
  try {
   let file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
   if(!file.startsWith(root+path.sep)) file=path.join(root,'index.html');
   try{if(!(await fs.stat(file)).isFile()) file=path.join(root,'index.html');}catch{file=path.join(root,'index.html');}
   res.setHeader('Content-Type',({'.html':'text/html','.js':'application/javascript','.css':'text/css','.jpg':'image/jpeg','.png':'image/png'})[path.extname(file)]||'application/octet-stream');
   res.end(await fs.readFile(file));
  } catch {res.writeHead(500);res.end();}
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 let browser; const report={},writes=[],queries=[],errors=[];
 try {
  browser=await chromium.launch({channel:'msedge',headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/**',async route=>{
   const req=route.request(),url=new URL(req.url()),endpoint=url.pathname.replace(/^\/api/,'');
   if(req.method()!=='GET'){writes.push({endpoint,body:req.postDataJSON()});}
   if(endpoint==='/products') queries.push(Object.fromEntries(url.searchParams));
   let data={ok:true,categories:[],brands:[],games:[],pages:[],items:[],count:0};
   if(endpoint==='/auth/me') data={user:{user_id:'admin',name:'QA Admin',email:'qa@example.com',role:'admin'}};
   if(endpoint==='/settings/whatsapp') data={enabled:false};
   if(endpoint==='/admin/categories'||endpoint==='/categories') data={categories};
   if(endpoint==='/admin/products'||endpoint==='/products') data={products:[product],total:1,page:1};
   await route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
  });
  const origin=`http://127.0.0.1:${server.address().port}`;
  await page.goto(origin+'/admin/categories');
  await page.getByRole('tab',{name:'Material',exact:true}).click();
  await page.getByRole('cell',{name:'Titanium',exact:true}).waitFor();
  assert.equal(await page.getByTestId('master-category-table').getByText('Pria',{exact:true}).count(),0);
  await page.getByRole('button',{name:'Tambah Material',exact:true}).click();
  await page.getByRole('dialog').getByLabel('Nama',{exact:true}).fill('Stainless');
  await page.getByRole('button',{name:'Simpan',exact:true}).click();
  assert.equal(writes.at(-1).body.group_type,'material'); assert(!Object.hasOwn(writes.at(-1).body,'parent_id'));
  report.flatMasterTabsAndCreate=true;
  await page.screenshot({path:path.join(__dirname,'flat-master-admin-categories.png')});
  await page.goto(origin+'/admin/products'); await page.getByTestId('edit-p').click();
  await page.getByTestId('product-master-material').getByLabel('Titanium',{exact:true}).check();
  await page.getByRole('button',{name:'Simpan',exact:true}).click();
  assert.deepEqual(new Set(writes.at(-1).body.category_ids),new Set(['frame','male','round','titanium']));
  report.editProductMasterGroups=true;
  await page.getByTestId('new-product-btn').click();
  await page.getByTestId('pf-name').fill('Frame baru'); await page.getByTestId('pf-desc').fill('Deskripsi frame');
  await page.getByTestId('product-master-gender').getByLabel('Wanita',{exact:true}).check();
  await page.screenshot({path:path.join(__dirname,'flat-master-product-form.png')});
  await page.getByRole('button',{name:'Simpan',exact:true}).click();
  assert.deepEqual(new Set(writes.at(-1).body.category_ids),new Set(['frame','female']));
  report.createProductMasterGroups=true;
  await page.goto(origin+'/products');
  await page.getByTestId('filter-master-round').click();
  await page.waitForFunction(()=>new URLSearchParams(location.search).get('category_ids')==='round');
  const combinedResponse=page.waitForResponse(r=>r.url().includes('/api/products?')&&new URL(r.url()).searchParams.get('category_ids')==='round,titanium');
  await page.getByTestId('filter-master-titanium').click(); await combinedResponse;
  await page.waitForFunction(()=>new URLSearchParams(location.search).get('category_ids')==='round,titanium');
  assert(queries.some(q=>q.category_ids==='round,titanium')); report.catalogCombinedFilters=true;
  await page.screenshot({path:path.join(__dirname,'flat-master-catalog-desktop.png')});
  await page.setViewportSize({width:390,height:844});
  await page.getByTestId('open-filter-mobile').click();
  await page.locator('.md\\:hidden.fixed').getByTestId('filter-master-female').click();
  await page.waitForFunction(()=>new URLSearchParams(location.search).get('category_ids')?.includes('female'));
  assert(new URLSearchParams(new URL(page.url()).search).get('category_ids').includes('female'));
  await page.screenshot({path:path.join(__dirname,'flat-master-catalog-mobile.png')});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)); report.mobileMasterFilters=true;
  assert.deepEqual(errors,[]); report.browserErrors=errors;report.ok=true;
  await fs.writeFile(path.join(__dirname,'flat-master-browser-report.json'),JSON.stringify(report,null,2)); console.log(JSON.stringify(report));
 } finally {await browser?.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
