import { faceFrameFit, smoothFaceFit } from './faceTracking';

export const face = () => {
  const points = Array(478);
  const set = (id, x, y, z = 0) => { points[id] = { x, y, z }; };
  set(33, .3, .4); set(133, .4, .4); set(362, .6, .4); set(263, .7, .4);
  set(468, .35, .4); set(473, .65, .4);
  set(234, .2, .45); set(454, .8, .45); set(10, .5, .1); set(152, .5, .9);
  return points;
};
const source = { width: 640, height: 480 }, stage = { width: 800, height: 600 };
test('frame follows eye midpoint and scales with head size', () => {
  const points = face();
  const original = faceFrameFit(points, source, stage);
  expect(original.x).toBeCloseTo(50);
  expect(original.width).toBeCloseTo(70.95);
  const closer = points.map(p => p && ({ ...p, x: .5 + (p.x - .5) * 1.2 }));
  expect(faceFrameFit(closer, source, stage).width).toBeCloseTo(original.width * 1.2);
});
test('object-contain letterboxing uses image coordinates rather than stage coordinates', () => {
  const fit = faceFrameFit(face(), { width: 480, height: 640 }, stage);
  expect(fit.x).toBeCloseTo(50);
  expect(fit.width).toBeCloseTo(70.95 * 450 / 800);
  expect(fit.y).toBeCloseTo(40.675);
});
test('camera is mirrored while uploaded photos keep their original orientation', () => {
  const points = face().map(p => p && ({ ...p, x: p.x - .1 }));
  points[473].y = .46;
  const photo = faceFrameFit(points, source, stage, false);
  const camera = faceFrameFit(points, source, stage, true);
  expect(photo.x).toBeCloseTo(40);
  expect(camera.x).toBeCloseTo(60);
  expect(camera.roll).toBeCloseTo(-photo.roll);
});
test('depth landmarks drive head rotation and admin asset calibration remains applied', () => {
  const points = face(); points[454].z = .1; points[152].z = .1;
  const fit = faceFrameFit(points, source, stage);
  expect(fit.yaw).toBeGreaterThan(0); expect(fit.pitch).toBeGreaterThan(0);
  const calibrated = faceFrameFit(points, source, stage, false, { scale: 1.2, rotation_z: 5 });
  expect(calibrated.width).toBeCloseTo(fit.width * 1.2);
  expect(calibrated.roll).toBeCloseTo(fit.roll + 5);
});
test('missing faces, invalid landmarks and off-screen eyes never produce an overlay', () => {
  expect(faceFrameFit(null, source, stage)).toBeNull();
  expect(faceFrameFit([], source, stage)).toBeNull();
  const points = face(); points[468].x = -1;
  expect(faceFrameFit(points, source, stage)).toBeNull();
});
test('smoothing reduces jitter and loses the overlay immediately when a face disappears', () => {
  const fit = faceFrameFit(face(), source, stage);
  expect(smoothFaceFit(fit, { ...fit, x: 70 }).x).toBeCloseTo(58);
  expect(smoothFaceFit(fit, null)).toBeNull();
});

test('fullscreen cover projects onto the cropped camera image in portrait', () => {
  const fit = faceFrameFit(face(), source, { width: 390, height: 844 }, false, {}, 'cover');
  // A 640x480 stream covers 390x844 as a centered 1125.33x844 image.
  expect(fit.x).toBeCloseTo(50);
  expect(fit.y).toBeCloseTo(41.2);
  expect(fit.width).toBeCloseTo(204.7241);
  expect(fit.width).toBeGreaterThan(180); // The cropped frame can extend past the viewport.
});
test('fullscreen camera preserves mirroring and the landscape crop', () => {
  const shifted = face().map(p => p && ({ ...p, x: p.x - .1 }));
  const fit = faceFrameFit(shifted, source, { width: 390, height: 844 }, true, {}, 'cover');
  expect(fit.x).toBeCloseTo(78.8547);
  const landscape = faceFrameFit(face(), source, { width: 844, height: 390 }, true, {}, 'cover');
  expect(landscape.x).toBeCloseTo(50);
  expect(landscape.y).toBeCloseTo(35.7169);
  expect(landscape.width).toBeCloseTo(70.95);
});
