import { ALGORITHM_VERSION, finiteNumber, reasonResult } from './constants';
import { calibratedPoints, vector, dot, cross, unit } from './geometry';

const result = (parameter, unitName, values, input, method) => ({
  valid: true, parameter, unit: unitName, values, reasons: [], method,
  captureId: input.captureId || null, sourceCaptureIds: input.captureId ? [input.captureId] : [], algorithmVersion: ALGORITHM_VERSION,
  uncertainty: null, requiresReview: true, clinicallyValidated: false,
  referencePlane: input.calibration?.referencePlane || null,
  limitations: input.calibration?.limitations || [],
});

function confirmed(input, keys) {
  return keys.filter(key => input.confirmations?.[key] !== true).map(key => `Konfirmasi operator belum lengkap: ${key}.`);
}

export function measurePD(input = {}) {
  if (!input || typeof input !== 'object') return reasonResult('pd_distance', ['Input pengukuran tidak valid.'], { unit: 'mm' });
  const parameter = input.gaze === 'near' ? 'pd_near' : 'pd_distance';
  const reasons = confirmed(input, ['gazeCorrect', 'landmarksConfirmed', 'headPoseAcceptable']);
  if (input.view !== 'frontal') reasons.push('PD kamera memerlukan foto frontal.');
  if (!['distance', 'near'].includes(input.gaze)) reasons.push('Pilih protokol target jauh atau target dekat.');
  if (input.gaze === 'near' && (!finiteNumber(input.workingDistanceCm) || input.workingDistanceCm <= 0)) reasons.push('Jarak kerja target dekat wajib dicatat dalam cm.');
  const converted = calibratedPoints(input.calibration, input.points, ['rightPupil', 'leftPupil', 'midlineTop', 'midlineBottom']);
  if (!converted.valid) reasons.push(...converted.reasons);
  if (reasons.length) return reasonResult(parameter, reasons, { unit: 'mm' });
  const p = converted.points;
  const vertical = unit(vector(p.midlineTop, p.midlineBottom));
  if (!vertical) return reasonResult(parameter, ['Garis tengah referensi harus mempunyai dua titik berbeda.'], { unit: 'mm' });
  const horizontal = { x: vertical.y, y: -vertical.x };
  const rightSigned = dot(vector(p.midlineTop, p.rightPupil), horizontal);
  const leftSigned = dot(vector(p.midlineTop, p.leftPupil), horizontal);
  if (rightSigned * leftSigned >= 0) return reasonResult(parameter, ['Garis tengah harus berada di antara pusat pupil kanan dan kiri.'], { unit: 'mm' });
  const rightMm = Math.abs(rightSigned); const leftMm = Math.abs(leftSigned);
  return result(parameter, 'mm', {
    rightMm, leftMm, binocularMm: rightMm + leftMm,
    workingDistanceCm: input.gaze === 'near' ? input.workingDistanceCm : null,
    referenceRollDeg: Math.atan2(vertical.x, vertical.y) * 180 / Math.PI,
    pdReference: input.pdReference || 'frame_bridge',
  }, input, 'calibrated_planar_pd');
}

export function measureVertex(input = {}) {
  if (!input || typeof input !== 'object') return reasonResult('vertex', ['Input pengukuran tidak valid.'], { unit: 'mm' });
  const reasons = confirmed(input, ['surfaceVisible', 'landmarksConfirmed', 'headPoseAcceptable']);
  if (!['lateral_right', 'lateral_left'].includes(input.view)) reasons.push('Vertex Distance memerlukan foto lateral masing-masing sisi, bukan foto frontal.');
  const converted = calibratedPoints(input.calibration, input.points, ['cornea', 'backLens', 'gazeStart', 'gazeEnd']);
  if (!converted.valid) reasons.push(...converted.reasons);
  if (reasons.length) return reasonResult('vertex', reasons, { unit: 'mm' });
  const p = converted.points; const gaze = unit(vector(p.gazeStart, p.gazeEnd));
  if (!gaze) return reasonResult('vertex', ['Arah pandang/referensi harus mempunyai panjang yang bukan nol.'], { unit: 'mm' });
  const delta = vector(p.cornea, p.backLens); const vertexMm = dot(delta, gaze);
  if (vertexMm <= 0) return reasonResult('vertex', ['Titik permukaan belakang lensa harus berada di depan apex kornea menurut arah pandang yang ditandai.'], { unit: 'mm' });
  const output = result('vertex', 'mm', {
    side: input.view === 'lateral_right' ? 'right' : 'left', vertexMm,
    offAxisMm: Math.abs(cross(delta, gaze)),
  }, input, 'lateral_gaze_projection');
  output.limitations = [...output.limitations, 'Pastikan titik permukaan belakang lensa merupakan titik yang sesuai arah pandang. Rim depan frame bukan pengganti permukaan belakang lensa. Nilai off-axis ditampilkan untuk pemeriksaan operator.'];
  return output;
}

export function measurePantoscopic(input = {}) {
  if (!input || typeof input !== 'object') return reasonResult('pantoscopic', ['Input pengukuran tidak valid.'], { unit: 'deg' });
  const reasons = confirmed(input, ['verticalReferenceConfirmed', 'landmarksConfirmed', 'headPoseAcceptable']);
  if (!['lateral_right', 'lateral_left'].includes(input.view)) reasons.push('Pantoscopic tilt memerlukan foto lateral.');
  if (!['left', 'right'].includes(input.inwardDirection)) reasons.push('Pilih arah menuju wajah pada foto untuk konvensi tanda.');
  if (!finiteNumber(input.headPitchDeg) || Math.abs(input.headPitchDeg) >= 90) reasons.push('Head pitch terukur wajib diberikan, bukan diasumsikan nol.');
  if (!['instrument', 'manual_reference', 'operator_reference'].includes(input.headPitchSource)) reasons.push('Catat sumber head pitch dari alat atau referensi manual; estimasi otomatis belum tersedia.');
  const converted = calibratedPoints(input.calibration, input.points, ['lensTop', 'lensBottom', 'verticalTop', 'verticalBottom']);
  if (!converted.valid) reasons.push(...converted.reasons);
  if (reasons.length) return reasonResult('pantoscopic', reasons, { unit: 'deg' });
  const p = converted.points; const lens = unit(vector(p.lensTop, p.lensBottom)); const vertical = unit(vector(p.verticalTop, p.verticalBottom));
  if (!lens || !vertical) return reasonResult('pantoscopic', ['Garis lensa dan garis vertikal harus mempunyai panjang yang bukan nol.'], { unit: 'deg' });
  const signed = Math.atan2(cross(vertical, lens), dot(vertical, lens)) * 180 / Math.PI;
  const rawDeg = signed * (input.inwardDirection === 'left' ? 1 : -1);
  if (Math.abs(rawDeg) >= 90) return reasonResult('pantoscopic', ['Periksa urutan atas/bawah dan arah vertikal; sudut garis tidak sesuai tampilan lateral.'], { unit: 'deg' });
  if (Math.abs(rawDeg - input.headPitchDeg) >= 90) return reasonResult('pantoscopic', ['Sudut terkoreksi tidak sesuai definisi pantoscopic. Periksa head pitch, sumber referensi dan konvensi tanda.'], { unit: 'deg' });
  const output = result('pantoscopic', 'deg', {
    side: input.view === 'lateral_right' ? 'right' : 'left', rawDeg,
    headPitchDeg: input.headPitchDeg, correctedDeg: rawDeg - input.headPitchDeg,
    headPitchSource: input.headPitchSource,
    signConvention: 'Positif: bagian bawah lensa lebih dekat ke wajah. Head pitch positif: kontribusi kepala menunduk.',
  }, input, 'lateral_plane_angle_manual_pitch');
  return output;
}

export function frameDerived(input = {}) {
  if (!input || typeof input !== 'object') return { valid: false, reasons: ['Data frame tidak valid.'], values: null };
  const reasons = [];
  ['aMm', 'dblMm'].forEach(key => {
    if (!finiteNumber(input[key]) || input[key] <= 0) reasons.push(`${key} harus berupa ukuran positif dalam mm.`);
  });
  ['bMm', 'edMm'].forEach(key => {
    if (input[key] !== null && input[key] !== undefined && input[key] !== '' && (!finiteNumber(input[key]) || input[key] <= 0)) reasons.push(`${key} harus berupa ukuran positif dalam mm bila diisi.`);
  });
  if (reasons.length) return { valid: false, reasons, values: null };
  const framePdMm = input.aMm + input.dblMm;
  const values = { framePdMm, totalDecentrationMm: null, rightDecentrationMm: null, leftDecentrationMm: null, asymmetryMm: null };
  const hasPds = finiteNumber(input.rightPdMm) && finiteNumber(input.leftPdMm) && input.rightPdMm > 0 && input.leftPdMm > 0;
  if (hasPds && input.pdReference === 'frame_bridge') {
    values.rightDecentrationMm = framePdMm / 2 - input.rightPdMm;
    values.leftDecentrationMm = framePdMm / 2 - input.leftPdMm;
    values.totalDecentrationMm = framePdMm - input.rightPdMm - input.leftPdMm;
    values.asymmetryMm = Math.abs(input.rightPdMm - input.leftPdMm);
  }
  const warnings = [];
  if (hasPds && input.pdReference !== 'frame_bridge') warnings.push('Decentration belum dihitung: monocular PD harus memakai garis tengah bridge frame yang sama.');
  if (hasPds && finiteNumber(input.asymmetryThresholdMm) && input.asymmetryThresholdMm >= 0
    && Math.abs(input.rightPdMm - input.leftPdMm) > input.asymmetryThresholdMm) warnings.push('Perbedaan monocular PD melebihi ambang organisasi; periksa ulang tanpa memaksakan simetri.');
  if (finiteNumber(input.edMm) && input.edMm < Math.max(input.aMm, input.bMm || 0)) warnings.push('ED lebih kecil daripada A/B; periksa kembali data boxing frame.');
  return { valid: true, values, ...values, reasons: [], warnings,
    signConvention: 'Decentration positif = ke nasal; negatif = ke temporal.',
    assumption: 'Kedua lens box memakai ukuran A yang sama dan bridge frame merupakan referensi centration.' };
}

export function validatePrescription(input = {}) {
  if (!input || typeof input !== 'object') return { valid: false, errors: ['Data resep tidak valid.'], reasons: ['Data resep tidak valid.'] };
  const errors = [];
  if (!finiteNumber(input.sph)) errors.push('SPH wajib berupa angka dari resep.');
  if (!finiteNumber(input.cyl)) errors.push('CYL wajib berupa angka dari resep; gunakan 0 bila memang tertulis plano/sferis.');
  if (finiteNumber(input.cyl) && input.cyl !== 0 && (!finiteNumber(input.axis) || input.axis < 1 || input.axis > 180)) errors.push('AXIS wajib antara 1–180° ketika CYL bukan nol.');
  if (input.axis !== null && input.axis !== undefined && input.axis !== '' && (!finiteNumber(input.axis) || input.axis < 0 || input.axis > 180)) errors.push('AXIS tidak valid.');
  if (input.add !== null && input.add !== undefined && input.add !== '' && !finiteNumber(input.add)) errors.push('ADD harus berupa angka atau dikosongkan.');
  return { valid: errors.length === 0, errors, reasons: errors };
}

export function transposePrescription(input = {}) {
  const validation = validatePrescription(input);
  if (!validation.valid) return { valid: false, reasons: validation.reasons, original: { ...input }, transposed: null };
  const transposed = {
    ...input, sph: Number((input.sph + input.cyl).toFixed(8)), cyl: input.cyl === 0 ? 0 : -input.cyl,
    axis: input.cyl === 0 ? (input.axis || null) : ((input.axis + 89) % 180) + 1,
  };
  return { valid: true, reasons: [], original: { ...input }, transposed,
    formula: 'S′ = S + C; C′ = −C; AXIS′ = AXIS ± 90° (1–180°).',
    note: 'Perubahan notasi ekuivalen. Resep asli tetap disimpan; bukan kompensasi posisi pemakaian.' };
}

export function recordManualMeasurement(input = {}) {
  if (!input || typeof input !== 'object') return reasonResult('manual', ['Input pengukuran tidak valid.']);
  const allowed = ['wrap', 'vertex', 'pantoscopic', 'pd_distance', 'pd_near'];
  const reasons = [];
  if (!allowed.includes(input.parameter)) reasons.push('Jenis pengukuran manual tidak dikenal.');
  if (input.operatorConfirmed !== true) reasons.push('Operator harus mengonfirmasi pembacaan alat.');
  if (typeof input.instrumentReference !== 'string' || !input.instrumentReference.trim()) reasons.push('Nama/identitas alat dan referensi metode wajib dicatat.');
  const values = input.values || {};
  const right = values.right ?? values.rightMm ?? values.rightDeg;
  const left = values.left ?? values.leftMm ?? values.leftDeg;
  if (!finiteNumber(right) || !finiteNumber(left)) reasons.push('Nilai kanan dan kiri wajib dicatat secara independen.');
  if (['vertex', 'pd_distance', 'pd_near'].includes(input.parameter) && (right <= 0 || left <= 0)) reasons.push('Ukuran dalam mm harus lebih dari nol.');
  if (['wrap', 'pantoscopic'].includes(input.parameter) && (Math.abs(right) >= 90 || Math.abs(left) >= 90)) reasons.push('Sudut harus berada di antara −90° dan 90°; periksa konvensi tanda alat.');
  if (input.parameter === 'pd_near' && (!finiteNumber(input.workingDistanceCm) || input.workingDistanceCm <= 0)) reasons.push('Jarak kerja near PD wajib dicatat.');
  if (input.parameter === 'wrap' && (typeof input.angleReference !== 'string' || !input.angleReference.trim())) reasons.push('Referensi bidang dan konvensi wrap angle wajib dicatat.');
  if (reasons.length) return reasonResult(input.parameter, reasons);
  const unitName = ['wrap', 'pantoscopic'].includes(input.parameter) ? 'deg' : 'mm';
  const outputValues = { right, left };
  if (unitName === 'mm') { outputValues.rightMm = right; outputValues.leftMm = left; }
  else { outputValues.rightDeg = right; outputValues.leftDeg = left; }
  if (input.parameter.startsWith('pd_')) { outputValues.binocularMm = right + left; outputValues.workingDistanceCm = input.parameter === 'pd_near' ? input.workingDistanceCm : null; }
  if (input.parameter === 'vertex') outputValues.meanMm = (right + left) / 2;
  if (input.parameter === 'wrap') { outputValues.totalDeg = right + left; outputValues.meanDeg = (right + left) / 2; outputValues.angleReference = input.angleReference; }
  const output = result(input.parameter, unitName, outputValues, input, 'manual_instrument');
  output.instrumentReference = input.instrumentReference.trim();
  output.referencePlane = input.referencePlane || input.angleReference || null;
  return output;
}
