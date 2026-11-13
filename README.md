# Meow Eyes — optical marketplace

Aplikasi optik dengan React, FastAPI, SQLAlchemy, dan **Oracle MySQL 5.7.24-log**.
Paket ini melanjutkan pengerjaan sampai **Step 9** sesuai persetujuan pengguna:
migrasi MongoDB ke MySQL, checkout resep dan rating, Flash Sale kategori,
storefront, CMS, Virtual Try-On, DOKU Checkout dan Everpro.

Pembaruan 9 November 2026 mengintegrasikan **Meowsurement** di **/meowsurement/**
dengan akun customer website, resep dari profil, dan spesifikasi frame katalog
admin. Riwayat/revisi tersimpan di backend; customer tidak membuat organisasi,
admin lokal, operator, atau pasien terpisah.
[Mulai dari dokumentasi OptiFit](docs/optifit/README.md), lalu baca
[rancangan integrasi customer](docs/optifit/DESIGN.md) dan
[hasil validasi perangkat lunak](docs/optifit/VALIDATION.md).

## Mulai dari sini

- [Poin, Manage Games, Cashback, RMA, dan halaman Virtual Try-On](docs/LOYALTY_GAMES_RMA.md)
- [Fitur lengkap dan panduan rilis](docs/FEATURES_AND_RELEASE.md)
- [Konfigurasi DOKU, Everpro dan rekonsiliasi](docs/INTEGRATIONS.md)
- [Hasil pengujian dan batas verifikasi](docs/mysql-migration/VALIDATION.md)
- [Rencana implementasi Step 1–9](docs/mysql-migration/IMPLEMENTATION_PLAN.md)

Backend aplikasi adalah **`server:app`** dalam direktori `backend`.
`mysql_bootstrap:app` hanya untuk diagnostik skema. Endpoint asli dipertahankan
kecuali pertukaran sesi Google Emergent yang diganti autentikasi Google langsung,
dan ditambah endpoint fitur/integrasi. Tidak ada query runtime
Motor/PyMongo. Head Alembic saat ini **`20261112_0012`**. [Daftar/login Google langsung](docs/FEATURES_AND_RELEASE.md#daftar-dan-login-google-langsung), [Lens Index dan resep checkout](docs/FEATURES_AND_RELEASE.md#lens-index-jenis-lensa-dan-resep-checkout), [manajemen produk dan aksi massal](docs/FEATURES_AND_RELEASE.md#hapus-dan-nonaktifkan-produk), [master kategori independen](docs/mysql-migration/STEP_2.md#master-kategori-independen-0006), [alur menu pengukuran dan frame manual](docs/optifit/CUSTOMER_FLOW.md), serta [poin, game, cashback, RMA dan Virtual Try-On](docs/LOYALTY_GAMES_RMA.md).

## Database dan data sebelumnya

- [Arsitektur dan konfigurasi MySQL](docs/mysql-migration/STEP_1.md)
- [Migrasi backend Step 2](docs/mysql-migration/STEP_2.md)
- [Impor data, resume dan rekonsiliasi](docs/mysql-migration/DATA_IMPORT.md)
- [Referensi 68 tabel dasar e-commerce](docs/mysql-migration/SCHEMA_REFERENCE.md)
- [11 tabel tambahan Meowsurement; total 79 tabel](docs/optifit/SCHEMA.md)
- [SQL skema dasar 0002](backend/sql/001_initial_schema.sql)
- [SQL upgrade Meowsurement 0003](backend/sql/003_customer_meowsurement.sql)
- [Audit kode awal](docs/mysql-migration/SOURCE_AUDIT.md)

## Konfigurasi minimum

Salin `backend/.env.mysql.example` ke `backend/.env.mysql`, isi koneksi database,
jalankan Alembic serta audit integritas, kemudian seed fitur dan FastAPI sesuai
panduan rilis. Frontend memakai `npm ci` dengan `package-lock.json`; contoh
konfigurasi frontend tersedia pada `frontend/.env.example`.

Kredensial DOKU/Everpro berada di environment server. Halaman admin integrasi
menampilkan kesiapan konfigurasi tanpa mengekspos secret. Simulasi pembayaran
hanya dapat digunakan pada development/test dengan flag eksplisit; status paid
pada produksi harus berasal dari konfirmasi penyedia yang terverifikasi.

Source code dan pengujian lokal tidak berarti data produksi sudah dipindahkan
atau transaksi eksternal sudah dijalankan. Export MongoDB, target MySQL, akun
penyedia, dan infrastruktur deployment belum disediakan pada sesi pengerjaan.
