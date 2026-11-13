/** Application assets only. Never cache patient data, API responses or images. */
export async function prepareOffline() {
  if (!globalThis.isSecureContext || !('serviceWorker' in navigator)) return { ready: false, reason: 'Mode offline memerlukan HTTPS/localhost dan browser dengan service worker.' };
  if (process.env.NODE_ENV !== 'production') return { ready: false, reason: 'Mode offline tersedia pada build produksi setelah pemasangan pertama.' };
  try {
    const registration = await navigator.serviceWorker.register('/meowsurement/sw.js', { scope: '/meowsurement/' });
    const active = await Promise.race([navigator.serviceWorker.ready, new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 20000))]);
    if (!active.active) return { ready: false, reason: 'Aset offline masih dipasang. Tunggu sebelum memutus koneksi.' };
    const persisted = navigator.storage?.persisted ? await navigator.storage.persisted() : false;
    return { ready: true, persisted, updateWaiting: !!registration.waiting, reason: 'Aset aplikasi tersimpan. Login, profil, riwayat dan penyimpanan pengukuran tetap memerlukan koneksi ke Meow Eyes.' };
  } catch {
    return { ready: false, reason: 'Pemasangan aset belum selesai. Hubungkan internet dan muat ulang untuk menggunakan Meowsurement.' };
  }
}
