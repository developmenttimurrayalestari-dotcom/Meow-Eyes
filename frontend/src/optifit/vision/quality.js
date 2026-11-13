import { ALGORITHM_VERSION, finiteNumber } from './constants';

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const medianOf = numbers => { const sorted = [...numbers].sort((a, b) => a - b); const half = Math.floor(sorted.length / 2); return sorted.length % 2 ? sorted[half] : (sorted[half - 1] + sorted[half]) / 2; };

function validImage(image) {
  return image && Number.isInteger(image.width) && Number.isInteger(image.height)
    && image.width >= 4 && image.height >= 4 && image.width * image.height <= 24000000
    && image.data?.length === image.width * image.height * 4;
}

// Screen image usability only. These defaults are adjustable engineering
// thresholds, not a camera/clinical accuracy model or a medical acceptance limit.
export const IMAGE_SCREENING = Object.freeze({ laplacianMinimum: 25, minimumLuminance: 45, maximumLuminance: 215, maximumClippedFraction: 0.35 });

export function analyseImage(image, policy = IMAGE_SCREENING) {
  if (!validImage(image)) return { valid: false, score: 0, reasons: ['Data gambar RGBA tidak valid atau melebihi 24 MP.'], unknown: [] };
  const { width: sourceWidth, height: sourceHeight, data } = image;
  // Use a common analysis resolution. Full-resolution imported photos and a
  // camera thumbnail must not silently apply the same blur threshold at very
  // different pixel scales. This does not resize stored/annotated image data.
  const scale = Math.min(1, 320 / Math.max(sourceWidth, sourceHeight));
  const width = Math.max(4, Math.round(sourceWidth * scale));
  const height = Math.max(4, Math.round(sourceHeight * scale));
  const count = width * height;
  const screening = { ...IMAGE_SCREENING };
  Object.keys(screening).forEach(key => { if (finiteNumber(policy?.[key]) && policy[key] > 0) screening[key] = policy[key]; });
  const gray = new Float32Array(count); let sum = 0; let sumSquare = 0; let dark = 0; let bright = 0;
  for (let i = 0; i < count; i += 1) {
    const x = i % width; const y = Math.floor(i / width);
    const sx0 = Math.floor(x * sourceWidth / width); const sx1 = Math.max(sx0 + 1, Math.floor((x + 1) * sourceWidth / width));
    const sy0 = Math.floor(y * sourceHeight / height); const sy1 = Math.max(sy0 + 1, Math.floor((y + 1) * sourceHeight / height));
    let localSum = 0; let localCount = 0;
    for (let sy = sy0; sy < sy1; sy += 1) for (let sx = sx0; sx < sx1; sx += 1) {
      const offset = 4 * (sy * sourceWidth + sx);
      localSum += 0.2126 * data[offset] + 0.7152 * data[offset + 1] + 0.0722 * data[offset + 2]; localCount += 1;
    }
    const value = localSum / localCount;
    gray[i] = value; sum += value; sumSquare += value * value;
    if (value < 12) dark += 1;
    if (value > 243) bright += 1;
  }
  let lapSum = 0; let lapSquare = 0; let lapCount = 0;
  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const i = y * width + x; const value = 4 * gray[i] - gray[i - 1] - gray[i + 1] - gray[i - width] - gray[i + width];
      lapSum += value; lapSquare += value * value; lapCount += 1;
    }
  }
  const meanLuminance = sum / count;
  const laplacianVariance = Math.max(0, lapSquare / lapCount - (lapSum / lapCount) ** 2);
  const darkFraction = dark / count; const brightFraction = bright / count;
  const sharpness = laplacianVariance >= screening.laplacianMinimum ? 'usable' : 'low';
  const exposure = meanLuminance < screening.minimumLuminance ? 'low' : meanLuminance > screening.maximumLuminance ? 'high' : 'usable';
  const reasons = [];
  if (sharpness === 'low') reasons.push('Detail gambar rendah/buram menurut skrining Laplacian; periksa pupil dan marker.');
  if (exposure === 'low') reasons.push('Pencahayaan terlalu rendah.');
  if (exposure === 'high') reasons.push('Pencahayaan terlalu tinggi.');
  if (Math.max(darkFraction, brightFraction) > screening.maximumClippedFraction) reasons.push('Banyak area kehilangan detail pada bayangan atau sorotan.');
  const signature = [];
  for (let y = 0; y < 12; y += 1) for (let x = 0; x < 16; x += 1) {
    signature.push(Math.round(gray[Math.min(height - 1, Math.floor((y + 0.5) * height / 12)) * width + Math.min(width - 1, Math.floor((x + 0.5) * width / 16))]));
  }
  const score = Math.round(100 * (
    0.45 * clamp(laplacianVariance / Math.max(screening.laplacianMinimum, 1), 0, 1)
    + 0.35 * (exposure === 'usable' ? 1 : 0)
    + 0.2 * (1 - clamp(Math.max(darkFraction, brightFraction), 0, 1))));
  return {
    valid: true, width: sourceWidth, height: sourceHeight, analysisWidth: width, analysisHeight: height, meanLuminance, stdLuminance: Math.sqrt(Math.max(0, sumSquare / count - meanLuminance ** 2)),
    laplacianVariance, darkFraction, brightFraction, sharpness, exposure, score, reasons, signature,
    usable: reasons.length === 0, policy: screening,
    unknown: ['headPose', 'cameraDistance', 'blink', 'pupilOcclusion', 'frameClipping', 'opticalReflections'],
    algorithmVersion: ALGORITHM_VERSION,
  };
}
export const analyzeImage = analyseImage;

export function rankBurstSamples(samples = []) {
  if (!Array.isArray(samples)) return { valid: false, selectedIndices: [], rows: [], reasons: ['Rangkaian gambar tidak valid.'] };
  const rows = samples.map((sample, index) => {
    const analysis = sample?.analysis || sample || {};
    const previous = samples[index - 1]?.analysis || samples[index - 1];
    const currentSignature = analysis.signature || [];
    const previousSignature = previous?.signature || [];
    const frameDifference = currentSignature.length && currentSignature.length === previousSignature.length
      ? currentSignature.reduce((sum, value, i) => sum + Math.abs(value - previousSignature[i]), 0) / currentSignature.length / 255 : null;
    return { index, analysis, frameDifference,
      selectionScore: analysis.valid ? (analysis.score || 0) + Math.log1p(analysis.laplacianVariance || 0) - (frameDifference || 0) * 20 : -Infinity };
  });
  const ranked = rows.filter(row => row.analysis.valid).sort((a, b) => b.selectionScore - a.selectionScore || a.index - b.index);
  return {
    valid: ranked.length >= 3, selectedIndices: ranked.slice(0, 3).map(row => row.index),
    rows: rows.map(({ index, analysis, frameDifference, selectionScore }) => ({ index, analysis, frameDifference, selectionScore: finiteNumber(selectionScore) ? selectionScore : null })),
    reasons: ranked.length >= 3 ? [] : ['Diperlukan setidaknya tiga frame dengan data gambar yang valid.'],
    note: 'Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.',
  };
}

function otsuThreshold(histogram, total) {
  let totalSum = 0; for (let i = 0; i < 256; i += 1) totalSum += i * histogram[i];
  let weightBackground = 0; let sumBackground = 0; let best = -1; let threshold = 0;
  for (let i = 0; i < 256; i += 1) {
    weightBackground += histogram[i]; if (!weightBackground) continue;
    const weightForeground = total - weightBackground; if (!weightForeground) break;
    sumBackground += i * histogram[i];
    const meanDifference = sumBackground / weightBackground - (totalSum - sumBackground) / weightForeground;
    const variance = weightBackground * weightForeground * meanDifference * meanDifference;
    if (variance > best) { best = variance; threshold = i; }
  }
  return threshold;
}

// Candidate detector intentionally needs an operator-selected eye ROI. It
// classifies dark image components, not anatomical pupil truth. The operator
// must confirm/correct the result; no iris diameter or population PD is assumed.
export function suggestPupil(image, roi = {}) {
  const failed = reason => ({ found: false, candidate: null, candidates: [], requiresConfirmation: true, reasons: [reason], algorithmVersion: ALGORITHM_VERSION });
  if (!validImage(image)) return failed('Gambar tidak valid.');
  if (!roi || typeof roi !== 'object') return failed('Area mata tidak valid.');
  if (![roi.x, roi.y, roi.width, roi.height].every(finiteNumber) || roi.width < 8 || roi.height < 8) return failed('Pilih area satu mata yang cukup jelas.');
  const x0 = clamp(Math.floor(roi.x), 0, image.width - 1); const y0 = clamp(Math.floor(roi.y), 0, image.height - 1);
  const width = Math.min(Math.floor(roi.width), image.width - x0); const height = Math.min(Math.floor(roi.height), image.height - y0);
  if (width * height > image.width * image.height / 2 || width < 8 || height < 8) return failed('Area terlalu luas/kecil; batasi pada satu mata.');
  const size = width * height; const gray = new Uint8Array(size); const histogram = new Uint32Array(256);
  let minimum = 255; let maximum = 0;
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const source = ((y0 + y) * image.width + x0 + x) * 4;
    const value = Math.round(0.2126 * image.data[source] + 0.7152 * image.data[source + 1] + 0.0722 * image.data[source + 2]);
    gray[y * width + x] = value; histogram[value] += 1; minimum = Math.min(minimum, value); maximum = Math.max(maximum, value);
  }
  if (maximum - minimum < 18) return failed('Kontras area mata terlalu rendah untuk kandidat otomatis.');
  const threshold = otsuThreshold(histogram, size); const visited = new Uint8Array(size); const queue = new Int32Array(size); const candidates = [];
  for (let start = 0; start < size; start += 1) {
    if (visited[start] || gray[start] > threshold) continue;
    let head = 0; let tail = 1; queue[0] = start; visited[start] = 1;
    let area = 0; let weightedX = 0; let weightedY = 0; let weightSum = 0; let perimeter = 0;
    let minX = width; let maxX = 0; let minY = height; let maxY = 0; let touchesBorder = false;
    while (head < tail) {
      const index = queue[head++]; const x = index % width; const y = Math.floor(index / width); const weight = threshold + 1 - gray[index];
      area += 1; weightSum += weight; weightedX += x * weight; weightedY += y * weight;
      minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y);
      if (x === 0 || y === 0 || x === width - 1 || y === height - 1) touchesBorder = true;
      const neighbours = [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]];
      neighbours.forEach(([nx, ny]) => {
        if (nx < 0 || ny < 0 || nx >= width || ny >= height) { perimeter += 1; return; }
        const next = ny * width + nx;
        if (gray[next] > threshold) { perimeter += 1; return; }
        if (!visited[next]) { visited[next] = 1; queue[tail++] = next; }
      });
    }
    const boxWidth = maxX - minX + 1; const boxHeight = maxY - minY + 1; const aspect = boxWidth / boxHeight;
    if (touchesBorder || area < 4 || area > size * 0.4 || aspect < 0.35 || aspect > 2.8) continue;
    const x = weightedX / weightSum; const y = weightedY / weightSum;
    const circularity = perimeter ? Math.min(1, 4 * Math.PI * area / (perimeter * perimeter)) : 0;
    const centrality = 1 - Math.min(1, Math.hypot((x - width / 2) / width, (y - height / 2) / height));
    candidates.push({ x: x + x0, y: y + y0, areaPixels: area, circularity, box: { x: minX + x0, y: minY + y0, width: boxWidth, height: boxHeight }, rank: 0.7 * circularity + 0.3 * centrality });
  }
  candidates.sort((a, b) => b.rank - a.rank || b.areaPixels - a.areaPixels);
  if (!candidates.length) return failed('Tidak ada kandidat pupil yang memadai. Tandai pusat pupil secara manual.');
  return { found: true, candidate: { x: candidates[0].x, y: candidates[0].y }, candidates: candidates.slice(0, 5),
    requiresConfirmation: true, reasons: ['Kandidat area gelap belum membuktikan pusat pupil; periksa refleksi, iris, bulu mata dan posisi titik.'], threshold, algorithmVersion: ALGORITHM_VERSION };
}

export function aggregateMeasurements(samples = []) {
  if (!Array.isArray(samples)) return { valid: false, count: 0, inlierCount: 0, median: null, sampleStdDev: null, uncertainty: null, samples: [], outlierIndices: [], reasons: ['Daftar sampel pengukuran tidak valid.'], requiresReview: true };
  const validSamples = samples.map((value, index) => ({ value, index })).filter(row => finiteNumber(row.value));
  const values = validSamples.map(row => row.value);
  const base = { count: samples.length, validCount: values.length, samples: [...samples], uncertainty: null, requiresReview: true, algorithmVersion: ALGORITHM_VERSION };
  if (values.length < 3) return { ...base, valid: false, inlierCount: values.length, median: null, mad: null, sampleStdDev: null, min: null, max: null, outlierIndices: [], reasons: ['Setidaknya tiga hasil independen diperlukan untuk ringkasan repeatability.'] };
  const centre = medianOf(values); const mad = medianOf(values.map(value => Math.abs(value - centre)));
  // No invented noise floor when MAD=0. Keep every sample, expose range/SD.
  const outlierIndices = mad > 1e-12 ? validSamples.filter(row => 0.67448975 * Math.abs(row.value - centre) / mad > 3.5).map(row => row.index) : [];
  const inliers = validSamples.filter(row => !outlierIndices.includes(row.index)).map(row => row.value);
  const mean = inliers.reduce((sum, value) => sum + value, 0) / inliers.length;
  const sampleStdDev = inliers.length > 1 ? Math.sqrt(inliers.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (inliers.length - 1)) : null;
  return { ...base, valid: inliers.length >= 3, inlierCount: inliers.length, median: medianOf(inliers), mad,
    sampleStdDev, min: Math.min(...inliers), max: Math.max(...inliers), outlierIndices,
    reasons: inliers.length >= 3 ? [] : ['Terlalu sedikit hasil tersisa setelah penolakan outlier. Ukur ulang.'],
    note: 'SD sampel menunjukkan repeatability kumpulan ini, bukan ketidakpastian klinis atau akurasi terhadap alat referensi.' };
}

const QUALITY_CHECKS = Object.freeze([
  ['landmarksConfirmed', 'Landmark belum dikonfirmasi operator.'],
  ['frameVisible', 'Frame belum dipastikan terlihat penuh.'],
  ['pupilsVisible', 'Pupil/referensi mata belum dipastikan terlihat.'],
  ['noReflections', 'Refleksi pada area ukur belum diperiksa.'],
  ['gazeCorrect', 'Arah pandang belum sesuai protokol.'],
  ['headPoseAcceptable', 'Posisi kepala belum diperiksa.'],
  ['distanceAppropriate', 'Jarak kamera belum diperiksa secara manual.'],
  ['scaleConsistent', 'Konsistensi skala beberapa frame belum diperiksa.'],
]);

export function assessQuality(input = {}) {
  if (!input || typeof input !== 'object') return { score: 0, category: 'low', label: 'Rendah', reasons: ['Bukti kualitas belum tersedia.'], uncertainty: null, kind: 'engineering_evidence', requiresReview: true, clinicallyValidated: false };
  const manual = input.source === 'manual_instrument'; const reasons = [];
  let achieved = 0; let possible = 0;
  const components = [];
  const check = (name, passed, weight, reason) => {
    possible += weight; if (passed) achieved += weight; else reasons.push(reason);
    components.push({ name, passed: !!passed, weight });
  };
  if (manual) {
    check('instrument', !!String(input.instrumentReference || '').trim(), 3, 'Identitas alat/metode referensi belum dicatat.');
    check('reading', input.confirmations?.landmarksConfirmed === true || input.confirmations?.readingConfirmed === true, 3, 'Pembacaan alat belum dikonfirmasi.');
    check('repeatability', input.repeatability?.valid === true, 2, 'Belum ada tiga pengulangan valid untuk nilai ini.');
    check('protocol', input.confirmations?.gazeCorrect === true && input.confirmations?.headPoseAcceptable === true, 2, 'Protokol pandang/posisi belum dikonfirmasi.');
  } else {
    check('calibration', input.calibration?.valid === true, 3, 'Kalibrasi belum valid.');
    check('marker', input.calibration?.method === 'marker', 1, 'Kalibrasi frame lebih bergantung pada asumsi bidang/perspektif daripada marker fisik.');
    const analyses = Array.isArray(input.imageAnalyses) ? input.imageAnalyses : [];
    check('imageQuality', analyses.length >= 1 && analyses.every(a => a?.valid && a.sharpness === 'usable' && a.exposure === 'usable'), 2, 'Ketajaman/pencahayaan belum memenuhi skrining gambar.');
    QUALITY_CHECKS.forEach(([key, reason]) => check(key, input.confirmations?.[key] === true, 1, reason));
    check('repeatability', input.repeatability?.valid === true, 2, 'Belum ada tiga hasil ukur valid yang dianotasi independen.');
    reasons.push('Protokol kamera belum divalidasi terhadap alat referensi; skor kamera dibatasi sebagai kualitas teknis sementara.');
  }
  let score = possible ? Math.round(achieved / possible * 100) : 0;
  if (!manual) score = Math.min(score, 69);
  if (!manual && input.calibration?.valid !== true) score = 0;
  const category = score >= 80 ? 'high' : score >= 50 ? 'medium' : 'low';
  return { score, category, label: { high: 'Tinggi', medium: 'Sedang', low: 'Rendah' }[category], reasons,
    components, kind: 'engineering_evidence', uncertainty: null, requiresReview: true,
    clinicallyValidated: false, algorithmVersion: ALGORITHM_VERSION,
    explanation: 'Skor mengikuti kelengkapan bukti dan pemeriksaan teknis; bukan persentase ketepatan pengukuran. Ambang kategori bukan target akurasi klinis.' };
}
