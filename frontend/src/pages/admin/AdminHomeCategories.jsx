import React, { useCallback, useEffect, useState } from 'react';
import { Plus, RefreshCw } from 'lucide-react';
import { api, apiError } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import FormField from '../../components/FormField';
import ImagePicker from '../../components/ImagePicker';
import HomeCategoryCard from '../../components/HomeCategoryCard';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '../../components/ui/dialog';
import { toast } from 'sonner';

const empty = { title: '', description: '', link_url: '/shop-now', background_image: '', icon: 'frame', theme: 'coral', sort_order: 0, is_active: true };
const control = 'w-full rounded-xl border border-meow-midnight/10 bg-meow-bg px-3 py-2.5 outline-none focus:border-meow-salmon';

export default function AdminHomeCategories() {
  const { user } = useAuth();
  const canEdit = user?.role !== 'staff' || user?.permissions?.includes('setting.update');
  const [items, setItems] = useState([]), [version, setVersion] = useState(0);
  const [loading, setLoading] = useState(true), [loaded, setLoaded] = useState(false), [error, setError] = useState('');
  const [editing, setEditing] = useState(null), [saving, setSaving] = useState(false), [formError, setFormError] = useState('');
  const apply = useCallback(({ items: next, version: nextVersion }) => { setItems(next); setVersion(nextVersion); }, []);
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { const { data } = await api.get('/admin/home-categories'); apply(data); setLoaded(true); }
    catch (err) { setError(apiError(err, 'Kategori pilihan belum dapat dimuat.')); }
    finally { setLoading(false); }
  }, [apply]);
  useEffect(() => { load(); }, [load]);
  const edit = item => { setEditing({ ...item, version }); setFormError(''); };
  const set = (key, value) => setEditing(current => ({ ...current, [key]: value }));
  const save = async event => {
    event.preventDefault(); if (saving) return;
    setSaving(true); setFormError('');
    try {
      const { id, ...payload } = editing;
      const { data } = id ? await api.put('/admin/home-categories/' + encodeURIComponent(id), payload) : await api.post('/admin/home-categories', payload);
      apply(data); setEditing(null); toast.success('Card kategori pilihan tersimpan');
    } catch (err) { setFormError(apiError(err, 'Card belum berhasil disimpan.')); }
    finally { setSaving(false); }
  };
  const remove = async item => {
    if (!window.confirm(`Hapus card "${item.title}" dari Kategori Pilihan Beranda?`)) return;
    setSaving(true); setError('');
    try { const { data } = await api.delete('/admin/home-categories/' + encodeURIComponent(item.id), { params: { version } }); apply(data); toast.success('Card dihapus'); }
    catch (err) { setError(apiError(err, 'Card belum berhasil dihapus.')); }
    finally { setSaving(false); }
  };
  return <div data-testid="admin-home-categories" className="space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><h1 className="font-heading text-3xl font-black">Kategori Pilihan Beranda</h1><p className="text-sm text-meow-gray mt-2">Atur card di beranda beserta gambar latar dan halaman tujuan. Angka urutan terkecil tampil lebih dahulu. Maksimal 50 card.</p></div>
      <div className="flex flex-wrap gap-2"><button type="button" disabled={loading || saving} onClick={load} className="btn-secondary text-sm"><RefreshCw className="inline h-4 w-4 mr-1" />Muat ulang</button>
        {canEdit && <button type="button" disabled={!loaded || loading || saving || items.length >= 50} onClick={() => edit({ ...empty, sort_order: Math.min(9999, Math.max(-1, ...items.map(item => item.sort_order)) + 1) })} className="btn-primary text-sm" data-testid="add-home-category"><Plus className="inline h-4 w-4 mr-1" />Tambah Card</button>}</div>
    </div>
    {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {loading && <p role="status">Memuat kategori pilihan…</p>}
    {loaded && !loading && <><p className="text-sm text-meow-gray">{items.filter(item => item.is_active).length} aktif dari {items.length} card. Bagian beranda disembunyikan bila tidak ada card aktif.</p>
      {!items.length && <p className="rounded-2xl bg-white p-6 text-sm">Belum ada card. Klik Tambah Card untuk menampilkan kategori pilihan di beranda.</p>}
      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">{items.map(item => <div key={item.id} className="rounded-3xl border bg-white p-3 space-y-3" data-testid={`admin-home-category-${item.id}`}>
        <HomeCategoryCard item={item} preview />
        <p className="text-xs text-meow-gray">Urutan {item.sort_order} · {item.is_active ? 'Aktif' : 'Nonaktif'}</p><p className="text-xs break-all">Tujuan: {item.link_url}</p>
        {canEdit && <div className="flex gap-4"><button type="button" disabled={saving} onClick={() => edit(item)} className="text-sm font-bold text-meow-salmon" aria-label={`Edit card ${item.title}`}>Edit</button><button type="button" disabled={saving} onClick={() => remove(item)} className="text-sm font-bold text-red-600" aria-label={`Hapus card ${item.title}`}>Hapus</button></div>}
      </div>)}</div></>}
    <Dialog open={!!editing} onOpenChange={open => { if (!open && !saving) setEditing(null); }}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-2xl">
        <DialogTitle>{editing?.id ? 'Edit Card Kategori Pilihan' : 'Tambah Card Kategori Pilihan'}</DialogTitle>
        <DialogDescription>Atur judul, gambar latar, dan tautan tujuan card yang ditampilkan di beranda.</DialogDescription>
        {editing && <form onSubmit={save} className="space-y-4" data-testid="home-category-form">
          <fieldset disabled={saving} className="space-y-4">
            <FormField label="Judul card"><input required maxLength={100} value={editing.title} onChange={event => set('title', event.target.value)} className={control} /></FormField>
            <FormField label="Keterangan singkat (opsional)" hint="Teks singkat di bawah judul, maksimal 180 karakter."><textarea rows={2} maxLength={180} value={editing.description} onChange={event => set('description', event.target.value)} className={control} /></FormField>
            <FormField label="Tautan tujuan" hint="Contoh: /shop-now?product_type=frame, /category/nama-kategori, atau URL https://…"><input required maxLength={2048} value={editing.link_url} onChange={event => set('link_url', event.target.value)} className={control} /></FormField>
            <ImagePicker label="Gambar latar card (opsional)" value={editing.background_image} onChange={url => set('background_image', url)} testId="home-category-image" />
            <p className="text-xs text-meow-gray">Unggah atau pilih gambar dari galeri. Gambar akan mengisi card dan dapat terpotong mengikuti layar. Lapisan gelap menjaga tulisan tetap terbaca. Tanpa gambar, card memakai warna tema.</p>
            <div className="grid sm:grid-cols-2 gap-3"><FormField label="Ikon"><select value={editing.icon} onChange={event => set('icon', event.target.value)} className={control}>{[['frame','Kacamata'],['lens','Lensa'],['package','Paket'],['sparkles','Bintang'],['tag','Label promo']].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></FormField>
              <FormField label="Warna tema (tanpa gambar)"><select value={editing.theme} onChange={event => set('theme', event.target.value)} className={control}>{[['coral','Coral'],['amber','Amber'],['mint','Mint'],['midnight','Midnight']].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></FormField></div>
            <FormField label="Urutan tampilan" hint="Angka 0–9999; angka lebih kecil tampil lebih dahulu."><input required type="number" min={0} max={9999} step={1} value={editing.sort_order} onChange={event => set('sort_order', event.target.value === '' ? '' : Number(event.target.value))} className={control} /></FormField>
            <label className="flex gap-2 items-center text-sm"><input type="checkbox" checked={editing.is_active} onChange={event => set('is_active', event.target.checked)} />Tampilkan card di beranda</label>
            <div><p className="text-xs font-bold mb-2">Pratinjau card</p><HomeCategoryCard item={{ ...editing, title: editing.title || 'Judul card' }} preview /></div>
          </fieldset>
          {formError && <p role="alert" className="text-sm text-red-600">{formError}</p>}
          <div className="flex gap-2"><button type="button" disabled={saving} onClick={() => setEditing(null)} className="btn-secondary flex-1">Batal</button><button type="submit" disabled={saving} className="btn-primary flex-1">{saving ? 'Menyimpan…' : 'Simpan'}</button></div>
        </form>}
      </DialogContent>
    </Dialog>
  </div>;
}
