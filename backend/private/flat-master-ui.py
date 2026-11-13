from pathlib import Path

categories=r'''import React, { useCallback, useEffect, useState } from 'react';
import { api, apiError } from '../../lib/api';
import { Plus, Edit2, Trash2, Tags, X } from 'lucide-react';
import { toast } from 'sonner';
import { MASTER_GROUPS } from '../../lib/masterCategories';

export default function AdminCategories() {
  const [rows, setRows] = useState([]), [group, setGroup] = useState('product_type');
  const [editing, setEditing] = useState(null), [q, setQ] = useState(''), [page, setPage] = useState(1);
  const [error, setError] = useState(''), [loading, setLoading] = useState(true), [saving, setSaving] = useState(false);
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { const { data } = await api.get('/admin/categories'); setRows(data.categories || []); }
    catch (e) { setError(apiError(e)); } finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const label = MASTER_GROUPS.find(item => item.key === group)?.label;
  const filtered = rows.filter(item => item.group_type === group && item.name.toLowerCase().includes(q.toLowerCase()));
  const pageSize = 15, pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const shown = filtered.slice((Math.min(page, pageCount) - 1) * pageSize, Math.min(page, pageCount) * pageSize);
  const open = item => { setError(''); setEditing(item ? { ...item } : { name: '', group_type: group, code: '', slug: '', is_active: true, is_featured: false, sort_order: 0 }); };
  const save = async e => {
    e.preventDefault(); setSaving(true); setError('');
    const body = Object.fromEntries(['name', 'group_type', 'code', 'slug', 'description', 'icon', 'banner_image', 'sort_order', 'is_featured', 'is_active'].filter(key => editing[key] !== undefined).map(key => [key, editing[key]]));
    if (!body.code) delete body.code; if (!body.slug) delete body.slug;
    try { await api[editing.id ? 'put' : 'post'](`/admin/categories${editing.id ? '/' + editing.id : ''}`, body); setEditing(null); toast.success('Master data disimpan'); await load(); }
    catch (e) { setError(apiError(e)); } finally { setSaving(false); }
  };
  const remove = async item => {
    if (!window.confirm(`Hapus ${item.name}?`)) return;
    try { await api.delete(`/admin/categories/${item.id}`); toast.success('Master data dihapus'); await load(); }
    catch (e) { setError(apiError(e)); }
  };
  return <div data-testid="admin-categories" className="space-y-5">
    <div className="flex flex-wrap justify-between items-center gap-3"><div><h1 className="text-3xl font-black flex gap-2 items-center"><Tags className="text-meow-salmon" />Master Kategori</h1><p className="text-sm text-meow-gray mt-2">Setiap grup berdiri sendiri dan dapat dihubungkan ke produk.</p></div><button onClick={() => open()} className="btn-primary text-sm"><Plus size={16} className="inline mr-1" />Tambah {label}</button></div>
    <div role="tablist" aria-label="Grup master kategori" className="flex flex-wrap gap-2">{MASTER_GROUPS.map(item => <button type="button" role="tab" id={`master-tab-${item.key}`} aria-selected={group === item.key} aria-controls="master-panel" key={item.key} onClick={() => { setGroup(item.key); setPage(1); setQ(''); setError(''); }} className={`px-4 py-2 rounded-xl text-sm font-bold ${group === item.key ? 'bg-meow-midnight text-white' : 'bg-white border'}`}>{item.label}</button>)}</div>
    {error && !editing && <p role="alert" className="bg-red-50 text-red-700 p-4 rounded-xl">{error}</p>}
    <section id="master-panel" role="tabpanel" aria-labelledby={`master-tab-${group}`} className="bg-white border rounded-3xl overflow-hidden">
      <div className="p-4 flex flex-wrap justify-between items-center gap-3"><h2 className="font-bold">{label} <span className="font-normal text-sm text-meow-gray">({filtered.length})</span></h2><input aria-label={`Cari ${label}`} placeholder={`Cari ${label}…`} value={q} onChange={e => { setQ(e.target.value); setPage(1); }} className="bg-meow-bg border rounded-xl px-3 py-2 text-sm" /></div>
      {loading ? <p role="status" className="p-6">Memuat master data…</p> : <div className="overflow-x-auto"><table className="w-full text-sm" data-testid="master-category-table"><thead className="bg-meow-bg"><tr><th className="text-left p-4">Nama</th><th className="text-left p-4">Status</th><th className="text-right p-4">Aksi</th></tr></thead><tbody>{shown.map(item => <tr key={item.id} className="border-t"><td className="p-4 font-semibold">{item.name}</td><td className="p-4">{item.is_active ? 'Aktif' : 'Nonaktif'}</td><td className="p-4"><div className="flex justify-end gap-3"><button aria-label={`Edit ${item.name}`} onClick={() => open(item)} className="flex items-center gap-1 text-meow-salmon"><Edit2 size={14} />Edit</button><button aria-label={`Hapus ${item.name}`} onClick={() => remove(item)} className="flex items-center gap-1 text-red-600"><Trash2 size={14} />Hapus</button></div></td></tr>)}</tbody></table>{!shown.length && <p className="text-center p-8 text-meow-gray">Tidak ada data pada grup ini.</p>}</div>}
      <div className="p-4 border-t flex justify-between text-sm"><button disabled={page <= 1} onClick={() => setPage(page - 1)}>Sebelumnya</button><span>{Math.min(page, pageCount)} / {pageCount}</span><button disabled={page >= pageCount} onClick={() => setPage(page + 1)}>Berikutnya</button></div>
    </section>
    {editing && <div className="fixed inset-0 z-50 bg-black/60 p-4 grid place-items-center" onClick={() => !saving && setEditing(null)}><form role="dialog" aria-modal="true" aria-labelledby="master-form-title" onSubmit={save} onClick={e => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-md w-full space-y-4">
      <div className="flex justify-between items-center"><h2 id="master-form-title" className="text-xl font-bold">{editing.id ? 'Edit' : 'Tambah'} {label}</h2><button type="button" aria-label="Tutup form" disabled={saving} onClick={() => setEditing(null)}><X size={20} /></button></div>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <label className="block text-sm">Nama<input required maxLength={group === 'gender' ? 64 : 255} value={editing.name} onChange={e => setEditing({ ...editing, name: e.target.value })} className="w-full bg-meow-bg rounded-xl border px-3 py-2 mt-1" /></label>
      {!editing.id && group === 'product_type' && <label className="block text-sm">Jenis produk sistem<select required value={editing.code} onChange={e => setEditing({ ...editing, code: e.target.value })} className="w-full bg-meow-bg rounded-xl border px-3 py-2 mt-1"><option value="">Pilih jenis</option><option value="frame">Frame</option><option value="lens">Lensa</option><option value="package">Paket</option></select></label>}
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={editing.is_active} onChange={e => setEditing({ ...editing, is_active: e.target.checked })} />Aktif</label>
      <div className="flex gap-3"><button type="button" className="btn-secondary flex-1" disabled={saving} onClick={() => setEditing(null)}>Batal</button><button className="btn-primary flex-1" disabled={saving}>{saving ? 'Menyimpan…' : 'Simpan'}</button></div>
    </form></div>}
  </div>;
}
'''
Path('../frontend/src/pages/admin/AdminCategories.jsx').write_text(categories,encoding='utf-8')

p=Path('../frontend/src/pages/admin/AdminProducts.jsx');t=p.read_text(encoding='utf-8')
t=t.replace('import ImagePicker from','import ProductMasterFields from "../../components/ProductMasterFields";\nimport { productMasterIds } from "../../lib/masterCategories";\nimport ImagePicker from',1)
t=t.replace('    name: product.name, description: product.description,','    name: product.name, sku: product.sku, description: product.description,').replace('    name: "", description: "", product_type: "frame",','    name: "", sku: "", description: "", product_type: "frame",')
t=t.replace('      if (isEdit) {\n        await api.put(`/admin/products/${product.id}`, form);','''      const categoryIds = productMasterIds(form, categories);
      const payload = { ...form, category_ids: categoryIds, primary_category_id: null,
        segments: categories.filter(item => item.group_type === 'gender' && categoryIds.includes(item.id)).map(item => item.name) };
      if (!payload.sku) delete payload.sku;
      if (isEdit) {
        await api.put(`/admin/products/${product.id}`, payload);''').replace('await api.post("/admin/products", form);','await api.post("/admin/products", payload);')
a=t.index('          <select value={form.product_type}');b=t.index('          </select>',a)+len('          </select>')
t=t[:a]+'''          <input aria-label="SKU produk" placeholder="SKU produk (otomatis jika kosong)" value={form.sku || ''} onChange={e => setForm({ ...form, sku: e.target.value })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" />'''+t[b:]
a=t.index('          <select value={form.primary_category_id');b=t.index('          </select>',a)+len('          </select>');t=t[:a]+t[b:]
anchor='        <ImagePicker\n';t=t.replace(anchor,'        <ProductMasterFields categories={categories} form={form} onChange={setForm} />\n'+anchor,1)
a=t.index('        <div>\n          <p className="text-xs font-bold uppercase tracking-wider mb-2">Segmentasi');b=t.index('        <div>',a+20);t=t[:a]+t[b:]
p.write_text(t,encoding='utf-8')
