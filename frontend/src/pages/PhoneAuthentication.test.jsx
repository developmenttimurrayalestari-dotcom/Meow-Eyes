jest.mock('../components/FacebookAuthButton',()=>()=>null);
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import RegisterPage from './RegisterPage';
import LoginPage from './LoginPage';
import { toast } from 'sonner';

const mockRegister=jest.fn(), mockLogin=jest.fn();
let mockPhoneEnabled=true;
jest.mock('../contexts/AuthContext',()=>({useAuth:()=>({register:mockRegister,login:mockLogin,phoneEnabled:mockPhoneEnabled})}));
jest.mock('../components/GoogleAuthButton',()=>()=> <p>Google available separately</p>);
jest.mock('../lib/api',()=>({apiError:(error,fallback)=>Array.isArray(error.response?.data?.detail)?error.response.data.detail.map(item=>item.msg).join('; '):error.response?.data?.detail||fallback}));
jest.mock('sonner',()=>({toast:{success:jest.fn(),error:jest.fn()}}));
let root,host;
const type=async(node,value)=>act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(node,value);node.dispatchEvent(new Event('input',{bubbles:true}));});
beforeEach(()=>{jest.clearAllMocks();mockPhoneEnabled=true;mockRegister.mockResolvedValue({name:'Customer',has_pin:false});mockLogin.mockResolvedValue({name:'Customer',has_pin:true});host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});
async function mount(path){await act(async()=>root.render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/register" element={<RegisterPage/>}/><Route path="/login" element={<LoginPage/>}/><Route path="/setup-pin" element={<p>Setup PIN</p>}/><Route path="/" element={<p>Signed in</p>}/></Routes></MemoryRouter>));}
const submit=()=>act(async()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));

test('phone registration requires no email and preserves PIN onboarding',async()=>{
 await mount('/register');
 await act(async()=>[...host.querySelectorAll('button')].find(node=>node.textContent==='Nomor telepon').click());
 expect(host.querySelector('input[type="email"]')).toBeNull();
 await type(host.querySelector('[data-testid="register-name"]'),'Phone Customer');
 await type(host.querySelector('[data-testid="register-phone"]'),'081234567890');
 await type(host.querySelector('[data-testid="register-password"]'),'Example123!');
 await submit();
 expect(mockRegister).toHaveBeenCalledWith({name:'Phone Customer',phone:'081234567890',password:'Example123!'});
 expect(host.textContent).toBe('Setup PIN');
});

test('switching back to email never sends the stale phone',async()=>{
 await mount('/register');
 const button=label=>[...host.querySelectorAll('button')].find(node=>node.textContent===label);
 await act(async()=>button('Nomor telepon').click());
 await type(host.querySelector('[data-testid="register-phone"]'),'081234567890');
 await act(async()=>button('Email').click());
 await type(host.querySelector('[data-testid="register-name"]'),'Email Customer');
 await type(host.querySelector('[data-testid="register-email"]'),'email@example.com');
 await type(host.querySelector('[data-testid="register-password"]'),'Example123!');
 await submit();
 expect(mockRegister).toHaveBeenCalledWith({name:'Email Customer',email:'email@example.com',password:'Example123!'});
});

test.each(['081234567890','email@example.com'])('login accepts %s in the same input',async identifier=>{
 await mount('/login');const input=host.querySelector('[data-testid="login-email"]');
 expect(input.type).toBe('text');
 await type(input,identifier);await type(host.querySelector('[data-testid="login-password"]'),'Example123!');await submit();
 expect(mockLogin).toHaveBeenCalledWith(identifier,'Example123!');expect(host.textContent).toBe('Signed in');
});

test('invalid phone API validation is displayed as text',async()=>{
 mockRegister.mockRejectedValue({response:{data:{detail:[{msg:'Nomor telepon tidak valid'}]}}});
 await mount('/register');await type(host.querySelector('[data-testid="register-password"]'),'Example123!');await submit();
 expect(toast.error).toHaveBeenCalledWith('Nomor telepon tidak valid');
});


test('disabled phone authentication hides the option and uses an email login field',async()=>{
 mockPhoneEnabled=false;await mount('/register');
 expect(host.querySelector('[aria-label="Metode registrasi"]')).toBeNull();
 expect(host.querySelector('[data-testid="register-phone"]')).toBeNull();
 expect(host.querySelector('[data-testid="register-email"]').type).toBe('email');
 await act(async()=>root.render(<MemoryRouter><LoginPage/></MemoryRouter>));
 expect(host.querySelector('[data-testid="login-email"]').type).toBe('email');
});
