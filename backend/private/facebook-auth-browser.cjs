const assert=require('node:assert/strict');
const fs=require('node:fs/promises');const path=require('node:path');
const {chromium}=require('./tryon-browser-tools/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 let phase='cancel',configured=true,signed=false;const errors=[],exchanges=[];
 const user={user_id:'facebook-qa',name:'Facebook QA',email:'qa@example.com',phone:null,provider:'facebook',role:'customer',has_pin:false,points_balance:0};
 try{
  const page=await browser.newPage({viewport:{width:390,height:844},serviceWorkers:'block'});
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('https://connect.facebook.net/id_ID/sdk.js',route=>route.fulfill({contentType:'application/javascript',body:`window.FB={init(config){window.__facebookConfig=config;},login(callback,options){window.__facebookLoginOptions=options;window.__facebookCallback=callback;window.__facebookInvoke=()=>callback(window.__facebookCancel?{status:'unknown'}:{authResponse:{accessToken:'qa-meta-user-token'}});window.__facebookInvoke();}};`}));
  await page.route('**/api/**',async route=>{
   const req=route.request(),endpoint=new URL(req.url()).pathname.replace(/^\/api/,'');let status=200,data={items:[],products:[],categories:[],pages:[],orders:[],count:0,logs:[]};
   if(endpoint==='/auth/config')data={phone_enabled:false};
   else if(endpoint==='/auth/google/config')data={enabled:false,client_id:null};
   else if(endpoint==='/auth/facebook/config')data={enabled:configured,app_id:configured?'12345':null,version:configured?'v27.0':null};
   else if(endpoint==='/auth/facebook'){
    const payload=req.postDataJSON();exchanges.push(payload);assert.deepEqual(payload,{access_token:'qa-meta-user-token'});
    if(phase==='denied'){status=403;data={detail:'Akun dinonaktifkan'};}else{signed=true;data={token:'qa-local-facebook-session',user};}
   }else if(endpoint==='/auth/me'){if(signed)data={user};else{status=401;data={detail:'Not authenticated'};}}
   else if(endpoint==='/customer/profile')data={profile:{name:user.name,email:user.email,phone:'',prescription:{},version:0},ready:false,missing_fields:['phone']};
   else if(endpoint==='/settings/whatsapp')data={enabled:false};
   await route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
  });
  await page.goto('http://localhost:3000/register');
  const facebook=page.getByTestId('facebook-login-btn');await facebook.waitFor();
  await page.waitForFunction(()=>!document.querySelector('[data-testid="facebook-login-btn"]').disabled);
  assert.equal(await page.getByRole('button',{name:'Nomor telepon',exact:true}).count(),0);
  assert.equal(await page.getByTestId('register-email').getAttribute('type'),'email');
  await page.evaluate(()=>{window.__facebookCancel=true;});await facebook.click();
  await page.getByRole('alert').filter({hasText:'dibatalkan'}).waitFor();assert.equal(exchanges.length,0);
  await page.evaluate(()=>{window.__facebookCancel=false;});phase='accept';
  await page.screenshot({path:path.join(__dirname,'facebook-register-mobile.png'),fullPage:true});
  await facebook.click();await page.waitForURL('**/setup-pin');
  assert.equal(await page.evaluate(()=>localStorage.getItem('meow_token')),'qa-local-facebook-session');
  user.has_pin=true;await page.goto('http://localhost:3000/login?returnTo=%2Fprofile');
  await page.getByTestId('facebook-login-btn').click();await page.waitForURL('**/profile');
  phase='denied';await page.goto('http://localhost:3000/login');
  await page.getByTestId('facebook-login-btn').click();await page.getByRole('alert').filter({hasText:'Akun dinonaktifkan'}).waitFor();
  assert.equal(await page.getByTestId('login-email').getAttribute('type'),'email');
  configured=false;await page.reload();await page.getByText('Login Facebook belum tersedia.',{exact:true}).waitFor();
  assert.equal(await page.getByTestId('facebook-login-btn').isDisabled(),true);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
  assert.deepEqual(errors,[]);assert.equal(exchanges.length,3);
  const report={ok:true,api:'mocked; no real account/session writes',metaConsent:'mock SDK; real Meta App ID and Secret required',phoneUIHidden:true,facebookSignupAndPin:true,facebookLoginAndReturn:true,cancelNoTokenExchange:true,backendErrorsVisible:true,missingConfigHandled:true,mobileNoOverflow:true,errors};
  await fs.writeFile(path.join(__dirname,'facebook-auth-browser-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
