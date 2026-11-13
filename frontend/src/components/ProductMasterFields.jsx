import React from 'react';
import { groupedMasters, productMasterIds } from '../lib/masterCategories';

export default function ProductMasterFields({ categories, brands = [], form, onChange }) {
  const selected = productMasterIds(form, categories);
  const choose = item => {
    if (item.group_type === 'product_type') {
      const next = { ...form, product_type: item.code };
      onChange({ ...next, category_ids: productMasterIds(next, categories), primary_category_id: null });
    } else {
      const ids = selected.includes(item.id) ? selected.filter(id => id !== item.id) : [...selected, item.id];
      onChange({ ...form, category_ids: ids, primary_category_id: null });
    }
  };
  return <section className="border rounded-2xl p-4 space-y-4" data-testid="product-master-fields">
    <div><h3 className="font-bold">Klasifikasi Produk</h3><p className="text-xs text-meow-gray mt-1">Pilih satu Jenis Produk dan satu Brand (opsional). Grup lain dapat dipilih lebih dari satu sesuai produk.</p></div>
    <div className="grid sm:grid-cols-2 gap-4">{groupedMasters(categories).map(group => <fieldset key={group.key} className="min-w-0" data-testid={`product-master-${group.key}`}>
      <legend className="text-xs font-bold mb-2">{group.label}{group.key === 'product_type' ? ' (wajib)' : ''}</legend>
      <div className="flex flex-wrap gap-2">{group.items.filter(item => item.is_active || selected.includes(item.id)).map(item => <label key={item.id} className={`inline-flex items-center gap-2 px-3 py-2 rounded-xl border text-sm cursor-pointer ${selected.includes(item.id) ? 'bg-meow-salmon/10 border-meow-salmon' : 'bg-meow-bg border-transparent'}`}>
        <input type={group.key === 'product_type' ? 'radio' : 'checkbox'} name={group.key === 'product_type' ? 'master-product-type' : undefined} checked={selected.includes(item.id)} disabled={!item.is_active && !selected.includes(item.id)} onChange={() => choose(item)} />
        {item.name}{!item.is_active && <span className="text-xs text-meow-gray">(nonaktif)</span>}
      </label>)}</div>
      {!group.items.length && <p className="text-xs text-meow-gray">Master data belum tersedia.</p>}
    </fieldset>)}
      <fieldset className="min-w-0" data-testid="product-master-brand">
        <legend className="text-xs font-bold mb-2">Brand (opsional)</legend>
        <div className="flex flex-wrap gap-2">
          {[{ id: null, name: 'Tanpa brand', is_active: true }, ...brands.filter(item => item.is_active || item.id === form.brand_id)].map(item => <label key={item.id || 'no-brand'} className={`inline-flex items-center gap-2 px-3 py-2 rounded-xl border text-sm cursor-pointer ${(form.brand_id || null) === item.id ? 'bg-meow-salmon/10 border-meow-salmon' : 'bg-meow-bg border-transparent'}`}>
            <input type="radio" name="master-brand" checked={(form.brand_id || null) === item.id} onChange={() => onChange({ ...form, brand_id: item.id })} />
            {item.name}{!item.is_active && <span className="text-xs text-meow-gray">(nonaktif)</span>}
          </label>)}
        </div>
      </fieldset>
    </div>
  </section>;
}
