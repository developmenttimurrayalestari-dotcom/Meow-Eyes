import React, { useCallback, useEffect, useState } from "react";
import { Plus, Zap, X, Edit2 } from "lucide-react";
import { toast } from "sonner";
import { api, formatIDR } from "../../lib/api";
import { adminError, inputClass, localDateTime, utcDateTime } from "./adminUtils";

const blankRule = () => ({ category_id: "", include_descendants: true, discount_type: "percent", discount_value: 15, quota_per_product: 10 });
const blankCampaign = () => ({ name: "", start_at: new Date().toISOString(), end_at: new Date(Date.now() + 86400000).toISOString(), is_active: true, items: [], category_rules: [] });

export default function AdminFlashSales() {
  const [campaigns, setCampaigns] = useState([]);
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState(null);
  const [rule, setRule] = useState(blankRule);
  const [item, setItem] = useState({ product_id: "", flash_price: 0, quota: 10 });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [sales, cats] = await Promise.all([api.get("/admin/flash-sales"), api.get("/admin/categories")]);
      setCampaigns(sales.data.flash_sales || []); setCategories(cats.data.categories || []);
    } catch (err) { setError(adminError(err, "Flash Sale belum dapat dimuat.")); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try { const { data } = await api.get("/admin/products", { params: { q: query, limit: 100 }, signal: controller.signal }); setProducts(data.products || []); }
      catch (err) { if (!controller.signal.aborted) setError(adminError(err)); }
    }, 200);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query]);
  const open = (campaign) => { setEditing(campaign ? { ...campaign, items: campaign.items || [], category_rules: campaign.category_rules || [] } : blankCampaign()); setRule(blankRule()); setItem({ product_id: "", flash_price: 0, quota: 10 }); setError(""); };
  const addRule = () => {
    if (!rule.category_id) return toast.error("Pilih kategori terlebih dahulu");
    if (editing.category_rules.some(r => r.category_id === rule.category_id)) return toast.error("Kategori sudah ditambahkan");
    if (!Number.isFinite(rule.discount_value) || rule.discount_value <= 0 || (rule.discount_type === "percent" && rule.discount_value > 100) || !Number.isInteger(rule.quota_per_product) || rule.quota_per_product < 1) return toast.error("Isi diskon dan kuota yang valid");
    setEditing({ ...editing, category_rules: [...editing.category_rules, rule] }); setRule(blankRule());
  };
  const addItem = () => {
    if (!item.product_id) return toast.error("Pilih produk terlebih dahulu");
    if (editing.items.some(i => i.product_id === item.product_id)) return toast.error("Produk sudah ditambahkan");
    if (item.flash_price < 0 || !Number.isFinite(item.flash_price) || !Number.isInteger(item.quota) || item.quota < 1) return toast.error("Isi harga dan kuota yang valid");
    setEditing({ ...editing, items: [...editing.items, { ...item, product_name: products.find(p => p.id === item.product_id)?.name }] }); setItem({ product_id: "", flash_price: 0, quota: 10 });
  };
  const save = async event => {
    event.preventDefault(); setError("");
    if (new Date(editing.end_at) <= new Date(editing.start_at)) return setError("Waktu selesai harus setelah waktu mulai.");
    if (!editing.items.length && !editing.category_rules.length) return setError("Tambahkan setidaknya satu kategori atau produk.");
    setSaving(true);
    try {
      const payload = { name: editing.name, start_at: editing.start_at, end_at: editing.end_at, is_active: editing.is_active, category_rules: editing.category_rules.map(({ category_id, include_descendants, discount_type, discount_value, quota_per_product }) => ({ category_id, include_descendants, discount_type, discount_value, quota_per_product })), items: editing.items.map(({ product_id, variant_id, flash_price, quota, id, is_active }) => editing.id ? ({ id, flash_price, quota, is_active: is_active !== false }) : ({ product_id, ...(variant_id ? { variant_id } : {}), flash_price, quota })) };
      if (editing.id) delete payload.category_rules;
      if (editing.id) await api.patch(`/admin/flash-sales/${editing.id}`, payload);
      else await api.post("/admin/flash-sales", payload);
      setEditing(null); toast.success("Flash Sale tersimpan"); await load();
    } catch (err) { setError(adminError(err)); }
    finally { setSaving(false); }
  };
  return <div className="space-y-5" data-testid="admin-flashsales">
    <header className="flex flex-wrap justify-between gap-4"><div><h1 className="font-heading text-3xl font-black flex items-center gap-2"><Zap /> Flash Sale</h1><p className="text-sm text-meow-gray mt-2">Atur promo per kategori atau produk, jadwal tayang, dan kuota pembelian.</p></div><button onClick={() => open()} className="btn-primary inline-flex items-center gap-2" data-testid="add-flash-btn"><Plus size={16} /> Buat Flash Sale</button></header>
    {error && !editing && <p role="alert" className="bg-red-50 p-4 rounded-xl text-red-700">{error} <button onClick={load} className="underline">Coba lagi</button></p>}
    {loading ? <p role="status">Memuat Flash Sale…</p> : campaigns.length === 0 ? <p className="bg-white rounded-3xl border p-8 text-center text-meow-gray">Belum ada Flash Sale. Buat kampanye pertama dari kategori atau produk pilihan.</p> : <div className="grid md:grid-cols-2 gap-4">{campaigns.map(campaign => {
      const scheduled = new Date(campaign.start_at) > new Date(); const ended = new Date(campaign.end_at) <= new Date();
      return <article key={campaign.id} className="rounded-3xl border border-zinc-200 bg-white p-5 space-y-3" data-testid={`flash-${campaign.id}`}>
        <div className="flex gap-2 justify-between items-start"><h2 className="font-heading font-extrabold text-lg">{campaign.name}</h2><span className={`text-xs rounded-full px-2 py-1 ${campaign.is_active && !ended ? "bg-amber-100 text-amber-900" : "bg-zinc-100"}`}>{!campaign.is_active ? "Nonaktif" : ended ? "Berakhir" : scheduled ? "Terjadwal" : "Aktif"}</span></div>
        <p className="text-xs text-meow-gray">{new Date(campaign.start_at).toLocaleString("id-ID")} – {new Date(campaign.end_at).toLocaleString("id-ID")}</p><p className="text-sm">{campaign.items?.length || 0} produk · {campaign.category_rules?.length || 0} aturan kategori</p>
        <div className="flex flex-wrap gap-4 text-sm font-bold"><button onClick={() => open(campaign)} className="inline-flex gap-1 items-center text-meow-salmon"><Edit2 size={14} /> Edit</button><button onClick={async () => { try { await api.patch(`/admin/flash-sales/${campaign.id}`, { is_active: !campaign.is_active }); await load(); } catch (err) { toast.error(adminError(err)); } }} className="text-meow-gray">{campaign.is_active ? "Nonaktifkan" : "Aktifkan"}</button></div>
      </article>;
    })}</div>}
    {editing && <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={() => !saving && setEditing(null)}><form onSubmit={save} onClick={e => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-3xl w-full space-y-4 max-h-[92vh] overflow-y-auto" data-testid="flash-form" role="dialog" aria-modal="true" aria-labelledby="flash-form-title">
      <div className="flex justify-between"><h2 id="flash-form-title" className="font-heading font-extrabold text-xl">{editing.id ? "Edit" : "Buat"} Flash Sale</h2><button type="button" onClick={() => setEditing(null)} disabled={saving} aria-label="Tutup"><X /></button></div>
      {error && <p role="alert" className="bg-red-50 text-red-700 p-3 rounded-xl text-sm">{error}</p>}
      <label className="block text-sm font-bold">Nama kampanye<input required value={editing.name} onChange={e => setEditing({ ...editing, name: e.target.value })} className={`${inputClass} mt-1`} /></label>
      <div className="grid sm:grid-cols-2 gap-3"><label className="text-sm font-bold">Mulai (waktu lokal)<input required type="datetime-local" value={localDateTime(editing.start_at)} onChange={e => setEditing({ ...editing, start_at: utcDateTime(e.target.value) })} className={`${inputClass} mt-1`} /></label><label className="text-sm font-bold">Selesai (waktu lokal)<input required type="datetime-local" value={localDateTime(editing.end_at)} onChange={e => setEditing({ ...editing, end_at: utcDateTime(e.target.value) })} className={`${inputClass} mt-1`} /></label></div>
      <section className="border border-amber-200 bg-amber-50/50 rounded-2xl p-4 space-y-3"><h3 className="font-bold">Promo berdasarkan kategori</h3><p className="text-xs text-meow-gray">Produk aktif dalam kategori dipilih saat kampanye dibuat. Penyegaran kategori menambahkan produk baru tanpa mengubah harga, kuota, atau penjualan yang sudah tercatat.</p>
        {editing.category_rules.map((r, index) => <div key={r.category_id} className="flex items-center gap-2 bg-white p-3 rounded-xl text-xs"><span className="flex-1"><strong>{categories.find(c => c.id === r.category_id)?.name || r.category_id}</strong> · {r.discount_type === "percent" ? `${r.discount_value}%` : `${r.discount_type === "fixed_price" ? "Harga " : "Potongan "}${formatIDR(r.discount_value)}`} · Kuota {r.quota_per_product}/produk{r.include_descendants ? " · Termasuk subkategori" : ""}</span>{!editing.id && <button type="button" onClick={() => setEditing({ ...editing, category_rules: editing.category_rules.filter((_, i) => i !== index) })} aria-label="Hapus aturan kategori"><X size={16} /></button>}</div>)}
        {!editing.id && <><label className="block text-xs font-bold">Kategori<select aria-label="Kategori" value={rule.category_id} onChange={e => setRule({ ...rule, category_id: e.target.value })} className={`${inputClass} mt-1`}><option value="">Pilih kategori</option>{categories.filter(c => c.is_active).map(c => <option key={c.id} value={c.id}>{"— ".repeat(c.level || 0)}{c.name}</option>)}</select></label>
        <div className="grid sm:grid-cols-3 gap-2"><label className="text-xs font-bold">Jenis diskon<select aria-label="Jenis diskon" value={rule.discount_type} onChange={e => setRule({ ...rule, discount_type: e.target.value })} className={`${inputClass} mt-1`}><option value="percent">Persentase (%)</option><option value="nominal">Potongan (Rp)</option><option value="fixed_price">Harga promo (Rp)</option></select></label><label className="text-xs font-bold">Nilai<input type="number" min="0" step="0.01" value={rule.discount_value} onChange={e => setRule({ ...rule, discount_value: Number(e.target.value) })} className={`${inputClass} mt-1`} /></label><label className="text-xs font-bold">Kuota per produk<input type="number" min="1" step="1" value={rule.quota_per_product} onChange={e => setRule({ ...rule, quota_per_product: Number(e.target.value) })} className={`${inputClass} mt-1`} /></label></div>
        <div className="flex flex-wrap items-center justify-between gap-3"><label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={rule.include_descendants} onChange={e => setRule({ ...rule, include_descendants: e.target.checked })} /> Sertakan subkategori</label><button type="button" onClick={addRule} className="text-sm font-bold text-meow-salmon">+ Tambah aturan kategori</button></div></>}
        {editing.id && editing.category_rules.length > 0 && <button type="button" disabled={saving} className="text-sm font-bold text-meow-salmon" onClick={async () => { setSaving(true); try { await api.post(`/admin/flash-sales/${editing.id}/refresh-categories`); const { data } = await api.get("/admin/flash-sales"); setCampaigns(data.flash_sales); const updated = data.flash_sales.find(c => c.id === editing.id); if (updated) setEditing(updated); toast.success("Produk kategori diperbarui"); } catch (err) { setError(adminError(err)); } finally { setSaving(false); } }}>Tambahkan produk kategori terbaru</button>}
      </section>
      <section className="border rounded-2xl p-4 space-y-3"><h3 className="font-bold">Produk dalam kampanye</h3><p className="text-xs text-meow-gray">Harga dan kuota tersimpan akan divalidasi kembali terhadap penjualan serta reservasi aktif.</p><div className="space-y-2 max-h-64 overflow-y-auto">{editing.items.map((it, index) => <div key={it.id || `${it.product_id}-${index}`} className="grid grid-cols-[1fr_5.5rem_4rem_1.5rem] items-end gap-2 text-xs border-b pb-2"><span className="min-w-0 break-words">{it.product_name || products.find(p => p.id === it.product_id)?.name || it.product_id}<span className="block text-zinc-500">Terjual {it.sold || 0} · Dipesan {it.reserved || 0}</span></span><label>Harga<input aria-label={`Harga produk ${index + 1}`} type="number" min="0" step="0.01" value={it.flash_price} onChange={e => setEditing({ ...editing, items: editing.items.map((row, i) => i === index ? { ...row, flash_price: Number(e.target.value) } : row) })} className="w-full border p-1 rounded" /></label><label>Kuota<input aria-label={`Kuota produk ${index + 1}`} type="number" min="1" step="1" value={it.quota} onChange={e => setEditing({ ...editing, items: editing.items.map((row, i) => i === index ? { ...row, quota: Number(e.target.value) } : row) })} className="w-full border p-1 rounded" /></label>{editing.id ? <input type="checkbox" aria-label={`Produk ${index + 1} aktif`} checked={it.is_active !== false} onChange={e => setEditing({ ...editing, items: editing.items.map((row, i) => i === index ? { ...row, is_active: e.target.checked } : row) })} /> : <button type="button" onClick={() => setEditing({ ...editing, items: editing.items.filter((_, i) => i !== index) })} aria-label="Hapus produk"><X size={15} /></button>}</div>)}</div>
        {!editing.id && <><input aria-label="Cari produk" placeholder="Cari produk berdasarkan nama" value={query} onChange={e => setQuery(e.target.value)} className={inputClass} /><div className="grid sm:grid-cols-[2fr_1fr_1fr] gap-2"><label className="text-xs font-bold">Produk<select aria-label="Produk" value={item.product_id} onChange={e => { const p = products.find(row => row.id === e.target.value); setItem({ ...item, product_id: e.target.value, flash_price: p?.discount_price ?? p?.price ?? 0 }); }} className={`${inputClass} mt-1`}><option value="">Pilih produk</option>{products.filter(p => p.is_active).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label><label className="text-xs font-bold">Harga promo (Rp)<input type="number" min="0" step="0.01" value={item.flash_price} onChange={e => setItem({ ...item, flash_price: Number(e.target.value) })} className={`${inputClass} mt-1`} /></label><label className="text-xs font-bold">Kuota<input type="number" min="1" step="1" value={item.quota} onChange={e => setItem({ ...item, quota: Number(e.target.value) })} className={`${inputClass} mt-1`} /></label></div><button type="button" onClick={addItem} className="text-sm font-bold text-meow-salmon">+ Tambah produk</button></>}
      </section>
      <label className="flex gap-2 items-center text-sm font-bold"><input type="checkbox" checked={editing.is_active} onChange={e => setEditing({ ...editing, is_active: e.target.checked })} /> Aktif sesuai jadwal</label><div className="flex justify-end gap-3"><button type="button" disabled={saving} onClick={() => setEditing(null)} className="btn-secondary">Batal</button><button disabled={saving} type="submit" className="btn-primary disabled:opacity-50">{saving ? "Menyimpan…" : "Simpan Flash Sale"}</button></div>
    </form></div>}
  </div>;
}
