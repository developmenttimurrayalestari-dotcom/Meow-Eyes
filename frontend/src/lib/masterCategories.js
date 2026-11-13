export const MASTER_GROUPS = [
  { key: 'product_type', label: 'Jenis Produk' },
  { key: 'lens_type', label: 'Jenis Lensa' },
  { key: 'gender', label: 'Gender' },
  { key: 'frame_shape', label: 'Frame Shape' },
  { key: 'material', label: 'Material' },
];
// Brand has an existing master table and product FK; present it alongside
// category groups without mixing brand IDs into product_categories.
export const ADMIN_MASTER_GROUPS = [...MASTER_GROUPS, { key: 'brand', label: 'Brand' }];
export function groupedMasters(categories) {
  return MASTER_GROUPS.map(group => ({ ...group, items: categories.filter(item => item.group_type === group.key) }));
}
export function productMasterIds(form, categories) {
  const kind = categories.find(item => item.group_type === 'product_type' && item.code === form.product_type);
  const selected = (form.category_ids || []).filter(id => categories.some(item => item.id === id && item.group_type !== 'product_type' && MASTER_GROUPS.some(group => group.key === item.group_type)));
  return [...new Set([...selected, ...(kind ? [kind.id] : [])])];
}
