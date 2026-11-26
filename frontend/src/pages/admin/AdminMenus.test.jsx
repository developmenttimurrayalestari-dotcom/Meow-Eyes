import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import AdminMenus from './AdminMenus';
import {api} from '../../lib/api';
jest.mock('../../lib/api',()=>({api:{get:jest.fn(),post:jest.fn(),put:jest.fn(),delete:jest.fn()},apiError:(err,fallback)=>err.response?.data?.detail||fallback}));
let mockUser={role:'super_admin'};
jest.mock('../../contexts/AuthContext',()=>({useAuth:()=>({user:mockUser})}));
jest.mock('sonner',()=>({toast:{success:jest.fn()}}));
let root,host;
const item={id:'menu',label:'Beranda',url:'/',location:'header',icon:'home',sort_order:0,is_active:true,new_tab:false};
const form=()=>document.querySelector('[data-testid="menu-form"]');
const input=label=>[...form().querySelectorAll('label')].find(node=>node.textContent.startsWith(label)).control;
const type=async(node,value)=>act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(node,value);node.dispatchEvent(new Event('input',{bubbles:true}));});
beforeEach(async()=>{jest.clearAllMocks();mockUser={role:'super_admin'};api.get.mockImplementation(url=>Promise.resolve({data:url==='/pages'?{pages:[]}:{version:0,items:[item]}}));host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);await act(async()=>root.render(<AdminMenus/>));});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.restoreAllMocks();});

test('creates a labelled menu with editable URL and new-tab behavior',async()=>{
  await act(async()=>host.querySelector('[data-testid="add-menu"]').click());
  await type(input('Nama menu'),'Promo');await type(input('URL tujuan menu'),'/flash-sale');
  await act(async()=>[...form().querySelectorAll('label')].find(node=>node.textContent==='Buka tautan di tab baru').querySelector('input').click());
  api.post.mockResolvedValue({data:{version:1,items:[item,{...item,id:'new',label:'Promo',url:'/flash-sale',sort_order:1,new_tab:true}]}});
  await act(async()=>form().dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(api.post).toHaveBeenCalledWith('/admin/menus',expect.objectContaining({version:0,label:'Promo',url:'/flash-sale',new_tab:true,sort_order:1}));
  expect(form()).toBeNull();expect(host.textContent).toContain('Promo');
});

test('conflicts preserve edited URLs and delete uses the loaded collection version',async()=>{
  await act(async()=>host.querySelector('[aria-label="Edit menu Beranda"]').click());await type(input('URL tujuan menu'),'/shop-now');
  api.put.mockRejectedValue({response:{data:{detail:'Tutup form dan muat ulang'}}});
  await act(async()=>form().dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(input('URL tujuan menu').value).toBe('/shop-now');expect(document.querySelector('[role="alert"]').textContent).toContain('muat ulang');
  await act(async()=>[...form().querySelectorAll('button')].find(button=>button.textContent==='Batal').click());
  jest.spyOn(window,'confirm').mockReturnValue(true);api.delete.mockResolvedValue({data:{version:1,items:[]}});
  await act(async()=>host.querySelector('[aria-label="Hapus menu Beranda"]').click());
  expect(api.delete).toHaveBeenCalledWith('/admin/menus/menu',{params:{version:0}});
});

test('read-only staff can view each menu location without mutation controls',async()=>{
  mockUser={role:'staff',permissions:['setting.view']};await act(async()=>root.render(<AdminMenus/>));
  expect(host.querySelector('[data-testid="add-menu"]')).toBeNull();
  expect(host.querySelector('[aria-label="Edit menu Beranda"]')).toBeNull();
  await act(async()=>[...host.querySelectorAll('button')].find(button=>button.textContent==='Footer Eksplorasi').click());
  expect(host.textContent).toContain('Belum ada menu pada lokasi ini');
});
