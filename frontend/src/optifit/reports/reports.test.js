import { buildReportSnapshot, reportSections, serializeCSV, renderPrintHTML, generateReport, validateReportPhotos } from './index';
import { measurementContext } from '../domain/measurementContext';
const input = () => {
  const data = { prescription: { od: { sph: -1, cyl: 0, axis: null, add: null }, os: { sph: 0, cyl: 0, axis: null, add: null } }, frame: { a: 50, b: 40, dbl: 18, ed: 55 }, results: {}, requiredParameters: ['distance_pd'], notes: 'Catatan QA' };
  return { confirmed: true, patient: { id: 'p1', fullName: 'Pasien QA', recordNumber: 'QA-001' }, session: { id: 's1', patientId: 'p1', examinationDate: '2026-11-09', currentRevisionId: 'r1', status: 'draft', algorithmVersion: 'qa' }, revision: { id: 'r1', sessionId: 's1', data }, data, organization: { name: 'Optik QA' } };
};
test('exports require conscious confirmation and the exact patient and revision', () => {
  const options = input(); expect(() => buildReportSnapshot({ ...options, confirmed: false })).toThrow(/Konfirmasi/);
  expect(() => buildReportSnapshot({ ...options, patient: { id: 'another' } })).toThrow(/tidak cocok/);
  expect(() => buildReportSnapshot({ ...options, data: { different: true } })).toThrow(/revisi/);
});
test('a session flag alone cannot label a PDF or JSON as reviewer-approved', () => {
  const options = input(); options.session.status = 'approved';
  expect(buildReportSnapshot(options).status).toBe('needs_verification');
  options.review = { revisionId: 'r1', decision: 'approved', reviewerId: 'reviewer1', reviewerName: 'Reviewer QA' };
  expect(buildReportSnapshot(options).status).toBe('needs_verification'); // A fabricated/incomplete review record is insufficient.
});
test('a complete independent review approves only its measurement scope and never restores photo bytes', () => {
  const options=input(); options.session.createdBy='operator1'; options.session.status='approved';
  options.revision.actorId='operator1'; options.revision.actorName='Operator QA';
  options.data.results.distance_pd={valid:true,method:'manual_instrument',algorithmVersion:'qa',instrumentReference:'Reference QA',measurementContext:measurementContext(options.data),quality:{score:65,category:'medium'},values:{rightMm:31,leftMm:33,binocularMm:64},internalImage:'data:image/png;base64,hidden'};
  options.data.results.wrap_right={valid:true,values:{angleDeg:12},quality:{score:20,category:'low'}};
  options.review={revisionId:'r1',decision:'approved',reviewerId:'reviewer1',reviewerName:'Reviewer QA',evidence:{professionalVerified:true,referenceInstrument:'Reference QA',protocolId:'QA-ONLY',comparisonNotes:'Synthetic review policy fixture only.'}};
  const snapshot=buildReportSnapshot(options);
  expect(snapshot.status).toBe('approved'); expect(snapshot.approvalScope).toEqual(['distance_pd']);
  expect(snapshot.clinical.results.wrap_right).toBeUndefined(); expect(snapshot.excludedUnreviewedParameters).toEqual(['wrap_right']);
  expect(JSON.stringify(snapshot)).not.toContain('base64'); expect(snapshot.operator.name).toBe('Operator QA');
});
test('default report omits photograph bytes and requires separate thumbnail consent', () => {
  const options = input(); options.data.photoDataUrl = 'data:image/jpeg;base64,private'; options.data.captures = [{ id: 'c1', imageBlob: new Blob(['private']), points: { p: { x: 1, y: 2 } } }];
  const snapshot = buildReportSnapshot(options);
  expect(JSON.stringify(snapshot)).not.toContain('base64'); expect(JSON.stringify(snapshot)).not.toContain('imageBlob');
  expect(() => buildReportSnapshot({ ...options, includePhotos: true })).toThrow(/Persetujuan/);
});
test('CSV text cannot create spreadsheet formulas and print output escapes HTML', () => {
  const options = input(); options.patient.fullName = '=HYPERLINK("https://example.test")'; options.data.notes = '<img src=x onerror=alert(1)>';
  const snapshot = buildReportSnapshot(options); const csv = serializeCSV(snapshot), html = renderPrintHTML(snapshot);
  expect(csv).toContain("'=HYPERLINK"); expect(html).toContain('&lt;img'); expect(html).not.toContain('<img src=x'); expect(html).not.toContain('<script');
});
test('reports expose unavailable measurements without inventing mm, angles or uncertainty', () => {
  const snapshot = buildReportSnapshot(input()); const sections = reportSections(snapshot);
  expect(sections.find(s => s.title === 'Jarak Pupil Jauh').rows[0][1]).toMatch(/Tidak tersedia/);
  expect(JSON.stringify(sections)).toContain('Ketidakpastian'); expect(JSON.stringify(sections)).not.toContain('±');
});
test('decentration in reports requires symmetric-frame confirmation and the actual bridge midline', () => {
  const options=input();options.data.results.distance_pd={valid:true,values:{rightMm:31,leftMm:33,binocularMm:64,pdReference:'frame_bridge'}};
  const decentration=()=>reportSections(buildReportSnapshot(options)).find(s=>s.title==='Frame dan perhitungan turunan').rows.find(r=>r[0]==='Decentration OD')[1];
  expect(decentration()).toMatch(/Tidak tersedia/);
  options.data.frame.symmetric=true;expect(decentration()).toBe('3 mm');
  options.data.results.distance_pd.values.pdReference='facial_midline';options.data.results.distance_pd.referencePlane='frame_bridge';
  expect(decentration()).toMatch(/Tidak tersedia/);
});
test('JSON generation creates an actual downloadable data blob without any network request', async () => {
  const result = await generateReport({ ...input(), format: 'json' });
  expect(result.blob).toBeInstanceOf(Blob); expect(result.mimeType).toBe('application/json'); expect(result.filename).toMatch(/^OF-.*\.json$/);
});

test('JSON and PDF thumbnail validators reject missing revision consent, foreign IDs and non-images', () => {
  const clinical={consents:{thumbnail:true},captures:[{photoId:'owned'}]};
  expect(()=>validateReportPhotos({includePhotos:true,photoConsentConfirmed:true,photos:[{photoId:'foreign',dataUrl:'data:text/html;base64,PHNjcmlwdD4='}]},clinical)).toThrow();
  expect(()=>validateReportPhotos({includePhotos:true,photoConsentConfirmed:true,photos:[{photoId:'owned',dataUrl:'data:image/png;base64,PHNjcmlwdD4='}]},clinical)).toThrow();
  expect(()=>validateReportPhotos({includePhotos:true,photoConsentConfirmed:false,photos:[]},clinical)).toThrow();
});
