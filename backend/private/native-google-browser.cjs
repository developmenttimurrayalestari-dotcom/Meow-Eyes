const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('./tryon-browser-tools/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const errors = [], exchanges = [], brokerRequests = [];
  let scenario = 'signup', sdkLoads = 0;
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, serviceWorkers: 'block' });
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*emergentagent.com/**', async route => { brokerRequests.push(route.request().url()); await route.abort(); });
    await page.route('https://accounts.google.com/gsi/client', async route => {
      sdkLoads++;
      await route.fulfill({ contentType: 'application/javascript', body: `window.google={accounts:{id:{initialize(config){window.__nativeGoogleConfig=config;},renderButton(element,options){const button=document.createElement('button');button.type='button';button.textContent=options.text==='signup_with'?'Daftar dengan Google':'Masuk dengan Google';button.onclick=()=>window.__nativeGoogleConfig.callback({credential:'mock-google-signed-credential'});element.appendChild(button);}}}};` });
    });
    await page.route('**/api/**', async route => {
      const request = route.request(), endpoint = new URL(request.url()).pathname.replace(/^\/api/, '');
      const user = { user_id: 'native-google-qa', email: 'qa@gmail.com', name: 'Google QA', role: 'customer', provider: 'google', has_pin: scenario !== 'signup', points_balance: 0 };
      let status = 200, data = { items: [], orders: [], pages: [], count: 0, spins: [] };
      if (endpoint === '/auth/google/config') data = { enabled: scenario !== 'unconfigured', client_id: scenario === 'unconfigured' ? null : 'qa.apps.googleusercontent.com' };
      else if (endpoint === '/auth/google') {
        const payload = request.postDataJSON(); exchanges.push(payload);
        assert.equal(payload.credential, 'mock-google-signed-credential');
        assert.match(payload.nonce, /^[a-f0-9]{48}$/);
        assert.equal(payload.nonce, await page.evaluate(() => window.__nativeGoogleConfig.nonce));
        if (scenario === 'rejected') { status = 403; data = { detail: 'Akun dinonaktifkan' }; }
        else data = { token: 'qa-local-token', user };
      } else if (endpoint === '/auth/me') {
        if (request.headers().authorization === 'Bearer qa-local-token') data = { user };
        else { status = 401; data = { detail: 'Not authenticated' }; }
      } else if (endpoint === '/settings/whatsapp') data = { enabled: false };
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) });
    });
    await page.goto('http://localhost:3000/register');
    await page.getByRole('button', { name: 'Daftar dengan Google', exact: true }).waitFor();
    assert.equal(await page.getByTestId('register-email').inputValue(), '');
    await page.screenshot({ path: path.join(__dirname, 'native-google-register-desktop.png'), fullPage: true });
    await page.getByRole('button', { name: 'Daftar dengan Google', exact: true }).click();
    await page.waitForURL('**/setup-pin');
    assert.equal(await page.evaluate(() => localStorage.getItem('meow_token')), 'qa-local-token');
    scenario = 'login';
    await page.goto('http://localhost:3000/login?returnTo=%2Forders');
    await page.getByRole('button', { name: 'Masuk dengan Google', exact: true }).click();
    await page.waitForURL('**/orders');
    scenario = 'rejected';
    await page.goto('http://localhost:3000/login');
    await page.getByRole('button', { name: 'Masuk dengan Google', exact: true }).click();
    await page.getByRole('alert').filter({ hasText: 'Akun dinonaktifkan' }).waitFor();
    assert.equal(new URL(page.url()).pathname, '/login');
    scenario = 'unconfigured'; const loadsBefore = sdkLoads;
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:3000/register');
    await page.getByText('Daftar/masuk Google belum tersedia.', { exact: false }).waitFor();
    assert.equal(sdkLoads, loadsBefore);
    assert.equal(await page.getByTestId('google-register-btn').locator('div').first().isVisible(), false);
    assert.equal(await page.getByTestId('register-submit-btn').isEnabled(), true);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    await page.screenshot({ path: path.join(__dirname, 'native-google-register-mobile-unconfigured.png'), fullPage: true });
    assert.equal(exchanges.length, 3); assert.deepEqual(brokerRequests, []); assert.deepEqual(errors, []);
    const report = { ok: true, api: 'mocked; no store account/session writes', googleConsent: 'mock SDK; real Google login requires store OAuth Client ID',
      nativeSignupAndPin: true, nativeLoginAndSafeReturn: true, backendErrorsVisible: true,
      missingConfigurationFallback: true, mobileNoOverflow: true, exchanges: exchanges.length, brokerRequests, errors };
    await fs.writeFile(path.join(__dirname, 'native-google-browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
