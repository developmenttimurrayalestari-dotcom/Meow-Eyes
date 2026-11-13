import {
  createCalibration, transformPoint, measurePD, measureVertex, measurePantoscopic,
  frameDerived, transposePrescription, validatePrescription, recordManualMeasurement,
  analyseImage, suggestPupil, rankBurstSamples, aggregateMeasurements, assessQuality, CAPABILITIES,
} from './index';

const evidence = { knownSize: true, fullyVisible: true, samePlane: true, clearEdges: true, frontoparallel: true };
const marker = (overrides = {}) => createCalibration({ method: 'marker', image: { width: 300, height: 200 },
  corners: [{ x: 10, y: 10 }, { x: 110, y: 10 }, { x: 110, y: 110 }, { x: 10, y: 110 }], widthMm: 10, heightMm: 10, evidence, referencePlane: 'Synthetic test plane', ...overrides });
const pdInput = () => ({ calibration: marker(), view: 'frontal', gaze: 'distance',
  points: { rightPupil: { x: 40, y: 60 }, leftPupil: { x: 110, y: 60 }, midlineTop: { x: 70, y: 20 }, midlineBottom: { x: 70, y: 100 } },
  confirmations: { gazeCorrect: true, landmarksConfirmed: true, headPoseAcceptable: true } });

test('known rectangular scale and projective corners map to physical coordinates', () => {
  const calibration = marker(); expect(calibration.valid).toBe(true);
  const centre = transformPoint(calibration.matrix, { x: 60, y: 60 });
  expect(centre.x).toBeCloseTo(5, 8); expect(centre.y).toBeCloseTo(5, 8);
  const corners = [{ x: 40, y: 30 }, { x: 240, y: 45 }, { x: 220, y: 180 }, { x: 55, y: 150 }];
  const perspective = marker({ corners, widthMm: 40, heightMm: 30 });
  expect(perspective.valid).toBe(true);
  [[0, 0], [40, 0], [40, 30], [0, 30]].forEach(([x, y], i) => {
    const mapped = transformPoint(perspective.matrix, corners[i]); expect(mapped.x).toBeCloseTo(x, 7); expect(mapped.y).toBeCloseTo(y, 7);
  });
  expect(perspective.limitations.join(' ')).toMatch(/parallax/);
});

test.each(['knownSize', 'fullyVisible', 'samePlane', 'clearEdges'])('calibration rejects missing %s evidence without output mm matrix', key => {
  const calibration = marker({ evidence: { ...evidence, [key]: false } });
  expect(calibration.valid).toBe(false); expect(calibration.matrix).toBeNull();
});

test('calibration rejects cropped, crossed, zero-sized and numerically degenerate marker', () => {
  expect(marker({ widthMm: 0 }).valid).toBe(false);
  expect(marker({ corners: [{ x: 0, y: 0 }, { x: 100, y: 0 }, { x: 100, y: 100 }, { x: 0, y: 100 }] }).valid).toBe(false);
  expect(marker({ corners: [{ x: 10, y: 10 }, { x: 110, y: 110 }, { x: 110, y: 10 }, { x: 10, y: 110 }] }).valid).toBe(false);
  expect(marker({ corners: Array.from({ length: 4 }, (_, i) => ({ x: 10 + i * 20, y: 50 })) }).valid).toBe(false);
});

test('calibration requires an explicit reference plane and original integer dimensions', () => {
  expect(marker({ referencePlane: '' }).valid).toBe(false);
  expect(marker({ referencePlane: '   ' }).matrix).toBeNull();
  expect(marker({ image: { width: 300.5, height: 200 } }).valid).toBe(false);
});

test('projective extrapolation cannot cross the marker plane horizon', () => {
  const calibration = marker({ image: { width: 600, height: 400 },
    corners: [{ x: 100, y: 20 }, { x: 400, y: 20 }, { x: 300, y: 100 }, { x: 200, y: 100 }] });
  expect(calibration.valid).toBe(true);
  const output = measurePD({ ...pdInput(), calibration,
    points: { rightPupil: { x: 250, y: 220 }, leftPupil: { x: 350, y: 220 }, midlineTop: { x: 300, y: 180 }, midlineBottom: { x: 300, y: 260 } } });
  expect(output.valid).toBe(false); expect(output.values).toBeNull(); expect(output.reasons.join(' ')).toMatch(/horizon/);
});

test('frame segment calibration requires explicit frontal-plane verification', () => {
  const input = { method: 'frame', image: { width: 300, height: 200 }, segment: [{ x: 20, y: 20 }, { x: 120, y: 20 }], lengthMm: 50, evidence, referencePlane: 'Synthetic test plane' };
  expect(createCalibration({ ...input, evidence: { ...evidence, frontoparallel: false } }).valid).toBe(false);
  const calibration = createCalibration(input);
  expect(calibration.valid).toBe(true); expect(transformPoint(calibration.matrix, { x: 120, y: 20 }).x).toBeCloseTo(50);
  expect(calibration.limitations.join(' ')).toMatch(/foreshortening/);
});

test('monocular PD is measured independently; binocular is their sum', () => {
  const input = pdInput(); const output = measurePD(input);
  expect(output.valid).toBe(true); expect(output.values.rightMm).toBeCloseTo(3); expect(output.values.leftMm).toBeCloseTo(4);
  expect(output.values.binocularMm).toBeCloseTo(7); expect(output.uncertainty).toBeNull(); expect(output.requiresReview).toBe(true);
  expect(input.points.rightPupil).toEqual({ x: 40, y: 60 });
});

test('PD uses the marked midline orientation instead of silently halving a binocular distance', () => {
  const input = pdInput(); const pivot = { x: 70, y: 60 }; const radians = 15 * Math.PI / 180;
  const rotate = point => ({ x: pivot.x + Math.cos(radians) * (point.x - pivot.x) - Math.sin(radians) * (point.y - pivot.y), y: pivot.y + Math.sin(radians) * (point.x - pivot.x) + Math.cos(radians) * (point.y - pivot.y) });
  input.points = Object.fromEntries(Object.entries(input.points).map(([key, point]) => [key, rotate(point)]));
  const output = measurePD(input); expect(output.valid).toBe(true); expect(output.values.rightMm).toBeCloseTo(3); expect(output.values.leftMm).toBeCloseTo(4);
});

test('near PD requires working distance and gaze protocol, and stays separate from distance PD', () => {
  const input = { ...pdInput(), gaze: 'near' };
  expect(measurePD(input).valid).toBe(false);
  const output = measurePD({ ...input, workingDistanceCm: 40 }); expect(output.valid).toBe(true); expect(output.parameter).toBe('pd_near'); expect(output.values.workingDistanceCm).toBe(40);
  expect(measurePD({ ...input, workingDistanceCm: 40, confirmations: { ...input.confirmations, gazeCorrect: false } }).valid).toBe(false);
});

test('PD does not provide millimeters without valid calibration or an intervening midline', () => {
  expect(measurePD({ ...pdInput(), calibration: { valid: false } }).values).toBeNull();
  const input = pdInput(); input.points.midlineTop.x = 150; input.points.midlineBottom.x = 150;
  expect(measurePD(input).valid).toBe(false);
});

test('VD requires the respective lateral image and visible back-lens surface', () => {
  const input = { calibration: marker(), view: 'lateral_right',
    points: { cornea: { x: 40, y: 60 }, backLens: { x: 100, y: 60 }, gazeStart: { x: 30, y: 60 }, gazeEnd: { x: 140, y: 60 } },
    confirmations: { surfaceVisible: true, landmarksConfirmed: true, headPoseAcceptable: true } };
  const output = measureVertex(input); expect(output.valid).toBe(true); expect(output.values.vertexMm).toBeCloseTo(6); expect(output.values.offAxisMm).toBeCloseTo(0); expect(output.values.side).toBe('right');
  expect(measureVertex({ ...input, view: 'frontal' }).valid).toBe(false);
  expect(measureVertex({ ...input, confirmations: { ...input.confirmations, surfaceVisible: false } }).valid).toBe(false);
  expect(measureVertex({ ...input, points: { ...input.points, gazeStart: input.points.gazeEnd, gazeEnd: input.points.gazeStart } }).valid).toBe(false);
});

test('pantoscopic sign agrees across left/right views and preserves raw and corrected pitch', () => {
  const input = { calibration: marker(), view: 'lateral_right', inwardDirection: 'left', headPitchDeg: 2, headPitchSource: 'instrument',
    points: { lensTop: { x: 80, y: 20 }, lensBottom: { x: 70, y: 120 }, verticalTop: { x: 90, y: 20 }, verticalBottom: { x: 90, y: 120 } },
    confirmations: { verticalReferenceConfirmed: true, landmarksConfirmed: true, headPoseAcceptable: true } };
  const output = measurePantoscopic(input); expect(output.valid).toBe(true); expect(output.values.rawDeg).toBeCloseTo(5.710593, 5); expect(output.values.correctedDeg).toBeCloseTo(3.710593, 5);
  const other = measurePantoscopic({ ...input, view: 'lateral_left', inwardDirection: 'right', points: { ...input.points, lensTop: { x: 70, y: 20 }, lensBottom: { x: 80, y: 120 } } });
  expect(other.values.rawDeg).toBeCloseTo(output.values.rawDeg);
  expect(measurePantoscopic({ ...input, headPitchDeg: null }).valid).toBe(false);
  expect(measurePantoscopic({ ...input, headPitchSource: 'assumed_zero' }).valid).toBe(false);
});

test('frame PD depends on A+DBL, decentration uses each mono value and compatible bridge reference', () => {
  const input = { aMm: 52, dblMm: 18, rightPdMm: 31, leftPdMm: 33, pdReference: 'frame_bridge' };
  const derived = frameDerived(input); expect(derived.framePdMm).toBe(70); expect(derived.rightDecentrationMm).toBe(4); expect(derived.leftDecentrationMm).toBe(2); expect(derived.totalDecentrationMm).toBe(6);
  expect(frameDerived({ ...input, pdReference: 'facial_midline' }).rightDecentrationMm).toBeNull();
  expect(frameDerived({ ...input, aMm: -1 }).valid).toBe(false);
});

test('transposition is reversible, keeps ADD and never mutates the original prescription', () => {
  const source = Object.freeze({ sph: -2, cyl: -1, axis: 180, add: 2 });
  const first = transposePrescription(source); expect(first.transposed).toEqual({ sph: -3, cyl: 1, axis: 90, add: 2 });
  expect(transposePrescription(first.transposed).transposed).toEqual(source); expect(first.original).toEqual(source);
  expect(validatePrescription({ sph: 0, cyl: -1, axis: 0 }).valid).toBe(false);
  expect(validatePrescription({ sph: 0, cyl: 0, axis: null, add: null }).valid).toBe(true);
});

test('manual wrap requires real instrument/method reference and independent sides', () => {
  const input = { parameter: 'wrap', values: { right: 5, left: 7 }, operatorConfirmed: true, instrumentReference: 'Alat W-01; hasil pembacaan operator', angleReference: 'Bidang frontal frame; temporal posterior positif' };
  const output = recordManualMeasurement(input); expect(output.valid).toBe(true); expect(output.values.rightDeg).toBe(5); expect(output.values.leftDeg).toBe(7); expect(output.values.totalDeg).toBe(12); expect(output.method).toBe('manual_instrument');
  expect(recordManualMeasurement({ ...input, angleReference: '' }).valid).toBe(false);
  expect(recordManualMeasurement({ ...input, values: { right: 5 } }).valid).toBe(false);
  expect(recordManualMeasurement({ ...input, instrumentReference: '' }).valid).toBe(false);
  expect(recordManualMeasurement({ ...input, instrumentReference: {} }).valid).toBe(false);
  expect(CAPABILITIES.automaticWrapReconstruction).toBe(false); expect(CAPABILITIES.depth).toBe(false);
});

function image(width, height, valueAt) {
  const data = new Uint8ClampedArray(width * height * 4);
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const value = valueAt(x, y); const index = 4 * (y * width + x); data[index] = value; data[index + 1] = value; data[index + 2] = value; data[index + 3] = 255;
  }
  return { width, height, data };
}

test('image quality identifies flat dark images and retains unavailable detector states', () => {
  const dark = analyseImage(image(32, 32, () => 8)); expect(dark.sharpness).toBe('low'); expect(dark.exposure).toBe('low'); expect(dark.usable).toBe(false);
  const patterned = analyseImage(image(32, 32, (x, y) => (x + y) % 2 ? 170 : 70)); expect(patterned.sharpness).toBe('usable'); expect(patterned.exposure).toBe('usable');
  expect(patterned.unknown).toContain('headPose'); expect(patterned.unknown).toContain('cameraDistance');
  expect(analyseImage({ width: 32, height: 32, data: [] }).valid).toBe(false);
});

test('local dark-component candidate locates a synthetic pupil but requires confirmation', () => {
  const pixels = image(100, 80, (x, y) => Math.hypot(x - 40, y - 36) < 7 ? 15 : 180);
  const detected = suggestPupil(pixels, { x: 15, y: 15, width: 50, height: 45 });
  expect(detected.found).toBe(true); expect(detected.candidate.x).toBeCloseTo(40, 0); expect(detected.candidate.y).toBeCloseTo(36, 0); expect(detected.requiresConfirmation).toBe(true);
  expect(suggestPupil(image(100, 80, () => 128), { x: 15, y: 15, width: 50, height: 45 }).found).toBe(false);
});

test('burst selection uses actual image evidence, never target measurement values', () => {
  const samples = [10, 60, 90, 80, 70].map((score, index) => ({ analysis: { valid: true, score, laplacianVariance: score, signature: [100, 100] }, arbitraryPD: [63, 65, 77, 90, 40][index] }));
  const ranked = rankBurstSamples(samples); expect(ranked.valid).toBe(true); expect(ranked.selectedIndices).toEqual([2, 3, 4]); expect(ranked.rows).toHaveLength(5);
});

test('repeatability preserves raw outliers and reports SD without inventing uncertainty', () => {
  const input = [31, 31.1, 31.2, 90]; const repeat = aggregateMeasurements(input);
  expect(repeat.valid).toBe(true); expect(repeat.median).toBeCloseTo(31.1); expect(repeat.outlierIndices).toEqual([3]); expect(repeat.samples).toEqual(input); expect(repeat.uncertainty).toBeNull();
  expect(aggregateMeasurements([31, 32]).valid).toBe(false);
  const zeroMad = aggregateMeasurements([31, 31, 35]); expect(zeroMad.outlierIndices).toEqual([]); expect(zeroMad.sampleStdDev).toBeGreaterThan(0);
});

test('camera quality never promotes unvalidated geometry to high clinical confidence', () => {
  const confirmations = Object.fromEntries(['landmarksConfirmed', 'frameVisible', 'pupilsVisible', 'noReflections', 'gazeCorrect', 'headPoseAcceptable', 'distanceAppropriate', 'scaleConsistent'].map(key => [key, true]));
  const quality = assessQuality({ source: 'camera', calibration: marker(), confirmations, imageAnalyses: [{ valid: true, sharpness: 'usable', exposure: 'usable' }], repeatability: aggregateMeasurements([31, 31.1, 31.2]) });
  expect(quality.score).toBe(69); expect(quality.category).toBe('medium'); expect(quality.uncertainty).toBeNull(); expect(quality.clinicallyValidated).toBe(false);
  expect(assessQuality({ source: 'camera', calibration: null, confirmations }).score).toBe(0);
});

test('malformed input fails closed instead of exposing plausible measurement values', () => {
  [measurePD, measureVertex, measurePantoscopic, recordManualMeasurement, frameDerived, createCalibration, validatePrescription].forEach(fn => expect(fn(null).valid).toBe(false));
  expect(aggregateMeasurements(null).valid).toBe(false); expect(rankBurstSamples(null).valid).toBe(false); expect(rankBurstSamples([null]).valid).toBe(false);
  expect(assessQuality(null).score).toBe(0);
  expect(recordManualMeasurement({ parameter: 'wrap', values: { right: 5, left: 5 }, angleReference: 123, operatorConfirmed: true, instrumentReference: 'Alat referensi' }).valid).toBe(false);
});
