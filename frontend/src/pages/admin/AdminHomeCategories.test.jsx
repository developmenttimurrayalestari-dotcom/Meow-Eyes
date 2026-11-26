import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import AdminHomeCategories from './AdminHomeCategories';
import { api } from '../../lib/api';
jest.mock('../../lib/api', () => ({ api:{get:jest.fn(),post:jest.fn(),put:jest.fn(),delete:jest.fn()},imageSrc:value=>value,apiError:(err,fallback)=>err.response?.data?.detail||fallback }));
jest.mock('../../contexts/AuthContext',()=>({useAuth:()=>({user:{role:'super_admin'}})}));
jest.mock('../../components/ImagePicker',()=>({__esModule:true,default:({label,value,onChange})=><label>{label}<input data-testid="upload-background" value={value} onChange={event=>onChange(event.target.value)}/></label>}));
jest.mock('sonner',()=>({toast:{success:jest.fn()}}));
let root,host;
const item={id:'card',title:'Frame',description:'Premium',link_url:'/shop-now',background_image:'',sort_order:0,is_active:true,icon:'frame',theme:'coral'};
const change=async(input,value)=>act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,value);input.dispatchEvent(new Event('input',{bubbles:true}));});
const labelInput=(form,label)=>[...form.querySelectorAll('label')].find(node=>node.textContent.startsWith(label)).control;
const form=()=>document.querySelector('[data-testid="home-category-form"]');
beforeEach(async()=>{jest.clearAllMocks();api.get.mockResolvedValue({data:{version:0,items:[item]}});host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);await act(async()=>root.render(<AdminHomeCategories/>));});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.restoreAllMocks();});

test('creates a managed card with uploaded background, destination, order and active state',async()=>{
  await act(async()=>host.querySelector('[data-testid="add-home-category"]').click());
  const f=form();
  await change(labelInput(f,'Judul card'),'Card Baru');
  await change(f.querySelector('[data-testid="upload-background"]'),'/api/uploads-files/new.webp');
  api.post.mockResolvedValue({data:{version:1,items:[item,{...item,id:'new',title:'Card Baru',background_image:'/api/uploads-files/new.webp'}]}});
  await act(async()=>f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(api.post).toHaveBeenCalledWith('/admin/home-categories',expect.objectContaining({version:0,title:'Card Baru',sort_order:1,background_image:'/api/uploads-files/new.webp',is_active:true}));
  expect(form()).toBeNull();expect(host.textContent).toContain('Card Baru');
});

test('edits an existing card and preserves a conflict message and unsaved input',async()=>{
  await act(async()=>host.querySelector('[aria-label="Edit card Frame"]').click());
  await change(labelInput(form(),'Judul card'),'Frame Baru');
  api.put.mockRejectedValue({response:{status:409,data:{detail:'Tutup form dan muat ulang'}}});
  await act(async()=>form().dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(document.querySelector('[role="alert"]').textContent).toContain('muat ulang');
  expect(labelInput(form(),'Judul card').value).toBe('Frame Baru');
  api.put.mockResolvedValue({data:{version:1,items:[{...item,title:'Frame Baru',is_active:false}]}});
  await act(async()=>form().querySelector('input[type="checkbox"]').click());
  await act(async()=>form().dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(api.put).toHaveBeenLastCalledWith('/admin/home-categories/card',expect.objectContaining({version:0,title:'Frame Baru',is_active:false}));
  expect(host.textContent).toContain('Nonaktif');
});

test('delete requires confirmation and passes the current collection version',async()=>{
  const confirm=jest.spyOn(window,'confirm').mockReturnValue(false);
  await act(async()=>host.querySelector('[aria-label="Hapus card Frame"]').click());
  expect(api.delete).not.toHaveBeenCalled();confirm.mockReturnValue(true);
  api.delete.mockResolvedValue({data:{version:1,items:[]}});
  await act(async()=>host.querySelector('[aria-label="Hapus card Frame"]').click());
  expect(api.delete).toHaveBeenCalledWith('/admin/home-categories/card',{params:{version:0}});
  expect(host.textContent).toContain('Belum ada card');
});
