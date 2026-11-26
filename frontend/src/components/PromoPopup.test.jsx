import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import PromoPopup from './PromoPopup';
import { api } from '../lib/api';

jest.mock('../lib/api', () => ({ api: { get: jest.fn() }, imageSrc: value => value }));
let host, root, navigate;
const banner = { id: 'promo', title: 'Promo Akhir Tahun', position: 'popup', is_active: true, image_desktop: '/promo.jpg', image_mobile: '/promo-mobile.jpg', link_type: 'internal', link_url: '/flash-sale', sort_order: 0, target_device: 'all' };
function Harness() { navigate = useNavigate(); return <PromoPopup />; }
const mount = async (path = '/') => act(async () => root.render(<MemoryRouter initialEntries={[path]}><Harness /></MemoryRouter>));
const loaded = async () => act(async () => host.querySelector('[data-testid="promo-popup-preload"]').dispatchEvent(new Event('load')));
const popup = () => document.querySelector('[data-testid="promo-popup"]');
beforeEach(() => {
  jest.clearAllMocks(); sessionStorage.clear();
  api.get.mockResolvedValue({ data: { banners: [banner] } });
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); jest.restoreAllMocks(); });

test('dismissal lasts for the current homepage visit and the promo returns on the next homepage entry', async () => {
  await mount();
  expect(popup()).toBeNull();
  expect(sessionStorage.length).toBe(0);
  await loaded();
  expect(popup().textContent).toContain('Promo Akhir Tahun');
  expect(document.activeElement.getAttribute('aria-label')).toBe('Tutup promo');
  await act(async () => document.querySelector('[data-testid="close-promo-popup"]').click());
  expect(popup()).toBeNull();
  expect(host.querySelector('[data-testid="promo-popup-preload"]')).toBeNull();
  await act(async () => navigate('/shop-now'));
  expect(popup()).toBeNull();
  await act(async () => navigate('/'));
  await loaded(); expect(popup()).not.toBeNull();
  expect(api.get).toHaveBeenCalledTimes(2);
});

test('internal banner click navigates and reopening the homepage shows the promo again', async () => {
  await mount(); await loaded();
  const link = popup().querySelector('a');
  expect(link.getAttribute('href')).toBe('/flash-sale');
  await act(async () => link.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })));
  expect(popup()).toBeNull();
  await act(async () => navigate('/checkout'));
  await act(async () => navigate('/'));
  await loaded(); expect(popup()).not.toBeNull();
});

test.each(['/admin/banners', '/checkout', '/payment/123', '/login', '/profile', '/shop-now', '/products/frame', '/flash-sale'])('never opens or requests a promo on %s', async path => {
  await mount(path);
  expect(api.get).not.toHaveBeenCalled(); expect(popup()).toBeNull();
});

test('mobile selects mobile artwork and falls back to desktop if that image fails', async () => {
  window.matchMedia = jest.fn(() => ({ matches: true }));
  await mount();
  expect(api.get).toHaveBeenCalledWith('/banners', expect.objectContaining({ params: { position: 'popup', device: 'mobile' } }));
  expect(host.querySelector('img').getAttribute('src')).toBe('/promo-mobile.jpg');
  await act(async () => host.querySelector('img').dispatchEvent(new Event('error')));
  expect(host.querySelector('img').getAttribute('src')).toBe('/promo.jpg');
  expect(sessionStorage.length).toBe(0);
  await loaded();
  expect(popup().querySelector('img').getAttribute('src')).toBe('/promo.jpg');
  delete window.matchMedia;
});

test('inactive, future, expired, non-popup and wrong-device promos are ignored', async () => {
  api.get.mockResolvedValue({ data: { banners: [
    { ...banner, is_active: false }, { ...banner, start_at: '2099-01-01T00:00:00Z' },
    { ...banner, end_at: '2000-01-01T00:00:00Z' }, { ...banner, position: 'hero' },
    { ...banner, target_device: 'mobile' },
  ] } });
  await mount();
  expect(host.querySelector('img')).toBeNull(); expect(popup()).toBeNull();
});

test('failed artwork falls through to the next priority without consuming the session', async () => {
  api.get.mockResolvedValue({ data: { banners: [{ ...banner, id: 'later', sort_order: 10, image_desktop: '/later.jpg' }, banner] } });
  await mount();
  expect(host.querySelector('img').getAttribute('src')).toBe('/promo.jpg');
  await act(async () => host.querySelector('img').dispatchEvent(new Event('error')));
  expect(sessionStorage.length).toBe(0);
  expect(host.querySelector('img').getAttribute('src')).toBe('/later.jpg');
  await loaded(); expect(popup()).not.toBeNull();
});

test.each(['javascript:alert(1)', '//evil.example', '/\\evil.example'])('unsafe destination %s renders an unlinked image', async url => {
  api.get.mockResolvedValue({ data: { banners: [{ ...banner, link_url: url }] } });
  await mount(); await loaded();
  expect(popup().querySelector('a')).toBeNull();
});

test('external promo uses a protected new tab and network failure never blocks the page', async () => {
  api.get.mockResolvedValueOnce({ data: { banners: [{ ...banner, link_type: 'external', link_url: 'https://example.com/promo' }] } });
  await mount(); await loaded();
  expect(popup().querySelector('a').rel).toContain('noopener');
  expect(popup().querySelector('a').target).toBe('_blank');
  await act(async () => root.render(null)); sessionStorage.clear();
  api.get.mockRejectedValue(new Error('offline'));
  await mount(); expect(popup()).toBeNull();
});

test('late CMS responses after leaving the storefront cannot open a popup', async () => {
  let resolve;
  api.get.mockImplementation(() => new Promise(done => { resolve = done; }));
  await mount(); await act(async () => navigate('/checkout'));
  await act(async () => resolve({ data: { banners: [banner] } }));
  expect(popup()).toBeNull(); expect(sessionStorage.length).toBe(0);
});

test('Escape dismisses the accessible dialog', async () => {
  await mount(); await loaded();
  await act(async () => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })));
  expect(popup()).toBeNull();
});

test('homepage refreshes and blocked storage do not prevent the promo from appearing', async () => {
  jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
  await mount(); await loaded();
  expect(popup()).not.toBeNull();
  await act(async () => document.querySelector('[data-testid="close-promo-popup"]').click());
  expect(popup()).toBeNull();
  expect(host.querySelector('[data-testid="promo-popup-preload"]')).toBeNull();
  await act(async () => root.render(null));
  jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked'); });
  await mount(); await loaded(); expect(popup()).not.toBeNull();
});

test('legacy session markers are ignored and a new homepage history entry reopens the popup', async () => {
  sessionStorage.setItem('meow_promo_popup_seen_v1','1');
  await mount(); await loaded();
  await act(async()=>document.querySelector('[data-testid="close-promo-popup"]').click());
  await act(async()=>navigate('/'));
  await loaded(); expect(popup()).not.toBeNull();
});
