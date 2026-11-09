# Validasi akhir — MySQL 5.7.24-log dan Step 1–9

Tanggal: 6 November 2026. Laporan ini mencatat pengujian source code dalam
paket, dengan data fixture terisolasi. Database toko, server produksi, akun
merchant, dan data pelanggan nyata tidak diakses.

## Hasil eksekusi

| Pemeriksaan | Hasil yang diamati |
| --- | --- |
| Seluruh suite backend | 251 passed, 1 skipped, 1 warning dalam 90.63 detik |
| Suite frontend | 11 passed dalam 3 suite |
| Build produksi frontend | Berhasil, tidak ada error lint/kompilasi |
| Browser pelanggan | 11/11 skenario passed; tidak ada JavaScript page error |
| Browser admin | 11/11 skenario passed; tidak ada JavaScript page error |
| Python compileall | Berhasil untuk backend, migrasi, dan pengujian |
| Dependensi Python | `uv pip check`: 43 paket kompatibel |
| SQL export | Full dan incremental identik byte-for-byte dengan render Alembic terbaru |
| Riwayat migrasi | Kedua hash revisi tetap sama; head tunggal `20261106_0002` |

Perintah backend dari direktori `backend/`:

```bash
python -m pytest -c pytest-mysql.ini -q
```

Perintah frontend dari direktori `frontend/`:

```bash
CI=true npm test -- --watchAll=false --runInBand --no-cache
CI=true GENERATE_SOURCEMAP=false npm run build
```

Satu pengujian backend dilewati karena memerlukan server MySQL 5.7.24-log
nyata, database kosong bernama `test_meow_*`, `MYSQL_INTEGRATION_TESTS=1`,
`APP_ENV=test`, dan variabel koneksi eksplisit. Server tersebut tidak tersedia
pada sesi ini. Satu warning berasal dari deprecation jalur kompatibilitas
Starlette TestClient/httpx; tidak menyebabkan kegagalan. Suite juga menggunakan
httpx ASGITransport secara langsung.

Build diperiksa dengan Node 24. Peringatan data Browserslist yang berumur enam
bulan dan deprecation `fs.F_OK` pada tooling tidak menggagalkan build. Entrypoint
hasil build yang digunakan untuk browser QA adalah `main.5e6c2ed9.js`.

## Backend dan kontrak data

| Area | Lingkup verifikasi |
| --- | --- |
| Kontrak router | Semua 159 deklarasi method/path router awal tetap ada; API kini mempunyai 193 operasi pada 156 path OpenAPI, tanpa operation ID ganda |
| Runtime SQL | AST scan tidak menemukan Motor/PyMongo atau metode query dokumen lama pada modul runtime; startup dan readiness memvalidasi MySQL |
| Auth/RBAC | Password/PIN hash, token sesi tersimpan sebagai hash, expiry/revocation, akun nonaktif, PIN lock, serta pemeriksaan izin staf dan kepemilikan |
| Transaksi SQL | Rollback, read session tanpa commit implisit, snapshot pesanan, reservasi stok/promosi, idempotensi checkout/pembayaran/pembatalan |
| Catalog/CMS | Filter, paging, varian dan stok, update parsial, kategori, artikel/knowledge, 8 ekspor Excel, media publik, dan banner |
| Harga paket | Varian frame terpilih, Flash Sale aktif, SKU lensa eksplisit, surcharge indeks dan total bundle dibandingkan dengan kalkulasi `priced_cart` |
| Fitur optik | 12 pengujian fitur: resep, foto privat, rating pembeli, WhatsApp, New Arrival, seed konten, Flash Sale kategori, aset try-on dan akses |
| Integrasi | 33 pengujian transport/protokol DOKU dan Everpro, beserta transaksi SQL dan penanganan retry/rekonsiliasi |
| Commerce | 26 pengujian domain termasuk stok frame/lensa, Decimal, promo, poin, kuota, scheduler, dan idempotensi |
| Impor MongoDB | 44 pengujian mencakup 37 collection, referensi relasional, integritas nilai, checksum sumber, checkpoint/resume, rollback chunk, konflik dan drift |
| Fixture impor lengkap | 40 record sumber berkembang menjadi 69 row target; peringatan historis mengenai detail lensa yang tidak tersedia tetap eksplisit |
| Konfigurasi | Literal password, error tanpa kebocoran SQL/secret, readiness fail-closed, TLS dan kebijakan mock produksi |
| MySQL tanpa RETURNING | Jalur server-default async diuji dengan RETURNING/insertmanyvalues dimatikan; `eager_defaults=True` mencegah implicit I/O |

Pengujian foto resep memastikan file didekode penuh, dinormalisasi, disimpan
terpisah dari upload publik, dan hanya dapat dibuka pemilik/admin atau staf
berizin dengan hubungan pesanan. Batas input 8 MiB dan 20 MP diuji. Snapshot
resep pesanan tidak berubah ketika isi keranjang diperbarui.

Pengujian pembayaran memeriksa signature dari byte asli, merchant/environment,
identitas invoice dan nominal. Callback ganda tidak mengonsumsi stok lagi;
status authorization/refund/failed bukan bukti penerimaan pembayaran SALE.
Pembayaran terlambat, nominal berbeda, dan kegagalan ledger menghasilkan
rekonsiliasi tanpa memaksakan fulfillment. Pemulihan ledger memakai verifikasi
SUCCESS baru dan menyimpan audit event sebelumnya.

Pengujian Everpro memeriksa quote yang terikat pengguna, keranjang, alamat,
konfigurasi pengirim/akun, dan masa berlaku. Booking dilakukan setelah paid,
retry yang belum pasti mencari identitas pengiriman yang sama, dan callback
terlambat tidak menurunkan status delivered.

Jumlah skenario bukan ukuran seluruh kombinasi input atau jadwal concurrency.
Suite default memakai SQLite/doubles untuk isolasi dan tidak membuktikan
perilaku lock, collation, SIGNAL atau privilege MySQL nyata.

## Pengujian frontend dan browser

Tiga suite frontend berada di:

- `frontend/src/components/storefront.test.jsx`: parameter halaman, sanitasi HTML,
  nilai resep nol vs kosong, penyimpanan resep, penolakan file, serta lifecycle kamera.
- `frontend/src/pages/CheckoutPage.test.jsx`: quote milik pengguna, penggunaan ulang
  idempotency key sesudah kegagalan jaringan, dan penahanan checkout saat preview berubah.
- `frontend/src/pages/ProductDetailPage.test.jsx`: pergantian varian, respons bundle
  yang datang terlambat, harga override SKU lensa, dan identitas SKU pada keranjang.

Browser QA menggunakan Chromium 153 sebenarnya, build produksi, FastAPI dan
SQLite file terisolasi dengan WAL/foreign key. Browser memanggil route aplikasi
sebenarnya. Pembayaran dan ongkir secara eksplisit memakai mode mock; kamera
menggunakan perangkat tiruan browser atau penolakan izin yang disimulasikan.
Aset frame/model/foto adalah fixture QA, bukan data optik atau pelanggan nyata.

### Sebelas skenario pelanggan

1. Shop Now berisi 15 produk; halaman kedua berisi 5 dari fixture total 20,
   dengan filter/sort pada URL.
2. New Arrival dan kategori Frame New Arrival menampilkan produk yang sesuai.
3. Flash Sale frontend sama dengan API kampanye/harga aktif.
4. Breadcrumb, harga bundle sesuai varian, gambar try-on, renderer GLB nyata,
   dan pemilihan foto lokal berfungsi.
5. Kamera hanya dimulai setelah klik dan stream berhenti saat modal ditutup.
6. Penolakan kamera menampilkan pilihan foto yang tetap dapat digunakan.
7. Share/Copy Link artikel dan knowledge, clipboard browser, serta halaman 404.
8. WhatsApp tampil global pada login/storefront dengan pesan yang dienkode.
9. Checkout frame+lensa menyimpan semua pengukuran OD/OS, PD dan foto privat;
   akses foto tanpa login ditolak 401; satu intent pembayaran dibuat.
10. Pembayaran mock berhasil menampilkan rating produk dan transaksi, dan hasilnya
    benar-benar tersimpan pada database fixture.
11. Storefront, detail produk, modal dan checkout pada lebar 390 px tidak membuat
    dokumen melebar horizontal. Tabel resep mempunyai area scroll tersendiri.

### Sebelas skenario admin

1. Simpan WhatsApp memperbarui tombol global.
2. Publish/Unpublish artikel memengaruhi akses publik.
3. Publish/Unpublish knowledge memengaruhi akses publik.
4. Buat/edit/publish aset GLB beserta urutan sumber.
5. Form Flash Sale kategori menghasilkan anggota produk.
6. Edit kuota mempertahankan ID item kampanye dan counter.
7. Nonaktifkan kampanye secara manual.
8. Flag New Arrival tersimpan tanpa mengganti varian.
9. URL tujuan dan urutan banner tersimpan.
10. Dashboard integrasi merender status tanpa nilai kredensial.
11. Form admin WhatsApp pada lebar 390 px tidak melebar horizontal.

Ringkasan hasil mesin dan screenshot perwakilan tersedia pada
[folder QA](../qa/README.md). Screenshot dilihat langsung untuk memastikan form
resep mobile, tampilan GLB dan halaman Flash Sale admin dapat digunakan.

## Skema MySQL 5.7

- 68 tabel aplikasi/pendukung, ditambah `alembic_version`.
- 680 kolom; 107 foreign-key constraints.
- 52 UNIQUE eksplisit di luar primary key, dan 57 indeks eksplisit.
- 97 predikat validasi pada metadata; 90 trigger BEFORE INSERT/UPDATE pada 45 tabel.
- InnoDB, `ROW_FORMAT=DYNAMIC`, `utf8mb4_unicode_ci`, ID opak binary,
  uang `DECIMAL(18,2)` dan waktu UTC `DATETIME(6)`.
- Tidak ada native CHECK atau default TEXT/BLOB/JSON yang tidak didukung dalam SQL.
- Export full: 112210 byte, 69 tabel termasuk Alembic, 90 trigger.
- Export incremental kompatibilitas: 48060 byte, 90 trigger, tanpa pembuatan tabel.

SHA-256 revisi awal:

```text
79c191750eda0eea805bbdcf8c1ea748c090f8bfc9b11f632d0c14d5c18d72c1
```

SHA-256 revisi kompatibilitas:

```text
54068e89ed959673a73c80414119f28af0f3959388a223e8b633c1a4ee88fbca
```

Perbaikan Step 2 untuk default `point_logs.note` tetap dipertahankan. Compiler
mengadaptasi default TEXT legacy tersebut tanpa memutasi revision historis;
ORM memasok default Python. Export Alembic penuh dan metadata kini sejalan.
Trigger diuji untuk parity predikat, NULL semantics, SQL mode, recovery DDL yang
terputus dan penolakan guard yang berubah; sebagian memakai connection double
atau trigger SQLite ekuivalen, bukan eksekusi SIGNAL MySQL.

## Penerimaan eksternal yang belum dijalankan

1. **MySQL 5.7.24-log nyata:** DDL/trigger, izin/definer, collation, driver, dan
   contention InnoDB. Pengujian opt-in mencakup dua pelanggan memperebutkan unit
   terakhir dan pengulangan pembayaran/pembatalan, tetapi server target belum tersedia.
2. **Data MongoDB toko:** jumlah record, field produksi, snapshot backup, berkas
   media, rekonsiliasi nilai serta kapasitas dataset besar. Export asli belum
   diberikan; importer merencanakan seluruh export dalam memori dan perlu
   penilaian kapasitas pada dataset besar.
3. **Akun sandbox/production DOKU dan Everpro:** adapter nyata tersedia, tetapi
   credential, onboarding provider, callback HTTPS publik dan transaksi/booking
   jaringan merchant belum diuji. HTTP transport double bukan transaksi sandbox.
4. **Perangkat pelanggan nyata:** kamera hardware, Safari/iOS/Android, model frame
   toko dan ketepatan kalibrasinya. Try-on adalah penyesuaian visual manual,
   tanpa pengukuran wajah atau landmark tracking otomatis.
5. **Deployment/cutover/rollback produksi:** tidak ada server, saldo, stok,
   pesanan pelanggan atau file produksi yang diubah.

Gunakan [panduan rilis](../FEATURES_AND_RELEASE.md),
[integrasi](../INTEGRATIONS.md) dan [DATA_IMPORT](DATA_IMPORT.md) untuk aktivasi.
Newsletter warisan tetap simulasi; refund gateway nyata memerlukan proses
merchant. Hasil hijau lokal tidak menggantikan penerimaan MySQL dan merchant.
