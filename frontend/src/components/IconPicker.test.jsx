import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import IconPicker from './IconPicker';
import AppIcon from './AppIcon';
import {loadIconCatalog} from '../lib/iconLibrary';
let host,root;
const click=async node=>act(async()=>node.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})));
const type=async value=>act(async()=>{const input=host.querySelector('input[type=search]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,value);input.dispatchEvent(new Event('input',{bubbles:true}));});
const button=text=>[...host.querySelectorAll('button')].find(node=>node.textContent===text);
beforeEach(()=>{host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});

test('searches the full local icon collection, previews results, and selects a real Lucide name',async()=>{
  const onChange=jest.fn();
  await act(async()=>root.render(<IconPicker value="frame" onChange={onChange}/>));
  expect(host.querySelector('[data-testid="selected-icon-preview"] svg')).not.toBeNull();
  await click(button('Pilih ikon'));
  expect(Object.keys((await loadIconCatalog()).icons).length).toBeGreaterThan(1000);
  expect(host.querySelectorAll('[aria-label^="Pilih ikon "]').length).toBeLessThanOrEqual(48);
  await type('kamera');
  expect(host.querySelector('[aria-label="Pilih ikon camera"] svg')).not.toBeNull();
  await click(host.querySelector('[aria-label="Pilih ikon camera"]'));
  expect(onChange).toHaveBeenCalledWith('lucide:camera');
  expect(host.querySelector('input[type=search]')).toBeNull();
});

test('supports pagination, a no-results state, and explicitly removing an icon',async()=>{
  const onChange=jest.fn();await act(async()=>root.render(<IconPicker value="home" onChange={onChange}/>));
  await click(button('Pilih ikon'));const first=host.querySelector('[aria-label^="Pilih ikon "]').getAttribute('aria-label');
  await click(button('Berikutnya'));
  expect(host.querySelector('[aria-label^="Pilih ikon "]').getAttribute('aria-label')).not.toBe(first);
  await type('not-an-icon-xyz-987');expect(host.textContent).toContain('Ikon tidak ditemukan');
  await click(button('Tanpa ikon'));expect(onChange).toHaveBeenCalledWith('none');
});

test('chosen icons render on the storefront and arbitrary names are never treated as markup',async()=>{
  await act(async()=>{root.render(<AppIcon name="lucide:camera" data-testid="customer-icon"/>);await loadIconCatalog();});
  expect(host.querySelector('svg')).not.toBeNull();expect(host.querySelector('svg path')).not.toBeNull();
  for(const name of ['<script>bad</script>','constructor','__proto__']){
    await act(async()=>root.render(<AppIcon name={name}/>));
    expect(host.querySelector('script')).toBeNull();expect(host.querySelector('svg')).not.toBeNull();
  }
});
