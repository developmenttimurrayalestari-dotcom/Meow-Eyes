/** Browser-native authenticated encryption. No plaintext or key is persisted. */
export const KDF_ITERATIONS = 600000;
export const MAX_BACKUP_BYTES = 192 * 1024 * 1024;

export class VaultError extends Error {
  constructor(code, message) { super(message); this.name = 'VaultError'; this.code = code; }
}

export function cryptoProvider(provider = globalThis.crypto) {
  if (!provider?.subtle || typeof provider.getRandomValues !== 'function') {
    throw new VaultError('CRYPTO_UNAVAILABLE', 'Enkripsi perangkat tidak tersedia. Gunakan HTTPS atau localhost pada browser yang mendukung WebCrypto.');
  }
  return provider;
}
export function bytesToBase64(value) {
  const bytes = value instanceof Uint8Array ? value : new Uint8Array(value);
  let binary = '';
  for (let i = 0; i < bytes.length; i += 16384) binary += String.fromCharCode(...bytes.subarray(i, i + 16384));
  return btoa(binary);
}
export function base64ToBytes(value, limit = MAX_BACKUP_BYTES) {
  if (typeof value !== 'string' || value.length > Math.ceil(limit * 4 / 3) + 8 || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
    throw new VaultError('INVALID_ENVELOPE', 'Format berkas terenkripsi tidak valid.');
  }
  const binary = atob(value);
  if (binary.length > limit) throw new VaultError('TOO_LARGE', 'Ukuran data melebihi batas aplikasi.');
  return Uint8Array.from(binary, c => c.charCodeAt(0));
}
export function randomBytes(length, provider) { return cryptoProvider(provider).getRandomValues(new Uint8Array(length)); }
export function opaqueId(prefix, provider) { return `${prefix}_${Array.from(randomBytes(16, provider), b => b.toString(16).padStart(2, '0')).join('')}`; }
export function clone(value) { return value == null ? value : JSON.parse(JSON.stringify(value)); }
export function canonical(value, depth = 0) {
  if (depth > 60) throw new VaultError('INVALID_DATA', 'Struktur data terlalu dalam.');
  if (value === null || typeof value === 'boolean' || typeof value === 'string') return JSON.stringify(value);
  if (typeof value === 'number' && Number.isFinite(value)) return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(v => canonical(v, depth + 1)).join(',')}]`;
  if (value && Object.getPrototypeOf(value) === Object.prototype) {
    return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${canonical(value[k], depth + 1)}`).join(',')}}`;
  }
  throw new VaultError('INVALID_DATA', 'Data harus berupa JSON dengan angka terbatas; file gambar disimpan melalui penyimpanan foto privat.');
}
export async function digest(value, provider) {
  const bytes = new TextEncoder().encode(typeof value === 'string' ? value : canonical(value));
  return bytesToBase64(await cryptoProvider(provider).subtle.digest('SHA-256', bytes));
}
export function validateSecret(secret, { backup = false } = {}) {
  if (typeof secret !== 'string' || secret.length > 256 || secret.trim() !== secret || secret.length < (backup ? 12 : 10)) {
    throw new VaultError('WEAK_SECRET', backup ? 'Gunakan frasa sandi backup minimal 12 karakter, tanpa spasi di awal/akhir.' : 'Gunakan frasa sandi minimal 12 karakter atau PIN 10–32 digit, tanpa spasi di awal/akhir.');
  }
  if (/^\d+$/.test(secret)) {
    if (backup || secret.length > 32 || /^(.)\1+$/.test(secret) || '0123456789012345678901234567890123456789'.includes(secret) || '9876543210987654321098765432109876543210'.includes(secret)) {
      throw new VaultError('WEAK_SECRET', 'Pilih frasa sandi yang kuat; PIN berulang/berurutan dan PIN untuk backup tidak diterima.');
    }
  } else if (secret.length < 12) throw new VaultError('WEAK_SECRET', 'Frasa sandi harus minimal 12 karakter.');
  return true;
}
export async function importDataKey(bytes, provider) {
  if (!(bytes instanceof Uint8Array) || bytes.byteLength !== 32) throw new VaultError('INVALID_KEY', 'Kunci penyimpanan tidak valid.');
  return cryptoProvider(provider).subtle.importKey('raw', bytes, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
}
export async function deriveKey(secret, salt, provider) {
  const c = cryptoProvider(provider);
  if (typeof secret !== 'string' || secret.length > 256 || !(salt instanceof Uint8Array) || salt.length !== 32) throw new VaultError('INVALID_KEY', 'Parameter kunci tidak valid.');
  const input = await c.subtle.importKey('raw', new TextEncoder().encode(secret), 'PBKDF2', false, ['deriveKey']);
  return c.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: KDF_ITERATIONS, hash: 'SHA-256' }, input, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
}
export async function encryptBytes(key, bytes, aad, provider) {
  const c = cryptoProvider(provider), iv = randomBytes(12, c);
  const encrypted = await c.subtle.encrypt({ name: 'AES-GCM', iv, additionalData: new TextEncoder().encode(aad), tagLength: 128 }, key, bytes);
  return { algorithm: 'AES-256-GCM', iv: bytesToBase64(iv), ciphertext: bytesToBase64(encrypted) };
}
export async function decryptBytes(key, envelope, aad, provider) {
  if (!envelope || envelope.algorithm !== 'AES-256-GCM') throw new VaultError('INVALID_ENVELOPE', 'Format enkripsi tidak dikenal.');
  const iv = base64ToBytes(envelope.iv, 12);
  if (iv.length !== 12) throw new VaultError('INVALID_ENVELOPE', 'Nonce enkripsi tidak valid.');
  const ciphertext = base64ToBytes(envelope.ciphertext);
  if (ciphertext.length < 16) throw new VaultError('INVALID_ENVELOPE', 'Data terenkripsi tidak lengkap.');
  try {
    return new Uint8Array(await cryptoProvider(provider).subtle.decrypt({ name: 'AES-GCM', iv, additionalData: new TextEncoder().encode(aad), tagLength: 128 }, key, ciphertext));
  } catch {
    throw new VaultError('DECRYPT_FAILED', 'Kunci tidak sesuai atau data terenkripsi telah berubah/rusak.');
  }
}
export async function encryptJSON(key, value, aad, provider) { return encryptBytes(key, new TextEncoder().encode(canonical(value)), aad, provider); }
export async function decryptJSON(key, envelope, aad, provider) {
  const bytes = await decryptBytes(key, envelope, aad, provider);
  try { return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)); }
  catch { throw new VaultError('INVALID_ENVELOPE', 'Isi data terenkripsi tidak valid.'); }
  finally { bytes.fill(0); }
}
export function assertKdf(value) {
  if (!value || value.name !== 'PBKDF2' || value.hash !== 'SHA-256' || value.iterations !== KDF_ITERATIONS || base64ToBytes(value.salt, 32).length !== 32) {
    throw new VaultError('INVALID_ENVELOPE', 'Parameter derivasi kunci tidak didukung.');
  }
}
