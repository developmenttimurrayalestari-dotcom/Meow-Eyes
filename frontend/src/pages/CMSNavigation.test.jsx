import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import FooterPages from '../components/Layout/FooterPages';
import StaticPage from './StaticPage';
import { api } from '../lib/api';
jest.mock('../lib/api', () => ({ api: { get: jest.fn() }, imageSrc: value => value }));
let root, host;
const pages = [{ id: 'shipping', slug: 'kebijakan-pengiriman', title: 'Kebijakan Pengiriman', page_type: 'shipping_policy' }, { id: 'custom', slug: 'panduan-belanja', title: 'Panduan Belanja', page_type: 'custom' }];
const render = async children => act(async () => root.render(<MemoryRouter>{children}</MemoryRouter>));
const click = async element => act(async () => element.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })));
beforeEach(() => { jest.clearAllMocks(); host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

test('footer lists published CMS metadata using real /pages/slug links', async () => {
  api.get.mockResolvedValue({ data: { pages } });
  await render(<ul><FooterPages /></ul>);
  const links = [...host.querySelectorAll('a')];
  expect(links.map(link => link.getAttribute('href'))).toEqual(['/pages/kebijakan-pengiriman', '/pages/panduan-belanja']);
});
test('clicking a footer menu opens the CMS page and renders its HTML', async () => {
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/pages' ? { pages } : { page: { ...pages[1], content: '<h2>Cara berbelanja</h2><p>Isi halaman CMS.</p>' } } }));
  await render(<Routes><Route path="/" element={<ul><FooterPages /></ul>} /><Route path="/pages/:slug" element={<StaticPage />} /></Routes>);
  await click(host.querySelector('a[href="/pages/panduan-belanja"]'));
  expect(host.querySelector('[data-testid="page-title"]').textContent).toBe('Panduan Belanja');
  expect(host.querySelector('[data-testid="page-content"] h2').textContent).toBe('Cara berbelanja');
});
test('backend failures show a retry action instead of reporting a missing page', async () => {
  api.get.mockRejectedValueOnce({ response: { status: 503 } }).mockResolvedValueOnce({ data: { page: { slug: 'about', title: 'Tentang', content: '<p>Halo</p>' } } });
  await render(<StaticPage slug="about" />);
  expect(host.querySelector('[role="alert"]')).not.toBeNull();
  expect(host.querySelector('[data-testid="static-notfound"]')).toBeNull();
  await click(host.querySelector('button'));
  expect(host.querySelector('[data-testid="page-title"]').textContent).toBe('Tentang');
});
test('unpublished or missing pages produce the public not-found view', async () => {
  api.get.mockRejectedValue({ response: { status: 404 } });
  await render(<StaticPage slug="draft" />);
  expect(host.querySelector('[data-testid="static-notfound"]').textContent).toContain('belum dipublikasikan');
});
test('legacy policy aliases fall back to the published page type when its slug differs', async () => {
  api.get.mockImplementation(url => url === '/pages/kebijakan-privasi' ? Promise.reject({ response: { status: 404 } }) : Promise.resolve({ data: url === '/pages' ? { pages: [{ slug: 'privacy-baru', page_type: 'privacy_policy' }] } : { page: { slug: 'privacy-baru', title: 'Privasi Baru', content: '<p>Kebijakan</p>' } } }));
  await render(<StaticPage slug="kebijakan-privasi" pageType="privacy_policy" />);
  expect(host.querySelector('[data-testid="page-title"]').textContent).toBe('Privasi Baru');
});
test('a stale page response cannot replace a newly opened page', async () => {
  let resolve;
  api.get.mockImplementation(url => url === '/pages/old' ? new Promise(done => { resolve = done; }) : Promise.resolve({ data: { page: { slug: 'new', title: 'Baru', content: 'Isi' } } }));
  await render(<StaticPage slug="old" />); await render(<StaticPage slug="new" />);
  await act(async () => resolve({ data: { page: { slug: 'old', title: 'Lama', content: 'Isi lama' } } }));
  expect(host.querySelector('[data-testid="page-title"]').textContent).toBe('Baru');
});
