import FormField from "./FormField";
import React, { useEffect, useRef, useState } from "react";
import { CheckCircle2, FileImage, Upload, Save, X, UserRound } from "lucide-react";
import { toast } from "sonner";
import { api, apiError, formatIDR } from "../lib/api";

const fields = ["od_sph", "od_cyl", "od_axis", "od_add", "os_sph", "os_cyl", "os_axis", "os_add", "pd_total", "pd_right", "pd_left"];
const EXISTING_LENS = '__existing_lens__';
const selectedLens = (item) => item.lens_index?.id || (item.lens_product ? EXISTING_LENS : '');
export const prescriptionValues = (source = {}) => ({
  ...Object.fromEntries(fields.map((key) => [key, source?.[key] ?? (key === "pd_total" ? source?.pd : "") ?? ""])),
  notes: source?.notes || "", attachment_upload_id: source?.attachment_upload_id || null
});

export const profilePrescriptionValues = (source) => prescriptionValues({
  ...Object.fromEntries(['od', 'os'].flatMap((eye) => ['sph', 'cyl', 'axis', 'add'].map((key) => [`${eye}_${key}`, source?.[eye]?.[key] ?? '']))),
  pd_total: source?.pd_total, pd_right: source?.pd_right, pd_left: source?.pd_left,
  notes: source?.notes || ''
});
const hasMeasurements = (value) => fields.some((key) => value[key] !== '' && value[key] != null);
const measurementText = (value) => value === '' || value == null ? '—' : String(value);

function PrescriptionSummary({ value, onClear, disabled }) {

  return <div className="rounded-xl bg-meow-bg p-3 text-xs space-y-3" data-testid="prescription-summary">
    <p className="font-bold">{"Ukuran resep untuk item ini"}</p>
    <div className="grid grid-cols-2 gap-3">{[['od', 'Kanan (OD)'], ['os', 'Kiri (OS)']].map(([eye, label]) => <div key={eye}>
      <p className="font-semibold mb-1">{label}</p>
      <dl className="grid grid-cols-2 gap-x-2 gap-y-1">{['sph', 'cyl', 'axis', 'add'].map((key) => <React.Fragment key={key}><dt>{key.toUpperCase()}</dt><dd>{measurementText(value[`${eye}_${key}`])}</dd></React.Fragment>)}</dl>
    </div>)}</div>
    {value.pd_total !== '' && value.pd_total != null && <p>{"PD total: "}{value.pd_total}{" mm"}</p>}
    {value.pd_right !== '' && value.pd_right != null && <p>{"PD kanan: "}{value.pd_right}{" mm · PD kiri: "}{value.pd_left}{" mm"}</p>}
    <button type="button" disabled={disabled} onClick={onClear} className="underline disabled:opacity-50">{"Gunakan foto/catatan saja (hapus ukuran)"}</button>
  </div>;
}

export function PrescriptionFields({ value, onChange, idPrefix, disabled = false, showMeasurements = true }) {

  const [pdMode, setPdMode] = useState(value.pd_right !== "" && value.pd_right != null ? "pair" : "total");
  const set = (key, val) => onChange({ ...value, [key]: val });
  return <fieldset disabled={disabled} className="space-y-4 min-w-0 max-w-full">
    {showMeasurements && <>
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-separate border-spacing-1">
        <caption className="sr-only">{"Resep kacamata untuk mata kanan dan kiri"}</caption>
        <thead><tr><th className="text-left font-semibold">{"Mata"}</th>{["SPH", "CYL", "AXIS", "ADD"].map((name) => <th key={name} className="text-xs font-bold text-meow-gray">{name}</th>)}</tr></thead>
        <tbody>{[["od", "Kanan (OD)"], ["os", "Kiri (OS)"]].map(([eye, label]) => <tr key={eye}>
          <th scope="row" className="text-left font-semibold text-xs whitespace-nowrap pr-2">{label}</th>
          {["sph", "cyl", "axis", "add"].map((measure) => <td key={measure}>
            <FormField label={measure.toUpperCase()}><input type="number" inputMode="decimal" step={measure === "axis" ? "1" : "0.01"}
                  min={measure === "axis" ? 0 : -999.99} max={measure === "axis" ? 180 : 999.99}
                  id={`${idPrefix}-${eye}-${measure}`} aria-label={`${label} ${measure.toUpperCase()}`} placeholder={measure === "axis" ? "0–180" : "0.00"}
                  value={value[`${eye}_${measure}`]} onChange={(event) => set(`${eye}_${measure}`, event.target.value)}
                  className="w-full min-w-16 px-2 py-2 rounded-lg bg-meow-bg border border-meow-midnight/10 outline-none focus:border-meow-salmon" /></FormField>
          </td>)}
        </tr>)}</tbody>
      </table>
    </div>
    <p className="sm:hidden text-xs text-meow-gray">{"Geser tabel ke samping untuk melihat semua kolom resep."}</p>
    <div>
      <div className="flex flex-wrap gap-3 items-center text-xs mb-2">
        <span className="font-bold">{"PD (mm)"}</span>
        {[["total", "PD total"], ["pair", "PD per mata"]].map(([mode, label]) => <label key={mode} className="inline-flex items-center gap-1">
          <input type="radio" name={`${idPrefix}-pd-mode`} checked={pdMode === mode} onChange={() => {setPdMode(mode);onChange({ ...value, pd_total: "", pd_left: "", pd_right: "" });}} /> {label}
        </label>)}
      </div>
      <div className="grid grid-cols-2 gap-2 max-w-sm">
        {(pdMode === "total" ? [["pd_total", "PD total"]] : [["pd_right", "PD kanan"], ["pd_left", "PD kiri"]]).map(([key, label]) => <label key={key} className="text-xs font-semibold">
          {label}{" (mm)"}
            <input type="number" min="0.01" max="999.99" step="0.01" inputMode="decimal" value={value[key]} onChange={(event) => set(key, event.target.value)}
            className="block w-full px-3 py-2 mt-1 rounded-xl bg-meow-bg border border-meow-midnight/10 outline-none focus:border-meow-salmon" />
        </label>)}
      </div>
    </div>
    </>}
    <label className="block text-xs font-semibold">{"Catatan resep (opsional)"}
      <textarea value={value.notes} maxLength={10000} rows={2} onChange={(event) => set("notes", event.target.value)}
      className="block w-full mt-1 px-3 py-2 rounded-xl bg-meow-bg border border-meow-midnight/10 outline-none focus:border-meow-salmon" />
    </label>
  </fieldset>;
}

export default function PrescriptionForm({ item, onDirtyChange, onSaved, disabled = false, showMeasurements = true, selectLens = false, allowProfile = false }) {

  const [value, setValue] = useState(() => prescriptionValues(item.prescription));
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const profileRequest = useRef(null);
  useEffect(() => () => profileRequest.current?.abort(), []);
  const [error, setError] = useState("");
  const canSelectLens = selectLens && ['frame', 'package'].includes(item.product?.product_type);
  const isPackage = item.product?.product_type === 'package';
  const isFrame = item.product?.product_type === 'frame';
  const [lensIndexId, setLensIndexId] = useState(() => selectedLens(item));
  const saved = useRef({ value: prescriptionValues(item.prescription), lens: selectedLens(item) });
  const [lensOptions, setLensOptions] = useState(null);
  const [lensError, setLensError] = useState('');
  useEffect(() => {
    if (!canSelectLens) return undefined;
    const controller = new AbortController();
    setLensOptions(null);setLensError('');
    api.get(`/cart/${item.id}/lens-options`, { signal: controller.signal }).
    then(({ data }) => {if (!controller.signal.aborted) setLensOptions(data);}).
    catch((err) => {if (!controller.signal.aborted) setLensError(apiError(err, 'Pilihan lensa belum dapat dimuat. Silakan muat ulang halaman.'));});
    return () => controller.abort();
  }, [item.id, canSelectLens]);
  const [filename, setFilename] = useState(item.prescription?.attachment_upload_id ? "Foto resep tersimpan" : "");
  const edit = (next, lens = lensIndexId) => {
    const changed = JSON.stringify(next) !== JSON.stringify(saved.current.value) || canSelectLens && lens !== saved.current.lens;
    setValue(next);setDirty(changed);setError('');onDirtyChange?.(item.id, changed);
  };
  const useProfile = async () => {
    if (profileLoading || uploading || saving || disabled) return;
    setProfileLoading(true);setError('');
    onDirtyChange?.(item.id, true);
    const controller = new AbortController();
    profileRequest.current = controller;
    try {
      const { data } = await api.get('/customer/profile', { signal: controller.signal });
      if (controller.signal.aborted) return;
      const prescription = data?.profile?.prescription;
      if (!prescription?.id) {
        setError('Belum ada resep tersimpan di profil. Isi dan simpan resep pada halaman Profil terlebih dahulu.');
        onDirtyChange?.(item.id, dirty);
        return;
      }
      edit(profilePrescriptionValues(prescription));
      setFilename('');
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(apiError(err, 'Resep profil belum dapat dimuat. Silakan coba kembali.'));
      onDirtyChange?.(item.id, dirty);
    } finally {if (!controller.signal.aborted) setProfileLoading(false);}
  };
  const upload = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || profileLoading || saving || uploading || disabled) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size > 8 * 1024 * 1024) {
      setError("Gunakan foto JPG, PNG, atau WebP berukuran maksimal 8 MB.");return;
    }
    setUploading(true);
    onDirtyChange?.(item.id, true);
    setError("");
    try {
      const body = new FormData();body.append("file", file);
      const { data } = await api.post("/uploads/prescription", body);
      edit({ ...value, attachment_upload_id: data.id });
      setFilename(file.name);
    } catch (err) {
      setError(apiError(err, "Foto resep belum berhasil diunggah."));
      onDirtyChange?.(item.id, dirty);
    } finally {setUploading(false);}
  };
  const save = async (event) => {
    event.preventDefault();
    if (saving || uploading || profileLoading || disabled) return;
    if (showMeasurements && value.pd_right !== "" !== (value.pd_left !== "")) {setError("Isi PD kanan dan kiri, atau pilih PD total.");return;}
    setSaving(true);setError("");
    try {
      const payload = { ...value, ...Object.fromEntries(fields.map((key) => [key, value[key] === "" ? null : Number(value[key])])) };
      if (canSelectLens) {
        payload.lens_index_id = lensIndexId && lensIndexId !== EXISTING_LENS ? lensIndexId : null;
        if (isFrame && !lensIndexId && item.lens_product) payload.frame_only = true;
      }
      const { data } = await api.patch(`/cart/${item.id}/prescription`, payload);
      const next = prescriptionValues(data.prescription);
      const lens = data.cart_item ? selectedLens(data.cart_item) : lensIndexId;
      saved.current = { value: next, lens };
      setValue(next);setLensIndexId(lens);
      setDirty(false);
      onDirtyChange?.(item.id, false);
      onSaved?.(item.id, data.prescription, data.cart_item);
      toast.success("Resep tersimpan untuk produk ini");
    } catch (err) {setError(apiError(err, "Resep belum berhasil disimpan."));} finally
    {setSaving(false);}
  };
  const download = async () => {
    try {
      const { data } = await api.get(`/prescriptions/uploads/${value.attachment_upload_id}`, { responseType: "blob" });
      const url = URL.createObjectURL(data);
      const anchor = document.createElement("a");anchor.href = url;anchor.download = "resep-kacamata";anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch {toast.error("Lampiran belum dapat diunduh.");}
  };
  return <form onSubmit={save} className="border border-meow-midnight/10 rounded-2xl p-4 space-y-3" data-testid={`prescription-${item.id}`}>
    <div>
      <p className="font-bold text-sm">{item.product?.["name"]}</p>
      <span className="conveythis-no-translate notranslate" translate="no" data-conveythis-private="">{item.variant?.sku && <p className="text-xs text-meow-gray">{"SKU: "}{item.variant.sku}</p>}</span>
      {item.lens_product && <p className="text-xs text-meow-gray">+ {item.lens_product?.["name"]}</p>}
      {item.quantity > 1 && <p className="text-xs text-meow-gray mt-1">{"Satu resep berlaku untuk seluruh "}{item.quantity}{" produk pada baris ini."}</p>}
    </div>
    {canSelectLens && <div className="space-y-2">
      <label htmlFor={`rx-lens-${item.id}`} className="block text-xs font-semibold">{"Lens Index (opsional)"}</label>
      <select id={`rx-lens-${item.id}`} data-testid={`rx-lens-${item.id}`} value={lensIndexId}
      disabled={disabled || saving || uploading || profileLoading || !lensOptions}
      onChange={(event) => {const lens = event.target.value;setLensIndexId(lens);edit(value, lens);}}
      className="w-full px-3 py-2 rounded-xl bg-meow-bg border border-meow-midnight/10 text-sm">
        <option value="">{lensOptions ? isFrame ? "Beli frame saja (tanpa lensa)" : "Tanpa pilihan Lens Index" : "Memuat pilihan lensa…"}</option>
        {isFrame && item.lens_product && <option value={EXISTING_LENS}>{`${item.lens_product?.["name"]} — tanpa tambahan Lens Index`}</option>}
        {lensIndexId && lensIndexId !== EXISTING_LENS && lensOptions && !lensOptions.items?.some((index) => index.id === lensIndexId) && <option value={lensIndexId} disabled>{"Pilihan lama tidak tersedia — pilih kembali"}</option>}
        {/* Native options need a single text expression; development visual editing wraps mixed text in spans. */}
        {(lensOptions?.items || []).map((index) => <option key={index.id} value={index.id} translate="no" data-conveythis-private="">{`${index?.["name"]} — ${isPackage ? 'Termasuk harga paket' : `+${formatIDR(index.additional_price)} / produk`}`}</option>)}
      </select>
      <p className="text-xs text-meow-gray">{isPackage ? `Pilihan mengikuti Jenis Lensa paket${
        lensOptions?.lens_types?.length ? `: ${lensOptions.lens_types.map((type) => type.name).join(', ')}` : ''}. Harga lensa sudah termasuk dalam harga paket.` : "Beli frame saja: lensa dan resep boleh dikosongkan. Anda bisa langsung checkout tanpa Simpan Resep. Jika menambah atau menghapus lensa, simpan perubahan untuk memperbarui harga."
        }</p>
      {lensOptions && !lensOptions.items?.length && <p className="text-xs text-amber-700">{"Pilihan lensa untuk produk ini belum tersedia. Hubungi toko untuk bantuan."}</p>}
      {lensError && <p role="alert" className="text-xs text-red-600">{lensError}</p>}
    </div>}
    {allowProfile && <div className="rounded-xl border border-meow-midnight/10 p-3 space-y-2 text-xs">
      <p className="font-semibold">{"Pilihan resep"}</p>
      <p className="text-meow-gray">{"Gunakan resep yang sudah Anda simpan di Profil, atau lampirkan foto resep di bawah. Data profil mengganti ukuran dan catatan item ini; foto lama dilepas."}</p>
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" disabled={disabled || saving || uploading || profileLoading} onClick={useProfile} className="btn-secondary text-xs inline-flex items-center gap-2 disabled:opacity-50" data-testid={`use-profile-prescription-${item.id}`}><UserRound className="h-4 w-4" />{profileLoading ? "Memuat resep profil..." : "Gunakan resep profil"}</button>
        <a href="/profile#resep" target="_blank" rel="noopener noreferrer" className="underline">{"Buka Profil"}</a>
      </div>
      <p className="text-meow-gray">{"Setelah memilih resep, klik Simpan Resep untuk menerapkannya pada item ini."}</p>
    </div>}
    {!showMeasurements && hasMeasurements(value) && <PrescriptionSummary value={value} disabled={disabled || saving || uploading || profileLoading} onClear={() => edit({ ...value, ...Object.fromEntries(fields.map((key) => [key, ''])) })} />}
    <PrescriptionFields value={value} onChange={edit} idPrefix={`rx-${item.id}`} disabled={disabled || saving || uploading || profileLoading} showMeasurements={showMeasurements} />
    <div className="rounded-xl border border-dashed border-meow-midnight/20 p-3 text-xs space-y-2">
      <label className={`inline-flex items-center gap-2 font-bold text-meow-salmon cursor-pointer ${uploading ? "opacity-60" : ""}`}>
        <Upload className="h-4 w-4" /> {uploading ? "Mengunggah foto…" : "Lampirkan foto resep (opsional)"}
        <input type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} disabled={disabled || uploading || saving || profileLoading} className="sr-only" data-testid={`rx-upload-${item.id}`} />
      </label>
      <p className="text-meow-gray">{"JPG, PNG, WebP · maksimal 8 MB. Foto tersimpan privat untuk pemrosesan pesanan Anda."}</p>
      {value.attachment_upload_id && <div className="flex items-center gap-2">
        <FileImage className="h-4 w-4 shrink-0" /><button type="button" onClick={download} className="underline break-all text-left">{filename || "Foto resep tersimpan"}</button>
        <button type="button" aria-label={"Hapus lampiran dari resep"} disabled={disabled || saving || uploading || profileLoading} onClick={() => {edit({ ...value, attachment_upload_id: null });setFilename("");}} className="ml-auto p-1"><X className="h-4 w-4" /></button>
      </div>}
    </div>
    {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
    <div className="flex flex-wrap items-center justify-between gap-2">
      <p className={`text-xs ${dirty ? "text-amber-700" : "text-meow-gray"}`}>{dirty ? "Perubahan resep belum disimpan." : item.prescription ? "Resep tersimpan." : item.lens_index ? "Pilihan lensa tersimpan." : showMeasurements ? "Isi sesuai resep Anda. Kolom yang tidak tercantum boleh dikosongkan." : "Lampirkan foto resep dan tambahkan catatan jika diperlukan."}</p>
      <button type="submit" disabled={disabled || saving || uploading || profileLoading || !dirty} className="inline-flex items-center gap-1.5 rounded-full bg-meow-midnight text-white text-xs font-bold px-4 py-2 disabled:opacity-40">
        {dirty ? <Save className="h-3.5 w-3.5" /> : <CheckCircle2 className="h-3.5 w-3.5" />}{saving ? "Menyimpan…" : "Simpan Resep"}
      </button>
    </div>
  </form>;
}
