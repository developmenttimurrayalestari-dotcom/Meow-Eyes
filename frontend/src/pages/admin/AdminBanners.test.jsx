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

test('hero banners save independent mobile artwork and preview both images without hiding the upload fields',async()=>{
  await act(async()=>[...host.querySelector('form').querySelectorAll('button')].find(button=>button.textContent==='Batal').click());
  await act(async()=>host.querySelector('[data-testid="add-banner-btn"]').click());
  const form=host.querySelector('form');
  await type(form.querySelector('input[placeholder="Judul"]'),'Promo Mobile');
  await type(form.querySelector('[data-testid="banner-image-desktop-picker"]'),'/api/uploads-files/desktop.webp');
  await type(form.querySelector('[data-testid="banner-image-mobile-picker"]'),'/api/uploads-files/mobile.webp');
  expect(form.textContent).toContain('Pada layar sampai 767 px');
  expect([...form.querySelectorAll('[data-testid="banner-artwork-preview"] img')].map(img=>img.getAttribute('src'))).toEqual(['/api/uploads-files/desktop.webp','/api/uploads-files/mobile.webp']);
  await act(async()=>form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(api.post).toHaveBeenCalledWith('/admin/banners-v2',expect.objectContaining({position:'hero',target_device:'all',image_desktop:'/api/uploads-files/desktop.webp',image_mobile:'/api/uploads-files/mobile.webp'}));
});

test('an existing hero can replace its mobile artwork through Edit',async()=>{
  await act(async()=>root.render(null));
  api.get.mockResolvedValue({data:{banners:[{id:'hero',title:'Promo',image_desktop:'/desktop.webp',image_mobile:'/old.webp',position:'hero',target_device:'all',link_type:'internal',link_url:'/',sort_order:0,is_active:true}]}});
  api.put.mockResolvedValue({data:{ok:true}});
  await act(async()=>root.render(<AdminBannersV2/>));
  await act(async()=>[...host.querySelectorAll('button')].find(button=>button.textContent==='Edit').click());
  const form=host.querySelector('form');
  await type(form.querySelector('[data-testid="banner-image-mobile-picker"]'),'/new-mobile.webp');
  await act(async()=>form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(api.put).toHaveBeenCalledWith('/admin/banners-v2/hero',expect.objectContaining({image_desktop:'/desktop.webp',image_mobile:'/new-mobile.webp'}));
});
