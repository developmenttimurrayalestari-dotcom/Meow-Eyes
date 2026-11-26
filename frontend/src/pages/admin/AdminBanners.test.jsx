import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { AdminBannersV2 } from './AdminContent';
import { api } from '../../lib/api';
import { toast } from 'sonner';

jest.mock('../../lib/api', () => ({ api: { get: jest.fn(), post: jest.fn(), put: jest.fn(), delete: jest.fn() } }));
jest.mock('../../components/RichTextEditor', () => () => null);
jest.mock('../../components/ImagePicker', () => ({ __esModule: true, resolveImageUrl: value => value, default: ({ label, value, onChange, testId }) => <label>{label}<input data-testid={testId} value={value} onChange={event => onChange(event.target.value)} /></label> }));
jest.mock('sonner', () => ({ toast: { success: jest.fn(), error: jest.fn() } }));
let root, host;
const type = async (input, value) => act(async () => {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, value);
  input.dispatchEvent(new Event('input', { bubbles: true }));
});
beforeEach(async () => {
  jest.clearAllMocks(); api.get.mockResolvedValue({ data: { banners: [] } }); api.post.mockResolvedValue({ data: { ok: true } });
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
  await act(async () => root.render(<AdminBannersV2 />));
  await act(async () => host.querySelector('[data-testid="add-popup-banner-btn"]').click());
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

test('creates a popup via existing banner management with labelled images and session guidance', async () => {
  const form = host.querySelector('form');
  expect(form.textContent).toContain('Satu popup ditampilkan per sesi tab browser');
  expect(form.querySelector('option[value="popup"]').selected).toBe(true);
  await type(form.querySelector('input[placeholder="Judul"]'), 'Promo November');
  await type(form.querySelector('[data-testid="banner-image-desktop-picker"]'), '/promo.jpg');
  await type(form.querySelector('[data-testid="banner-image-mobile-picker"]'), '/mobile.jpg');
  await act(async () => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  expect(api.post).toHaveBeenCalledWith('/admin/banners-v2', expect.objectContaining({ position: 'popup', title: 'Promo November', image_desktop: '/promo.jpg', image_mobile: '/mobile.jpg', link_type: 'none', is_active: true }));
  expect(host.querySelector('form')).toBeNull();
});

test('requires a banner image before allowing save', async () => {
  const form = host.querySelector('form');
  await type(form.querySelector('input[placeholder="Judul"]'), 'Promo');
  await act(async () => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  expect(api.post).not.toHaveBeenCalled();
  expect(toast.error).toHaveBeenCalledWith('Isi judul dan gambar desktop banner terlebih dahulu.');
  expect(form.querySelector('button[type=submit]').disabled).toBe(false);
});
