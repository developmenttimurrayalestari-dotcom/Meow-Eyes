import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { TextEncoder } from 'util';
import SetupPasswordPage from './SetupPasswordPage';
import ProtectedRoute from '../components/ProtectedRoute';
import { api } from '../lib/api';

let mockUser;
const mockRefresh = jest.fn();
jest.mock('../contexts/AuthContext', () => ({ useAuth: () => ({ user: mockUser, refreshMe: mockRefresh, loading: false, logout: jest.fn() }) }));
jest.mock('../lib/api', () => ({ api: { post: jest.fn() }, apiError: (error, fallback) => error.response?.data?.detail || fallback }));
let host, root;
beforeEach(() => {
  global.TextEncoder = TextEncoder;
  jest.clearAllMocks();
  mockUser = { provider: 'facebook', has_password: false, has_pin: false };
  api.post.mockResolvedValue({ data: { ok: true } });
  mockRefresh.mockImplementation(async () => { mockUser = { ...mockUser, has_password: true }; return mockUser; });
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
const type = async (node, value) => act(async () => {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(node, value);
  node.dispatchEvent(new Event('input', { bubbles: true }));
});
async function mount() {
  await act(async () => root.render(<MemoryRouter initialEntries={['/orders?status=paid']}><Routes>
    <Route path="/orders" element={<ProtectedRoute><p>Order history</p></ProtectedRoute>} />
    <Route path="/setup-password" element={<ProtectedRoute><SetupPasswordPage /></ProtectedRoute>} />
    <Route path="/setup-pin" element={<p>Setup PIN</p>} />
  </Routes></MemoryRouter>));
}

test.each([false, true])('direct protected visits require password; existing PIN = %s', async pin => {
  mockUser.has_pin = pin;
  await mount();
  expect(host.textContent).toContain('Buat Password Akun');
  await type(host.querySelectorAll('input')[0], 'MyNewPassword123');
  await type(host.querySelectorAll('input')[1], 'MyNewPassword123');
  await act(async () => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  expect(api.post).toHaveBeenCalledWith('/auth/password/setup', { password: 'MyNewPassword123', confirm_password: 'MyNewPassword123' });
  expect(host.textContent).toContain(pin ? 'Order history' : 'Setup PIN');
});

test('password mismatch keeps the account on setup and does not send a request', async () => {
  await mount();
  await type(host.querySelectorAll('input')[0], 'MyNewPassword123');
  await type(host.querySelectorAll('input')[1], 'DifferentPassword123');
  await act(async () => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  expect(api.post).not.toHaveBeenCalled();
  expect(host.querySelector('[role=alert]').textContent).toContain('tidak cocok');
});
