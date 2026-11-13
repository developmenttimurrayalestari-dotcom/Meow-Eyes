const fs=require('node:fs/promises'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require('./tryon-browser-tools/node_modules/playwright');
const root=path.resolve(__dirname,'../../frontend/build');
const initial=()=>['A','B','C'].map(id=>({id,name:`Frame ${id}`,slug:id,sku:`ME-${id}`,description:'Frame contoh',price:350000,product_type:'frame',main_image:'/logo-meow.jpg',is_active:true,variants:[]}));
(async()=>{
 const server=http.createServer(async(req,res)=>{
  try{let file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
   if(!file.startsWith(root+path.sep))file=path.join(root,'index.html');
   try{if(!(await fs.stat(file)).isFile())file=path.join(root,'index.html');}catch{file=path.join(root,'index.html');}
   res.setHeader('Content-Type',({'.html':'text/html','.js':'application/javascript','.css':'text/css','.jpg':'image/jpeg'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));
  }catch{res.writeHead(500);res.end();}
 });
 await new Promise(done=>server.listen(0,'127.0.0.1',done));
 let browser,products=initial(),accept=true,fail=false;const calls=[],errors=[],report={};
 try{
  browser=await chromium.launch({channel:'msedge',headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('dialog',async dialog=>{if(accept)await dialog.accept();else await dialog.dismiss();accept=true;});
  await page.route('**/api/**',async route=>{
   const req=route.request(),url=new URL(req.url()),endpoint=url.pathname.replace(/^\/api/,'');
   let data={categories:[],brands:[],games:[],pages:[],items:[],count:0,ok:true};
   if(endpoint==='/auth/me')data={user:{user_id:'admin',name:'QA Admin',email:'qa@example.com',role:'admin'}};
   if(endpoint==='/settings/whatsapp')data={enabled:false};
   if(endpoint==='/admin/products'){
    const q=url.searchParams.get('q')||'',filtered=products.filter(p=>p.name.includes(q));data={products:filtered,total:filtered.length};
   }
   if(endpoint==='/admin/products/bulk-actions'){
    const body=req.postDataJSON();calls.push(body);
    if(fail){fail=false;await route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({detail:'Coba muat ulang produk.'})});return;}
    products=body.action==='delete'?products.filter(p=>!body.product_ids.includes(p.id)):products.map(p=>body.product_ids.includes(p.id)?{...p,is_active:false}:p);
   }
   await route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
  });
  const url=`http://127.0.0.1:${server.address().port}/admin/products`;
  await page.goto(url);await page.getByTestId('product-row-A').waitFor();
  await page.getByLabel('Pilih Frame A',{exact:true}).check();
  assert(await page.getByLabel('Pilih semua produk pada halaman ini',{exact:true}).evaluate(el=>el.indeterminate));
  await page.getByLabel('Pilih semua produk pada halaman ini',{exact:true}).check();
  await page.screenshot({path:path.join(__dirname,'product-actions-desktop.png')});
  accept=false;await page.getByTestId('bulk-delete-products').click();assert.equal(calls.length,0);report.cancelPreservesSelection=true;
  await page.getByTestId('bulk-deactivate-products').click();
  await page.waitForFunction(()=>document.querySelector('[data-testid="deactivate-A"]').disabled);
  assert.equal(await page.locator('tbody tr').count(),3);assert.equal(calls.at(-1).action,'deactivate');assert.equal(calls.at(-1).product_ids.length,3);report.bulkDeactivation=true;
  await page.getByLabel('Pilih semua produk pada halaman ini',{exact:true}).check();
  await page.getByTestId('bulk-delete-products').click();await page.getByText('Belum ada produk.',{exact:true}).waitFor();
  assert.equal(calls.at(-1).action,'delete');assert.equal(calls.at(-1).product_ids.length,3);report.bulkDeletion=true;
  products=initial();await page.reload();await page.getByTestId('product-row-A').waitFor();
  await page.getByTestId('delete-A').click();await page.waitForFunction(()=>!document.querySelector('[data-testid="product-row-A"]'));
  assert.deepEqual(calls.at(-1),{action:'delete',product_ids:['A']});report.singleDeletion=true;
  await page.getByTestId('deactivate-B').click();await page.waitForFunction(()=>document.querySelector('[data-testid="deactivate-B"]').disabled);
  assert.equal(await page.locator('tbody tr').count(),2);report.singleDeactivation=true;
  await page.getByLabel('Pilih Frame C',{exact:true}).check();fail=true;await page.getByTestId('bulk-delete-products').click();
  await page.getByRole('alert').filter({hasText:'Coba muat ulang produk.'}).waitFor();
  assert(await page.getByLabel('Pilih Frame C',{exact:true}).isChecked());report.errorPreservesSelection=true;
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(__dirname,'product-actions-mobile.png')});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  assert(await page.getByTestId('bulk-delete-products').isVisible());report.mobileActions=true;
  assert.deepEqual(errors,[]);report.browserErrors=errors;report.ok=true;
  await fs.writeFile(path.join(__dirname,'product-actions-browser-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser?.close();await new Promise(done=>server.close(done));}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
