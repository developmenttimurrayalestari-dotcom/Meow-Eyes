import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import ShippingOriginForm from './ShippingOriginForm';
import AdminIntegrations from './AdminIntegrations';
import { api } from '../../lib/api';
let mockUser={role:'super_admin'};
jest.mock('../../contexts/AuthContext',()=>({useAuth:()=>({user:mockUser})}));
jest.mock('../../lib/api',()=>({api:{get:jest.fn(),put:jest.fn()},API_BASE:'/api',apiError:(e,f)=>e.response?.data?.detail||f}));
jest.mock('../../components/EverproRegionFields',()=>({value,onChange})=><button type="button" onClick={()=>onChange({...value,province_id:'p',city_id:'c',district_id:'d',subdistrict_id:'s',postal_code:'40115'})}>Pilih wilayah</button>);
const origin={name:'Toko Meow',phone:'081234567890',email:'',address:'Jalan Toko 12',version:0,latitude:null,longitude:null};
let host,root;
beforeEach(()=>{
  jest.clearAllMocks(); mockUser={role:'super_admin'};
  api.get.mockImplementation(url=>Promise.resolve({data:url==='/admin/shipping-origin'?{origin,source:'env'}:{payment:{},shipping:{}}}));
  api.put.mockImplementation((url,body)=>Promise.resolve({data:{origin:{...body,version:1},source:'admin'}}));
  host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);
});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});
test('superadmin selects canonical region and saves the dispatch address with its version',async()=>{
  const saved=jest.fn();
  await act(async()=>root.render(<ShippingOriginForm onSaved={saved}/>));
  expect(host.querySelector('input[type="tel"]').value).toBe(origin.phone);
  await act(async()=>[...host.querySelectorAll('button')].find(b=>b.textContent==='Pilih wilayah').click());
  await act(async()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(api.put).toHaveBeenCalledWith('/admin/shipping-origin',expect.objectContaining({address:origin.address,subdistrict_id:'s',postal_code:'40115',version:0}));
  expect(host.textContent).toContain('Alamat asal pengiriman disimpan');expect(saved).toHaveBeenCalledTimes(1);
});
test('server rejection preserves the address for correction',async()=>{
  api.put.mockRejectedValue({response:{data:{detail:'Alamat asal sudah diubah.'}}});
  await act(async()=>root.render(<ShippingOriginForm/>));
  await act(async()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(host.querySelector('[role="alert"]').textContent).toContain('Alamat asal sudah diubah');
  expect(host.querySelector('textarea').value).toBe(origin.address);
});
test.each(['admin','staff'])('origin settings are not loaded or displayed for %s',async role=>{
  mockUser={role};await act(async()=>root.render(<AdminIntegrations/>));
  expect(host.querySelector('[data-testid="shipping-origin-form"]')).toBeNull();
  expect(api.get).not.toHaveBeenCalledWith('/admin/shipping-origin');
});
