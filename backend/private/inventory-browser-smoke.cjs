const fs=require('node:fs/promises'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require('./tryon-browser-tools/node_modules/playwright');
const root=path.resolve(__dirname,'../../frontend/build');
const initial=()=>[
 {product_id:'new',variant_id:null,sku:'NEW',name:'Frame Baru',variant_label:'-',stock:0,reserved:0,min_alert:5,product_active:true,variant_active:true,can_adjust:true},
 {product_id:'existing',variant_id:'v-existing',sku:'EXISTING',name:'Frame Existing',variant_label:'Hitam',stock:10,reserved:2,min_alert:5,product_active:true,variant_active:true,can_adjust:true}
];
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
   if(endpoint==='/admin/inventory')data={items:products,deleted_items:[{...initial()[1],product_id:'deleted',name:'Frame dihapus',deleted_at:'2026-11-12',can_adjust:false}]};
   if(endpoint.endsWith('/stock')&&req.method()==='POST'){
    const body=req.postDataJSON();calls.push(body);
    const id=endpoint.split('/')[3],item=products.find(p=>p.product_id===id);
    item.stock+=body.adjustment_type==='receipt_stock'?body.quantity:-body.quantity;
    item.variant_id=item.variant_id||'v-new';data={ok:true,stock:item.stock,variant_id:item.variant_id};
   }
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
  const url=`http://127.0.0.1:${server.address().port}/admin/inventory`;
  await page.goto(url);await page.getByTestId('inv-row-0').waitFor();
  assert.equal(await page.getByTestId('inventory-table').locator('tbody tr').count(),2);
  assert(await page.getByTestId('inv-deleted-adjust-0').isDisabled());
  assert((await page.getByTestId('inv-deleted-row-0').getAttribute('class')).includes('bg-zinc-100'));
  await page.getByTestId('inv-adjust-0').click();
  await page.getByLabel('Nomor TTB',{exact:true}).fill('TTB-001');
  await page.getByLabel('Jumlah',{exact:true}).fill('8');
  await page.screenshot({path:path.join(__dirname,'inventory-receipt-desktop.png')});
  await page.getByTestId('inv-save').click();await page.getByRole('dialog').waitFor({state:'hidden'});
  assert.deepEqual(calls.at(-1),{variant_id:null,adjustment_type:'receipt_stock',quantity:8,ttb_number:'TTB-001',note:''});report.initialReceipt=true;
  await page.getByTestId('inv-adjust-0').click();
  await page.getByLabel('Jenis Adjust Stock',{exact:true}).selectOption('issue_stock');
  await page.getByLabel('Nomor TTB',{exact:true}).fill('TTB-002');await page.getByLabel('Jumlah',{exact:true}).fill('3');
  await page.getByTestId('inv-save').click();await page.getByRole('dialog').waitFor({state:'hidden'});
  assert.equal(calls.at(-1).variant_id,'v-new');assert.equal(calls.at(-1).adjustment_type,'issue_stock');assert.equal(products[0].stock,5);report.issueStock=true;
  await page.screenshot({path:path.join(__dirname,'inventory-tables-desktop.png')});
  await page.setViewportSize({width:390,height:844});await page.getByTestId('inv-adjust-0').click();
  await page.screenshot({path:path.join(__dirname,'inventory-receipt-mobile.png')});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));report.mobileForm=true;report.deletedDisabled=true;
  assert.deepEqual(errors,[]);report.browserErrors=errors;report.ok=true;
  await fs.writeFile(path.join(__dirname,'inventory-browser-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser?.close();await new Promise(done=>server.close(done));}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
