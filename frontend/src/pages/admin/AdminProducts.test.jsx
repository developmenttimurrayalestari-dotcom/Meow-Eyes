import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import AdminProducts from './AdminProducts';
import { api } from '../../lib/api';

jest.mock('../../lib/api', () => ({ api: {get:jest.fn(),post:jest.fn()}, apiError:(e,fallback)=>e.response?.data?.detail||fallback, formatIDR:value=>`Rp ${value}` }));
jest.mock('sonner', () => ({toast:{success:jest.fn(),error:jest.fn()}}));
jest.mock('../../components/ImagePicker', () => () => null);
jest.mock('../../components/RichTextEditor', () => ({ value, onChange, testId }) => <textarea data-testid={testId} value={value} onChange={event => onChange(event.target.value)} />);
jest.mock('./FrameSpecificationEditor', () => () => null);

let root,host,products;
const makeProduct = (id,is_active=true) => ({id,name:`Frame ${id}`,sku:id,product_type:'frame',price:100,is_active,main_image:'/frame.png',variants:[]});
const click = async node => act(async()=>node.click());
const mount = async()=>act(async()=>root.render(<AdminProducts />));
beforeEach(()=>{
  jest.clearAllMocks();jest.spyOn(window,'confirm').mockReturnValue(true);
  products=[makeProduct('a'),makeProduct('b',false)];
  api.get.mockImplementation((url,config)=>{
    if(url==='/admin/products'){
      const {q='',page=1,limit=50}=config.params;
      const filtered=products.filter(product=>product.name.toLowerCase().includes(q.toLowerCase()));
      return Promise.resolve({data:{products:filtered.slice((page-1)*limit,page*limit),total:filtered.length}});
    }
    return Promise.resolve({data:{categories:[],brands:[]}});
  });
  api.post.mockImplementation((url,{action,product_ids})=>{
    products=action==='delete'?products.filter(product=>!product_ids.includes(product.id)):products.map(product=>product_ids.includes(product.id)?{...product,is_active:false}:product);
    return Promise.resolve({data:{ok:true}});
  });
  host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);
});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.restoreAllMocks();});

test('row actions distinguish deactivation from deletion, including inactive products',async()=>{
  await mount();
  expect(host.querySelector('[data-testid="deactivate-b"]').disabled).toBe(true);
  expect(host.querySelector('[data-testid="delete-b"]').disabled).toBe(false);
  await click(host.querySelector('[data-testid="deactivate-a"]'));
  expect(api.post).toHaveBeenLastCalledWith('/admin/products/bulk-actions',{action:'deactivate',product_ids:['a']});
  expect(host.querySelector('[data-testid="product-row-a"]')).not.toBeNull();
  expect(host.querySelector('[data-testid="deactivate-a"]').disabled).toBe(true);
  await click(host.querySelector('[data-testid="delete-b"]'));
  expect(api.post).toHaveBeenLastCalledWith('/admin/products/bulk-actions',{action:'delete',product_ids:['b']});
  expect(host.querySelector('[data-testid="product-row-b"]')).toBeNull();
  expect(host.querySelector('[data-testid="product-row-a"]')).not.toBeNull();
});

test('select all supports bulk deactivation and clears selection after success',async()=>{
  await mount();
  const header=host.querySelector('[aria-label="Pilih semua produk pada halaman ini"]');
  expect(host.querySelector('[data-testid="bulk-delete-products"]').disabled).toBe(true);
  await click(host.querySelector('[aria-label="Pilih Frame a"]'));
  expect(header.indeterminate).toBe(true);
  await click(header);
  expect(header.checked).toBe(true);expect(header.indeterminate).toBe(false);
  await click(host.querySelector('[data-testid="bulk-deactivate-products"]'));
  expect(api.post).toHaveBeenCalledWith('/admin/products/bulk-actions',{action:'deactivate',product_ids:['a','b']});
  expect(host.querySelectorAll('tbody tr')).toHaveLength(2);
  expect(host.querySelector('[role="status"]').textContent).toBe('0 produk dipilih');
});

test('bulk deletion removes selected rows after confirmation',async()=>{
  await mount();
  await click(host.querySelector('thead input'));
  await click(host.querySelector('[data-testid="bulk-delete-products"]'));
  expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining('Hapus 2 produk terpilih'));
  expect(api.post).toHaveBeenCalledWith('/admin/products/bulk-actions',{action:'delete',product_ids:['a','b']});
  expect(host.querySelectorAll('tbody tr')).toHaveLength(0);
  expect(host.textContent).toContain('Belum ada produk.');
});

test('cancelling and rejecting a bulk action preserve selected rows',async()=>{
  await mount();await click(host.querySelector('thead input'));
  window.confirm.mockReturnValue(false);
  await click(host.querySelector('[data-testid="bulk-delete-products"]'));
  expect(api.post).not.toHaveBeenCalled();
  expect(host.querySelector('[role="status"]').textContent).toBe('2 produk dipilih');
  window.confirm.mockReturnValue(true);
  api.post.mockRejectedValue({response:{data:{detail:'Sebagian produk tidak ditemukan.'}}});
  await click(host.querySelector('[data-testid="bulk-delete-products"]'));
  expect(host.querySelector('[role="alert"]').textContent).toContain('Sebagian produk tidak ditemukan.');
  expect(host.querySelectorAll('tbody tr')).toHaveLength(2);
  expect(host.querySelector('[role="status"]').textContent).toBe('2 produk dipilih');
  expect(host.querySelector('[data-testid="bulk-delete-products"]').disabled).toBe(false);
});

test('changing search and page clears selections and never selects hidden products',async()=>{
  products=Array.from({length:51},(_,i)=>makeProduct(String(i+1)));
  await mount();await click(host.querySelector('thead input'));
  expect(host.querySelector('[role="status"]').textContent).toBe('50 produk dipilih');
  await click([...host.querySelectorAll('button')].find(node=>node.textContent==='Berikutnya'));
  expect(host.querySelector('[role="status"]').textContent).toBe('0 produk dipilih');
  expect(host.querySelectorAll('tbody tr')).toHaveLength(1);
  await click(host.querySelector('thead input'));
  await click(host.querySelector('[data-testid="bulk-delete-products"]'));
  expect(api.post).toHaveBeenCalledWith('/admin/products/bulk-actions',{action:'delete',product_ids:['51']});
  await click(host.querySelector('thead input'));
  const search=host.querySelector('[data-testid="admin-product-search"]');
  await act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(search,'Frame 2');search.dispatchEvent(new Event('input',{bubbles:true}));});
  expect(host.querySelector('[role="status"]').textContent).toBe('0 produk dipilih');
  expect(host.querySelector('[data-testid="product-row-1"]')).toBeNull();
});

test('buttons are disabled while an action is pending to prevent duplicate requests',async()=>{
  let resolve;api.post.mockImplementation(()=>new Promise(done=>{resolve=done;}));
  await mount();await click(host.querySelector('thead input'));
  await click(host.querySelector('[data-testid="bulk-delete-products"]'));
  expect(host.querySelector('[data-testid="bulk-delete-products"]').disabled).toBe(true);
  expect(host.querySelector('thead input').disabled).toBe(true);
  await click(host.querySelector('[data-testid="bulk-deactivate-products"]'));
  expect(api.post).toHaveBeenCalledTimes(1);
  await act(async()=>resolve({data:{ok:true}}));
  expect(host.querySelector('[data-testid="admin-product-search"]').disabled).toBe(false);
});

test('duplicate opens the independent inactive copy in Edit and leaves the original unchanged',async()=>{
  const copy = { ...makeProduct('copy',false), name:'Frame a (Salinan)', sku:'a-COPY-NEW', description:'Copied description',
    gallery:[], category_ids:[], badges:[], segments:[], variants:[{id:'copy-variant',sku:'VAR-COPY-NEW',stock:0,reserved:0}] };
  api.post.mockImplementation(async url=>{
    expect(url).toBe('/admin/products/a/duplicate');
    products=[copy,...products]; return {data:{ok:true,product:copy}};
  });
  await mount();
  await click(host.querySelector('[data-testid="duplicate-a"]'));
  expect(api.post).toHaveBeenCalledTimes(1);
  expect(host.querySelector('[data-testid="product-form"]')).not.toBeNull();
  expect(host.querySelector('[data-testid="pf-name"]').value).toBe('Frame a (Salinan)');
  expect(host.querySelector('[aria-label="SKU produk"]').value).toBe('a-COPY-NEW');
  expect(host.querySelector('[data-testid="pf-active"]').checked).toBe(false);
  expect(host.querySelector('[data-testid="product-row-a"]')).not.toBeNull();
  expect(host.querySelector('[data-testid="product-row-copy"]').textContent).toContain('Nonaktif');
  expect(products.find(product=>product.id==='a').is_active).toBe(true);
  expect(window.confirm).not.toHaveBeenCalled();
});

test('a failed duplicate preserves the list and repeated clicks cannot send concurrent copies',async()=>{
  let reject;
  api.post.mockImplementation(()=>new Promise((_resolve,fail)=>{reject=fail;}));
  await mount();
  await click(host.querySelector('[data-testid="duplicate-a"]'));
  expect(host.querySelector('[data-testid="duplicate-a"]').disabled).toBe(true);
  await click(host.querySelector('[data-testid="duplicate-a"]'));
  expect(api.post).toHaveBeenCalledTimes(1);
  await act(async()=>reject({response:{data:{detail:'Produk sudah dihapus dari katalog'}}}));
  expect(host.querySelector('[role="alert"]').textContent).toContain('Produk sudah dihapus');
  expect(host.querySelectorAll('tbody tr')).toHaveLength(2);
  expect(host.querySelector('[data-testid="product-form"]')).toBeNull();
  expect(host.querySelector('[data-testid="duplicate-a"]').disabled).toBe(false);
});
