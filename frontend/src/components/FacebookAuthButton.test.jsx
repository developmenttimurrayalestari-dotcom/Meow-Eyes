import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import FacebookAuthButton from './FacebookAuthButton';
import { api } from '../lib/api';
import { loadFacebookIdentity } from '../lib/facebookIdentity';
const mockLogin = jest.fn();
jest.mock('../contexts/AuthContext', () => ({ useAuth: () => ({ loginWithFacebook: mockLogin }) }));
jest.mock('../lib/api', () => ({ api: { get: jest.fn() }, apiError: (error, fallback) => error.response?.data?.detail || fallback }));
jest.mock('../lib/facebookIdentity', () => ({ loadFacebookIdentity: jest.fn() }));
jest.mock('sonner', () => ({ toast: { success: jest.fn() } }));
let host, root, sdk;
beforeEach(() => {
  jest.clearAllMocks(); sdk = { init: jest.fn(), login: jest.fn() };
  api.get.mockResolvedValue({ data: { enabled: true, app_id: '12345', version: 'v27.0' } });
  loadFacebookIdentity.mockResolvedValue(sdk); mockLogin.mockResolvedValue({ name: 'Facebook Customer', has_pin: true });
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
async function mount() {
  await act(async () => root.render(<MemoryRouter initialEntries={['/login']}><Routes>
    <Route path="/login" element={<FacebookAuthButton returnTo="/orders" />} />
    <Route path="/orders" element={<p>Orders</p>} /><Route path="/setup-pin" element={<p>Setup PIN</p>} />
  </Routes></MemoryRouter>));
}
const click = () => act(async () => host.querySelector('button').click());

test('Facebook SDK starts from a click, exchanges only its token, and preserves return path', async () => {
  await mount(); expect(sdk.init).toHaveBeenCalledWith(expect.objectContaining({ appId: '12345', version: 'v27.0', autoLogAppEvents: false }));
  expect(sdk.login).not.toHaveBeenCalled();
  await click(); expect(sdk.login.mock.calls[0][1].scope).toBe('public_profile,email');
  expect(sdk.login.mock.calls[0][1].auth_type).toBe('rerequest');
  await act(async () => sdk.login.mock.calls[0][0]({ authResponse: { accessToken: 'user-token', userID: 'untrusted-id' } }));
  expect(mockLogin).toHaveBeenCalledWith('user-token'); expect(host.textContent).toBe('Orders');
});

test('new Facebook customers still set up a PIN', async () => {
  mockLogin.mockResolvedValue({ name: 'New', has_pin: false }); await mount(); await click();
  await act(async () => sdk.login.mock.calls[0][0]({ authResponse: { accessToken: 'token' } }));
  expect(host.textContent).toBe('Setup PIN');
});

test('missing Meta configuration disables the button without loading the SDK', async () => {
  api.get.mockResolvedValue({ data: { enabled: false } }); await mount();
  expect(host.querySelector('button').disabled).toBe(true); expect(loadFacebookIdentity).not.toHaveBeenCalled();
  expect(host.textContent).toContain('belum tersedia');
});

test('cancelled login never exchanges a token, and backend errors remain visible', async () => {
  await mount(); await click();
  await act(async () => sdk.login.mock.calls[0][0]({ status: 'unknown' }));
  expect(mockLogin).not.toHaveBeenCalled(); expect(host.querySelector('[role="alert"]').textContent).toContain('dibatalkan');
  await click(); mockLogin.mockRejectedValue({ response: { data: { detail: 'Akun dinonaktifkan' } } });
  await act(async () => sdk.login.mock.calls[1][0]({ authResponse: { accessToken: 'token' } }));
  expect(host.querySelector('[role="alert"]').textContent).toBe('Akun dinonaktifkan');
});

test('SDK load errors offer retry and stale callbacks do not sign in', async () => {
  loadFacebookIdentity.mockRejectedValueOnce(new Error('SDK offline')); await mount();
  expect(host.querySelector('[role="alert"]').textContent).toContain('SDK offline');
  await act(async () => [...host.querySelectorAll('button')].find(node => node.textContent.includes('Muat ulang')).click());
  await click(); const callback = sdk.login.mock.calls[0][0];
  await act(async () => root.render(<p>Other page</p>));
  await act(async () => callback({ authResponse: { accessToken: 'stale-token' } }));
  expect(mockLogin).not.toHaveBeenCalled();
});
