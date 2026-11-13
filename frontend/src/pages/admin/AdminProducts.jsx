import React, { useCallback, useEffect, useRef, useState } from "react";
import { api, apiError, formatIDR } from "../../lib/api";
import { Plus, Edit2, Trash2, Search, Power, Ruler, Copy } from "lucide-react";
import { toast } from "sonner";
import ProductMasterFields from "../../components/ProductMasterFields";
import { productMasterIds } from "../../lib/masterCategories";
import ImagePicker from "../../components/ImagePicker";
import RichTextEditor from "../../components/RichTextEditor";
import { hasRichContent } from "../../lib/richContent";
import { localDateTime, utcDateTime } from "./adminUtils";
import FrameSpecificationEditor from "./FrameSpecificationEditor";

const AdminProducts = () => {
  const [products, setProducts] = useState([]);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState(null); // product object or "new"
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [frameSpecifications, setFrameSpecifications] = useState(null);
  const [selected, setSelected] = useState([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const selectAll = useRef(null);
  const pageSize = 50;

  const load = useCallback(async ({ signal } = {}) => {
    setLoading(true);
    try {
      const { data } = await api.get("/admin/products", { params: { q, page, limit: pageSize }, signal });
      if (signal?.aborted) return;
      const rows = data.products || [];
      setProducts(rows); setTotal(data.total ?? rows.length);
      setSelected(ids => ids.filter(id => rows.some(product => product.id === id)));
      const lastPage = Math.max(1, Math.ceil((data.total ?? rows.length) / pageSize));
      if (page > lastPage) setPage(lastPage);
    } catch (err) {
      if (!signal?.aborted) { setProducts([]); setSelected([]); setError(apiError(err, "Daftar produk belum dapat dimuat.")); }
    } finally { if (!signal?.aborted) setLoading(false); }
  }, [q, page]);
  useEffect(() => {
    const controller = new AbortController(); setError("");
    load({ signal: controller.signal });
    return () => controller.abort();
  }, [load]);
  useEffect(() => {
    api.get("/admin/categories").then(({ data }) => setCategories(data.categories));
    api.get("/admin/brands").then(({ data }) => setBrands(data.brands));
  }, []);

  const allSelected = products.length > 0 && products.every(product => selected.includes(product.id));
  useEffect(() => {
    if (selectAll.current) selectAll.current.indeterminate = selected.length > 0 && !allSelected;
  }, [selected, allSelected]);
  const toggle = id => setSelected(ids => ids.includes(id) ? ids.filter(value => value !== id) : [...ids, id]);
  const handleAction = async (action, ids) => {
    if (busy || loading || !ids.length) return;
    const target = ids.length === 1 ? `produk "${products.find(product => product.id === ids[0])?.name || ids[0]}"` : `${ids.length} produk terpilih`;
    const message = action === "delete"
      ? `Hapus ${target} dari daftar admin dan katalog? Riwayat pesanan tetap disimpan.`
      : `Nonaktifkan ${target}? Produk dapat diaktifkan kembali melalui Edit Produk.`;
    if (!window.confirm(message)) return;
    setBusy(true); setError("");
    try {
      await api.post("/admin/products/bulk-actions", { action, product_ids: ids });
      setSelected(current => current.filter(id => !ids.includes(id)));
      toast.success(`${ids.length} produk ${action === "delete" ? "dihapus" : "dinonaktifkan"}`);
      await load();
    } catch (err) {
      setError(err?.response?.status === 405
        ? "Layanan backend belum memuat endpoint aksi produk terbaru. Restart backend secara manual, lalu muat ulang halaman ini dan coba kembali."
        : apiError(err, "Aksi produk belum berhasil. Silakan coba kembali."));
    } finally { setBusy(false); }
  };
  const duplicate = async product => {
    if (busy || loading) return;
    setBusy(true); setError('');
    try {
      const { data } = await api.post(`/admin/products/${product.id}/duplicate`);
      if (!data.product?.id || data.product.id === product.id) throw new Error('Invalid duplicate response');
      setSelected([]);
      if (q || page !== 1) { setQ(''); setPage(1); }
      else await load();
      setEditing(data.product);
      toast.success('Produk diduplikat sebagai nonaktif dengan SKU baru dan stok nol.');
    } catch (err) {
      setError(apiError(err, 'Produk belum berhasil diduplikat. Silakan coba kembali.'));
    } finally { setBusy(false); }
  };

  return (
    <div data-testid="admin-products">
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-heading text-3xl font-black">Produk</h1>
        <button disabled={busy} onClick={() => setEditing("new")} className="btn-primary text-sm" data-testid="new-product-btn">
          <Plus className="inline h-4 w-4 mr-1" /> Tambah Produk
        </button>
      </div>

      <div className="flex items-center bg-white border border-zinc-200 rounded-full px-4 py-2 mb-4 max-w-md">
        <Search className="h-4 w-4 text-meow-gray mr-2" />
        <input disabled={busy} value={q} onChange={(e) => { setQ(e.target.value); setPage(1); setSelected([]); }} placeholder="Cari produk..." className="bg-transparent flex-1 min-w-0 outline-none text-sm" data-testid="admin-product-search" />
      </div>

      {error && <div role="alert" className="mb-4 p-4 bg-red-50 text-red-700 rounded-xl text-sm">{error}<button type="button" disabled={busy || loading} onClick={() => { setError(""); load(); }} className="underline ml-3">Muat ulang</button></div>}
      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-2xl border bg-white p-3" data-testid="product-bulk-actions" aria-busy={busy}>
        <span className="text-sm font-semibold mr-auto" role="status" aria-live="polite">{selected.length} produk dipilih</span>
        <button type="button" disabled={busy || loading || !selected.length} onClick={() => handleAction("deactivate", [...selected])} className="inline-flex gap-2 items-center px-3 py-2 rounded-xl border text-sm disabled:opacity-40" data-testid="bulk-deactivate-products"><Power size={16} />Nonaktifkan Terpilih</button>
        <button type="button" disabled={busy || loading || !selected.length} onClick={() => handleAction("delete", [...selected])} className="inline-flex gap-2 items-center px-3 py-2 rounded-xl bg-red-50 text-red-700 border border-red-200 text-sm disabled:opacity-40" data-testid="bulk-delete-products"><Trash2 size={16} />Hapus Terpilih</button>
        {busy && <span className="text-xs text-meow-gray">Memproses...</span>}
      </div>
      <p className="text-xs text-meow-gray mb-3">Pilih beberapa produk atau centang semua produk pada halaman ini. Hapus menghilangkan produk dari daftar; riwayat pesanan tetap tersimpan.</p>
      <div className="bg-white rounded-3xl overflow-x-auto border border-zinc-200" aria-busy={loading}>
        <table className="w-full text-sm" data-testid="admin-products-table">
          <thead className="bg-meow-bg text-xs uppercase tracking-wider text-meow-gray">
            <tr>
              <th className="px-3 py-3 w-10"><input ref={selectAll} type="checkbox" aria-label="Pilih semua produk pada halaman ini" checked={allSelected} disabled={busy || loading || !products.length} onChange={() => setSelected(allSelected ? [] : products.map(product => product.id))} /></th>
              <th className="text-left px-4 py-3">Produk</th>
              <th className="text-left px-4 py-3 hidden md:table-cell">Tipe</th>
              <th className="text-left px-4 py-3 hidden md:table-cell">Harga</th>
              <th className="text-left px-4 py-3 hidden lg:table-cell">Stok</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-right px-4 py-3">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => {
              const stock = (p.variants || []).reduce((s, v) => s + (v.stock || 0), 0);
              return (
                <tr key={p.id} className={`border-t border-zinc-100 ${selected.includes(p.id) ? "bg-meow-salmon/5" : ""}`} data-testid={`product-row-${p.id}`}>
                  <td className="px-3 py-3"><input type="checkbox" aria-label={`Pilih ${p.name}`} checked={selected.includes(p.id)} disabled={busy || loading} onChange={() => toggle(p.id)} /></td>
                  <td className="px-4 py-3 flex items-center gap-3">
                    <img src={p.main_image} alt="" className="h-12 w-12 rounded-xl object-cover" />
                    <div>
                      <p className="font-bold">{p.name}</p>
                      <p className="text-xs text-meow-gray">{p.sku}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell capitalize">{p.product_type}</td>
                  <td className="px-4 py-3 hidden md:table-cell">{formatIDR(p.discount_price || p.price)}</td>
                  <td className="px-4 py-3 hidden lg:table-cell">{stock}</td>
                  <td className="px-4 py-3">
                    {p.is_active ? <span className="text-xs px-2 py-1 rounded-full bg-meow-mint/20 text-meow-mint">Aktif</span> : <span className="text-xs px-2 py-1 rounded-full bg-zinc-100">Nonaktif</span>}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    {p.product_type === "frame" && <button type="button" disabled={busy} onClick={() => setFrameSpecifications(p)} className="p-2 text-meow-gray hover:text-meow-salmon disabled:opacity-40" aria-label={"Spesifikasi Meowsurement " + p.name} title="Spesifikasi Meowsurement" data-testid={"frame-specification-" + p.id}><Ruler className="h-4 w-4" /></button>}
                    <button type="button" disabled={busy} onClick={() => setEditing(p)} className="p-2 text-meow-gray hover:text-meow-salmon disabled:opacity-40" aria-label={`Edit ${p.name}`} data-testid={`edit-${p.id}`}><Edit2 className="h-4 w-4" /></button>
                    <button type="button" disabled={busy || loading} onClick={() => duplicate(p)} className="inline-flex items-center gap-1 p-2 text-meow-gray hover:text-meow-salmon disabled:opacity-40 text-xs" aria-label={`Duplikat ${p.name}`} data-testid={`duplicate-${p.id}`}><Copy className="h-4 w-4" />Duplikat</button>
                    <button type="button" disabled={busy || loading || !p.is_active} onClick={() => handleAction("deactivate", [p.id])} className="inline-flex items-center gap-1 p-2 text-meow-gray hover:text-amber-700 disabled:opacity-40 text-xs" aria-label={`Nonaktifkan ${p.name}`} data-testid={`deactivate-${p.id}`}><Power className="h-4 w-4" />Nonaktifkan</button>
                    <button type="button" disabled={busy || loading} onClick={() => handleAction("delete", [p.id])} className="inline-flex items-center gap-1 p-2 text-red-600 hover:text-red-800 disabled:opacity-40 text-xs" aria-label={`Hapus ${p.name}`} data-testid={`delete-${p.id}`}><Trash2 className="h-4 w-4" />Hapus</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {loading ? <p className="text-center text-meow-gray py-8">Memuat produk...</p> : products.length === 0 && <p className="text-center text-meow-gray py-8">Belum ada produk.</p>}
      </div>
      <div className="flex flex-wrap justify-between items-center gap-3 mt-4 text-sm">
        <span>{total} produk · Halaman {page} dari {Math.max(1, Math.ceil(total / pageSize))}</span>
        <div className="flex gap-4"><button type="button" disabled={busy || loading || page <= 1} className="disabled:opacity-40" onClick={() => { setSelected([]); setPage(page - 1); }}>Sebelumnya</button><button type="button" disabled={busy || loading || page * pageSize >= total} className="disabled:opacity-40" onClick={() => { setSelected([]); setPage(page + 1); }}>Berikutnya</button></div>
      </div>

      {frameSpecifications && <FrameSpecificationEditor product={frameSpecifications} onClose={() => setFrameSpecifications(null)} />}
      {editing && (
        <ProductForm
          product={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); load(); }}
          categories={categories}
          brands={brands}
        />
      )}
    </div>
  );
};

const ProductForm = ({ product, onClose, onSaved, categories, brands }) => {
  const isEdit = !!product;
  const [form, setForm] = useState(product ? {
    name: product.name, sku: product.sku, description: product.description,
    product_type: product.product_type,
    price: product.price, discount_price: product.discount_price,
    weight_gram: product.weight_gram,
    primary_category_id: product.primary_category_id,
    category_ids: product.category_ids || [],
    brand_id: product.brand_id,
    segments: product.segments || [],
    main_image: product.main_image,
    gallery: product.gallery || [],
    variants: product.variants || [],
    badges: product.badges || [],
    is_active: product.is_active,
    is_new_arrival: product.is_new_arrival || false,
    new_arrival_until: product.new_arrival_until || null,
  } : {
    name: "", sku: "", description: "", product_type: "frame",
    price: 0, discount_price: null, weight_gram: 100,
    primary_category_id: null, category_ids: [],
    brand_id: null, segments: ["Unisex"],
    main_image: "https://images.unsplash.com/photo-1772009288423-96090d2998c7?w=900",
    gallery: [], variants: [{ color: "Hitam", color_hex: "#0B192C", size: "M", sku: `ME-NEW-${Date.now()}`, stock: 0 }],
    badges: [], is_active: true, is_new_arrival: false, new_arrival_until: null,
  });

  const submit = async (e) => {
    e.preventDefault();
    if (!hasRichContent(form.description)) { toast.error("Deskripsi produk wajib diisi"); return; }
    try {
      const categoryIds = productMasterIds(form, categories);
      const payload = { ...form, category_ids: categoryIds, primary_category_id: null,
        segments: categories.filter(item => item.group_type === 'gender' && categoryIds.includes(item.id)).map(item => item.name) };
      if (!payload.sku) delete payload.sku;
      if (isEdit) {
        await api.put(`/admin/products/${product.id}`, payload);
        toast.success("Produk diupdate");
      } else {
        await api.post("/admin/products", payload);
        toast.success("Produk dibuat");
      }
      onSaved();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Gagal");
    }
  };

  const addVariant = () => setForm({ ...form, variants: [...form.variants, { color: "", color_hex: "#000000", size: "M", sku: `ME-${Date.now()}`, stock: 0 }] });
  const updVariant = (i, k, v) => {
    const next = [...form.variants]; next[i] = { ...next[i], [k]: v }; setForm({ ...form, variants: next });
  };
  const delVariant = (i) => setForm({ ...form, variants: form.variants.filter((_, j) => j !== i) });

  return (
    <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4 overflow-y-auto" onClick={onClose}>
      <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto space-y-3" data-testid="product-form">
        <h2 className="font-heading text-2xl font-black">{isEdit ? "Edit Produk" : "Produk Baru"}</h2>
        <div className="grid grid-cols-2 gap-2">
          <input required placeholder="Nama produk" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="pf-name" />
          <input aria-label="SKU produk" placeholder="SKU produk (otomatis jika kosong)" value={form.sku || ''} onChange={e => setForm({ ...form, sku: e.target.value })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" />
        </div>
        <RichTextEditor key={product?.id || 'new-product'} label="Deskripsi produk" value={form.description || ''} onChange={description => setForm(current => ({ ...current, description }))} testId="pf-desc" />
        <div className="grid grid-cols-3 gap-2">
          <input required type="number" placeholder="Harga" value={form.price} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="pf-price" />
          <input type="number" placeholder="Harga Diskon" value={form.discount_price || ""} onChange={(e) => setForm({ ...form, discount_price: e.target.value ? Number(e.target.value) : null })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="pf-disc" />
          <input required type="number" placeholder="Berat (g)" value={form.weight_gram} onChange={(e) => setForm({ ...form, weight_gram: Number(e.target.value) })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="pf-weight" />
        </div>
        <ProductMasterFields categories={categories} brands={brands} form={form} onChange={setForm} />
        <ImagePicker
          label="Gambar Utama Produk"
          value={form.main_image}
          onChange={(url) => setForm({ ...form, main_image: url })}
          testId="pf-image-picker"
        />

        <div>
          <p className="text-xs font-bold uppercase tracking-wider mb-2">Galeri (opsional)</p>
          <div className="space-y-2">
            {(form.gallery || []).map((g, i) => (
              <ImagePicker
                key={i}
                value={g}
                onChange={(url) => {
                  const next = [...(form.gallery || [])];
                  if (url) next[i] = url; else next.splice(i, 1);
                  setForm({ ...form, gallery: next });
                }}
                testId={`pf-gallery-${i}`}
              />
            ))}
            <button
              type="button"
              onClick={() => setForm({ ...form, gallery: [...(form.gallery || []), ""] })}
              className="text-xs underline text-meow-salmon"
              data-testid="pf-add-gallery"
            >
              + Tambah gambar galeri
            </button>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-bold uppercase tracking-wider">Varian</p>
            <button type="button" onClick={addVariant} className="text-xs underline text-meow-salmon" data-testid="pf-add-variant">+ Tambah Varian</button>
          </div>
          <div className="space-y-2">
            {form.variants.map((v, i) => (
              <div key={i} className="grid grid-cols-6 gap-1 text-xs">
                <input placeholder="Warna" value={v.color || ""} onChange={(e) => updVariant(i, "color", e.target.value)} className="px-2 py-1 rounded bg-meow-bg outline-none" />
                <input placeholder="#hex" value={v.color_hex || ""} onChange={(e) => updVariant(i, "color_hex", e.target.value)} className="px-2 py-1 rounded bg-meow-bg outline-none" />
                <input placeholder="Size" value={v.size || ""} onChange={(e) => updVariant(i, "size", e.target.value)} className="px-2 py-1 rounded bg-meow-bg outline-none" />
                <input placeholder="SKU" value={v.sku} onChange={(e) => updVariant(i, "sku", e.target.value)} className="px-2 py-1 rounded bg-meow-bg outline-none" />
                <input type="number" placeholder="Stok" value={v.stock} onChange={(e) => updVariant(i, "stock", Number(e.target.value))} className="px-2 py-1 rounded bg-meow-bg outline-none" />
                <button type="button" onClick={() => delVariant(i)} className="text-red-500 text-xs">Hapus</button>
              </div>
            ))}
          </div>
        </div>

        <section className="border rounded-2xl p-4 space-y-3"><label className="flex items-center gap-2 text-sm font-bold"><input type="checkbox" checked={Boolean(form.is_new_arrival)} onChange={e => setForm({ ...form, is_new_arrival: e.target.checked })} data-testid="pf-new-arrival" /> New Arrival</label><label className="block text-xs">Tampilkan sampai (opsional, waktu lokal)<input type="datetime-local" value={localDateTime(form.new_arrival_until)} onChange={e => setForm({ ...form, new_arrival_until: utcDateTime(e.target.value) })} className="block mt-1 w-full rounded-xl bg-meow-bg px-3 py-2" /></label><p className="text-xs text-meow-gray">Frame yang aktif akan masuk ke halaman New Arrival selama periode ini.</p></section>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} data-testid="pf-active" /> Aktif
        </label>

        <div className="flex gap-2 pt-3">
          <button type="button" onClick={onClose} className="btn-secondary flex-1" data-testid="pf-cancel">Batal</button>
          <button type="submit" className="btn-primary flex-1" data-testid="pf-save">Simpan</button>
        </div>
      </form>
    </div>
  );
};

export default AdminProducts;
