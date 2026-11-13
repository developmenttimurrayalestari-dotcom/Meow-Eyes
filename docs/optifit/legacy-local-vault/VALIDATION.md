> Arsip implementasi vault lokal sebelumnya. Dokumen ini tidak menjadi petunjuk alur customer saat ini. Gunakan [dokumentasi aktif](../README.md).

# Verifikasi Meowsurement

Tanggal pengujian: **9 November 2026**. Target backend tetap Oracle MySQL
5.7.24-log. Seluruh pasien, operator, nilai ukur, protokol dan foto yang dipakai
pada QA bersifat sintetis. Hasil di bawah memverifikasi perangkat lunak,
bukan akurasi klinis atau transaksi produksi.

## Hasil yang benar-benar dijalankan

| Pemeriksaan | Hasil | Batas bukti |
| --- | --- | --- |
| Production build | Lulus: npm run build, termasuk generator offline shell | Build lokal; belum deploy ke domain produksi |
| Suite frontend | **92 passed, 9 suites**, tanpa snapshot | 81 tes OptiFit dan 11 regresi storefront/checkout/product detail |
| Browser produksi | **10/10 skenario lulus**, nol uncaught page error | Chromium 153.0.8010.0, Linux, viewport desktop dan mobile |
| Bootstrap storefront | **1 smoke lulus**: font eksternal diblokir, navigasi toko tetap tampil dan membuka gate privat | API fixture sengaja 503; bukan transaksi atau katalog backend nyata |
| IndexedDB | Vault, pasien, revisi dan ciphertext foto diuji pada IndexedDB browser asli | Bukan pembuktian terhadap perangkat/JS yang telah dikompromikan |
| Offline | Reload, unlock, baca data dan PDF berhasil saat jaringan browser dimatikan | Application shell sebelumnya telah disiapkan online |
| Kamera | Izin, burst, ciphertext, stop saat lock | Perangkat kamera tiruan browser; bukan ponsel/lensa fisik |
| Backup/restore | Ekspor terenkripsi, salah passphrase ditolak, restore pada proses browser baru berhasil | Pengujian dengan data sintetis terkontrol |
| PDF | PDF A4 tiga halaman dari aplikasi, font lokal; seluruh halaman dirender, teks/batas halaman diperiksa | Fixture manual PD, tanpa thumbnail pasien |
| Backend existing | Hash **85/85 berkas backend sama** dengan rilis 6 November | Tidak ada perubahan backend baru yang memerlukan migrasi |
| SQL OptiFit opsional | 16 tabel, 61 FK, 13 trigger; review statis/dialect target 5.7.24 | Tidak dijalankan pada server MySQL nyata; bukan runtime sync |

Ringkasan terstruktur browser tersedia pada
[BROWSER_VALIDATION.json](BROWSER_VALIDATION.json).
Screenshot dan unduhan data pasien QA digunakan untuk pemeriksaan internal,
bukan isi paket sumber.

## Cakupan suite OptiFit

- **Domain, 14 tes:** input nol/kosong/desimal, resep dan axis, ukuran frame,
  identifikasi metode kamera, submission, near PD, review independen,
  kualitas rendah, revisi stale, foto duplikat, aturan administrator,
  invalidasi konteks dan round-trip canonical JSON.
- **Storage, 17 tes:** enkripsi nyata/WebCrypto, kredensial salah, tampering,
  peran/ownership, revisi immutable, stale write, approval, consent/retensi,
  backup/restore, lock, revocation dan audit.
- **Vision/editor/kamera, 30 tes:** homography dan degenerasi, bidang/horizon,
  independent PD, near, vertex, panto, transpose, manual input, outlier,
  batas kualitas, izin/lifecycle, decode/dimensi dan editor read-only.
- **UI/aggregation, 11 tes:** PD asimetris, duplikasi sumber, near/context,
  consent terpisah dari checklist, alasan koreksi, ekspor/audit/lock,
  PHI pada lock, serta median panto dan sumber head pitch.
- **Reports, 9 tes:** exact patient/revision, bukti approval, lingkup
  parameter final, penghilangan foto default, injection CSV/HTML,
  nilai tidak tersedia, JSON, consent/ownership thumbnail dan syarat
  decentration yang sama dengan UI.

Tes storage menggunakan WebCrypto asli dengan adapter store terkontrol.
Perilaku native IndexedDB diuji terpisah oleh browser E2E, sehingga kelulusan
adapter tidak dianggap sebagai bukti kemampuan browser.

## Sepuluh skenario browser

1. Entry privat memuat aplikasi tanpa API, analytics atau aset pihak ketiga.
2. Membuat vault, reviewer terpisah dan pasien; plaintext sensitif tidak
   ditemukan dalam record IndexedDB yang disimpan.
3. Menyalin resep, melihat transpose tanpa overwrite, menyimpan OD 31 dan OS
   33 mm, lalu review setelah round-trip enkripsi. Operator tidak dapat
   menyetujui pekerjaannya sendiri.
4. JSON/CSV mempertahankan prescription asli, PD terpisah, status, provenance
   dan scope; foto tidak ikut secara default.
5. Service worker menyiapkan aset statis; reload/unlock dan PDF bekerja
   offline tanpa mengambil font/logo dari internet.
6. Hasil tampil pada viewport 390 × 844 dalam tema terang/gelap tanpa
   horizontal overflow halaman.
7. Perubahan A frame 50 menjadi 52 membatalkan hasil revisi aktif; revisi
   historis yang disetujui tetap dapat diekspor dengan A=50.
8. Checklist tidak mengaktifkan kamera tanpa consent; burst disimpan
   terenkripsi dan semua video track berhenti saat vault dikunci.
9. Backup terenkripsi tidak memuat nama pasien plaintext; sandi salah gagal,
   sedangkan pemulihan dengan sandi benar membuka data pada browser baru.
10. Tidak ada uncaught JavaScript error, permintaan unggah data klinis,
    permintaan API otomatis atau request HTTP pihak ketiga dari modul.

Identitas dan pembacaan pada langkah 3 adalah fixture perangkat lunak,
bukan hasil pemeriksaan seseorang. Status “Disetujui” dalam QA membuktikan
aturan aplikasi saja, bukan persetujuan klinis atau kalibrasi alat.

Pemeriksaan tambahan bootstrap menemukan kegagalan font eksternal dapat
menggagalkan CSS chunk storefront. Font opsional kini dimuat setelah shell
toko aktif, terpisah dari CSS lokal. Build ulang dan smoke dengan kedua font
sengaja diblokir lulus: navigasi tampil, permintaan produk tetap limit=15,
error API 503 ditangani, tautan OptiFit memuat dokumen baru, dan tidak ada
uncaught error maupun API/aset eksternal pada dokumen privat.

## PDF dan format laporan

Laporan aktual dihasilkan melalui UI, termasuk saat offline, dengan jsPDF
4.2.1 dan font DejaVu yang dibundel. Pemeriksaan meliputi tiga halaman A4,
render visual, identitas/status/revisi, resep asli, PD kanan/kiri, lingkup
persetujuan, reviewer, disclaimer, tidak ada JavaScript dalam PDF, serta
tidak ada kata keluar dari batas halaman.

Repeatability pada PDF/CSV/cetak diringkas dengan jumlah sampel, inlier,
median, SD sampel dan outlier; struktur rinci tetap tersedia pada JSON.
SD bukan estimasi akurasi terhadap referensi, dan banyaknya angka desimal
bukan klaim ketelitian klinis. PDF/CSV/JSON hasil ekspor tidak otomatis
dienkripsi; pengguna harus memilih tujuan penyimpanannya secara sadar.
Backup seluruh vault memakai format terenkripsi yang berbeda.

## Menjalankan ulang

Di frontend:

    npm ci
    CI=true npm test -- --watchAll=false --runInBand --no-cache
    CI=true npm run build

Untuk E2E, siapkan Playwright pada lingkungan QA dan browser Chromium.
Jalankan frontend/e2e/optifit-browser.cjs dari direktori mana saja; secara
default script mengambil frontend/build dan memulai server fixture lokal.
OPTIFIT_BROWSER_EXECUTABLE dapat menunjuk executable Chromium yang sudah
diinstal. OPTIFIT_QA_DIR mengatur folder keluaran internal.

Script menggunakan pasien/secret sintetis di konteks browser sementara dan
tidak menyentuh vault pengguna. Server dan browser dijalankan pada proses
pengujian yang sama; API fixture sengaja tidak tersedia untuk membuktikan
fungsi inti lokal. Output memuat data sintetis untuk inspeksi, sehingga
jangan memakai script ini pada origin/data pasien produksi.

## Regresi e-commerce dan hal yang belum dijalankan

Rilis sebelumnya mencatat 251 backend tests passed, satu pengujian native
MySQL dilewati, serta 22 skenario browser pelanggan/admin dengan provider
mock. Angka tersebut adalah bukti historis **6 November 2026**, bukan
pengujian ulang backend/provider pada pembaruan OptiFit ini. Berkas backend
tidak berubah; 11 tes frontend e-commerce ikut suite 92 tes terbaru.

Belum dijalankan pada sesi ini:

- Pemindahan database produksi dari export MongoDB pengguna ke server
  MySQL 5.7.24-log nyata.
- Transaksi merchant DOKU dan shipment Everpro menggunakan akun nyata.
- Pemasangan pada domain produksi dan pengujian konfigurasi reverse proxy.
- Uji kamera ponsel fisik, iOS/Android/Safari, variasi sensor dan cahaya.
- Studi manusia terhadap pupillometer/instrumen lain, bias/agreement,
  variasi operator, toleransi dan ketidakpastian klinis.
- Sinkronisasi OptiFit ke MySQL, multi-cabang, server tenancy dan anchoring
  audit; SQL yang disertakan tetap rancangan opsional.

Kemampuan otomatis penuh, estimasi wrap 3D, biometric unlock dan OCR
tervalidasi belum menjadi fitur runtime. Tersedia metode manual,
semi-otomatis dan protokol validasi lapangan untuk melanjutkan secara
terukur tanpa menciptakan angka pengukuran atau akurasi.
