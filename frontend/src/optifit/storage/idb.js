import { VaultError } from './crypto';

const STORES = ['meta', 'state', 'photos'];
const conflict = () => new VaultError('CONFLICT', 'Data diubah di tab lain. Buka ulang vault sebelum melanjutkan agar revisi tidak tertimpa.');

/** Crypto runs before opening write transactions. All writes below are atomic. */
export class IndexedDBStore {
  constructor(name = 'optifit-meowsurement-v1', factory = globalThis.indexedDB) { this.name = name; this.factory = factory; this.connection = null; }
  async open() {
    if (this.connection) return this.connection;
    if (!this.factory) throw new VaultError('STORAGE_UNAVAILABLE', 'IndexedDB tidak tersedia. Penyimpanan plaintext tidak digunakan sebagai pengganti.');
    this.connection = new Promise((resolve, reject) => {
      const request = this.factory.open(this.name, 1);
      request.onupgradeneeded = () => { for (const name of STORES) if (!request.result.objectStoreNames.contains(name)) request.result.createObjectStore(name); };
      request.onerror = () => { this.connection = null; reject(new VaultError('STORAGE_UNAVAILABLE', 'Penyimpanan privat tidak dapat dibuka. Periksa izin dan kapasitas browser.')); };
      request.onblocked = () => { this.connection = null; reject(new VaultError('STORAGE_BLOCKED', 'Tutup tab OptiFit lain sebelum membuka versi penyimpanan ini.')); };
      request.onsuccess = () => {
        const db = request.result;
        db.onversionchange = () => { db.close(); this.connection = null; };
        resolve(db);
      };
    });
    return this.connection;
  }
  async read(includePhotos = false) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(includePhotos ? STORES : ['meta', 'state'], 'readonly');
      const header = transaction.objectStore('meta').get('header');
      const state = transaction.objectStore('state').get('encrypted');
      const photos = includePhotos ? transaction.objectStore('photos').getAll() : null;
      transaction.oncomplete = () => resolve({ header: header.result || null, state: state.result || null, ...(photos ? { photos: photos.result } : {}) });
      transaction.onerror = transaction.onabort = () => reject(new VaultError('STORAGE_READ_FAILED', 'Data privat tidak dapat dibaca.'));
    });
  }
  async commit(expected, header, state, { putPhotos = [], deletePhotoIds = [], replace = false, guard = () => true } = {}) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORES, 'readwrite');
      let rejection;
      const check = transaction.objectStore('meta').get('header');
      check.onsuccess = () => {
        if (!guard()) { rejection = new VaultError('LOCKED', 'Perubahan dibatalkan karena vault dikunci.'); transaction.abort(); return; }
        const current = check.result;
        if (expected === null ? !!current : !current || current.id !== expected.id || current.revision !== expected.revision) {
          rejection = conflict(); transaction.abort(); return;
        }
        if (replace) { for (const name of STORES) transaction.objectStore(name).clear(); }
        transaction.objectStore('meta').put(header, 'header');
        transaction.objectStore('state').put(state, 'encrypted');
        for (const photo of putPhotos) transaction.objectStore('photos').put(photo, photo.id);
        for (const id of deletePhotoIds) transaction.objectStore('photos').delete(id);
      };
      transaction.oncomplete = () => resolve();
      transaction.onerror = transaction.onabort = () => reject(rejection || new VaultError(transaction.error?.name === 'QuotaExceededError' ? 'STORAGE_FULL' : 'STORAGE_WRITE_FAILED', 'Perubahan tidak tersimpan. Periksa kapasitas/izin browser; data sebelumnya tetap dipertahankan.'));
    });
  }
  async getPhoto(id) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('photos', 'readonly'), request = transaction.objectStore('photos').get(id);
      transaction.oncomplete = () => resolve(request.result || null);
      transaction.onerror = transaction.onabort = () => reject(new VaultError('STORAGE_READ_FAILED', 'Foto privat tidak dapat dibaca.'));
    });
  }
  async authState(id, failureAt = null, reset = false) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('meta', failureAt != null || reset ? 'readwrite' : 'readonly');
      const store = transaction.objectStore('meta'), request = store.get(`auth:${id}`); let result;
      request.onsuccess = () => {
        result = request.result || { failures: 0, nextAttemptAt: 0 };
        if (reset) result = { failures: 0, nextAttemptAt: 0 };
        else if (failureAt != null) {
          const failures = result.failures + 1;
          result = { failures, nextAttemptAt: failureAt + (failures < 5 ? 0 : Math.min(900000, 30000 * (2 ** Math.min(failures - 5, 10)))) };
        }
        if (failureAt != null || reset) store.put(result, `auth:${id}`);
      };
      transaction.oncomplete = () => resolve(result);
      transaction.onerror = transaction.onabort = () => reject(new VaultError('STORAGE_WRITE_FAILED', 'Status penguncian tidak dapat diperbarui.'));
    });
  }
  async clear(expected) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORES, 'readwrite'); let rejection;
      const check = transaction.objectStore('meta').get('header');
      check.onsuccess = () => {
        if (!check.result || check.result.id !== expected.id || check.result.revision !== expected.revision) { rejection = conflict(); transaction.abort(); return; }
        for (const name of STORES) transaction.objectStore(name).clear();
      };
      transaction.oncomplete = () => resolve();
      transaction.onabort = transaction.onerror = () => reject(rejection || new VaultError('STORAGE_WRITE_FAILED', 'Vault tidak dapat dihapus.'));
    });
  }
  async close() { if (this.connection) (await this.connection).close(); this.connection = null; }
}
