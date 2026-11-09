# Step 2 — aplikasi MySQL dan konversi data

> Catatan historis Step 2. Fitur lanjutan dan integrasi telah dilanjutkan pada
> [panduan rilis Step 3–9](../FEATURES_AND_RELEASE.md); keterangan simulator dan
> fitur yang belum dibuat di bawah menggambarkan batas paket Step 2 saat itu.

Target tetap **Oracle MySQL 5.7.24-log**, dengan skema Alembic
`20261106_0002`. Step 2 mengganti backend aplikasi ke SQLAlchemy/MySQL;
kedua file revisi skema sebelumnya tetap utuh. Compiler/SQL instalasi baru juga
diperbaiki untuk menghilangkan default TEXT yang tidak didukung MySQL 5.7;
catatan poin kosong disediakan oleh default aplikasi.

## Hasil implementasi

`server:app` sekarang adalah backend aplikasi MySQL. Semua akses database
runtime menggunakan query SQLAlchemy terhadap tabel relasional. Driver Motor
atau PyMongo, operator dokumen MongoDB, dan fallback ke MongoDB tidak digunakan.
`mysql_bootstrap:app` masih tersedia sebagai diagnostik skema saja.

| Area | Implementasi SQL |
| --- | --- |
| Akun dan akses | Registrasi/login, sesi dengan hash SHA-256, permission staff, PIN dan penguncian percobaan gagal. Hash password/PIN lama tetap dapat digunakan. |
| Katalog | Produk, varian, kategori, merek, filter, urutan dan pagination; daftar relasi dimuat dari tabel anak. |
| Keranjang dan pesanan | Alamat, item frame/lensa, harga Decimal, snapshot pesanan, reservasi stok dan riwayat perubahan. |
| Pembayaran dan pembatalan | Transisi idempoten, pelepasan reservasi, kuota promo, pengembalian poin dan penyimpanan percobaan pembayaran. Provider masih simulator dengan batas lingkungan. |
| CMS/admin | Artikel, knowledge, FAQ, halaman, banner, kontak, staff, moderasi, dashboard, impor spreadsheet dan ekspor Excel. |
| Engagement | Game, roulette, saldo/ledger poin, wishlist, newsletter dan langganan produk. |
| Maintenance | Kedaluwarsa pesanan, jendela Flash Sale, pemeriksaan pengiriman simulasi dan penyelesaian pesanan memakai layanan SQL. |
| Konversi sumber | Importer lokal untuk seluruh 37 koleksi yang ditemukan pada kode asli, dengan dry run, pemeriksaan relasi, checkpoint dan rekonsiliasi. |

Bentuk URL dan metode **159 endpoint router asli** dipertahankan. Alias respons
React seperti `variants`, `gallery`, `items`, `address`, `permissions`,
`is_published`, `payment_url` dan `tracking_number` disusun dari tabel terkait.
Frontend tidak perlu berpindah ke entry point diagnostik.

### Koreksi kompatibilitas dari paket sebelumnya

Audit Step 2 menemukan `point_logs.note TEXT DEFAULT ('')` pada hasil SQL
sebelumnya. MySQL 5.7 tidak mengizinkan default TEXT. Hasil SQL terbaru menghapus
DEFAULT tersebut; model aplikasi mengisi catatan kosong bila diperlukan.
Snapshot revisi 0001 tetap utuh, dan compiler adaptasi membuat replay-nya sesuai
5.7. Sumber: [MySQL 5.7 data type defaults](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/data-type-defaults.html).

Jika percobaan instalasi SQL lama gagal sebagian, jangan mengubah Alembic head
secara manual untuk melewati kegagalan. Periksa hasilnya dan gunakan database
uji baru yang kosong untuk penerimaan; DDL MySQL dapat meninggalkan tabel yang
sudah dibuat sebelum sebuah perintah gagal. Jangan hapus database berisi data
bisnis untuk mengikuti prosedur uji ini.

## 1. Konfigurasi dan menjalankan backend

Gunakan environment Python baru agar dependensi MongoDB lama tidak ikut terbawa.
Dari root proyek:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp backend/.env.mysql.example backend/.env.mysql
```

Di Windows PowerShell, aktivasi menggunakan `.venv\Scripts\Activate.ps1`.
Sesuaikan `backend/.env.mysql` sebelum menghubungkan aplikasi:

- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`.
- Server Anda umumnya memakai port `3306`; Compose lokal yang disediakan memakai
  `127.0.0.1:3307`. Image Compose adalah `mysql:5.7.24`.
- `APP_ENV=production` memerlukan TLS dengan `MYSQL_SSL_MODE=verify_identity`
  dan origin frontend eksplisit dalam `CORS_ORIGINS`.
- `SCHEDULER_ENABLED=1` hanya pada worker yang ditugaskan menjalankan maintenance.
  Worker API lainnya dapat memakai `0`.
- `ENABLE_MOCK_PAYMENTS=0` adalah default. Aktifkan `1` hanya pada development
  atau test untuk menguji checkout simulasi. Produksi selalu menolaknya.

Siapkan skema menggunakan akun migrasi yang memiliki privilege DDL/trigger.
Akun aplikasi harian dapat dibatasi ke akses data tanpa privilege trigger.

```bash
cd backend
python -m alembic upgrade head
python -m mysql.check_integrity
python -m uvicorn server:app --host 127.0.0.1 --port 8001
```

`/api/health/live` menandakan proses berjalan. `/api/health/ready` dan
`/api/health` memeriksa koneksi, keluarga versi server, persyaratan InnoDB dan
revisi skema. Startup berhenti apabila pemeriksaan database tidak lolos;
aplikasi tidak diam-diam berpindah ke database lain atau membuat tabel sendiri.

MySQL 5.7 tetap menggunakan 90 trigger untuk 97 aturan integritas. Audit trigger
menggunakan akun operator, bukan setiap permintaan aplikasi. Detail privilege,
DYNAMIC, large prefix, page size dan penyimpanan tersedia di [Step 1](STEP_1.md).

## 2. Perilaku transaksi

Satu `session_scope()` adalah satu unit kerja: berhasil seluruhnya atau rollback.
Pembacaan memakai `read_session()` yang tidak melakukan commit otomatis.
Tidak ada satu AsyncSession yang dibagikan ke task paralel. MySQL 5.7 tidak
mendukung INSERT RETURNING; `eager_defaults=True` memuat default server saat
flush yang di-await sehingga serializer tidak memicu I/O implisit. Perilaku
ini mengikuti [panduan async SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession).

Checkout membaca harga dan stok dari server. Nilai uang tetap `Decimal` selama
perhitungan dan penyimpanan; konversi ke angka JSON hanya pada batas API agar
kontrak frontend tetap sesuai. Frame dan lensa memiliki kebutuhan stok masing-
masing; beberapa baris keranjang yang menggunakan SKU sama dijumlahkan.

Mutasi keranjang, checkout, wallet dan reward mengunci baris pengguna. Stok
menggunakan locking reads pada produk/varian dalam urutan stabil. Order, isi
pesanan, snapshot alamat/resep, reservasi, penggunaan voucher/reward dan ledger
poin ditulis dalam transaksi yang sama. Percobaan pembayaran disimpan sebelum
adapter provider dijalankan di luar transaksi stok.

Header `Idempotency-Key` dapat digunakan pada konfirmasi checkout. Klien lama
juga mendapat identitas retry berdasarkan item keranjang yang dipilih.
Pemakaian ulang key untuk payload berbeda ditolak. Konfirmasi pembayaran,
pembatalan dan kedaluwarsa memakai state transition yang sama agar tidak
mengurangi stok atau mengembalikan poin dua kali.

Percobaan PIN gagal dikomit sebelum respons kesalahan dikirim. Karena itu
rollback sebuah permintaan checkout tidak menghapus catatan percobaan PIN.

Jika MySQL mengembalikan deadlock/lock timeout, transaksi dibatalkan dan API
mengembalikan konflik yang dapat dicoba ulang. Klien harus memakai key yang
sama ketika mengulang checkout yang sama; jangan mengubah payload pada retry.

## 3. Penyesuaian perilaku yang perlu diketahui

Penyesuaian ini diperlukan untuk menjaga integritas backend relasional:

- Produk yang sudah dipakai pesanan dinonaktifkan, bukan dihapus beserta
  sejarahnya. Varian yang dihilangkan dari form CMS juga dinonaktifkan;
  ID dan saldo reservasi tidak dibuat ulang saat mengedit produk.
- Kategori tidak dapat membentuk siklus atau dihapus saat masih direferensikan.
- Produk yang dibeli harus mempunyai varian aktif dengan stok. Produk tanpa
  varian tidak lagi diperlakukan seolah mempunyai stok tidak terbatas.
- Ulasan memerlukan baris pembelian yang benar-benar dimiliki pengguna, dibayar
  dan selesai. Endpoint tetap ada; UI rating baru tetap berada pada Step 3.
- Endpoint simulasi pembayaran memerlukan login pemilik pesanan/admin dan
  flag development/test. Endpoint cron manual memerlukan admin.
- Admin tidak bisa mengubah status menjadi paid sebagai pengganti pembayaran.
  Refund dana melalui gateway belum diimplementasikan pada tahap ini.
- URL aset publik kini memeriksa metadata `uploads` dan hanya menyajikan file
  publik yang terdaftar. File private, file tidak terdaftar, traversal dan
  symlink tidak disajikan oleh URL publik. Upload/download resep privat dan
  penyimpanan privat tersendiri tetap perlu diselesaikan pada Step 3.
- Newsletter mempertahankan simulasi proyek: respons `mocked: true`, status
  dan jumlah terkirim bersifat simulasi; tidak ada email yang benar-benar dikirim.
- Flash Sale yang dimatikan operator tidak otomatis diaktifkan kembali oleh
  scheduler. Form kategori dan penyelarasan seluruh halaman promo tetap Step 4.
- SSO memakai penyedia identitas yang sudah ada pada proyek. Kredensial dan
  perilaku layanan pihak ketiga tidak diuji terhadap akun nyata pada tahap ini.

## 4. Migrasi data sebenarnya

Tidak ada export MongoDB atau koneksi database produksi yang diberikan dalam
paket sumber. Karena itu tahap ini menyediakan kode konversi dan pengujiannya,
bukan klaim bahwa data toko sudah dipindahkan.

Gunakan backup konsisten dan file `mongoexport` JSON/JSONL per koleksi. Inventaris
penuh membutuhkan file untuk 37 koleksi, termasuk `[]` untuk koleksi yang memang
kosong. File BSON dari `mongodump` tidak dibaca langsung oleh importer ini.

Jalankan dry run terlebih dahulu; perintah ini tidak menghubungi MySQL:

```bash
python -m mysql.import_mongo /path/to/export --report /path/to/migration-report.json
```

Pemeriksaan read-only terhadap target skema kosong:

```bash
python -m mysql.import_mongo /path/to/export --target-check --report /path/to/target-report.json
```

Setelah semua error diperbaiki, warning ditinjau, backup tersedia, dan penulis
lama/baru termasuk scheduler dihentikan, gunakan prosedur apply/resume dalam
[DATA_IMPORT.md](DATA_IMPORT.md). Importer menolak merge diam-diam ke database
berisi data bisnis, perubahan input saat resume, perubahan baris yang sudah
terimpor, atau baris tambahan tanpa provenance yang cocok.

ID aplikasi, hash password/PIN, waktu, nominal historis dan source checksum
dipertahankan. Token sesi di-hash dengan algoritma yang sama dengan lookup
runtime. Import tidak mengarang pilihan lensa/resep yang sudah tidak tersimpan
pada pesanan lama, tidak membuat ulasan/pembelian palsu untuk menyamakan cached
rating, dan tidak mengganti SKU produksi yang duplikat secara otomatis.

Jalankan rekonsiliasi sebelum mengarahkan trafik ke MySQL. Jika aplikasi sudah
menerima penulisan baru setelah cutover, rollback ke MongoDB memerlukan
rekonsiliasi transaksi baru; jangan sekadar mengganti environment variable.

## 5. Data demo

`seed.py` dan `seed_content.py` kini menggunakan SQL dan opt-in eksplisit.
Mereka hanya ditujukan untuk database demo development/test. Tidak ada password
admin default yang diam-diam ditambahkan ke database produksi. Konfigurasi
kredensial demo, cakupan data dan perilaku rerun dijelaskan di
[DATA_IMPORT.md](DATA_IMPORT.md).

SKU produk demo yang bertabrakan pada sumber lama sudah dibedakan secara
terdeterminasi untuk fixture demo saja. Kebijakan ini tidak diterapkan pada
import data pelanggan/toko sebenarnya.

## 6. Pengujian dan batas validasi

```bash
python -m pip install -r requirements-mysql-test.txt
python -m pytest -c pytest-mysql.ini
```

Suite ini mencakup skema, konfigurasi MySQL, guard 5.7, autentikasi, kontrak
rute, operasi katalog/CMS, transaksi belanja dan konversi data. Pengujian SQL
portabel memakai SQLite dengan foreign key/constraint aktif; itu tidak
membuktikan perilaku lock, collation atau trigger pada server MySQL sebenarnya.

Pengujian MySQL langsung memerlukan opt-in `MYSQL_INTEGRATION_TESTS=1`,
`APP_ENV=test`, dan database **kosong** bernama `test_meow_*`. Pengujian itu
menjalankan Alembic, memeriksa trigger, kemudian menguji transaksi paralel stok
terakhir dan retry pembayaran/pembatalan. Ia meninggalkan skema dan fixture
untuk inspeksi, tidak menjatuhkan database yang sudah ada. Gunakan database
baru untuk rerun. Petunjuk koneksi tersedia pada Step 1.

Direktori `backend/tests/` menyimpan suite HTTP lama untuk referensi. Ia tidak
lagi mengarah secara default ke server preview eksternal dan hanya dapat
dijalankan setelah `MEOW_LEGACY_HTTP_TESTS=1` serta URL test eksplisit disetel.
Sebagian asersi lamanya mencerminkan mock dan kebijakan lama; suite tersebut
bukan pengganti suite penerimaan MySQL di atas.

Hasil eksekusi dan batas yang belum diuji dicatat pada [VALIDATION.md](VALIDATION.md).

## Batas tahap berikutnya

Frontend tetap seperti semula. Form checkout/rating baru, UI Flash Sale berbasis
kategori, pagination 15 item, WhatsApp global, menu New Arrival, tombol share,
CMS tambahan, Virtual Try-On, DOKU nyata dan Everpro nyata mengikuti urutan
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), setelah konfirmasi pengguna.
