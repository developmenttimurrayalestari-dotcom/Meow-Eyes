from pathlib import Path
p=Path('private/vto-package-browser-smoke.cjs').read_text(encoding='utf-8')
p=p.replace('const assets=[];',"const assets=[{id:'asset-pkg',product_id:'pkg',asset_type:'image',status:'published',source_url:'/games/space-war/meow-pilot.png',scale:1}];")
p=p.replace("if(endpoint==='/try-on/catalog')data={products:assets.length?[{...pkg,try_on_assets:assets}]:[],next_offset:null};", "if(endpoint==='/try-on/catalog')data={products:[{...pkg,try_on_assets:assets},{...frame,try_on_assets:[{...assets[0],id:'asset-frame',product_id:'frame'}]}],next_offset:null};")
insertion="""  await page.addInitScript(()=>{
   window.qaCameraCalls=0;window.qaStopped=0;
   Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:async()=>{
    window.qaCameraCalls++;const source=document.createElement('canvas');source.width=640;source.height=480;
    source.getContext('2d').fillRect(0,0,640,480);const stream=source.captureStream(10);
    stream.getTracks().forEach(track=>{const stop=track.stop.bind(track);track.stop=()=>{window.qaStopped++;stop();};});return stream;
   }}});
  });
"""
p=p.replace("  await page.route('**/api/**'",insertion+"  await page.route('**/api/**'")
a=p.index("  await page.goto(origin+");b=p.index('  assert.deepEqual(errors,[]);',a)
p=p[:a]+"""  await page.goto(origin+'/virtual-try-on');await page.getByTestId('try-on-stage').waitFor();
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
"""+p[b:]
p=p.replace('vto-package-browser-report','vto-fullwidth-browser-report')
Path('private/vto-fullwidth-browser-smoke.cjs').write_text(p,encoding='utf-8')
print('Full-width VTO browser check prepared')
