import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import HomeCategoryCard from './HomeCategoryCard';
import HomePage from '../pages/HomePage';
import { api } from '../lib/api';

jest.mock('../lib/api', () => ({ api: { get: jest.fn() }, imageSrc: value => value, apiError: (err, fallback) => fallback }));
jest.mock('./ProductCard', () => () => null);
let host, root;
const item = { id:'custom', title:'Pilihan Customer', description:'Frame premium', link_url:'/shop-now?product_type=frame', background_image:'/card.webp', icon:'frame', theme:'coral' };
const render = async element => act(async () => root.render(<MemoryRouter>{element}</MemoryRouter>));
beforeEach(() => { jest.clearAllMocks(); host=document.createElement('div'); document.body.appendChild(host); root=createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

test('renders a clickable card with decorative uploaded background and readable overlay', async () => {
  await render(<HomeCategoryCard item={item} />);
  expect(host.querySelector('a').getAttribute('href')).toBe(item.link_url);
  expect(host.querySelector('img').getAttribute('src')).toBe('/card.webp');
  expect(host.querySelector('img').alt).toBe('');
  expect(host.querySelector('p').className).toContain('text-white');
  await act(async () => host.querySelector('img').dispatchEvent(new Event('error')));
  expect(host.querySelector('img')).toBeNull();
  expect(host.querySelector('p').className).toContain('text-meow-midnight');
});

test('external targets use a protected new tab, unsafe targets and admin previews are not clickable', async () => {
  await render(<HomeCategoryCard item={{...item,link_url:'https://example.com/promo'}} />);
  expect(host.querySelector('a').rel).toContain('noopener');
  await render(<HomeCategoryCard item={{...item,link_url:'javascript:alert(1)'}} />);
  expect(host.querySelector('a')).toBeNull();
  await render(<HomeCategoryCard item={item} preview />);
  expect(host.querySelector('a')).toBeNull();
});

test('homepage uses managed cards from the API and hides the section when there are none', async () => {
  const homepage = { bestsellers:[],newest:[],home_categories:[item] };
  api.get.mockImplementation(url => Promise.resolve({data:url==='/homepage'?homepage:url==='/flash-sales/active'?{flash_sales:[]}:{banners:[]}}));
  await render(<HomePage />);
  const section = host.querySelector('[data-testid="category-tiles-section"]');
  expect(section.textContent).toContain('Pilihan Customer');
  expect(section.textContent).not.toContain('Leinz Series');
  expect(section.querySelectorAll('a')).toHaveLength(1);
  await act(async () => root.render(null));
  homepage.home_categories=[];
  await render(<HomePage />);
  expect(host.querySelector('[data-testid="category-tiles-section"]')).toBeNull();
});
