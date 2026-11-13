import React, { useCallback, useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, Eye, LoaderCircle, RefreshCw, Save } from "lucide-react";
import { api } from "../lib/api";
import { localToday, profileFieldLabel, profileFormValues, profileRequestError, profileSavePayload } from "../lib/customerProfile";
import { safeMeowsurementReturn } from "../lib/authReturn";

const inputClass = "w-full mt-1 px-3 py-2.5 rounded-xl border border-meow-midnight/15 bg-meow-bg outline-none focus:border-meow-salmon focus:bg-white";

function Field({ label, hint, children }) {
  return <label className="block text-sm min-w-0"><span className="font-semibold">{label}</span>{children}{hint && <small className="block mt-1 text-meow-gray leading-relaxed">{hint}</small>}</label>;
}

export default function CustomerProfileForm({ userId, onSaved, returnTo }) {
  const [form, setForm] = useState(() => profileFormValues());
  const [version, setVersion] = useState(0);
  const [readiness, setReadiness] = useState({ ready: false, missing_fields: [] });
  const [loading, setLoading] = useState(true), [loaded, setLoaded] = useState(false), [saving, setSaving] = useState(false);
  const [error, setError] = useState(""), [notice, setNotice] = useState("");
  const [dirty, setDirty] = useState(false), [conflict, setConflict] = useState(false);
  const load = useCallback(async signal => {
    if (!userId) return;
    setLoading(true); setLoaded(false); setError("");
    try {
      const { data } = await api.get("/customer/profile", { signal, withCredentials: true });
      if (signal?.aborted) return;
      setForm(profileFormValues(data.profile)); setVersion(data.profile?.version ?? data.version ?? 0);
      setReadiness({ ready: data.ready === true, missing_fields: data.missing_fields || [] });
      setDirty(false); setConflict(false); setLoaded(true);
    } catch (err) { if (!signal?.aborted) setError(profileRequestError(err, "Profil belum dapat dimuat. Coba kembali.")); }
    finally { if (!signal?.aborted) setLoading(false); }
  }, [userId]);
  useEffect(() => { const controller = new AbortController(); void load(controller.signal); return () => controller.abort(); }, [load]);
  const update = (key, value) => { setForm(previous => ({ ...previous, [key]: value })); setDirty(true); setNotice(""); };
  const updateRx = (eye, field, value) => {
    setForm(previous => ({ ...previous, prescription: { ...previous.prescription, [eye]: { ...previous.prescription[eye], [field]: value } } }));
    setDirty(true); setNotice("");
  };
  const updatePrescription = (field, value) => {
    setForm(previous => ({ ...previous, prescription: { ...previous.prescription, [field]: value } }));
    setDirty(true); setNotice("");
  };
  const submit = async event => {
    event.preventDefault();
    if (!loaded || conflict || saving) return;
    setError(""); setNotice("");
    let payload;
    try { payload = profileSavePayload(form, version); }
    catch (err) { setError(err.message); return; }
    setSaving(true);
    try {
      const { data } = await api.put("/customer/profile", payload, { withCredentials: true });
      setForm(profileFormValues(data.profile)); setVersion(data.profile?.version ?? data.version ?? 0);
      setReadiness({ ready: data.ready === true, missing_fields: data.missing_fields || [] });
      setDirty(false); setConflict(false);
      setNotice(data.ready ? "Profil dan resep tersimpan. Data ini akan terisi otomatis saat membuka Meowsurement." : "Profil tersimpan. Lengkapi bagian yang ditandai sebelum menggunakan Meowsurement.");
      if (onSaved) await onSaved();
    } catch (err) { setConflict(err?.response?.status === 409); setError(profileRequestError(err)); }
    finally { setSaving(false); }
  };
  const destination = safeMeowsurementReturn(returnTo);
  return <section className="mt-6 bg-white rounded-3xl p-5 md:p-7 border border-meow-midnight/10" aria-labelledby="profile-health-heading" data-testid="customer-profile-form-panel">
    <div className="flex items-start gap-3 mb-5"><span className="p-3 bg-meow-mint/15 rounded-2xl text-meow-midnight"><Eye className="w-6 h-6" /></span><div><h2 id="profile-health-heading" className="font-heading text-2xl font-black">Profil & resep kacamata</h2><p className="text-sm text-meow-gray mt-1">Meowsurement memakai data akun Anda dan spesifikasi frame yang dikelola admin Meow Eyes.</p></div></div>
    {!readiness.ready && readiness.missing_fields.length > 0 && <div className="bg-meow-amber/15 rounded-2xl p-4 text-sm" data-testid="profile-missing-fields"><p className="font-bold">Lengkapi data berikut untuk Meowsurement:</p><ul className="list-disc pl-5 mt-2 space-y-1">{readiness.missing_fields.map((field, index) => <li key={String(field) + index}>{profileFieldLabel(typeof field === "string" ? field : field.field || field.label || "")}</li>)}</ul></div>}
    {loading ? <p className="flex items-center gap-2 text-meow-gray" role="status"><LoaderCircle className="w-5 h-5 animate-spin" />Memuat profil…</p> : loaded && <form onSubmit={submit} data-testid="customer-profile-form"><fieldset disabled={saving} className="space-y-5 min-w-0">
      <div className="grid sm:grid-cols-2 gap-4">
        <Field label="Nama lengkap"><input aria-label="Nama lengkap" value={form.name} onChange={event => update("name", event.target.value)} maxLength={255} className={inputClass} autoComplete="name" required /></Field>
        <Field label="Email akun" hint="Email mengikuti akun Meow Eyes yang sedang digunakan."><input aria-label="Email akun" value={form.email} readOnly className={inputClass + " opacity-70"} type="email" /></Field>
        <Field label="Nomor telepon" hint="Wajib untuk menggunakan Meowsurement."><input aria-label="Nomor telepon" value={form.phone} onChange={event => update("phone", event.target.value)} type="tel" maxLength={32} autoComplete="tel" className={inputClass} /></Field>
        <Field label="Tanggal lahir" hint="Wajib untuk menggunakan Meowsurement."><input aria-label="Tanggal lahir" value={form.birth_date} onChange={event => update("birth_date", event.target.value)} type="date" max={localToday()} autoComplete="bday" className={inputClass} /></Field>
        <Field label="Jenis kelamin (opsional)"><select aria-label="Jenis kelamin (opsional)" value={form.gender} onChange={event => update("gender", event.target.value)} className={inputClass}><option value="">Belum diisi</option><option value="male">Laki-laki</option><option value="female">Perempuan</option><option value="unspecified">Tidak ingin menyebutkan</option></select></Field>
        <Field label="Alamat profil (opsional)" hint="Alamat pengiriman tetap dikelola pada menu Alamat."><textarea aria-label="Alamat profil (opsional)" value={form.address} onChange={event => update("address", event.target.value)} maxLength={2000} rows={2} className={inputClass} /></Field>
      </div>
      <div id="resep" className="border-t border-meow-midnight/10 pt-5">
        <h3 className="font-heading text-xl font-black">Resep kacamata saya</h3>
        <p className="text-sm text-meow-gray mt-2 mb-4">Salin dari resep atau pemeriksaan tenaga optik. Kamera Meowsurement tidak menentukan SPH, CYL, AXIS, atau ADD. Isi angka 0 hanya jika memang tertulis plano/tanpa silinder; kolom kosong berarti belum diketahui.</p>
        <Field label="Tanggal resep / pemeriksaan" hint="Tanggal dari resep yang Anda masukkan."><input aria-label="Tanggal resep / pemeriksaan" type="date" value={form.prescription.date} onChange={event => updatePrescription("date", event.target.value)} max={localToday()} className={inputClass + " sm:max-w-xs"} /></Field>
        <div className="grid md:grid-cols-2 gap-4 mt-4">
          {[["od", "Mata kanan (OD)"], ["os", "Mata kiri (OS)"]].map(([eye, title]) => <fieldset key={eye} className="rounded-2xl border border-meow-midnight/10 p-4 min-w-0"><legend className="font-bold px-1">{title}</legend><div className="grid grid-cols-2 gap-3">{[["sph", "SPH (D)"], ["cyl", "CYL (D)"], ["axis", "AXIS (°)"], ["add", "ADD (D), opsional"]].map(([field, label]) => <Field key={field} label={label}><input aria-label={title + " " + label} type="number" inputMode="decimal" step={field === "axis" ? "1" : "0.01"} min={field === "axis" ? 0 : undefined} max={field === "axis" ? 180 : undefined} value={form.prescription[eye][field]} onChange={event => updateRx(eye, field, event.target.value)} placeholder="Belum diisi" className={inputClass} /></Field>)}</div><p className="text-xs text-meow-gray mt-3">SPH dan CYL diperlukan untuk Meowsurement. Jika CYL bukan nol, AXIS harus 1–180°.</p></fieldset>)}
        </div>
        <fieldset className="mt-4 rounded-2xl border border-meow-midnight/10 p-4"><legend className="font-semibold px-1">PD pada resep (opsional)</legend><p className="text-sm text-meow-gray mb-3">Isi hanya jika tercantum pada resep. Data ini disimpan sebagai referensi; hasil pengukuran Meowsurement diperiksa secara terpisah.</p><div className="grid sm:grid-cols-3 gap-3">{[["pd_total", "PD total (mm)"], ["pd_right", "PD kanan (mm)"], ["pd_left", "PD kiri (mm)"]].map(([key, label]) => <Field key={key} label={label}><input aria-label={label} type="number" inputMode="decimal" min="0.01" max="999.99" step="0.01" value={form.prescription[key]} onChange={event => updatePrescription(key, event.target.value)} placeholder="Belum diisi" className={inputClass} /></Field>)}</div></fieldset>
        <div className="mt-4"><Field label="Catatan resep (opsional)"><textarea aria-label="Catatan resep (opsional)" value={form.prescription.notes} onChange={event => updatePrescription("notes", event.target.value)} rows={2} maxLength={4000} className={inputClass} /></Field></div>
      </div>
      {notice && <p className="rounded-2xl bg-meow-mint/15 p-4 text-sm flex items-start gap-2" role="status"><CheckCircle2 className="w-5 h-5 shrink-0" />{notice}</p>}
      
      {dirty && <p className="text-sm text-meow-gray">Ada perubahan yang belum disimpan. Simpan terlebih dahulu agar Meowsurement memakai profil dan resep terbaru.</p>}
      <div className="flex flex-wrap items-center gap-3">
        <button type="submit" disabled={saving || conflict} className="btn-primary inline-flex items-center gap-2 disabled:opacity-50" data-testid="save-customer-profile">{saving ? <LoaderCircle className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}Simpan profil & resep</button>
        {readiness.ready && !dirty && !saving && !conflict ? <a href={destination} className="btn-secondary inline-flex items-center gap-2" data-testid="continue-meowsurement">Lanjut ke Meowsurement<ArrowRight className="w-4 h-4" /></a> : <button type="button" disabled className="btn-secondary opacity-50" data-testid="continue-meowsurement-disabled">Lengkapi & simpan untuk lanjut</button>}
      </div>
    </fieldset></form>}
    {error && <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-800 text-sm" role="alert"><p>{error}</p>{conflict && <p className="mt-2">Profil telah berubah pada sesi lain. Muat data terbaru sebelum menyimpan ulang; perubahan yang belum disimpan akan diganti.</p>}<button type="button" onClick={() => load()} className="underline mt-3 inline-flex items-center gap-1"><RefreshCw className="w-4 h-4" />Muat profil terbaru</button></div>}
  </section>;
}
