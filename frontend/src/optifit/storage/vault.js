import { IndexedDBStore } from './idb';
import {
  VaultError, KDF_ITERATIONS, MAX_BACKUP_BYTES, cryptoProvider, randomBytes,
  opaqueId, bytesToBase64, base64ToBytes, deriveKey, importDataKey,
  encryptJSON, decryptJSON, encryptBytes, decryptBytes, validateSecret,
  assertKdf, clone,
} from './crypto';
import { appendAudit, verifyAudit, stateDigest, assertJSON } from './audit';
import { evaluateSubmission, evaluateReview } from '../domain/workflow';

export { VaultError } from './crypto';
export const DEFAULT_SETTINGS = Object.freeze({ autoLockMinutes: 5, photoRetentionDays: 30, lockOnHidden: true, asymmetryWarningMm: null, calibrationMethods: ['marker', 'frame'] });
export const PHOTO_LIMIT_BYTES = 8 * 1024 * 1024;
const ROLES = ['admin', 'operator', 'reviewer'];
const cleanText = (value, field, max = 200, required = false) => {
  if (typeof value !== 'string' || value.length > max || (required && !value.trim())) throw new VaultError('INVALID_DATA', `${field} tidak valid.`);
  return value.trim();
};
function username(value) { const name = cleanText(value, 'Nama login', 64, true).toLowerCase(); if (!/^[a-z0-9._-]{3,64}$/.test(name)) throw new VaultError('INVALID_DATA', 'Nama login memakai 3–64 huruf, angka, titik, tanda minus atau garis bawah.'); return name; }
function settings(value) {
  assertJSON(value || {});
  const result = { ...DEFAULT_SETTINGS, ...clone(value || {}) };
  const allowed = Object.keys(DEFAULT_SETTINGS);
  if (Object.keys(result).some(key => !allowed.includes(key)) || !Number.isFinite(result.autoLockMinutes) || result.autoLockMinutes < 1 || result.autoLockMinutes > 30
    || !Number.isInteger(result.photoRetentionDays) || result.photoRetentionDays < 1 || result.photoRetentionDays > 3650 || result.lockOnHidden !== true
    || (result.asymmetryWarningMm !== null && (!Number.isFinite(result.asymmetryWarningMm) || result.asymmetryWarningMm <= 0))
    || !Array.isArray(result.calibrationMethods) || !result.calibrationMethods.length || result.calibrationMethods.some(v => !['marker', 'frame'].includes(v))) {
    throw new VaultError('INVALID_DATA', 'Pengaturan retensi, penguncian, atau kalibrasi tidak valid.');
  }
  return result;
}
function dateOnly(value, field) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(Date.parse(`${value}T00:00:00Z`)) || new Date(`${value}T00:00:00Z`).toISOString().slice(0, 10) !== value) throw new VaultError('INVALID_DATA', `${field} tidak valid.`);
  return value;
}
const aad = (header, kind, value) => `optifit:v1:${header.id}:${kind}:${value}`;
const sameIdentity = (a, b) => !!a && !!b && a.id === b.id && a.revision === b.revision;
function organizationLogo(value) {
  if (value === undefined || value === null || value === '') return null;
  if (typeof value !== 'string' || value.length > 1400000) throw new VaultError('INVALID_IMAGE', 'Logo harus PNG/JPEG lokal maksimal 1 MiB.');
  const match = /^data:image\/(png|jpeg);base64,([A-Za-z0-9+/=]+)$/.exec(value);
  if (!match) throw new VaultError('INVALID_IMAGE', 'Logo harus data PNG/JPEG lokal; URL cloud/SVG tidak diterima.');
  const bytes = base64ToBytes(match[2], 1024 * 1024);
  const valid = match[1] === 'png' ? [137, 80, 78, 71, 13, 10, 26, 10].every((b, i) => bytes[i] === b) : bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255;
  if (!valid) throw new VaultError('INVALID_IMAGE', 'Isi logo tidak sesuai dengan tipe gambar.');
  return value;
}

function requireFound(value, description) { if (!value) throw new VaultError('NOT_FOUND', `${description} tidak ditemukan atau tidak dapat diakses.`); return value; }
function requiredReason(value) { return cleanText(value, 'Alasan', 1000, true); }
function photoIds(data) {
  const ids = new Set();
  function scan(value) {
    if (!value || typeof value !== 'object') return;
    for (const [key, child] of Object.entries(value)) {
      if ((key === 'photoId' || key === 'profilePhotoId') && typeof child === 'string') ids.add(child);
      else if (typeof child === 'object') scan(child);
    }
  }
  scan(data); return [...ids];
}
function blobBytes(blob) {
  if (typeof blob.arrayBuffer === 'function') return blob.arrayBuffer().then(buffer => new Uint8Array(buffer));
  return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(new Uint8Array(reader.result)); reader.onerror = () => reject(new VaultError('FILE_READ_FAILED', 'Berkas tidak dapat dibaca.')); reader.readAsArrayBuffer(blob); });
}
async function blobText(blob) { return typeof blob.text === 'function' ? blob.text() : new TextDecoder().decode(await blobBytes(blob)); }
function validateHeader(header) {
  if (!header || header.format !== 'optifit-vault-v1' || typeof header.id !== 'string' || !/^vault_[a-f0-9]{32}$/.test(header.id)
    || !Number.isSafeInteger(header.revision) || header.revision < 1 || !Array.isArray(header.credentials) || !header.credentials.length || header.credentials.length > 100) throw new VaultError('INVALID_ENVELOPE', 'Header vault tidak valid.');
  const ids = new Set(), names = new Set();
  for (const credential of header.credentials) {
    assertKdf(credential.kdf);
    if (typeof credential.id !== 'string' || ids.has(credential.id) || names.has(credential.username) || username(credential.username) !== credential.username) throw new VaultError('INVALID_ENVELOPE', 'Identitas akun vault tidak valid.');
    ids.add(credential.id); names.add(credential.username);
  }
}
function validateState(state, header) {
  if (!state || state.schemaVersion !== 1 || state.vaultId !== header.id || state.revision !== header.revision) throw new VaultError('INVALID_ENVELOPE', 'Versi state vault tidak sesuai.');
  for (const collection of ['users', 'patients', 'sessions', 'revisions', 'reviews', 'photos', 'audit']) {
    if (!Array.isArray(state[collection])) throw new VaultError('INVALID_ENVELOPE', 'Struktur state vault tidak lengkap.');
    if (collection !== 'audit' && new Set(state[collection].map(item => item.id)).size !== state[collection].length) throw new VaultError('INVALID_ENVELOPE', 'Identitas record vault berulang.');
  }
  settings(state.settings);
  if (!state.organization || typeof state.organization.name !== 'string' || !state.organization.name.trim()) throw new VaultError('INVALID_ENVELOPE', 'Organisasi tidak valid.');
  organizationLogo(state.organization.logoDataUrl);
  if (!state.users.some(user => user.active && user.role === 'admin')) throw new VaultError('INVALID_ENVELOPE', 'Vault tidak mempunyai administrator aktif.');
  for (const user of state.users) if (!ROLES.includes(user.role) || username(user.username) !== user.username || typeof user.id !== 'string' || typeof user.displayName !== 'string') throw new VaultError('INVALID_ENVELOPE', 'Data pengguna vault tidak valid.');
  for (const credential of header.credentials) if (!state.users.some(user => user.id === credential.id && user.username === credential.username && user.active)) throw new VaultError('INVALID_ENVELOPE', 'Kredensial vault tidak cocok dengan akun aktif.');
  if (state.users.filter(user => user.active).length !== header.credentials.length) throw new VaultError('INVALID_ENVELOPE', 'Kredensial akun aktif tidak lengkap.');
  const patients = new Set(state.patients.map(patient => patient.id));
  for (const session of state.sessions) {
    if (!patients.has(session.patientId) || !state.revisions.some(revision => revision.id === session.currentRevisionId && revision.sessionId === session.id)) throw new VaultError('INVALID_ENVELOPE', 'Relasi sesi/revisi tidak valid.');
  }
}

/** One clinical workspace per origin; roles enforce the application workflow. */
export class OptiFitVault {
  constructor({ store = new IndexedDBStore(), crypto = globalThis.crypto, now = () => Date.now(), timers = true, broadcast = true } = {}) {
    this.store = store; this.crypto = crypto; this.now = now; this.timers = timers;
    this._state = null; this._header = null; this._key = null; this._keyBytes = null; this._userId = null;
    this._generation = 0; this._listeners = new Set(); this._queue = Promise.resolve(); this._timer = null; this._expiresAt = 0; this._lockReason = null;
    this._channel = broadcast && typeof BroadcastChannel !== 'undefined' ? new BroadcastChannel('optifit-vault-events-v1') : null;
    if (this._channel) { this._channel.onmessage = () => this.lock('changed-in-another-tab'); this._channel.unref?.(); }
  }
  subscribe(callback) { this._listeners.add(callback); return () => this._listeners.delete(callback); }
  _notify() { for (const listener of this._listeners) { try { listener(); } catch { /* A view listener cannot abort a committed storage write. */ } } }
  _time() { const value = this.now(); return value instanceof Date ? value.getTime() : value; }
  _iso() { return new Date(this._time()).toISOString(); }
  _id(prefix) { return opaqueId(prefix, this.crypto); }
  async status() {
    const { header } = await this.store.read();
    if (header) validateHeader(header);
    return { initialized: !!header, locked: !this._key, logins: header?.credentials.map(c => ({ id: c.id, username: c.username })) || [], lockReason: this._lockReason };
  }
  touch() {
    if (!this._key) return;
    if (this._expiresAt && this._time() >= this._expiresAt) { this.lock('idle'); return; }
    this._expiresAt = this._time() + (this._state.settings.autoLockMinutes * 60000);
    if (this._timer) clearTimeout(this._timer);
    if (this.timers) this._timer = setTimeout(() => this.lock('idle'), this._state.settings.autoLockMinutes * 60000);
  }
  lock(reason = 'manual') {
    this._generation += 1;
    if (this._timer) clearTimeout(this._timer);
    this._timer = null; this._expiresAt = 0;
    if (this._keyBytes) this._keyBytes.fill(0);
    this._keyBytes = null; this._key = null; this._state = null; this._header = null; this._userId = null; this._lockReason = reason;
    this._notify();
  }
  _ensureUnlocked() {
    if (this._key && this._time() >= this._expiresAt) this.lock('idle');
    if (!this._key || !this._state) throw new VaultError('LOCKED', 'Vault terkunci. Masuk kembali untuk melanjutkan.');
  }
  getUser() {
    try { this._ensureUnlocked(); return clone(this._state.users.find(user => user.id === this._userId)); } catch { return null; }
  }
  getState() {
    try { this._ensureUnlocked(); } catch { return null; }
    const state = clone(this._state), actor = state.users.find(user => user.id === this._userId);
    if (!actor?.active) { this.lock('account-inactive'); return null; }
    if (actor.role === 'operator') {
      state.patients = state.patients.filter(patient => patient.createdBy === actor.id);
      const patientIds = new Set(state.patients.map(patient => patient.id));
      state.sessions = state.sessions.filter(session => patientIds.has(session.patientId));
      const sessionIds = new Set(state.sessions.map(session => session.id));
      state.revisions = state.revisions.filter(revision => sessionIds.has(revision.sessionId));
      state.reviews = state.reviews.filter(review => sessionIds.has(review.sessionId));
      state.photos = state.photos.filter(photo => patientIds.has(photo.patientId));
      state.audit = state.audit.filter(event => event.actorId === actor.id);
      state.users = state.users.filter(user => user.id === actor.id);
    }
    return state;
  }
  async _credential(header, user, secret) {
    validateSecret(secret); const salt = randomBytes(32, this.crypto);
    const key = await deriveKey(secret, salt, this.crypto);
    const wrappedKey = await encryptJSON(key, { vaultId: header.id, userId: user.id, key: bytesToBase64(this._keyBytes) }, aad(header, 'credential', user.id), this.crypto);
    return { id: user.id, username: user.username, kdf: { name: 'PBKDF2', hash: 'SHA-256', iterations: KDF_ITERATIONS, salt: bytesToBase64(salt) }, wrappedKey };
  }
  async create({ organization, admin, settings: suppliedSettings } = {}) {
    if ((await this.store.read()).header) throw new VaultError('ALREADY_EXISTS', 'Vault sudah tersedia. Buka vault yang ada.');
    cryptoProvider(this.crypto); validateSecret(admin?.secret);
    const name = typeof organization === 'string' ? organization : organization?.name;
    const org = { name: cleanText(name, 'Nama optik', 200, true), address: cleanText(organization?.address || '', 'Alamat optik', 1000), phone: cleanText(organization?.phone || '', 'Telepon optik', 40), logoDataUrl: organizationLogo(organization?.logoDataUrl) };
    const actor = { id: this._id('user'), username: username(admin?.username), displayName: cleanText(admin?.displayName || admin?.name, 'Nama administrator', 120, true), role: 'admin', active: true, createdAt: this._iso() };
    const header = { format: 'optifit-vault-v1', id: this._id('vault'), revision: 1, credentials: [] };
    const state = { schemaVersion: 1, vaultId: header.id, revision: 1, organization: org, settings: settings(suppliedSettings), users: [actor], patients: [], sessions: [], revisions: [], reviews: [], photos: [], audit: [], createdAt: this._iso(), updatedAt: this._iso() };
    this._keyBytes = randomBytes(32, this.crypto); const generation = this._generation;
    try {
      this._key = await importDataKey(this._keyBytes, this.crypto);
      header.credentials = [await this._credential(header, actor, admin.secret)];
      await appendAudit(state, { action: 'vault_created', actor, timestamp: this._iso() }, this.crypto);
      const encrypted = await encryptJSON(this._key, state, aad(header, 'state', 1), this.crypto);
      if (generation !== this._generation) throw new VaultError('LOCKED', 'Pembuatan vault dibatalkan karena perangkat dikunci.');
      await this.store.commit(null, header, encrypted, { guard: () => generation === this._generation });
      if (generation !== this._generation) throw new VaultError('LOCKED', 'Vault telah dibuat lalu dikunci. Buka kembali menggunakan akun administrator.');
      this._header = header; this._state = state; this._userId = actor.id; this._lockReason = null; this.touch(); this._notify();
      this._channel?.postMessage({ changed: true });
      return clone(actor);
    } catch (error) { this.lock('setup-failed'); throw error; }
  }
  async unlock(name, secret) {
    this.lock('unlocking'); const generation = this._generation;
    const { header, state: encrypted } = await this.store.read();
    validateHeader(header);
    const credential = header.credentials.find(c => c.username === username(name));
    if (!credential) throw new VaultError('AUTH_FAILED', 'Nama login atau kunci tidak sesuai.');
    const attempts = await this.store.authState(credential.id);
    if (attempts.nextAttemptAt > this._time()) throw new VaultError('AUTH_BACKOFF', `Terlalu banyak percobaan. Coba lagi setelah ${Math.ceil((attempts.nextAttemptAt - this._time()) / 1000)} detik.`);
    let keyBytes;
    try {
      const wrappingKey = await deriveKey(secret, base64ToBytes(credential.kdf.salt, 32), this.crypto);
      const payload = await decryptJSON(wrappingKey, credential.wrappedKey, aad(header, 'credential', credential.id), this.crypto);
      if (payload.vaultId !== header.id || payload.userId !== credential.id) throw new VaultError('AUTH_FAILED', 'Identitas kunci tidak sesuai.');
      keyBytes = base64ToBytes(payload.key, 32);
    } catch {
      await this.store.authState(credential.id, this._time());
      throw new VaultError('AUTH_FAILED', 'Nama login atau kunci tidak sesuai.');
    }
    try {
      const key = await importDataKey(keyBytes, this.crypto);
      const state = await decryptJSON(key, encrypted, aad(header, 'state', header.revision), this.crypto);
      validateState(state, header); await verifyAudit(state, this.crypto);
      const actor = state.users.find(user => user.id === credential.id && user.username === credential.username && user.active);
      if (!actor) throw new VaultError('AUTH_FAILED', 'Akun tidak aktif.');
      if (generation !== this._generation) throw new VaultError('LOCKED', 'Pembukaan vault dibatalkan karena perangkat dikunci.');
      await this.store.authState(credential.id, null, true);
      if (generation !== this._generation) throw new VaultError('LOCKED', 'Pembukaan vault dibatalkan karena perangkat dikunci.');
      this._keyBytes = keyBytes; this._key = key; this._header = header; this._state = state; this._userId = actor.id; this._lockReason = null; this.touch(); this._notify();
      if (state.photos.some(photo => !photo.deletedAt && Date.parse(photo.expiresAt) <= this._time())) await this._applyRetention();
      return clone(actor);
    } catch (error) { keyBytes.fill(0); this.lock('integrity-or-unlock-failed'); throw error; }
  }
  _actor(state, allowed = ROLES) {
    const actor = state.users.find(user => user.id === this._userId && user.active);
    if (!actor) throw new VaultError('FORBIDDEN', 'Akun tidak aktif atau telah berubah.');
    if (!allowed.includes(actor.role)) throw new VaultError('FORBIDDEN', 'Peran Anda tidak mempunyai izin untuk tindakan ini.');
    return actor;
  }
  _patient(state, id, actor) {
    return requireFound(state.patients.find(patient => patient.id === id && (actor.role !== 'operator' || patient.createdBy === actor.id)), 'Pasien');
  }
  _session(state, id, actor) {
    const session = requireFound(state.sessions.find(row => row.id === id), 'Sesi');
    this._patient(state, session.patientId, actor); return session;
  }
  async _readUnlocked() {
    this._ensureUnlocked(); const generation = this._generation, key = this._key, vaultId = this._header.id;
    try {
      const record = await this.store.read();
      if (generation !== this._generation) throw new VaultError('LOCKED', 'Vault terkunci saat data dibaca.');
      validateHeader(record.header);
      const oldCredential = this._header?.credentials.find(c => c.id === this._userId);
      const newCredential = record.header.credentials.find(c => c.id === this._userId);
      if (oldCredential && newCredential && JSON.stringify(oldCredential) !== JSON.stringify(newCredential)) { this.lock('credential-changed'); throw new VaultError('LOCKED', 'Kunci akun telah diubah. Masuk kembali.'); }
      if (record.header.id !== vaultId) { this.lock('vault-replaced'); throw new VaultError('LOCKED', 'Vault sudah diganti. Masuk kembali.'); }
      const state = await decryptJSON(key, record.state, aad(record.header, 'state', record.header.revision), this.crypto);
      validateState(state, record.header); await verifyAudit(state, this.crypto);
      if (generation !== this._generation) throw new VaultError('LOCKED', 'Vault terkunci saat data dibaca.');
      this._actor(state);
      this._state = state; this._header = record.header;
      return { state, header: record.header, generation };
    } catch (error) {
      if (['AUDIT_INVALID', 'DECRYPT_FAILED', 'INVALID_ENVELOPE', 'FORBIDDEN'].includes(error.code)) this.lock('integrity-or-account-changed');
      throw error;
    }
  }
  _mutate(action, subjectId, allowed, change) {
    const queuedGeneration = this._generation;
    const operation = async () => {
      if (queuedGeneration !== this._generation) throw new VaultError('LOCKED', 'Perubahan dari sesi sebelumnya dibatalkan.');
      const { state: previous, header: oldHeader, generation } = await this._readUnlocked();
      const state = clone(previous), header = clone(oldHeader), actor = this._actor(state, allowed);
      const beforeHash = await stateDigest(previous, this.crypto);
      const output = await change(state, header, actor) || {};
      header.revision += 1; state.revision = header.revision; state.updatedAt = this._iso();
      await appendAudit(state, { action, actor, subjectId: output.subjectId || subjectId, details: output.details || {}, beforeHash, timestamp: this._iso() }, this.crypto);
      validateState(state, header); assertJSON(state, { allowOrganizationLogo: true });
      const encrypted = await encryptJSON(this._key, state, aad(header, 'state', header.revision), this.crypto);
      if (generation !== this._generation) throw new VaultError('LOCKED', 'Perubahan dibatalkan karena vault terkunci.');
      this._ensureUnlocked();
      await this.store.commit(oldHeader, header, encrypted, { ...output, guard: () => generation === this._generation && !!this._key && this._time() < this._expiresAt });
      if (generation === this._generation) { this._state = state; this._header = header; this.touch(); this._notify(); }
      this._channel?.postMessage({ changed: true });
      return clone(output.result ?? null);
    };
    const pending = this._queue.then(operation, operation);
    this._queue = pending.catch(() => {}); return pending;
  }
  async addUser({ username: name, displayName, role, secret }) {
    const normalName = username(name); validateSecret(secret);
    if (!ROLES.includes(role)) throw new VaultError('INVALID_DATA', 'Peran tidak dikenal.');
    return this._mutate('user_added', null, ['admin'], async (state, header) => {
      if (state.users.some(user => user.username === normalName)) throw new VaultError('DUPLICATE', 'Nama login sudah digunakan.');
      const user = { id: this._id('user'), username: normalName, displayName: cleanText(displayName, 'Nama pengguna', 120, true), role, active: true, createdAt: this._iso() };
      header.credentials.push(await this._credential(header, user, secret)); state.users.push(user);
      return { result: user, subjectId: user.id, details: { role } };
    });
  }
  async updateUser(id, patch) {
    const permitted = ['displayName', 'role', 'active', 'isActive', 'secret'];
    if (!patch || Object.keys(patch).some(key => !permitted.includes(key))) throw new VaultError('INVALID_DATA', 'Perubahan akun tidak valid.');
    return this._mutate('user_updated', id, ['admin'], async (state, header) => {
      const user = requireFound(state.users.find(row => row.id === id), 'Pengguna');
      if (patch.displayName !== undefined) user.displayName = cleanText(patch.displayName, 'Nama pengguna', 120, true);
      if (patch.role !== undefined) { if (!ROLES.includes(patch.role)) throw new VaultError('INVALID_DATA', 'Peran tidak dikenal.'); user.role = patch.role; }
      const active = patch.active ?? patch.isActive;
      if (active !== undefined) { if (typeof active !== 'boolean') throw new VaultError('INVALID_DATA', 'Status akun tidak valid.'); user.active = active; }
      if (!state.users.some(row => row.active && row.role === 'admin')) throw new VaultError('LAST_ADMIN', 'Administrator aktif terakhir tidak boleh dinonaktifkan.');
      if (!user.active) header.credentials = header.credentials.filter(row => row.id !== id);
      else if (patch.secret !== undefined) {
        const credential = await this._credential(header, user, patch.secret);
        header.credentials = [...header.credentials.filter(row => row.id !== id), credential];
      } else if (!header.credentials.some(row => row.id === id)) throw new VaultError('SECRET_REQUIRED', 'Aktivasi ulang memerlukan kunci baru.');
      user.updatedAt = this._iso(); return { result: user, details: { role: user.role, active: user.active, credentialChanged: patch.secret !== undefined } };
    });
  }
  async updateSettings(patch) {
    return this._mutate('settings_updated', null, ['admin'], (state) => { state.settings = settings({ ...state.settings, ...patch }); return { result: state.settings, details: { fields: Object.keys(patch).sort() } }; });
  }
  async updateOrganization(patch) {
    if (!patch || Object.keys(patch).some(key => !['name', 'address', 'phone', 'logoDataUrl'].includes(key))) throw new VaultError('INVALID_DATA', 'Data organisasi tidak valid.');
    return this._mutate('organization_updated', null, ['admin'], (state) => {
      for (const [key, value] of Object.entries(patch)) state.organization[key] = key === 'logoDataUrl' ? organizationLogo(value) : cleanText(value, key, key === 'address' ? 1000 : 200, key === 'name');
      return { result: state.organization, details: { fields: Object.keys(patch).sort() } };
    });
  }
  async savePatient(input) {
    const allowed = ['id', 'fullName', 'customerId', 'examinationDate', 'birthDate', 'sex', 'phone', 'address', 'email', 'occupation', 'complaint', 'notes', 'photoConsent', 'profilePhotoId'];
    if (!input || Object.keys(input).some(key => !allowed.includes(key))) throw new VaultError('INVALID_DATA', 'Kolom pasien tidak dikenal.');
    return this._mutate(input.id ? 'patient_updated' : 'patient_created', input.id || null, ['admin', 'operator'], (state, header, actor) => {
      const prior = input.id ? this._patient(state, input.id, actor) : null;
      const patient = prior || { id: this._id('patient'), recordNumber: `OM-${this._iso().slice(0, 10).replace(/-/g, '')}-${this._id('record').slice(-10).toUpperCase()}`, createdBy: actor.id, createdAt: this._iso(), photoConsent: false };
      const merged = { ...patient, ...clone(input) };
      merged.fullName = cleanText(merged.fullName, 'Nama lengkap', 200, true);
      merged.examinationDate = dateOnly(merged.examinationDate || this._iso().slice(0, 10), 'Tanggal pemeriksaan');
      for (const key of ['customerId', 'sex', 'phone', 'address', 'email', 'occupation', 'complaint', 'notes']) if (merged[key] != null) merged[key] = cleanText(merged[key], key, ['address', 'complaint', 'notes'].includes(key) ? 4000 : 200);
      if (merged.birthDate) dateOnly(merged.birthDate, 'Tanggal lahir');
      if (typeof merged.photoConsent !== 'boolean') throw new VaultError('INVALID_DATA', 'Persetujuan foto harus dipilih secara eksplisit.');
      const deletePhotoIds = [];
      if (merged.photoConsent === false && prior?.profilePhotoId) {
        const profile = state.photos.find(photo => photo.id === prior.profilePhotoId && photo.patientId === patient.id && photo.purpose === 'profile');
        if (profile && !profile.deletedAt) { profile.deletedAt = this._iso(); profile.deletionReason = 'Persetujuan foto profil dicabut'; deletePhotoIds.push(profile.id); }
        merged.profilePhotoId = null;
      }
      if (merged.profilePhotoId) {
        const photo = state.photos.find(p => p.id === merged.profilePhotoId && p.patientId === patient.id && p.purpose === 'profile' && !p.deletedAt);
        if (!photo || !merged.photoConsent) throw new VaultError('CONSENT_REQUIRED', 'Foto profil memerlukan persetujuan dan foto privat milik pasien ini.');
      }
      merged.updatedAt = this._iso(); merged.updatedBy = actor.id;
      if (prior) Object.assign(prior, merged); else state.patients.push(merged);
      return { result: merged, subjectId: merged.id, details: { fields: Object.keys(input).filter(key => key !== 'id').sort(), profilePhotosDeleted: deletePhotoIds.length }, deletePhotoIds };
    });
  }
  _attachPhotos(state, data, patientId, sessionId, actor) {
    for (const id of photoIds(data)) {
      const photo = requireFound(state.photos.find(p => p.id === id && p.patientId === patientId), 'Foto');
      // Old revisions retain references to intentional deletion tombstones.
      // Only a new attachment must still contain readable, unexpired bytes.
      if (photo.sessionId !== sessionId && (photo.deletedAt || (photo.expiresAt && Date.parse(photo.expiresAt) <= this._time()))) throw new VaultError('PHOTO_EXPIRED', 'Foto baru sudah dihapus atau melewati masa retensi.');
      if (photo.sessionId && photo.sessionId !== sessionId) throw new VaultError('INVALID_DATA', 'Foto sudah terkait sesi lain.');
      this._patient(state, photo.patientId, actor);
      if (photo.purpose === 'capture') photo.sessionId = sessionId;
    }
  }
  async createSession({ patientId, raw = {}, algorithmVersion = 'optifit-1.0.0', device = {}, consents = {}, examinationDate } = {}) {
    assertJSON(raw); assertJSON(device); assertJSON(consents);
    return this._mutate('session_created', null, ['admin', 'operator'], (state, header, actor) => {
      const patient = this._patient(state, patientId, actor);
      const id = this._id('session'), revisionId = this._id('revision'), createdAt = this._iso();
      this._attachPhotos(state, raw, patientId, id, actor);
      const session = {
        id, patientId, examinationDate: dateOnly(examinationDate || raw.examinationDate || patient.examinationDate, 'Tanggal pemeriksaan'),
        raw: clone(raw), currentRevisionId: revisionId, latestRevisionId: revisionId, status: 'draft',
        algorithmVersion: cleanText(algorithmVersion, 'Versi algoritma', 100, true), device: clone(device), consents: clone(consents),
        createdBy: actor.id, operatorId: actor.id, operatorName: actor.displayName, createdAt, updatedAt: createdAt,
      };
      const revision = { id: revisionId, sessionId: id, parentRevisionId: null, data: clone(raw), reason: 'Pencatatan awal', actorId: actor.id, actorName: actor.displayName, createdAt, algorithmVersion: session.algorithmVersion };
      state.sessions.push(session); state.revisions.push(revision);
      return { result: session, subjectId: id, details: { revisionId, patientId } };
    });
  }
  async appendRevision(sessionId, { data, reason, expectedRevisionId, algorithmVersion } = {}) {
    assertJSON(data); const explanation = requiredReason(reason);
    return this._mutate('revision_appended', sessionId, ['admin', 'operator'], (state, header, actor) => {
      const session = this._session(state, sessionId, actor);
      if (!expectedRevisionId || session.currentRevisionId !== expectedRevisionId) throw new VaultError('CONFLICT', 'Revisi dasar berubah. Muat ulang sesi sebelum menyimpan koreksi.');
      this._attachPhotos(state, data, session.patientId, sessionId, actor);
      const revision = { id: this._id('revision'), sessionId, parentRevisionId: session.currentRevisionId, data: clone(data), reason: explanation, actorId: actor.id, actorName: actor.displayName, createdAt: this._iso(), algorithmVersion: cleanText(algorithmVersion || data.algorithmVersion || session.algorithmVersion, 'Versi algoritma', 100, true) };
      state.revisions.push(revision); session.currentRevisionId = revision.id; session.latestRevisionId = revision.id; session.status = 'draft'; session.updatedAt = this._iso();
      return { result: revision, details: { revisionId: revision.id, parentRevisionId: revision.parentRevisionId, reason: explanation } };
    });
  }
  async submitSession(sessionId, { expectedRevisionId } = {}) {
    return this._mutate('session_submitted', sessionId, ['admin', 'operator'], (state, header, actor) => {
      const session = this._session(state, sessionId, actor);
      if (expectedRevisionId && session.currentRevisionId !== expectedRevisionId) throw new VaultError('CONFLICT', 'Revisi berubah sebelum diajukan.');
      if (session.status === 'approved') throw new VaultError('IMMUTABLE', 'Hasil yang sudah disetujui memerlukan revisi baru sebelum diajukan ulang.');
      const revision = requireFound(state.revisions.find(row => row.id === session.currentRevisionId), 'Revisi');
      const policy = evaluateSubmission(revision.data, { session, settings: state.settings });
      if (!policy.valid) throw new VaultError('INVALID_SUBMISSION', policy.errors.join('\n'));
      session.status = policy.status; session.updatedAt = this._iso();
      return { result: session, details: { revisionId: revision.id, status: session.status, warnings: policy.warnings || [] } };
    });
  }
  async reviewSession(sessionId, { decision, note = '', evidence, manualVerification, expectedRevisionId, revisionId } = {}) {
    const reviewNote = cleanText(note, 'Catatan review', 4000, decision !== 'approved');
    const proof = clone(evidence || manualVerification || {}); assertJSON(proof);
    return this._mutate('session_reviewed', sessionId, ['admin', 'reviewer'], (state, header, actor) => {
      const session = this._session(state, sessionId, actor);
      const expected = expectedRevisionId || revisionId;
      if (!expected || session.currentRevisionId !== expected) throw new VaultError('CONFLICT', 'Revisi berubah atau belum dipilih. Muat ulang hasil sebelum review.');
      const revision = requireFound(state.revisions.find(row => row.id === session.currentRevisionId), 'Revisi');
      const policy = evaluateReview({ session, revision, actor, decision, evidence: proof, settings: state.settings });
      if (!policy.allowed) throw new VaultError('REVIEW_REJECTED', policy.reasons.join('\n'));
      const review = { id: this._id('review'), sessionId, revisionId: revision.id, reviewerId: actor.id, reviewerName: actor.displayName, decision, note: reviewNote, evidence: proof, createdAt: this._iso() };
      state.reviews.push(review); session.status = decision; session.updatedAt = this._iso(); session.latestReviewId = review.id;
      return { result: review, details: { reviewId: review.id, revisionId: revision.id, decision } };
    });
  }
  async putPhoto({ patientId, sessionId = null, blob, consent, metadata = {} } = {}) {
    this._ensureUnlocked(); const generation = this._generation;
    if (consent !== true) throw new VaultError('CONSENT_REQUIRED', 'Penyimpanan foto memerlukan persetujuan eksplisit.');
    if (!blob || typeof blob.size !== 'number' || blob.size <= 0 || blob.size > PHOTO_LIMIT_BYTES || !['image/jpeg', 'image/png', 'image/webp'].includes(blob.type)) throw new VaultError('INVALID_IMAGE', 'Gunakan JPG, PNG atau WebP maksimal 8 MiB.');
    const allowed = ['width', 'height', 'view', 'purpose', 'capturedAt', 'source'];
    if (Object.keys(metadata).some(key => !allowed.includes(key))) throw new VaultError('INVALID_DATA', 'Metadata foto tidak dikenal.');
    if ((metadata.width !== undefined || metadata.height !== undefined) && (!Number.isInteger(metadata.width) || !Number.isInteger(metadata.height) || metadata.width <= 0 || metadata.height <= 0 || metadata.width * metadata.height > 20000000)) throw new VaultError('INVALID_IMAGE', 'Ukuran foto tidak valid atau melampaui 20 megapiksel.');
    const purpose = metadata.purpose || 'capture';
    if (!['capture', 'profile'].includes(purpose)) throw new VaultError('INVALID_DATA', 'Tujuan foto tidak dikenal.');
    const bytes = await blobBytes(blob);
    if (generation !== this._generation) { bytes.fill(0); throw new VaultError('LOCKED', 'Pembacaan foto dibatalkan karena vault dikunci.'); }
    const jpg = bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255;
    const png = [137, 80, 78, 71, 13, 10, 26, 10].every((b, i) => bytes[i] === b);
    const webp = String.fromCharCode(...bytes.subarray(0, 4)) === 'RIFF' && String.fromCharCode(...bytes.subarray(8, 12)) === 'WEBP';
    if (!(blob.type === 'image/jpeg' && jpg) && !(blob.type === 'image/png' && png) && !(blob.type === 'image/webp' && webp)) { bytes.fill(0); throw new VaultError('INVALID_IMAGE', 'Isi berkas tidak cocok dengan format gambar.'); }
    try {
      return await this._mutate('photo_stored', null, ['admin', 'operator'], async (state, header, actor) => {
        this._patient(state, patientId, actor);
        if (sessionId && this._session(state, sessionId, actor).patientId !== patientId) throw new VaultError('INVALID_DATA', 'Foto dan sesi berasal dari pasien berbeda.');
        const id = this._id('photo'), createdAt = this._iso();
        const photo = { id, patientId, sessionId, purpose, mimeType: blob.type, bytes: bytes.byteLength, ...clone(metadata), createdAt, consentedAt: createdAt, createdBy: actor.id, expiresAt: new Date(this._time() + state.settings.photoRetentionDays * 86400000).toISOString(), deletedAt: null };
        const encrypted = await encryptBytes(this._key, bytes, aad(header, 'photo', id), this.crypto);
        state.photos.push(photo);
        return { result: id, subjectId: id, details: { patientId, sessionId, purpose }, putPhotos: [{ id, envelope: encrypted }] };
      });
    } finally { bytes.fill(0); }
  }
  async getPhoto(id) {
    const { state, header, generation } = await this._readUnlocked(), actor = this._actor(state);
    const photo = requireFound(state.photos.find(row => row.id === id && !row.deletedAt), 'Foto');
    this._patient(state, photo.patientId, actor);
    if (Date.parse(photo.expiresAt) <= this._time()) throw new VaultError('PHOTO_EXPIRED', 'Masa retensi foto telah berakhir.');
    const key = this._key;
    const record = requireFound(await this.store.getPhoto(id), 'Foto privat');
    if (generation !== this._generation) throw new VaultError('LOCKED', 'Vault dikunci saat foto dibaca.');
    const bytes = await decryptBytes(key, record.envelope, aad(header, 'photo', id), this.crypto);
    try {
      if (generation !== this._generation) throw new VaultError('LOCKED', 'Vault dikunci saat foto dibaca.');
      return new Blob([bytes], { type: photo.mimeType });
    } finally { bytes.fill(0); }
  }
  async deletePhoto(id, { reason, confirmed = true } = {}) {
    const explanation = requiredReason(reason);
    if (confirmed !== true) throw new VaultError('CONFIRMATION_REQUIRED', 'Konfirmasi penghapusan foto diperlukan.');
    return this._mutate('photo_deleted', id, ['admin', 'operator'], (state, header, actor) => {
      const photo = requireFound(state.photos.find(row => row.id === id && !row.deletedAt), 'Foto');
      const patient = this._patient(state, photo.patientId, actor);
      photo.deletedAt = this._iso(); photo.deletionReason = explanation;
      if (patient.profilePhotoId === id) patient.profilePhotoId = null;
      return { result: photo, details: { reason: explanation, patientId: photo.patientId }, deletePhotoIds: [id] };
    });
  }
  async _applyRetention() {
    return this._mutate('retention_policy_applied', null, ROLES, (state) => {
      const expired = state.photos.filter(photo => !photo.deletedAt && Date.parse(photo.expiresAt) <= this._time());
      const ids = expired.map(photo => photo.id);
      for (const photo of expired) { photo.deletedAt = this._iso(); photo.deletionReason = 'Masa retensi berakhir'; }
      for (const patient of state.patients) if (ids.includes(patient.profilePhotoId)) patient.profilePhotoId = null;
      return { result: { count: ids.length }, details: { count: ids.length, photoIds: ids }, deletePhotoIds: ids };
    });
  }
  async purgeExpiredPhotos({ confirmed } = {}) {
    if (confirmed !== true) throw new VaultError('CONFIRMATION_REQUIRED', 'Konfirmasi penerapan retensi diperlukan.');
    return this._mutate('expired_photos_purged', null, ['admin'], (state) => {
      const expired = state.photos.filter(photo => !photo.deletedAt && Date.parse(photo.expiresAt) <= this._time());
      const ids = expired.map(photo => photo.id);
      for (const photo of expired) { photo.deletedAt = this._iso(); photo.deletionReason = 'Masa retensi berakhir'; }
      for (const patient of state.patients) if (ids.includes(patient.profilePhotoId)) patient.profilePhotoId = null;
      return { result: { count: expired.length }, details: { count: expired.length, photoIds: ids }, deletePhotoIds: ids };
    });
  }
  async deletePatient(id, { confirmation, reason } = {}) {
    const explanation = requiredReason(reason);
    return this._mutate('patient_permanently_deleted', id, ['admin'], (state, header, actor) => {
      const patient = this._patient(state, id, actor);
      if (confirmation !== patient.recordNumber) throw new VaultError('CONFIRMATION_REQUIRED', 'Ketik nomor rekam yang tepat untuk menghapus pasien secara permanen.');
      const sessionIds = new Set(state.sessions.filter(session => session.patientId === id).map(session => session.id));
      const ids = state.photos.filter(photo => photo.patientId === id).map(photo => photo.id);
      state.patients = state.patients.filter(row => row.id !== id);
      state.sessions = state.sessions.filter(row => row.patientId !== id);
      state.revisions = state.revisions.filter(row => !sessionIds.has(row.sessionId));
      state.reviews = state.reviews.filter(row => !sessionIds.has(row.sessionId));
      state.photos = state.photos.filter(row => row.patientId !== id);
      // Audit retains opaque IDs/hashes, not a copy of patient/session contents.
      return { result: { deleted: true }, details: { reason: explanation, sessionsDeleted: sessionIds.size, photosDeleted: ids.length }, deletePhotoIds: ids };
    });
  }
  async recordExport({ sessionId, revisionId, format, confirmed, includePhoto = false, photoIds: selectedPhotoIds = [] } = {}) {
    if (confirmed !== true || !['pdf', 'csv', 'json', 'print'].includes(format)) throw new VaultError('CONFIRMATION_REQUIRED', 'Pilih format dan konfirmasikan ekspor data.');
    return this._mutate('report_exported', sessionId, ROLES, (state, header, actor) => {
      const session = this._session(state, sessionId, actor);
      const revision = state.revisions.find(row => row.id === (revisionId || session.currentRevisionId) && row.sessionId === sessionId);
      requireFound(revision, 'Revisi');
      if (typeof includePhoto !== 'boolean') throw new VaultError('INVALID_DATA', 'Pilihan thumbnail tidak valid.');
      if (includePhoto) {
        if (!revisionId || revision.data?.consents?.thumbnail !== true) throw new VaultError('CONSENT_REQUIRED', 'Thumbnail memerlukan persetujuan pada revisi yang dipilih dan konfirmasi ekspor.');
        const referenced = new Set(photoIds(revision.data));
        if (!Array.isArray(selectedPhotoIds) || !selectedPhotoIds.length || selectedPhotoIds.length > 3 || new Set(selectedPhotoIds).size !== selectedPhotoIds.length) throw new VaultError('INVALID_SELECTION', 'Pilih secara eksplisit satu sampai tiga thumbnail dari revisi ini.');
        if (selectedPhotoIds.some(id => !referenced.has(id) || !state.photos.some(photo => photo.id === id && photo.patientId === session.patientId && !photo.deletedAt && Date.parse(photo.expiresAt) > this._time()))) throw new VaultError('PHOTO_UNAVAILABLE', 'Foto pada revisi ini sudah dihapus, kedaluwarsa, atau tidak dapat diakses.');
      }
      return { result: { exported: true }, details: { format, revisionId: revision.id, includePhoto, photoIds: includePhoto ? selectedPhotoIds : [], status: session.status } };
    });
  }
  async verifyAudit() { const { state } = await this._readUnlocked(); return verifyAudit(state, this.crypto); }
  async exportBackup(passphrase, { confirmed } = {}) {
    this._ensureUnlocked(); const requestedGeneration = this._generation;
    if (confirmed !== true) throw new VaultError('CONFIRMATION_REQUIRED', 'Konfirmasi ekspor backup diperlukan.');
    validateSecret(passphrase, { backup: true });
    await this._mutate('encrypted_backup_exported', null, ['admin'], () => ({ details: { format: 'optifit-backup-v1' } }));
    this._ensureUnlocked(); const generation = this._generation;
    if (requestedGeneration !== generation) throw new VaultError('LOCKED', 'Backup dari sesi sebelumnya dibatalkan.');
    const record = await this.store.read(true);
    if (!sameIdentity(record.header, this._header)) throw new VaultError('CONFLICT', 'Data berubah saat backup disiapkan. Coba lagi.');
    if (generation !== this._generation) throw new VaultError('LOCKED', 'Backup dibatalkan karena vault dikunci.');
    const dataKey = bytesToBase64(this._keyBytes);
    const salt = randomBytes(32, this.crypto), key = await deriveKey(passphrase, salt, this.crypto);
    const kdf = { name: 'PBKDF2', hash: 'SHA-256', iterations: KDF_ITERATIONS, salt: bytesToBase64(salt) };
    const payload = { format: 'optifit-backup-payload-v1', createdAt: this._iso(), dataKey, ...record };
    const encrypted = await encryptJSON(key, payload, `optifit-backup:v1:${kdf.salt}`, this.crypto);
    if (generation !== this._generation) throw new VaultError('LOCKED', 'Backup dibatalkan karena vault terkunci.');
    const blob = new Blob([JSON.stringify({ format: 'optifit-backup-v1', kdf, encrypted })], { type: 'application/json' });
    if (blob.size > MAX_BACKUP_BYTES) throw new VaultError('TOO_LARGE', 'Backup melebihi batas 192 MiB. Tinjau retensi foto sebelum membuat backup.');
    return blob;
  }
  async restoreBackup(blob, passphrase, { confirmed, replaceConfirmation } = {}) {
    if (confirmed !== true) throw new VaultError('CONFIRMATION_REQUIRED', 'Konfirmasi pemulihan backup diperlukan.');
    if (!blob || blob.size <= 0 || blob.size > MAX_BACKUP_BYTES) throw new VaultError('INVALID_BACKUP', 'Berkas backup tidak valid atau melebihi 192 MiB.');
    const current = await this.store.read();
    if (current.header) {
      await this._readUnlocked(); this._actor(this._state, ['admin']);
      if (replaceConfirmation !== 'GANTI VAULT') throw new VaultError('CONFIRMATION_REQUIRED', 'Pemulihan mengganti seluruh vault aktif. Ketik GANTI VAULT setelah membuat backup data sekarang.');
    }
    const generation = this._generation;
    let envelope;
    try { envelope = JSON.parse(await blobText(blob)); } catch { throw new VaultError('INVALID_BACKUP', 'Berkas backup bukan JSON yang valid.'); }
    if (envelope?.format !== 'optifit-backup-v1') throw new VaultError('INVALID_BACKUP', 'Format backup tidak didukung.');
    assertKdf(envelope.kdf);
    const wrappingKey = await deriveKey(passphrase, base64ToBytes(envelope.kdf.salt, 32), this.crypto);
    const payload = await decryptJSON(wrappingKey, envelope.encrypted, `optifit-backup:v1:${envelope.kdf.salt}`, this.crypto);
    if (payload?.format !== 'optifit-backup-payload-v1' || !Array.isArray(payload.photos)) throw new VaultError('INVALID_BACKUP', 'Isi backup tidak lengkap.');
    validateHeader(payload.header);
    const bytes = base64ToBytes(payload.dataKey, 32);
    try {
      const key = await importDataKey(bytes, this.crypto);
      const state = await decryptJSON(key, payload.state, aad(payload.header, 'state', payload.header.revision), this.crypto);
      validateState(state, payload.header); await verifyAudit(state, this.crypto);
      const photoById = new Map(payload.photos.map(photo => [photo.id, photo]));
      if (photoById.size !== payload.photos.length) throw new VaultError('INVALID_BACKUP', 'Backup memuat foto duplikat.');
      const expected = state.photos.filter(photo => !photo.deletedAt);
      if (expected.length !== payload.photos.length) throw new VaultError('INVALID_BACKUP', 'Jumlah foto backup tidak cocok.');
      for (const photo of expected) {
        const encrypted = requireFound(photoById.get(photo.id), 'Foto backup');
        const verified = await decryptBytes(key, encrypted.envelope, aad(payload.header, 'photo', photo.id), this.crypto);
        if (verified.length !== photo.bytes) throw new VaultError('INVALID_BACKUP', 'Ukuran foto backup tidak cocok.');
        verified.fill(0);
      }
      if (generation !== this._generation) throw new VaultError('LOCKED', 'Pemulihan dibatalkan karena vault dikunci.');
      // Append a restoration event without claiming trusted independent time.
      const beforeHash = await stateDigest(state, this.crypto);
      const header = clone(payload.header); header.revision += 1; state.revision = header.revision; state.updatedAt = this._iso();
      await appendAudit(state, { action: 'encrypted_backup_restored', actor: null, details: { priorRevision: payload.header.revision }, beforeHash, timestamp: this._iso() }, this.crypto);
      const encryptedState = await encryptJSON(key, state, aad(header, 'state', header.revision), this.crypto);
      await this.store.commit(current.header, header, encryptedState, { replace: true, putPhotos: payload.photos, guard: () => generation === this._generation });
      this.lock('backup-restored'); this._channel?.postMessage({ changed: true });
      return { restored: true, users: header.credentials.map(c => ({ id: c.id, username: c.username })) };
    } finally { bytes.fill(0); }
  }
  async destroy({ confirmation } = {}) {
    const { state, header } = await this._readUnlocked(); this._actor(state, ['admin']);
    if (confirmation !== 'HAPUS VAULT') throw new VaultError('CONFIRMATION_REQUIRED', 'Ketik HAPUS VAULT untuk menghapus seluruh data lokal.');
    await this.store.clear(header); this.lock('vault-deleted'); this._channel?.postMessage({ changed: true });
    return { deleted: true };
  }
  async persistence() {
    if (!globalThis.navigator?.storage) return { available: false, persisted: false };
    try { return { available: true, persisted: await navigator.storage.persisted(), ...(await navigator.storage.estimate()) }; }
    catch { return { available: false, persisted: false }; }
  }
  async requestPersistence() {
    if (!globalThis.navigator?.storage?.persist) return false;
    try { return await navigator.storage.persist(); } catch { return false; }
  }
  close() { this.lock('closed'); this._channel?.close(); this._channel = null; return this.store.close(); }
}

export const vault = new OptiFitVault();
