import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import {MemoryRouter,useLocation} from 'react-router-dom';
import StorefrontMenus,{useStorefrontMenus} from './StorefrontMenus';
import {api} from '../lib/api';
import MainLayout from './Layout/MainLayout';
jest.mock('../lib/api',()=>({api:{get:jest.fn()}}));
jest.mock('../contexts/AuthContext',()=>({useAuth:()=>({user:null,cartCount:2,logout:jest.fn()})}));
jest.mock('./PromoPopup',()=>()=>null);
jest.mock('./Layout/FooterPages',()=>()=>null);
jest.mock('./ConveyThisTranslation',()=>({TranslationButtons:()=>null}));
let root,host;
const item={id:'custom-menu',label:'Panduan',url:'/pages/panduan',icon:'article',location:'header',sort_order:1,is_active:true,new_tab:false};
const click=async node=>act(async()=>node.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})));
function Path(){return <span data-testid="path">{useLocation().pathname}</span>;}
function Live(){const menus=useStorefrontMenus();return <StorefrontMenus items={menus} location="header"/>;}
const render=async node=>act(async()=>root.render(<MemoryRouter>{node}<Path/></MemoryRouter>));
beforeEach(()=>{jest.clearAllMocks();host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});

test('configured header links honor sorting, active status, safe URLs and client navigation',async()=>{
  await render(<StorefrontMenus items={[item,{...item,id:'first',label:'Beranda',url:'/',sort_order:0},{...item,id:'hidden',is_active:false},{...item,id:'unsafe',url:'javascript:alert(1)'}]} location="header"/>);
  expect([...host.querySelectorAll('a')].map(link=>link.textContent)).toEqual(['Beranda','Panduan']);
  await click(host.querySelector('[data-testid="custom-menu"]'));
  expect(host.querySelector('[data-testid="path"]').textContent).toBe('/pages/panduan');
});

test('Meowsurement keeps native document navigation and configured new-tab links are protected',async()=>{
  await render(<StorefrontMenus items={[{...item,url:'/meowsurement/'},{...item,id:'external',url:'https://example.com',new_tab:true}]} location="header"/>);
  expect(host.querySelector('[data-testid="custom-menu"]').hasAttribute('data-discover')).toBe(false);
  const link=host.querySelector('[data-testid="external"]');expect(link.target).toBe('_blank');expect(link.rel).toContain('noopener');
});

test('mobile navigation retains the cart badge and the logged-out profile destination',async()=>{
  const items=[{...item,id:'bn-profile',label:'Profil',url:'/profile',icon:'profile',location:'mobile'},{...item,id:'bn-cart',label:'Cart',url:'/cart',icon:'cart',location:'mobile'}];
  await render(<StorefrontMenus items={items} location="mobile" cartCount={3}/>);
  expect(host.querySelector('[data-testid="bn-profile"]').getAttribute('href')).toBe('/login');
  expect(host.querySelector('[data-testid="bn-profile"]').textContent).toBe('Masuk');
  expect(host.querySelector('[data-testid="bn-cart"]').textContent).toContain('3');
});

test('successful empty configurations stay hidden while failed loads use initial navigation',async()=>{
  api.get.mockResolvedValueOnce({data:{items:[]}});
  await render(<Live/>);expect(host.querySelector('nav')).toBeNull();
  await act(async()=>root.render(null));api.get.mockRejectedValue(new Error('offline'));
  await render(<Live/>);expect(host.querySelector('[data-testid="nav-home"]')).not.toBeNull();
});

test('focus refreshes configured navigation and pending requests are aborted on unmount',async()=>{
  api.get.mockResolvedValue({data:{items:[item]}});await render(<Live/>);
  api.get.mockResolvedValue({data:{items:[{...item,label:'Nama Baru'}]}});
  await act(async()=>window.dispatchEvent(new Event('focus')));
  expect(host.textContent).toContain('Nama Baru');
  const signal=api.get.mock.calls.at(-1)[1].signal;await act(async()=>root.render(null));expect(signal.aborted).toBe(true);
});

test('the real customer layout reads one managed collection for header, footer and mobile',async()=>{
  api.get.mockResolvedValue({data:{items:[item,{...item,id:'footer-custom',location:'footer',label:'Bantuan Toko',url:'/pages/bantuan'},{...item,id:'mobile-custom',location:'mobile',label:'Belanja',url:'/shop-now',icon:'shop'}]}});
  await render(<MainLayout><p>Isi halaman</p></MainLayout>);
  expect(host.querySelector('[data-testid="main-menu"] a').getAttribute('href')).toBe('/pages/panduan');
  expect(host.querySelector('[data-testid="main-footer"] a[data-testid="footer-custom"]').getAttribute('href')).toBe('/pages/bantuan');
  expect(host.querySelector('[data-testid="bottom-nav"] a').textContent).toBe('Belanja');
  expect(host.querySelector('[data-testid="nav-home"]')).toBeNull();
  expect(api.get.mock.calls.filter(([url])=>url==='/menus')).toHaveLength(1);
});
