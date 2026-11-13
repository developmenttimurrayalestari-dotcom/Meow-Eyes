import { ALGORITHM_VERSION, finiteNumber } from './constants';

export const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
export const vector = (a, b) => ({ x: b.x - a.x, y: b.y - a.y });
export const dot = (a, b) => a.x * b.x + a.y * b.y;
export const cross = (a, b) => a.x * b.y - a.y * b.x;
export const magnitude = a => Math.hypot(a.x, a.y);
export const unit = a => { const size = magnitude(a); return size > 1e-10 ? { x: a.x / size, y: a.y / size } : null; };
export const isPoint = p => !!p && finiteNumber(p.x) && finiteNumber(p.y);

export function pointInImage(point, image, margin = 0) {
  return isPoint(point) && image && finiteNumber(image.width) && finiteNumber(image.height)
    && point.x >= margin && point.y >= margin
    && point.x < image.width - margin && point.y < image.height - margin;
}

// Gaussian elimination with partial pivoting. This is a planar coordinate
// transform, not a camera-pose or depth reconstruction algorithm.
function solveLinear(matrix, values) {
  const n = values.length;
  const rows = matrix.map((row, index) => [...row, values[index]]);
  for (let col = 0; col < n; col += 1) {
    let pivot = col;
    for (let row = col + 1; row < n; row += 1) {
      if (Math.abs(rows[row][col]) > Math.abs(rows[pivot][col])) pivot = row;
    }
    if (Math.abs(rows[pivot][col]) < 1e-10) return null;
    [rows[col], rows[pivot]] = [rows[pivot], rows[col]];
    const scale = rows[col][col];
    for (let k = col; k <= n; k += 1) rows[col][k] /= scale;
    for (let row = 0; row < n; row += 1) {
      if (row === col) continue;
      const factor = rows[row][col];
      for (let k = col; k <= n; k += 1) rows[row][k] -= factor * rows[col][k];
    }
  }
  const solution = rows.map(row => row[n]);
  return solution.every(finiteNumber) ? solution : null;
}

export function transformPoint(matrix, point) {
  if (!Array.isArray(matrix) || matrix.length !== 9 || !matrix.every(finiteNumber) || !isPoint(point)) return null;
  const denominator = matrix[6] * point.x + matrix[7] * point.y + matrix[8];
  if (Math.abs(denominator) < 1e-10) return null;
  const result = {
    x: (matrix[0] * point.x + matrix[1] * point.y + matrix[2]) / denominator,
    y: (matrix[3] * point.x + matrix[4] * point.y + matrix[5]) / denominator,
  };
  return isPoint(result) ? result : null;
}

export function homographyFromRectangle(corners, widthMm, heightMm, image) {
  const src = corners.map(point => ({ x: point.x / image.width, y: point.y / image.height }));
  const dst = [{ x: 0, y: 0 }, { x: widthMm, y: 0 }, { x: widthMm, y: heightMm }, { x: 0, y: heightMm }];
  const a = []; const b = [];
  src.forEach((point, index) => {
    const { x, y } = point; const { x: u, y: v } = dst[index];
    a.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
    a.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
  });
  const h = solveLinear(a, b);
  if (!h) return null;
  return [h[0] / image.width, h[1] / image.height, h[2],
    h[3] / image.width, h[4] / image.height, h[5],
    h[6] / image.width, h[7] / image.height, 1];
}

function invalidCalibration(input, reasons) {
  return { valid: false, matrix: null, method: input?.method || null, image: input?.image || null,
    unit: 'mm', reasons, limitations: [], algorithmVersion: ALGORITHM_VERSION };
}

export function createCalibration(input = {}) {
  if (!input || typeof input !== 'object') return invalidCalibration({}, ['Data kalibrasi harus berupa objek.']);
  const { method, image } = input;
  const evidence = input.evidence && typeof input.evidence === 'object' ? input.evidence : {};
  const reasons = [];
  if (!image || !Number.isInteger(image.width) || !Number.isInteger(image.height) || image.width < 16 || image.height < 16 || image.width * image.height > 24000000) {
    reasons.push('Dimensi gambar asli tidak valid.');
  }
  if (!['marker', 'frame'].includes(method)) reasons.push('Metode kalibrasi harus marker fisik atau referensi frame.');
  if (typeof input.referencePlane !== 'string' || !input.referencePlane.trim()) reasons.push('Catat bidang fisik marker/referensi yang benar-benar dipakai; bidang tidak boleh diasumsikan.');
  const required = {
    knownSize: 'Ukuran fisik referensi belum diketahui dan diperiksa.',
    fullyVisible: 'Referensi kalibrasi harus terlihat penuh, tidak terpotong.',
    samePlane: 'Bidang marker/referensi harus diperiksa terhadap bidang pengukuran; parallax belum diselesaikan.',
    clearEdges: 'Batas referensi belum dipastikan tajam dan jelas.',
  };
  Object.entries(required).forEach(([key, message]) => { if (evidence[key] !== true) reasons.push(message); });
  if (reasons.length) return invalidCalibration(input, reasons);
  let matrix; let geometry;
  if (method === 'marker') {
    const { corners, widthMm, heightMm } = input;
    if (!finiteNumber(widthMm) || !finiteNumber(heightMm) || widthMm <= 0 || heightMm <= 0) {
      return invalidCalibration(input, ['Lebar dan tinggi marker nyata harus lebih dari nol.']);
    }
    if (!Array.isArray(corners) || corners.length !== 4 || corners.some(p => !pointInImage(p, image, 1))) {
      return invalidCalibration(input, ['Tandai empat sudut marker utuh di dalam gambar: kiri atas, kanan atas, kanan bawah, kiri bawah.']);
    }
    const edges = corners.map((p, i) => vector(p, corners[(i + 1) % 4]));
    const lengths = edges.map(magnitude);
    const turns = edges.map((edge, index) => cross(edge, edges[(index + 1) % 4]));
    if (lengths.some(length => length < 4) || turns.some(turn => turn <= 0)) {
      return invalidCalibration(input, ['Urutan sudut terbalik, bersilangan, terlalu kecil, atau marker degenerat.']);
    }
    const minSine = Math.min(...turns.map((turn, i) => turn / (lengths[i] * lengths[(i + 1) % 4])));
    const perspectiveRatio = Math.max(lengths[0] / lengths[2], lengths[2] / lengths[0], lengths[1] / lengths[3], lengths[3] / lengths[1]);
    // Numerical geometry screening only; not a clinical accuracy tolerance.
    if (minSine < 0.15 || perspectiveRatio > 4) return invalidCalibration(input, ['Perspektif marker terlalu ekstrem untuk metode planar ini. Ambil ulang.']);
    matrix = homographyFromRectangle(corners, widthMm, heightMm, image);
    if (!matrix) return invalidCalibration(input, ['Kalibrasi tidak dapat diselesaikan: titik referensi tidak independen.']);
    const reprojection = corners.map((p, i) => {
      const projected = transformPoint(matrix, p);
      const target = [{ x: 0, y: 0 }, { x: widthMm, y: 0 }, { x: widthMm, y: heightMm }, { x: 0, y: heightMm }][i];
      return projected ? distance(projected, target) : Infinity;
    });
    if (Math.max(...reprojection) > 1e-6 * Math.max(widthMm, heightMm, 1)) return invalidCalibration(input, ['Transformasi marker tidak stabil secara numerik.']);
    geometry = { corners: corners.map(p => ({ ...p })), widthMm, heightMm, perspectiveRatio, minSine };
  } else {
    const { segment, lengthMm } = input;
    if (evidence.frontoparallel !== true) return invalidCalibration(input, ['Referensi frame hanya boleh digunakan setelah bidang frontal/paralel kamera diperiksa; satu segmen tidak mengoreksi perspektif.']);
    if (!finiteNumber(lengthMm) || lengthMm <= 0 || !Array.isArray(segment) || segment.length !== 2
      || segment.some(p => !pointInImage(p, image, 1)) || distance(segment[0], segment[1]) < 4) {
      return invalidCalibration(input, ['Pilih dua ujung bagian frame yang terukur dan masukkan panjang nyatanya dalam mm.']);
    }
    const [start, end] = segment; const dx = end.x - start.x; const dy = end.y - start.y;
    const factor = lengthMm / (dx * dx + dy * dy);
    matrix = [factor * dx, factor * dy, -factor * (dx * start.x + dy * start.y),
      -factor * dy, factor * dx, factor * (dy * start.x - dx * start.y), 0, 0, 1];
    geometry = { segment: segment.map(p => ({ ...p })), lengthMm, mmPerPixel: lengthMm / distance(start, end) };
  }
  return {
    valid: true, matrix, method, unit: 'mm', image: { ...image }, geometry,
    evidence: { ...evidence }, referencePlane: input.referencePlane.trim(),
    reasons: [], algorithmVersion: ALGORITHM_VERSION,
    limitations: [
      'Koordinat adalah proyeksi pada bidang kalibrasi. Perbedaan kedalaman pupil/lensa/marker dapat menyebabkan parallax.',
      'Distorsi optik kamera dan kedalaman belum dikoreksi karena intrinsics/depth tervalidasi tidak tersedia.',
      ...(method === 'frame' ? ['Referensi segmen frame tidak memperbaiki foreshortening atau geometri frame yang melengkung.'] : []),
    ],
  };
}

export function calibratedPoints(calibration, points, requiredKeys) {
  if (!calibration?.valid || !Array.isArray(calibration.matrix) || calibration.matrix.length !== 9 || !calibration.matrix.every(finiteNumber)) return { valid: false, reasons: ['Kalibrasi valid diperlukan sebelum menampilkan ukuran kamera.'] };
  const anchor = calibration.geometry?.corners?.[0] || calibration.geometry?.segment?.[0];
  if (!isPoint(anchor)) return { valid: false, reasons: ['Geometri sumber kalibrasi tidak tersedia. Kalibrasi ulang gambar asli.'] };
  const denominator = point => calibration.matrix[6] * point.x + calibration.matrix[7] * point.y + calibration.matrix[8];
  const anchorDenominator = denominator(anchor);
  if (!finiteNumber(anchorDenominator) || Math.abs(anchorDenominator) < 1e-10) return { valid: false, reasons: ['Bidang kalibrasi berada pada singularitas transformasi. Ambil ulang gambar.'] };
  const converted = {};
  for (const key of requiredKeys) {
    if (!pointInImage(points?.[key], calibration.image)) return { valid: false, reasons: [`Titik ${key} belum valid pada koordinat gambar asli.`] };
    const pointDenominator = denominator(points[key]);
    if (!finiteNumber(pointDenominator) || Math.abs(pointDenominator) < 1e-10 || Math.sign(pointDenominator) !== Math.sign(anchorDenominator)) return { valid: false, reasons: ['Titik melewati horizon/singularitas bidang marker. Transformasi tidak dapat diekstrapolasi ke titik tersebut; ambil ulang.'] };
    converted[key] = transformPoint(calibration.matrix, points[key]);
    if (!converted[key]) return { valid: false, reasons: ['Titik berada pada singularitas transformasi. Ambil ulang gambar.'] };
  }
  return { valid: true, points: converted, reasons: [] };
}
