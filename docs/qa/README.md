# Bukti browser QA

Diambil pada 6 November 2026 dari build produksi `main.5e6c2ed9.js` memakai
Chromium 153, FastAPI dan SQLite terisolasi. Pembayaran/ongkir memakai mode mock.
Model frame, foto wajah, akun dan alamat adalah fixture QA sintetis.
Screenshot bukan transaksi pelanggan atau kalibrasi aset toko.

- [Hasil pelanggan: 11 passed](customer-browser-results.json)
- [Hasil admin: 11 passed](admin-results.json)
- [Checkout mobile dan resep](customer-checkout-mobile.png)
- [Renderer GLB dengan foto lokal](customer-try-on-glb.png)
- [Manajemen Flash Sale kategori](admin-flash-sale.png)

Kedua sesi mencatat nol JavaScript page error. Lihat
[laporan validasi lengkap](../mysql-migration/VALIDATION.md) untuk lingkup dan
batas pengujian. Kamera QA menggunakan perangkat browser tiruan atau izin yang
ditolak secara sengaja; belum ada pengujian hardware pelanggan.
