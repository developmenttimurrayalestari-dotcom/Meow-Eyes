# Meow Eyes — optical marketplace

Aplikasi optik dengan React, FastAPI, SQLAlchemy, dan **Oracle MySQL 5.7.24-log**.
Paket ini melanjutkan pengerjaan sampai **Step 9** sesuai persetujuan pengguna:
migrasi MongoDB ke MySQL, checkout resep dan rating, Flash Sale kategori,
storefront, CMS, Virtual Try-On, DOKU Checkout dan Everpro.

## Mulai dari sini

- [Fitur lengkap dan panduan rilis](docs/FEATURES_AND_RELEASE.md)
- [Konfigurasi DOKU, Everpro dan rekonsiliasi](docs/INTEGRATIONS.md)
- [Hasil pengujian dan batas verifikasi](docs/mysql-migration/VALIDATION.md)
- [Rencana implementasi Step 1–9](docs/mysql-migration/IMPLEMENTATION_PLAN.md)

Backend aplikasi adalah **`server:app`** dalam direktori `backend`.
`mysql_bootstrap:app` hanya untuk diagnostik skema. Semua 159 endpoint router
asli dipertahankan dan ditambah endpoint fitur/integrasi. Tidak ada query runtime
Motor/PyMongo. Head Alembic tetap **`20261106_0002`**.

## Database dan data sebelumnya

- [Arsitektur dan konfigurasi MySQL](docs/mysql-migration/STEP_1.md)
- [Migrasi backend Step 2](docs/mysql-migration/STEP_2.md)
- [Impor data, resume dan rekonsiliasi](docs/mysql-migration/DATA_IMPORT.md)
- [Referensi 68 tabel relasional](docs/mysql-migration/SCHEMA_REFERENCE.md)
- [SQL skema](backend/sql/001_initial_schema.sql)
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
