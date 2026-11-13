/* ARCHIVED: this acceptance script targets the retired local-vault entry from release v5.
 * It is preserved as historical evidence, not an active test for the customer-integrated entry.
 * Run meowsurement-customer-browser.cjs for the current production flow.
 */
/* Production-build browser regression using only synthetic patients.
 * Requires Playwright. Set OPTIFIT_BROWSER_EXECUTABLE for a system Chromium.
 * All screenshots/downloads go to OPTIFIT_QA_DIR (default OS temporary folder).
 */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const {chromium} = require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright') : 'playwright');
const build = path.resolve(process.env.OPTIFIT_BUILD_DIR || path.join(__dirname,'../build'));
const output = process.env.OPTIFIT_QA_DIR || fs.mkdtempSync(path.join(os.tmpdir(),'optifit-qa-'));
fs.mkdirSync(output,{recursive:true});
const mime = {'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json','.webmanifest':'application/manifest+json','.jpg':'image/jpeg','.png':'image/png','.ttf':'font/ttf'};
const results=[], errors=[], requests=[];
let browser, context, page, base, server;
const secret='Synthetic-QA-Only-2026!';
const launchOptions={headless:true,...(process.env.OPTIFIT_BROWSER_EXECUTABLE?{executablePath:process.env.OPTIFIT_BROWSER_EXECUTABLE}:{}),args:['--no-sandbox','--no-zygote','--single-process','--disable-dev-shm-usage','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']};
async function test(name,run) {
  const started=Date.now();
  try { const detail=await run(); results.push({name,status:'passed',durationMs:Date.now()-started,detail}); console.log('PASS '+name); }
  catch(error) { results.push({name,status:'failed',error:error.message}); console.error('FAIL '+name+': '+error.message); if(page) { await page.screenshot({path:path.join(output,'failure.png'),fullPage:true}).catch(()=>{}); fs.writeFileSync(path.join(output,'failure.txt'),await page.locator('body').innerText().catch(()=>'')); } throw error; }
}
async function field(label,value,scope=page) { await scope.getByLabel(label,{exact:true}).fill(String(value)); }
async function unlock(username) {
  await page.getByLabel('Username lokal',{exact:true}).selectOption(username);
  await field('PIN atau frasa sandi',secret);
  await page.getByRole('button',{name:'Buka kunci',exact:true}).click();
  await page.getByRole('heading',{name:'Pasien',exact:true}).waitFor();
}
async function openSession() {
  await page.getByRole('button',{name:'Riwayat',exact:true}).click();
  await page.locator('.of-session-row').first().click();
  await page.getByRole('button',{name:'4. Hasil & review',exact:true}).click();
}
async function exportReport(format,name) {
  await page.getByRole('button',{name:'Ekspor / cetak laporan',exact:true}).click();
  const dialog=page.getByRole('dialog');
  await dialog.getByLabel('Format laporan',{exact:true}).selectOption(format);
  assert.equal(await dialog.getByRole('button',{name:'Buat dan unduh laporan'}).isEnabled(),false);
  await dialog.getByRole('checkbox',{name:/Saya mengonfirmasi ekspor data pasien ini/}).check();
  const pending=page.waitForEvent('download');
  await dialog.getByRole('button',{name:'Buat dan unduh laporan'}).click();
  const download=await pending; const target=path.join(output,name);
  await download.saveAs(target); await dialog.waitFor({state:'hidden'});
  return target;
}
async function rawStorage() {
  return page.evaluate(async()=>{
    const db=await new Promise((resolve,reject)=>{const q=indexedDB.open('optifit-meowsurement-v1');q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error);});
    const result={}; await Promise.all(['meta','state','photos'].map(name=>new Promise((resolve,reject)=>{
      const tx=db.transaction(name,'readonly'),q=tx.objectStore(name).getAll();
      tx.oncomplete=()=>{result[name]=q.result;resolve();};tx.onerror=()=>reject(tx.error);
    }))); db.close(); return result;
  });
}
(async()=>{
  server=http.createServer((req,res)=>{
    const url=new URL(req.url,'http://localhost');
    if(url.pathname.startsWith('/api/')) {res.writeHead(503,{'content-type':'application/json'});res.end('{"detail":"No API in offline module fixture"}');return;}
    let requested=path.resolve(build,'.'+decodeURIComponent(url.pathname));
    if(!requested.startsWith(build+path.sep) && requested!==build){res.writeHead(403);res.end();return;}
    if(!fs.existsSync(requested)||fs.statSync(requested).isDirectory()) requested=path.join(build,'index.html');
    res.writeHead(200,{'content-type':mime[path.extname(requested)]||'application/octet-stream','cache-control':'no-store','X-Content-Type-Options':'nosniff'});
    fs.createReadStream(requested).pipe(res);
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  base='http://127.0.0.1:'+server.address().port;
  browser=await chromium.launch(launchOptions);
  context=await browser.newContext({viewport:{width:1365,height:1000},permissions:['camera'],acceptDownloads:true});
  await context.addInitScript(()=>{
    window.__qaStreams=[];
    const original=navigator.mediaDevices?.getUserMedia.bind(navigator.mediaDevices);
    if(original) navigator.mediaDevices.getUserMedia=async constraints=>{const stream=await original(constraints);window.__qaStreams.push(stream);return stream;};
  });
  page=await context.newPage(); page.setDefaultTimeout(20000);
  page.on('pageerror',error=>errors.push(error.message)); context.on('request',req=>requests.push({url:req.url(),method:req.method()}));
  await test('Private entry loads without API, analytics or third-party assets',async()=>{
    await page.goto(base+'/meowsurement/'); await page.getByRole('heading',{name:'Siapkan ruang kerja'}).waitFor();
    assert.equal(requests.filter(r=>!r.url.startsWith(base)).length,0);
    assert.equal(requests.filter(r=>new URL(r.url).pathname.startsWith('/api/')).length,0);
    assert.equal(await page.locator('a[href*="wa.me"]').count(),0);
    await page.screenshot({path:path.join(output,'setup-desktop.png'),fullPage:true});
  });
  await test('Native IndexedDB vault, separate reviewer and synthetic patient',async()=>{
    await field('Nama optik / organisasi','Optik QA Sintetis'); await field('Nama administrator','Admin QA');
    await field('Username lokal','qa_admin'); await field('PIN atau frasa sandi',secret); await field('Ulangi PIN atau frasa sandi',secret);
    await page.getByRole('button',{name:'Buat ruang kerja terenkripsi'}).click();
    await page.getByRole('heading',{name:'Pasien',exact:true}).waitFor();
    await page.getByRole('button',{name:'Pengaturan',exact:true}).click();
    await page.getByRole('button',{name:'Tambah pengguna',exact:false}).click();
    const dialog=page.getByRole('dialog'); await field('Nama pengguna','Reviewer QA',dialog);await field('Username lokal','qa_reviewer',dialog);
    await dialog.getByLabel('Peran pengguna',{exact:true}).selectOption('reviewer'); await field('PIN / frasa sandi',secret,dialog); await field('Ulangi kredensial',secret,dialog);
    await dialog.getByRole('button',{name:'Simpan pengguna'}).click(); await dialog.waitFor({state:'hidden'});
    await page.getByRole('button',{name:'Pasien',exact:true}).click();await page.getByRole('button',{name:'Tambah pasien',exact:true}).click();
    await field('Nama lengkap pasien','Pasien Sintetis QA');await field('Tanggal pemeriksaan','2026-11-09');
    await page.getByRole('button',{name:'Simpan pasien',exact:true}).click();
    await page.getByRole('heading',{name:'Pasien Sintetis QA',exact:true}).waitFor();
    const raw=JSON.stringify(await rawStorage());
    for(const sensitive of ['Pasien Sintetis QA','Admin QA','Optik QA Sintetis',secret]) assert.equal(raw.includes(sensitive),false);
    return {encryptedPatient:true,localRoles:true};
  });
  await test('Manual prescription, unequal PD and original revision survive encrypted round-trip',async()=>{
    await page.getByRole('button',{name:'Sesi baru',exact:true}).click();
    const dialog=page.getByRole('dialog');
    await field('Mata Kanan (OD) SPH (D)',-1.25,dialog);await field('Mata Kanan (OD) CYL (D)',-0.5,dialog);await field('Mata Kanan (OD) Axis (°)',90,dialog);
    await field('Mata Kiri (OS) SPH (D)',0,dialog);await field('Mata Kiri (OS) CYL (D)',0,dialog);
    await field('A — lebar lens box (mm)',50,dialog);await field('B — tinggi lens box (mm)',38,dialog);await field('DBL — jarak lens box (mm)',18,dialog);await field('ED — diameter efektif (mm)',55,dialog);
    await dialog.getByRole('button',{name:'Lihat transpose'}).click();
    assert.match(await dialog.innerText(),/SPH -1,75 · CYL 0,5 · Axis 180/);
    await dialog.getByRole('button',{name:'Simpan draft sesi'}).click();await dialog.waitFor({state:'hidden'});
    await page.getByRole('button',{name:'4. Hasil & review',exact:true}).click();
    assert.equal(await page.getByRole('button',{name:'Ajukan review',exact:true}).isEnabled(),false);
    await page.getByRole('button',{name:'Catat hasil alat / metode referensi',exact:true}).click();
    const manual=page.getByRole('dialog');
    for(let i=1;i<=3;i++){await field('Pembacaan '+i+' kanan',[31,31.1,30.9][i-1],manual);await field('Pembacaan '+i+' kiri',[33,33.1,32.9][i-1],manual);}
    await field('Identitas alat dan metode referensi','QA instrument fixture; synthetic values only',manual);
    await manual.getByRole('checkbox',{name:/Saya mengonfirmasi pembacaan/}).check();await manual.getByRole('checkbox',{name:/Posisi kepala dan arah pandang/}).check();
    await manual.getByRole('button',{name:'Simpan pembacaan sebagai revisi'}).click();await manual.waitFor({state:'hidden'});
    assert.equal(await page.getByRole('button',{name:'Ajukan review',exact:true}).isEnabled(),true);
    await page.getByRole('button',{name:'Ajukan review',exact:true}).click();
    await page.getByRole('button',{name:'Periksa & beri keputusan'}).click();
    assert.match(await page.getByRole('dialog').innerText(),/Reviewer harus berbeda/);
    await page.getByRole('dialog').getByRole('button',{name:'Batal',exact:true}).click();
    await page.getByRole('button',{name:'Kunci',exact:true}).click();
    assert.equal(await page.getByText('Pasien Sintetis QA',{exact:true}).count(),0);
    await unlock('qa_reviewer'); await openSession();
    await page.getByRole('button',{name:'Periksa & beri keputusan'}).click();
    const review=page.getByRole('dialog');await review.getByLabel('Keputusan review').selectOption('approved');
    await field('Catatan reviewer','Synthetic QA: interface and policy test only.',review);
    await field('Alat / metode pembanding','QA reference instrument fixture',review);await field('Nomor protokol verifikasi','QA-SOFTWARE-ONLY',review);
    await field('Hasil perbandingan dan dasar keputusan','Synthetic fixture; no clinical accuracy outcome asserted.',review);
    await review.getByRole('checkbox',{name:/Saya telah melakukan verifikasi profesional/}).check();
    await review.getByRole('button',{name:'Simpan keputusan review'}).click();await review.waitFor({state:'hidden'});
    assert.match(await page.locator('.of-page-heading').innerText(),/Disetujui/);
  });
  await test('JSON and CSV retain scope, provenance, independent PD and no image bytes',async()=>{
    const filename=await exportReport('json','approved.json'), report=JSON.parse(fs.readFileSync(filename,'utf8'));
    assert.equal(report.status,'approved');assert.equal(report.clinical.results.distance_pd.values.rightMm,31);assert.equal(report.clinical.results.distance_pd.values.leftMm,33);assert.equal(report.photoIncluded,false);
    assert.equal(report.clinical.prescription.od.sph,-1.25);assert.equal(report.clinical.prescription.od.cyl,-0.5);assert.ok(report.reviewer.id!==report.operator.id);assert.ok(!JSON.stringify(report).includes('data:image'));
    const csv=fs.readFileSync(await exportReport('csv','approved.csv'),'utf8');assert.match(csv,/Jarak Pupil Jauh kanan/); assert.match(csv,/31 mm/);
    await page.screenshot({path:path.join(output,'results-desktop.png'),fullPage:true});
    return {status:report.status,rightMm:31,leftMm:33,photoIncluded:false};
  });
  await test('Offline reload, encrypted unlock and real PDF generation use cached local assets',async()=>{
    await page.waitForFunction(()=>navigator.serviceWorker.controller!==null);
    const cacheURLs=await page.evaluate(async()=>{const urls=[];for(const key of await caches.keys())for(const req of await(await caches.open(key)).keys())urls.push(req.url);return urls;});
    assert.ok(cacheURLs.length>5); assert.ok(cacheURLs.every(url=>!url.includes('/api/')&&!url.startsWith('blob:')));
    await context.setOffline(true);await page.reload();await page.getByRole('heading',{name:'Buka ruang kerja'}).waitFor();await unlock('qa_reviewer');await openSession();
    if(process.env.OPTIFIT_PDF_OPERATION_MARKER){
      const marker=spawnSync(process.execPath,[process.env.OPTIFIT_PDF_OPERATION_MARKER,'--operation-kind','create','--expected-output-count','1','--output-format','pdf'],{encoding:'utf8'});
      if(marker.status!==0)throw new Error('PDF operation marker failed: '+marker.stderr);
    }
    const pdf=fs.readFileSync(await exportReport('pdf','approved.pdf'));
    assert.ok(pdf.subarray(0,5).toString()==='%PDF-');assert.ok(pdf.length>20000);
    await context.setOffline(false);return {cachedStaticAssets:cacheURLs.length,pdfBytes:pdf.length};
  });
  await test('Responsive light/dark results layout has no horizontal page overflow',async()=>{
    await page.setViewportSize({width:390,height:844});
    for(let i=0;i<2;i++){
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
      await page.screenshot({path:path.join(output,'results-mobile-'+i+'.png'),fullPage:true});
      await page.getByRole('button',{name:/Gunakan tema/}).click();
    }
    await page.setViewportSize({width:1365,height:1000});
  });
  await test('Changing frame invalidates current results and preserves approved historical revision',async()=>{
    await page.getByRole('button',{name:'Kunci',exact:true}).click();await unlock('qa_admin');await openSession();
    await page.getByRole('button',{name:'1. Data',exact:true}).click();
    await field('A — lebar lens box (mm)',52);await field('Alasan revisi data sesi','Synthetic test: changed frame measurement.');
    await page.getByRole('button',{name:'Simpan sebagai revisi baru'}).click();await page.getByRole('button',{name:'4. Hasil & review',exact:true}).click();
    assert.equal(await page.getByRole('button',{name:'Ajukan review',exact:true}).isEnabled(),false);
    const revisions=page.getByLabel('Versi data yang ditampilkan');const options=await revisions.locator('option').evaluateAll(nodes=>nodes.map(n=>n.value));assert.ok(options.length>=3);
    await revisions.selectOption(options[1]);const historical=JSON.parse(fs.readFileSync(await exportReport('json','historical.json'),'utf8'));
    assert.equal(historical.historicalRevision,true);assert.equal(historical.status,'approved');assert.equal(historical.clinical.frame.a,50);
    await revisions.selectOption(options.at(-1));return {revisions:options.length};
  });
  await test('Camera requires consent, stores encrypted burst, and stops tracks on lock',async()=>{
    await page.getByRole('button',{name:'2. Persiapan',exact:true}).click();await page.getByRole('button',{name:'Semua persiapan siap'}).click();
    const save=page.getByRole('button',{name:'Simpan persiapan dan persetujuan'});assert.equal(await save.isEnabled(),false);
    await page.getByRole('checkbox',{name:/Pasien menyetujui pengambilan/}).check();await save.click();
    await page.getByRole('button',{name:'Buka kamera',exact:true}).click();
    await page.getByTestId('optifit-camera-start').click();
    await page.waitForFunction(()=>document.querySelector('video')?.videoWidth>0);
    const buttons=await page.getByRole('button').allTextContents();fs.writeFileSync(path.join(output,'camera-buttons.json'),JSON.stringify(buttons));
    await page.getByTestId('optifit-camera-capture').click();
    await page.getByAltText('Sampel pengukuran 1').waitFor();
    const raw=await rawStorage();assert.ok(raw.photos.length>=1);const serialized=JSON.stringify(raw.photos);assert.ok(!serialized.includes('data:image'));assert.ok(!serialized.includes('Pasien Sintetis QA'));
    await page.getByRole('button',{name:/Ambil ulang dengan kamera/}).click();await page.getByTestId('optifit-camera-start').click();await page.waitForFunction(()=>document.querySelector('video')?.videoWidth>0);
    await page.getByRole('button',{name:'Kunci',exact:true}).click();
    await page.waitForFunction(()=>window.__qaStreams.every(stream=>stream.getTracks().every(track=>track.readyState==='ended')));
    return {encryptedPhotos:raw.photos.length};
  });
  await test('Encrypted backup restores a native vault and rejects the wrong passphrase',async()=>{
    await unlock('qa_admin');await page.getByRole('button',{name:'Pengaturan',exact:true}).click();await page.getByRole('button',{name:'Buat cadangan terenkripsi'}).click();
    const dialog=page.getByRole('dialog');await field('Frasa sandi cadangan',secret,dialog);await field('Ulangi frasa sandi cadangan',secret,dialog);await dialog.getByRole('checkbox',{name:/Saya mengonfirmasi ekspor cadangan/}).check();
    const pending=page.waitForEvent('download');await dialog.getByRole('button',{name:'Enkripsi dan unduh cadangan'}).click();const backup=await pending;const filename=path.join(output,'encrypted-backup.json');await backup.saveAs(filename);
    assert.ok(!fs.readFileSync(filename,'utf8').includes('Pasien Sintetis QA'));
    await browser.close();browser=await chromium.launch(launchOptions);context=await browser.newContext({acceptDownloads:true});context.on('request',req=>requests.push({url:req.url(),method:req.method()}));page=await context.newPage();page.setDefaultTimeout(20000);page.on('pageerror',error=>errors.push(error.message));
    await page.goto(base+'/meowsurement/');await page.getByRole('button',{name:'Pulihkan cadangan terenkripsi'}).click();
    const restore=page.getByRole('dialog');await restore.getByLabel('Berkas cadangan',{exact:true}).setInputFiles(filename);await field('Frasa sandi cadangan','Wrong-Secret-For-QA!',restore);await restore.getByRole('checkbox',{name:/Saya memilih untuk memulihkan/}).check();
    await restore.getByRole('button',{name:'Periksa dan pulihkan'}).click();await restore.getByRole('alert').waitFor();
    await field('Frasa sandi cadangan',secret,restore);await restore.getByRole('button',{name:'Periksa dan pulihkan'}).click();await restore.waitFor({state:'hidden'});
    await unlock('qa_admin');assert.match(await page.locator('main').innerText(),/Pasien Sintetis QA/);
  });
  await test('No uncaught browser errors or clinical network uploads',async()=>{
    const network=requests.filter(r=>/^https?:/.test(r.url));
    assert.deepEqual(errors,[]);assert.ok(network.every(r=>r.method==='GET'));assert.equal(network.filter(r=>!r.url.startsWith(base)).length,0);assert.equal(network.filter(r=>new URL(r.url).pathname.startsWith('/api/')).length,0);
    return {uncaughtErrors:errors.length,requests:requests.length};
  });
})().catch(error=>{process.exitCode=1;console.error(error.stack);}).finally(async()=>{
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({results,errors,requests},null,2));
  if(browser)await browser.close().catch(()=>{});if(server)await new Promise(resolve=>server.close(resolve));
  console.log('QA output: '+output);
});
