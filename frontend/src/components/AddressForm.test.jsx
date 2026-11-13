import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import AddressForm from './AddressForm';
import { api } from '../lib/api';

jest.mock('../lib/api', () => ({ api: { get: jest.fn(), post: jest.fn(), patch: jest.fn() }, apiError: (error, fallback) => error?.response?.data?.detail || fallback }));
jest.mock('sonner', () => ({ toast: { success: jest.fn() } }));
let host, root;
const options = (url, config) => {
  if (url.endsWith('/provinces')) return [{ id: 'p+/=', name: 'Jawa Barat' }, { id: 'p2', name: 'Bali' }];
  if (url.endsWith('/cities')) return config.params.province_id === 'p2' ? [{ id: 'c2', name: 'Denpasar' }] : [{ id: 'c1', name: 'Kota Bandung' }];
  if (url.endsWith('/districts')) return [{ id: 'd1', name: 'Bandung Wetan' }];
  return [{ id: 'v1', name: 'Citarum', postal_code: '40115' }];
};
const render = async node => act(async () => root.render(node));
const select = async (name, value) => act(async () => { const node = host.querySelector(`[data-testid="addr-${name}"]`); node.value = value; node.dispatchEvent(new Event('change', { bubbles: true })); });
const enter = async (name, value) => act(async () => { const node = host.querySelector(`[data-testid="addr-${name}"]`); Object.getOwnPropertyDescriptor(node.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype, 'value').set.call(node, value); node.dispatchEvent(new Event('input', { bubbles: true })); });
const fillRegions = async () => { await select('province', 'p+/='); await select('city', 'c1'); await select('district', 'd1'); await select('subdistrict', 'v1'); };
beforeEach(() => {
  jest.clearAllMocks(); host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
  api.get.mockImplementation(async (url, config) => ({ data: { locations: options(url, config) } }));
  api.post.mockResolvedValue({ data: { address: { id: 'saved' } } }); api.patch.mockResolvedValue({ data: { address: { id: 'existing' } } });
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

test('official cascade fills a readonly postcode and submits canonical names and hierarchy IDs', async () => {
  const saved = jest.fn(); await render(<AddressForm onSaved={saved}/>);
  expect(host.querySelector('[data-testid="addr-province"]').tagName).toBe('SELECT');
  expect(host.querySelector('[data-testid="addr-city"]').disabled).toBe(true);
  expect(host.querySelector('[data-testid="addr-save"]').disabled).toBe(true);
  await fillRegions();
  expect(host.querySelector('[data-testid="addr-postal_code"]').value).toBe('40115');
  expect(host.querySelector('[data-testid="addr-postal_code"]').readOnly).toBe(true);
  await enter('recipient', '  Customer QA  '); await enter('phone', '081234567890'); await enter('street', 'Jl. QA 1');
  await act(async () => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  expect(api.post).toHaveBeenCalledWith('/addresses', expect.objectContaining({ recipient: 'Customer QA', province: 'Jawa Barat', city: 'Kota Bandung', district: 'Bandung Wetan', subdistrict: 'Citarum', postal_code: '40115',
    everpro_location: { province_id: 'p+/=', city_id: 'c1', district_id: 'd1', subdistrict_id: 'v1' } }));
  expect(saved).toHaveBeenCalledWith({ id: 'saved' });
});

test('changing parent clears all child selections and postcode', async () => {
  await render(<AddressForm/>); await fillRegions(); await select('province', 'p2');
  for (const name of ['city', 'district', 'subdistrict', 'postal_code']) expect(host.querySelector(`[data-testid="addr-${name}"]`).value).toBe('');
  expect(host.querySelector('[data-testid="addr-save"]').disabled).toBe(true);
});

test('late city response from the previous province cannot overwrite current options', async () => {
  let late;
  api.get.mockImplementation((url, config) => url.endsWith('/cities') && config.params.province_id === 'p+/=' ? new Promise(resolve => { late = resolve; }) : Promise.resolve({ data: { locations: options(url, config) } }));
  await render(<AddressForm/>); await select('province', 'p+/='); await select('province', 'p2');
  await act(async () => late({ data: { locations: [{ id: 'stale', name: 'Wrong city' }] } }));
  expect(host.querySelector('[data-testid="addr-city"]').textContent).toContain('Denpasar');
  expect(host.querySelector('[data-testid="addr-city"]').textContent).not.toContain('Wrong city');
});

test('existing address resolves official hierarchy and edits instead of creating a duplicate', async () => {
  await render(<AddressForm initialAddress={{ id: 'existing', label: 'Rumah', recipient: 'Customer QA', phone: '081234567890', street: 'Jl. QA 1', province: 'jawa barat', city: 'Kota Bandung', district: 'Bandung Wetan', subdistrict: 'Citarum', postal_code: '40115', is_default: true }} onSaved={jest.fn()}/>);
  expect(host.querySelector('[data-testid="addr-subdistrict"]').value).toBe('v1');
  await enter('street', 'Jl. QA 2');
  await act(async () => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  expect(api.patch).toHaveBeenCalledWith('/addresses/existing', expect.objectContaining({ street: 'Jl. QA 2', province: 'Jawa Barat' }));
  expect(api.post).not.toHaveBeenCalled();
});

test('provider failure blocks save and offers retry without reverting to free text', async () => {
  api.get.mockRejectedValueOnce(new Error('provider unavailable'));
  await render(<AddressForm/>);
  expect(host.querySelector('[role="alert"]').textContent).toContain('Data wilayah belum dapat dimuat');
  expect(host.querySelector('[data-testid="addr-save"]').disabled).toBe(true);
  await act(async () => [...host.querySelectorAll('button')].find(button => button.textContent === 'Coba lagi').click());
  expect(host.querySelector('[data-testid="addr-province"]').disabled).toBe(false);
});
