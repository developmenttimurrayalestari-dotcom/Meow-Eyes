import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import {MemoryRouter} from 'react-router-dom';
import AccountBenefits from './AccountBenefits';
import {api} from '../lib/api';
jest.mock('../contexts/AuthContext',()=>({useAuth:()=>({user:{user_id:'u',name:'Customer',email:'customer@example.test'},refreshMe:jest.fn()})}));
jest.mock('../lib/api',()=>({api:{get:jest.fn(),post:jest.fn()},apiError:e=>e.response?.data?.detail||'Gagal'}));
jest.mock('sonner',()=>({toast:{success:jest.fn()}}));
let host,root,checked;
const click=async n=>act(async()=>n.dispatchEvent(new MouseEvent('click',{bubbles:true})));
beforeEach(()=>{jest.clearAllMocks();checked=false;host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);
  api.get.mockImplementation(()=>Promise.resolve({data:{email:'customer@example.test',email_delivery_ready:true,email_verified_at:null,referral_code:'ME123',referral_count:2,checkin_today:checked,config:{checkin_enabled:true,use_streak:false,daily_points:3,checkin_expiry_days:30,referral_enabled:true,referral_trigger:'first_order'}}}));
});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});
const mount=async()=>act(async()=>root.render(<MemoryRouter><AccountBenefits/></MemoryRouter>));
test('check-in becomes unavailable after the server records today',async()=>{
  api.post.mockImplementation(()=>{checked=true;return Promise.resolve({data:{}});});await mount();
  await click([...host.querySelectorAll('button')].find(n=>n.textContent==='Check-in Sekarang'));
  expect(api.post).toHaveBeenCalledWith('/account/check-in');
  expect([...host.querySelectorAll('button')].find(n=>n.textContent==='Sudah Check-in').disabled).toBe(true);
  expect(host.querySelector('[aria-label="Link referral"]').value).toContain('/register?ref=ME123');
});
test('email resend respects the server cooldown',async()=>{
  api.post.mockRejectedValue({response:{status:429,headers:{'retry-after':'60'},data:{detail:'Tunggu sebelum kirim ulang'}}});await mount();
  await click([...host.querySelectorAll('button')].find(n=>n.textContent==='Kirim Ulang Verifikasi'));
  const button=[...host.querySelectorAll('button')].find(n=>n.textContent.includes('Kirim ulang dalam'));
  expect(button.disabled).toBe(true);expect(host.querySelector('[role="alert"]').textContent).toContain('Tunggu');
});
