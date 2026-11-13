// Use one lens dimension from the immutable session, never the whole-frame
// width, a box diagonal, or a guessed temple length.
export function frameScaleReference(frame = {}, view = 'frontal') {
  const dimension = view.startsWith('frontal') ? 'a' : view.startsWith('lateral_') ? 'b' : null;
  if (!dimension) return null;
  const length = frame[dimension];
  return { dimension, lengthMm: typeof length === 'number' && Number.isFinite(length) && length > 0 ? length : null,
    label: dimension === 'a' ? 'Lebar satu lensa (A)' : 'Tinggi satu lensa (B)',
    start: dimension === 'a' ? 'A: ujung kiri satu lensa' : 'B: ujung atas lensa',
    end: dimension === 'a' ? 'A: ujung kanan lensa yang sama' : 'B: ujung bawah lensa yang sama',
    referencePlane: `Ukuran frame sesi ${dimension.toUpperCase()}, bidang sejajar kamera, dikonfirmasi customer` };
}

export function frameScaleSpec(frame, view, previous = {}) {
  const reference = frameScaleReference(frame, view);
  const unchanged = reference && previous.method === 'frame' && previous.scaleSource === 'session_frame'
    && previous.frameDimension === reference.dimension && previous.lengthMm === reference.lengthMm;
  return { method: 'frame', ...(reference ? { scaleSource: 'session_frame', frameDimension: reference.dimension, lengthMm: reference.lengthMm,
    referencePlane: reference.referencePlane } : { lengthMm: null, referencePlane: '' }), evidence: unchanged ? { ...previous.evidence } : {} };
}

export function customerFrameCapture(capture, frame) {
  const spec = frameScaleSpec(frame, capture.view, capture.calibrationSpec);
  const changed = capture.calibrationSpec?.scaleSource !== 'session_frame' || capture.calibrationSpec?.method !== 'frame'
    || capture.calibrationSpec?.frameDimension !== spec.frameDimension || capture.calibrationSpec?.lengthMm !== spec.lengthMm;
  const clean = points => Object.fromEntries(Object.entries(points || {}).filter(([key]) => !changed || !['markerTL', 'markerTR', 'markerBR', 'markerBL', 'scaleStart', 'scaleEnd'].includes(key)));
  return { spec, changed, points: clean(capture.points), automaticPoints: clean(capture.automaticPoints),
    confirmations: { ...capture.confirmations, ...(changed ? { landmarksConfirmed: false } : {}) } };
}
