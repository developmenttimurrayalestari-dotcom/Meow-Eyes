# Penyelesaian Step 3–9 dan panduan rilis

Dokumen ini melanjutkan fondasi MySQL pada Step 1 dan migrasi aplikasi pada
Step 2. Pengguna telah menyetujui pengerjaan sampai tahap terakhir. Target
database tetap **Oracle MySQL 5.7.24-log**. Backend tetap FastAPI dan SQLAlchemy;
frontend tetap React. Tidak ada pergantian framework atau fallback MongoDB.

Kode dan pengujian lokal disediakan dalam paket ini. Migrasi data toko,
pemasangan pada server produksi, dan transaksi nyata DOKU/Everpro memerlukan
akses serta konfigurasi lingkungan toko. Hasil uji yang benar-benar dijalankan
tercantum di [VALIDATION](mysql-migration/VALIDATION.md).

## Fitur pelanggan dan admin

Pembaruan 11 November 2026 menambahkan dompet poin dengan rate per perolehan, Manage Games dinamis, Puzzle Geser 20 level, Meow Space War, event cashback, RMA penggantian produk dengan video privat, dan halaman Virtual Try-On. Lihat [rancangan dan panduan konfigurasi](LOYALTY_GAMES_RMA.md).

| Tahap | Hasil implementasi | Lokasi utama |
| --- | --- | --- |
| 3. Checkout dan rating | Resep per item frame+lensa: SPH, CYL, AXIS, ADD untuk OD/OS, PD total atau kanan/kiri, catatan, dan foto privat. Snapshot resep disimpan pada pesanan. Rating produk/lensa dan transaksi tersedia sesudah pembayaran terkonfirmasi. | `/checkout`, `/payment/:orderNumber`, `/orders/:id` |
| 4. Flash Sale | Keanggotaan kampanye aktif menjadi sumber daftar dan harga promo. Pembuatan berdasarkan kategori, pilihan subkategori, persentase/potongan/harga tetap, kuota, jadwal, serta produk manual. | `/flash-sale`, `/admin/flash-sales` |
| 5. Storefront | Pagination 15 item, filter dan halaman pada URL, breadcrumb detail, menu New Arrival, kategori Frame New Arrival, tombol WhatsApp global, tombol berbagi serta Copy Link. | `/shop-now`, `/products`, `/new-arrival`, artikel dan Product Knowledge |
| 6. CMS | Publish/Unpublish, urutan dan URL banner, nomor/pesan WhatsApp, pengelolaan aset try-on, penambahan konten knowledge idempoten. | `/admin/articles`, `/admin/knowledge`, `/admin/banners`, `/admin/whatsapp`, `/admin/try-on` |
| 7. Virtual Try-On | Kamera atau foto lokal dengan deteksi mata/wajah otomatis, posisi/skala/rotasi frame mengikuti kepala, aset gambar transparan maupun GLB/GLTF, serta penanganan perangkat yang tidak mendukung kamera/WebGL. | Halaman detail frame dengan aset published |
| 8. DOKU | Hosted Checkout, penandatanganan request, verifikasi notifikasi, pemeriksaan nilai/identitas pesanan, proses ulang idempoten dan rekonsiliasi status. | Backend integrasi, halaman pembayaran, `/admin/integrations` |
| 9. Everpro | Tarif dari API, quote tersimpan dan dibatasi masa berlaku, booking sesudah dibayar, pilihan DROP/PICKUP, resi, pelacakan, callback terverifikasi dan pembaruan status. | Checkout, admin detail pesanan, `/admin/integrations` |

### Daftar dan login Google langsung

Halaman `/register` dan `/login` memakai tombol resmi **Google Identity Services**
(`https://accounts.google.com/gsi/client`). Backend memverifikasi token dengan
library resmi `google-auth[requests]`, kemudian menerbitkan sesi lokal aplikasi.
Alur ini menggantikan redirect dan pertukaran sesi melalui Emergent. Endpoint
lama `/api/auth/google-session` tidak dipakai lagi; bookmark `/auth/callback`
dikembalikan ke login tanpa menerima kredensial broker lama.

Konfigurasi awal oleh pemilik toko:

1. Buka [Google Auth Platform](https://console.cloud.google.com/auth/overview),
   pilih/buat proyek, lalu isi Branding dan Audience. Jika aplikasi masih dalam
   mode Testing, tambahkan akun penguji pada Audience.
2. Di Clients, buat OAuth client bertipe **Web application**. Isi Authorized
   JavaScript origins dengan `http://localhost` dan `http://localhost:3000` untuk
   pengujian lokal, serta origin HTTPS website produksi. Masukkan origin saja,
   tanpa path `/login` atau `/auth/callback`. Flow popup ini menggunakan callback
   JavaScript; tidak membutuhkan redirect ke server Emergent.
3. Salin Client ID ke `backend/.env.mysql`:

   ```dotenv
   GOOGLE_CLIENT_ID=CLIENT_ID_ANDA.apps.googleusercontent.com
   ```

4. Pastikan `CORS_ORIGINS` backend memuat origin frontend yang sama persis.
   Backend menyajikan Client ID publik lewat `GET /api/auth/google/config`;
   tidak perlu Client Secret atau konfigurasi Google terpisah di frontend.
5. Gunakan virtual environment backend, jalankan `python -m pip install -r
   requirements.txt` bila menginstal pada mesin lain, backup database lalu
   `python -m alembic upgrade head`. Jalankan ulang backend **secara manual**
   agar konfigurasi dan route baru terbaca; refresh halaman login/registrasi.

Client ID saat pembaruan belum tersedia; field konfigurasinya disiapkan kosong.
Selama kosong, UI menampilkan keterangan Google belum tersedia, dan form
email/password tetap bisa dipakai. Google membatasi origin ke HTTPS dengan
pengecualian localhost. IP LAN biasa seperti `http://192.168.x.x:3000` tidak
dapat dipakai sebagai origin Google; untuk akses perangkat lain gunakan domain
HTTPS yang terdaftar dan API HTTPS/proxy pada origin tersebut. Lihat
[panduan setup Google](https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid)
dan [aturan origin](https://developers.google.com/identity/protocols/oauth2/javascript-implicit-flow#origin-validation).

Migrasi `20261112_0011` menambahkan `users.google_subject` nullable dan unik,
tanpa mengubah akun atau sesi lama. Identitas ditautkan memakai `sub` Google.
Akun lama dengan Gmail atau email Workspace terverifikasi dapat dipakai kembali
tanpa kehilangan password, PIN, nama, hak akses, atau poin. Akun email pihak
ketiga yang sudah ada tidak digabung otomatis; pelanggan memakai metode login
sebelumnya. Token Google diverifikasi tanda tangan, audience, issuer, waktu,
email terverifikasi dan nonce; request dari origin lain ditolak. Token Google
tidak disimpan. Uji lokal memakai token bertanda tangan dan sertifikat uji,
serta mock SDK di browser; persetujuan/login Google nyata perlu Client ID toko.
Referensi: [verifikasi token Google](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token).

### Master produk dan editor deskripsi

Jenis Produk sistem mendukung **Frame, Lensa, Paket, dan Aksesoris**. Pilihan
pada form Tambah Jenis Produk dibaca dari `GET /api/admin/categories` melalui
field `product_types`, sehingga sesuai validasi backend. Tambahkan master
Aksesoris dari admin agar tersedia pada form produk dan filter katalog. Impor
produk juga menerima `product_type=accessories`. Produk Aksesoris memakai harga
dan stok biasa; tambahan Lens Index dan Virtual Try-On tetap untuk jenis produk
yang mendukungnya.

Migrasi `20261112_0012` memperbarui empat trigger validasi INSERT/UPDATE pada
`categories` dan `products` agar menerima `accessories`. Aturan harga, stok,
rating, dan larangan mengganti kode/grup kategori tetap berlaku. Migrasi ini
tidak mengubah atau menambah data master, produk, stok, akun, dan pesanan toko.
Backup dahulu, jalankan `python -m alembic upgrade head` dari backend, lalu
restart backend secara manual dan muat ulang halaman admin.

Brand dikelola dari tab **Brand** pada halaman Master Kategori dengan tambah,
edit, hapus, dan status aktif. Form Produk menampilkan pilihan Brand berupa
radio seperti pilihan kategori, termasuk Tanpa brand. Satu produk memiliki
maksimal satu Brand. Tab ini memakai master `brands` dan relasi `brand_id` yang
sudah ada, sehingga data dan filter Brand lama tetap terhubung tanpa migrasi.

Revisi `20261112_0008` menghapus Koleksi dari master yang dapat digunakan, filter
katalog, dan form tambah/edit Produk. Lima grup yang tersedia adalah Jenis
Produk, Jenis Lensa, Gender, Frame Shape, dan Material. Tag Koleksi lama dilepas
dari produk dan primary category lama dipindahkan ke master Jenis Produk.
Kategori Koleksi lama diarsipkan nonaktif untuk riwayat internal; API menolak
pembuatan atau penugasan Koleksi baru. Pemetaan asli disimpan privat pada setting
`taxonomy-0008-retired-collections`. Aturan flash sale Koleksi dilepas setelah
mengarsipkan asal item; item promo yang sudah terbentuk tetap mempertahankan
harga, kuota, penjualan, dan reservasinya. Tautan banner yang merujuk Koleksi
dilepas agar tidak menuju kategori yang sudah dihapus.

Deskripsi pada form tambah/edit Produk memakai `RichTextEditor` yang sama dengan
Product Knowledge: H1–H6, paragraf, format teks, daftar, tautan, tabel, gambar,
resize gambar, serta alignment. Deskripsi wajib berisi konten. HTML disimpan
pada field `description` yang sudah ada dan ditampilkan melalui `HtmlContent`
yang menyaring markup berbahaya serta menjaga gambar tetap responsif. Deskripsi
teks biasa yang sudah tersimpan tetap dapat dibaca dan diedit.

Jalankan `python -m alembic upgrade head` dari `backend` setelah backup.
Migrasi 0008 memerlukan koneksi online untuk arsip referensi. Restart backend
secara manual dan refresh frontend setelah pembaruan.

### Lens Index, Jenis Lensa, dan resep checkout

Di `/admin/lens-indexes`, tombol tambah dan Edit menyediakan pilihan satu atau
beberapa master Jenis Lensa. Harga Lensa memakai `lens_indexes.additional_price`.
Lens Index lama tetap tanpa relasi sampai admin mengaturnya; tidak ada pemetaan
otomatis berdasarkan nama. Lens Index tanpa relasi tetap tersedia untuk Frame.

Setiap baris checkout mempunyai pilihan Lens Index, foto resep, dan catatan
sendiri. Paket hanya menampilkan Lens Index aktif yang beririsan dengan master
Jenis Lensa pada kategori produk paket. Harga Lens Index sudah termasuk harga
paket, sehingga tambahan selalu Rp0. Frame menampilkan seluruh Lens Index aktif
dan menambahkan harganya per unit produk. Konfigurasi lensa tambahan dari detail
produk tetap dihitung seperti sebelumnya. Pilihan bersifat opsional.

Pada Frame, opsi **Beli frame saja (tanpa lensa)** membolehkan checkout tanpa
Lens Index, catatan, foto, atau Simpan Resep. Jika sebelumnya terdapat tambahan
lensa, pilih opsi tersebut lalu Simpan Resep untuk melepas lensa beserta biaya
tambahannya. Form yang dikembalikan ke kondisi awal tidak menghalangi checkout.
Resep kosong tidak dibuat sebagai data resep maupun snapshot pesanan.

Klik Simpan Resep setelah mengubah pilihan. Backend memvalidasi kepemilikan dan
kecocokan Jenis Lensa, lalu checkout menghitung ulang ongkir dan total. Pesanan
menyimpan snapshot nama Lens Index, biaya tambahan, foto, dan catatan. Perubahan
master setelah pesanan dibuat tidak mengubah nilai historis tersebut.

Ringkasan menampilkan Harga produk, Tambahan lensa, dan Subtotal secara terpisah.
Harga produk mengikuti promo yang berlaku, termasuk prioritas Flash Sale.
Contoh: frame Flash Sale Rp99.000 + lensa Rp350.000 = subtotal Rp449.000;
ongkir Rp8.000 menghasilkan total Rp457.000. Harga lensa tidak ditambahkan dua
kali. Biaya tambahan lensa untuk Paket tetap Rp0. Hasil hitung lama dibuang saat
pilihan resep/lensa disimpan agar respons yang terlambat tidak menimpa total baru.

Migrasi `20261112_0010` menambahkan tabel penghubung `lens_index_types`, dengan
foreign key ke Lens Index dan kategori. Backup lalu jalankan `python -m alembic
upgrade head` dan restart backend secara manual. Atur relasi melalui Edit Lens
Index dan kategori Jenis Lensa pada produk Paket sebelum digunakan pelanggan.
SQL incremental tersedia pada `backend/sql/010_lens_index_types.sql`.

### Inventory, Receipt Stock, dan Issue Stock

Inventory memuat semua produk yang belum dihapus, termasuk produk tanpa varian
atau stok awal, dengan produk terbaru di urutan atas, pencarian SKU/nama, dan
tombol Muat Ulang. Produk tanpa varian ditampilkan pada stok nol dengan aksi
Inisialisasi Stok. Receipt Stock pertama membuat varian stok standar secara
atomik. Form Produk/varian baru dimulai dari stok nol agar stok awal dapat
dicatat melalui penerimaan di Inventory.

Form Adjust menyediakan Receipt Stock (tambah) dan Issue Stock (kurang), Nomor
TTB wajib maksimal 128 karakter, jumlah bulat positif, dan catatan opsional.
Jenis transaksi, TTB, delta, jumlah akhir, reserved, dan admin dicatat dalam
`stock_movements`. Issue Stock tidak boleh mengambil stok reserved. Produk yang
sudah dihapus dan varian nonaktif ditolak oleh backend untuk penyesuaian stok.

Produk yang dihapus tetap memiliki riwayat stok pada tabel terpisah
**Stok Produk yang Dihapus**. Baris berwarna abu-abu dengan tombol dinonaktifkan.
Pemisahan ini adalah tampilan inventory, tanpa menghapus stok historis atau
memindahkan data pesanan. Halaman memuat ulang saat kembali fokus ke tab browser.

Migrasi `20261112_0009` menambahkan kolom nullable `stock_movements.ttb_number`
tanpa mengubah saldo stok lama. Backup lalu jalankan `python -m alembic upgrade
head` dan restart backend manual. Endpoint stok menerima `adjustment_type`
(`receipt_stock`/`issue_stock`), `quantity`, `ttb_number`, dan `variant_id`.
Permintaan lama dengan signed `delta` tetap diterima untuk kompatibilitas.

### Duplikat produk

Di Admin Produk, klik **Duplikat** pada baris sumber. Sistem membuat produk
nonaktif dengan nama berakhiran `(Salinan)`, SKU produk/varian baru, dan stok
serta reserved nol. Form Edit langsung terbuka untuk menyesuaikan data sebelum
diaktifkan. Salinan tetap tersimpan jika form Edit ditutup; pengisian stok
dilakukan melalui Inventory.

Deskripsi, harga katalog, kategori independen, Brand, gambar utama/galeri,
varian, spesifikasi frame dan override per varian ikut disalin. Aset Virtual
Try-On memakai record baru berstatus draft dengan relasi varian yang baru.
Penjualan, rating, reservasi, transaksi stok, dan riwayat pesanan tetap milik
produk asal. Harga/badge Flash Sale tidak disalin sebagai promo baru.

Endpoint `POST /api/admin/products/{id}/duplicate` hanya tersedia untuk admin.
Penyalinan dilakukan dalam satu transaksi dan produk yang telah dihapus ditolak.
Fitur ini menggunakan tabel yang sudah ada dan tidak memerlukan migrasi baru.

### Hapus dan nonaktifkan produk

Admin **Produk** menyediakan aksi **Nonaktifkan** dan **Hapus** pada setiap baris.
Checkbox per produk dan checkbox header memilih semua produk pada halaman yang
sedang ditampilkan (maksimal 50 per halaman). Tombol **Nonaktifkan Terpilih** dan
**Hapus Terpilih** meminta konfirmasi jumlah produk. Pergantian pencarian atau
halaman mengosongkan pilihan agar produk yang tersembunyi tidak ikut diproses.

Nonaktifkan mengubah `is_active=false`; produk tetap terlihat di admin dan dapat
diaktifkan melalui Edit Produk. Hapus mengisi `products.deleted_at` sekaligus
menonaktifkan produk, sehingga produk hilang dari daftar admin dan katalog.
Penghapusan ini bersifat logis: ID produk/varian dan referensi pesanan, stok,
Meowsurement, serta riwayat lain tetap disimpan. Produk yang sudah dihapus tidak
dapat diaktifkan kembali melalui form edit atau impor. Pesanan yang sudah dibuat
sebelum penghapusan masih dapat menyelesaikan pembayaran menggunakan snapshot.

`POST /api/admin/products/bulk-actions` menerima
`{"action":"delete"|"deactivate","product_ids":["id1","id2"]}`. Endpoint hanya
untuk admin/super admin, membatasi 200 ID per permintaan, menghapus ID duplikat,
dan mengunci produk dengan urutan tetap dalam satu transaksi. ID yang tidak
ditemukan membatalkan seluruh batch; permintaan ulang tidak menghapus riwayat
atau mengubah waktu penghapusan pertama. `DELETE /api/admin/products/{id}` kini
menjalankan Hapus, terpisah dari Nonaktifkan.

Migrasi `20261112_0007` menambahkan kolom tanggal penghapusan dan indeks daftar
admin. Buat backup lalu jalankan `python -m alembic upgrade head` dari `backend`,
diikuti `python -m mysql.check_integrity`, dan restart backend manual. Migrasi
tidak menghapus atau menonaktifkan produk yang sudah ada, dan tidak menyalakan
server. Tidak ada endpoint pemulihan produk yang sudah dihapus pada rilis ini.

### Resep dan rating

Resep melekat pada baris keranjang frame+lensa, bukan satu isian global untuk
seluruh pesanan. Dua frame pada pesanan yang sama dapat memakai resep berbeda.
Perubahan resep harus disimpan sebelum mengonfirmasi checkout. Nilai resep pada
pesanan adalah snapshot sehingga perubahan keranjang berikutnya tidak mengubah
pesanan yang sudah dibuat.

Upload menerima foto JPEG, PNG atau WebP sampai 8 MiB dan batas dimensi/piksel
yang divalidasi server. Berkas didekode serta dinormalisasi ulang; metadata foto
tidak dipertahankan. Berkas ini disimpan di `PRIVATE_UPLOAD_ROOT`, terpisah dari
aset CMS publik. Download memakai endpoint terautentikasi
`/api/prescriptions/uploads/{upload_id}`. Pemilik serta admin dapat mengaksesnya;
staff dengan `order.view` hanya boleh membuka lampiran yang sudah terkait
pesanan. URL aset publik tidak memberikan akses ke foto resep.

Rating baru boleh dikirim setelah backend mengonfirmasi pembayaran. Backend
memeriksa pemilik pesanan dan produk/komponen yang benar-benar dibeli, serta
menolak duplikasi. Form produk dan transaksi ditampilkan setelah pembayaran
berhasil dan dapat dibuka kembali melalui detail pesanan. Rating produk tetap
mengikuti moderasi review yang sudah ada.

### Flash Sale

Produk masuk halaman Flash Sale berdasarkan baris kampanye yang aktif, berada
dalam rentang waktu tayang, dan masih mempunyai kuota. Operator tidak perlu
menambahkan badge secara manual. Harga yang dikembalikan katalog dan harga yang
dipakai checkout berasal dari kampanye yang sama; backend memeriksa kembali
harga, stok, dan kuota saat transaksi.

Untuk kampanye kategori, pilih satu atau beberapa kategori, tentukan apakah
subkategori disertakan, jenis/nilai diskon, dan kuota per produk. Produk yang
cocok dimaterialisasi saat kampanye dibuat. Diskon dihitung dari harga normal
produk (`price`), bukan harga diskon; contoh 60% dari Rp420.000 menghasilkan
Rp168.000. Tombol **Sinkronkan harga & produk kategori** memperbarui harga sesuai
aturan kategori dan memasukkan produk baru tanpa mereset kuota, jumlah terjual,
reservasi, harga manual produk, atau snapshot pesanan. Aturan kategori
kampanye yang sudah dibuat tetap dipertahankan; gunakan kampanye baru untuk
mengganti aturan tersebut. Harga, kuota, keaktifan item dan metadata kampanye
dapat dikelola tanpa mengganti identitas item.

Flash Sale mengesampingkan diskon produk. Checkout yang memiliki item Flash Sale
tidak menggabungkan voucher, penukaran poin, atau reward roulette; backend
mengabaikan promo tambahan tersebut dan tidak mengonsumsi saldo/kuotanya.

Tombol **Hapus Flash Sale** meminta konfirmasi dan menghapus kampanye beserta
item/aturan kategorinya. Kampanye dengan transaksi, reservasi, atau tautan banner
tidak dapat dihapus; gunakan Nonaktifkan untuk kampanye bersejarah, atau lepaskan
tautan banner terlebih dahulu.

Untuk mengoreksi harga kampanye kategori yang dibuat dengan rumus lama, jalankan
dari `backend` (tanpa `--apply` hanya memeriksa):

```powershell
python -m mysql.reprice_flash_sales --report private/flash-price-preflight.json
python -m mysql.reprice_flash_sales --apply --report private/flash-price-applied.json
```

Kuota yang sedang direservasi tidak boleh ditimpa atau diturunkan melewati
jumlah terjual dan dipesan. Jadwal di form menggunakan waktu lokal perangkat
admin; API dan database menyimpan waktu UTC. Kampanye yang dinonaktifkan admin
tidak otomatis diaktifkan ulang oleh scheduler.

### Konten, banner, dan New Arrival

Alamat publik halaman CMS adalah `/pages/<slug>`; daftar admin menampilkan
alamat tersebut dan tombol **Buka halaman** untuk halaman Published. Semua
halaman Published otomatis muncul di kolom **Bantuan** pada footer melalui
`GET /api/pages` (metadata tanpa isi HTML). Halaman Draft, Unpublished, dan
Archived tidak tampil di footer dan tidak dapat dibuka melalui API publik.
Alias `/terms` dan `/privacy` tetap tersedia; jika slug bawaan tidak ditemukan,
alias mencari halaman Published dengan tipe kebijakan yang sesuai.

Artikel, Product Knowledge, dan CMS Pages memakai editor visual Tiptap pada
form admin. Admin dapat memilih paragraf atau H1–H6, font dan ukuran teks,
tebal/miring/garis bawah/coret, warna/sorotan, perataan, daftar, kutipan, serta
tautan. Tabel mendukung tambah/hapus baris dan kolom, header, serta gabung/pisah
sel. Gambar dapat diunggah atau dipilih dari galeri yang sama dengan thumbnail;
tambahkan teks alternatif, lalu klik **Tambahkan gambar ke konten**. Lebarnya
dapat diatur lewat preset atau dengan menarik pegangan pada keempat sudut
gambar. Rasio gambar tetap dipertahankan; hasil resize disimpan sebagai
persentase area konten sehingga tetap responsif di mobile. Setelah gambar
diklik, pilih rata kiri/tengah/kanan pada toolbar gambar atau toolbar utama.
Pegangan resize juga mendukung tombol panah pada keyboard.

Konten disimpan sebagai HTML pada field yang sama; tidak memerlukan migrasi
database atau API key editor. Tampilan publik memakai format heading, tabel,
dan gambar yang sama. Sanitasi membatasi CSS pada tipografi yang didukung dan
menghapus skrip, event handler, URL berbahaya, serta elemen aktif. Path unggahan
tetap relatif pada data dan disesuaikan dengan alamat backend ketika ditampilkan.

Status publikasi menjadi satu sumber keputusan untuk artikel dan knowledge.
Unpublish menghilangkan konten dari daftar dan detail publik. Teks HTML CMS
dirender melalui sanitizer di frontend. Banner dapat diurutkan dengan
`sort_order`, diberi URL tujuan, serta dijadwalkan. Link yang tidak aman ditolak.

New Arrival mempunyai flag dan batas waktu opsional pada form produk. Menu
`/new-arrival` menampilkan produk aktif yang ditandai, sedangkan kategori
`frame-new-arrival` khusus untuk frame. Keanggotaan kategori ini dihitung dari
flag dan periode produk; tidak menyalin hubungan kategori secara permanen. Seed fitur melakukan satu kali pemetaan badge `new`
lama ke flag agar katalog sebelumnya tetap dapat digunakan. Marker seed
mencegah pemetaan ulang menyalakan produk yang kemudian dinonaktifkan admin.

Nomor dan pesan awal WhatsApp dikelola dari halaman terpisah. Tombol global
hanya muncul jika fitur diaktifkan dan nomor tersedia. Nomor dapat menggunakan
format internasional Indonesia, misalnya pola `628…`; pesan dimasukkan ke URL
WhatsApp dengan encoding yang sesuai.

## Menyiapkan lingkungan

### Backend dan MySQL

Gunakan Python 3.12 dan environment terpisah. Dari root proyek:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp backend/.env.mysql.example backend/.env.mysql
```

Isi koneksi MySQL di `.env.mysql`, lalu jalankan dari direktori backend:

```bash
cd backend
python -m alembic upgrade head
python -m mysql.check_integrity
python seed_features.py
```

Perintah seed tanpa `--apply` menampilkan rencana. Setelah memeriksa hasilnya:

```bash
python seed_features.py --apply
python -m uvicorn server:app --host 127.0.0.1 --port 8001
```

Migrasi head kini `20261112_0012`: 68 tabel dasar, 11 tabel Meowsurement customer,
14 tabel poin, game, cashback dan RMA, serta tabel relasi Lens Index–Jenis Lensa
(94 tabel aplikasi). Lihat
[panduan fitur baru](LOYALTY_GAMES_RMA.md) dan [runbook Meowsurement](optifit/RUNBOOK.md).
Kedua revisi historis 0001/0002 tidak diubah. Pengujian nyata terhadap MySQL
5.7.24 tetap diperlukan untuk lock, collation dan trigger. Gunakan akun migrasi
untuk DDL/audit trigger dan akun aplikasi untuk operasi harian.

Sumber MongoDB sebenarnya diproses melalui prosedur dry run, rekonsiliasi, dan
cutover di [DATA_IMPORT](mysql-migration/DATA_IMPORT.md). Seed demo hanya untuk
database development/test kosong dengan password dan PIN yang disediakan
operator secara eksplisit. Jangan gunakan seed demo pada data toko.

### Konten tambahan

Seed fitur memasukkan topik berikut jika belum ada, tanpa mengganti konten
editorial yang sudah tersimpan:

- Frame Shape: Hexagonal, Kotak (Square), Bulat (Round), Half Rim, Full Rim.
- Material: Plastic, Mixed Material (contoh Acetate mix Titanium).
- Lens Type: Lensa Normal, Lensa Minus, Lensa Plus, Lensa Silinder.

Half Rim dan Full Rim dijelaskan sebagai konstruksi bingkai dalam kelompok
navigasi yang diminta. Informasi lensa bersifat penjelasan produk; nilai resep
pelanggan berasal dari isian atau dokumen mereka.

### Frontend

Gunakan Node 20–24; build paket ini diperiksa dengan Node 24. Lockfile yang
menjadi acuan adalah `frontend/package-lock.json`. `.npmrc` mempertahankan
resolusi peer dependency yang diperlukan stack React/CRA lama. Ajv 8 dipasang
secara eksplisit agar alat build tidak memasangkan `ajv-keywords` 5 dengan Ajv 6.

```bash
cd frontend
npm ci
cp .env.example .env
npm start
```

Development memakai `REACT_APP_BACKEND_URL=http://localhost:8001`. Untuk reverse
proxy produksi yang menyajikan frontend dan `/api` pada origin yang sama,
biarkan nilai ini kosong saat build. Untuk origin terpisah, isi URL backend
HTTPS dan daftarkan origin frontend secara eksplisit pada `CORS_ORIGINS`.

```bash
npm run build
```

Sajikan hasil `frontend/build` dengan fallback route SPA ke `index.html`.
Proxy `/api` ke FastAPI sebelum menerapkan fallback SPA. Berkas resep privat
hanya disajikan melalui FastAPI, bukan alias static server.

## Virtual Try-On

Pilihan produk aset mengambil master dengan `product_type IN ('frame','package')`
dan `deleted_at IS NULL`; produk Lensa dan produk yang sudah dihapus tidak
ditampilkan. Stok nol dan belum memiliki aset bukan alasan produk disembunyikan.
Frame maupun Paket mempertahankan jenis produknya. Form memuat ulang
pilihan saat dibuka, mendukung pencarian nama/SKU produk maupun SKU varian, dan
menampilkan pesan kosong/error beserta aksi muat ulang agar tidak tampak macet.

Admin memilih produk Frame/Paket, varian opsional, sumber gambar publik transparan
atau URL model GLB/GLTF, preview, urutan, dan status. Aset published dari produk
aktif tersedia pada halaman produk dan katalog Virtual Try-On, untuk Frame dan
Paket. Varian nonaktif tidak menampilkan aset spesifik variannya. API admin
`GET /api/admin/products?try_on_eligible=true` menyediakan kedua jenis produk.
Tidak diperlukan migrasi database. Restart backend manual untuk memuat aturan
validasi/katalog baru. Gunakan sumber HTTPS/CORS yang dapat diakses browser. Model
GLTF dengan tekstur/buffer eksternal memerlukan sumber dependensi yang valid;
GLB dengan aset tertanam lebih mudah dikelola.

Pratinjau kamera/foto memakai MediaPipe Face Landmarker untuk mendeteksi mata
dan wajah di browser. Frame otomatis mengikuti titik tengah mata, lebar wajah,
dan kemiringan kepala; pelanggan tidak mengisi slider atau menyeret frame.
Koordinat disesuaikan dengan rasio gambar dan kamera bercermin. Hasil kamera
dihaluskan untuk mengurangi getaran; ketika wajah hilang, frame disembunyikan.
Pratinjau ini bukan pengukuran ukuran fisik frame atau PD.

Model dan runtime disajikan dari `frontend/public/try-on/vision/`, bukan CDN
eksternal saat customer memakai fitur. Manifest menyimpan versi dan checksum.
Jika menyiapkan ulang aset, jalankan `npm run prepare:try-on` dari frontend
(memerlukan koneksi internet saat setup). Foto/video tidak dikirim ke server
oleh antarmuka try-on. Kamera hanya dibuka setelah tindakan pelanggan; stream,
loop deteksi, dan detector dilepas ketika tampilan ditutup atau kamera dihentikan.

Skala admin adalah pengali lebar frame, offset X/Y berupa proporsi lebar frame,
dan rotasi dalam derajat. JSON kalibrasi adalah metadata yang disimpan; renderer
menggunakan kolom numerik tersebut dan tidak menerapkan pengukuran fisik dari
metadata secara otomatis. Atur kalibrasi pada perangkat perwakilan sebelum
menerbitkan aset. Jika WebGL tidak tersedia, gunakan aset gambar; jika kamera
ditolak atau tidak tersedia, pelanggan dapat memilih foto lokal. HTTPS atau
localhost diperlukan browser untuk akses kamera.

## Pembayaran dan pengiriman

Detail konfigurasi, endpoint resmi, notifikasi, polling dan penanganan kondisi
belum pasti tersedia di [INTEGRATIONS](INTEGRATIONS.md).

Aktifkan `PAYMENT_PROVIDER=doku` dan `SHIPPING_PROVIDER=everpro` pada lingkungan
yang sudah mempunyai kredensial. Simpan kredensial hanya di environment atau
secret manager. Status konfigurasi yang dapat ditinjau admin tersedia pada
`/admin/integrations`; halaman ini tidak menampilkan secret.

DOKU menggunakan halaman pembayaran hosted. Kembalinya browser ke website tidak
mengubah status menjadi paid; status bersumber dari hasil server yang telah
diverifikasi. Nominal dikirim dalam rupiah bulat sesuai API DOKU. Booking
Everpro dilakukan sesudah pesanan dibayar dan operator menyiapkan paket.

Timeout saat membuat pembayaran/pengiriman dapat berarti penyedia telah
menerima request meskipun respons belum diterima aplikasi. Sistem menyimpan
identitas request dan status proses untuk rekonsiliasi. Jangan membuat transaksi
baru atau memaksa status paid untuk melewati kondisi tersebut. Gunakan tindakan
pembaruan status, scheduler, dan panduan rekonsiliasi penyedia.

Simulasi tersedia hanya pada development/test dengan flag eksplisit
`ENABLE_MOCK_PAYMENTS=1` serta provider mock. Produksi menolaknya. Pengujian
adapter dengan transport tiruan membuktikan perilaku aplikasi terhadap contoh
protokol; pengujian akun sandbox tetap harus dilakukan sebelum produksi.

## Urutan aktivasi toko

1. Siapkan backup, lingkungan staging, dan MySQL 5.7.24 dengan konfigurasi yang
   lolos readiness serta audit integritas.
2. Jalankan dry run impor MongoDB, tinjau konflik dan rekonsiliasi. Terapkan impor
   pada target yang sesuai setelah penulis sumber dihentikan sebagaimana panduan.
3. Jalankan seed fitur, lalu tinjau konten, New Arrival, banner, Flash Sale,
   pengaturan WhatsApp, serta aset try-on di dashboard.
4. Konfigurasikan akun sandbox DOKU/Everpro, origin pengiriman, URL HTTPS publik,
   notifikasi, dan satu worker scheduler. Uji pembayaran sukses/gagal/kedaluwarsa,
   notifikasi ulang, perubahan keranjang setelah quote, serta resi dan pelacakan.
5. Setelah penerimaan staging, gunakan kredensial produksi dan alamat endpoint
   produksi yang diberikan penyedia. Pantau rekonsiliasi pembayaran, stok,
   saldo/kuota, pengiriman dan readiness.

Paket ini tidak mengirim email newsletter nyata; mekanisme simulasi newsletter
warisan tetap diberi penanda `mocked`. Refund uang melalui gateway dan automatic
face tracking bukan bagian dari fitur yang diaktifkan oleh implementasi ini.
