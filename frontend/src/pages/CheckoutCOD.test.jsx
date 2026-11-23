import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import CheckoutPage from './CheckoutPage';
import { api } from '../lib/api';
const mockNavigate=jest.fn();
jest.mock('react-router-dom', () => ({ ...jest.requireActual('react-router-dom'),useNavigate:()=>mockNavigate }));
jest.mock('../contexts/AuthContext',()=>({useAuth:()=>({user:{user_id:'customer',has_pin:true},refreshMe:jest.fn(),refreshCartCount:jest.fn()})}));
jest.mock('../lib/api',()=>({api:{get:jest.fn(),post:jest.fn()},apiError:(e,f)=>e.response?.data?.detail||f,imageSrc:v=>v,formatIDR:v=>`Rp ${v||0}`}));
jest.mock('sonner',()=>({toast:{success:jest.fn(),warning:jest.fn()}}));
let host,root;
const flush=async()=>act(async()=>{await new Promise(r=>setTimeout(r,0));});
const click=async n=>act(async()=>n.dispatchEvent(new MouseEvent('click',{bubbles:true})));
beforeEach(()=>{
  jest.clearAllMocks(); sessionStorage.clear(); host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);
  api.get.mockImplementation(url=>Promise.resolve({data:{
    '/addresses':{addresses:[{id:'address',label:'Rumah',recipient:'Customer',city:'Jakarta',is_default:true}]},
    '/cart':{items:[{id:'cart',quantity:1,unit_price:115000,subtotal:115000,frame_price:100000,addon_price:15000,addons:[{product_id:'case',name:'Case',unit_price:15000}],product:{name:'Frame',main_image:'frame.png'}}]},
    '/integrations/status':{payment:{ready:false},shipping:{ready:true},cod:{ready:true}},
    '/roulette/my-rewards':{spins:[]},'/points/logs':{},'/cashback-events':{events:[]},
  }[url]||{indexes:[]}}));
  api.post.mockImplementation((url,body)=>{
    if(url==='/checkout/shipping-options')return Promise.resolve({data:{options:[{quote_id:body.payment_mode+'-quote',courier_code:'JNE',service_code:'REG',cost:10000}]}});
    if(url==='/checkout/preview')return Promise.resolve({data:{subtotal:115000,product_subtotal:100000,addon_subtotal:15000,total:125000,shipping:{cost:10000}}});
    if(url==='/checkout/confirm')return Promise.resolve({data:{order:{id:'cod-order',payment_mode:'cod',order_number:'MEOW1'},payment:{provider:'cod',payment_url:null}}});
    return Promise.reject(new Error('unexpected request'));
  });
});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});
test('COD remains available without DOKU and navigates directly to its order',async()=>{
  await act(async()=>root.render(<MemoryRouter initialEntries={[{pathname:'/checkout',state:{selected_item_ids:['cart']}}]}><CheckoutPage/></MemoryRouter>));await flush();await flush();
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(true);
  expect(host.querySelector('[data-testid="checkout-addon-subtotal"]').textContent).toContain('Rp 15000');
  await click(host.querySelector('input[name="payment-mode"][value="cod"]'));await flush();await flush();
  for(let i=0;i<6;i++)await act(async()=>{const n=host.querySelector(`[data-testid="checkout-pin-${i}"]`);Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(n,String(i+1));n.dispatchEvent(new Event('input',{bubbles:true}));});
  const button=host.querySelector('[data-testid="submit-order-btn"]');expect(button.disabled).toBe(false);expect(button.textContent).toBe('Buat Pesanan COD');
  await click(button);await flush();
  expect(api.post).toHaveBeenCalledWith('/checkout/confirm',expect.objectContaining({payment_mode:'cod',shipping_quote_id:'cod-quote'}),expect.any(Object));
  expect(mockNavigate).toHaveBeenCalledWith('/orders/cod-order');
  expect(mockNavigate.mock.calls.some(([url])=>url.startsWith('/payment/'))).toBe(false);
});
