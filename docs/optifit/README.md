# Meowsurement terintegrasi dengan akun Meow Eyes

Pembaruan 9 November 2026 mengubah entry `/meowsurement/` menjadi fitur akun customer di website Meow Eyes. Profil dan resep dibaca dari akun yang sudah login; ukuran frame dapat diisi manual atau dibaca dari katalog yang dikelola admin. Pembaruan 10 November memisahkan jenis pengukuran menjadi kartu; lihat [rancangan UI customer](CUSTOMER_FLOW.md). Customer tidak membuat organisasi, administrator lokal, operator, atau pasien terpisah.

## Alur yang tersedia

1. Customer membuka Meowsurement atau tombol Meowsurement pada detail frame/varian.
2. Jika belum login, login website menerima `returnTo` lokal yang tervalidasi. Jalur ini tidak meminta pembuatan PIN checkout.
3. Server memeriksa nama, telepon, tanggal lahir, tanggal resep, SPH/CYL kedua mata, dan AXIS bila CYL tidak nol. Profil yang belum lengkap diarahkan ke `/profile`; draft tetap dapat disimpan.
4. Customer melengkapi resep, lalu kembali ke tujuan frame/varian sebelumnya. Nilai `0` dipertahankan dan berbeda dari kolom kosong.
5. Pilih kartu jenis pengukuran. Isi A/B/DBL manual, atau pilih frame/varian katalog aktif dengan spesifikasi A/B/DBL lengkap dan diaktifkan admin. ED opsional pada kedua sumber. Varian dapat mengikuti spesifikasi produk atau memakai override.
6. Server membuat sesi dengan snapshot profil/resep dan frame. Form customer tidak menawarkan perubahan resep atau dimensi katalog di dalam sesi.
7. Persiapan, persetujuan, foto/landmark, pembacaan manual, hasil, revisi, dan pengajuan review menggunakan sesi tersebut. Riwayat diambil dari API akun customer.
8. Admin/staf web berizin `meowsurement.review` membuka antrean di `/admin/meowsurement`. Petugas tidak perlu melengkapi resep pribadinya untuk meninjau customer.

## Sumber data dan database

Migrasi **`20261109_0003`** menambahkan **11 tabel**, sehingga ada **79 tabel aplikasi**, di luar `alembic_version`. Head terkini **`20261110_0004`** mengizinkan sesi tanpa ID produk/varian dengan sumber ukuran manual; tidak menambah tabel. Target tetap Oracle **MySQL 5.7.24-log**. Model, FK komposit, guard MySQL, ekspor SQL, dan pemeriksaan integritas sudah disertakan.

- [Rancangan relasional dan ERD](SCHEMA.md)
- [SQL migrasi 0002 ke 0003](SCHEMA_MYSQL57.sql)
- [SQL migrasi 0003 ke 0004](../../backend/sql/004_optional_customer_frame.sql)
- [Arsitektur, kontrak API, dan keputusan produk](DESIGN.md)
- [Urutan instalasi, migrasi, dan deployment](RUNBOOK.md)
- [Kepemilikan, persetujuan foto, dan keamanan](SECURITY.md)
- [Layar dan flow pengguna](UI_WIREFRAMES.md)
- [Hasil pengujian aktual](VALIDATION.md)

## Foto, jaringan, dan riwayat

Hasil, landmark, dan revisi disimpan ke backend akun Meow Eyes. Foto secara default hanya berada di memori selama dokumen terbuka. Ada pilihan terpisah untuk mengunggah foto secara privat agar dapat dibuka kembali untuk koreksi/review. Pilihan thumbnail laporan juga terpisah dan nonaktif secara default.

Static service worker hanya menyimpan aset aplikasi. Login, profil, katalog, riwayat, dan penyimpanan revisi membutuhkan jaringan. Alur customer ini tidak menjanjikan akses riwayat atau penyimpanan offline. Kamera dan geometri tetap diproses pada perangkat; gambar tidak diunggah tanpa pilihan eksplisit tersebut.

Mode lokal/vault sebelumnya tidak lagi dipasang pada entry produksi. Kode dan pengujian kompatibilitas lama dipertahankan, serta dokumentasinya ditandai di `legacy-local-vault/`. Data IndexedDB lama tidak dihapus, dipetakan ke customer, atau diunggah secara otomatis. Migrasi SQL baru hanya menangani struktur server; pemetaan data lokal lama memerlukan proses terpisah bila memang ada data nyata.

## Kemampuan fitting yang dipertahankan

Modul tetap mendukung input/konfirmasi landmark, kalibrasi bidang, pengukuran PD, geometri lateral yang didukung, pembacaan alat referensi, review independen, dan laporan PDF/CSV/JSON/print. Detail teknis ada di [MEASUREMENTS](MEASUREMENTS.md). Resep merupakan input pemeriksaan profesional; kamera tidak menentukan SPH, CYL, AXIS, atau ADD.

Deteksi/head-pose/wrap 3D otomatis penuh belum tersedia. Pengujian perangkat lunak bukan pembuktian akurasi klinis; [protokol validasi lapangan](FIELD_VALIDATION_PROTOCOL.md) tetap terpisah.
