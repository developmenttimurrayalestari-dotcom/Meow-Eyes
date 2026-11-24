import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import FormField from './FormField';

let host, root;
beforeEach(() => { host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

test('repeated product fields keep distinct visible labels even after values are filled', async () => {
  await act(async () => root.render(<>{['Merah', 'Biru'].map(color => <FormField key={color} label="Warna varian"><input defaultValue={color} /></FormField>)}</>));
  const inputs = [...host.querySelectorAll('input')];
  expect(new Set(inputs.map(input => input.id)).size).toBe(2);
  inputs.forEach(input => {
    expect(input.labels).toHaveLength(1);
    expect(input.labels[0].textContent).toBe('Warna varian');
    expect(input.labels[0].control).toBe(input);
  });
});

test('instructions stay visible and associated without losing existing descriptions or native validation', async () => {
  await act(async () => root.render(<form><p id="existing-help">Harga dalam rupiah.</p><FormField label="Harga produk (Rp)" hint="Isi tanpa pemisah ribuan."><input id="product-price" type="number" required aria-describedby="existing-help" defaultValue="" /></FormField></form>));
  const input = host.querySelector('input');
  expect(input.labels[0].control).toBe(input);
  expect(input.id).toBe('product-price');
  const descriptions = input.getAttribute('aria-describedby').split(' ').map(id => document.getElementById(id)?.textContent);
  expect(descriptions).toEqual(['Harga dalam rupiah.', 'Isi tanpa pemisah ribuan.']);
  expect(host.querySelector('form').checkValidity()).toBe(false);
});
