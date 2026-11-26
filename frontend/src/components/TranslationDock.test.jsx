import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import {MemoryRouter,useNavigate} from 'react-router-dom';
import {ConveyThisBoundary,StandaloneTranslation} from './ConveyThisTranslation';
import {conveyThisSnapshot,resetConveyThis} from '../lib/conveyThis';

let root,host,navigate,originalKey;
const click=async node=>act(async()=>node.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})));
const toggle=()=>host.querySelector('[aria-label="Translate — pilih bahasa"]');
const panel=()=>host.querySelector('[data-testid="translation-panel"]');
const changed=language=>document.dispatchEvent(new CustomEvent('conveythis-language-changed',{detail:{language:{code2:language}}}));
function Nav(){navigate=useNavigate();return <main>Halaman pelanggan</main>;}
const mount=async()=>act(async()=>root.render(<MemoryRouter><ConveyThisBoundary><Nav/></ConveyThisBoundary></MemoryRouter>));
function nativeWidget(){
  const widget=document.createElement('div');widget.id='conveythis-wrapper';
  const controls={};
  for(const[code,label]of[['id','Indonesia'],['en','English']]){
    const control=document.createElement('div');control.className='conveythis-widget-language';
    const title=document.createElement('span');title.className='language_title';title.textContent=label;
    control.appendChild(title);widget.appendChild(control);controls[code]=control;
  }
  const branding=document.createElement('a');branding.textContent='ConveyThis';branding.href='https://www.conveythis.com';widget.appendChild(branding);
  document.body.appendChild(widget);
  document.getElementById('meow-conveythis-script')?.dispatchEvent(new Event('load'));
  return{widget,controls,branding};
}
beforeEach(()=>{
  originalKey=process.env.REACT_APP_CONVEYTHIS_API_KEY;process.env.REACT_APP_CONVEYTHIS_API_KEY='pub_test';
  window.history.replaceState(null,'','/');resetConveyThis();
  host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);
});
afterEach(async()=>{
  await act(async()=>root.unmount());resetConveyThis();host.remove();document.getElementById('conveythis-wrapper')?.remove();
  if(originalKey===undefined)delete process.env.REACT_APP_CONVEYTHIS_API_KEY;else process.env.REACT_APP_CONVEYTHIS_API_KEY=originalKey;
});

test('starts collapsed and relocates the same native widget and branding inside the dock',async()=>{
  await mount();let native;await act(async()=>{native=nativeWidget();});
  expect(host.querySelector('[data-testid="translation-dock"]').hidden).toBe(false);
  expect(toggle().getAttribute('aria-expanded')).toBe('false');
  expect(panel().getAttribute('aria-hidden')).toBe('true');expect(panel().hasAttribute('inert')).toBe(true);
  expect(native.widget.parentElement.id).toBe('meow-conveythis-widget');
  expect(native.widget.contains(native.branding)).toBe(true);
  expect(document.documentElement.classList.contains('meow-conveythis-docked')).toBe(true);
  await click(toggle());expect(panel().getAttribute('aria-hidden')).toBe('false');expect(panel().hasAttribute('inert')).toBe(false);
});

test('native language choices show progress and close only after the SDK confirms the language',async()=>{
  await mount();let native;await act(async()=>{native=nativeWidget();});await click(toggle());
  await act(async()=>changed('id'));
  expect(panel().getAttribute('aria-hidden')).toBe('false');
  const translated=jest.fn();native.controls.en.addEventListener('click',translated);
  await click(native.controls.en);
  expect(translated).toHaveBeenCalledTimes(1);expect(conveyThisSnapshot().phase).toBe('translating');
  expect(panel().getAttribute('aria-hidden')).toBe('false');
  expect(panel().textContent).toContain('Menerjemahkan halaman');
  await act(async()=>changed('en'));
  expect(document.documentElement.lang).toBe('en');expect(panel().getAttribute('aria-hidden')).toBe('true');expect(document.activeElement).toBe(toggle());
});

test('Escape, outside clicks and navigation close the panel without losing native controls',async()=>{
  await mount();let native;await act(async()=>{native=nativeWidget();});await click(toggle());
  await act(async()=>document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true})));
  expect(panel().getAttribute('aria-hidden')).toBe('true');await click(toggle());
  await act(async()=>document.body.dispatchEvent(new Event('pointerdown',{bubbles:true})));
  expect(panel().getAttribute('aria-hidden')).toBe('true');await click(toggle());
  await act(async()=>navigate('/shop-now'));
  expect(panel().getAttribute('aria-hidden')).toBe('true');expect(document.getElementById('conveythis-wrapper')).toBe(native.widget);
});

test('supports an existing embed without adding another SDK and rehomes widgets rebuilt by the vendor',async()=>{
  delete process.env.REACT_APP_CONVEYTHIS_API_KEY;
  const native=nativeWidget();await mount();
  expect(document.getElementById('meow-conveythis-script')).toBeNull();
  expect(conveyThisSnapshot().configured).toBe(true);expect(native.widget.parentElement.id).toBe('meow-conveythis-widget');
  await act(async()=>{native.widget.remove();nativeWidget();});
  expect(document.querySelectorAll('#conveythis-wrapper')).toHaveLength(1);
  expect(document.getElementById('conveythis-wrapper').parentElement.id).toBe('meow-conveythis-widget');
});

test('standalone measurement pages use the same dock and native div controls support the keyboard',async()=>{
  await act(async()=>root.render(<StandaloneTranslation><main>Meowsurement</main></StandaloneTranslation>));
  let native;await act(async()=>{native=nativeWidget();});
  await act(async()=>window.dispatchEvent(new Event('meow:open-translation')));
  expect(panel().getAttribute('aria-hidden')).toBe('false');
  expect(native.controls.en.getAttribute('role')).toBe('button');expect(native.controls.en.tabIndex).toBe(0);
  const selected=jest.fn();native.controls.en.addEventListener('click',selected);
  await act(async()=>native.controls.en.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true})));
  expect(selected).toHaveBeenCalledTimes(1);
});
