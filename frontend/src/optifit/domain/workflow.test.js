import { validatePrescription, validateFrame, numberOrNull, evaluateSubmission, evaluateReview, latestRevision, isCameraResult } from './workflow';
import { measurementContext, sameMeasurementContext } from './measurementContext';
const quality = { score: 65, category: 'medium' };
const data = () => withContext({
  prescription: { od: { sph: -1.25, cyl: -0.5, axis: 90, add: null }, os: { sph: 0, cyl: 0, axis: null, add: 0 } },
  frame: { a: 50, b: 38, dbl: 18, ed: 55 }, captures: [{id:'capture1',photoHash:'hash1',view:'frontal'},{id:'capture2',photoHash:'hash2',view:'frontal'},{id:'capture3',photoHash:'hash3',view:'frontal'}], requiredParameters: ['distance_pd'],
  results: { distance_pd: { valid: true, method: 'calibrated_planar_pd', calibration:{valid:true,method:'marker',matrix:[1,0,0,0,1,0,0,0,1],evidence:{knownSize:true,fullyVisible:true,samePlane:true,clearEdges:true}}, unit: 'mm', algorithmVersion: 'test', sourceCaptureIds: ['capture1','capture2','capture3'], sourcePhotoHashes: ['hash1','hash2','hash3'], repeatability: {valid:true,sampleCount:3,inlierCount:3,byField:{rightMm:{valid:true,inlierCount:3},leftMm:{valid:true,inlierCount:3}}}, values: { rightMm: 31, leftMm: 33, binocularMm: 64 }, quality } },
});
function withContext(d) {
  const context=measurementContext(d);
  for (const capture of d.captures || []) capture.measurementContext=context;
  for (const result of Object.values(d.results || {})) result.measurementContext=context;
  return d;
}
const session = () => ({ id: 'session1', patientId: 'patient1', examinationDate: '2026-11-09', createdBy: 'operator1', currentRevisionId: 'revision1', status: 'pending_review' });
const reviewInput = () => ({ session: session(), revision: { id: 'revision1', sessionId: 'session1', actorId: 'operator1', data: data() }, actor: { id: 'reviewer1', role: 'reviewer' }, decision: 'approved', evidence: { professionalVerified: true, comparisonAccepted: true, referenceInstrument: 'Pupillometer reference QA', protocolId: 'VALIDATION-QA-01', comparisonNotes: 'Synthetic policy fixture; not a clinical validation result.' } });

test('number validation preserves zero, distinguishes blank and accepts Indonesian decimal comma', () => {
  expect(numberOrNull('0')).toBe(0); expect(numberOrNull('')).toBe(null);
  expect(numberOrNull('-1,25')).toBe(-1.25); expect(Number.isNaN(numberOrNull('Infinity'))).toBe(true);
  expect(Number.isNaN(numberOrNull('1,2,3'))).toBe(true);
});
test('a nonzero cylinder requires a prescription axis and no values are invented for a missing eye', () => {
  const rx = data().prescription; expect(validatePrescription(rx, { partial: false }).valid).toBe(true);
  rx.od.axis = null; expect(validatePrescription(rx).valid).toBe(false);
  expect(validatePrescription({}, { partial: false }).valid).toBe(false);
});
test('frame values must be known positive numbers without substituting ED from a box diagonal', () => {
  expect(validateFrame(data().frame, { partial: false }).valid).toBe(true);
  expect(validateFrame({ ...data().frame, ed: null }, { partial: false }).valid).toBe(true);
  expect(validateFrame({ ...data().frame, ed: -1 }, { partial: false }).valid).toBe(false);
  expect(validateFrame({ ...data().frame, a: Infinity }).valid).toBe(false);
});
test('calibrated and lateral methods are treated as camera estimates requiring reference review', () => {
  for (const method of ['calibrated_planar_pd', 'lateral_gaze_projection', 'lateral_plane_angle_manual_pitch']) expect(isCameraResult({ method })).toBe(true);
  expect(isCameraResult({ method: 'manual_instrument' })).toBe(false);
});
test('valid drafts submit with a warning, low quality stays in manual verification, invalid scale cannot submit', () => {
  let d = data(); let policy = evaluateSubmission(d, { session: session() });
  expect(policy.valid).toBe(true); expect(policy.status).toBe('pending_review'); expect(policy.warnings.length).toBeGreaterThan(0);
  d.results.distance_pd.quality = { score: 20, category: 'low' };
  policy = evaluateSubmission(d, { session: session() }); expect(policy.valid).toBe(true); expect(policy.status).toBe('needs_verification');
  d.results.distance_pd.valid = false; expect(evaluateSubmission(d, { session: session() }).valid).toBe(false);
});
test('near PD requires its own working distance and independently recorded monocular values', () => {
  const d = data(); d.requiredParameters = ['near_pd']; d.workingDistanceCm=40; d.captures=d.captures.map(c=>({...c,view:'frontal_near'})); d.results.near_pd = { ...d.results.distance_pd, values: { rightMm: 29, leftMm: 31, binocularMm: 60 } };
  expect(evaluateSubmission(d, { session: session() }).valid).toBe(false);
  d.results.near_pd.values.workingDistanceCm = 40; withContext(d); expect(evaluateSubmission(d, { session: session() }).valid).toBe(true);
  d.results.near_pd.values.binocularMm = 63; expect(evaluateSubmission(d, { session: session() }).valid).toBe(false);
});
test('review approval requires a different active reviewer and the exact current revision', () => {
  const input = reviewInput(); expect(evaluateReview(input).allowed).toBe(true);
  input.actor.id = 'operator1'; expect(evaluateReview(input).allowed).toBe(false);
  input.actor.id = 'reviewer1'; input.revision.id = 'stale'; expect(evaluateReview(input).allowed).toBe(false);
});
test('a high score never bypasses evidence or authorizes an operator to approve', () => {
  const input = reviewInput(); input.revision.data.results.distance_pd.quality = { score: 99, category: 'high' };
  input.evidence = {}; expect(evaluateReview(input).allowed).toBe(false);
  input.actor.role = 'operator'; expect(evaluateReview(input).allowed).toBe(false);
});
test('low quality remains blocked even when review evidence is provided', () => {
  const input = reviewInput(); input.revision.data.results.distance_pd.quality = { score: 20, category: 'low' };
  expect(evaluateReview(input).allowed).toBe(false);
});
test('missing current revision never silently returns a different old record', () => {
  const s = session(); const state = { revisions: [{ id: 'older', sessionId: s.id, data: data() }] };
  expect(latestRevision(state, s)).toBe(null);
});

test('camera approval rejects duplicate photos and manufactured sample counts', () => {
  const input = reviewInput(); input.revision.data.results.distance_pd.sourcePhotoHashes = ['hash1','hash1','hash1'];
  expect(evaluateReview(input).allowed).toBe(false);
  const other = reviewInput(); other.revision.data.results.distance_pd.repeatability.inlierCount = 1;
  expect(evaluateReview(other).allowed).toBe(false);
});

test('administrator calibration restrictions are enforced by domain policy', () => {
  expect(evaluateSubmission(data(), {session:session(),settings:{calibrationMethods:['frame']}}).valid).toBe(false);
});

test('changed fitting context and invalidated captures cannot submit stale results', () => {
  const d=data(); d.frame.a=52;
  expect(evaluateSubmission(d,{session:session()}).valid).toBe(false);
  const other=data(); other.captures[0].contextInvalidated=true;
  expect(evaluateSubmission(other,{session:session()}).valid).toBe(false);
  const missing=data(); delete missing.results.distance_pd.measurementContext;
  expect(evaluateSubmission(missing,{session:session()}).valid).toBe(false);
});

test('canonical encrypted JSON preserves context equality despite object key order', () => {
  const context=measurementContext(data());
  const restored={workingDistanceCm:context.workingDistanceCm,frame:Object.fromEntries(Object.entries(context.frame).reverse())};
  expect(sameMeasurementContext(context,restored)).toBe(true);
  restored.frame.a+=1; expect(sameMeasurementContext(context,restored)).toBe(false);
});
