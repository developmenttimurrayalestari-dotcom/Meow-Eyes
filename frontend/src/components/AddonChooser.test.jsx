import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import AddonChooser from './AddonChooser';
import { api } from '../lib/api';
jest.mock('../lib/api', () => ({ api: { get: jest.fn() }, apiError: () => 'Gagal memuat', imageSrc: v => v, formatIDR: v => `Rp ${v}` }));
let host, root;
const click = async n => act(async () => n.dispatchEvent(new MouseEvent('click', { bubbles: true })));
beforeEach(() => { jest.useFakeTimers(); jest.clearAllMocks(); host=document.createElement('div'); document.body.appendChild(host); root=createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); jest.useRealTimers(); });
const product = (id, stock=5) => ({ id, name: id, price: 100, main_image:'asset.png', variants:[{ id:id+'-sku', sku:id, stock, reserved:0 }] });
const mount = async props => { await act(async () => root.render(<AddonChooser quantity={2} onClose={jest.fn()} {...props} />)); await act(async () => jest.advanceTimersByTime(210)); };
test('multiple add-ons preserve their SKU identities and follow primary quantity', async () => {
  api.get.mockResolvedValue({ data: { products:[product('Case'),product('Cleaner')], total:2 } });
  const confirm=jest.fn(); await mount({ onConfirm:confirm });
  await click(host.querySelector('[aria-label="Tambahkan Case"]')); await click(host.querySelector('[aria-label="Tambahkan Cleaner"]'));
  expect(host.textContent).toContain('2 Add On · Tambahan Rp 400');
  await click([...host.querySelectorAll('button')].find(n => n.textContent==='Lanjutkan'));
  expect(confirm).toHaveBeenCalledWith([{ product_id:'Case',variant_id:'Case-sku' },{ product_id:'Cleaner',variant_id:'Cleaner-sku' }]);
  expect(api.get).toHaveBeenCalledWith('/products', expect.objectContaining({ params:expect.objectContaining({ sale_role:'add_on' }) }));
});
test('insufficient add-on stock cannot be selected; primary-only purchase remains possible', async () => {
  api.get.mockResolvedValue({ data:{ products:[product('Case',1)],total:1 } }); const confirm=jest.fn(); await mount({ onConfirm:confirm });
  expect(host.querySelector('[aria-label="Tambahkan Case"]').disabled).toBe(true);
  await click(host.querySelector('[data-testid="addon-skip"]')); expect(confirm).toHaveBeenCalledWith([]);
});
test('catalog failure keeps a visible error and does not invent selections', async () => {
  api.get.mockRejectedValue(new Error('offline')); const confirm=jest.fn(); await mount({ onConfirm:confirm });
  expect(host.querySelector('[role="alert"]').textContent).toBe('Gagal memuat');
  await click(host.querySelector('[data-testid="addon-skip"]')); expect(confirm).toHaveBeenCalledWith([]);
});
