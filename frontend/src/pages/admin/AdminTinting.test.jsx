import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import AdminTinting from './AdminTinting';
import {api} from '../../lib/api';
jest.mock('../../lib/api',()=>({api:{get:jest.fn(),post:jest.fn(),put:jest.fn(),delete:jest.fn()},formatIDR:value=>`Rp ${value}`,apiError:(err,fallback)=>err.response?.data?.detail||fallback}));
jest.mock('../../contexts/AuthContext',()=>({useAuth:()=>({user:{role:'super_admin'}})}));
jest.mock('sonner',()=>({toast:{success:jest.fn()}}));
let host,root;
const item={id:'black',code:'04S',name:'Black',kind:'solid',group:'fashion',hex_color:'#000000',mid_hex_color:null,bottom_hex_color:null,additional_price:60000,sort_order:0,is_active:true,requires_sample:false,source_note:''};
const click=node=>act(async()=>node.click());
const field=(form,label)=>[...form.querySelectorAll('label')].find(node=>node.textContent.startsWith(label)).control;
const type=(node,value)=>act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(node,value);node.dispatchEvent(new Event('input',{bubbles:true}));});
const form=()=>document.querySelector('[data-testid=tinting-form]');
beforeEach(async()=>{jest.clearAllMocks();api.get.mockResolvedValue({data:{version:0,items:[item]}});host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);await act(async()=>root.render(<AdminTinting/>));});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.restoreAllMocks();});

test('edits the color name, HEX and price with an unchanged master version',async()=>{
  await click(host.querySelector('[aria-label="Edit tinting 04S"]'));
  await type(field(form(),'Nama warna'),'Black Baru');
  await type(field(form(),'HEX warna solid'),'#112233');
  await type(field(form(),'Harga tambahan'),'75000');
  api.put.mockResolvedValue({data:{version:1,items:[{...item,name:'Black Baru',hex_color:'#112233',additional_price:75000}]}});
  await act(async()=>form().dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(api.put).toHaveBeenCalledWith('/admin/tinting/black',expect.objectContaining({version:0,name:'Black Baru',hex_color:'#112233',additional_price:75000}));
  expect(form()).toBeNull();expect(host.textContent).toContain('Black Baru');
});

test('a version conflict retains the edited form for review',async()=>{
  await click(host.querySelector('[aria-label="Edit tinting 04S"]'));
  await type(field(form(),'Nama warna'),'New draft');
  api.put.mockRejectedValue({response:{data:{detail:'Tutup form dan muat ulang'}}});
  await act(async()=>form().dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(field(form(),'Nama warna').value).toBe('New draft');
  expect(form().querySelector('[role=alert]').textContent).toContain('muat ulang');
});

test('can add a color and delete it using a confirmed versioned request',async()=>{
  await click(host.querySelector('[data-testid=add-tinting]'));
  await type(field(form(),'Kode warna'),'NEW');await type(field(form(),'Nama warna'),'New Color');
  api.post.mockResolvedValue({data:{version:1,items:[item,{...item,id:'new',code:'NEW',name:'New Color'}]}});
  await act(async()=>form().dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(api.post).toHaveBeenCalledWith('/admin/tinting',expect.objectContaining({code:'NEW',name:'New Color',additional_price:60000}));
  jest.spyOn(window,'confirm').mockReturnValue(true);
  api.delete.mockResolvedValue({data:{version:2,items:[item]}});
  await click(host.querySelector('[aria-label="Hapus tinting NEW"]'));
  expect(api.delete).toHaveBeenCalledWith('/admin/tinting/new',{params:{version:1}});
});
