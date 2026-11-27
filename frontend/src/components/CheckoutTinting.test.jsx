import React, { act, useState } from 'react';
import { createRoot } from 'react-dom/client';
import CheckoutTinting from './CheckoutTinting';
import { api } from '../lib/api';

jest.mock('../lib/api',()=>({api:{get:jest.fn(),patch:jest.fn()},formatIDR:value=>`Rp ${value}`,apiError:(err,fallback)=>err.response?.data?.detail||fallback}));
let host,root;
const colors=[{id:'black',code:'04S',name:'Black',kind:'solid',group:'fashion',hex_color:'#000000',additional_price:60000},
  {id:'blue-gradient',code:'02G',name:'Blue Gradient',kind:'gradient',group:'fashion',hex_color:'#81A5C5',mid_hex_color:null,bottom_hex_color:'#FFFFFF',additional_price:60000},
  {id:'therapy',code:'39S',name:'Therapeutic Orange',kind:'solid',group:'therapeutic',hex_color:'#F79348',additional_price:120000}];
const first={id:'a',quantity:2,product:{name:'Frame A',product_type:'frame'}};
const second={id:'b',quantity:1,product:{name:'Paket B',product_type:'package'}};
const click=node=>act(async()=>node.click());
const type=(node,value)=>act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(node,value);node.dispatchEvent(new Event('input',{bubbles:true}));});
beforeEach(()=>{jest.clearAllMocks();api.get.mockResolvedValue({data:{items:colors}});host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});

test('loads color cards on demand and saves one choice per line, including a quantity of two',async()=>{
  const changed=jest.fn(),saved=jest.fn();
  function Demo(){const[items,setItems]=useState([first,second]);return <CheckoutTinting items={items} onDirtyChange={changed} onSaved={item=>{saved(item);setItems(previous=>previous.map(row=>row.id===item.id?item:row));}}/>;}
  await act(async()=>root.render(<Demo/>));
  expect(api.get).not.toHaveBeenCalled();
  expect(host.querySelector('[data-testid=tinting-a]').textContent).toContain('seluruh 2 produk');
  await click(host.querySelector('[data-testid=choose-tinting-a]'));
  expect(api.get).toHaveBeenCalledWith('/tinting');
  expect(host.querySelectorAll('input[type=radio]')).toHaveLength(3);
  api.patch.mockResolvedValue({data:{cart_item:{...first,tinting:colors[0],tinting_price:60000}}});
  await click(host.querySelector('input[type=radio]'));
  expect(api.patch).toHaveBeenCalledWith('/cart/a/tinting',{tinting_id:'black'});
  expect(changed).toHaveBeenCalledWith('tinting:a',true);
  expect(changed).toHaveBeenLastCalledWith('tinting:a',false);
  expect(host.querySelector('[data-testid=tinting-a]').textContent).toContain('04S');
  expect(host.querySelector('[data-testid=tinting-b] [data-testid=tinting-details]')).toBeNull();
  await click(host.querySelector('[data-testid=choose-tinting-b]'));
  expect(api.get).toHaveBeenCalledTimes(1);
  api.patch.mockResolvedValue({data:{cart_item:{...second,tinting:colors[2],tinting_price:120000}}});
  await click(host.querySelectorAll('[data-testid=tinting-b] input[type=radio]')[2]);
  expect(api.patch).toHaveBeenLastCalledWith('/cart/b/tinting',{tinting_id:'therapy'});
  expect(saved).toHaveBeenCalledTimes(2);
});

test('search filters the cards without changing or saving an existing choice',async()=>{
  await act(async()=>root.render(<CheckoutTinting items={[first]} onDirtyChange={jest.fn()} onSaved={jest.fn()}/>));
  await click(host.querySelector('[data-testid=choose-tinting-a]'));
  await type(host.querySelector('input[type=search]'),'39S');
  expect(host.querySelectorAll('input[type=radio]')).toHaveLength(1);
  expect(host.textContent).toContain('Therapeutic Orange');
  expect(api.patch).not.toHaveBeenCalled();
});

test('failed or uncertain saves keep checkout dirty until retry succeeds',async()=>{
  const changed=jest.fn();
  await act(async()=>root.render(<CheckoutTinting items={[first]} onDirtyChange={changed} onSaved={jest.fn()}/>));
  await click(host.querySelector('[data-testid=choose-tinting-a]'));
  api.patch.mockRejectedValue(new Error('network'));
  await click(host.querySelector('input[type=radio]'));
  expect(changed).toHaveBeenLastCalledWith('tinting:a',true);
  expect(host.querySelector('[role=alert]')).not.toBeNull();
  api.patch.mockResolvedValue({data:{cart_item:{...first,tinting:colors[0],tinting_price:60000}}});
  await click([...host.querySelectorAll('button')].find(button=>button.textContent==='Coba simpan lagi'));
  expect(changed).toHaveBeenLastCalledWith('tinting:a',false);
});

test('removing a choice confirms a server update, and accessories do not show tinting',async()=>{
  const saved=jest.fn();
  await act(async()=>root.render(<CheckoutTinting items={[{...first,tinting:colors[0]},{id:'x',product:{product_type:'accessory',name:'Case'}}]} onDirtyChange={jest.fn()} onSaved={saved}/>));
  expect(host.querySelector('[data-testid=tinting-x]')).toBeNull();
  api.patch.mockResolvedValue({data:{cart_item:{...first,tinting:null,tinting_price:0}}});
  await click(host.querySelector('[aria-label="Hapus tinting Frame A"]'));
  expect(api.patch).toHaveBeenCalledWith('/cart/a/tinting',{tinting_id:null});
  expect(saved).toHaveBeenCalledWith(expect.objectContaining({tinting:null}));
});
