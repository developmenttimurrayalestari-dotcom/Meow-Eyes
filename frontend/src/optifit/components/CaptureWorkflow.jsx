import React, { useEffect, useMemo, useState } from "react";
import { Camera, Check, ImagePlus, Info, Save, ShieldCheck } from "lucide-react";
import { workspace as vault } from "../storage/workspace";
import CameraCapture from "../vision/CameraCapture";
import LandmarkEditor from "../vision/LandmarkEditor";
import { aggregateMeasurements, analyseImage, assessQuality, createCalibration, measurePD, measurePantoscopic, measureVertex } from "../vision";
import { Button, Field, Help, Modal, Notice, asNumber, dataUrlBlob, formatNumber, makeId, normalizedImage, safeError } from "./ui";
import { measurementContext, sameMeasurementContext } from "./measurementContext";
import { customerViews } from '../domain/customerFlow';
import { CustomerPhotoChecks, CustomerScaleFields } from './CustomerCaptureFields';
import MeasurementIllustrationGuide from './MeasurementIllustrationGuide';
import { customerFrameCapture, frameScaleReference, frameScaleSpec } from '../domain/frameScale';

const PREPARATION = [
  "Frame telah disetel pada posisi pemakaian normal.", "Temple dan nose pad sudah disesuaikan.", "Pasien menggunakan natural head posture.",
  "Rambut tidak menutupi mata atau frame.", "Pupil dan tepi frame terlihat jelas.", "Tidak ada refleksi berlebihan pada area ukur.",
  "Pencahayaan cukup dan merata; kamera bersih.", "Kamera frontal berada sejajar dengan tinggi mata.", "Kamera utama dipakai; ultra-wide tidak digunakan.",
  "Digital zoom dinonaktifkan atau diperiksa pada perangkat.", "Marker atau bagian frame dengan ukuran nyata telah disiapkan.",
];
export const VIEWS = [
  ["frontal", "Frontal — target jauh", "Pasien melihat target jauh di belakang atau di samping operator. Jangan melihat layar ponsel."],
  ["three_quarter_left", "Tiga-perempat kiri", "Tampilkan bidang frame kiri. Foto ini merupakan dokumentasi multi-sudut; wrap tidak ditebak dari satu foto."],
  ["three_quarter_right", "Tiga-perempat kanan", "Tampilkan bidang frame kanan dengan posisi pemakaian tetap."],
  ["lateral_right", "Lateral kanan (OD)", "Tampilkan apex kornea dan permukaan belakang lensa kanan; pasang skala dekat bidang yang diukur."],
  ["lateral_left", "Lateral kiri (OS)", "Tampilkan apex kornea dan permukaan belakang lensa kiri; jangan mengganti permukaan lensa dengan rim depan."],
  ["frontal_near", "Frontal — target dekat", "Gunakan target pada jarak kerja yang dicatat. Simpan terpisah dari pengukuran jauh."],
];
const QUALITY_CONFIRMATIONS = [
  ["landmarksConfirmed", "Landmark telah diperiksa dan dikonfirmasi"], ["frameVisible", "Frame terlihat penuh"],
  ["pupilsVisible", "Pupil / referensi mata terlihat jelas"], ["noReflections", "Area ukur bebas refleksi yang mengganggu"],
  ["gazeCorrect", "Arah pandang sesuai protokol"], ["headPoseAcceptable", "Posisi kepala sesuai panduan"],
  ["distanceAppropriate", "Jarak kamera telah diperiksa operator"], ["scaleConsistent", "Skala antar sampel telah dibandingkan"],
];
const REASONS = ["Penandaan awal", "Landmark salah", "Refleksi", "Frame rimless", "Mata tertutup sebagian", "Marker tidak tepat", "Koreksi posisi lensa", "Alasan lain"];

export function Preparation({ data, onSave, disabled = false, serverMode = false }) {
  const [checked, setChecked] = useState(data.preparation || []);
  const [consent, setConsent] = useState(data.consents?.capture || false);
  const [retain, setRetain] = useState(data.consents?.retainPhotos !== false);
  const [thumbnail, setThumbnail] = useState(data.consents?.thumbnail || false);
  const [uploadPhotos, setUploadPhotos] = useState(data.consents?.uploadPhotos === true);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [examples, setExamples] = useState(false);
  const save = async () => { setError(""); setBusy(true); try { await onSave({ ...data, preparation: checked, consents: { ...data.consents, capture: consent, retainPhotos: serverMode ? true : retain, uploadPhotos: serverMode && uploadPhotos, thumbnail: serverMode ? uploadPhotos && thumbnail : thumbnail, confirmedAt: new Date().toISOString() } }, "Persiapan pengukuran dan pilihan persetujuan pasien dicatat."); } catch (err) { setError(safeError(err)); } finally { setBusy(false); } };
  return <section className="of-card"><div className="of-section-heading"><div><h2>Persiapan pengukuran</h2><p>Periksa posisi pemakaian sebelum kamera dibuka.</p></div><ShieldCheck size={28} /></div>
    <div className="of-checkbox-grid">{PREPARATION.map((text, index) => <label className="of-check" key={text}><input type="checkbox" checked={checked.includes(index)} disabled={disabled} onChange={e => setChecked(v => e.target.checked ? [...v, index] : v.filter(i => i !== index))} /><span>{text}</span></label>)}</div>
    <div className="of-actions of-actions-start"><Button variant="secondary" disabled={disabled} onClick={() => setChecked(PREPARATION.map((_, i) => i))}>Semua persiapan siap</Button><Button variant="quiet" onClick={() => setExamples(true)}><Info size={17} />Lihat contoh posisi</Button></div>
    <div className="of-consent-box"><h3>{serverMode ? "Persetujuan pengukuran" : "Persetujuan pasien"}</h3><p>{serverMode ? "Hasil, titik ukur, dan revisi akan disimpan pada akun Meow Eyes Anda. Foto diproses di perangkat; penyimpanan foto ke akun merupakan pilihan terpisah." : "Gambar digunakan untuk membantu fitting dan review pada perangkat ini."} Pengambilan gambar tidak mengukur kekuatan resep dan tidak menggantikan pemeriksaan profesional.</p><label className="of-check"><input type="checkbox" checked={consent} disabled={disabled} onChange={e => setConsent(e.target.checked)} /><span>{serverMode ? "Saya menyetujui pengambilan gambar dan penyimpanan hasil untuk tujuan fitting ini." : "Pasien menyetujui pengambilan gambar untuk tujuan fitting ini."}</span></label>
      {serverMode ? <><label className="of-check"><input type="checkbox" checked={uploadPhotos} disabled={disabled} onChange={e => { setUploadPhotos(e.target.checked); if (!e.target.checked) setThumbnail(false); }} /><span>Simpan juga foto secara privat di akun Meow Eyes agar dapat dibuka kembali untuk koreksi dan review. Opsional.</span></label><Notice>{uploadPhotos ? "Foto yang disimpan hanya tersedia bagi pemilik akun dan petugas Meow Eyes yang berwenang, sesuai masa simpan foto." : "Foto tidak diunggah dan hanya tersedia selama halaman ini terbuka. Setelah halaman dimuat ulang, hasil serta titik ukur tetap tersimpan; foto perlu diambil ulang jika ingin melakukan koreksi visual."}</Notice></> : <><Field label="Penyimpanan foto pengukuran"><select value={retain ? "retain" : "delete"} disabled={disabled} onChange={e => setRetain(e.target.value === "retain")}><option value="retain">Simpan terenkripsi untuk koreksi dan review</option><option value="delete">Hapus foto setelah landmark dan hasil disimpan</option></select></Field>{!retain && <Notice tone="warning">Foto tiap sampel dihapus sesudah koreksinya disimpan. Landmark, metode dan riwayat tetap ada, tetapi gambar tidak dapat dibuka kembali untuk review. Ambil ulang jika membutuhkan koreksi gambar lebih lanjut.</Notice>}</>}
      <label className="of-check"><input type="checkbox" checked={thumbnail} disabled={disabled || (serverMode && !uploadPhotos)} onChange={e => setThumbnail(e.target.checked)} /><span>{serverMode ? "Saya juga menyetujui thumbnail foto pada laporan jika dipilih saat ekspor." : "Pasien juga menyetujui thumbnail pada laporan jika dipilih saat ekspor."} Pilihan ekspor foto tetap nonaktif secara default.</span></label>
    </div>
    {error && <Notice tone="danger">{error}</Notice>}<Button disabled={disabled || !consent || checked.length !== PREPARATION.length} busy={busy} onClick={save}><Check size={18} />Simpan persiapan dan persetujuan</Button>
    {examples && <Modal title="Panduan posisi pengambilan" onClose={() => setExamples(false)}><div className="of-position-examples"><svg viewBox="0 0 380 190" role="img" aria-label="Panduan frontal dan lateral dengan kamera sejajar mata"><g fill="none" stroke="currentColor" strokeWidth="2"><ellipse cx="97" cy="83" rx="42" ry="59" /><path d="M50 82h94M97 17v133M159 82h39" strokeDasharray="5 5" /><rect x="61" y="67" width="29" height="19" rx="4" /><rect x="104" y="67" width="29" height="19" rx="4" /><path d="M90 75h14M265 27c-26 8-35 29-31 53l-10 10 13 6c-1 35 13 48 37 47M257 65l-5 38M247 78h65" /><rect x="311" y="65" width="28" height="30" rx="4" /></g><text x="57" y="174" fill="currentColor">Frontal sejajar mata</text><text x="238" y="174" fill="currentColor">Lateral sejajar</text></svg><p>Pertahankan natural head posture dan posisi frame yang sudah disetel. Kamera utama berada sejajar area ukur; pasien melihat target yang sesuai protokol.</p><p>Untuk distance PD, target jauh berada di belakang atau di samping operator. Untuk near PD, gunakan jarak kerja yang dicatat. Marker harus terlihat utuh dan berada pada bidang referensi yang relevan.</p></div></Modal>}
  </section>;
}

export function CapturePanel({ data, session, patient, onSave, onAnnotate, disabled = false, customerMode = false }) {
  const allowedViews = customerViews(data.requiredParameters);
  const [view, setView] = useState(customerMode ? allowedViews[0] || 'frontal' : "frontal"); const [camera, setCamera] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const ready = data.consents?.capture && (customerMode ? data.preparation?.includes('customer_ready') || data.preparation?.length === PREPARATION.length : data.preparation?.length === PREPARATION.length);
  const visibleViews = VIEWS.filter(([key]) => customerMode ? allowedViews.includes(key) : key !== "frontal_near" || data.requiredParameters?.includes("near_pd"));
  const currentCaptures = (data.captures || []).filter(c => c.view === view && !c.superseded);
  const saveSamples = async (samples, deviceMetadata = {}, burstAnalysis = null) => {
    if (!ready) throw new Error("Persetujuan dan persiapan harus disimpan terlebih dahulu.");
    const photoIds = []; const burstId = makeId();
    try {
      const captures = []; const hashes = new Set();
      for (let i = 0; i < samples.length; i += 1) {
        const sample = samples[i]; const blob = sample.blob || dataUrlBlob(sample.dataUrl);
        const digest = await crypto.subtle.digest("SHA-256", await blob.arrayBuffer());
        const photoHash = [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, "0")).join("");
        if (hashes.has(photoHash)) throw new Error("Rangkaian berisi foto yang identik. Ambil pengukuran ulang yang independen; satu foto tidak dihitung sebagai beberapa sampel.");
        hashes.add(photoHash);
        const photoId = await vault.putPhoto({ patientId: patient.id, sessionId: session.id, blob, consent: true, metadata: { purpose: "capture", width: sample.width, height: sample.height, view } });
        photoIds.push(photoId);
        captures.push({ id: makeId(), view, burstId, sampleIndex: i, photoId, photoHash, width: sample.width, height: sample.height, createdAt: new Date().toISOString(), analysis: sample.analysis, device: deviceMetadata, burstAnalysis, measurementContext: measurementContext(data), points: {}, automaticPoints: {}, calibrationSpec: customerMode ? frameScaleSpec(data.frame, view) : { method: "marker", widthMm: null, heightMm: null, lengthMm: null, referencePlane: "", evidence: {} }, confirmations: {}, measurements: {}, superseded: false });
      }
      const next = { ...data, captures: [...(data.captures || []).map(c => c.view === view && !c.superseded ? { ...c, superseded: true, supersededBy: burstId } : c), ...captures] };
      // A retake invalidates the old aggregate for that view until new samples
      // have actually been annotated. Previous values remain in earlier revisions.
      const keys = view === "frontal" ? ["distance_pd"] : view === "frontal_near" ? ["near_pd"] : view.startsWith("lateral_") ? [`vertex_${view.endsWith("right") ? "right" : "left"}`, `pantoscopic_${view.endsWith("right") ? "right" : "left"}`] : [];
      next.results = { ...(data.results || {}) }; keys.forEach(key => { if (next.results[key]?.source === "camera") delete next.results[key]; });
      await onSave(next, `Pengambilan ${samples.length} sampel ${VIEWS.find(([key]) => key === view)?.[1] || view}.`);
      setCamera(false);
    } catch (err) {
      for (const id of photoIds) { try { await vault.deletePhoto(id, { reason: "Pengambilan foto tidak berhasil disimpan sebagai revisi sesi." }); } catch {} }
      throw err;
    }
  };
  const captured = async packet => { setBusy(true); setError(""); try { await saveSamples(packet.samples?.length ? packet.samples : [packet], packet.deviceMetadata, packet.burstAnalysis); } catch (err) { setError(safeError(err)); } finally { setBusy(false); } };
  const importImages = async event => {
    const files = [...(event.target.files || [])]; event.target.value = ""; if (!files.length) return;
    if (files.length > 5) { setError("Pilih maksimal lima foto untuk satu posisi."); return; }
    setBusy(true); setError("");
    try { const samples = []; for (const file of files) { const image = await normalizedImage(file); samples.push({ ...image, analysis: analyseImage(image.imageData) }); } await saveSamples(samples, { source: "operator_import", model: data.deviceModel || "Tidak tersedia" }); }
    catch (err) { setError(safeError(err)); } finally { setBusy(false); }
  };
  return <section className="of-card"><div className="of-section-heading"><div><h2>Foto pengukuran</h2><p>Ambil beberapa sampel nyata untuk tiap posisi. {vault.serverMode ? "Hasil disimpan pada akun; foto hanya diunggah jika Anda memilihnya pada tahap persetujuan." : "Foto dan metadata tetap lokal."}</p></div><Camera size={27} /></div>
    {customerMode && !camera && <MeasurementIllustrationGuide data={data} view={view} collapsible/>}
    {!ready && <Notice tone="warning">Simpan checklist dan persetujuan pasien pada tahap Persiapan sebelum membuka kamera atau memilih foto.</Notice>}
    <div className="of-view-tabs" role="group" aria-label="Posisi pengambilan">{visibleViews.map(([key, title]) => <button key={key} type="button" className={view === key ? "active" : ""} disabled={camera || busy} onClick={() => { setView(key); setError(""); }}>{title}<small>{(data.captures || []).filter(c => c.view === key && !c.superseded).length} sampel</small></button>)}</div>
    <Notice>{customerMode ? (view === 'frontal' ? 'Lihat benda yang jauh, bukan layar. Posisikan kamera sejajar mata dan pastikan kedua mata terlihat jelas.' : view === 'frontal_near' ? 'Lihat benda bacaan pada jarak yang Anda isi. Ambil foto dari depan dengan kamera sejajar mata.' : 'Minta bantuan untuk mengambil foto dari sisi wajah yang dipilih. Jaga posisi kepala dan kacamata tetap nyaman.') : VIEWS.find(([key]) => key === view)?.[2]}{view === "frontal_near" && <strong> Jarak membaca: {formatNumber(data.workingDistanceCm)} cm.</strong>}</Notice>
    {view.startsWith("three_quarter") && <Notice>Rekonstruksi wrap otomatis belum tersedia. Simpan gambar multi-sudut untuk pemeriksaan dan catat wrap dari alat/metode referensi di tahap Hasil.</Notice>}
    {camera ? <CameraCapture customerMode={customerMode} view={view} consent={!!data.consents?.capture} checklistComplete={!!ready} uploadEnabled={vault.serverMode && data.consents?.uploadPhotos === true} onCapture={captured} onCancel={() => setCamera(false)} /> : <div className="of-capture-actions"><Button onClick={() => setCamera(true)} disabled={disabled || !ready || busy}><Camera size={18} />{currentCaptures.length ? "Ambil ulang dengan kamera" : "Buka kamera"}</Button><label className={`of-button of-button-secondary ${disabled || !ready || busy ? "of-disabled" : ""}`}><ImagePlus size={18} />Pilih foto lokal<input type="file" className="of-visually-hidden" accept="image/jpeg,image/png,image/webp" multiple onChange={importImages} disabled={disabled || !ready || busy} /></label></div>}
    {busy && <p className="of-muted" role="status">Mengenkripsi dan menyimpan sampel…</p>}{error && <Notice tone="danger">{error}</Notice>}
    <div className="of-capture-grid">{currentCaptures.map((capture, index) => <CaptureCard customerMode={customerMode} key={capture.id} capture={capture} index={index} onOpen={() => onAnnotate(capture.id)} readOnly={disabled || capture.contextInvalidated || capture.photoRetained === false} disabled={busy} />)}</div>
    <p className="of-small of-muted">Tandai setiap sampel secara independen. Perbandingan beberapa frame gambar saja belum membuktikan repeatability nilai ukur.</p>
  </section>;
}

function CaptureCard({ capture, index, onOpen, disabled, readOnly, customerMode = false }) {
  const [url, setUrl] = useState(null); const [unavailable, setUnavailable] = useState(false);
  useEffect(() => { let active = true; let objectUrl; setUnavailable(false); setUrl(null); vault.getPhoto(capture.photoId).then(blob => { if (active) { objectUrl = URL.createObjectURL(blob); setUrl(objectUrl); } }).catch(() => { if (active) setUnavailable(true); }); return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); }; }, [capture.photoId]);
  return <div className="of-capture-card"><div className="of-capture-thumb">{url ? <img src={url} alt={`Sampel pengukuran ${index + 1}`} /> : <span>{unavailable ? "Foto sudah dihapus / tidak tersedia" : "Membuka foto terenkripsi…"}</span>}</div><div><strong>Sampel {index + 1}</strong><p>{capture.width} × {capture.height} px</p><small>Detail: {capture.analysis?.sharpness === "usable" ? "dapat diperiksa" : "perlu diperiksa ulang"} · cahaya: {capture.analysis?.exposure === "usable" ? "memadai" : "perlu diperiksa"}</small>{capture.contextInvalidated && <p className="of-warning-text of-small">Konteks telah berubah; ambil ulang.</p>}<Button variant="secondary" disabled={disabled || (!readOnly && unavailable)} onClick={onOpen}>{readOnly ? "Lihat foto & jejak ukur" : Object.keys(capture.points || {}).length ? "Periksa / koreksi titik" : customerMode ? "Tandai titik & acuan frame" : "Tandai titik & kalibrasi"}</Button></div></div>;
}

export function CaptureViewer({ capture, onClose }) {
  const [image, setImage] = useState(null); const [error, setError] = useState("");
  useEffect(() => { let active = true; let url; vault.getPhoto(capture.photoId).then(blob => { if (active) { url = URL.createObjectURL(blob); setImage({ dataUrl: url, width: capture.width, height: capture.height }); } }).catch(err => { if (active) setError(safeError(err)); }); return () => { active = false; if (url) URL.revokeObjectURL(url); }; }, [capture.photoId, capture.width, capture.height]);
  const labels = { rightPupil: "Pupil kanan (OD)", leftPupil: "Pupil kiri (OS)", midlineTop: "Garis tengah: atas", midlineBottom: "Garis tengah: bawah", markerTL: "Marker kiri atas", markerTR: "Marker kanan atas", markerBR: "Marker kanan bawah", markerBL: "Marker kiri bawah", scaleStart: "Referensi awal", scaleEnd: "Referensi akhir", cornea: "Apex kornea", backLens: "Belakang lensa", gazeStart: "Pandangan awal", gazeEnd: "Pandangan depan", lensTop: "Lensa atas", lensBottom: "Lensa bawah", verticalTop: "Vertikal atas", verticalBottom: "Vertikal bawah" };
  const definitions = [...new Set([...Object.keys(capture.points || {}), ...Object.keys(capture.automaticPoints || {})])].map(key => ({ key, label: labels[key] || key }));
  return <Modal title="Pemeriksaan foto & jejak ukur" onClose={onClose} wide><Notice>Mode baca saja. Perbesaran dan perbandingan titik tidak mengubah data revisi ini.</Notice>{capture.contextInvalidated && <Notice tone="warning">Konteks sesi berubah setelah pengambilan ini. Sampel disimpan sebagai riwayat dan tidak dipakai untuk hasil konteks baru.</Notice>}{image && <LandmarkEditor image={image} points={capture.points || {}} automaticPoints={capture.automaticPoints || {}} pointDefinitions={definitions} disabled />}{error && <Notice tone="warning">Foto tidak dapat dibuka: {error} Landmark dan data pengukuran yang tersimpan tetap dapat diperiksa.</Notice>}<div className="of-grid-two"><section className="of-subcard"><h3>Kalibrasi tersimpan</h3><p>Metode: {capture.calibrationSpec?.method || "Belum ditandai"}</p><p>Bidang: {capture.calibrationSpec?.referencePlane || "Belum dicatat"}</p><p>Ukuran referensi: {capture.calibrationSpec?.method === "frame" ? formatNumber(capture.calibrationSpec?.lengthMm) : `${formatNumber(capture.calibrationSpec?.widthMm)} × ${formatNumber(capture.calibrationSpec?.heightMm)}`} mm</p><p>Status: {capture.calibration?.valid ? "Transformasi tersedia" : "Belum valid"}</p>{(capture.calibration?.reasons || []).map(reason => <p key={reason} className="of-small">{reason}</p>)}</section><section className="of-subcard"><h3>Provenans sampel</h3><p>Posisi: {VIEWS.find(([key]) => key === capture.view)?.[1] || capture.view}</p><p>Resolusi asli: {capture.width} × {capture.height} px</p><p>Head pitch: {capture.headPitchDeg == null ? "Tidak tersedia" : `${formatNumber(capture.headPitchDeg)}° (${capture.headPitchSource})`}</p><p>Referensi PD: {capture.measurementContext?.frame?.pdReference || "Belum dicatat"}</p><p>Jarak kerja: {formatNumber(capture.measurementContext?.workingDistanceCm)} cm</p></section></div><details className="of-result-evidence"><summary>Koordinat, hasil sampel & konfirmasi tersimpan</summary><pre>{JSON.stringify({ points: capture.points, automaticPoints: capture.automaticPoints, measurements: capture.measurements, confirmations: capture.confirmations, calibrationEvidence: capture.calibrationSpec?.evidence, measurementContext: capture.measurementContext, captureId: capture.id, photoHash: capture.photoHash }, null, 2)}</pre></details><div className="of-actions"><Button onClick={onClose}>Selesai memeriksa</Button></div></Modal>;
}

export function CaptureEditor({ capture, data, settings, onClose, onSave, customerMode = false }) {
  const initialCustomer = customerMode ? customerFrameCapture(capture, data.frame) : null;
  const frameReference = frameScaleReference(data.frame, capture.view);
  const [image, setImage] = useState(null); const [points, setPoints] = useState(initialCustomer?.points || capture.points || {}); const [automaticPoints, setAutomaticPoints] = useState(initialCustomer?.automaticPoints || capture.automaticPoints || {});
  const [spec, setSpec] = useState(initialCustomer?.spec || capture.calibrationSpec || { method: "marker", evidence: {}, referencePlane: "" }); const [confirmations, setConfirmations] = useState(initialCustomer?.confirmations || capture.confirmations || {});
  const [headPitchDeg, setHeadPitchDeg] = useState(capture.headPitchDeg ?? ""); const [headPitchSource, setHeadPitchSource] = useState(capture.headPitchSource || ""); const [inwardDirection, setInwardDirection] = useState(capture.inwardDirection || "");
  const [reason, setReason] = useState(customerMode ? 'Penandaan titik oleh customer' : ""); const [reasonDetail, setReasonDetail] = useState(""); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  useEffect(() => { let active = true; let url; vault.getPhoto(capture.photoId).then(blob => { if (active) { url = URL.createObjectURL(blob); setImage({ dataUrl: url, width: capture.width, height: capture.height }); } }).catch(err => { if (active) setError(safeError(err)); }); return () => { active = false; if (url) URL.revokeObjectURL(url); }; }, [capture.photoId, capture.width, capture.height]);
  const lateral = capture.view.startsWith("lateral_"); const frontal = capture.view.startsWith("frontal");
  const side = capture.view.endsWith('right') ? 'right' : 'left';
  const vertex = !customerMode || data.requiredParameters?.includes(`vertex_${side}`);
  const panto = !customerMode || data.requiredParameters?.includes(`pantoscopic_${side}`);
  const documentationOnly = customerMode && capture.view.startsWith('three_quarter');
  const definitions = useMemo(() => [
    ...(customerMode ? [["scaleStart", frameReference?.start], ["scaleEnd", frameReference?.end]] : spec.method === "marker" ? [["markerTL", "Marker: kiri atas"], ["markerTR", "Marker: kanan atas"], ["markerBR", "Marker: kanan bawah"], ["markerBL", "Marker: kiri bawah"]] : [["scaleStart", "Referensi frame: ujung awal"], ["scaleEnd", "Referensi frame: ujung akhir"]]),
    ...(frontal ? [["rightPupil", "Pusat pupil kanan pasien (OD)"], ["leftPupil", "Pusat pupil kiri pasien (OS)"], ["midlineTop", "Garis tengah bridge: atas"], ["midlineBottom", "Garis tengah bridge: bawah"]] : []),
    ...(lateral && vertex ? [["cornea", "Bagian depan mata"], ["backLens", "Permukaan belakang lensa"], ["gazeStart", "Arah pandang: awal"], ["gazeEnd", "Arah pandang: depan"]] : []),
    ...(lateral && panto ? [["lensTop", "Lensa: ujung atas"], ["lensBottom", "Lensa: ujung bawah"], ["verticalTop", "Garis tegak: atas"], ["verticalBottom", "Garis tegak: bawah"]] : []),
  ].filter(([, label]) => label).map(([key, label]) => ({ key, label: customerMode ? label.replaceAll('Marker', 'Pembanding').replaceAll('pasien', 'Anda').replaceAll('bridge', data.frame?.pdReference === 'frame_bridge' ? 'kacamata' : 'wajah') : label })), [spec.method, frontal, lateral, vertex, panto, customerMode, data.frame?.pdReference, frameReference?.start, frameReference?.end]);
  const calibration = createCalibration({ ...spec, image: { width: capture.width, height: capture.height }, corners: [points.markerTL, points.markerTR, points.markerBR, points.markerBL], segment: [points.scaleStart, points.scaleEnd] });
  const updated = { ...capture, points, automaticPoints, measurementContext: capture.measurementContext || measurementContext(data), calibrationSpec: spec, calibration, confirmations, headPitchDeg: asNumber(headPitchDeg), headPitchSource, inwardDirection };
  const measured = Object.fromEntries(Object.entries(computeCapture(updated, data)).filter(([key]) => !customerMode || data.requiredParameters?.includes(key)));
  const save = async () => {
    if (!reason || (reason === "Alasan lain" && !reasonDetail.trim())) { setError("Pilih alasan penandaan/koreksi; jelaskan jika memilih alasan lain."); return; }
    setBusy(true); setError("");
    try {
      const captures = (data.captures || []).map(c => c.id === capture.id ? { ...updated, measurements: measured, photoRetained: data.consents?.retainPhotos !== false } : c);
      const next = { ...data, captures, results: aggregateCaptureResults(captures, data.results || {}) };
      await onSave(next, `${reason}${reasonDetail.trim() ? `: ${reasonDetail.trim()}` : ""}`);
      if (data.consents?.retainPhotos === false) await vault.deletePhoto(capture.photoId, { reason: "Foto dihapus setelah ekstraksi landmark sesuai pilihan persetujuan pasien." });
      onClose();
    } catch (err) { setError(safeError(err)); } finally { setBusy(false); }
  };
  const setCalibration = (key, value) => setSpec(v => ({ ...v, [key]: value }));
  return <Modal title={`${VIEWS.find(([key]) => key === capture.view)?.[1] || capture.view} · Sampel ${capture.sampleIndex + 1}`} onClose={busy ? undefined : onClose} wide>
    {customerMode && initialCustomer?.changed && !documentationOnly && <Notice>Foto lama tetap tersimpan. Tandai ulang dua ujung acuan frame dan konfirmasi posisinya untuk memakai alur baru; titik pembanding lama tidak digunakan otomatis.</Notice>}
    {customerMode && <MeasurementIllustrationGuide data={data} view={capture.view} method={spec.method} initialStage={documentationOnly ? 'photo' : 'points'} collapsible/>}
    {documentationOnly && image && <img src={image.dataUrl} alt="Foto sudut kacamata" className="of-customer-photo"/>}
    <Notice>{customerMode ? "Kanan/kiri mengikuti mata Anda. Tandai dua ujung acuan frame dan titik pengukuran pada foto. Ukuran frame sesi dipakai otomatis untuk menghitung jarak dalam milimeter." : "OD/OS mengacu pada mata pasien. Semua titik memakai koordinat gambar asli; periksa pencerminan foto yang diimpor. Nilai mm hanya tampil bila kalibrasi valid."}</Notice>
    {image && !documentationOnly && <LandmarkEditor image={image} points={points} automaticPoints={automaticPoints} pointDefinitions={definitions} onChange={setPoints} onAutomaticPoints={next => setAutomaticPoints(previous => ({ ...next, ...previous }))} disabled={busy} allowAutomatic={data.mode !== "manual"} />}
    {customerMode ? !documentationOnly && <div className="of-editor-controls"><CustomerScaleFields spec={spec} setSpec={setSpec} calibration={calibration} disabled={busy} frame={data.frame} view={capture.view}/><CustomerPhotoChecks confirmations={confirmations} setConfirmations={setConfirmations} frontal={frontal} vertex={lateral && vertex} panto={lateral && panto} headPitchDeg={headPitchDeg} setHeadPitchDeg={setHeadPitchDeg} headPitchSource={headPitchSource} setHeadPitchSource={setHeadPitchSource} inwardDirection={inwardDirection} setInwardDirection={setInwardDirection}/></div> : (<div className="of-editor-controls"><section className="of-subcard"><h3>Kalibrasi</h3><Field label="Metode kalibrasi"><select value={spec.method} onChange={e => setCalibration("method", e.target.value)}>{(settings.calibrationMethods || ["marker", "frame"]).map(method => <option value={method} key={method}>{method === "marker" ? "Marker fisik empat sudut" : "Bagian frame dengan panjang diketahui"}</option>)}</select></Field>
      {spec.method === "marker" ? <div className="of-grid-two"><Field label="Lebar nyata marker (mm)"><input type="number" min="0.01" step="0.01" value={spec.widthMm ?? ""} onChange={e => setCalibration("widthMm", asNumber(e.target.value))} /></Field><Field label="Tinggi nyata marker (mm)"><input type="number" min="0.01" step="0.01" value={spec.heightMm ?? ""} onChange={e => setCalibration("heightMm", asNumber(e.target.value))} /></Field></div> : <Field label="Panjang referensi frame (mm)"><input type="number" min="0.01" step="0.01" value={spec.lengthMm ?? ""} onChange={e => setCalibration("lengthMm", asNumber(e.target.value))} /></Field>}
      <Field label="Jenis marker / bidang referensi"><input value={spec.referencePlane || ""} onChange={e => setCalibration("referencePlane", e.target.value)} maxLength={240} placeholder="Catat marker dan posisi bidang yang benar-benar dipakai" /></Field>
      {[["knownSize", "Ukuran nyata telah diukur dan diketahui"], ["fullyVisible", "Marker / referensi terlihat utuh"], ["samePlane", "Bidang referensi sesuai dengan bidang pengukuran"], ["clearEdges", "Tepi referensi jelas dan tajam"], ...(spec.method === "frame" ? [["frontoparallel", "Bagian frame berada pada bidang paralel kamera"]] : [])].map(([key, label]) => <label key={key} className="of-check"><input type="checkbox" checked={!!spec.evidence?.[key]} onChange={e => setSpec(v => ({ ...v, evidence: { ...v.evidence, [key]: e.target.checked } }))} /><span>{label}</span></label>)}
      <Notice tone={calibration.valid ? "success" : "warning"}>{calibration.valid ? "Transformasi bidang kalibrasi tersedia. Tetap periksa parallax dan distorsi; hasil memerlukan review." : calibration.reasons.join(" ")}</Notice>
    </section><section className="of-subcard"><h3>Pemeriksaan operator</h3>{QUALITY_CONFIRMATIONS.map(([key, label]) => <label className="of-check" key={key}><input type="checkbox" checked={!!confirmations[key]} onChange={e => setConfirmations(v => ({ ...v, [key]: e.target.checked }))} /><span>{label}</span></label>)}
      {lateral && <><label className="of-check"><input type="checkbox" checked={!!confirmations.surfaceVisible} onChange={e => setConfirmations(v => ({ ...v, surfaceVisible: e.target.checked }))} /><span>Apex kornea dan permukaan belakang lensa yang sesuai terlihat</span></label><label className="of-check"><input type="checkbox" checked={!!confirmations.verticalReferenceConfirmed} onChange={e => setConfirmations(v => ({ ...v, verticalReferenceConfirmed: e.target.checked }))} /><span>Garis vertikal mempunyai referensi yang diperiksa</span></label>
        <div className="of-grid-two"><Field label="Head pitch terukur (°)"><input type="number" step="0.01" min="-89.99" max="89.99" value={headPitchDeg} onChange={e => setHeadPitchDeg(e.target.value)} placeholder="Jangan mengasumsikan nol" /></Field><Field label="Sumber head pitch"><select value={headPitchSource} onChange={e => setHeadPitchSource(e.target.value)}><option value="">Pilih sumber</option><option value="instrument">Alat ukur</option><option value="manual_reference">Referensi manual</option></select></Field></div><Field label="Arah menuju wajah pada foto"><select value={inwardDirection} onChange={e => setInwardDirection(e.target.value)}><option value="">Pilih arah</option><option value="left">Ke kiri gambar</option><option value="right">Ke kanan gambar</option></select></Field><Help title="Konvensi pantoscopic tilt">Positif berarti bagian bawah lensa lebih dekat ke pipi. Head pitch positif menyatakan kontribusi kepala menunduk. Nilai mentah dan terkoreksi disimpan terpisah.</Help></>}
    </section></div>)}
    <section className="of-subcard"><h3>Hasil sampel saat ini</h3>{Object.keys(measured).length ? Object.entries(measured).map(([key, result]) => <div className="of-sample-result" key={key}><strong>{key.replaceAll("_", " ")}</strong>{result.valid ? <span>{result.unit === "mm" ? result.values.binocularMm != null ? `OD ${formatNumber(result.values.rightMm)} · OS ${formatNumber(result.values.leftMm)} · total ${formatNumber(result.values.binocularMm)} mm` : `${formatNumber(result.values.vertexMm)} mm` : `${formatNumber(result.values.correctedDeg)}° terkoreksi`}</span> : <span className="of-warning-text">{result.reasons.join(" ")}</span>}</div>) : <p className="of-muted">Gambar tiga-perempat disimpan sebagai dokumentasi. Wrap dihitung dari alat/metode referensi, bukan dari satu gambar ini.</p>}<p className="of-small of-muted">Ketidakpastian: Tidak tersedia. Simpan tiap sampel untuk menghitung median dan variasi dari minimal tiga hasil yang valid.</p></section>
    {!customerMode && (<div className="of-grid-two"><Field label="Alasan penandaan atau koreksi" required><select value={reason} onChange={e => setReason(e.target.value)} required><option value="">Pilih alasan</option>{REASONS.map(text => <option key={text}>{text}</option>)}</select></Field><Field label="Penjelasan koreksi"><input value={reasonDetail} onChange={e => setReasonDetail(e.target.value)} maxLength={1000} required={reason === "Alasan lain"} /></Field></div>)}
    {error && <Notice tone="danger">{error}</Notice>}<div className="of-actions"><Button variant="secondary" onClick={onClose} disabled={busy}>Batal</Button><Button onClick={save} busy={busy} disabled={!reason}><Save size={17} />Simpan sebagai revisi</Button></div>
  </Modal>;
}

export function computeCapture(capture, data) {
  const common = { ...capture, view: capture.view, calibration: capture.calibration, points: capture.points, confirmations: capture.confirmations, captureId: capture.id };
  const context = capture.measurementContext || measurementContext(data);
  const stale = capture.contextInvalidated || !sameMeasurementContext(context, measurementContext(data));
  const withContext = result => ({ ...result, measurementContext: context, ...(stale ? { valid: false, contextInvalidated: true, values: null, reasons: [...(result.reasons || []), "Konteks sesi berubah. Ambil ulang gambar pada konteks frame, referensi, dan jarak kerja yang baru."] } : {}) });
  if (capture.view === "frontal" || capture.view === "frontal_near") {
    const near = capture.view === "frontal_near";
    return { [near ? "near_pd" : "distance_pd"]: withContext(measurePD({ ...common, view: "frontal", gaze: near ? "near" : "distance", workingDistanceCm: context.workingDistanceCm, pdReference: context.frame.pdReference })) };
  }
  if (capture.view.startsWith("lateral_")) {
    const side = capture.view.endsWith("right") ? "right" : "left";
    return { [`vertex_${side}`]: withContext(measureVertex(common)), [`pantoscopic_${side}`]: withContext(measurePantoscopic(common)) };
  }
  return {};
}

export function aggregateCaptureResults(captures, previousResults = {}) {
  const results = { ...previousResults };
  const keys = [...new Set(captures.filter(c => !c.superseded).flatMap(c => Object.keys(c.measurements || {})))];
  for (const key of keys) {
    const seenPhotos = new Set();
    const sources = captures.filter(c => {
      if (c.superseded || c.contextInvalidated || !c.measurements?.[key]?.valid || !c.photoHash || seenPhotos.has(c.photoHash)) return false;
      seenPhotos.add(c.photoHash); return true;
    });
    if (!sources.length) { if (results[key]?.source === "camera") delete results[key]; continue; }
    const initial = sources[0].measurements[key];
    const signature = capture => {
      const result = capture.measurements[key];
      return JSON.stringify({ method: result.method, parameter: result.parameter, context: result.measurementContext || capture.measurementContext || null,
        referencePlane: String(capture.calibrationSpec?.referencePlane || capture.calibration?.referencePlane || "").trim().toLowerCase(),
        pdReference: result.values?.pdReference || null, workingDistanceCm: key === "near_pd" ? result.values?.workingDistanceCm : null,
        headPitchSource: key.startsWith("pantoscopic_") ? result.values?.headPitchSource || capture.headPitchSource || null : null });
    };
    const compatible = sources.every(capture => signature(capture) === signature(sources[0]));
    const fields = key.endsWith("_pd") ? ["rightMm", "leftMm"] : key.startsWith("vertex_") ? ["vertexMm"] : ["rawDeg", "headPitchDeg", "correctedDeg"];
    const repeated = Object.fromEntries(fields.map(field => [field, aggregateMeasurements(sources.map(c => c.measurements[key].values[field]))]));
    const mainKey = key.endsWith("_pd") ? "rightMm" : key.startsWith("vertex_") ? "vertexMm" : "correctedDeg";
    const repeatability = repeated[mainKey]; const enough = compatible && fields.every(field => repeated[field].valid);
    const values = { ...initial.values };
    fields.forEach(field => { if (repeated[field].valid) values[field] = repeated[field].median; });
    if (key.endsWith("_pd")) values.binocularMm = values.rightMm + values.leftMm;
    const confirmations = Object.fromEntries(QUALITY_CONFIRMATIONS.map(([name]) => [name, sources.every(c => c.confirmations?.[name] === true)]));
    const weakestCalibration = sources.every(c => c.calibration?.valid)
      ? (sources.find(c => c.calibration?.method === "frame") || sources[0]).calibration : { valid: false };
    const quality = assessQuality({ source: "camera", calibration: weakestCalibration, imageAnalyses: sources.map(c => c.analysis), confirmations, repeatability: enough ? repeatability : { ...repeatability, valid: false } });
    results[key] = { ...initial, valid: enough, source: "camera", values, quality, calibration: weakestCalibration, measurementContext: initial.measurementContext || sources[0].measurementContext || null,
      aggregationMethod: enough ? "componentwise_median" : "insufficient_compatible_samples",
      sourceMeasurements: sources.map(capture => ({ captureId: capture.id, photoHash: capture.photoHash, values: { ...capture.measurements[key].values } })),
      sourceCaptureIds: sources.map(c => c.id), sourcePhotoHashes: sources.map(c => c.photoHash), repeatability: { ...repeatability, valid: enough, sampleCount: sources.length, byField: repeated }, sampleCount: sources.length, reasons: [...(initial.reasons || []), ...(!compatible ? ["Sampel memakai metode, bidang, referensi PD, jarak kerja, atau sumber head pitch yang berbeda. Jangan gabungkan; ambil ulang dengan konteks yang sama."] : !enough ? ["Kurang dari tiga hasil valid; nilai sampel sementara dan perlu pengukuran ulang."] : [])], requiresReview: true };
  }
  return results;
}
