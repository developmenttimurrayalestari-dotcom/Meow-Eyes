import { webcrypto } from 'crypto';
import { OptiFitVault } from './vault';
import { clone, VaultError, validateSecret, encryptJSON, decryptJSON, importDataKey, randomBytes } from './crypto';
import { measurementContext } from '../domain/measurementContext';

jest.setTimeout(30000);

/** A transactional store double exercises domain/crypto; browser QA uses IDB. */
class MemoryStore {
  constructor() { this.header = null; this.state = null; this.photos = new Map(); this.attempts = new Map(); this.beforeCommit = null; }
  async read(includePhotos = false) { return { header: clone(this.header), state: clone(this.state), ...(includePhotos ? { photos: [...this.photos.values()].map(clone) } : {}) }; }
  async commit(expected, header, state, { putPhotos = [], deletePhotoIds = [], replace = false, guard = () => true } = {}) {
    if (this.beforeCommit) await this.beforeCommit();
    if (!guard()) throw new VaultError('LOCKED', 'locked');
    if (expected === null ? !!this.header : !this.header || this.header.id !== expected.id || this.header.revision !== expected.revision) throw new VaultError('CONFLICT', 'conflict');
    const next = replace ? new Map() : new Map(this.photos);
    for (const photo of putPhotos) next.set(photo.id, clone(photo));
    for (const id of deletePhotoIds) next.delete(id);
    this.header = clone(header); this.state = clone(state); this.photos = next;
    if (replace) this.attempts.clear();
  }
  async getPhoto(id) { return clone(this.photos.get(id)); }
  async authState(id, failureAt = null, reset = false) {
    let record = this.attempts.get(id) || { failures: 0, nextAttemptAt: 0 };
    if (reset) record = { failures: 0, nextAttemptAt: 0 };
    else if (failureAt !== null) { const failures = record.failures + 1; record = { failures, nextAttemptAt: failureAt + (failures < 5 ? 0 : Math.min(900000, 30000 * 2 ** Math.min(failures - 5, 10))) }; }
    this.attempts.set(id, record); return clone(record);
  }
  async clear(expected) { if (!this.header || this.header.revision !== expected.revision || this.header.id !== expected.id) throw new VaultError('CONFLICT', 'conflict'); this.header = null; this.state = null; this.photos.clear(); this.attempts.clear(); }
  async close() {}
}
const secret = 'AwanJernih-Patut-2026';
const backupSecret = 'Cadangan-optik-terpisah-2026';
const fixtures = [];
async function fresh({ now = () => Date.now(), store = new MemoryStore() } = {}) {
  const vault = new OptiFitVault({ store, crypto: webcrypto, now, timers: false, broadcast: false }); fixtures.push(vault);
  await vault.create({ organization: { name: 'Optik QA' }, admin: { username: 'admin', displayName: 'Administrator QA', secret } });
  return { vault, store };
}
function existing(store, now = () => Date.now()) { const vault = new OptiFitVault({ store, crypto: webcrypto, now, timers: false, broadcast: false }); fixtures.push(vault); return vault; }
afterEach(() => { for (const vault of fixtures.splice(0)) vault.lock(); });
const person = { fullName: 'Pasien Sintetis Rahasia', examinationDate: '2026-11-09', notes: 'Catatan privat sintetis' };
const validData = quality => {
  const data = {
  prescription: { od: { sph: -1, cyl: 0, axis: null, add: null }, os: { sph: -1.25, cyl: -0.5, axis: 90, add: null } },
  frame: { a: 50, b: 38, dbl: 18, ed: 55 }, requiredParameters: ['distance_pd'],
  results: { distance_pd: { valid: true, source: 'instrument', method: 'manual_instrument', algorithmVersion: 'optifit-1.0.0', instrumentReference: 'Pupillometer referensi QA', values: { rightMm: 31, leftMm: 33, binocularMm: 64 }, quality: { score: quality === 'low' ? 25 : 75, category: quality || 'medium' }, uncertainty: null } },
  };
  data.results.distance_pd.measurementContext = measurementContext(data);
  return data;
};
const png = () => new Blob([Uint8Array.from([137, 80, 78, 71, 13, 10, 26, 10, 1, 2, 3, 4])], { type: 'image/png' });

it('stores encrypted patient data and rejects a wrong unlock credential or changed ciphertext', async () => {
  const { vault, store } = await fresh(); await vault.savePatient(person);
  expect(JSON.stringify(await store.read())).not.toContain(person.fullName);
  expect(JSON.stringify(await store.read())).not.toContain(person.notes);
  vault.lock();
  await expect(vault.unlock('admin', 'Wrong-password-2026')).rejects.toMatchObject({ code: 'AUTH_FAILED' });
  expect(vault.getState()).toBeNull();
  await vault.unlock('admin', secret); expect(vault.getState().patients[0].fullName).toBe(person.fullName);
  vault.lock(); const cipher = store.state.ciphertext; store.state.ciphertext = (cipher[0] === 'A' ? 'B' : 'A') + cipher.slice(1);
  await expect(vault.unlock('admin', secret)).rejects.toMatchObject({ code: 'DECRYPT_FAILED' });
  expect(vault.getState()).toBeNull();
});

it('authenticates role and ownership from encrypted users; operator sees only own patients and reviewer cannot edit', async () => {
  const { vault } = await fresh(); const adminPatient = await vault.savePatient(person);
  await vault.addUser({ username: 'operator', displayName: 'Operator QA', role: 'operator', secret });
  await vault.addUser({ username: 'reviewer', displayName: 'Reviewer QA', role: 'reviewer', secret });
  vault.lock(); await vault.unlock('operator', secret);
  expect(vault.getState().patients).toHaveLength(0);
  await expect(vault.savePatient({ id: adminPatient.id, fullName: 'Changed' })).rejects.toMatchObject({ code: 'NOT_FOUND' });
  await expect(vault.updateSettings({ photoRetentionDays: 1 })).rejects.toMatchObject({ code: 'FORBIDDEN' });
  await vault.savePatient({ ...person, fullName: 'Pasien milik operator' }); expect(vault.getState().patients).toHaveLength(1);
  vault.lock(); await vault.unlock('reviewer', secret);
  expect(vault.getState().patients).toHaveLength(2);
  await expect(vault.savePatient(person)).rejects.toMatchObject({ code: 'FORBIDDEN' });
  await expect(vault.addUser({ username: 'rogue', displayName: 'Rogue', role: 'admin', secret })).rejects.toMatchObject({ code: 'FORBIDDEN' });
});

it('preserves original measurements and previous revisions, rejects stale corrections, and protects state getters', async () => {
  const { vault } = await fresh(), patient = await vault.savePatient(person);
  const raw = validData(), session = await vault.createSession({ patientId: patient.id, raw });
  raw.frame.a = 999;
  const revised = validData(); revised.frame.a = 51; revised.algorithmVersion = 'optifit-test-v2';
  const revision = await vault.appendRevision(session.id, { data: revised, reason: 'Koreksi ukuran frame berdasarkan alat', expectedRevisionId: session.currentRevisionId });
  const state = vault.getState(); expect(state.sessions[0].raw.frame.a).toBe(50);
  expect(state.revisions).toHaveLength(2); expect(state.revisions[0].data.frame.a).toBe(50);
  expect(state.revisions[1].data.frame.a).toBe(51); expect(revision.algorithmVersion).toBe('optifit-test-v2'); expect(state.sessions[0].algorithmVersion).toBe('optifit-1.0.0'); expect(revision.parentRevisionId).toBe(session.currentRevisionId);
  state.sessions[0].raw.frame.a = 777; expect(vault.getState().sessions[0].raw.frame.a).toBe(50);
  await expect(vault.appendRevision(session.id, { data: validData(), reason: 'Koreksi lama', expectedRevisionId: session.currentRevisionId })).rejects.toMatchObject({ code: 'CONFLICT' });
  expect((await vault.verifyAudit()).valid).toBe(true);
});

it('requires an independent reviewer and blocks low-quality approval until a new adequate revision', async () => {
  const { vault } = await fresh(), patient = await vault.savePatient(person);
  const reviewer = await vault.addUser({ username: 'reviewer', displayName: 'Reviewer QA', role: 'reviewer', secret });
  const session = await vault.createSession({ patientId: patient.id, raw: validData('low') });
  expect((await vault.submitSession(session.id)).status).toBe('needs_verification');
  const evidence = { professionalVerified: true, referenceInstrument: 'Pupillometer QA', protocolId: 'QA-001', comparisonNotes: 'Catatan referensi sintetis' };
  await expect(vault.reviewSession(session.id, { decision: 'approved', evidence, expectedRevisionId: session.currentRevisionId })).rejects.toMatchObject({ code: 'REVIEW_REJECTED' });
  vault.lock(); await vault.unlock('reviewer', secret);
  await expect(vault.reviewSession(session.id, { decision: 'approved', evidence, expectedRevisionId: session.currentRevisionId })).rejects.toMatchObject({ code: 'REVIEW_REJECTED' });
  await expect(vault.reviewSession(session.id, { decision: 'needs_remeasure', expectedRevisionId: session.currentRevisionId })).rejects.toMatchObject({ code: 'INVALID_DATA' });
  await vault.reviewSession(session.id, { decision: 'needs_remeasure', note: 'Ulang dengan referensi yang memadai.', expectedRevisionId: session.currentRevisionId });
  vault.lock(); await vault.unlock('admin', secret);
  const revision = await vault.appendRevision(session.id, { data: validData(), reason: 'Diukur ulang dengan alat referensi', expectedRevisionId: session.currentRevisionId });
  expect((await vault.submitSession(session.id)).status).toBe('pending_review');
  vault.lock(); await vault.unlock('reviewer', secret);
  const review = await vault.reviewSession(session.id, { decision: 'approved', evidence, expectedRevisionId: revision.id });
  expect(review.reviewerId).toBe(reviewer.id); expect(vault.getState().sessions[0].status).toBe('approved');
  expect(vault.getState().sessions[0].raw.results.distance_pd.quality.category).toBe('low');
});

it('encrypts photos, requires consent, rejects public bytes in state, and applies retention when unlocked', async () => {
  let time = Date.parse('2026-11-09T00:00:00Z'); const { vault, store } = await fresh({ now: () => time });
  const patient = await vault.savePatient(person); await vault.updateSettings({ photoRetentionDays: 1 });
  await expect(vault.putPhoto({ patientId: patient.id, blob: png(), consent: false })).rejects.toMatchObject({ code: 'CONSENT_REQUIRED' });
  const id = await vault.putPhoto({ patientId: patient.id, blob: png(), consent: true, metadata: { purpose: 'capture', view: 'frontal', width: 1, height: 1 } });
  expect(store.photos.get(id).envelope.ciphertext).toBeDefined(); expect(store.photos.get(id).patientId).toBeUndefined();
  expect((await vault.getPhoto(id)).size).toBe(12);
  await expect(vault.createSession({ patientId: patient.id, raw: { photo: 'data:image/png;base64,AAAA' } })).rejects.toMatchObject({ code: 'RAW_IMAGE_IN_STATE' });
  time += 2 * 86400000; vault.lock(); await vault.unlock('admin', secret);
  expect(store.photos.size).toBe(0); expect(vault.getState().photos[0].deletedAt).toBeTruthy();
  expect(vault.getState().audit.at(-1).action).toBe('retention_policy_applied');
  await expect(vault.getPhoto(id)).rejects.toMatchObject({ code: 'NOT_FOUND' });
});

it('commits one concurrent edit and rejects the other rather than silently losing a patient', async () => {
  const { vault, store } = await fresh(), other = existing(store); await other.unlock('admin', secret);
  let release; const gate = new Promise(resolve => { release = resolve; }); let arrivals = 0;
  store.beforeCommit = async () => { arrivals += 1; if (arrivals === 2) release(); await gate; };
  const result = await Promise.allSettled([vault.savePatient(person), other.savePatient({ ...person, fullName: 'Pasien kedua' })]);
  expect(result.filter(item => item.status === 'fulfilled')).toHaveLength(1);
  expect(result.find(item => item.status === 'rejected').reason.code).toBe('CONFLICT');
  store.beforeCommit = null; vault.lock(); await vault.unlock('admin', secret);
  expect(vault.getState().patients).toHaveLength(1); expect((await vault.verifyAudit()).valid).toBe(true);
});

it('aborts a pending write when the vault is locked before its atomic commit', async () => {
  const { vault, store } = await fresh(); let ready, release;
  const reached = new Promise(resolve => { ready = resolve; }); const gate = new Promise(resolve => { release = resolve; });
  store.beforeCommit = async () => { ready(); await gate; };
  const pending = vault.savePatient(person); await reached; vault.lock('hidden'); release();
  await expect(pending).rejects.toMatchObject({ code: 'LOCKED' });
  store.beforeCommit = null; await vault.unlock('admin', secret); expect(vault.getState().patients).toHaveLength(0);
});

it('backs up and restores authenticated encrypted state/photos; wrong password and unconfirmed replacement preserve data', async () => {
  const { vault, store } = await fresh(), patient = await vault.savePatient(person);
  await vault.putPhoto({ patientId: patient.id, blob: png(), consent: true });
  const backup = await vault.exportBackup(backupSecret, { confirmed: true });
  const before = await store.read(true);
  await expect(vault.restoreBackup(backup, backupSecret, { confirmed: true })).rejects.toMatchObject({ code: 'CONFIRMATION_REQUIRED' });
  await expect(vault.restoreBackup(backup, 'Wrong-backup-passphrase', { confirmed: true, replaceConfirmation: 'GANTI VAULT' })).rejects.toMatchObject({ code: 'DECRYPT_FAILED' });
  expect(await store.read(true)).toEqual(before);
  const destinationStore = new MemoryStore(), destination = existing(destinationStore);
  await destination.restoreBackup(backup, backupSecret, { confirmed: true }); expect(destination.getState()).toBeNull();
  await destination.unlock('admin', secret); expect(destination.getState().patients[0].fullName).toBe(person.fullName);
  expect((await destination.getPhoto(destination.getState().photos[0].id)).size).toBe(12);
  expect((await destination.verifyAudit()).valid).toBe(true);
});

it('permanently deletes patient clinical rows and image bytes while retaining an opaque audit event', async () => {
  const { vault, store } = await fresh(), patient = await vault.savePatient(person);
  const photoId = await vault.putPhoto({ patientId: patient.id, blob: png(), consent: true });
  await vault.createSession({ patientId: patient.id, raw: { ...validData(), captures: [{ photoId }] } });
  await expect(vault.deletePatient(patient.id, { confirmation: 'wrong', reason: 'Permintaan pasien' })).rejects.toMatchObject({ code: 'CONFIRMATION_REQUIRED' });
  await vault.deletePatient(patient.id, { confirmation: patient.recordNumber, reason: 'Permintaan pasien' });
  const state = vault.getState(); for (const key of ['patients', 'sessions', 'revisions', 'reviews', 'photos']) expect(state[key]).toHaveLength(0);
  expect(store.photos.size).toBe(0); expect(JSON.stringify(state.audit)).not.toContain(person.fullName);
  expect(state.audit.at(-1).action).toBe('patient_permanently_deleted'); expect((await vault.verifyAudit()).valid).toBe(true);
});

it('does not accept local lockout bypass through the normal API and auto-locks inactive sessions', async () => {
  let time = Date.parse('2026-11-09T00:00:00Z'); const { vault } = await fresh({ now: () => time });
  vault.lock();
  for (let i = 0; i < 5; i += 1) await expect(vault.unlock('admin', 'wrong')).rejects.toMatchObject({ code: 'AUTH_FAILED' });
  await expect(vault.unlock('admin', secret)).rejects.toMatchObject({ code: 'AUTH_BACKOFF' });
  time += 31000; await vault.unlock('admin', secret); time += 6 * 60000;
  expect(vault.getState()).toBeNull(); await expect(vault.savePatient(person)).rejects.toMatchObject({ code: 'LOCKED' });
});

it('detects a changed audit trail even when a test actor re-encrypts the modified state', async () => {
  const { vault, store } = await fresh(); await vault.savePatient(person);
  const header = store.header, key = vault._key;
  const state = await decryptJSON(key, store.state, `optifit:v1:${header.id}:state:${header.revision}`, webcrypto);
  state.audit[1].action = 'forged'; store.state = await encryptJSON(key, state, `optifit:v1:${header.id}:state:${header.revision}`, webcrypto);
  vault.lock(); await expect(vault.unlock('admin', secret)).rejects.toMatchObject({ code: 'AUDIT_INVALID' });
});

it('rejects weak secrets, invalid frame data serialization, and last-admin removal', async () => {
  expect(() => validateSecret('1234567890')).toThrow(); expect(() => validateSecret('1111111111')).toThrow();
  expect(() => validateSecret('5837291640')).not.toThrow(); expect(() => validateSecret('5837291640', { backup: true })).toThrow();
  const { vault } = await fresh();
  await expect(vault.updateUser(vault.getUser().id, { active: false })).rejects.toMatchObject({ code: 'LAST_ADMIN' });
  await expect(vault.updateSettings({ asymmetryWarningMm: NaN })).rejects.toMatchObject({ code: 'INVALID_DATA' });
  const patient = await vault.savePatient(person);
  await expect(vault.createSession({ patientId: patient.id, raw: { value: NaN } })).rejects.toMatchObject({ code: 'INVALID_DATA' });
  await expect(vault.recordExport({ sessionId: 'missing', format: 'pdf', confirmed: false })).rejects.toMatchObject({ code: 'CONFIRMATION_REQUIRED' });
});

it('uses fresh IVs and binds ciphertext to the record identity', async () => {
  const key = await importDataKey(randomBytes(32, webcrypto), webcrypto);
  const a = await encryptJSON(key, { sample: 1 }, 'record:a', webcrypto), b = await encryptJSON(key, { sample: 1 }, 'record:a', webcrypto);
  expect(a.iv).not.toBe(b.iv); expect(a.ciphertext).not.toBe(b.ciphertext);
  await expect(decryptJSON(key, a, 'record:b', webcrypto)).rejects.toMatchObject({ code: 'DECRYPT_FAILED' });
});


it('permits consented thumbnails only from the exact immutable revision selected for export', async () => {
  const { vault } = await fresh(), patient = await vault.savePatient(person);
  const photoId = await vault.putPhoto({ patientId: patient.id, blob: png(), consent: true });
  const raw = { ...validData(), consents: { thumbnail: false }, captures: [{ photoId }] };
  const session = await vault.createSession({ patientId: patient.id, raw });
  await expect(vault.recordExport({ sessionId: session.id, revisionId: session.currentRevisionId, format: 'pdf', confirmed: true, includePhoto: true, photoIds: [photoId] })).rejects.toMatchObject({ code: 'CONSENT_REQUIRED' });
  const revised = clone(raw); revised.consents.thumbnail = true;
  const revision = await vault.appendRevision(session.id, { data: revised, reason: 'Persetujuan thumbnail dicatat', expectedRevisionId: session.currentRevisionId });
  await expect(vault.recordExport({ sessionId: session.id, revisionId: session.currentRevisionId, format: 'pdf', confirmed: true, includePhoto: true, photoIds: [photoId] })).rejects.toMatchObject({ code: 'CONSENT_REQUIRED' });
  await vault.recordExport({ sessionId: session.id, revisionId: revision.id, format: 'pdf', confirmed: true, includePhoto: true, photoIds: [photoId] });
  await vault.deletePhoto(photoId, { reason: 'Persetujuan penyimpanan dicabut' });
  await expect(vault.recordExport({ sessionId: session.id, revisionId: revision.id, format: 'pdf', confirmed: true, includePhoto: true, photoIds: [photoId] })).rejects.toMatchObject({ code: 'PHOTO_UNAVAILABLE' });
  // Deleting an optional photo never destroys original numerical/landmark data.
  const corrected = clone(revised); corrected.frame.a = 52;
  await vault.appendRevision(session.id, { data: corrected, reason: 'Koreksi frame setelah foto dihapus', expectedRevisionId: revision.id });
  expect(vault.getState().sessions[0].raw.captures[0].photoId).toBe(photoId);
});

it('revoking profile-photo consent deletes its ciphertext atomically with the patient change', async () => {
  const { vault, store } = await fresh(), patient = await vault.savePatient({ ...person, photoConsent: true });
  const photoId = await vault.putPhoto({ patientId: patient.id, blob: png(), consent: true, metadata: { purpose: 'profile' } });
  await vault.savePatient({ id: patient.id, profilePhotoId: photoId });
  await vault.savePatient({ id: patient.id, photoConsent: false });
  expect(vault.getState().patients[0].profilePhotoId).toBeNull(); expect(store.photos.has(photoId)).toBe(false);
  expect(vault.getState().photos[0].deletedAt).toBeTruthy(); expect((await vault.verifyAudit()).valid).toBe(true);
});


it('rechecks revoked credentials and disabled users even if a tab misses a broadcast notification', async () => {
  const { vault, store } = await fresh();
  const actor = await vault.addUser({ username: 'operator', displayName: 'Operator QA', role: 'operator', secret });
  const operator = existing(store); await operator.unlock('operator', secret);
  await vault.updateUser(actor.id, { secret: 'Kunci-operator-baru-2026' });
  await expect(operator.savePatient(person)).rejects.toMatchObject({ code: 'LOCKED' });
  await operator.unlock('operator', 'Kunci-operator-baru-2026');
  await vault.updateUser(actor.id, { active: false });
  await expect(operator.savePatient(person)).rejects.toMatchObject({ code: 'FORBIDDEN' }); expect(operator.getState()).toBeNull();
});

it('permits only a small local PNG/JPEG organization logo and never a cloud or SVG source', async () => {
  const { vault } = await fresh();
  const logo = 'data:image/png;base64,iVBORw0KGgoBAgME';
  await vault.updateOrganization({ logoDataUrl: logo });
  expect(vault.getState().organization.logoDataUrl).toBe(logo);
  await expect(vault.updateOrganization({ logoDataUrl: 'https://example.com/logo.png' })).rejects.toMatchObject({ code: 'INVALID_IMAGE' });
  await expect(vault.updateOrganization({ logoDataUrl: 'data:image/svg+xml;base64,PHN2Zz4=' })).rejects.toMatchObject({ code: 'INVALID_IMAGE' });
  const patient = await vault.savePatient(person);
  await expect(vault.createSession({ patientId: patient.id, raw: { image: logo } })).rejects.toMatchObject({ code: 'RAW_IMAGE_IN_STATE' });
  expect((await vault.verifyAudit()).valid).toBe(true);
});
