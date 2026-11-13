import React, { useState } from "react";
import { CheckCircle2, ClipboardCheck, Download, FileCheck2, FileOutput, Plus, Ruler, Send } from "lucide-react";
import { workspace as vault } from "../storage/workspace";
import { collectMeasurements, evaluateReview, evaluateSubmission, PARAMETER_LABELS, QUALITY_NOTICE, resultQuality, STATUS_LABELS } from "../domain/workflow";
import { aggregateMeasurements, assessQuality, frameDerived, recordManualMeasurement } from "../vision";
import { downloadReport, generateReport, printReport } from "../reports";
import { Button, Field, Help, Modal, Notice, StatusBadge, asNumber, formatNumber, readableDate, safeError } from "./ui";
import { measurementContext } from "./measurementContext";
import { measurementType } from '../domain/customerFlow';

export function ResultsPanel({ state, patient, session, revision, data, actor, onSave, readOnly = false, canEdit = actor.role !== 'reviewer', customerMode = false }) {
  const [manual, setManual] = useState(false); const [review, setReview] = useState(false); const [exportOpen, setExportOpen] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const results = collectMeasurements(data); const policy = evaluateSubmission(data, { session, settings: state.settings });
  const required = data.requiredParameters?.length ? data.requiredParameters : ["distance_pd"];
  const pd = results.distance_pd?.valid ? results.distance_pd.values : {};
  const frame = data.frame || {};
  const derived = frameDerived({ aMm: frame.a, bMm: frame.b, dblMm: frame.dbl, edMm: frame.ed, rightPdMm: frame.symmetric ? pd.rightMm : null, leftPdMm: frame.symmetric ? pd.leftMm : null, pdReference: frame.pdReference, asymmetryThresholdMm: state.settings.asymmetryWarningMm });
  const submit = async () => { setBusy(true); setError(""); try { await vault.submitSession(session.id, { expectedRevisionId: revision.id }); } catch (err) { setError(safeError(err)); } finally { setBusy(false); } };
  const reviewRows = state.reviews.filter(r => r.sessionId === session.id && (!r.revisionId || r.revisionId === revision.id));
  return <>
    <section className="of-card"><div className="of-section-heading"><div><h2>Hasil fitting</h2><p>Versi yang dipilih: {readableDate(revision.createdAt)} · {required.length} parameter dalam lingkup</p></div><StatusBadge status={readOnly ? "draft" : session.status} labels={readOnly ? { draft: "Revisi historis" } : STATUS_LABELS} /></div>
      <Notice>{QUALITY_NOTICE}</Notice>
      <div className="of-result-grid">{Object.entries(PARAMETER_LABELS).filter(([key]) => !customerMode || required.includes(key)).map(([key, label]) => <MeasurementCard key={key} result={results[key]} parameter={key} label={label} required={required.includes(key)} />)}</div>
      {!readOnly && canEdit && <Button variant="secondary" onClick={() => setManual(true)}><Plus size={18} />Catat hasil alat / metode referensi</Button>}
    </section>
    <div className="of-grid-two"><section className="of-card"><div className="of-section-heading"><h2>Frame & decentration</h2><Ruler size={24} /></div><div className="of-metric-row"><span>Frame PD</span><strong>{formatNumber(derived.values?.framePdMm)} mm</strong></div>{[["A", frame.a], ["B", frame.b], ["DBL", frame.dbl], ["ED", frame.ed]].map(([name, value]) => <div className="of-metric-row" key={name}><span>{name}</span><strong>{formatNumber(value)} mm</strong></div>)}<hr />{[["Decentration kanan", derived.values?.rightDecentrationMm], ["Decentration kiri", derived.values?.leftDecentrationMm], ["Total decentration", derived.values?.totalDecentrationMm]].map(([name, value]) => <div className="of-metric-row" key={name}><span>{name}</span><strong>{value == null ? "Belum dihitung" : `${formatNumber(value)} mm`}</strong></div>)}<Help title="Dasar perhitungan decentration">Untuk frame simetris: (A + DBL) / 2 − monocular PD masing-masing mata. Positif berarti ke nasal. Monocular PD harus memakai referensi bridge yang sama. Nilai tidak diperoleh dengan membagi binocular PD secara rata.</Help>{!frame.symmetric && <p className="of-small of-muted">Konfirmasi frame simetris diperlukan sebelum menghitung decentration.</p>}{(derived.warnings || []).map(text => <Notice tone="warning" key={text}>{text}</Notice>)}</section>
      <section className="of-card"><h2>Resep tersimpan</h2><p className="of-muted">Berasal dari resep profesional, bukan kamera.</p>{[["od", "Mata Kanan (OD)"], ["os", "Mata Kiri (OS)"]].map(([eye, title]) => <div className="of-rx-summary" key={eye}><strong>{title}</strong><div className="of-grid-four">{["sph", "cyl", "axis", "add"].map(key => <span key={key}><small>{key.toUpperCase()}</small><b>{data.prescription?.[eye]?.[key] == null ? "—" : formatNumber(data.prescription[eye][key])}</b></span>)}</div></div>)}<p>{data.prescription?.notes || "Tidak ada catatan resep tambahan."}</p><h3>{customerMode ? 'Catatan Anda' : 'Catatan operator'}</h3><p className="of-prewrap">{data.notes || "Tidak ada catatan tambahan."}</p></section></div>
    <section className="of-card"><div className="of-section-heading"><h2>Review & laporan</h2><ClipboardCheck size={25} /></div>
      {!policy.valid && <Notice tone="warning"><strong>Draft belum dapat diajukan:</strong><ul>{policy.errors.map((message, index) => <li key={`${index}-${message}`}>{message}</li>)}</ul></Notice>}
      {policy.warnings.map(message => <Notice key={message} tone="warning">{message}</Notice>)}
      {reviewRows.map(row => <div className="of-review-history" key={row.id}><strong>{row.reviewerName || state.users.find(u => u.id === row.reviewerId)?.displayName || "Reviewer"}</strong><StatusBadge status={row.decision} labels={STATUS_LABELS} /><small>{readableDate(row.createdAt)}</small><p>{row.note}</p>{row.evidence?.referenceInstrument && <small>Referensi: {row.evidence.referenceInstrument} · Protokol {row.evidence.protocolId}</small>}</div>)}
      {error && <Notice tone="danger">{error}</Notice>}
      <div className="of-actions of-actions-start">{!readOnly && canEdit && <Button onClick={submit} busy={busy} disabled={!policy.valid || ["pending_review", "needs_verification", "approved"].includes(session.status)}><Send size={17} />Ajukan review</Button>}{!readOnly && !customerMode && ["admin", "reviewer"].includes(actor.role) && ["pending_review", "needs_verification"].includes(session.status) && <Button variant="secondary" onClick={() => setReview(true)}><FileCheck2 size={18} />Periksa & beri keputusan</Button>}<Button variant="secondary" onClick={() => setExportOpen(true)}><FileOutput size={18} />Ekspor / cetak laporan</Button></div>
    </section>
    {manual && <ManualMeasurementDialog customerMode={customerMode} data={data} onClose={() => setManual(false)} onSave={async (next, reason) => { await onSave(next, reason); setManual(false); }} />}
    {review && <ReviewDialog session={session} revision={revision} actor={actor} settings={state.settings} onClose={() => setReview(false)} />}
    {exportOpen && <ExportDialog state={state} patient={patient} session={session} revision={revision} data={data} onClose={() => setExportOpen(false)} />}
  </>;
}

function MeasurementCard({ result, parameter, label, required }) {
  const q = resultQuality(result); const v = result?.values || {}; const pd = parameter.endsWith("_pd");
  const pantoMedians = parameter.startsWith("pantoscopic") && result?.aggregationMethod === "componentwise_median";
  const value = pd ? v.binocularMm : parameter.startsWith("vertex_") ? v.vertexMm ?? v.valueMm : v.correctedDeg ?? v.angleDeg ?? (parameter.endsWith("right") ? v.rightDeg : v.leftDeg);
  return <article className={`of-measurement ${result?.valid ? "" : "of-measurement-empty"}`}>
    <div className="of-measurement-top"><h3>{label}</h3>{required && <span className="of-scope">Dalam lingkup</span>}</div>
    {pantoMedians && result?.valid && <small className="of-muted">Median sudut terkoreksi</small>}
    <strong className="of-measurement-value">{result?.valid ? formatNumber(value) : "Belum lengkap"}{result?.valid && <small>{pd || parameter.startsWith("vertex_") ? "mm" : "°"}</small>}</strong>
    {pd && result?.valid && <div className="of-eye-pair"><span>OD <b>{formatNumber(v.rightMm)} mm</b></span><span>OS <b>{formatNumber(v.leftMm)} mm</b></span></div>}
    {parameter === "near_pd" && result?.valid && <p className="of-small">Jarak kerja {formatNumber(v.workingDistanceCm)} cm</p>}
    {parameter.startsWith("pantoscopic") && result?.valid && <p className="of-small">{result.source === "manual_instrument" ? "Sudut yang dilaporkan alat/metode referensi." : <>{pantoMedians ? "Median mentah" : "Mentah"} {formatNumber(v.rawDeg)}° · {pantoMedians ? "median head pitch" : "head pitch"} {formatNumber(v.headPitchDeg)}°</>}<br />Positif: bagian bawah lensa lebih dekat ke pipi.{pantoMedians && <><br />Ketiga median dihitung terpisah. Selisih median mentah dan median head pitch dapat berbeda dari median terkoreksi; pasangan tiap sampel tetap disimpan.</>}</p>}
    {result && <><span className={`of-quality of-quality-${q?.category || "low"}`}>Kualitas teknik: {q?.label || ({ high: "Tinggi", medium: "Sedang", low: "Rendah" })[q?.category] || "Belum dinilai"}{q ? ` · ${q.score}/100` : ""}</span><p className="of-small of-muted">{result.method === "manual_instrument" ? "Alat / metode referensi manual" : "Estimasi kamera terkalibrasi"}</p>{result.repeatability && <p className="of-small">{result.sampleCount || result.repeatability.sampleCount || result.repeatability.count || 0} sampel · SD {result.repeatability.valid ? formatNumber(result.repeatability.sampleStdDev, 3) : "belum tersedia"}</p>}<details className="of-result-evidence"><summary>Metode dan bukti kualitas</summary><p>{result.instrumentReference || result.referencePlane || result.method}</p>{result.referenceConvention && <p>{result.referenceConvention}</p>}<ul>{[...(result.reasons || []), ...(q?.reasons || [])].map((reason, index) => <li key={`${index}-${reason}`}>{reason}</li>)}</ul><p>Ketidakpastian: Tidak tersedia.</p><small>Algoritma {result.algorithmVersion}</small></details></>}
    {!result && <p className="of-muted of-small">Belum ada hasil. Gunakan foto terkalibrasi atau catatan alat referensi yang benar-benar digunakan.</p>}
  </article>;
}

function ManualMeasurementDialog({ data, onClose, onSave, customerMode = false }) {
  const selectedType = measurementType(data.requiredParameters);
  const selectedParameter = ({ distance_pd: 'pd_distance', near_pd: 'pd_near' })[selectedType.id] || selectedType.id;
  const [parameter, setParameter] = useState(customerMode ? selectedParameter : "pd_distance"); const [rows, setRows] = useState([{ right: "", left: "" }, { right: "", left: "" }, { right: "", left: "" }]);
  const [instrument, setInstrument] = useState(""); const [convention, setConvention] = useState(""); const [confirmed, setConfirmed] = useState(false); const [protocol, setProtocol] = useState(false); const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const angular = ["wrap", "pantoscopic"].includes(parameter);
  const replacing = parameter.startsWith("pd_") ? !!data.results?.[parameter === "pd_near" ? "near_pd" : "distance_pd"] : ["right", "left"].some(side => !!data.results?.[`${parameter}_${side}`]);
  const submit = async event => {
    event.preventDefault(); setError("");
    const filled = rows.filter(row => row.right !== "" || row.left !== "");
    const readings = filled.map(row => recordManualMeasurement({ parameter, values: { right: asNumber(row.right), left: asNumber(row.left) }, operatorConfirmed: confirmed, instrumentReference: instrument, angleReference: convention, workingDistanceCm: data.workingDistanceCm }));
    if (!readings.length) { setError("Catat setidaknya satu pembacaan kanan dan kiri secara independen."); return; }
    if (readings.some(result => !result.valid)) { setError(readings.flatMap(result => result.reasons || []).join(" ")); return; }
    if (!protocol) { setError("Konfirmasi protokol pandang dan posisi kepala sebelum menyimpan pembacaan."); return; }
    if (replacing && reason.trim().length < 5) { setError("Jelaskan alasan mengganti atau mengoreksi hasil yang telah tersimpan."); return; }
    const rightRepeat = aggregateMeasurements(readings.map(r => angular ? r.values.rightDeg : r.values.rightMm));
    const leftRepeat = aggregateMeasurements(readings.map(r => angular ? r.values.leftDeg : r.values.leftMm));
    const right = rightRepeat.valid ? rightRepeat.median : (angular ? readings[0].values.rightDeg : readings[0].values.rightMm);
    const left = leftRepeat.valid ? leftRepeat.median : (angular ? readings[0].values.leftDeg : readings[0].values.leftMm);
    const combined = recordManualMeasurement({ parameter, values: { right, left }, operatorConfirmed: confirmed, instrumentReference: instrument, angleReference: convention, workingDistanceCm: data.workingDistanceCm });
    if (parameter.startsWith("pd_")) combined.values.pdReference = data.frame?.pdReference || "unspecified";
    const repeatability = { ...rightRepeat, valid: rightRepeat.valid && leftRepeat.valid, sampleCount: readings.length, bySide: { right: rightRepeat, left: leftRepeat } };
    const quality = assessQuality({ source: "manual_instrument", instrumentReference: instrument, confirmations: { readingConfirmed: confirmed, gazeCorrect: protocol, headPoseAcceptable: protocol }, repeatability });
    const base = { ...combined, source: "manual_instrument", measurementContext: measurementContext(data), quality, repeatability, sampleCount: readings.length, rawReadings: readings, referenceConvention: convention || null, operatorConfirmed: confirmed, sourceCaptureIds: [], reasons: [...combined.reasons, ...(!repeatability.valid ? ["Belum ada tiga pembacaan valid. Nilai pembacaan pertama dicatat; median/repeatability belum tersedia."] : [])] };
    const results = { ...(data.results || {}) }; const manualMeasurements = { ...(data.manualMeasurements || {}) };
    if (parameter.startsWith("pd_")) { const key = parameter === "pd_near" ? "near_pd" : "distance_pd"; results[key] = base; manualMeasurements[key] = base; }
    else for (const [side, value] of [["right", right], ["left", left]]) {
      const key = `${parameter === "pantoscopic" ? "pantoscopic" : parameter}_${side}`;
      const values = parameter === "vertex" ? { ...base.values, side, vertexMm: value } : parameter === "pantoscopic" ? { ...base.values, side, correctedDeg: value, rawDeg: null, headPitchDeg: null, headPitchSource: "instrument_reported" } : { ...base.values, side, angleDeg: value };
      results[key] = { ...base, values }; manualMeasurements[key] = results[key];
    }
    setBusy(true);
    try { await onSave({ ...data, results, manualMeasurements }, reason.trim() || `Pencatatan ${parameter} dari alat/metode referensi yang dikonfirmasi pengguna.`); }
    catch (err) { setError(safeError(err)); } finally { setBusy(false); }
  };
  return <Modal title="Catat hasil alat / metode referensi" onClose={busy ? undefined : onClose} wide><form onSubmit={submit} className="of-form">
    <Notice>Masukkan pembacaan yang benar-benar dilakukan. Kolom pengulangan tidak diisi otomatis. Ini bukan perkiraan dari resep atau kontur wajah.</Notice>
    <Field label={customerMode ? "Jenis pengukuran" : "Parameter alat referensi"}><select disabled={customerMode} value={parameter} onChange={e => { setParameter(e.target.value); setRows([{ right: "", left: "" }, { right: "", left: "" }, { right: "", left: "" }]); }}><option value="pd_distance">PD jauh</option><option value="pd_near">PD dekat</option><option value="vertex">Vertex Distance</option><option value="pantoscopic">Pantoscopic Tilt (hasil alat)</option><option value="wrap">Face Form / Wrap Angle</option></select></Field>
    {parameter === "pd_near" && <Notice>Jarak kerja sesi ini: {formatNumber(data.workingDistanceCm)} cm. Ubah data sesi terlebih dahulu jika target menggunakan jarak berbeda.</Notice>}
    <div className="of-reading-grid"><strong>Pembacaan</strong><strong>Kanan / OD ({angular ? "°" : "mm"})</strong><strong>Kiri / OS ({angular ? "°" : "mm"})</strong>{rows.map((row, index) => <React.Fragment key={index}><span>Ke-{index + 1}{index > 0 ? " (opsional)" : ""}</span>{["right", "left"].map(side => <input key={side} type="number" inputMode="decimal" step="0.01" min={angular ? -89.99 : 0.01} max={angular ? 89.99 : undefined} aria-label={`Pembacaan ${index + 1} ${side === "right" ? "kanan" : "kiri"}`} value={row[side]} onChange={e => setRows(v => v.map((r, i) => i === index ? { ...r, [side]: e.target.value } : r))} required={index === 0} />)}</React.Fragment>)}</div>
    <Field label="Identitas alat dan metode referensi" required hint="Contoh: nama alat, nomor identifikasi/kalibrasi dan metode yang dipakai."><textarea rows={2} value={instrument} onChange={e => setInstrument(e.target.value)} required minLength={5} maxLength={2000} /></Field>
    {(!customerMode || angular) && <Field label="Referensi bidang dan konvensi sudut" required={parameter === "wrap"} hint="Untuk wrap, catat bidang acuan serta arti tanda positif/negatif. Pantoscopic positif berarti bawah lensa lebih dekat ke pipi."><textarea rows={2} value={convention} onChange={e => setConvention(e.target.value)} required={parameter === "wrap"} maxLength={2000} /></Field>}
    <label className="of-check"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} /><span>Saya mengonfirmasi pembacaan masing-masing sisi dari alat/metode tersebut.</span></label><label className="of-check"><input type="checkbox" checked={protocol} onChange={e => setProtocol(e.target.checked)} /><span>Posisi kepala dan arah pandang mengikuti protokol pengukuran.</span></label>
    <Field label="Alasan pencatatan / koreksi" required={replacing}><textarea value={reason} onChange={e => setReason(e.target.value)} maxLength={1000} required={replacing} minLength={replacing ? 5 : undefined} /></Field>
    {error && <Notice tone="danger">{error}</Notice>}<div className="of-actions"><Button variant="secondary" onClick={onClose} disabled={busy}>Batal</Button><Button type="submit" busy={busy} disabled={!confirmed || !protocol}>Simpan pembacaan sebagai revisi</Button></div>
  </form></Modal>;
}

function ReviewDialog({ session, revision, actor, settings, onClose }) {
  const [decision, setDecision] = useState("needs_verification"); const [note, setNote] = useState("");
  const [evidence, setEvidence] = useState({ professionalVerified: false, comparisonAccepted: false, referenceInstrument: "", protocolId: "", comparisonNotes: "" });
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const policy = evaluateReview({ session, revision, actor, decision, evidence, settings });
  const set = (key, value) => setEvidence(v => ({ ...v, [key]: value }));
  const submit = async event => { event.preventDefault(); setBusy(true); setError(""); try { await vault.reviewSession(session.id, { decision, note, evidence, expectedRevisionId: revision.id }); onClose(); } catch (err) { setError(safeError(err)); } finally { setBusy(false); } };
  return <Modal title="Keputusan reviewer" onClose={busy ? undefined : onClose} wide><form onSubmit={submit} className="of-form"><Notice>Keputusan terikat pada revisi yang sedang ditinjau. Reviewer harus berbeda dari operator/pembuat revisi. Keputusan tidak mengubah resep atau data mentah.</Notice>
    <Field label="Keputusan review"><select value={decision} onChange={e => setDecision(e.target.value)}><option value="needs_verification">Perlu verifikasi manual</option><option value="needs_remeasure">Perlu diukur ulang</option><option value="approved">Disetujui</option></select></Field>
    <Field label="Catatan reviewer" required><textarea value={note} onChange={e => setNote(e.target.value)} minLength={5} maxLength={4000} required rows={3} /></Field>
    {decision === "approved" && <><div className="of-grid-two"><Field label="Alat / metode pembanding" required><input value={evidence.referenceInstrument} onChange={e => set("referenceInstrument", e.target.value)} required maxLength={500} /></Field><Field label="Nomor protokol verifikasi" required><input value={evidence.protocolId} onChange={e => set("protocolId", e.target.value)} required maxLength={160} /></Field></div><Field label="Hasil perbandingan dan dasar keputusan" required><textarea value={evidence.comparisonNotes} onChange={e => set("comparisonNotes", e.target.value)} required maxLength={4000} rows={3} /></Field><label className="of-check"><input type="checkbox" checked={evidence.professionalVerified} onChange={e => set("professionalVerified", e.target.checked)} /><span>Saya telah melakukan verifikasi profesional atas data dan pengukuran ini.</span></label><label className="of-check"><input type="checkbox" checked={evidence.comparisonAccepted} onChange={e => set("comparisonAccepted", e.target.checked)} /><span>Hasil kamera telah dibandingkan dengan referensi sesuai protokol organisasi dan diterima.</span></label></>}
    {!policy.allowed && <Notice tone="warning"><ul>{policy.reasons.map(text => <li key={text}>{text}</li>)}</ul></Notice>}{error && <Notice tone="danger">{error}</Notice>}
    <div className="of-actions"><Button variant="secondary" onClick={onClose} disabled={busy}>Batal</Button><Button type="submit" busy={busy} disabled={!policy.allowed || !note.trim()}><CheckCircle2 size={17} />Simpan keputusan review</Button></div>
  </form></Modal>;
}

export function ExportDialog({ state, patient, session, revision, data, onClose }) {
  const [format, setFormat] = useState("pdf"); const [confirmed, setConfirmed] = useState(false); const [includePhotos, setIncludePhotos] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const submit = async event => {
    event.preventDefault(); if (!confirmed) return; setBusy(true); setError("");
    try {
      const photos = [];
      if (includePhotos && data.consents?.thumbnail) {
        const liveIds = new Set((state.photos || []).filter(photo => !photo.deletedAt && Date.parse(photo.expiresAt) > Date.now()).map(photo => photo.id));
        for (const capture of (data.captures || []).filter(c => !c.superseded && c.photoId && liveIds.has(c.photoId)).slice(0, 3)) {
          const blob = await vault.getPhoto(capture.photoId);
          const dataUrl = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => reject(new Error("Foto tidak dapat dimasukkan ke laporan.")); reader.readAsDataURL(blob); });
          photos.push({ dataUrl, width: capture.width, height: capture.height, view: capture.view, label: capture.view, photoId: capture.photoId, consent: true });
        }
        if (!photos.length) throw new Error("Tidak ada foto aktif yang dapat disertakan. Nonaktifkan thumbnail untuk mengekspor laporan tanpa foto.");
      }
      const review = state.reviews.filter(r => r.revisionId === revision.id && r.decision === "approved").at(-1);
      const result = await generateReport({ format, patient, session, revision, data, organization: state.organization, operator: state.users.find(u => u.id === session.createdBy), reviewer: review ? state.users.find(u => u.id === review.reviewerId) : null, review, includePhotos, photos, photoConsentConfirmed: includePhotos && data.consents?.thumbnail === true, confirmed: true });
      await vault.recordExport({ sessionId: session.id, revisionId: revision.id, format, confirmed: true, includePhoto: includePhotos, photoIds: photos.map(photo => photo.photoId) });
      if (format === "print") printReport(result); else downloadReport(result);
      onClose();
    } catch (err) { setError(safeError(err)); } finally { setBusy(false); }
  };
  return <Modal title="Ekspor atau cetak laporan" onClose={busy ? undefined : onClose}><form onSubmit={submit} className="of-form"><Notice>Laporan memuat data pasien dan status revisi yang dipilih. Draft tetap berlabel draft. Foto tidak disertakan secara default.</Notice><Field label="Format laporan"><select value={format} onChange={e => { setFormat(e.target.value); setIncludePhotos(false); }}><option value="pdf">PDF</option><option value="csv">CSV</option><option value="json">JSON untuk integrasi</option><option value="print">Tampilan cetak</option></select></Field>
    {["pdf", "json"].includes(format) && <label className="of-check"><input type="checkbox" checked={includePhotos} onChange={e => setIncludePhotos(e.target.checked)} disabled={!data.consents?.thumbnail} /><span>Sertakan maksimal tiga thumbnail foto yang disetujui pasien.{!data.consents?.thumbnail && <small> Persetujuan thumbnail belum tercatat pada revisi ini.</small>}</span></label>}
    <label className="of-check"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} /><span>Saya mengonfirmasi ekspor data pasien ini dan akan menyimpan atau membagikannya hanya kepada pihak yang berwenang.</span></label>
    {error && <Notice tone="danger">{error}</Notice>}<div className="of-actions"><Button variant="secondary" onClick={onClose} disabled={busy}>Batal</Button><Button type="submit" disabled={!confirmed} busy={busy}><Download size={17} />{format === "print" ? "Siapkan cetak" : "Buat dan unduh laporan"}</Button></div>
  </form></Modal>;
}

export function ReviewQueue({ state, onOpen }) {
  const sessions = state.sessions.filter(s => ["pending_review", "needs_verification", "needs_remeasure"].includes(s.status));
  return <><div className="of-page-heading"><div><span className="of-eyebrow">VERIFIKASI INDEPENDEN</span><h1>Review pengukuran</h1><p>Periksa versi, metode dan bukti sebelum memberi keputusan.</p></div><ClipboardCheck size={34} /></div><section className="of-card">{sessions.length ? <div className="of-session-list">{sessions.map(session => <button className="of-session-row" type="button" key={session.id} onClick={() => onOpen(session.id)}><ClipboardCheck size={23} /><span className="of-grow"><strong>{state.patients.find(p => p.id === session.patientId)?.fullName || "Pasien"}</strong><small>{readableDate(session.examinationDate)} · {state.users.find(u => u.id === session.createdBy)?.displayName || "Operator"}</small></span><StatusBadge status={session.status} labels={STATUS_LABELS} /><span>→</span></button>)}</div> : <div className="of-empty"><FileCheck2 size={35} /><h3>Antrean review kosong</h3><p>Sesi yang diajukan operator akan muncul di sini.</p></div>}</section></>;
}
