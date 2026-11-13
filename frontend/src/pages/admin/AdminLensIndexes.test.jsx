import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { AdminLensIndexes } from './AdminContent';
import { api } from '../../lib/api';

jest.mock('../../lib/api', () => ({ api: { get: jest.fn(), post: jest.fn(), put: jest.fn(), delete: jest.fn() } }));
jest.mock('../../components/RichTextEditor', () => () => null);
jest.mock('../../components/ImagePicker', () => ({ __esModule: true, default: () => null, resolveImageUrl: value => value }));
jest.mock('sonner', () => ({ toast: { success: jest.fn() } }));

let host, root;
const categories = [{ id: 'sv', name: 'Single Vision', group_type: 'lens_type', is_active: true },
  { id: 'photo', name: 'Photochromic', group_type: 'lens_type', is_active: true },
  { id: 'gender', name: 'Pria', group_type: 'gender', is_active: true }];
beforeEach(() => {
  jest.clearAllMocks();
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/categories' ? { categories } : {
    items: [{ id: 'index', name: '1.56 Standard', index_value: '1.56', additional_price: 50000, is_active: true, lens_type_ids: ['sv'], lens_types: [categories[0]] }],
  } }));
  api.put.mockResolvedValue({ data: { ok: true } });
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

test('admin edits an existing Lens Index and saves multiple independent lens type assignments', async () => {
  await act(async () => root.render(<AdminLensIndexes />));
  await act(async () => host.querySelector('[aria-label="Edit Lens Index 1.56 Standard"]').click());
  const form = host.querySelector('form');
  const labels = [...form.querySelectorAll('label')];
  expect(form.textContent).not.toContain('Pria');
  expect(labels.find(label => label.textContent === 'Single Vision').querySelector('input').checked).toBe(true);
  await act(async () => labels.find(label => label.textContent === 'Photochromic').querySelector('input').click());
  await act(async () => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  expect(api.put).toHaveBeenCalledWith('/admin/lens/indexes/index', expect.objectContaining({ lens_type_ids: ['sv', 'photo'], additional_price: 50000 }));
  expect(host.querySelector('form')).toBeNull();
});
