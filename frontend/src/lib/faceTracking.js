const degrees = radians => radians * 180 / Math.PI;
const limit = (value, min, max) => Math.min(max, Math.max(min, value));
const midpoint = (a, b) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, z: ((a.z || 0) + (b.z || 0)) / 2 });
const valid = point => point && Number.isFinite(point.x) && Number.isFinite(point.y);

// Project into the same centered contain/cover rectangle as the video/photo.
// Only the live video is mirrored; an uploaded photograph is not mirrored.
export function faceFrameFit(landmarks, source, stage, mirrored = false, asset = {}, objectFit = 'contain') {
  if (!landmarks || !source.width || !source.height || !stage.width || !stage.height) return null;
  if (![33, 133, 362, 263, 234, 454, 10, 152].every(index => valid(landmarks[index]))) return null;
  const left = valid(landmarks[468]) ? landmarks[468] : midpoint(landmarks[33], landmarks[133]);
  const right = valid(landmarks[473]) ? landmarks[473] : midpoint(landmarks[362], landmarks[263]);
  if ([left, right].some(p => p.x < 0 || p.x > 1 || p.y < 0 || p.y > 1)) return null;
  const factor = (objectFit === 'cover' ? Math.max : Math.min)(stage.width / source.width, stage.height / source.height);
  const contentWidth = source.width * factor, contentHeight = source.height * factor;
  const project = point => ({ x: (stage.width - contentWidth) / 2 + (mirrored ? 1 - point.x : point.x) * contentWidth,
    y: (stage.height - contentHeight) / 2 + point.y * contentHeight });
  const eyes = [project(left), project(right)].sort((a, b) => a.x - b.x);
  const eyeDistance = Math.hypot(eyes[1].x - eyes[0].x, eyes[1].y - eyes[0].y);
  if (eyeDistance < 8 || eyeDistance > contentWidth * 0.75) return null;
  const temples = [landmarks[234], landmarks[454]];
  const dx = (temples[1].x - temples[0].x) * source.width;
  const dz = ((temples[1].z || 0) - (temples[0].z || 0)) * source.width;
  const yaw = limit(degrees(Math.atan2(dz, Math.abs(dx))), -65, 65) * (mirrored ? -1 : 1);
  const pitch = limit(degrees(Math.atan2(((landmarks[152].z || 0) - (landmarks[10].z || 0)) * source.width,
    (landmarks[152].y - landmarks[10].y) * source.height)), -45, 45);
  const projectedWidth = Math.max(eyeDistance * 2.15, Math.abs(dx) * factor * 1.05);
  // Leave a little extra room beyond the detected face for the frame edges.
  const width = projectedWidth * 1.1 / Math.max(0.65, Math.cos(yaw * Math.PI / 180));
  const calibration = key => Number.isFinite(Number(asset[key])) ? Number(asset[key]) : 0;
  return {
    width: limit(width / stage.width * 100 * (Number(asset.scale) || 1), 3, objectFit === 'cover' ? Math.max(180, contentWidth / stage.width * 180) : 180),
    x: (eyes[0].x + eyes[1].x) / 2 / stage.width * 100 + calibration('offset_x') * width / stage.width * 100,
    y: ((eyes[0].y + eyes[1].y) / 2 + eyeDistance * 0.03) / stage.height * 100 + calibration('offset_y') * width / stage.height * 100,
    roll: degrees(Math.atan2(eyes[1].y - eyes[0].y, eyes[1].x - eyes[0].x)) + calibration('rotation_z'),
    yaw: yaw + calibration('rotation_y'), pitch: pitch + calibration('rotation_x'), depth: calibration('offset_z'),
  };
}

export function smoothFaceFit(previous, next, amount = 0.4) {
  if (!previous || !next) return next;
  return Object.fromEntries(Object.keys(next).map(key => [key, previous[key] + (next[key] - previous[key]) * amount]));
}

export async function createFaceTracker(mode) {
  const { FaceLandmarker, FilesetResolver } = await import('@mediapipe/tasks-vision');
  const root = `${(process.env.PUBLIC_URL || '').replace(/\/$/, '')}/try-on/vision`;
  const files = await FilesetResolver.forVisionTasks(`${root}/wasm`);
  return FaceLandmarker.createFromOptions(files, {
    baseOptions: { modelAssetPath: `${root}/face_landmarker.task`, delegate: 'CPU' },
    runningMode: mode, numFaces: 1,
    minFaceDetectionConfidence: 0.6, minFacePresenceConfidence: 0.6, minTrackingConfidence: 0.6,
    outputFaceBlendshapes: false, outputFacialTransformationMatrixes: false,
  });
}
