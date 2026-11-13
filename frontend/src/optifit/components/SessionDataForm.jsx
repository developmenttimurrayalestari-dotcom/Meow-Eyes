import React, { useState } from "react";
import { ArrowRightLeft, Download, Ruler, Save } from "lucide-react";
import { validateFrame, validatePrescription } from "../domain/workflow";
import { frameDerived, transposePrescription } from "../vision";
import { Button, Field, Help, Notice, asNumber, formatNumber, safeError, todayLocal } from "./ui";
import { invalidateChangedMeasurementContext } from "./measurementContext";

export const PARAMETER_OPTIONS = [
  ["distance_pd", "PD jauh"], ["near_pd", "PD dekat"], ["vertex_right", "Vertex Distance kanan"], ["vertex_left", "Vertex Distance kiri"],
  ["pantoscopic_right", "Pantoscopic kanan"], ["pantoscopic_left", "Pantoscopic kiri"], ["wrap_right", "Wrap kanan"], ["wrap_left", "Wrap kiri"],
];
export const blankSessionData = () => ({
  prescription: { od: { sph: null, cyl: null, axis: null, add: null }, os: { sph: null, cyl: null, axis: null, add: null }, notes: "", source: "professional_prescription" },
  frame: { brand: "", model: "", a: null, b: null, dbl: null, ed: null, symmetric: false, pdReference: "unspecified" },
  captures: [], results: {}, manualMeasurements: {}, requiredParameters: ["distance_pd"], workingDistanceCm: 40,
  mode: "semi_automatic", notes: "", deviceModel: "", consents: { capture: false, retainPhotos: true, thumbnail: false },
});

export default function SessionDataForm({ data: source, examinationDate, onSave, onCancel, editing = false, loadFrameCatalog }) {
  const [data, setData] = useState(() => ({ ...blankSessionData(), ...source, prescription: { ...blankSessionData().prescription, ...source?.prescription }, frame: { ...blankSessionData().frame, ...source?.frame } }));
  const [date, setDate] = useState(examinationDate || todayLocal()); const [reason, setReason] = useState("");
  const [transpose, setTranspose] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const [catalogConsent, setCatalogConsent] = useState(false); const [catalogQuery, setCatalogQuery] = useState(""); const [catalog, setCatalog] = useState([]);
  const setRx = (eye, key, value) => setData(d => ({ ...d, prescription: { ...d.prescription, [eye]: { ...d.prescription[eye], [key]: asNumber(value) } } }));
  const setFrame = (key, value) => setData(d => ({ ...d, frame: { ...d.frame, [key]: value } }));
  const derived = frameDerived({ aMm: data.frame.a, bMm: data.frame.b, dblMm: data.frame.dbl, edMm: data.frame.ed });
  const submit = async event => {
    event.preventDefault(); setError("");
    const checks = [validatePrescription(data.prescription), validateFrame(data.frame)];
    const errors = checks.flatMap(c => c.errors || []);
    if (errors.length) { setError(errors.join(" ")); return; }
    if (!data.requiredParameters.length) { setError("Pilih setidaknya satu parameter yang akan diperiksa."); return; }
    if (editing && !reason.trim()) { setError("Alasan revisi wajib diisi. Data awal tetap disimpan."); return; }
    setBusy(true);
    try { await onSave(editing ? invalidateChangedMeasurementContext(source, data) : data, { examinationDate: date, reason }); }
    catch (err) { setError(safeError(err)); }
    finally { setBusy(false); }
  };
  const findCatalog = async () => {
    if (!catalogConsent) return; setBusy(true); setError("");
    try { const result = await loadFrameCatalog({ query: catalogQuery, confirmed: true }); setCatalog(result?.products || result?.items || (Array.isArray(result) ? result : [])); }
    catch (err) { setError(safeError(err)); } finally { setBusy(false); }
  };
  return <form onSubmit={submit} className="of-form" autoComplete="off">
    <div className="of-grid-two"><Field label="Tanggal pemeriksaan sesi" required><input type="date" value={date} onChange={e => setDate(e.target.value)} disabled={editing} required /></Field><Field label="Model perangkat" hint="Isi model sebenarnya. Browser tidak selalu mengetahui model perangkat."><input value={data.deviceModel || ""} onChange={e => setData(d => ({ ...d, deviceModel: e.target.value }))} placeholder="Contoh: model ponsel yang digunakan" maxLength={160} /></Field></div>
    <section className="of-subcard"><div className="of-section-heading"><div><h3>Resep kacamata</h3><p>Salin dari resep atau hasil pemeriksaan profesional.</p></div><Button variant="quiet" onClick={() => setTranspose(v => !v)}><ArrowRightLeft size={16} />{transpose ? "Tutup transpose" : "Lihat transpose"}</Button></div>
      <Notice>Kamera tidak menentukan SPH, CYL, Axis, atau ADD. Kolom yang belum diketahui dapat disimpan sebagai draft; angka nol adalah nilai yang berbeda dari kolom kosong.</Notice>
      <div className="of-rx-grid">{[["od", "Mata Kanan (OD)"], ["os", "Mata Kiri (OS)"]].map(([eye, title]) => <fieldset key={eye}><legend>{title}</legend><div className="of-grid-two">{[["sph", "SPH", "D"], ["cyl", "CYL", "D"], ["axis", "Axis", "°"], ["add", "ADD", "D"]].map(([key, label, unit]) => <Field key={key} label={`${title} ${label} (${unit})`}><input type="number" inputMode="decimal" step={key === "axis" ? 1 : "0.01"} min={key === "axis" ? 0 : undefined} max={key === "axis" ? 180 : undefined} value={data.prescription[eye]?.[key] ?? ""} onChange={e => setRx(eye, key, e.target.value)} placeholder="Belum dicatat" /></Field>)}</div>{transpose && <Transpose eye={data.prescription[eye]} />}</fieldset>)}</div>
      <Field label="Catatan sumber resep"><textarea rows={2} value={data.prescription.notes || ""} onChange={e => setData(d => ({ ...d, prescription: { ...d.prescription, notes: e.target.value } }))} maxLength={4000} /></Field>
    </section>
    <section className="of-subcard"><div className="of-section-heading"><div><h3>Frame yang dipakai</h3><p>Semua ukuran dalam milimeter. Periksa tulisan atau hasil pembacaan frame secara langsung.</p></div><Ruler size={25} /></div>
      {loadFrameCatalog && <details className="of-import-panel"><summary><Download size={16} />Ambil identitas frame dari katalog</summary><label className="of-check"><input type="checkbox" checked={catalogConsent} onChange={e => setCatalogConsent(e.target.checked)} /><span>Izinkan permintaan katalog Meow Eyes. Foto dan data pasien tetap lokal.</span></label><div className="of-inline-form"><input aria-label="Cari frame katalog" value={catalogQuery} onChange={e => setCatalogQuery(e.target.value)} placeholder="Nama atau merek frame" maxLength={120} /><Button variant="secondary" disabled={!catalogConsent || busy} onClick={findCatalog}>Cari frame</Button></div>{catalog.length > 0 && <Field label="Frame katalog"><select defaultValue="" onChange={e => { const product = catalog.find(p => String(p.id) === e.target.value); if (product) setData(d => ({ ...d, frame: { ...d.frame, productId: product.id, brand: typeof product.brand === "string" ? product.brand : product.brand?.name || "", model: product.name || "" } })); }}><option value="">Pilih frame</option>{catalog.map(product => <option value={product.id} key={product.id}>{product.name}</option>)}</select></Field>}<small>Ukuran A/B/DBL/ED tetap perlu dimasukkan dan diperiksa operator.</small></details>}
      <div className="of-grid-two"><Field label="Merek frame"><input value={data.frame.brand || ""} onChange={e => setFrame("brand", e.target.value)} maxLength={120} /></Field><Field label="Model frame"><input value={data.frame.model || ""} onChange={e => setFrame("model", e.target.value)} maxLength={160} /></Field></div>
      <div className="of-grid-four">{[["a", "A — lebar lens box"], ["b", "B — tinggi lens box"], ["dbl", "DBL — jarak lens box"], ["ed", "ED — diameter efektif (opsional)"]].map(([key, label]) => <Field label={`${label} (mm)`} key={key}><input type="number" step="0.01" inputMode="decimal" min="0.01" value={data.frame[key] ?? ""} onChange={e => setFrame(key, asNumber(e.target.value))} placeholder="Belum diukur" /></Field>)}</div>
      <div className="of-derived"><small>Frame PD = A + DBL</small><strong>{formatNumber(derived.values?.framePdMm ?? derived.framePdMm)}<span> mm</span></strong></div>
      <Help title="Arti A, B, DBL, ED dan Frame PD">A adalah lebar horizontal lens box; B adalah tinggi vertikalnya; DBL adalah jarak antar lens box. ED adalah diameter efektif bentuk lensa, tidak otomatis sama dengan diagonal kotak. Frame PD merupakan data turunan A + DBL.</Help>
      <label className="of-check"><input type="checkbox" checked={!!data.frame.symmetric} onChange={e => setFrame("symmetric", e.target.checked)} /><span>Operator mengonfirmasi frame simetris untuk perhitungan decentration.</span></label>
      <Field label="Referensi monocular PD untuk decentration"><select value={data.frame.pdReference || "unspecified"} onChange={e => setFrame("pdReference", e.target.value)}><option value="unspecified">Belum dikonfirmasi</option><option value="frame_bridge">Garis tengah bridge frame</option><option value="facial_midline">Garis tengah wajah</option></select></Field>
    </section>
    <section className="of-subcard"><h3>Ruang lingkup pengukuran</h3><div className="of-checkbox-grid">{PARAMETER_OPTIONS.map(([key, label]) => <label className="of-check" key={key}><input type="checkbox" checked={data.requiredParameters.includes(key)} onChange={e => setData(d => ({ ...d, requiredParameters: e.target.checked ? [...d.requiredParameters, key] : d.requiredParameters.filter(p => p !== key) }))} /><span>{label}</span></label>)}</div>
      {data.requiredParameters.includes("near_pd") && <Field label="Jarak kerja PD dekat (cm)" required hint="Dicatat bersama near PD; tidak diturunkan dari distance PD."><input type="number" inputMode="decimal" min="1" step="0.1" value={data.workingDistanceCm ?? ""} onChange={e => setData(d => ({ ...d, workingDistanceCm: asNumber(e.target.value) }))} required /></Field>}
      <Field label="Mode pengukuran"><select value={data.mode} onChange={e => setData(d => ({ ...d, mode: e.target.value }))}><option value="semi_automatic">Semi-otomatis — usulan titik dengan konfirmasi operator</option><option value="manual">Manual — semua titik atau alat referensi oleh operator</option><option value="automatic" disabled>Otomatis penuh — belum tersedia tanpa detektor tervalidasi</option></select></Field>
      <Field label="Catatan operator"><textarea rows={3} value={data.notes || ""} onChange={e => setData(d => ({ ...d, notes: e.target.value }))} maxLength={6000} /></Field>
    </section>
    {editing && <><Notice>Perubahan identitas/ukuran frame, referensi PD, atau jarak kerja membatalkan hasil konteks sebelumnya. Ambil foto atau pembacaan baru; data lama tetap tersimpan pada revisinya.</Notice><Field label="Alasan revisi data sesi" required><textarea value={reason} onChange={e => setReason(e.target.value)} required minLength={5} maxLength={1000} placeholder="Jelaskan perubahan. Resep dan data awal tetap disimpan." /></Field></>}
    {error && <Notice tone="danger">{error}</Notice>}
    <div className="of-actions"><Button variant="secondary" onClick={onCancel} disabled={busy}>Batal</Button><Button type="submit" busy={busy}><Save size={17} />{editing ? "Simpan sebagai revisi baru" : "Simpan draft sesi"}</Button></div>
  </form>;
}

function Transpose({ eye }) {
  const result = transposePrescription(eye || {});
  return <div className="of-transpose"><strong>Hasil transpose turunan</strong>{result.valid ? <p>SPH {formatNumber(result.transposed.sph)} · CYL {formatNumber(result.transposed.cyl)} · Axis {formatNumber(result.transposed.axis)}° · ADD {formatNumber(result.transposed.add)}</p> : <p>Isi SPH, CYL, dan Axis yang diperlukan untuk melihat transpose.</p>}<small>Resep asli tetap disimpan dan tidak diubah.</small></div>;
}
