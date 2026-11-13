import { customerFrameCapture, frameScaleReference, frameScaleSpec } from './frameScale';
import { createCalibration } from '../vision/geometry';

const frame = { a: 50, b: 38, dbl: 18 };
const evidence = Object.fromEntries(['knownSize', 'fullyVisible', 'samePlane', 'clearEdges', 'frontoparallel'].map(key => [key, true]));
test('PD uses one lens A; lateral views use B; missing sizes never fall back to DBL, temple or diagonal', () => {
  expect(frameScaleReference(frame, 'frontal_near').lengthMm).toBe(50);
  expect(frameScaleReference(frame, 'lateral_left').lengthMm).toBe(38);
  expect(frameScaleReference({ a: 50, dbl: 18, templeLength: 140 }, 'lateral_right').lengthMm).toBeNull();
  expect(frameScaleReference(frame, 'three_quarter_right')).toBeNull();
  const spec = frameScaleSpec(frame, 'frontal');
  expect(createCalibration({ ...spec, evidence, image: { width: 200, height: 100 }, segment: [{ x: 10, y: 10 }, { x: 110, y: 10 }] }).geometry.mmPerPixel).toBe(.5);
});
test('old marker anchors and confirmation cannot be silently reused as lens endpoints', () => {
  const capture = { view: 'frontal', points: { markerTL: { x: 1, y: 1 }, scaleStart: { x: 2, y: 2 }, rightPupil: { x: 30, y: 40 } }, automaticPoints: {},
    calibrationSpec: { method: 'marker', evidence }, confirmations: { landmarksConfirmed: true } };
  const next = customerFrameCapture(capture, frame);
  expect(next.changed).toBe(true);
  expect(next.points).toEqual({ rightPupil: { x: 30, y: 40 } });
  expect(next.confirmations.landmarksConfirmed).toBe(false);
  expect(next.spec.evidence).toEqual({});
  expect(capture.points.markerTL).toBeDefined();
});
test('explicit evidence only persists for unchanged source, dimension and length', () => {
  const spec = { ...frameScaleSpec(frame, 'frontal'), evidence };
  expect(frameScaleSpec(frame, 'frontal', spec).evidence.frontoparallel).toBe(true);
  expect(frameScaleSpec(frame, 'lateral_right', spec).evidence).toEqual({});
  expect(frameScaleSpec({ ...frame, a: 51 }, 'frontal', spec).evidence).toEqual({});
});
