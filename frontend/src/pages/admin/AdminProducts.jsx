import React, { useCallback, useEffect, useState } from "react";
import { api, formatIDR } from "../../lib/api";
import { Plus, Edit2, Trash2, Search, Package } from "lucide-react";
import { toast } from "sonner";
import ImagePicker from "../../components/ImagePicker";
import { localDateTime, utcDateTime } from "./adminUtils";

const AdminProducts = () => {
  const [products, setProducts] = useState([]);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState(null); // product object or "new"
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);

  const load = useCallback(() => {
    api.get("/admin/products", { params: { q } }).then(({ data }) => setProducts(data.products));
  }, [q]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    api.get("/admin/categories").then(({ data }) => setCategories(data.categories));
    api.get("/admin/brands").then(({ data }) => setBrands(data.brands));
  }, []);

  const handleDelete = async (pid) => {
    if (!confirm("Nonaktifkan produk ini?")) return;
    await api.delete(`/admin/products/${pid}`);
    toast.success("Produk dinonaktifkan");
    load();
  };

  return (
    <div data-testid="admin-products">
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-heading text-3xl font-black">Produk</h1>
        <button onClick={() => setEditing("new")} className="btn-primary text-sm" data-testid="new-product-btn">
          <Plus className="inline h-4 w-4 mr-1" /> Tambah Produk
        </button>
      </div>

      <div className="flex items-center bg-white border border-zinc-200 rounded-full px-4 py-2 mb-4 max-w-md">
        <Search className="h-4 w-4 text-meow-gray mr-2" />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari produk..." className="bg-transparent flex-1 outline-none text-sm" data-testid="admin-product-search" />
      </div>

      <div className="bg-white rounded-3xl overflow-hidden border border-zinc-200">
        <table className="w-full text-sm" data-testid="admin-products-table">
          <thead className="bg-meow-bg text-xs uppercase tracking-wider text-meow-gray">
            <tr>
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
                <tr key={p.id} className="border-t border-zinc-100" data-testid={`product-row-${p.id}`}>
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
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => setEditing(p)} className="p-2 text-meow-gray hover:text-meow-salmon" data-testid={`edit-${p.id}`}><Edit2 className="h-4 w-4" /></button>
                    <button onClick={() => handleDelete(p.id)} className="p-2 text-meow-gray hover:text-red-500" data-testid={`delete-${p.id}`}><Trash2 className="h-4 w-4" /></button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {products.length === 0 && <p className="text-center text-meow-gray py-8">Belum ada produk.</p>}
      </div>

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
    name: product.name, description: product.description,
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
    name: "", description: "", product_type: "frame",
    price: 0, discount_price: null, weight_gram: 100,
    primary_category_id: null, category_ids: [],
    brand_id: null, segments: ["Unisex"],
    main_image: "https://images.unsplash.com/photo-1772009288423-96090d2998c7?w=900",
    gallery: [], variants: [{ color: "Hitam", color_hex: "#0B192C", size: "M", sku: `ME-NEW-${Date.now()}`, stock: 10 }],
    badges: [], is_active: true, is_new_arrival: false, new_arrival_until: null,
  });

  const submit = async (e) => {
    e.preventDefault();
    try {
      if (isEdit) {
        await api.put(`/admin/products/${product.id}`, form);
        toast.success("Produk diupdate");
      } else {
        await api.post("/admin/products", form);
        toast.success("Produk dibuat");
      }
      onSaved();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Gagal");
    }
  };

  const addVariant = () => setForm({ ...form, variants: [...form.variants, { color: "", color_hex: "#000000", size: "M", sku: `ME-${Date.now()}`, stock: 5 }] });
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
          <select value={form.product_type} onChange={(e) => setForm({ ...form, product_type: e.target.value })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="pf-type">
            <option value="frame">Frame</option>
            <option value="lens">Lensa</option>
            <option value="package">Paket</option>
          </select>
        </div>
        <textarea required placeholder="Deskripsi" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" rows={3} data-testid="pf-desc" />
        <div className="grid grid-cols-3 gap-2">
          <input required type="number" placeholder="Harga" value={form.price} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="pf-price" />
          <input type="number" placeholder="Harga Diskon" value={form.discount_price || ""} onChange={(e) => setForm({ ...form, discount_price: e.target.value ? Number(e.target.value) : null })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="pf-disc" />
          <input required type="number" placeholder="Berat (g)" value={form.weight_gram} onChange={(e) => setForm({ ...form, weight_gram: Number(e.target.value) })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="pf-weight" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <select value={form.brand_id || ""} onChange={(e) => setForm({ ...form, brand_id: e.target.value || null })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="pf-brand">
            <option value="">-- Brand --</option>
            {brands.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
          <select value={form.primary_category_id || ""} onChange={(e) => {
            const id = e.target.value || null;
            const cats = id && !form.category_ids.includes(id) ? [...form.category_ids, id] : form.category_ids;
            setForm({ ...form, primary_category_id: id, category_ids: cats });
          }} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="pf-category">
            <option value="">-- Kategori Utama --</option>
            {categories.filter((c) => c.is_active).map((c) => <option key={c.id} value={c.id}>{"— ".repeat(c.level)}{c.name}</option>)}
          </select>
        </div>
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
          <p className="text-xs font-bold uppercase tracking-wider mb-2">Segmentasi</p>
          <div className="flex flex-wrap gap-2">
            {["Pria", "Wanita", "Anak-anak", "Unisex"].map((s) => (
              <label key={s} className="text-xs cursor-pointer">
                <input type="checkbox" checked={form.segments.includes(s)} onChange={() => {
                  const next = form.segments.includes(s) ? form.segments.filter(x => x !== s) : [...form.segments, s];
                  setForm({ ...form, segments: next });
                }} className="mr-1" /> {s}
              </label>
            ))}
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
