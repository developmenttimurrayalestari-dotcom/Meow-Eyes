import { STATUS_LABELS, PARAMETER_LABELS, DISCLAIMER, QUALITY_NOTICE, clinicalSnapshotForReport, collectMeasurements, resultQuality, evaluateReview, numberOrNull } from '../domain/workflow';

const text = value => value === null || value === undefined || value === '' ? 'Tidak tersedia' : String(value);
const escapeHTML = value => text(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
const safeName = value => String(value || 'laporan').replace(/[^A-Za-z0-9_-]+/g, '-').slice(0, 96);
const numeric = value => typeof value === 'number' && Number.isFinite(value) ? new Intl.NumberFormat('id-ID', { maximumFractionDigits: 2 }).format(value) : text(value);
const omitImageKeys = /^(blob|imageBlob|imageData|photoBytes|dataUrl|thumbnail|photoDataUrl|profilePhoto)$/i;
function cleanData(value) {
  if (typeof value === 'string' && /^data:image\//i.test(value.trim())) return undefined;
  if (value === null || typeof value !== 'object') return typeof value === 'number' && !Number.isFinite(value) ? null : value;
  if (value instanceof ArrayBuffer || (typeof Blob !== 'undefined' && value instanceof Blob) || ArrayBuffer.isView(value)) return undefined;
  if (Array.isArray(value)) return value.map(cleanData).filter(item => item !== undefined);
  return Object.fromEntries(Object.entries(value).filter(([key]) => !omitImageKeys.test(key)).map(([key, val]) => [key, cleanData(val)]).filter(([, val]) => val !== undefined));
}

export function buildReportSnapshot(options = {}) {
  const { patient, session, revision, data, organization = {}, operator = {}, reviewer = {}, review = null, includePhotos = false, photoConsentConfirmed = false, confirmed = false } = options;
  if (!confirmed) throw new Error('Konfirmasi ekspor data pasien diperlukan.');
  if (!patient?.id || patient.id !== session?.patientId) throw new Error('Pasien dan sesi laporan tidak cocok.');
  const clinical = clinicalSnapshotForReport({ session, revision, data });
  if (includePhotos && (photoConsentConfirmed !== true || clinical.consents?.thumbnail !== true)) throw new Error('Persetujuan khusus menyertakan foto pada laporan diperlukan.');
  const matchingReview = review?.revisionId === revision.id ? review : null;
  // Validate the stored receipt against its historical revision. This creates
  // a read-only policy input; it never changes a vault status or grants approval.
  const approved = matchingReview?.decision === 'approved' && evaluateReview({session:{...session,currentRevisionId:revision.id,status:'pending_review'},revision,actor:{id:matchingReview.reviewerId,role:'reviewer'},decision:'approved',evidence:matchingReview.evidence || {}}).allowed;
  let reportClinical = cleanData(clinical);
  const scope = clinical.requiredParameters?.length ? clinical.requiredParameters : ['distance_pd'];
  const excludedParameters = Object.keys(collectMeasurements(clinical)).filter(key => !scope.includes(key));
  if (approved) {
    const scopedResults = cleanData(Object.fromEntries(Object.entries(collectMeasurements(clinical)).filter(([key]) => scope.includes(key))));
    const usedCaptures = new Set(Object.values(scopedResults).flatMap(result => result.sourceCaptureIds || []));
    reportClinical = { prescription:reportClinical.prescription, frame:reportClinical.frame, notes:reportClinical.notes, requiredParameters:scope, workingDistanceCm:reportClinical.workingDistanceCm, results:scopedResults, captures:(reportClinical.captures || []).filter(c=>usedCaptures.has(c.id)).map(c=>({...c,measurements:Object.fromEntries(Object.entries(c.measurements || {}).filter(([key])=>scope.includes(key)))})) };
  }
  const reportStatus = approved ? 'approved' : (revision.id === session.currentRevisionId ? (session.status === 'approved' ? 'needs_verification' : session.status) : 'draft');
  const patientFields = ['id', 'recordNumber', 'fullName', 'examinationDate', 'birthDate', 'sex', 'gender', 'phone', 'address', 'email', 'occupation', 'complaint', 'notes', 'customerId'];
  const patientData = Object.fromEntries(patientFields.filter(key => patient[key] !== undefined).map(key => [key, cleanData(patient[key])]));
  return {
    schemaVersion: 1, product: 'Meowsurement', reportNumber: `OF-${safeName(session.id).slice(-16)}-${safeName(revision.id).slice(-8)}`,
    exportedAt: new Date().toISOString(), organization: { name: organization.name || 'Meow Eyes', branch: organization.branch || '', address: organization.address || '' },
    patient: patientData, examinationDate: session.examinationDate, sessionId: session.id, revisionId: revision.id,
    status: reportStatus || 'draft', statusLabel: STATUS_LABELS[reportStatus] || 'Draft', historicalRevision: revision.id !== session.currentRevisionId,
    operator: { id: operator.id || revision.actorId || session.createdBy, name: revision.actorName || session.operatorName || operator.displayName || operator.name || operator.fullName || 'Tidak tersedia' },
    reviewer: matchingReview ? { id: matchingReview.reviewerId || matchingReview.actorId || reviewer.id, name: matchingReview.reviewerName || reviewer.displayName || reviewer.name || reviewer.fullName || 'Tidak tersedia', decision: matchingReview.decision, note: matchingReview.note, evidence: cleanData(matchingReview.evidence), reviewedAt: matchingReview.createdAt } : null,
    algorithmVersion: revision.algorithmVersion || clinical.algorithmVersion || session.algorithmVersion || 'Tidak tersedia', device: cleanData(session.device || {}),
    requiredParameters: scope, approvalScope: approved ? scope : [], excludedUnreviewedParameters: approved ? excludedParameters : [], clinical: reportClinical,
    photoIncluded: includePhotos, disclaimer: DISCLAIMER, qualityNotice: QUALITY_NOTICE,
  };
}

function repeatabilityText(repeatability, unit) {
  const describe = r => r?.valid === true
    ? `Sampel valid ${text(r.validCount ?? r.sampleCount ?? r.count)}; inlier ${text(r.inlierCount)}; median ${numeric(r.median)} ${unit}; SD sampel ${numeric(r.sampleStdDev)} ${unit}; outlier ${(r.outlierIndices || []).length}.`
    : 'Sampel valid belum cukup; ringkasan repeatability belum tersedia.';
  const components = repeatability.byField || repeatability.bySide;
  const labels = {right:'OD',left:'OS',rightMm:'OD',leftMm:'OS',binocularMm:'Binocular',vertexMm:'VD',offAxisMm:'Deviasi tegak lurus',rawDeg:'Sudut mentah',headPitchDeg:'Head pitch',correctedDeg:'Sudut terkoreksi'};
  return components ? Object.entries(components).map(([name,r]) => `${labels[name] || name}: ${describe(r)}`).join('\n') : describe(repeatability);
}

function measurementRows(key, result) {
  const label = PARAMETER_LABELS[key], v = result?.values || {}, q = resultQuality(result);
  if (!result || result.valid !== true) return [[label, 'Tidak tersedia / hasil belum valid']];
  const rows = [];
  if (key.endsWith('_pd')) {
    rows.push([`${label} kanan`, `${numeric(v.rightMm)} mm`], [`${label} kiri`, `${numeric(v.leftMm)} mm`], [`${label} binocular`, `${numeric(v.binocularMm)} mm`]);
    rows.push(['Referensi garis tengah PD', ({frame_bridge:'Garis tengah bridge frame',facial_midline:'Garis tengah wajah'})[v.pdReference] || 'Tidak tersedia']);
    if (key === 'near_pd') rows.push(['Jarak kerja dekat', `${numeric(v.workingDistanceCm)} cm`]);
  } else if (key.startsWith('vertex_')) {
    rows.push([label, `${numeric(v.vertexMm ?? v.valueMm ?? (key.endsWith('_right') ? v.rightMm : v.leftMm))} mm`]);
    if (Number.isFinite(v.offAxisMm)) rows.push(['Deviasi tegak lurus arah pandang (diagnostik)', `${numeric(v.offAxisMm)} mm; periksa pemilihan titik, bukan ambang kelulusan otomatis.`]);
  }
  else rows.push([label, `${numeric(v.correctedDeg ?? v.angleDeg ?? v.degrees ?? (key.endsWith('_right') ? v.rightDeg : v.leftDeg))} derajat`]);
  if (key.startsWith('pantoscopic_')) rows.push(['Sudut sebelum koreksi', text(v.rawDeg === undefined ? null : `${numeric(v.rawDeg)} derajat`)], ['Head pitch', text(v.headPitchDeg === undefined ? null : `${numeric(v.headPitchDeg)} derajat; ${text(v.headPitchSource)}`)], ['Konvensi tanda', v.signConvention || 'Positif: bagian bawah lensa lebih dekat ke wajah.']);
  if (key.startsWith('pantoscopic_') && result.source === 'camera' && result.sampleCount > 1) rows.push(['Ringkasan sampel', 'Setiap komponen merupakan median sampel. Selisih median sudut mentah dan median head pitch tidak harus sama dengan median sudut terkoreksi; triple asli tersimpan per gambar.']);
  if (key.startsWith('wrap_')) rows.push(['Referensi wrap', result.referenceConvention || v.referenceConvention || v.angleReference || result.angleReference || result.convention || result.referencePlane]);
  rows.push(['Metode', result.method], ['Alat/referensi', result.instrumentReference || result.referencePlane || 'Tidak tersedia'], ['Kualitas teknik', q ? `${q.score}/100 - ${q.label || ({ high: 'Tinggi', medium: 'Sedang', low: 'Rendah' })[q.category]}` : 'Tidak tersedia'], ['Ketidakpastian', result.uncertainty ? JSON.stringify(result.uncertainty) : 'Tidak tersedia']);
  if (result.reasons?.length || q?.reasons?.length || result.limitations?.length) rows.push(['Keterangan kualitas', [...(result.reasons || []), ...(q?.reasons || []), ...(result.limitations || [])].join(' ') ]);
  if (result.repeatability) rows.push(['Repeatability (bukan akurasi)', repeatabilityText(result.repeatability, key.endsWith('_pd') || key.startsWith('vertex_') ? 'mm' : 'derajat')]);
  rows.push(['Versi / sumber', `${text(result.algorithmVersion)}; ${(result.sourceCaptureIds || []).join(', ') || text(result.captureId)}`]);
  return rows;
}

export function reportSections(snapshot) {
  const p = snapshot.patient, d = snapshot.clinical, rx = d.prescription || {}, f = d.frame || {}, results = collectMeasurements(d);
  const pd = results.distance_pd?.valid ? results.distance_pd.values : {};
  const a = numberOrNull(f.a), dbl = numberOrNull(f.dbl), frameKnown = f.a !== '' && f.dbl !== '' && Number.isFinite(a) && Number.isFinite(dbl) && a > 0 && dbl > 0;
  const framePD = frameKnown ? a + dbl : null;
  const bridge = pd.pdReference === 'frame_bridge' && f.symmetric === true;
  const sections = [
    { title: 'Identitas pemeriksaan', rows: [['Nomor laporan', snapshot.reportNumber], ['Status', `${snapshot.statusLabel}${snapshot.historicalRevision ? ' (revisi historis)' : ''}`], ['Nomor rekam', p.recordNumber], ['Nama pasien', p.fullName], ['Tanggal pemeriksaan', snapshot.examinationDate], ['Tanggal lahir', p.birthDate], ['Kontak', [p.phone, p.email].filter(Boolean).join(' / ')], ['Keluhan / catatan pasien', [p.complaint, p.notes].filter(Boolean).join(' | ')]] },
    { title: 'Resep dicatat dari pemeriksaan profesional', rows: [['Mata Kanan (OD)', ['sph', 'cyl', 'axis', 'add'].map(k => `${k.toUpperCase()}: ${numeric(rx.od?.[k])}`).join(' | ')], ['Mata Kiri (OS)', ['sph', 'cyl', 'axis', 'add'].map(k => `${k.toUpperCase()}: ${numeric(rx.os?.[k])}`).join(' | ')], ['Catatan resep', rx.notes || 'Tidak ada'], ['Sumber', 'Input resep. Tidak ditentukan oleh kamera.']] },
    { title: 'Frame dan perhitungan turunan', rows: [['Frame', [f.brand, f.model].filter(Boolean).join(' / ')], ['A / B / DBL / ED', `A ${numeric(f.a)}; B ${numeric(f.b)}; DBL ${numeric(f.dbl)}; ED ${numeric(f.ed)} mm`], ['Frame PD (A + DBL)', framePD === null ? 'Tidak tersedia' : `${numeric(framePD)} mm`], ['Decentration OD', frameKnown && bridge && Number.isFinite(pd.rightMm) ? `${numeric(framePD / 2 - pd.rightMm)} mm` : 'Tidak tersedia: memerlukan PD dengan referensi bridge'], ['Decentration OS', frameKnown && bridge && Number.isFinite(pd.leftMm) ? `${numeric(framePD / 2 - pd.leftMm)} mm` : 'Tidak tersedia: memerlukan PD dengan referensi bridge'], ['Konvensi decentration', 'Positif ke nasal. Mengasumsikan ukuran A kanan/kiri sama; tidak memaksakan PD kanan/kiri simetris.']] },
  ];
  for (const key of Object.keys(PARAMETER_LABELS)) sections.push({ title: PARAMETER_LABELS[key], rows: snapshot.status === 'approved' && !snapshot.requiredParameters.includes(key) ? [[PARAMETER_LABELS[key], 'Di luar lingkup persetujuan; nilai tidak dimasukkan ke laporan final.']] : measurementRows(key, results[key]) });
  const captures = Array.isArray(d.captures) ? d.captures : [];
  sections.push({ title: 'Kalibrasi dan jejak pengukuran', rows: [['Lingkup diminta', snapshot.requiredParameters.map(k => PARAMETER_LABELS[k] || k).join(', ')], ['Kalibrasi per view', captures.length ? captures.map(c => `${c.view}: ${c.calibrationSpec?.method || c.calibration?.method || 'belum tersedia'}; ${c.calibrationSpec?.widthMm || c.calibrationSpec?.lengthMm || '-'} mm; ${c.id}`).join('\n') : 'Tanpa foto; lihat metode instrumen pada hasil'], ['Operator', snapshot.operator.name], ['Reviewer', snapshot.reviewer?.name], ['Review / bukti', snapshot.reviewer ? [snapshot.reviewer.note, snapshot.reviewer.evidence?.referenceInstrument, snapshot.reviewer.evidence?.protocolId, snapshot.reviewer.evidence?.comparisonNotes].filter(Boolean).join('\n') : 'Belum direview'], ['Versi algoritma', snapshot.algorithmVersion], ['Perangkat', Object.keys(snapshot.device).length ? JSON.stringify(snapshot.device) : 'Tidak tersedia'], ['Catatan operator', d.notes || 'Tidak ada'], ['Revisi / waktu ekspor', `${snapshot.revisionId}\n${snapshot.exportedAt}`]] });
  sections.push({ title: 'Batas penggunaan', rows: [['Pernyataan', DISCLAIMER], ['Kualitas', QUALITY_NOTICE], ['Format angka', 'Angka ditampilkan hingga dua desimal untuk keterbacaan. Banyaknya desimal bukan klaim ketelitian klinis.'], ['Privasi', snapshot.photoIncluded ? 'Thumbnail disertakan berdasarkan konfirmasi khusus.' : 'Foto wajah tidak disertakan.']] });
  return sections;
}

export function serializeCSV(snapshot) {
  const cell = value => {
    let s = text(value);
    // Protect spreadsheet consumers from formula execution in free text.
    if (/^[\s]*[=+\-@\t\r]/.test(s)) s = "'" + s;
    return '"' + s.replace(/"/g, '""') + '"';
  };
  const rows = [['Bagian', 'Parameter', 'Nilai'], ...reportSections(snapshot).flatMap(section => section.rows.map(([label, value]) => [section.title, label, value]))];
  return '\ufeff' + rows.map(row => row.map(cell).join(',')).join('\r\n') + '\r\n';
}
export function renderPrintHTML(snapshot) {
  const sections = reportSections(snapshot).map(s => `<section><h2>${escapeHTML(s.title)}</h2><table>${s.rows.map(([label, value]) => `<tr><th>${escapeHTML(label)}</th><td>${escapeHTML(value)}</td></tr>`).join('')}</table></section>`).join('');
  return `<!doctype html><html lang="id"><head><meta charset="utf-8"><title>${escapeHTML(snapshot.reportNumber)}</title><meta name="referrer" content="no-referrer"><style>@page{size:A4;margin:16mm}body{font:11pt system-ui,sans-serif;color:#14352f}h1{font-size:20pt;margin:0}h2{font-size:13pt;border-bottom:1px solid #8ab6a7;padding-bottom:5pt;break-after:avoid}header{border-bottom:3px solid #176b5b;padding-bottom:12pt}section{margin-top:14pt}table{border-collapse:collapse;width:100%;font-size:9pt}tr{break-inside:avoid}th,td{vertical-align:top;text-align:left;padding:5pt;border-bottom:1px solid #dde8e2;white-space:pre-wrap;overflow-wrap:anywhere}th{width:30%;background:#f2f7f5}.status{font-weight:700;color:${snapshot.status === 'approved' ? '#176b5b' : '#994a08'}}p{line-height:1.5}</style></head><body><header><h1>${escapeHTML(snapshot.organization.name)}</h1><p>Meowsurement | ${escapeHTML(snapshot.organization.branch)}</p><div class="status">${escapeHTML(snapshot.statusLabel)} | ${escapeHTML(snapshot.reportNumber)}</div></header>${sections}</body></html>`;
}

const bytesToBase64 = bytes => {
  let out = ''; for (let i = 0; i < bytes.length; i += 0x8000) out += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(out);
};
async function staticBytes(path) {
  const response = await fetch(path, { credentials: 'omit', cache: 'force-cache' });
  if (!response.ok) throw new Error('Aset laporan belum tersedia. Selesaikan pemasangan offline saat terhubung internet.');
  return new Uint8Array(await response.arrayBuffer());
}
async function pdfReport(snapshot, options) {
  const { jsPDF } = await import('jspdf');
  const regular = options.assets?.regularFont || await staticBytes('/meowsurement/fonts/DejaVuSans.ttf');
  const bold = options.assets?.boldFont || await staticBytes('/meowsurement/fonts/DejaVuSans-Bold.ttf');
  const doc = new jsPDF({ unit: 'mm', format: 'a4', compress: true, putOnlyUsedFonts: true });
  doc.addFileToVFS('DejaVuSans.ttf', bytesToBase64(regular)); doc.addFont('DejaVuSans.ttf', 'OptiFit', 'normal');
  doc.addFileToVFS('DejaVuSans-Bold.ttf', bytesToBase64(bold)); doc.addFont('DejaVuSans-Bold.ttf', 'OptiFit', 'bold');
  doc.setProperties({ title: snapshot.reportNumber, subject: 'Laporan fitting - data pribadi', creator: 'Meowsurement', author: snapshot.organization.name });
  const margin = 16, width = 178, bottom = 278; let y = 17;
  const font = (size = 9, style = 'normal') => { doc.setFont('OptiFit', style); doc.setFontSize(size); doc.setTextColor(20, 53, 47); };
  const page = () => { doc.addPage(); y = 16; font(8, 'bold'); doc.text('Meowsurement | ' + snapshot.reportNumber, margin, y); y += 9; };
  let logo = options.organization?.logoDataUrl;
  if (!logo) { try { logo = 'data:image/jpeg;base64,' + bytesToBase64(options.assets?.logo || await staticBytes('/logo-meow.jpg')); } catch { logo = null; } }
  if (logo && /^data:image\/(png|jpeg);base64,/.test(logo) && logo.length < 1500000) { try { doc.addImage(logo, logo.startsWith('data:image/png') ? 'PNG' : 'JPEG', margin, y - 2, 14, 14); } catch { logo = null; } }
  font(17, 'bold'); const orgLines = doc.splitTextToSize(snapshot.organization.name, logo ? 157 : width); doc.text(orgLines, logo ? margin + 19 : margin, y + 4); y += Math.max(16, orgLines.length * 7 + 5);
  font(11, 'bold'); doc.text('Meowsurement', margin, y); y += 7;
  font(9); doc.text(snapshot.statusLabel + (snapshot.historicalRevision ? ' - revisi historis' : '') + ' | ' + snapshot.reportNumber, margin, y); y += 7;
  doc.setDrawColor(23, 107, 91); doc.setLineWidth(0.7); doc.line(margin, y, margin + width, y); y += 7;
  const row = (label, value) => {
    font(8.5); const lines = doc.splitTextToSize(text(value), 119); let pending = lines.length ? lines : ['Tidak tersedia']; let continuation = false;
    while (pending.length) {
      if (y + 13 > bottom) page();
      font(8, 'bold'); const left = doc.splitTextToSize(text(label) + (continuation ? ' (lanjutan)' : ''), 46);
      const available = Math.max(left.length, Math.floor((bottom - y - 5) / 4.3));
      const chunk = pending.slice(0, available); pending = pending.slice(available);
      const height = Math.max(left.length, chunk.length) * 4.3 + 4;
      if (y + height > bottom && y > 28) { page(); pending = [...chunk, ...pending]; continue; }
      doc.setFillColor(242, 247, 245); doc.rect(margin, y, 52, height, 'F');
      font(8, 'bold'); doc.text(left, margin + 2, y + 4);
      font(8.5); doc.text(chunk, margin + 55, y + 4);
      doc.setDrawColor(221, 232, 226); doc.setLineWidth(0.15); doc.line(margin, y + height, margin + width, y + height);
      y += height; continuation = true;
    }
  };
  for (const section of reportSections(snapshot)) {
    if (y + 25 > bottom) page();
    font(11, 'bold'); const heading = doc.splitTextToSize(section.title, width); doc.text(heading, margin, y + 4); y += 6 + heading.length * 4.3;
    for (const [label, value] of section.rows) row(label, value);
    y += 5;
  }
  if (options.includePhotos) {
    const photos = Array.isArray(options.photos) ? options.photos.slice(0, 6) : [];
    if (photos.length) {
      if (y + 60 > bottom) page(); font(11, 'bold'); doc.text('Thumbnail dengan persetujuan', margin, y + 4); y += 10;
      for (const photo of photos) {
        if (!/^data:image\/(png|jpeg);base64,/.test(photo.dataUrl || '') || photo.dataUrl.length > 12000000) throw new Error('Thumbnail harus JPEG/PNG lokal yang valid.');
        if (y + 51 > bottom) page();
        const props = doc.getImageProperties(photo.dataUrl); const h = Math.min(42, 65 * props.height / props.width), w = h * props.width / props.height;
        doc.addImage(photo.dataUrl, photo.dataUrl.startsWith('data:image/png') ? 'PNG' : 'JPEG', margin, y, Math.min(65, w), h); y += h + 4;
        font(8); doc.text(text(photo.label || photo.view || 'Foto fitting'), margin, y); y += 8;
      }
    }
  }
  const count = doc.getNumberOfPages();
  for (let n = 1; n <= count; n++) { doc.setPage(n); font(7); doc.setTextColor(90); doc.text(`${snapshot.reportNumber} | Data pribadi | ${snapshot.statusLabel}`, margin, 287); doc.text(`${n} / ${count}`, 194, 287, { align: 'right' }); }
  return doc.output('blob');
}

export function validateReportPhotos(options, clinical) {
  if (!options.includePhotos) return [];
  if (options.photoConsentConfirmed !== true || clinical?.consents?.thumbnail !== true) throw new Error('Persetujuan thumbnail pada revisi dan konfirmasi ekspor wajib tersedia.');
  const photos = options.photos || [];
  if (!Array.isArray(photos) || photos.length < 1 || photos.length > 3) throw new Error('Pilih satu sampai tiga thumbnail yang tersedia.');
  const allowed = new Set((clinical.captures || []).map(c=>c.photoId).filter(Boolean));
  const ids = new Set();
  for (const photo of photos) {
    const id = photo.photoId || photo.id;
    if (!id || !allowed.has(id) || ids.has(id)) throw new Error('Thumbnail harus berasal dari foto unik milik revisi ini.');
    ids.add(id);
    const source = photo.dataUrl || '';
    if (typeof source !== 'string' || source.length > 12000000 || !/^data:image\/(png|jpeg);base64,[A-Za-z0-9+/]+={0,2}$/.test(source)) throw new Error('Thumbnail harus berupa JPEG/PNG lokal yang valid.');
    let bytes; try { bytes = atob(source.split(',')[1]); } catch { throw new Error('Encoding thumbnail tidak valid.'); }
    if (bytes.length > 8*1024*1024) throw new Error('Thumbnail melebihi batas berkas.');
    const jpeg = source.startsWith('data:image/jpeg') && bytes.charCodeAt(0)===255 && bytes.charCodeAt(1)===216 && bytes.charCodeAt(2)===255;
    const png = source.startsWith('data:image/png') && [137,80,78,71,13,10,26,10].every((n,i)=>bytes.charCodeAt(i)===n);
    if (!jpeg && !png) throw new Error('Isi thumbnail tidak sesuai format gambar.');
  }
  return photos;
}

export async function generateReport(options = {}) {
  const format = options.format || 'pdf';
  if (options.includePhotos && !['pdf', 'json'].includes(format)) throw new Error('Thumbnail hanya dapat disertakan pada PDF atau JSON.');
  const snapshot = buildReportSnapshot(options);
  const photos = validateReportPhotos(options, options.revision.data);
  options = { ...options, photos };
  const base = safeName(snapshot.reportNumber); let blob, mimeType, html;
  if (format === 'pdf') { blob = await pdfReport(snapshot, options); mimeType = 'application/pdf'; }
  else if (format === 'csv') { mimeType = 'text/csv;charset=utf-8'; blob = new Blob([serializeCSV(snapshot)], { type: mimeType }); }
  else if (format === 'json') { mimeType = 'application/json'; const body = { ...snapshot }; if (options.includePhotos) body.thumbnails = (options.photos || []).map(p => ({ label: p.label || p.view, dataUrl: p.dataUrl })); blob = new Blob([JSON.stringify(body, null, 2)], { type: mimeType }); }
  else if (format === 'print') { mimeType = 'text/html;charset=utf-8'; html = renderPrintHTML(snapshot); blob = new Blob([html], { type: mimeType }); }
  else throw new Error('Format laporan tidak didukung.');
  return { blob, filename: base + (format === 'print' ? '.html' : '.' + format), mimeType, html, reportNumber: snapshot.reportNumber, status: snapshot.status, revisionId: snapshot.revisionId };
}
const reportUrls = new Set();
export function downloadReport(result) {
  if (!(result?.blob instanceof Blob)) throw new Error('Berkas laporan belum dibuat.');
  const url = URL.createObjectURL(result.blob); reportUrls.add(url);
  const link = document.createElement('a'); link.href = url; link.download = result.filename; link.rel = 'noopener'; document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => { URL.revokeObjectURL(url); reportUrls.delete(url); }, 30000);
}
export function printReport(result) {
  if (!result?.html) throw new Error('Tampilan cetak belum dibuat.');
  const frame = document.createElement('iframe'); frame.title = 'Laporan untuk dicetak'; frame.setAttribute('sandbox', 'allow-same-origin allow-modals'); frame.dataset.optifitPrint = 'true'; frame.style.cssText = 'position:fixed;width:0;height:0;border:0;';
  frame.onload = () => { frame.contentWindow.onafterprint = () => frame.remove(); frame.contentWindow.focus(); frame.contentWindow.print(); };
  frame.srcdoc = result.html; document.body.appendChild(frame); setTimeout(() => frame.remove(), 120000);
}
export function clearReportResources() { reportUrls.forEach(url => URL.revokeObjectURL(url)); reportUrls.clear(); document.querySelectorAll('[data-optifit-print]').forEach(el => el.remove()); }
