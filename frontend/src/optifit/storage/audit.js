import { canonical, digest, VaultError } from './crypto';

function businessState(state) { const data = { ...state }; delete data.audit; return data; }
export async function stateDigest(state, provider) { return digest(businessState(state), provider); }
export async function appendAudit(state, { action, actor, subjectId = null, details = {}, beforeHash = null, timestamp }, provider) {
  const previous = state.audit[state.audit.length - 1];
  const event = {
    sequence: state.audit.length + 1, timestamp,
    action, actorId: actor?.id || null, subjectId,
    details, beforeHash, afterHash: await stateDigest(state, provider),
    previousHash: previous?.hash || null,
  };
  const record = { ...event, hash: await digest(event, provider) };
  state.audit.push(record); return record;
}
export async function verifyAudit(state, provider) {
  if (!Array.isArray(state?.audit) || !state.audit.length) throw new VaultError('AUDIT_INVALID', 'Audit penyimpanan tidak tersedia.');
  let previous = null;
  for (let index = 0; index < state.audit.length; index += 1) {
    const { hash, ...event } = state.audit[index];
    if (event.sequence !== index + 1 || event.previousHash !== (previous?.hash || null)
      || event.beforeHash !== (previous?.afterHash || null)
      || hash !== await digest(event, provider)) {
      throw new VaultError('AUDIT_INVALID', 'Rantai audit berubah atau tidak lengkap. Data dikunci untuk pemeriksaan.');
    }
    previous = { ...event, hash };
  }
  if (previous.afterHash !== await stateDigest(state, provider)) throw new VaultError('AUDIT_INVALID', 'Data tidak cocok dengan catatan audit terakhir.');
  return { valid: true, events: state.audit.length, head: previous.hash };
}
export function assertJSON(value, { allowOrganizationLogo = false } = {}) {
  const result = canonical(value);
  if (result.length > 16 * 1024 * 1024) throw new VaultError('TOO_LARGE', 'Data sesi terlalu besar. Simpan gambar melalui penyimpanan foto terpisah.');
  const inspected = allowOrganizationLogo && value?.organization ? canonical({ ...value, organization: { ...value.organization, logoDataUrl: null } }) : result;
  if (/data:image\//i.test(inspected)) throw new VaultError('RAW_IMAGE_IN_STATE', 'Foto harus disimpan terpisah dengan persetujuan; gunakan photoId pada data sesi.');
  return value;
}
