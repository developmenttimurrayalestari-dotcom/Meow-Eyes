import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import {MemoryRouter} from 'react-router-dom';
import {AdminTryOn} from './AdminFeatures';
import {api} from '../../lib/api';
jest.mock('../../lib/api',()=>({api:{get:jest.fn()},imageSrc:value=>value}));
jest.mock('sonner',()=>({toast:{success:jest.fn(),error:jest.fn()}}));
jest.mock('../../components/ImagePicker',()=>()=>null);
let host,root,frames;
const click=async node=>act(async()=>node.click());
const settle=async()=>act(async()=>jest.advanceTimersByTime(200));
const frame={id:'frame',name:'Frame baru',sku:'FRAME-001',product_type:'frame',is_active:true,variants:[]};
beforeEach(()=>{
 jest.useFakeTimers();jest.clearAllMocks();frames=[];
 api.get.mockImplementation(url=>Promise.resolve({data:url==='/admin/products'?{products:frames}:{assets:[]}}));
 host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);
});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.useRealTimers();});
const mount=async()=>act(async()=>root.render(<MemoryRouter><AdminTryOn/></MemoryRouter>));
test('empty product options explain the Frame requirement and link to product management',async()=>{
 await mount();await click([...host.querySelectorAll('button')].find(b=>b.textContent.includes('Tambah aset')));await settle();
 const dialog=host.querySelector('[role="dialog"]');
 expect(dialog.textContent).toContain('berjenis Frame');expect(dialog.textContent).toContain('Paket');
 expect(dialog.querySelector('a[href="/admin/products"]')).not.toBeNull();
 expect([...dialog.querySelectorAll('button')].find(b=>b.textContent==='Simpan aset').disabled).toBe(true);
});
test('opening the form includes Frame and Paket with SKU and excludes lenses and deleted products',async()=>{
 await mount();await settle();
 frames=[frame,{...frame,id:'deleted',deleted_at:'2026-11-12'}, {...frame,id:'package',product_type:'package'}, {...frame,id:'lens',product_type:'lens'}, {...frame,id:'deleted-package',product_type:'package',deleted_at:'2026-11-12'}];
 await click([...host.querySelectorAll('button')].find(b=>b.textContent.includes('Tambah aset')));await settle();
 const select=host.querySelector('select');
 expect([...select.options].map(o=>o.value)).toEqual(['','frame','package']);
 expect(select.textContent).toContain('Paket');
 expect(select.textContent).toContain('FRAME-001');
 expect(api.get.mock.calls.filter(([url])=>url==='/admin/products')).toHaveLength(2);
 expect(api.get.mock.calls.filter(([url])=>url==='/admin/products').at(-1)[1].params).toEqual({q:'',limit:100,try_on_eligible:true});
});
test('product load failures remain visible in the dialog and support retry',async()=>{
 api.get.mockImplementation(url=>url==='/admin/products'?Promise.reject({response:{data:{detail:'Daftar frame gagal'}}}):Promise.resolve({data:{assets:[]}}));
 await mount();await settle();await click([...host.querySelectorAll('button')].find(b=>b.textContent.includes('Tambah aset')));await settle();
 expect(host.querySelector('[role="dialog"] [role="alert"]').textContent).toContain('Daftar frame gagal');
 frames=[frame];api.get.mockResolvedValue({data:{products:frames}});
 await click([...host.querySelectorAll('button')].find(b=>b.textContent==='Muat ulang frame'));await settle();
 expect(host.querySelector('select').options).toHaveLength(2);
});
