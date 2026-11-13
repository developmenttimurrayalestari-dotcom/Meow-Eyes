import React, { useCallback, useEffect, useState } from "react";
import { LoaderCircle, Ruler, Save } from "lucide-react";
import { api } from "../../lib/api";
import { profileNumeric, profileRequestError } from "../../lib/customerProfile";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "../../components/ui/dialog";

const dimensions = [["a", "A — lebar lens box"], ["b", "B — tinggi lens box"], ["dbl", "DBL — jarak lens box"], ["ed", "ED — diameter efektif (opsional)"], ["temple_length", "Panjang tangkai (opsional)"]];
export const frameSpecValues = (spec = {}) => ({
  a: spec?.a ?? "", b: spec?.b ?? "", dbl: spec?.dbl ?? "", ed: spec?.ed ?? "",
  temple_length: spec?.temple_length ?? "", symmetric: spec?.symmetric === true,
  enabled: spec?.enabled === true, source_note: spec?.source_note || "",
});
export function frameSpecPayload(spec) {
  const output = { enabled: spec.enabled === true, symmetric: spec.symmetric === true, source_note: spec.source_note.trim() };
  for (const [key, label] of dimensions) {
    output[key] = profileNumeric(spec[key], label);
    if (output[key] !== null && output[key] <= 0) throw new Error(label + " harus lebih besar dari nol dalam mm.");
    if (output.enabled && ['a', 'b', 'dbl'].includes(key) && output[key] === null) throw new Error("Lengkapi A, B, dan DBL sebelum mengaktifkan Meowsurement. ED opsional.");
  }
  return output;
}

export default function FrameSpecificationEditor({ product, onClose }) {
  const [spec, setSpec] = useState(() => frameSpecValues()), [variants, setVariants] = useState([]);
  const [version, setVersion] = useState(0), [loading, setLoading] = useState(true), [loaded, setLoaded] = useState(false), [saving, setSaving] = useState(false);
  const [error, setError] = useState(""), [success, setSuccess] = useState(""), [conflict, setConflict] = useState(false);
  const productId = product.id;
  const load = useCallback(async signal => {
    setLoading(true); setLoaded(false); setError(""); setSuccess("");
    try {
      const { data } = await api.get("/admin/products/" + encodeURIComponent(productId) + "/frame-specification", { signal, withCredentials: true });
      if (signal?.aborted) return;
      setSpec(frameSpecValues(data.specification));
      setVersion(data.version ?? data.specification?.version ?? 0);
      setVariants((data.variants || []).map(row => ({ ...row, variant_id: row.variant_id || row.id, inherit_default: row.inherit_default !== false, specification: frameSpecValues(row.specification) })));
      setConflict(false); setLoaded(true);
    } catch (err) { if (!signal?.aborted) setError(profileRequestError(err, "Spesifikasi frame belum dapat dimuat.")); }
    finally { if (!signal?.aborted) setLoading(false); }
  }, [productId]);
  useEffect(() => { const controller = new AbortController(); void load(controller.signal); return () => controller.abort(); }, [load]);
  const save = async event => {
    event.preventDefault();
    if (!loaded || conflict || saving) return;
    setError(""); setSuccess("");
    let payload;
    try { payload = { expected_version: version, specification: frameSpecPayload(spec), variants: variants.map(row => ({ variant_id: row.variant_id, inherit_default: row.inherit_default, ...(row.inherit_default ? {} : { specification: frameSpecPayload(row.specification) }) })) }; }
    catch (err) { setError(err.message); return; }
    setSaving(true);
    try {
      const { data } = await api.put("/admin/products/" + encodeURIComponent(productId) + "/frame-specification", payload, { withCredentials: true });
      setSpec(frameSpecValues(data.specification)); setVersion(data.version ?? data.specification?.version ?? version + 1);
      setVariants((data.variants || []).map(row => ({ ...row, variant_id: row.variant_id || row.id, inherit_default: row.inherit_default !== false, specification: frameSpecValues(row.specification) })));
      setConflict(false); setSuccess("Spesifikasi tersimpan. Sesi Meowsurement baru akan mengambil ukuran sesuai varian ini. Riwayat pengukuran sebelumnya tetap memakai snapshot lama.");
    } catch (err) { setConflict(err?.response?.status === 409); setError(profileRequestError(err, "Spesifikasi belum dapat disimpan.")); }
    finally { setSaving(false); }
  };
  const updateVariant = (id, patch) => setVariants(current => current.map(row => row.variant_id === id ? { ...row, ...patch } : row));
  return <Dialog open onOpenChange={open => { if (!open && !saving) onClose(); }}><DialogContent className="max-w-4xl max-h-[90dvh] overflow-y-auto bg-white p-5 sm:p-7" data-testid="frame-specification-editor">
    <DialogTitle className="font-heading text-2xl font-black flex items-center gap-2"><Ruler className="h-6 w-6" />Spesifikasi Meowsurement</DialogTitle>
    <DialogDescription>{product.name}. Ukuran dalam milimeter, sesuai frame yang dijual. Simpan produk dan variannya terlebih dahulu sebelum mengelola spesifikasi ini.</DialogDescription>
    {loading ? <p className="flex items-center gap-2 py-8" role="status"><LoaderCircle className="h-5 w-5 animate-spin" />Memuat spesifikasi…</p> : loaded && <form onSubmit={save}><fieldset disabled={saving} className="space-y-5 min-w-0">
      <p className="text-sm rounded-2xl bg-meow-amber/15 p-4">A, B, DBL dan ED tidak diambil dari SKU atau teks dimensi bebas. Masukkan ukuran yang telah diperiksa. ED adalah diameter efektif bentuk lensa, bukan perkiraan dari diagonal kotak.</p>
      <SpecFields title="Spesifikasi dasar produk" value={spec} onChange={setSpec} id="default-frame" />
      {variants.length > 0 && <section className="space-y-3"><h3 className="font-bold text-lg">Spesifikasi per varian</h3><p className="text-sm text-meow-gray">Gunakan ukuran dasar jika seluruh dimensi varian sama. Untuk varian ukuran berbeda, nonaktifkan pilihan tersebut dan isi ukuran yang sesuai.</p>{variants.map(row => {
        const detail = (product.variants || []).find(item => item.id === row.variant_id) || row;
        const label = [detail.sku, detail.color, detail.size].filter(Boolean).join(" · ") || row.variant_id;
        return <section key={row.variant_id} className="rounded-2xl border border-meow-midnight/10 p-4" data-testid={"frame-variant-spec-" + row.variant_id}><h4 className="font-semibold">{label}</h4>{detail.is_active === false && <p className="text-xs text-meow-gray">Varian nonaktif</p>}<label className="flex items-start gap-2 text-sm mt-3"><input type="checkbox" checked={row.inherit_default} onChange={event => updateVariant(row.variant_id, { inherit_default: event.target.checked, ...(!event.target.checked && !Object.values(row.specification).some(value => typeof value === "number" || (typeof value === "string" && value)) ? { specification: frameSpecValues(spec) } : {}) })} /><span>Gunakan spesifikasi dasar untuk {label}</span></label>{!row.inherit_default && <div className="mt-4"><SpecFields title={"Ukuran khusus " + label} value={row.specification} id={"variant-" + row.variant_id} onChange={value => updateVariant(row.variant_id, { specification: value })} /></div>}</section>;
      })}</section>}
      {success && <p className="rounded-2xl bg-meow-mint/15 p-4 text-sm" role="status">{success}</p>}
      <div className="flex flex-wrap gap-3"><button type="button" onClick={onClose} disabled={saving} className="btn-secondary">Tutup</button><button type="submit" className="btn-primary inline-flex items-center gap-2 disabled:opacity-50" disabled={saving || conflict} data-testid="save-frame-specification">{saving ? <LoaderCircle className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}Simpan spesifikasi</button></div>
    </fieldset></form>}
    {error && <div role="alert" className="rounded-2xl bg-red-50 border border-red-200 p-4 text-sm text-red-800"><p>{error}</p>{conflict && <p className="mt-2">Spesifikasi berubah sejak dibuka. Muat versi terbaru sebelum mengulangi perubahan.</p>}<button type="button" onClick={() => load()} className="underline mt-3">Muat spesifikasi terbaru</button></div>}
  </DialogContent></Dialog>;
}

function SpecFields({ title, value, onChange, id }) {
  const set = (key, field) => onChange({ ...value, [key]: field });
  return <fieldset className="rounded-2xl border border-meow-midnight/10 p-4 min-w-0"><legend className="font-semibold px-1">{title}</legend><div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">{dimensions.map(([key, label]) => <label key={key} className="text-sm block min-w-0"><span className="font-semibold">{label} (mm)</span><input aria-label={title + " " + label + " (mm)"} type="number" min="0.01" step="0.01" inputMode="decimal" value={value[key]} onChange={event => set(key, event.target.value)} className="w-full mt-1 px-3 py-2 rounded-xl bg-meow-bg border border-meow-midnight/10 focus:border-meow-salmon outline-none" data-testid={id + "-" + key} /></label>)}</div><label className="flex items-start gap-2 text-sm mt-4"><input type="checkbox" checked={value.symmetric} onChange={event => set("symmetric", event.target.checked)} /><span>Ukuran kanan/kiri frame ini telah dikonfirmasi simetris untuk perhitungan decentration.</span></label><label className="flex items-start gap-2 text-sm mt-3"><input type="checkbox" checked={value.enabled} onChange={event => set("enabled", event.target.checked)} data-testid={id + "-enabled"} /><span>Aktifkan spesifikasi ini untuk Meowsurement setelah A/B/DBL diperiksa. ED opsional.</span></label><label className="block text-sm mt-4"><span className="font-semibold">Sumber ukuran / catatan pemeriksaan</span><textarea aria-label={title + " Sumber ukuran / catatan pemeriksaan"} value={value.source_note} onChange={event => set("source_note", event.target.value)} rows={2} maxLength={2000} className="w-full mt-1 px-3 py-2 rounded-xl bg-meow-bg border border-meow-midnight/10 focus:border-meow-salmon outline-none" /></label></fieldset>;
}
