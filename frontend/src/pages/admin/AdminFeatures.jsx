import React, { useCallback, useEffect, useId, useState } from "react";
import { Link } from "react-router-dom";
import { Glasses, MessageCircle, Plus, Save, X, ExternalLink, Search } from "lucide-react";
import { toast } from "sonner";
import { api, imageSrc } from "../../lib/api";
import ImagePicker from "../../components/ImagePicker";
import { adminError, inputClass } from "./adminUtils";

function Field({ label, children, hint }) {
  const id = useId();
  return <div className="space-y-1 text-sm font-semibold"><label htmlFor={id} className="block">{label}</label>{React.cloneElement(children, { id, "aria-describedby": hint ? `${id}-hint` : undefined })}{hint && <p id={`${id}-hint`} className="font-normal text-xs text-meow-gray">{hint}</p>}</div>;
}

export function AdminWhatsApp() {
  const [form, setForm] = useState({ enabled: false, phone_number: "", default_text: "Halo, saya ingin bertanya tentang produk Meow Eyes." });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setError(""); setLoading(true);
    try { const { data } = await api.get("/admin/settings/whatsapp"); setForm(data); }
    catch (err) { setError(adminError(err, "Pengaturan WhatsApp belum dapat dimuat.")); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const submit = async (event) => {
    event.preventDefault(); setSaving(true); setError("");
    try {
      const { data } = await api.put("/admin/settings/whatsapp", form);
      setForm(data); toast.success("Pengaturan WhatsApp tersimpan");
      window.dispatchEvent(new Event("meow:whatsapp-updated"));
    } catch (err) { setError(adminError(err)); }
    finally { setSaving(false); }
  };
  const digits = (form.phone_number || "").replace(/\D/g, "");
  const link = /^\d{8,15}$/.test(digits) ? `https://wa.me/${digits}?text=${encodeURIComponent(form.default_text || "")}` : null;
  return <div className="max-w-3xl space-y-6" data-testid="admin-whatsapp">
    <header><h1 className="font-heading text-3xl font-black flex items-center gap-3"><MessageCircle /> WhatsApp</h1><p className="text-sm text-meow-gray mt-2">Atur kontak yang tampil pada tombol WhatsApp di seluruh halaman.</p></header>
    {error && <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}{!saving && <button onClick={load} className="ml-3 underline">Muat ulang</button>}</div>}
    {loading ? <p role="status">Memuat pengaturan…</p> : <form onSubmit={submit} className="rounded-3xl border border-zinc-200 bg-white p-6 space-y-5">
      <label className="flex items-center gap-3 font-bold"><input type="checkbox" checked={Boolean(form.enabled)} onChange={e => setForm({ ...form, enabled: e.target.checked })} className="h-5 w-5 accent-emerald-600" /> Tampilkan tombol WhatsApp</label>
      <Field label="Nomor WhatsApp" hint="Gunakan kode negara, misalnya 6281234567890. Tanpa awalan 0, spasi, atau tanda +.">
        <input required={form.enabled} type="tel" inputMode="numeric" pattern="[1-9][0-9]{7,14}" maxLength={15} value={form.phone_number || ""} onChange={e => setForm({ ...form, phone_number: e.target.value })} className={inputClass} data-testid="whatsapp-number" />
      </Field>
      <Field label="Pesan awal"><textarea rows={4} maxLength={2000} value={form.default_text || ""} onChange={e => setForm({ ...form, default_text: e.target.value })} className={inputClass} data-testid="whatsapp-text" /></Field>
      <div className="flex flex-wrap gap-3 items-center"><button type="submit" disabled={saving} className="btn-primary inline-flex items-center gap-2 disabled:opacity-50" data-testid="whatsapp-save"><Save size={16} />{saving ? "Menyimpan…" : "Simpan pengaturan"}</button>{link && <a href={link} target="_blank" rel="noopener noreferrer" className="text-sm text-emerald-700 font-bold inline-flex items-center gap-1">Coba tautan <ExternalLink size={14} /></a>}</div>
    </form>}
  </div>;
}

const emptyAsset = () => ({ product_id: "", variant_id: "", asset_type: "image", source_url: "", preview_url: "", status: "draft", scale: 1, offset_x: 0, offset_y: 0, offset_z: 0, rotation_x: 0, rotation_y: 0, rotation_z: 0, sort_order: 0, calibration: null });

export function AdminTryOn() {
  const [assets, setAssets] = useState([]);
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [calibration, setCalibration] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { const { data } = await api.get("/admin/try-on-assets"); setAssets(data.assets || []); }
    catch (err) { setError(adminError(err)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const { data } = await api.get("/admin/products", { params: { q: query, limit: 100, product_type: "frame" }, signal: controller.signal });
        setProducts((data.products || []).filter(p => p.product_type === "frame"));
      } catch (err) { if (!controller.signal.aborted) setError(adminError(err, "Daftar frame belum dapat dimuat.")); }
    }, 200);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query]);
  const open = (asset) => {
    setEditing(asset ? { ...emptyAsset(), ...asset, variant_id: asset.variant_id || "" } : emptyAsset());
    setCalibration(asset?.calibration ? JSON.stringify(asset.calibration, null, 2) : ""); setError("");
  };
  const submit = async (event) => {
    event.preventDefault(); setSaving(true); setError("");
    try {
      let parsed = null;
      if (calibration.trim()) {
        parsed = JSON.parse(calibration);
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Kalibrasi harus berupa objek JSON.");
      }
      const payload = Object.fromEntries(Object.keys(emptyAsset()).map(key => [key, editing[key]]));
      payload.variant_id = editing.variant_id || null; payload.calibration = parsed; payload.preview_url = editing.preview_url || null;
      payload.upload_id = editing.upload_id || null;
      if (payload.source_url) payload.upload_id = null;
      if (editing.id) await api.patch(`/admin/try-on-assets/${editing.id}`, payload);
      else await api.post("/admin/try-on-assets", payload);
      setEditing(null); toast.success("Aset Virtual Try-On tersimpan"); await load();
    } catch (err) { setError(err instanceof SyntaxError ? "Format JSON kalibrasi belum valid." : err.response ? adminError(err) : err.message); }
    finally { setSaving(false); }
  };
  const selected = products.find(p => p.id === editing?.product_id);
  return <div className="space-y-5" data-testid="admin-try-on">
    <header className="flex flex-wrap justify-between items-start gap-4"><div><h1 className="font-heading text-3xl font-black flex items-center gap-3"><Glasses /> Virtual Try-On</h1><p className="mt-2 text-sm text-meow-gray">Hubungkan frame dengan gambar transparan atau model 3D, lalu terbitkan ke halaman produk.</p></div><button onClick={() => open()} className="btn-primary inline-flex items-center gap-2"><Plus size={16} /> Tambah aset</button></header>
    {error && !editing && <p role="alert" className="bg-red-50 text-red-700 p-4 rounded-2xl">{error} <button onClick={load} className="underline">Coba lagi</button></p>}
    {loading ? <p role="status">Memuat aset…</p> : assets.length === 0 ? <div className="bg-white border rounded-3xl p-8 text-center"><Glasses className="mx-auto h-10 w-10 text-meow-gray" /><h2 className="font-bold mt-3">Belum ada aset try-on</h2><p className="text-sm text-meow-gray mt-2">Tambahkan gambar frame PNG/WebP transparan atau URL model GLB/GLTF.</p></div> : <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">{assets.map(asset => <article key={asset.id} className="bg-white border border-zinc-200 rounded-3xl overflow-hidden" data-testid={`try-on-asset-${asset.id}`}>
      <div className="h-36 bg-zinc-50 flex items-center justify-center">{asset.preview_url || asset.asset_type === "image" ? <img src={imageSrc(asset.preview_url || asset.source_url)} alt="Pratinjau frame" className="max-h-32 max-w-full object-contain" /> : <Glasses className="w-14 h-14 text-zinc-300" />}</div>
      <div className="p-4 space-y-3"><div><h2 className="font-bold">{asset.product_name || products.find(p => p.id === asset.product_id)?.name || asset.product_id}</h2><p className="text-xs text-meow-gray mt-1">{asset.asset_type.toUpperCase()} · {asset.status} · Urutan {asset.sort_order}</p></div><div className="flex gap-4 text-sm font-bold"><button onClick={() => open(asset)} className="text-meow-salmon">Edit aset</button><button onClick={async () => { if (!window.confirm("Hapus aset Virtual Try-On ini?")) return; try { await api.delete(`/admin/try-on-assets/${asset.id}`); await load(); } catch (err) { toast.error(adminError(err)); } }} className="text-red-600">Hapus</button>{(asset.product_slug || products.find(p => p.id === asset.product_id)?.slug) && <Link to={`/products/${asset.product_slug || products.find(p => p.id === asset.product_id)?.slug}`} className="ml-auto text-meow-gray">Lihat produk</Link>}</div></div>
    </article>)}</div>}
    {editing && <div className="fixed inset-0 z-50 bg-black/60 grid place-items-center p-4" onClick={() => !saving && setEditing(null)}><form onSubmit={submit} onClick={e => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="tryon-form-title" className="max-w-2xl w-full max-h-[90vh] overflow-y-auto bg-white rounded-3xl p-6 space-y-4">
      <div className="flex justify-between items-center"><h2 id="tryon-form-title" className="text-xl font-heading font-bold">{editing.id ? "Edit" : "Tambah"} aset Virtual Try-On</h2><button type="button" aria-label="Tutup" disabled={saving} onClick={() => setEditing(null)}><X /></button></div>
      {error && <p role="alert" className="bg-red-50 text-red-700 p-3 rounded-xl text-sm">{error}</p>}
      <Field label="Cari frame"><input value={query} onChange={e => setQuery(e.target.value)} className={inputClass} placeholder="Nama atau SKU frame" /></Field>
      <Field label="Produk frame"><select required value={editing.product_id} onChange={e => setEditing({ ...editing, product_id: e.target.value, variant_id: "" })} className={inputClass}><option value="">Pilih frame</option>{editing.product_id && !selected && <option value={editing.product_id}>{editing.product_name || editing.product_id}</option>}{products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
      <Field label="Varian"><select value={editing.variant_id || ""} onChange={e => setEditing({ ...editing, variant_id: e.target.value })} className={inputClass}><option value="">Semua varian produk ini</option>{editing.variant_id && !selected?.variants?.some(v => v.id === editing.variant_id) && <option value={editing.variant_id}>{editing.variant_id}</option>}{(selected?.variants || []).map(v => <option key={v.id} value={v.id}>{[v.color, v.size, v.sku].filter(Boolean).join(" · ")}</option>)}</select></Field>
      <div className="grid sm:grid-cols-2 gap-4"><Field label="Format aset"><select value={editing.asset_type} onChange={e => setEditing({ ...editing, asset_type: e.target.value })} className={inputClass}><option value="image">Gambar transparan</option><option value="glb">Model GLB</option><option value="gltf">Model GLTF</option></select></Field><Field label="Status"><select value={editing.status} onChange={e => setEditing({ ...editing, status: e.target.value })} className={inputClass}><option value="draft">Draft</option><option value="published">Published</option><option value="archived">Archived</option></select></Field></div>
      {editing.asset_type === "image" ? <ImagePicker label="Gambar frame (PNG / WebP transparan)" value={editing.source_url || ""} onChange={url => setEditing({ ...editing, source_url: url })} testId="tryon-image" /> : <Field label="URL model 3D" hint="Gunakan URL HTTPS yang dapat diakses browser. Server aset harus mengizinkan CORS; berkas tekstur GLTF harus tersedia pada lokasi yang sama."><input required type="url" value={editing.source_url || ""} onChange={e => setEditing({ ...editing, source_url: e.target.value })} className={inputClass} placeholder="https://cdn.toko.id/frames/model.glb" /></Field>}
      <ImagePicker label="Gambar pratinjau (opsional)" value={editing.preview_url || ""} onChange={url => setEditing({ ...editing, preview_url: url })} testId="tryon-preview" />
      <details className="rounded-2xl border p-4"><summary className="font-bold text-sm cursor-pointer">Posisi dan kalibrasi awal</summary><p className="text-xs text-meow-gray mt-2">Skala adalah pengali lebar frame. Offset X/Y berupa proporsi lebar/tinggi area. Rotasi dalam derajat. Pelanggan dapat menyesuaikan posisi saat mencoba frame.</p><div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-3">{["scale", "offset_x", "offset_y", "offset_z", "rotation_x", "rotation_y", "rotation_z"].map(key => <Field key={key} label={key.replaceAll("_", " ")}><input required type="number" step="0.001" min={key === "scale" ? "0.01" : key.startsWith("offset") ? "-10" : "-360"} max={key === "scale" || key.startsWith("offset") ? "10" : "360"} value={editing[key]} onChange={e => setEditing({ ...editing, [key]: e.target.value === "" ? "" : Number(e.target.value) })} className={inputClass} /></Field>)}</div><div className="mt-3"><Field label="Metadata kalibrasi (opsional)" hint="JSON ini disimpan sebagai catatan. Preview memakai nilai skala, offset, dan rotasi di atas."><textarea value={calibration} onChange={e => setCalibration(e.target.value)} rows={3} className={`${inputClass} font-mono`} placeholder='{"frame_width_mm": 138}' /></Field></div></details>
      <Field label="Urutan tampilan"><input type="number" step="1" min="0" required value={editing.sort_order} onChange={e => setEditing({ ...editing, sort_order: Number(e.target.value) })} className={inputClass} /></Field>
      <div className="flex justify-end gap-3"><button type="button" disabled={saving} onClick={() => setEditing(null)} className="btn-secondary">Batal</button><button disabled={saving} className="btn-primary disabled:opacity-50">{saving ? "Menyimpan…" : "Simpan aset"}</button></div>
    </form></div>}
  </div>;
}
