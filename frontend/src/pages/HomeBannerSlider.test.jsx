import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import {MemoryRouter} from 'react-router-dom';
import HomePage,{HeroSlider} from './HomePage';
import {api} from '../lib/api';
jest.mock('../lib/api',()=>({api:{get:jest.fn()},imageSrc:value=>value}));
let root,host;
const originalWidth=window.innerWidth;
const banner={id:'first',title:'Promo Frame',image_desktop:'/desktop.webp',image_mobile:'/mobile.webp',link_type:'internal',link_url:'/flash-sale'};
const render=async banners=>act(async()=>root.render(<MemoryRouter><HeroSlider banners={banners}/></MemoryRouter>));
const click=async node=>act(async()=>node.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})));
beforeEach(()=>{host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.useRealTimers();window.innerWidth=originalWidth;});

test('provides mobile artwork to small screens while retaining the desktop source and accessible link',async()=>{
  await render([banner]);
  const card=host.querySelector('[data-testid="hero-banner-first"]');
  expect(card.getAttribute('href')).toBe('/flash-sale');
  const picture=card.querySelector('picture');
  expect(picture.querySelector('source').media).toBe('(max-width: 767px)');
  expect(picture.querySelector('source').getAttribute('srcset')).toBe('/mobile.webp');
  expect(picture.querySelector('img').getAttribute('src')).toBe('/desktop.webp');
  expect(picture.querySelector('img').alt).toBe('Promo Frame');
  // Text and actions are siblings after the artwork rather than children over it.
  expect(picture.nextElementSibling.textContent).toContain('Promo Frame');
  expect(picture.nextElementSibling.textContent).toContain('Lihat Selengkapnya');
  expect(host.querySelector('[data-testid="hero-controls"]')).toBeNull();
});

test('a missing mobile image uses the desktop artwork and None destinations have no phantom link',async()=>{
  await render([{...banner,image_mobile:null,link_type:'none'}]);
  expect(host.querySelector('source')).toBeNull();
  expect(host.querySelector('img').getAttribute('src')).toBe('/desktop.webp');
  expect(host.querySelector('a')).toBeNull();
  expect(host.querySelector('[data-testid="hero-banner-cta-first"]')).toBeNull();
});

test('switching between banners with different artwork keeps only the current slide accessible',async()=>{
  await render([banner,{...banner,id:'second',title:'Promo Lensa',image_desktop:'/wide.webp',image_mobile:'/portrait.webp'}]);
  const first=host.querySelector('[data-testid="hero-banner-first"]').parentElement;
  const second=host.querySelector('[data-testid="hero-banner-second"]').parentElement;
  expect(first.getAttribute('aria-hidden')).toBe('false');expect(second.hasAttribute('inert')).toBe(true);
  await click(host.querySelector('[data-testid="hero-next"]'));
  expect(first.hasAttribute('inert')).toBe(true);expect(second.getAttribute('aria-hidden')).toBe('false');
  expect(second.querySelector('source').getAttribute('srcset')).toBe('/portrait.webp');
  const controls=host.querySelector('[data-testid="hero-controls"]');
  expect(controls.previousElementSibling.contains(second)).toBe(true);
  await click(host.querySelector('[data-testid="hero-prev"]'));
  expect(first.hasAttribute('inert')).toBe(false);
});

test('autoplay can still be paused and the default marketing slide is available without banners',async()=>{
  jest.useFakeTimers();
  await render([banner,{...banner,id:'second'}]);
  await act(async()=>jest.advanceTimersByTime(6000));
  expect(host.querySelector('[data-testid="hero-banner-second"]').parentElement.getAttribute('aria-hidden')).toBe('false');
  await click(host.querySelector('[aria-label="Jeda pergantian banner"]'));
  await act(async()=>jest.advanceTimersByTime(12000));
  expect(host.querySelector('[data-testid="hero-banner-second"]').parentElement.getAttribute('aria-hidden')).toBe('false');
  await render([]);
  expect(host.querySelector('[data-testid="hero-shop-btn"]')).not.toBeNull();
});

test.each([[360,'mobile'],[1280,'desktop']])('homepage requests banners for a %i px viewport (%s)',async(width,device)=>{
  window.innerWidth=width;api.get.mockClear();
  api.get.mockImplementation(url=>Promise.resolve({data:url==='/homepage'?{bestsellers:[],newest:[],home_categories:[]}:url==='/flash-sales/active'?{flash_sales:[]}:{banners:[banner]}}));
  await act(async()=>root.render(<MemoryRouter><HomePage/></MemoryRouter>));
  expect(api.get).toHaveBeenCalledWith('/banners?position=hero',{params:{device}});
});
