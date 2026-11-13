export const ALGORITHM_VERSION = 'optifit-local-geometry-1.0.0';

// Capabilities describe code actually shipped. A false value must never be
// replaced by a fabricated observation such as an assumed camera distance.
export const CAPABILITIES = Object.freeze({
  manualLandmarks: true,
  pupilCandidates: true,
  imageQuality: true,
  planarMarkerCalibration: true,
  frameSegmentCalibration: true,
  calibratedPD: true,
  lateralVertexProjection: true,
  lateralPantoscopicAngle: true,
  manualInstrumentMeasurements: true,
  automaticMode: false,
  faceDetection: false,
  facialLandmarks: false,
  anatomicalPupilIdentification: false,
  frameLandmarks: false,
  headPose: false,
  blinkDetection: false,
  occlusionDetection: false,
  depth: false,
  cameraDistance: false,
  cameraIntrinsics: false,
  lensDistortionCorrection: false,
  automaticWrapReconstruction: false,
  clinicalAccuracyValidated: false,
});

export const AUTOMATIC_MODE_REASON = 'Mode otomatis penuh belum tersedia: detektor wajah/frame, kalibrasi perangkat dan protokol validasi belum memenuhi syarat. Gunakan semi-otomatis dengan konfirmasi titik atau mode manual.';

export const MEASUREMENT_DISCLAIMER = 'Hasil kamera adalah alat bantu fitting yang harus diverifikasi tenaga optik kompeten. Aplikasi tidak mengukur SPH, CYL, AXIS atau ADD dan tidak menggantikan pemeriksaan refraksi atau kesehatan mata. Skor kualitas bukan probabilitas akurasi klinis.';

export const VIEW_LABELS = Object.freeze({
  frontal: 'Frontal — target jauh',
  frontal_near: 'Frontal — target dekat',
  three_quarter_left: 'Tiga-perempat kiri pasien',
  three_quarter_right: 'Tiga-perempat kanan pasien',
  lateral_right: 'Lateral kanan (OD)',
  lateral_left: 'Lateral kiri (OS)',
});

export const finiteNumber = value => typeof value === 'number' && Number.isFinite(value);
export const round = (value, places = 6) => Number(value.toFixed(places));
export const reasonResult = (parameter, reasons, extra = {}) => ({
  valid: false, parameter, values: null, reasons, uncertainty: null,
  requiresReview: true, algorithmVersion: ALGORITHM_VERSION, ...extra,
});
