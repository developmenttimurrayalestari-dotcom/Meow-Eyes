const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
const {chromium}=require('./tryon-browser-tools/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const errors=[],writes=[];let signed=false;
 const user={user_id:'phone-qa',name:'Phone Customer',email:null,phone:'+6281234567890',role:'customer',has_pin:false,points_balance:0};
 try{
  const page=await browser.newPage({viewport:{width:390,height:844},serviceWorkers:'block'});
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/**',async route=>{
   const req=route.request(),endpoint=new URL(req.url()).pathname.replace(/^\/api/,'');
   let status=200,data={items:[],products:[],categories:[],pages:[],orders:[],count:0,logs:[],balance:0};
   if(endpoint==='/auth/google/config')data={enabled:false,client_id:null};
   else if(endpoint==='/auth/register'||endpoint==='/auth/login'){
    const body=req.postDataJSON();writes.push({endpoint,body});signed=true;
    if(endpoint==='/auth/register'){assert.equal(body.phone,'081234567890');assert.equal(body.email,undefined);}
    else{assert.equal(body.identifier,'6281234567890');user.has_pin=true;}
    data={token:'qa-phone-session',user};
   }else if(endpoint==='/auth/me'){if(signed)data={user};else{status=401;data={detail:'Not authenticated'};}}
   else if(endpoint==='/customer/profile')data={profile:{name:user.name,email:null,phone:user.phone,prescription:{},version:0},ready:false,missing_fields:['birth_date']};
   else if(endpoint==='/settings/whatsapp')data={enabled:false};
   await route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
  });
  await page.goto('http://localhost:3000/register');
  await page.getByRole('button',{name:'Nomor telepon',exact:true}).click();
  assert.equal(await page.getByTestId('register-email').count(),0);
  await page.getByTestId('register-name').fill('Phone Customer');
  await page.getByTestId('register-phone').fill('081234567890');
  await page.getByTestId('register-password').fill('Example123!');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
  await page.screenshot({path:path.join(__dirname,'phone-registration-mobile.png'),fullPage:true});
  await page.getByTestId('register-submit-btn').click();await page.waitForURL('**/setup-pin');
  assert.equal(await page.evaluate(()=>localStorage.getItem('meow_token')),'qa-phone-session');
  await page.goto('http://localhost:3000/login?returnTo=%2Fprofile');
  await page.getByTestId('login-email').fill('6281234567890');await page.getByTestId('login-password').fill('Example123!');
  await page.getByTestId('login-submit-btn').click();await page.waitForURL('**/profile');
  await page.getByText('+6281234567890',{exact:true}).first().waitFor();
  assert.equal(writes.length,2);assert.deepEqual(errors,[]);
  const report={ok:true,api:'mocked; no real customer or session writes',phoneSignupWithoutEmail:true,phoneLogin:true,pinOnboarding:true,profileDisplaysPhone:true,mobileNoOverflow:true,errors};
  await fs.writeFile(path.join(__dirname,'phone-auth-browser-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
