import React, { act, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import ProductMasterFields from './ProductMasterFields';
import MasterCatalogFilters from './MasterCatalogFilters';
import AdminCategories from '../pages/admin/AdminCategories';
import AdminProducts from '../pages/admin/AdminProducts';
import ProductsPage from '../pages/ProductsPage';
import { api } from '../lib/api';

jest.mock('../lib/api', () => ({ api: { get: jest.fn(), post: jest.fn(), put: jest.fn(), delete: jest.fn() }, apiError: e => e.message, formatIDR: value => `Rp ${value}`, imageSrc: value => value }));
jest.mock('sonner', () => ({ toast: { success: jest.fn(), error: jest.fn() } }));
jest.mock('./ImagePicker', () => () => <div>Gambar</div>);
jest.mock('./RichTextEditor', () => ({value,onChange,testId,label}) => <textarea aria-label={label} data-testid={testId} value={value} onChange={e=>onChange(e.target.value)} />);
jest.mock('./ProductCard', () => ({ product }) => <div>{product.name}</div>);
jest.mock('../pages/admin/FrameSpecificationEditor', () => () => null);

const categories = [
  ['frame','Frame','product_type','frame'],['lens','Lensa','product_type','lens'],['package','Paket','product_type','package'],
  ['male','Pria','gender','pria'],['female','Wanita','gender','wanita'],['round','Round','frame_shape','round'],
  ['titanium','Titanium','material','titanium'],['single','Single Vision','lens_type','single-vision'],
].map(([id,name,group_type,code]) => ({ id,name,group_type,code,is_active:true }));
const product = { id:'p',name:'Frame contoh',sku:'EXAMPLE',description:'Deskripsi',product_type:'frame',price:100,
  category_ids:['frame','male','round'],segments:['Pria'],main_image:'/frame.png',gallery:[],variants:[],badges:[],is_active:true };
let host, root;
const mount = async element => act(async () => root.render(element));
const click = async node => act(async () => node.click());
const type = async (node,value) => act(async () => {
  Object.getOwnPropertyDescriptor(node instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype,'value').set.call(node,value);
  node.dispatchEvent(new Event('input',{bubbles:true}));
});
const submit = async node => act(async () => node.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
beforeEach(() => {
  jest.clearAllMocks();
  api.get.mockImplementation(url => Promise.resolve({data: url.endsWith('/categories') ? {categories} : url.endsWith('/brands') ? {brands:[]} : {products:[product],total:1}}));
  api.post.mockResolvedValue({data:{}}); api.put.mockResolvedValue({data:{}}); api.delete.mockResolvedValue({data:{}});
  host=document.createElement('div'); document.body.appendChild(host); root=createRoot(host);
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); jest.restoreAllMocks(); });

test('product groups allow multiple tags and preserve them when changing the product kind', async () => {
  let latest;
  function Form() {
    const [form,setForm]=useState(product); latest=form;
    return <ProductMasterFields categories={categories} form={form} onChange={setForm} />;
  }
  await mount(<Form />);
  await click(host.querySelector('[data-testid="product-master-material"] input'));
  await click([...host.querySelectorAll('label')].find(node=>node.textContent==='Lensa').querySelector('input'));
  expect(latest.product_type).toBe('lens');
  expect(latest.category_ids.sort()).toEqual(['lens','male','round','titanium']);
  expect(host.querySelectorAll('[data-testid="product-master-product_type"] input[type="radio"]:checked')).toHaveLength(1);
  expect(host.querySelector('select')).toBeNull();
});

test('collection masters are absent from product fields and submitted tags', async () => {
  const legacy={id:'legacy',name:'Round pria',group_type:'collection',is_active:true};
  let latest;
  await mount(<ProductMasterFields categories={[...categories,legacy]} form={{...product,category_ids:['frame','legacy','male']}} onChange={value=>{latest=value;}} />);
  expect(host.querySelector('[data-testid="product-master-collection"]')).toBeNull();
  await click(host.querySelector('[data-testid="product-master-material"] input'));
  expect(latest.category_ids).not.toContain('legacy');
});

test('brand uses a separate single choice and preserves product category tags', async () => {
  let latest;
  function Form() {
    const [form,setForm]=useState({...product,brand_id:'old'}); latest=form;
    return <ProductMasterFields categories={categories} brands={[{id:'old',name:'Brand lama',is_active:false},{id:'new',name:'Leinz',is_active:true}]} form={form} onChange={setForm} />;
  }
  await mount(<Form />);
  const brand=host.querySelector('[data-testid="product-master-brand"]');
  expect(brand.querySelector('input:checked').closest('label').textContent).toContain('Brand lama');
  await click([...brand.querySelectorAll('label')].find(node=>node.textContent==='Leinz').querySelector('input'));
  expect(latest.brand_id).toBe('new'); expect(latest.category_ids).toEqual(product.category_ids);
  expect(brand.querySelectorAll('input:checked')).toHaveLength(1);
  expect(brand.textContent).not.toContain('Brand lama');
  await click([...brand.querySelectorAll('label')].find(node=>node.textContent==='Tanpa brand').querySelector('input'));
  expect(latest.brand_id).toBeNull();
});

test('Brand tab manages existing brand records using brand endpoints', async () => {
  api.get.mockImplementation(url=>Promise.resolve({data:url==='/admin/brands'?{brands:[{id:'brand',name:'Leinz',slug:'leinz',is_active:true}]}:{categories}}));
  jest.spyOn(window,'confirm').mockReturnValue(true);
  await mount(<AdminCategories />);
  await click([...host.querySelectorAll('[role="tab"]')].find(node=>node.textContent==='Brand'));
  expect(host.querySelector('table').textContent).toContain('Leinz');
  await click(host.querySelector('[aria-label="Edit Leinz"]'));
  await type(host.querySelector('[role="dialog"] input'),'Leinz premium');
  await submit(host.querySelector('form'));
  expect(api.put).toHaveBeenCalledWith('/admin/brands/brand',{name:'Leinz premium',slug:'leinz',is_active:true});
  await click([...host.querySelectorAll('button')].find(node=>node.textContent.includes('Tambah Brand')));
  await type(host.querySelector('[role="dialog"] input'),'Brand baru');
  await submit(host.querySelector('form'));
  expect(api.post).toHaveBeenCalledWith('/admin/brands',{name:'Brand baru',is_active:true});
  await click(host.querySelector('[aria-label="Hapus Leinz"]'));
  expect(api.delete).toHaveBeenCalledWith('/admin/brands/brand');
});

test('flat master tabs create and edit only their own group without parent inputs', async () => {
  await mount(<AdminCategories />);
  expect(host.querySelector('table').textContent).toContain('Frame');
  await click([...host.querySelectorAll('[role="tab"]')].find(node=>node.textContent==='Material'));
  expect(host.querySelector('table').textContent).toContain('Titanium');
  expect(host.querySelector('table').textContent).not.toContain('Pria');
  await click([...host.querySelectorAll('button')].find(node=>node.textContent.includes('Tambah Material')));
  expect(host.querySelector('[role="dialog"] select')).toBeNull();
  await type(host.querySelector('[role="dialog"] input'),'Stainless');
  await submit(host.querySelector('form'));
  expect(api.post).toHaveBeenCalledWith('/admin/categories',expect.objectContaining({name:'Stainless',group_type:'material'}));
  expect(api.post.mock.calls[0][1]).not.toHaveProperty('parent_id');
  await click(host.querySelector('[aria-label="Edit Titanium"]'));
  await type(host.querySelector('[role="dialog"] input'),'Titanium premium');
  await submit(host.querySelector('form'));
  expect(api.put).toHaveBeenCalledWith('/admin/categories/titanium',expect.objectContaining({name:'Titanium premium',group_type:'material',code:'titanium'}));
});

test('product kinds come from the backend and Accessories can be saved', async () => {
  const options = [{code:'frame',name:'Frame'},{code:'accessories',name:'Aksesoris'}];
  let rows = [...categories];
  api.get.mockImplementation(url => Promise.resolve({data: url === '/admin/categories' ? {categories:rows,product_types:options} : {brands:[]}}));
  api.post.mockImplementation((url, body) => { rows.push({...body,id:'accessories'}); return Promise.resolve({data:{}}); });
  await mount(<AdminCategories />);
  await click([...host.querySelectorAll('button')].find(node => node.textContent.includes('Tambah Jenis Produk')));
  const select = host.querySelector('select');
  expect([...select.options].map(item => item.value)).toEqual(['','frame','accessories']);
  await type(host.querySelector('[role="dialog"] input'),'Aksesoris');
  await act(async () => { select.value='accessories'; select.dispatchEvent(new Event('change',{bubbles:true})); });
  await submit(host.querySelector('form'));
  expect(api.post).toHaveBeenCalledWith('/admin/categories',expect.objectContaining({name:'Aksesoris',code:'accessories',group_type:'product_type',is_active:true}));
  expect(host.querySelector('tbody').textContent).toContain('Aksesoris');
});

test('missing backend product kinds cannot submit an unsupported new category', async () => {
  await mount(<AdminCategories />);
  await click([...host.querySelectorAll('button')].find(node => node.textContent.includes('Tambah Jenis Produk')));
  expect(host.querySelector('select').disabled).toBe(true);
  expect(host.querySelector('[role="alert"]').textContent).toContain('backend diperbarui');
  expect([...host.querySelectorAll('button')].find(node => node.textContent === 'Simpan').disabled).toBe(true);
  await submit(host.querySelector('form'));
  expect(api.post).not.toHaveBeenCalled();
});

test('Accessories is available as a product kind and an independent catalog filter', async () => {
  const accessory = {id:'accessories',name:'Aksesoris',group_type:'product_type',code:'accessories',is_active:true};
  const rows = [...categories, accessory];
  const change = jest.fn();
  await mount(<ProductMasterFields categories={rows} form={product} onChange={change} />);
  await click([...host.querySelectorAll('label')].find(node => node.textContent === 'Aksesoris').querySelector('input'));
  expect(change).toHaveBeenCalledWith(expect.objectContaining({product_type:'accessories',category_ids:['male','round','accessories']}));
  await mount(<MasterCatalogFilters categories={rows} params={{product_type:'accessories'}} onChange={change} />);
  expect(host.querySelector('[data-testid="filter-master-accessories"]').checked).toBe(true);
});

test('admin add and edit product submit the independent master selections', async () => {
  await mount(<AdminProducts />);
  await click(host.querySelector('[data-testid="new-product-btn"]'));
  await type(host.querySelector('[data-testid="pf-desc"]'),'<h2>Deskripsi</h2><p>Frame baru</p>');
  await click(host.querySelector('[data-testid="product-master-material"] input'));
  await submit(host.querySelector('form'));
  expect(api.post).toHaveBeenCalledWith('/admin/products',expect.objectContaining({product_type:'frame',category_ids:['titanium','frame'],primary_category_id:null}));
  await click(host.querySelector('[data-testid="edit-p"]'));
  await click(host.querySelector('[data-testid="product-master-material"] input'));
  await submit(host.querySelector('form'));
  expect(api.put).toHaveBeenCalledWith('/admin/products/p',expect.objectContaining({category_ids:['male','round','titanium','frame'],sku:'EXAMPLE',segments:['Pria']}));
});

test('catalog filters retain all selections when migrating a legacy URL filter', async () => {
  const change=jest.fn();
  await mount(<MasterCatalogFilters categories={categories} params={{product_type:'frame',segment:'Pria',category_ids:'round'}} onChange={change} />);
  expect(host.querySelectorAll('input:checked')).toHaveLength(3);
  await click(host.querySelector('[data-testid="filter-master-titanium"]'));
  expect(change).toHaveBeenCalledWith(['round','frame','male','titanium']);
});

test('catalog sends combined master filters and resets pagination after changing them', async () => {
  await mount(<MemoryRouter initialEntries={['/products?product_type=frame&segment=Pria']}><ProductsPage /></MemoryRouter>);
  await click(host.querySelector('[data-testid="filter-master-titanium"]'));
  const calls=api.get.mock.calls.filter(([url])=>url==='/products');
  const params=calls[calls.length-1][1].params;
  expect(params.category_ids).toBe('frame,male,titanium');
  expect(params.page).toBe(1); expect(params).not.toHaveProperty('segment'); expect(params).not.toHaveProperty('product_type');
});
