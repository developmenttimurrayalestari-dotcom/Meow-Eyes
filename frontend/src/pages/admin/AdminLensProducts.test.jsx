import React,{act} from 'react';
import{createRoot}from'react-dom/client';
import AdminLensProducts from './AdminLensProducts';
import{api}from'../../lib/api';
jest.mock('../../lib/api',()=>({api:{get:jest.fn(),post:jest.fn(),put:jest.fn(),delete:jest.fn()},formatIDR:v=>`Rp ${v}`,apiError:(e,f)=>e.response?.data?.detail||f}));
jest.mock('../../contexts/AuthContext',()=>({useAuth:()=>({user:{role:'super_admin'}})}));
jest.mock('sonner',()=>({toast:{success:jest.fn()}}));
let host,root;
const data={version:0,types:[{code:'clear',name:'Clear'},{code:'uv420',name:'UV420'}],items:[]};
const click=n=>act(async()=>n.click());
const field=label=>[...document.querySelectorAll('[data-testid=lens-product-form] label')].find(n=>n.textContent.startsWith(label)).control;
const type=(n,v)=>act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(n,v);n.dispatchEvent(new Event('input',{bubbles:true}));});
beforeEach(async()=>{jest.clearAllMocks();api.get.mockResolvedValue({data});host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);await act(async()=>root.render(<AdminLensProducts/>));});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});
test('creates a priced type/index combination',async()=>{
  await click([...host.querySelectorAll('button')].find(n=>n.textContent==='Tambah Produk Lensa'));
  await type(field('Harga lensa'),'60000');await type(field('Indeks lensa'),'1.67');
  api.post.mockResolvedValue({data:{...data,version:1,items:[]}});
  await act(async()=>document.querySelector('[data-testid=lens-product-form]').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(api.post).toHaveBeenCalledWith('/admin/lens-products',expect.objectContaining({version:0,lens_type:'clear',index_value:'1.67',additional_price:60000}));
});
test('keeps a price draft after a version conflict',async()=>{
  await click([...host.querySelectorAll('button')].find(n=>n.textContent==='Tambah Produk Lensa'));
  await type(field('Harga lensa'),'90000');api.post.mockRejectedValue({response:{data:{detail:'Muat ulang sebelum menyimpan'}}});
  await act(async()=>document.querySelector('[data-testid=lens-product-form]').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(field('Harga lensa').value).toBe('90000');expect(document.querySelector('[role=alert]').textContent).toContain('Muat ulang');
});
