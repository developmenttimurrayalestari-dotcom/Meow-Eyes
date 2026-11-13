> Arsip implementasi vault lokal sebelumnya. Dokumen ini tidak menjadi petunjuk alur customer saat ini. Gunakan [dokumentasi aktif](../README.md).

# Meowsurement

Modul website/PWA privat berbahasa Indonesia pada **/meowsurement/**. Modul
ditambahkan ke proyek Meow Eyes React + FastAPI yang memakai **Oracle MySQL
5.7.24-log**. Pasien, resep, foto dan hasil fitting pada MVP disimpan terenkripsi
di perangkat; data klinis tidak dikirim ke database server secara otomatis.

Rancangan dibuat sebelum implementasi. Sumber dibagi menjadi UI, domain,
vision, storage, report, adapter integrasi, dan application shell offline.
Tidak ada pasien contoh, kredensial bawaan, model landmark palsu, atau angka
akurasi yang ditanam dalam aplikasi produksi.

## Dokumen dan urutan membaca

1. [DESIGN.md](DESIGN.md): 21 bagian desain yang diminta, kemudian urutan
   implementasi; termasuk PRD, user flow, ERD, skema, kontrak CV, rumus,
   confidence, privasi, backlog, acceptance dan test plan.
2. [RUNBOOK.md](RUNBOOK.md): pemasangan, menjalankan aplikasi, akun lokal,
   konfigurasi hosting, offline, backup dan operasi harian.
3. [UI_WIREFRAMES.md](UI_WIREFRAMES.md): layar dan interaksi.
4. [MEASUREMENTS.md](MEASUREMENTS.md): definisi nilai, koordinat, kalibrasi,
   perhitungan, repeatability dan batas inferensi.
5. [SECURITY.md](SECURITY.md): model ancaman, enkripsi, role, audit, retensi,
   ekspor dan pemulihan.
6. [SCHEMA.md](SCHEMA.md) dan [SCHEMA_MYSQL57.sql](SCHEMA_MYSQL57.sql):
   struktur lokal dan rancangan SQL opsional untuk fase sinkronisasi server.
7. [VALIDATION.md](VALIDATION.md): hasil pengujian perangkat lunak dan hal
   yang belum diverifikasi.
8. [FIELD_VALIDATION_PROTOCOL.md](FIELD_VALIDATION_PROTOCOL.md): protokol
   pembandingan instrumen/perangkat/manusia sebelum penggunaan klinis final.

## Kemampuan yang diimplementasikan

| Area | Implementasi |
| --- | --- |
| Pasien | ID/nomor rekam otomatis, nama dan tanggal pemeriksaan, detail opsional, pencarian, riwayat, foto profil hanya dengan persetujuan |
| Resep | Input OD/OS SPH, CYL, AXIS, ADD; nol dibedakan dari kosong; transpose sebagai hasil turunan tanpa mengubah resep asli |
| Frame | A/B/DBL/ED, identitas frame, Frame PD; decentration hanya dengan referensi bridge dan konfirmasi frame simetris |
| PD | Distance/near terpisah; OD dan OS independen; near memiliki jarak kerja; tidak membagi binocular PD menjadi dua |
| Kalibrasi | Marker empat sudut/homography atau panjang segmen frame yang diketahui; bukti bidang/ukuran wajib; tanpa skala valid tidak ada keluaran mm |
| Kamera | Izin eksplisit, frontal, frontal dekat, 3/4 dan lateral; burst lima frame dengan tiga sampel terpilih; stream dihentikan ketika dikunci/ditutup |
| Editor | Penandaan manual, kandidat pupil lokal untuk konfirmasi, zoom/pan, magnifier, undo/redo, sebelum/sesudah, pemeriksaan readonly oleh reviewer |
| VD dan panto | Geometri lateral dengan titik/bidang yang sesuai; panto menyimpan raw, head pitch, sumber dan corrected; hasil alat manual juga tersedia |
| Wrap | Pencatatan kanan/kiri dari instrumen/metode referensi beserta konvensi sudut; gambar multi-sudut dapat disimpan untuk review |
| Kualitas | Skrining luminance/blur/detail, checklist dan kualitas teknik, median/MAD/outlier/SD, penolakan foto duplikat; tidak mengklaim uncertainty tervalidasi |
| Revisi | Data awal tetap tersimpan; koreksi membuat revisi; perubahan frame/referensi/jarak kerja membatalkan hasil terkait |
| Review | Admin/operator/reviewer; persetujuan membutuhkan reviewer berbeda, revisi yang tepat, metode pembanding, protokol dan catatan |
| Laporan | PDF, CSV, JSON dan cetak; konfirmasi ekspor; foto default nonaktif; laporan final hanya memuat parameter dalam lingkup persetujuan |
| Privasi | AES-256-GCM, credential-wrapped key, IndexedDB, auto-lock, pembatasan role aplikasi, retensi, audit hash-chain, penghapusan terkontrol |
| Backup | Cadangan terenkripsi dengan frasa sandi tersendiri, verifikasi sebelum restore, penolakan sandi atau ciphertext salah |
| Admin | Identitas/logo optik, akun lokal, metode kalibrasi, retensi, auto-lock, audit dan permintaan persistent storage |
| Offline | Service worker hanya menyimpan shell/aset statis; refresh, buka vault dan ekspor PDF bekerja tanpa jaringan setelah persiapan awal |
| Meow Eyes | Pengambilan profil/katalog hanya melalui tindakan yang dikonfirmasi; ukuran frame tetap diperiksa operator |

## Batas kemampuan yang terlihat di aplikasi

Pengukuran kamera membantu fitting; SPH/CYL/AXIS/ADD berasal dari resep. Mode
otomatis penuh belum diaktifkan karena tidak ada detektor anatomi/head-pose
dan protokol yang telah divalidasi. Depth/intrinsics yang tidak diberikan
browser ditandai tidak tersedia. Wrap 3D otomatis, unlock biometrik, OCR resep,
sinkronisasi server dan multi-cabang belum menjadi fungsi runtime.

Skor 0–100 adalah kualitas bukti teknik, bukan probabilitas benar. Skor kamera
dibatasi di bawah kategori tinggi pada versi ini. Ketidakpastian tetap null
dan ditampilkan sebagai “Tidak tersedia”. Minimal tiga foto yang berbeda,
anotasi independen, dan perbandingan referensi diperlukan untuk persetujuan
hasil kamera; jumlah frame saja tidak membuktikan ketelitian klinis.

Role lokal melindungi alur aplikasi dan akses normal, tetapi semua anggota
workspace tepercaya menggunakan material kunci workspace yang sama. Ini bukan
isolasi kriptografis antar pelanggan yang saling tidak percaya. Gunakan vault
atau profil browser terpisah untuk konteks tersebut; lihat SECURITY.md.

## Menjalankan singkat

Di direktori frontend:

    npm ci
    npm start

Buka /meowsurement/ pada alamat development yang ditampilkan. Untuk offline,
buat build produksi dengan npm run build dan layani melalui HTTPS atau
localhost dengan konfigurasi SPA/MIME yang benar. npm start tidak menyediakan
service worker offline. Panduan lengkap dan contoh hosting ada di RUNBOOK.md.

Tidak ada akun default. Buat admin lokal pertama, tambahkan operator/reviewer,
dan simpan cadangan terenkripsi. Lupa seluruh secret tanpa backup yang dapat
dibuka tidak mempunyai jalur pemulihan tersembunyi.

## Hubungan dengan migrasi database e-commerce

Model/query backend e-commerce tetap SQLAlchemy/MySQL 5.7.24-log, 68 tabel,
Alembic head 20261106_0002. Penambahan OptiFit MVP tidak mengubah 85 berkas
backend dari paket sebelumnya. Rancangan 16 tabel SQL OptiFit bukan migrasi
yang telah diterapkan: API sinkronisasi, tenancy server, distribusi kunci dan
rekonsiliasi belum diimplementasikan.

## Verifikasi rilis

92 tes frontend dalam 9 suite lulus. Sepuluh skenario browser produksi lulus,
termasuk IndexedDB asli, review independen, offline reload/PDF, kamera,
mobile/light/dark, enkripsi, backup dan restore. PDF hasil aplikasi telah
dirender dan diperiksa. Ini adalah bukti perilaku perangkat lunak dengan data
sintetis; bukan hasil uji manusia atau klaim akurasi alat.
