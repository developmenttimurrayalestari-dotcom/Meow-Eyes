import React from 'react';
import { groupedMasters } from '../lib/masterCategories';

export default function MasterCatalogFilters({ categories, params, onChange }) {
  const selected = new Set((params.category_ids || '').split(',').filter(Boolean));
  for (const item of categories) {
    if (item.group_type === 'product_type' && item.code === params.product_type) selected.add(item.id);
    if (item.group_type === 'gender' && item.name.toLowerCase() === params.segment?.toLowerCase()) selected.add(item.id);
  }
  const toggle = id => { const ids = new Set(selected); if (ids.has(id)) ids.delete(id); else ids.add(id); onChange([...ids]); };
  return <>{groupedMasters(categories).map(group => <fieldset key={group.key} className="space-y-2" data-testid={`catalog-master-${group.key}`}>
    <legend className="font-bold text-xs uppercase tracking-wider text-meow-salmon mb-2">{group.label}</legend>
    <div className="space-y-2 max-h-48 overflow-y-auto">{group.items.filter(item => item.is_active).map(item => <label key={item.id} className="flex gap-2 items-center cursor-pointer"><input type="checkbox" checked={selected.has(item.id)} onChange={() => toggle(item.id)} data-testid={`filter-master-${item.id}`} />{item.name}</label>)}</div>
  </fieldset>)}</>;
}
