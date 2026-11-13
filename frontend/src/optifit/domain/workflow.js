/** Domain policy. Numerical fitting methods live separately in vision/. */
import { measurementContext, sameMeasurementContext } from './measurementContext';
export const STATUS_LABELS = Object.freeze({
  draft: 'Draft', needs_remeasure: 'Perlu diukur ulang',
  needs_verification: 'Perlu verifikasi manual', pending_review: 'Menunggu review', approved: 'Disetujui',
});
export const PARAMETER_LABELS = Object.freeze({
  distance_pd: 'Jarak Pupil Jauh', near_pd: 'Jarak Pupil Dekat',
  vertex_right: 'Vertex Distance Kanan', vertex_left: 'Vertex Distance Kiri',
  pantoscopic_right: 'Pantoscopic Tilt Kanan', pantoscopic_left: 'Pantoscopic Tilt Kiri',
  wrap_right: 'Wrap Angle Kanan', wrap_left: 'Wrap Angle Kiri',
});
export const DISCLAIMER = 'Hasil kamera merupakan alat bantu fitting dan harus diverifikasi tenaga optik atau profesional yang kompeten. Hasil berkualitas rendah tidak boleh digunakan sebagai hasil final. Aplikasi tidak menggantikan pemeriksaan refraksi atau pemeriksaan kesehatan mata. SPH, CYL, AXIS, dan ADD dicatat dari resep, bukan diukur kamera.';
export const QUALITY_NOTICE = 'Skor merupakan kualitas bukti teknik, bukan probabilitas benar atau klaim akurasi klinis. Ketidakpastian pengukuran: Tidak tersedia tanpa anggaran ketidakpastian yang tervalidasi.';

export function numberOrNull(value) {
  if (value === null || value === undefined || value === '') return null;
  if (typeof value === 'number') return Number.isFinite(value) ? value : NaN;
  const text = String(value).trim();
  if (!text) return null;
  if (!/^[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)$/.test(text)) return NaN;
  const n = Number(text.replace(',', '.'));
  return Number.isFinite(n) ? n : NaN;
}
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const finite = value => typeof value === 'number' && Number.isFinite(value);

export function validatePrescription(prescription = {}, { partial = true } = {}) {
  const errors = [];
  for (const [side, label] of [['od', 'Mata Kanan (OD)'], ['os', 'Mata Kiri (OS)']]) {
    const eye = prescription?.[side] || {};
    for (const key of ['sph', 'cyl', 'axis', 'add']) {
      const n = numberOrNull(eye[key]);
      if (n !== null && !Number.isFinite(n)) errors.push(`${label}: ${key.toUpperCase()} harus berupa angka.`);
    }
    const sph = numberOrNull(eye.sph), cyl = numberOrNull(eye.cyl), axis = numberOrNull(eye.axis);
    if (!partial && (sph === null || cyl === null)) errors.push(`${label}: SPH dan CYL harus diisi dari resep; isi 0 hanya jika memang tertulis plano/tanpa silinder.`);
    if (axis !== null && finite(axis) && (axis < 0 || axis > 180)) errors.push(`${label}: AXIS harus berada dalam 0–180 derajat.`);
    if (finite(cyl) && cyl !== 0 && (axis === null || axis < 1)) errors.push(`${label}: AXIS 1–180 diperlukan untuk CYL yang bukan nol.`);
  }
  return { valid: errors.length === 0, errors };
}

export function validateFrame(frame = {}, { partial = true } = {}) {
  const errors = [];
  for (const [key, label] of [['a', 'A'], ['b', 'B'], ['dbl', 'DBL'], ['ed', 'ED']]) {
    const n = numberOrNull(frame?.[key] ?? frame?.[`${key}Mm`]);
    if (n === null) { if (!partial && key !== 'ed') errors.push(`Ukuran frame ${label} wajib diisi dalam mm.`); }
    else if (!finite(n) || n <= 0) errors.push(`Ukuran ${label} harus berupa angka positif dalam mm.`);
  }
  return { valid: errors.length === 0, errors };
}

export function latestRevision(state, session) {
  if (!session) return null;
  const revisions = Array.isArray(state?.revisions) ? state.revisions : [];
  if (session.currentRevisionId) return revisions.find(r => r.id === session.currentRevisionId && r.sessionId === session.id) || null;
  return revisions.filter(r => r.sessionId === session.id).sort((a, b) => String(b.createdAt || '').localeCompare(String(a.createdAt || '')))[0] || null;
}
export function currentSessionData(state, session) {
  return latestRevision(state, session)?.data || session?.raw || {};
}

export function collectMeasurements(data = {}) {
  const results = {};
  for (const [key, value] of Object.entries(data.results || {})) {
    if (Object.hasOwn(PARAMETER_LABELS, key) && value && typeof value === 'object') results[key] = value;
  }
  // Imported early drafts may have a canonical manual map. Never infer a value
  // from a photo count, prescription, or another measurement.
  for (const [key, value] of Object.entries(data.manualMeasurements || {})) {
    if (!results[key] && Object.hasOwn(PARAMETER_LABELS, key) && value && typeof value === 'object') results[key] = value;
  }
  return results;
}

export function resultQuality(result) {
  const q = result?.quality || result?.confidence;
  if (!q || typeof q !== 'object') return null;
  const category = String(q.category || '').toLowerCase();
  const normalized = ({ tinggi: 'high', sedang: 'medium', rendah: 'low' })[category] || category;
  if (!['high', 'medium', 'low'].includes(normalized) || !finite(q.score) || q.score < 0 || q.score > 100) return null;
  return { ...q, category: normalized };
}
export function isCameraResult(result) {
  const method = String(result?.method || '').toLowerCase();
  return result?.source === 'camera' || method.includes('camera') || method.includes('marker') || method.includes('frame') || method.includes('photogram') || method.includes('homography') || method.startsWith('calibrated_') || method.startsWith('lateral_');
}

function validateResult(key, result) {
  const label = PARAMETER_LABELS[key];
  const errors = [];
  if (!result || result.valid !== true) return [`${label}: belum ada hasil valid dengan metode yang dapat ditelusuri.`];
  if (!nonempty(result.method)) errors.push(`${label}: metode belum dicatat.`);
  if (!nonempty(result.algorithmVersion)) errors.push(`${label}: versi algoritma belum dicatat.`);
  if (!resultQuality(result)) errors.push(`${label}: skor dan kategori kualitas belum lengkap.`);
  if (!result.values || typeof result.values !== 'object') errors.push(`${label}: nilai pengukuran belum tersedia.`);
  const values = result.values || {};
  if (key.endsWith('_pd')) {
    for (const part of ['rightMm', 'leftMm', 'binocularMm']) {
      if (!finite(values[part]) || values[part] <= 0) errors.push(`${label}: ${part} harus positif dan terukur.`);
    }
    if ([values.rightMm, values.leftMm, values.binocularMm].every(finite) && Math.abs(values.rightMm + values.leftMm - values.binocularMm) > 0.011) errors.push(`${label}: PD binocular harus sama dengan jumlah monocular; bukan dibagi rata.`);
    if (key === 'near_pd' && (!finite(values.workingDistanceCm) || values.workingDistanceCm <= 0)) errors.push('Jarak Pupil Dekat: jarak kerja belum dicatat.');
  } else if (key.startsWith('vertex_')) {
    const n = values.vertexMm ?? values.valueMm ?? values.value ?? (key.endsWith('_right') ? values.rightMm : values.leftMm);
    if (!finite(n) || n <= 0) errors.push(`${label}: nilai VD harus positif.`);
  } else {
    const n = values.correctedDeg ?? values.angleDeg ?? values.degrees ?? values.valueDeg ?? values.value;
    const sideValue = key.endsWith('_right') ? values.rightDeg : values.leftDeg;
    if (!finite(n) && !finite(sideValue)) errors.push(`${label}: nilai sudut belum tersedia.`);
    if (key.startsWith('wrap_') && !nonempty(result.referenceConvention || values.referenceConvention || values.angleReference || result.angleReference || result.convention)) errors.push(`${label}: konvensi referensi sudut wajib dicatat.`);
  }
  if (isCameraResult(result)) {
    if (result.calibration?.valid !== true || !['marker','frame'].includes(result.calibration.method) || !Array.isArray(result.calibration.matrix) || result.calibration.matrix.length !== 9 || !result.calibration.matrix.every(finite) || ['knownSize','fullyVisible','samePlane','clearEdges'].some(k => result.calibration.evidence?.[k] !== true)) errors.push(`${label}: kalibrasi valid dan bukti skala wajib tersedia.`);
    if (key.startsWith('wrap_')) errors.push('Rekonstruksi wrap kamera belum tersedia; gunakan pembacaan alat/metode referensi.');
    if (key.startsWith('pantoscopic_') && (!finite(values.rawDeg) || !finite(values.headPitchDeg) || !finite(values.correctedDeg) || !nonempty(values.headPitchSource))) errors.push(`${label}: sudut mentah, head pitch, sumbernya, dan sudut terkoreksi wajib tersedia.`);
    if (!Array.isArray(result.sourceCaptureIds) || !result.sourceCaptureIds.length) errors.push(`${label}: sumber gambar belum dihubungkan.`);
  } else if (!nonempty(result.instrumentReference || result.sourceReference || result.instrument)) {
    errors.push(`${label}: alat/metode referensi pengukuran manual belum dicatat.`);
  }
  return errors;
}

export function evaluateSubmission(data = {}, { session = {}, settings = {} } = {}) {
  const errors = [
    ...validatePrescription(data.prescription, { partial: false }).errors,
    ...validateFrame(data.frame, { partial: false }).errors,
  ];
  const warnings = [];
  const date = session.examinationDate || data.examinationDate;
  if (!nonempty(date) || !/^\d{4}-\d{2}-\d{2}/.test(date) || !Number.isFinite(Date.parse(date))) errors.push('Tanggal pemeriksaan belum valid.');
  const results = collectMeasurements(data);
  const required = Array.isArray(data.requiredParameters) && data.requiredParameters.length ? [...new Set(data.requiredParameters)] : ['distance_pd'];
  for (const key of required) {
    if (!Object.hasOwn(PARAMETER_LABELS, key)) errors.push('Lingkup pengukuran tidak dikenali.');
    else {
      const result = results[key]; errors.push(...validateResult(key, result));
      const context = measurementContext(data);
      if (result && (result.contextInvalidated || !sameMeasurementContext(result.measurementContext, context))) errors.push(`${PARAMETER_LABELS[key]}: konteks frame atau jarak kerja tidak sesuai; pengukuran harus diperbarui.`);
      if (result && isCameraResult(result)) {
        if (Array.isArray(settings.calibrationMethods) && !settings.calibrationMethods.includes(result.calibration?.method)) errors.push('Metode kalibrasi tidak diizinkan oleh konfigurasi administrator.');
        const expectedView = key === 'distance_pd' ? 'frontal' : key === 'near_pd' ? 'frontal_near' : key.endsWith('_right') ? 'lateral_right' : 'lateral_left';
        const captures = Array.isArray(data.captures) ? data.captures : [];
        for (const id of result.sourceCaptureIds || []) {
          const capture = captures.find(item => item.id === id);
          if (capture && Array.isArray(settings.calibrationMethods) && !settings.calibrationMethods.includes(capture.calibration?.method)) errors.push('Salah satu sampel memakai metode kalibrasi yang dinonaktifkan.');
          if (!capture || capture.view !== expectedView || capture.superseded || capture.contextInvalidated || !sameMeasurementContext(capture.measurementContext, context)) errors.push(`${PARAMETER_LABELS[key]}: sumber gambar aktif dari posisi dan konteks yang benar belum lengkap.`);
        }
        if (key === 'near_pd' && result.values?.workingDistanceCm !== numberOrNull(data.workingDistanceCm)) errors.push('Jarak kerja near PD berubah; lakukan perhitungan/pengukuran baru sesuai protokol.');
      }
    }
  }
  const selected = required.map(key => results[key]).filter(Boolean);
  const low = selected.some(result => resultQuality(result)?.category === 'low');
  const camera = selected.some(isCameraResult);
  if (low) warnings.push('Kualitas rendah: perlu verifikasi manual atau pengukuran ulang; persetujuan final diblokir.');
  if (camera) warnings.push('Estimasi kamera membutuhkan pembanding referensi dan reviewer independen; kalibrasi bidang tidak membuktikan akurasi klinis.');
  return { valid: errors.length === 0, errors, warnings, status: errors.length ? 'draft' : low ? 'needs_verification' : 'pending_review' };
}

export function evaluateReview({ session, revision, actor, decision, evidence = {}, settings = {} } = {}) {
  const reasons = [];
  if (!actor || !['admin', 'reviewer'].includes(actor.role) || actor.active === false) reasons.push('Review memerlukan akun reviewer atau admin yang aktif.');
  if (!session || !revision || revision.sessionId !== session.id || revision.id !== session.currentRevisionId) reasons.push('Revisi telah berubah; muat ulang hasil sebelum review.');
  if (!['pending_review', 'needs_verification'].includes(session?.status)) reasons.push('Sesi belum diajukan atau memerlukan revisi sebelum review.');
  if (actor?.id && [session?.createdBy, session?.operatorId, revision?.actorId, revision?.createdBy].filter(Boolean).includes(actor.id)) reasons.push('Reviewer harus berbeda dari operator/pembuat revisi.');
  if (!['approved', 'needs_remeasure', 'needs_verification'].includes(decision)) reasons.push('Keputusan review tidak dikenali.');
  if (decision === 'approved') {
    const data = revision?.data || session?.raw || {};
    const policy = evaluateSubmission(data, { session: session || {}, settings });
    reasons.push(...policy.errors);
    const results = collectMeasurements(data);
    const required = data.requiredParameters?.length ? data.requiredParameters : ['distance_pd'];
    const selected = required.map(key => results[key]).filter(Boolean);
    if (selected.some(result => resultQuality(result)?.category === 'low')) reasons.push('Hasil kualitas rendah harus diukur ulang atau diganti oleh revisi pengukuran referensi yang memadai.');
    if (evidence.professionalVerified !== true) reasons.push('Verifikasi profesional harus dikonfirmasi.');
    if (!nonempty(evidence.referenceInstrument)) reasons.push('Nama alat atau metode pembanding wajib dicatat.');
    if (!nonempty(evidence.protocolId)) reasons.push('Nomor protokol validasi/verifikasi wajib dicatat.');
    if (!nonempty(evidence.comparisonNotes)) reasons.push('Catatan perbandingan hasil dan dasar keputusan wajib dicatat.');
    if (selected.some(isCameraResult) && evidence.comparisonAccepted !== true) reasons.push('Pembandingan estimasi kamera dengan referensi belum dikonfirmasi.');
    for (const result of selected.filter(isCameraResult)) {
      const ids = Array.isArray(result.sourceCaptureIds) ? result.sourceCaptureIds : [];
      const hashes = Array.isArray(result.sourcePhotoHashes) ? result.sourcePhotoHashes : [];
      const captures = Array.isArray(data.captures) ? data.captures : [];
      const linked = ids.map(id => captures.find(c => c.id === id));
      if (new Set(ids).size < 3 || new Set(hashes).size < 3 || linked.some((c, i) => !c || c.photoHash !== hashes[i])) reasons.push('Hasil kamera memerlukan minimal tiga foto berbeda yang dapat ditelusuri pada revisi ini.');
      if (result.repeatability?.valid !== true || result.repeatability.sampleCount < 3 || result.repeatability.inlierCount < 3) reasons.push('Repeatability kamera belum didukung minimal tiga sampel valid.');
      const fields = Object.values(result.repeatability?.byField || {});
      if (!fields.length || fields.some(field => field?.valid !== true || field.inlierCount < 3)) reasons.push('Repeatability setiap komponen hasil kamera belum lengkap.');
    }
  }
  return { allowed: reasons.length === 0, reasons: [...new Set(reasons)] };
}

export function clinicalSnapshotForReport({ session, revision, data }) {
  if (!session?.id || !revision?.id || revision.sessionId !== session.id) throw new Error('Pilih sesi dan revisi yang valid untuk laporan.');
  if (data && data !== revision.data && JSON.stringify(data) !== JSON.stringify(revision.data)) throw new Error('Data laporan tidak cocok dengan revisi yang dipilih.');
  return revision.data || {};
}
