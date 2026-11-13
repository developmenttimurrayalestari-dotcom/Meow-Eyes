/* Real HTTP browser acceptance for the integrated customer/profile/catalog flow.
 * Run a production build first. Requires backend test dependencies + Playwright.
 * MEOW_QA_PYTHON points at the backend environment; MEOW_QA_BROWSER is optional.
 * Server and browser are spawned together, including in isolated network sandboxes.
 */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {chromium} = require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES, 'playwright') : 'playwright');
const project = path.resolve(__dirname, '../..');
const output = process.env.MEOW_QA_DIR || fs.mkdtempSync(path.join(os.tmpdir(), 'meow-customer-acceptance-'));
const password = 'Synthetic-Customer-QA-2026!';
const base = 'http://127.0.0.1:' + (process.env.MEOW_QA_PORT || '8829');
const results = [], pageErrors = [], requestedURLs = [];
let backend, browser, customer, admin, page, fixture, sessionId, backendLog = '';
fs.mkdirSync(output, {recursive:true});
for(const file of ['failure.png','failure.txt']) fs.rmSync(path.join(output,file),{force:true});
const screenshot = async name => page.screenshot({path:path.join(output, name + '.png'), fullPage:true, animations:'disabled'});
async function test(name, run) {
  const start = Date.now();
  try { const detail = await run(); results.push({name, status:'passed', durationMs:Date.now()-start, detail}); console.log('PASS ' + name); }
  catch (error) {
    results.push({name, status:'failed', error:error.message, durationMs:Date.now()-start});
    if(page) { await screenshot('failure').catch(()=>{}); fs.writeFileSync(path.join(output,'failure.txt'), await page.locator('body').innerText().catch(()=>'')); }
    throw error;
  }
}
async function waitReady() {
  for(let n=0;n<160;n++) {
    try { const response = await fetch(base+'/qa/ready'); if(response.ok) return response.json(); } catch {}
    if(backend.exitCode !== null) throw new Error('Fixture exited: ' + backendLog.slice(-5000));
    await new Promise(resolve=>setTimeout(resolve, 250));
  }
  throw new Error('Fixture not ready: ' + backendLog.slice(-5000));
}
async function api(method, endpoint, data, active=page) {
  return active.evaluate(async ({method, endpoint, data}) => {
    const response = await fetch('/api'+endpoint, {method, credentials:'include', headers:{'Content-Type':'application/json', Authorization:'Bearer '+localStorage.getItem('meow_token')}, body:data === undefined ? undefined : JSON.stringify(data)});
    const body = await response.json();
    return {status:response.status, body};
  }, {method, endpoint, data});
}
async function responseAfter(action, endpoint, method, active=page) {
  const pending = active.waitForResponse(response => new URL(response.url()).pathname === '/api'+endpoint && response.request().method() === method);
  await action();
  const response = await pending, body = await response.json();
  return {status:response.status(), body};
}
async function createContext() {
  const context = await browser.newContext({viewport:{width:1365,height:1000}});
  await context.route('**/*', route => route.request().url().startsWith(base) || /^(?:blob|data):/.test(route.request().url()) ? route.continue() : route.abort());
  context.on('request', request => requestedURLs.push(request.url()));
  context.on('page', tab => { tab.setDefaultTimeout(20000); tab.on('pageerror', error => pageErrors.push(error.message)); });
  return context;
}
async function login(email, returnTo, active=page) {
  await active.goto(base+'/login?returnTo='+encodeURIComponent(returnTo));
  await active.getByTestId('login-email').fill(email);
  await active.getByTestId('login-password').fill(password);
  await active.getByTestId('login-submit-btn').click();
}
async function fill(label, value, active=page) { await active.getByLabel(label,{exact:true}).fill(String(value)); }
function assertNoLocalAccounts(text) {
  for(const forbidden of ['Siapkan ruang kerja','Username lokal','Nama optik / organisasi','Tambah pasien','Buat ruang kerja terenkripsi']) assert.equal(text.includes(forbidden),false,forbidden);
}
(async()=>{
  backend = spawn(process.env.MEOW_QA_PYTHON || 'python', [path.join(__dirname,'meowsurement-server.py')], {
    cwd:path.join(project,'backend'), env:{...process.env, MEOW_QA_PASSWORD:password}, stdio:['ignore','pipe','pipe'],
  });
  backend.stdout.on('data', data=>backendLog+=data);
  backend.stderr.on('data', data=>backendLog+=data);
  backend.on('error', error=>backendLog+=error.stack);
  fixture = await waitReady();
  browser = await chromium.launch({headless:true, ...(process.env.MEOW_QA_BROWSER ? {executablePath:process.env.MEOW_QA_BROWSER} : {}), args:['--no-sandbox','--no-zygote','--disable-dev-shm-usage']});
  customer = await createContext(); page = await customer.newPage();
  const first = fixture.variants[0], large = fixture.variants[1];
  const target = '/meowsurement/?product_id='+fixture.frame_id+'&variant_id='+large.id;
  await test('Unauthenticated Meowsurement uses website login and incomplete customer profile; no PIN or local accounts', async()=>{
    await page.goto(base+target);
    await page.waitForURL(url=>url.pathname==='/login');
    assert.equal(new URL(page.url()).searchParams.get('returnTo'),target);
    await page.getByTestId('login-email').fill(fixture.customer_email);
    await page.getByTestId('login-password').fill(password);
    await page.getByTestId('login-submit-btn').click();
    await page.waitForURL(url=>url.pathname==='/profile');
    await page.getByTestId('customer-profile-form').waitFor();
    assert.equal(new URL(page.url()).searchParams.get('returnTo'),target);
    const account = await api('GET','/auth/me');
    assert.equal(account.body.user.has_pin,false);
    assert.equal(await page.getByTestId('continue-meowsurement-disabled').isDisabled(),true);
    assertNoLocalAccounts(await page.locator('body').innerText());
    await screenshot('customer-profile-required');
    return {profileGate:true, originalTargetPreserved:true, websiteCustomerWithoutPin:true};
  });
  await test('Incomplete prescription is a draft; literal zero survives; nonzero CYL requires AXIS', async()=>{
    await fill('Nomor telepon','081234567890'); await fill('Tanggal lahir','1994-06-12');
    await fill('Tanggal resep / pemeriksaan','2025-11-01');
    await fill('Mata kanan (OD) SPH (D)','0'); await fill('Mata kanan (OD) CYL (D)','0');
    await fill('Mata kiri (OS) SPH (D)','-1.25'); await fill('Mata kiri (OS) CYL (D)','-0.50');
    const draft = await responseAfter(()=>page.getByTestId('save-customer-profile').click(),'/customer/profile','PUT');
    assert.equal(draft.status,200); assert.equal(draft.body.ready,false);
    assert.ok(draft.body.missing_fields.includes('prescription.os.axis'));
    assert.equal(draft.body.profile.prescription.od.sph,0); assert.equal(draft.body.profile.prescription.od.axis,null);
    assert.equal(await page.getByTestId('continue-meowsurement-disabled').isDisabled(),true);
    await fill('Mata kiri (OS) AXIS (°)','90'); await fill('PD total (mm)','63');
    const saved = await responseAfter(()=>page.getByTestId('save-customer-profile').click(),'/customer/profile','PUT');
    assert.equal(saved.status,200); assert.equal(saved.body.ready,true);
    assert.equal(saved.body.profile.prescription.od.cyl,0); assert.equal(saved.body.profile.prescription.od.add,null);
    await page.getByTestId('continue-meowsurement').waitFor();
    assert.equal(await page.getByTestId('continue-meowsurement').getAttribute('href'),target);
    await page.reload(); await page.getByTestId('customer-profile-form').waitFor();
    assert.equal(await page.getByLabel('Mata kanan (OD) SPH (D)',{exact:true}).inputValue(),'0');
    assert.equal(await page.getByLabel('PD total (mm)',{exact:true}).inputValue(),'63');
    await screenshot('customer-profile-prescription');
    return {zeroPreserved:true, unknownAdd:null, ready:true, version:saved.body.profile.version};
  });
  admin = await createContext(); const adminPage = await admin.newPage();
  await test('Existing web admin saves typed default geometry and size-specific variant override', async()=>{
    page = adminPage; await login(fixture.admin_email,'/admin/products');
    await page.getByTestId('frame-specification-'+fixture.frame_id).click();
    await page.getByTestId('default-frame-a').waitFor();
    for(const [key,value] of Object.entries({a:52,b:38,dbl:18,ed:58,temple_length:140})) await page.getByTestId('default-frame-'+key).fill(String(value));
    const baseFields = page.getByTestId('default-frame-a').locator('xpath=ancestor::fieldset[1]');
    await baseFields.getByRole('checkbox',{name:/dikonfirmasi simetris/}).check();
    await page.getByTestId('default-frame-enabled').check();
    const variantRow = page.getByTestId('frame-variant-spec-'+large.id);
    await variantRow.getByRole('checkbox',{name:/Gunakan spesifikasi dasar/}).uncheck();
    for(const [key,value] of Object.entries({a:56,b:40,ed:64})) await page.getByTestId('variant-'+large.id+'-'+key).fill(String(value));
    const result = await responseAfter(()=>page.getByTestId('save-frame-specification').click(),'/admin/products/'+fixture.frame_id+'/frame-specification','PUT');
    assert.equal(result.status,200);
    assert.equal(result.body.specification.a,52);
    const inherited = result.body.variants.find(v=>v.variant_id===first.id), override = result.body.variants.find(v=>v.variant_id===large.id);
    assert.equal(inherited.inherit_default,true); assert.equal(inherited.effective_specification.a,52);
    assert.equal(override.inherit_default,false); assert.equal(override.effective_specification.a,56);
    await screenshot('admin-frame-default-and-variant');
    await page.getByRole('button',{name:'Tutup',exact:true}).click();
    return {defaultA:52,overrideA:56,version:result.body.version};
  });
  await test('Product detail reflects effective variant geometry and carries frame selection into Meowsurement', async()=>{
    page = customer.pages()[0]; await page.goto(base+'/products/'+fixture.frame_slug);
    const currentAccount = await api('GET','/auth/me');
    assert.equal(currentAccount.body.user.user_id,fixture.customer_id,'Customer browser session must remain isolated from the admin browser session');
    await page.getByTestId('variant-'+first.sku).click();
    await page.getByTestId('open-meowsurement').waitFor();
    assert.equal(await page.getByTestId('product-frame-spec-a').innerText(),'52 mm');
    await page.getByTestId('variant-'+large.sku).click();
    assert.equal(await page.getByTestId('product-frame-spec-a').innerText(),'56 mm');
    assert.equal(await page.getByTestId('open-meowsurement').getAttribute('href'),target);
    await page.getByTestId('open-meowsurement').click();
    await page.getByRole('heading',{name:'Meowsurement saya',exact:true}).waitFor();
    assertNoLocalAccounts(await page.locator('body').innerText());
    assert.equal(await page.getByTestId('rx-od-sph').innerText(),'0');
    assert.equal(await page.getByTestId('rx-od-cyl').innerText(),'0');
    assert.equal(await page.getByTestId('rx-od-add').innerText(),'—');
    assert.equal(await page.getByLabel('Varian frame').inputValue(),large.id);
    assert.match(await page.getByTestId('selected-frame-spec').innerText(),/56 mm/);
    await screenshot('customer-meowsurement-autofill');
    return {zeroDisplayed:true,variantPreserved:true,noLocalOnboarding:true};
  });
  await test('Session is created through real API with server-owned profile and frame snapshots', async()=>{
    const result = await responseAfter(()=>page.getByRole('button',{name:'Mulai pengukuran',exact:true}).click(),'/meowsurement/sessions','POST');
    assert.ok([200,201].includes(result.status),JSON.stringify(result));
    sessionId = result.body.session.id;
    const detail = await api('GET','/meowsurement/sessions/'+sessionId);
    assert.equal(detail.status,200);
    assert.equal(detail.body.session.variantId,large.id);
    const revision = detail.body.revisions.find(item=>item.id===detail.body.session.currentRevisionId);
    assert.equal(revision.data.prescription.od.sph,0); assert.equal(revision.data.prescription.os.axis,90);
    assert.equal(revision.data.frame.a,56);
    assert.equal(revision.data.consents.uploadPhotos,false);
    assert.equal(revision.data.consents.capture,false);
    assert.equal(revision.data.consents.thumbnail,false);
    await page.getByRole('button',{name:'2. Persiapan',exact:true}).click();
    assert.equal(await page.getByRole('checkbox',{name:/Simpan juga foto secara privat/}).isChecked(),false);
    assert.equal(await page.getByRole('checkbox',{name:/Saya menyetujui pengambilan gambar/}).isChecked(),false);
    await page.getByRole('button',{name:'1. Profil & frame',exact:true}).click();
    assert.equal(await page.getByTestId('rx-od-sph').innerText(),'0');
    assertNoLocalAccounts(await page.locator('body').innerText());
    await screenshot('customer-session-profile-frame');
    return {sessionId,profileVersion:detail.body.session.profileVersion,frameA:56,variantId:large.id,uploadPhotosDefault:false};
  });
  await test('Preparation, three independent manual PD readings, submission and evidence-bound approval use existing website accounts', async()=>{
    const customerPage = page;
    await page.getByRole('button',{name:'2. Persiapan',exact:true}).click();
    await page.getByRole('button',{name:'Semua persiapan siap',exact:true}).click();
    await page.getByRole('checkbox',{name:/Saya menyetujui pengambilan gambar dan penyimpanan hasil/}).check();
    assert.equal(await page.getByRole('checkbox',{name:/Simpan juga foto secara privat/}).isChecked(),false);
    const preparation = await responseAfter(()=>page.getByRole('button',{name:'Simpan persiapan dan persetujuan',exact:true}).click(),'/meowsurement/sessions/'+sessionId+'/revisions','POST');
    assert.ok([200,201].includes(preparation.status),JSON.stringify(preparation));
    assert.equal(preparation.body.revision.data.consents.uploadPhotos,false);
    await page.getByRole('button',{name:'4. Hasil & review',exact:true}).click();
    assert.equal(await page.getByRole('button',{name:'Ajukan review',exact:true}).isEnabled(),false);
    await page.getByRole('button',{name:'Catat hasil alat / metode referensi',exact:true}).click();
    const readings = page.getByRole('dialog');
    for(let index=0;index<3;index++) {
      await fill('Pembacaan '+(index+1)+' kanan',[31,31.1,30.9][index],readings);
      await fill('Pembacaan '+(index+1)+' kiri',[33,32.9,33.1][index],readings);
    }
    await fill('Identitas alat dan metode referensi','Synthetic QA reference instrument. UI/API contract test only.',readings);
    await readings.getByRole('checkbox',{name:/Saya mengonfirmasi pembacaan masing-masing sisi/}).check();
    await readings.getByRole('checkbox',{name:/Posisi kepala dan arah pandang mengikuti protokol/}).check();
    const measured = await responseAfter(()=>readings.getByRole('button',{name:'Simpan pembacaan sebagai revisi',exact:true}).click(),'/meowsurement/sessions/'+sessionId+'/revisions','POST');
    assert.ok([200,201].includes(measured.status),JSON.stringify(measured));
    await readings.waitFor({state:'hidden'});
    const result = measured.body.revision.data.results.distance_pd;
    assert.equal(result.source,'manual_instrument');
    assert.equal(result.values.rightMm,31); assert.equal(result.values.leftMm,33);
    assert.equal(result.values.binocularMm,64); assert.equal(result.sampleCount,3);
    assert.equal(result.rawReadings.length,3);
    assert.deepEqual(result.rawReadings.map(row=>row.values.rightMm),[31,31.1,30.9]);
    assert.deepEqual(result.rawReadings.map(row=>row.values.leftMm),[33,32.9,33.1]);
    const submitted = await responseAfter(()=>page.getByRole('button',{name:'Ajukan review',exact:true}).click(),'/meowsurement/sessions/'+sessionId+'/submit','POST');
    assert.equal(submitted.status,200,JSON.stringify(submitted));
    assert.ok(['pending_review','needs_verification'].includes(submitted.body.session.status));
    assert.equal(await page.getByRole('button',{name:'Periksa & beri keputusan',exact:true}).count(),0);
    page = adminPage; await page.bringToFront(); await page.goto(base+'/admin/meowsurement');
    await page.getByTestId('open-measurement-review-'+sessionId).click();
    await page.getByRole('button',{name:'4. Hasil & review',exact:true}).click();
    await page.getByRole('button',{name:'Periksa & beri keputusan',exact:true}).click();
    const review = page.getByRole('dialog');
    await review.getByLabel('Keputusan review').selectOption('approved');
    assert.equal(await review.getByRole('button',{name:'Simpan keputusan review',exact:true}).isEnabled(),false);
    await fill('Catatan reviewer','Synthetic browser acceptance; tests software workflow only.',review);
    await fill('Alat / metode pembanding','QA reference instrument fixture',review);
    await fill('Nomor protokol verifikasi','QA-SOFTWARE-CONTRACT-ONLY',review);
    await fill('Hasil perbandingan dan dasar keputusan','Synthetic independent 31 mm / 33 mm readings retained; no clinical accuracy claim.',review);
    await review.getByRole('checkbox',{name:/Saya telah melakukan verifikasi profesional/}).check();
    const approved = await responseAfter(()=>review.getByRole('button',{name:'Simpan keputusan review',exact:true}).click(),'/meowsurement/sessions/'+sessionId+'/reviews','POST');
    assert.equal(approved.status,200,JSON.stringify(approved));
    await review.waitFor({state:'hidden'});
    assert.equal(approved.body.session.status,'approved');
    const decision = approved.body.reviews.find(row=>row.decision==='approved');
    assert.ok(decision);
    assert.ok(decision.reviewerId!==fixture.customer_id,'Reviewer must use a separate existing website account');
    assert.equal(decision.revisionId,approved.body.session.currentRevisionId);
    assert.equal(decision.evidence.professionalVerified,true);
    assert.equal(decision.evidence.protocolId,'QA-SOFTWARE-CONTRACT-ONLY');
    assert.equal(approved.body.revision.data.results.distance_pd.values.leftMm,33);
    assertNoLocalAccounts(await page.locator('body').innerText());
    page = customerPage; await page.bringToFront();
    const persisted = await api('GET','/meowsurement/sessions/'+sessionId);
    assert.equal(persisted.body.session.status,'approved');
    assert.equal(persisted.body.reviews[0].evidence.protocolId,'QA-SOFTWARE-CONTRACT-ONLY');
    return {status:'approved',rightPdMm:31,leftPdMm:33,sampleCount:3,independentWebsiteReviewer:true,requiredEvidence:true,photoUploadEnabled:false};
  });
  await test('Concurrent profile update shows conflict and cannot overwrite saved version or old session snapshot', async()=>{
    await page.goto(base+'/profile?returnTo='+encodeURIComponent(target));
    await page.getByTestId('customer-profile-form').waitFor();
    const stale = await customer.newPage(); await stale.goto(base+'/profile?returnTo='+encodeURIComponent(target));
    await stale.getByTestId('customer-profile-form').waitFor();
    await page.bringToFront(); await fill('Nama lengkap','Customer QA Terbaru');
    await fill('Mata kanan (OD) SPH (D)','-0.75');
    const updated = await responseAfter(()=>page.getByTestId('save-customer-profile').click(),'/customer/profile','PUT');
    assert.equal(updated.status,200);
    await stale.bringToFront(); await fill('Nama lengkap','Perubahan tab lama',stale);
    const rejected = await responseAfter(()=>stale.getByTestId('save-customer-profile').click(),'/customer/profile','PUT',stale);
    assert.equal(rejected.status,409);
    assert.equal(await stale.getByTestId('save-customer-profile').isDisabled(),true);
    assert.equal(await stale.getByLabel('Nama lengkap',{exact:true}).inputValue(),'Perubahan tab lama');
    await stale.getByRole('button',{name:'Muat profil terbaru',exact:true}).click();
    await stale.getByTestId('customer-profile-form').waitFor();
    assert.equal(await stale.getByLabel('Nama lengkap',{exact:true}).inputValue(),'Customer QA Terbaru');
    const old = await api('GET','/meowsurement/sessions/'+sessionId,undefined,stale);
    const revision = old.body.revisions.find(item=>item.id===old.body.session.currentRevisionId);
    assert.equal(revision.data.prescription.od.sph,0);
    assert.equal(revision.data.frame.a,56);
    await stale.close(); await page.bringToFront();
    const catalog = await api('GET','/admin/products/'+fixture.frame_id+'/frame-specification',undefined,adminPage);
    assert.equal(catalog.status,200);
    const typedSpec = spec => Object.fromEntries(['a','b','dbl','ed','temple_length','enabled','symmetric','source_note'].map(key=>[key,spec[key]]));
    const specUpdate = await api('PUT','/admin/products/'+fixture.frame_id+'/frame-specification',{
      expected_version:catalog.body.version,
      specification:{...typedSpec(catalog.body.specification),a:53},
      variants:catalog.body.variants.map(row=>({variant_id:row.variant_id,inherit_default:row.inherit_default,...(row.inherit_default?{}:{specification:{...typedSpec(row.specification),a:57}})})),
    },adminPage);
    assert.equal(specUpdate.status,200);
    await page.goto(base+target); await page.getByRole('heading',{name:'Meowsurement saya',exact:true}).waitFor();
    assert.match(await page.getByTestId('selected-frame-spec').innerText(),/57 mm/);
    await page.reload(); await page.getByRole('heading',{name:'Meowsurement saya',exact:true}).waitFor();
    await page.getByRole('button',{name:'Riwayat saya',exact:true}).click();
    await page.locator('.of-session-row').first().click();
    await page.getByRole('button',{name:'1. Profil & frame',exact:true}).click();
    assert.equal(await page.getByTestId('rx-od-sph').innerText(),'0');
    assert.match(await page.locator('.of-customer-main').innerText(),/56 mm/);
    const persisted = await api('GET','/meowsurement/sessions/'+sessionId);
    assert.equal(persisted.body.revision.data.frame.a,56);
    assert.equal(persisted.body.revision.data.prescription.od.sph,0);
    await screenshot('customer-original-session-after-account-catalog-update');
    return {staleWriteStatus:409,immutableOriginalRx:0,currentProfileRx:-0.75,currentCatalogA:57,originalFrameA:56,realReload:true};
  });
  await test('Existing admin review queue opens customer session without requiring an admin prescription profile', async()=>{
    page = adminPage; await page.bringToFront(); await page.goto(base+'/admin/meowsurement');
    await page.getByLabel('Status pengukuran').selectOption('approved');
    const entry = page.getByTestId('open-measurement-review-'+sessionId);
    await entry.waitFor();
    assert.equal(await entry.getAttribute('href'),'/meowsurement/?review_session='+sessionId);
    await entry.click();
    await page.getByRole('button',{name:'1. Profil & frame',exact:true}).waitFor();
    await page.getByRole('button',{name:'1. Profil & frame',exact:true}).click();
    assert.equal(new URL(page.url()).pathname,'/meowsurement/');
    assert.equal(await page.getByTestId('rx-od-sph').innerText(),'0');
    assertNoLocalAccounts(await page.locator('body').innerText());
    await screenshot('admin-review-existing-web-account');
    return {reviewSession:sessionId,adminProfileNotRequired:true};
  });
  await test('Profile and admin specification editor fit a 390px viewport; customer cannot access catalog admin', async()=>{
    page = customer.pages()[0]; await page.bringToFront(); await page.setViewportSize({width:390,height:844});
    await page.goto(base+'/profile'); await page.getByTestId('customer-profile-form').waitFor();
    const profileWidth = await page.evaluate(()=>({viewport:innerWidth,width:document.documentElement.scrollWidth}));
    assert.ok(profileWidth.width<=profileWidth.viewport+1,JSON.stringify(profileWidth));
    await screenshot('profile-mobile');
    const denied = await api('GET','/admin/products/'+fixture.frame_id+'/frame-specification');
    assert.equal(denied.status,403);
    page = adminPage; await page.bringToFront(); await page.setViewportSize({width:390,height:844});
    await page.goto(base+'/admin/products'); await page.getByTestId('frame-specification-'+fixture.frame_id).click();
    await page.getByTestId('default-frame-a').waitFor();
    const dialogWidth = await page.getByRole('dialog').evaluate(node=>({width:node.getBoundingClientRect().width,scrollWidth:node.scrollWidth,clientWidth:node.clientWidth}));
    assert.ok(dialogWidth.width<=390,JSON.stringify(dialogWidth));
    assert.ok(dialogWidth.scrollWidth<=dialogWidth.clientWidth+1,JSON.stringify(dialogWidth));
    await screenshot('admin-frame-specification-mobile');
    return {profileWidth,dialogWidth,customerAdminStatus:403};
  });
  assert.deepEqual(pageErrors,[]);
})().catch(error=>{console.error(error.stack);if(!results.some(result=>result.status==='failed'))results.push({name:'driver',status:'failed',error:error.message});process.exitCode=1;}).finally(async()=>{
  if(browser) await browser.close().catch(()=>{});
  if(backend && backend.exitCode===null) { backend.kill('SIGTERM'); await new Promise(resolve=>{backend.once('exit',resolve);setTimeout(resolve,2000);}); }
  const report = {ranAt:new Date().toISOString(),environment:'Production React build + Chromium + real FastAPI endpoints + disposable SQLite. Synthetic accounts only; no payment/shipment provider calls.',results,pageErrors,passed:results.filter(r=>r.status==='passed').length,failed:results.filter(r=>r.status==='failed').length};
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(report,null,2));
  fs.writeFileSync(path.join(output,'backend.log'),backendLog);
  console.log(JSON.stringify({output,passed:report.passed,failed:report.failed,pageErrors}));
  if(report.failed || pageErrors.length) process.exitCode=1;
});
