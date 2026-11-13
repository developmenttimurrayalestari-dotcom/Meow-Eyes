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
categories.push({id:'legacy',name:'Koleksi lama',group_type:'collection',is_active:true});
const assets=[{id:'asset-pkg',product_id:'pkg',asset_type:'image',status:'published',source_url:'/games/space-war/meow-pilot.png',scale:1}];
const pkg={id:'pkg',slug:'package-qa',name:'Paket QA',sku:'PKG-001',product_type:'package',description:'<p>Paket frame dan lensa</p>',price:400000,main_image:'/logo-meow.jpg',gallery:[],badges:[],category_ids:[],is_active:true,variants:[{id:'v-pkg',sku:'PKG-001-BLK',color:'Hitam',stock:2,reserved:0,is_active:true}]};
const frame={...pkg,id:'frame',sku:'FRAME-001',name:'Frame QA',product_type:'frame'};
const lens={...pkg,id:'lens',sku:'LENS-001',name:'Lensa QA',product_type:'lens'};
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
  await page.addInitScript(()=>{
   window.qaCameraCalls=0;window.qaStopped=0;
   Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:async()=>{
    window.qaCameraCalls++;const source=document.createElement('canvas');source.width=640;source.height=480;
    source.getContext('2d').fillRect(0,0,640,480);const stream=source.captureStream(10);
    stream.getTracks().forEach(track=>{const stop=track.stop.bind(track);track.stop=()=>{window.qaStopped++;stop();};});return stream;
   }}});
  });
  await page.route('**/api/**',async route=>{
   const req=route.request(),url=new URL(req.url()),endpoint=url.pathname.replace(/^\/api/,'');
   if(req.method()!=='GET'){writes.push({endpoint,body:req.postDataJSON()});}
   if(endpoint==='/products') queries.push(Object.fromEntries(url.searchParams));
   let data={ok:true,categories:[],brands:[],games:[],pages:[],items:[],count:0};
   if(endpoint==='/auth/me') data={user:{user_id:'admin',name:'QA Admin',email:'qa@example.com',role:'admin'}};
   if(endpoint==='/settings/whatsapp') data={enabled:false};
   if(endpoint==='/admin/categories'||endpoint==='/categories') data={categories};
   if(endpoint==='/admin/brands') data={brands:[{id:'brand',name:'Leinz',slug:'leinz',is_active:true}]};
   if(endpoint==='/admin/products') data={products:[frame,pkg,lens],total:3};
   if(endpoint==='/admin/try-on-assets'){
    if(req.method()==='POST'){
     const body=req.postDataJSON();assets.push({...body,id:'asset-pkg',product_name:pkg.name,product_slug:pkg.slug});
     data={ok:true,asset:assets[0]};
    }else data={assets};
   }
   if(endpoint==='/products/package-qa')data={product:{...pkg,supports_try_on:true},reviews:[],related:[],breadcrumb:[]};
   if(endpoint==='/products/pkg/try-on')data={assets:assets.filter(a=>a.status==='published')};
   if(endpoint==='/try-on/catalog')data={products:[{...pkg,try_on_assets:assets},{...frame,try_on_assets:[{...assets[0],id:'asset-frame',product_id:'frame'}]}],next_offset:null};
   await route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
  });
  const origin=`http://127.0.0.1:${server.address().port}`;
  await page.goto(origin+'/virtual-try-on');await page.getByTestId('try-on-stage').waitFor();
  for(const width of [1280,1920,2560]){
   await page.setViewportSize({width,height:1000});
   const bounds=await page.evaluate(()=>{
    const rect=selector=>{const r=document.querySelector(selector).getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width};};
    return {viewport:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,stage:rect('[data-testid="try-on-stage"]'),video:rect('video'),catalog:rect('.vto-catalog'),details:rect('#vto-product-details'),fit:getComputedStyle(document.querySelector('video')).objectFit};
   });
   assert(Math.abs(bounds.stage.left)<1);assert(Math.abs(bounds.stage.width-bounds.viewport)<1);
   assert(Math.abs(bounds.video.width-bounds.stage.width)<1);assert.equal(bounds.fit,'cover');
   assert(bounds.catalog.right<=bounds.stage.right+1);assert(bounds.catalog.bottom<=bounds.details.top+1);
   assert(bounds.scroll<=bounds.viewport+1);report['width'+width]=true;
  }
  await page.screenshot({path:path.join(__dirname,'vto-fullwidth-desktop.png')});
  await page.getByTestId('try-on-camera').click();await page.waitForFunction(()=>!!document.querySelector('video')?.srcObject);
  await page.evaluate(()=>{window.qaVideo=document.querySelector('video');});
  await page.getByRole('button',{name:/Frame QA/}).click();
  assert(await page.evaluate(()=>window.qaVideo===document.querySelector('video')));
  assert.equal(await page.evaluate(()=>window.qaCameraCalls),1);assert.equal(await page.evaluate(()=>window.qaStopped),0);report.cameraPreserved=true;
  await page.setViewportSize({width:390,height:844});
  const mobile=await page.getByTestId('try-on-stage').boundingBox();
  assert(Math.abs(mobile.x)<1&&Math.abs(mobile.width-390)<1&&Math.abs(mobile.height-844)<1);
  await page.screenshot({path:path.join(__dirname,'vto-fullwidth-mobile.png')});report.mobileFullscreen=true;
  assert.deepEqual(errors,[]); report.browserErrors=errors;report.ok=true;
  await fs.writeFile(path.join(__dirname,'vto-fullwidth-browser-report.json'),JSON.stringify(report,null,2)); console.log(JSON.stringify(report));
 } finally {await browser?.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
