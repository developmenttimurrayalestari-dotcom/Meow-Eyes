# Runbook migrasi dan aktivasi Meowsurement customer

Target database: **Oracle MySQL 5.7.24-log**. Head sebelumnya `20261109_0003`; head baru **`20261110_0004`**. [Rancangan menu dan frame manual](CUSTOMER_FLOW.md). Perintah berikut disediakan untuk operator deployment; tidak berarti database produksi telah dimigrasikan dalam sesi pengerjaan source.

## 1. Persiapan release

Gunakan Python 3.12, dependensi `backend/requirements.txt`, dan Node yang sesuai `frontend/package.json`. Backup database serta volume upload privat, lalu uji pemulihan pada target latihan. Cocokkan versi MySQL, engine InnoDB, strict mode, charset dan pengaturan indeks dengan [panduan database](../mysql-migration/STEP_1.md).

Gunakan akun migrasi dengan hak DDL/trigger untuk upgrade dan audit; runtime memakai akun aplikasi berhak terbatas. Jadwalkan maintenance atau hentikan penulis selama DDL. Template `.env.mysql.example` adalah konfigurasi contoh, bukan instruksi mengubah versi server existing.

## 2. Konfigurasi

Salin `backend/.env.mysql.example` ke `backend/.env.mysql` bila file konfigurasi belum ada. Isi host, port, database dan kredensial pada lingkungan deployment. Jangan menimpa konfigurasi toko yang sudah terisi dengan template kosong.

Set `MEOWSUREMENT_PRIVATE_ROOT` ke direktori persisten yang hanya dapat diakses service backend dan berada di luar semua mount static/public. Default relatif untuk development adalah `./private_uploads/meowsurement`; produksi sebaiknya memakai path absolut. Sesuaikan CORS dan `APP_ENV`; aktifkan `ENABLE_SCHEDULER=1` hanya pada satu worker terjadwal.

Tidak diperlukan credential database dari browser, organisasi baru, akun operator lokal, PIN Meowsurement, atau seed pasien.

## 3. Upgrade dengan Alembic

Dari direktori backend dan virtual environment yang benar:

```bash
cd backend
python -m alembic current
python -m mysql.check_integrity --preflight-only
python -m alembic upgrade head
python -m mysql.check_integrity
python -m alembic current
```

Database toko pada 0002 menerima tambahan 11 tabel; database baru menjalankan seluruh rantai 0001 → 0002 → 0003 → 0004. Sesudah berhasil, head harus `20261110_0004`, terdapat 79 tabel aplikasi, dan audit mengembalikan `ok: true`. Startup readiness memakai head baru. Target yang sudah berada di 0003 menerima perubahan nullable product_id dan dua trigger sesi; tidak ada penambahan tabel atau penghapusan data.

Skema baru memakai InnoDB, utf8mb4, DECIMAL, DATETIME(6), JSON, FK dan indeks komposit. Aturan yang perlu enforcement pada MySQL 5.7 dipasang sebagai trigger; tidak mengandalkan CHECK yang diabaikan engine 5.7. DDL awal 0001/0002 dibekukan dan tidak ditulis ulang.

### Alternatif SQL manual

Untuk target yang sudah tepat berada pada 0003, jalankan `backend/sql/004_optional_customer_frame.sql`. Untuk target pada 0002 yang belum mempunyai tabel baru, jalankan SQL 003 lalu 004 secara berurutan. SQL 003 adalah `backend/sql/003_customer_meowsurement.sql` atau salinannya `docs/optifit/SCHEMA_MYSQL57.sql`. Pilih satu jalur, jangan menjalankan SQL lagi setelah Alembic berhasil.

```bash
mysql --show-warnings -h DB_HOST -u MIGRATION_USER -p DB_NAME < sql/003_customer_meowsurement.sql
mysql --show-warnings -h DB_HOST -u MIGRATION_USER -p DB_NAME < sql/004_optional_customer_frame.sql
python -m mysql.check_integrity
```

Client harus mendukung DELIMITER. Hindari `--force` dan jangan melakukan `alembic stamp` untuk menutupi kegagalan. MySQL melakukan implicit commit DDL; kegagalan sebagian membutuhkan inventaris langkah terpasang atau pemulihan backup target latihan. Migrasi menolak replay parsial yang berpotensi menimpa struktur/data. Migrasi 0004 menolak downgrade otomatis karena sesi manual mungkin sudah tersimpan. Rollback menggunakan backup yang sudah diuji; jangan menghapus sesi manual agar downgrade bisa lolos.

## 4. Impor MongoDB yang belum selesai

Jika toko masih memakai MongoDB, jalankan proses ekspor/import yang sudah ada di [DATA_IMPORT](../mysql-migration/DATA_IMPORT.md), dengan rekonsiliasi ID, jumlah data, uang, stok, order dan media pada target latihan. Upgrade schema dahulu sebelum startup aplikasi terbaru. Migrasi 0003 tidak membaca MongoDB atau IndexedDB dengan sendirinya.

Profil lama yang belum lengkap tetap memiliki readiness false. Tidak dipilihkan resep checkout lama secara otomatis. Ukuran frame tidak ditebak dari string size atau gambar. Customer/admin melengkapi data melalui UI yang sesuai setelah akun/katalog tersedia.

## 5. Jalankan backend dan frontend

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8001
```

Dari direktori frontend pada terminal/build worker yang sesuai:

```bash
npm ci
npm run build
```

Deploy seluruh isi `frontend/build` secara konsisten. Reverse proxy `/api` diarahkan ke FastAPI, fallback SPA harus menangani `/profile`, `/admin/meowsurement`, dan `/meowsurement/`. Berkas `/meowsurement/sw.js`, manifest dan font lokal harus mempunyai tipe MIME yang benar; path privat tidak boleh dipetakan ke direktori foto backend.

Asset service worker tidak menggantikan jaringan akun. Saat upgrade dari build lama, biarkan lifecycle service worker normal selesai dengan menutup/membuka tab; jangan hapus storage customer atau IndexedDB lama sebagai langkah rutin.

## 6. Aktivasi data dari UI

1. Admin web membuka katalog produk frame dan aksi Meowsurement.
2. Isi A/B/DBL/ED yang benar dalam mm, panjang tangkai bila tersedia, konfirmasi simetris bila sesuai, dan catatan sumber. Aktifkan bila lengkap.
3. Tinjau setiap varian: mengikuti default atau override lengkap. Simpan dan periksa kembali ukuran efektif pada halaman produk.
4. Bila review didelegasikan, berikan `meowsurement.review` pada akun staf web yang sudah ada.
5. Customer login, mengisi profil/resep, lalu membuka tombol Meowsurement pada frame/varian.
6. Verifikasi snapshot pada sesi dan buat revisi pengukuran; reviewer independen meninjau sebelum approval.

Tidak perlu seed organisasi, admin lokal, operator, pasien, maupun angka resep/frame contoh pada produksi.

## 7. Foto dan scheduler

Upload foto default mati. Uji pilihan consent capture, upload privat, dan thumbnail secara terpisah. Periksa folder tujuan tidak dilayani sebagai aset publik. API foto harus menolak akun lain, expiry, serta tombstone.

Job `expire-meowsurement-photos` berjalan tiap 60 menit pada scheduler aktif. Operator admin dapat memicunya melalui:

```text
POST /api/admin/scheduler/run/expire-meowsurement-photos
```

Gunakan session admin website yang sah. Endpoint bukan URL publik/cron tanpa autentikasi. Bila memakai scheduler eksternal, panggil job di lingkungan backend yang terkonfigurasi. Pantau kegagalan storage dan pastikan backup mempunyai kebijakan retensi sendiri. Endpoint menolak foto kedaluwarsa meskipun job purge belum selesai.

## 8. Pemeriksaan penerimaan

- Customer tanpa login masuk melalui login website dengan tujuan frame/varian dipertahankan.
- Customer tanpa profil/resep lengkap diarahkan ke profil; draft dapat disimpan, `0` tidak hilang dan AXIS wajib jika CYL tidak nol.
- Spesifikasi varian yang dipakai sesuai varian aktif; frame belum lengkap tidak dapat memulai sesi.
- Sesi baru memuat resep dan ukuran otomatis. Ubah profil/katalog, lalu periksa sesi lama tetap sama dan sesi baru memakai nilai terbaru.
- Refresh memperoleh riwayat server. Tanpa consent upload, foto RAM hilang setelah reload tetapi data hasil/landmark yang tersimpan tetap ada.
- Customer lain tidak dapat membaca/mutasi sesi/foto; reviewer menggunakan akun web, tanpa profil pasien pribadi.
- Revisi stale ditolak; bukti/snapshot yang diubah atau approval sendiri ditolak.
- Export membutuhkan konfirmasi dan menampilkan status revisi yang benar.

Pengujian otomatis aktual dan perintah ulang ada di [VALIDATION](VALIDATION.md). Native MySQL 5.7.24-log, perangkat kamera fisik dan deployment harus diuji pada lingkungan target sebelum cutover.
