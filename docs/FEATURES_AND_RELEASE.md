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

### Menjalankan frontend dan backend dengan PM2

File [ecosystem.config.js](../ecosystem.config.js) mendefinisikan `meow-backend`
(Uvicorn, port 4001) dan `meow-frontend` (development server CRACO seperti
`npm start`, port 4000). Frontend dijalankan melalui launcher
`frontend/scripts/start-pm2.cjs` yang menetapkan `NODE_ENV` dan `BABEL_ENV` ke
`development` sebelum memuat CRACO dengan argumen `start`. Ini mencegah konflik
React Refresh jika environment proses sebelumnya berisi `production`, dan
bekerja di Windows dan Linux. Field
`script` PM2 merupakan path executable/script, bukan nama perintah npm.

Backend memakai Python virtual environment `backend/.venv_backend`: pada Linux
`bin/python`, pada Windows `Scripts/python.exe`. Satu proses dan satu worker
menjaga maintenance scheduler tidak berjalan ganda. Konfigurasi backend tetap
berasal dari `backend/.env.mysql`.

Pasang PM2 sekali dengan `npm install -g pm2`. Di folder frontend, jalankan
`npm ci` bila dependencies belum terpasang. Sesuaikan `REACT_APP_BACKEND_URL`
pada `frontend/.env` dengan alamat backend yang dapat diakses browser pelanggan.
Samakan origin frontend dengan `CORS_ORIGINS` dan `PUBLIC_FRONTEND_URL` backend.

Hentikan proses manual yang menggunakan port sama, lalu dari folder `Meow-Eyes`:

```bash
pm2 start ecosystem.config.js
pm2 status
```

Jika sebelumnya frontend memakai server statis `serve`, ganti proses frontend
agar entry dan environment lama tidak dipakai kembali:

```bash
pm2 delete meow-frontend
pm2 start ecosystem.config.js --only meow-frontend
pm2 save
pm2 logs meow-frontend --lines 30
```

Jalankan perintah dengan akun OS yang sama dengan akun pemilik proses PM2.
Port dapat diubah melalui `FRONTEND_PORT`/`BACKEND_PORT` pada file ecosystem.
Setelah perubahan environment atau port, terapkan dengan:

```bash
pm2 restart ecosystem.config.js --update-env
pm2 save
```

Frontend mode ini mengompilasi source saat berjalan dan memperbarui tampilan
setelah source diedit. Perubahan `frontend/.env` memerlukan restart frontend.
Frontend development ini tidak membutuhkan `frontend/build/index.html`.

Mode server statis `serve` memerlukan hasil `npm run build` di folder frontend.
Error `ENOENT ... frontend/build/index.html` berarti file build belum tersedia.
Mengganti `script: 'serve'` menjadi `script: 'start'` saja tidak menjalankan
`npm start`; gunakan konfigurasi CRACO di ecosystem yang disediakan.

Periksa kesiapan API pada `http://127.0.0.1:4001/api/health/ready` (sesuaikan port).
Perintah pengelolaan:

```bash
pm2 logs meow-backend --lines 50
pm2 restart meow-backend
pm2 stop meow-frontend
pm2 resurrect
```

`pm2 save` menyimpan daftar proses; `pm2 resurrect` memulihkannya. Pada AlmaLinux,
jalankan `pm2 startup systemd` dan ikuti instruksinya, lalu `pm2 save` untuk
pemulihan setelah boot. Pada Windows, buat Task Scheduler **At log on** dengan
akun yang sama, menjalankan path lengkap `pm2.cmd` dengan argumen `resurrect`.

Referensi: [ecosystem PM2](https://pm2.keymetrics.io/docs/usage/application-declaration/),
[server statis dan SPA](https://pm2.keymetrics.io/docs/usage/expose/), dan
[startup/pemulihan proses](https://pm2.keymetrics.io/docs/usage/startup/).

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

### Registrasi/login nomor telepon: nonaktif sementara

Registrasi dan login telepon saat ini **nonaktif secara default**. Pelanggan
menggunakan email/password, Google, atau Facebook yang sudah dikonfigurasi.
Kolom/pilihan telepon disembunyikan pada form, dan API menolak registrasi/login
telepon dengan HTTP 403. Semua field login (`phone`, `identifier`, maupun field
legacy `email` berisi nomor) mematuhi pembatasan yang sama. Akun, password, PIN,
poin, dan nomor yang sudah tersimpan tidak dihapus. Sesi yang masih valid tetap
berlaku; fitur ini tidak mencabut sesi pelanggan yang sudah masuk.

Untuk mengaktifkan kembali, isi pada **backend/.env.mysql di server**:

```dotenv
AUTH_PHONE_ENABLED=true
```

Kemudian restart backend dan periksa flag publik (sesuaikan port):

```bash
pm2 restart meow-backend --update-env
curl http://127.0.0.1:4001/api/auth/config
```

Hasil harus `{"phone_enabled":true}`. Refresh penuh halaman registrasi/login.
Frontend membaca flag dari API; tidak perlu flag telepon terpisah di frontend.
Untuk mematikan lagi, set `AUTH_PHONE_ENABLED=false`, restart backend, dan refresh
browser. Variabel environment proses mengungguli file `.env.mysql`; pastikan
shell/konfigurasi PM2 tidak menyimpan override yang bertentangan.

Saat diaktifkan, pendaftaran telepon memakai nama, nomor, dan password tanpa
email. Format `08?`, `628?`, dan `+628?` dinormalisasi ke `+628?` dan harus unik.
Tidak ada pengiriman/verifikasi OTP. Nomor alamat/profil tidak otomatis menjadi
identitas login akun lama. Migrasi historis `20261117_0013` tetap diperlukan;
tidak ada downgrade atau penghapusan data untuk menonaktifkan fitur ini.

### Login Facebook langsung melalui Meta

Tombol **Masuk dengan Facebook** tersedia pada `/login` dan `/register`. Browser
memakai SDK resmi `https://connect.facebook.net/id_ID/sdk.js`; backend memeriksa
token melalui `/debug_token`, memvalidasi App ID, user ID, masa berlaku token
dan akses data, kemudian mengambil `/me` dengan `appsecret_proof`. Identitas
lokal diikat ke `users.facebook_subject` yang unik, bukan ID/nama/email yang
dikirim bebas oleh browser. Token Meta dan App Secret tidak disimpan pada sesi
lokal atau dikirim lewat URL website. Session token aplikasi tetap di-hash;
PIN onboarding serta tujuan halaman setelah login tetap berlaku.

Konfigurasi pemilik toko pada [Meta for Developers](https://developers.facebook.com/apps/):

1. Buat/pilih aplikasi dengan use case Facebook Login untuk autentikasi pengguna.
   Lengkapi App Domains (`meoweyes.com`), Website URL HTTPS, email dukungan,
   URL kebijakan privasi dan petunjuk penghapusan data yang sudah dipublikasikan
   dari CMS. Gunakan domain yang benar-benar dipakai website.
2. Aktifkan Facebook Login untuk web dan **Login with JavaScript SDK**, lalu isi
   **Allowed Domains for JavaScript SDK** dengan domain website. Flow ini memakai
   popup `FB.login` dan callback JavaScript pada halaman login/registrasi. Jangan
   mengisi endpoint callback backend yang tidak ada pada aplikasi ini.
3. Salin App ID dan App Secret ke konfigurasi **backend saja**:

   ```dotenv
   FACEBOOK_APP_ID=APP_ID_ANDA
   FACEBOOK_APP_SECRET=APP_SECRET_ANDA
   FACEBOOK_GRAPH_VERSION=v27.0
   AUTH_PHONE_ENABLED=false
   ```

4. Tambahkan origin HTTPS frontend ke `CORS_ORIGINS`, pertahankan origin lain
   yang masih dipakai, dan sesuaikan `PUBLIC_FRONTEND_URL`. Facebook SDK memerlukan
   HTTPS untuk tindakan autentikasi. App Secret tidak boleh dimasukkan ke
   `frontend/.env`, source React, log, atau dikirim melalui chat.
5. Gunakan akun dengan role aplikasi untuk pengujian Development. Untuk pelanggan
   umum, selesaikan persyaratan dashboard Meta dan aktifkan mode Live. Permintaan
   akses aplikasi dibatasi pada `public_profile,email`.

Deploy kode beserta migrasi, setelah backup database:

```bash
cd /home/vmnginx/Project/meow/Meow-Eyes/backend
.venv_backend/bin/python -m alembic upgrade head
.venv_backend/bin/python -m mysql.check_integrity
cd ..
pm2 restart meow-backend --update-env
pm2 restart meow-frontend --update-env
curl http://127.0.0.1:4001/api/auth/facebook/config
```

Hasil konfigurasi harus berisi `enabled:true`, App ID, dan versi Graph API;
App Secret tidak pernah ditampilkan. Jika App ID/Secret belum diisi, tombol
Facebook nonaktif dan menampilkan keterangan belum tersedia. Untuk frontend
statis, lakukan `npm run build` setelah mengubah source frontend.

Migrasi `20261117_0014` hanya menambahkan identitas Facebook nullable/unik tanpa
mengubah akun lama. Pendaftaran pertama membutuhkan email yang diberikan Meta.
Jika email tidak tersedia/izin ditolak, pelanggan diminta mengizinkan email
atau mendaftar melalui email. Login berikutnya tetap memakai identitas Facebook
meskipun Meta tidak mengembalikan email lagi. Email yang sudah terdaftar melalui
metode lain tidak digabung otomatis: pelanggan menggunakan metode akun lamanya.
Akun nonaktif tetap ditolak. Mengubah App ID dapat mengubah namespace identitas
Facebook; evaluasi pemetaan akun sebelum mengganti aplikasi Meta.

Uji lokal menggunakan SDK/token response Meta tiruan dan database terisolasi;
login/consent Facebook nyata memerlukan App ID, App Secret, dan domain HTTPS
milik toko yang sudah dikonfigurasi. Referensi resmi:
[Facebook Login Web](https://developers.facebook.com/docs/facebook-login/web/),
[Debug Token](https://developers.facebook.com/docs/graph-api/reference/debug_token/),
[Secure Requests](https://developers.facebook.com/docs/graph-api/guides/secure-requests/),
dan [versi Graph API](https://developers.facebook.com/docs/graph-api/changelog/).

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

Pada setiap baris checkout tersedia tombol **Gunakan resep profil** sebagai
pilihan selain upload foto. Tombol mengambil resep yang sudah disimpan pada
halaman Profil melalui `/customer/profile`, lalu menyalin SPH, CYL, AXIS, ADD,
PD dan catatan ke item tersebut. Angka 0 tetap dipertahankan sebagai angka,
bukan dianggap kolom kosong. Ukuran ditampilkan sebagai ringkasan baca-saja;
form ukuran manual tetap disembunyikan di checkout. Foto sebelumnya dilepas
saat memakai profil agar tidak tercampur dengan resep lain, dan customer dapat
melampirkan foto pendukung kembali jika diperlukan.

Klik **Simpan Resep** untuk menerapkannya. Pilihan per baris tetap terpisah;
jumlah dua atau lebih pada satu baris memakai resep yang sama. Jika profil
belum mempunyai resep atau gagal dimuat, draft item tetap ada dan customer
dapat memakai foto/catatan. Tautan **Buka Profil** membuka tab baru agar draft
checkout tidak hilang. Tombol **Gunakan foto/catatan saja (hapus ukuran)**
melepas ukuran yang sudah disalin. Pengisian resep tetap opsional untuk Frame.

Data yang disalin menjadi resep item dan snapshot pesanan melalui endpoint
yang sudah ada. Perubahan profil sesudahnya tidak mengubah resep item/pesanan
yang telah disimpan. Selama mengambil profil atau terdapat perubahan resep
yang belum disimpan, pembuatan pesanan ditahan. Fitur ini tidak memerlukan
migrasi database atau endpoint backend baru.

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

Migrasi head kini `20261117_0014`: 68 tabel dasar, 11 tabel Meowsurement customer,
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

## Program member, COD, dan Add On — 20 November 2026

Migrasi `20261120_0015` menambahkan tujuh tabel dan kolom tambahan, mempertahankan transaksi, harga produk, password, PIN, dan lot poin sebelumnya. Ekspor SQL tersedia di `backend/sql/015_customer_growth_cod_addons.sql`. Skema aplikasi menjadi 101 tabel bisnis.

| Struktur | Kolom / relasi baru |
| --- | --- |
| `users` | `email_verified_at`, `referral_code` unik; akun lama memperoleh kode tanpa dianggap sudah memverifikasi email |
| `email_verifications` | FK user, hash token unik, email tujuan, kedaluwarsa, waktu pemakaian |
| `customer_referrals` | PK referee, FK referrer, snapshot aturan dan penanda reward; satu pengajak per akun baru |
| `customer_growth_rewards` | Event unik, penerima, snapshot reward/rate, status antrean; mencegah pemberian berulang |
| `customer_voucher_grants` | Pasangan user–voucher unik dan sumber klaim/reward |
| `daily_checkins` | PK user–tanggal WIB, streak dan jumlah poin |
| `vouchers` | `audience`: general, new_member, referral |
| `products` | `sale_role`: main atau add_on; independen dari jenis Frame/Lensa/Paket/Aksesori |
| `cart_item_addons` | FK baris cart dan pasangan produk–varian; satu SKU per produk Add On |
| `orders` / `payments` | `payment_mode=online/cod`, `payment_status=cod_pending`, provider pembayaran `cod` |
| `order_item_components` | Snapshot komponen `add_on` selain primary/lens; tetap satu baris paket di order |
| `addon_flash_reservations` | FK komponen order dan Flash Sale; kuota Add On ikut dicadangkan/dikonsumsi/dilepas |
| `addresses` / `order_addresses` | Latitude/longitude berpasangan dan tervalidasi; order mempertahankan snapshot titik tujuan |

### Penggunaan customer dan admin

- Profil customer menyediakan verifikasi email, kirim ulang, pembaruan kontak, tautan referral, serta check-in. Tautan verifikasi berlaku 30 menit; database hanya menyimpan hash. Pengiriman ulang memiliki jeda 60 detik, dan penggantian email membatalkan verifikasi lama. Google dengan email otoritatif dapat mengonfirmasi email melalui identitas Google yang sudah diverifikasi backend.
- Admin membuka **Program Member & COD** untuk mengaktifkan referral, memilih trigger pendaftaran/transaksi pertama selesai, mengatur reward tiap pihak, serta poin harian/streak dan masa berlakunya. Reward referral dicatat melalui antrean idempoten; scheduler mengirimkannya tiap menit, atau saat akun penerima dibuka. Akun suspend tidak menerima reward sampai diaktifkan kembali.
- Semua poin baru memakai lot/history yang sama dengan fitur lama. Rate dan versi dicatat saat hak reward diperoleh; perubahan rate berikutnya tidak mengubah nilai poin tersebut. Check-in maksimal sekali per tanggal WIB, streak putus setelah melewatkan satu hari dan siklus hadiah berulang setiap tujuh hari.
- Pada pengaturan referral dan Daily Check-in, centang **Berlaku selamanya** untuk poin tanpa kedaluwarsa. Lepas centang untuk mengisi jumlah hari (1–3650). Perubahan berlaku pada check-in berikutnya dan referral baru; aturan referral yang sudah terdaftar serta masa berlaku poin yang sudah diperoleh tetap mengikuti snapshot sebelumnya. Masa berlaku voucher tetap mengikuti pengaturan voucher.
- Pada menu **Voucher**, pilih sasaran **Member Baru**. Email wajib terverifikasi untuk klaim maupun checkout, hanya transaksi pertama dan sekali per akun. Order belum dibayar juga menahan kuota; pembatalan melepasnya. Voucher **Penerima Reward Referral** memerlukan grant pada akun yang bersangkutan.
- Menu **Pelanggan** mendukung pencarian, filter Verified/Unverified/Aktif/Suspend, pagination, edit kontak, detail transaksi, saldo/nilai poin, history dan jumlah referral. Suspend mencabut sesi login. Admin tidak dapat memalsukan tanggal verifikasi melalui form edit.
- Main Product menampilkan pilihan beberapa Add On ketika ditambahkan/dibeli. Pilihan opsional, setiap Add On mengikuti kuantitas produk utama. Server menghitung seluruh harga, berat dan kebutuhan stok; checkout menyimpan satu item dengan snapshot rincian komponen. Lens Index dan resep opsional yang sudah ada tetap mengikuti aturan Frame/Paket sebelumnya. Flash Sale pada komponen tetap menonaktifkan diskon lain.
- Ulasan produk dan pesanan tersedia setelah `shipment_status=delivered`; pembayaran berhasil saja belum membuka form atau endpoint penilaian.

### SMTP Zimbra

Isi konfigurasi backend `.env.mysql`; contoh juga tersedia pada `.env.mysql.example`:

```dotenv
SMTP_HOST=mail.trl.co.id
SMTP_PORT=587
SMTP_SECURITY=starttls
SMTP_AUTH_REQUIRED=true
SMTP_USERNAME=admin@meoweyes.com
SMTP_PASSWORD=isi_di_server
SMTP_FROM_EMAIL=admin@meoweyes.com
PUBLIC_FRONTEND_URL=https://meoweyes.com
```

Port 587/STARTTLS merupakan contoh konfigurasi; sesuaikan dengan layanan Zimbra. Jika memakai SMTPS, gunakan port 465 dan `SMTP_SECURITY=ssl`. Sertifikat TLS diverifikasi. Akun SMTP harus diizinkan mengirim sebagai `admin@meoweyes.com`. Password tetap berada di server. Pendaftaran tetap berhasil jika SMTP belum siap; UI menyediakan pengiriman ulang dan tidak menganggap email sudah terverifikasi.

### Urutan penerapan

1. Backup database dan hentikan penulisan aplikasi selama upgrade skema/guard MySQL. Jangan menggunakan `alembic stamp` untuk melewati migrasi.
2. Dari direktori backend, gunakan Python venv yang sama dengan proses backend:

   ```bash
   .venv_backend/bin/python -m alembic upgrade head
   .venv_backend/bin/python -m mysql.check_integrity
   ```

   Windows menggunakan `.venv_backend\Scripts\python.exe`. Migrasi harus selesai sebelum backend versi baru dijalankan agar tidak terjadi `schema_revision_mismatch`.
3. Isi SMTP dan titik toko `EVERPRO_ORIGIN_LATITUDE/LONGITUDE`. Aktifkan program/reward melalui admin. Jalankan tepat satu scheduler aktif untuk penyaluran reward tertunda dan rekonsiliasi.
4. Restart backend secara manual setelah environment diperbarui. Jika menggunakan PM2: `pm2 restart meow-backend --update-env`. Repository memakai frontend development loader pada PM2; restart `meow-frontend` setelah memperbarui kode/env. Jika hosting melayani build statis, jalankan `npm run build` dan terapkan build baru melalui alur deployment biasa.
5. Ikuti audit dan pengujian sandbox pada [INTEGRATIONS.md](INTEGRATIONS.md). Tidak ada proses backend/PM2 yang dijalankan otomatis oleh pembaruan ini.

Validasi lokal: 453 tes backend dan 252 tes frontend lulus. Build produksi lulus dengan peringatan MediaPipe/source map yang sudah ada. Sembilan alur desktop/mobile diperiksa dengan Edge headless dan API tiruan, tanpa error JavaScript. Uji MySQL konkurensi tetap terpisah pada database kosong `test_meow_*`; dua tes symlink Windows memerlukan hak akses khusus. SMTP dan akun merchant DOKU/Everpro belum diuji melalui jaringan nyata. Migrasi disediakan sebagai kode/SQL; belum diterapkan ke database operasional.

### Pemulihan migrasi 0015 pada MySQL 5.7 — 23 November 2026

Error `Customer growth migration preflight failed: growth_fk_missing:...` pada tabel referral, reward, voucher grant, check-in, dan Add On dapat berasal dari pembacaan aturan foreign key. MySQL 5.7 dapat menghilangkan aturan default `ON DELETE RESTRICT` dari `SHOW CREATE TABLE`, sehingga SQLAlchemy mengembalikan opsi kosong. Pemeriksaan revisi `0015` kini memperlakukan opsi kosong, `RESTRICT`, dan `NO ACTION` sebagai aturan yang setara. `CASCADE`, `SET NULL`, kolom relasi, dan tabel tujuan tetap diperiksa.

DDL MySQL yang selesai sebelum error tetap tersimpan meskipun Alembic belum mencatat revisi `0015`. Jalur migrasi online kini memeriksa struktur yang sudah ada, melewati kolom/tabel/index yang sesuai, menyelesaikan objek yang belum dibuat, lalu memasang dan mengaudit trigger. Struktur yang tidak sesuai tetap menghentikan migrasi; data transaksi dan kode referral yang sudah terisi tidak ditulis ulang. Ekspor SQL offline tetap merupakan skrip untuk penerapan awal, bukan untuk mengulang deployment parsial.

1. Buat backup database, hentikan penulisan aplikasi selama pemulihan, dan perbarui kode server, khususnya `backend/migrations/versions/20261120_0015_customer_growth_cod_addons.py`.
2. Jalankan dengan venv backend dari direktori server:

   ```bash
   cd /home/vmnginx/Project/meow/Meow-Eyes/backend
   .venv_backend/bin/python -m alembic current
   .venv_backend/bin/python -m alembic upgrade head
   .venv_backend/bin/python -m alembic current
   .venv_backend/bin/python -m mysql.check_integrity
   ```

   Hasil akhir `alembic current` harus `20261120_0015 (head)` dan audit integritas harus lulus. Jika muncul `existing schema mismatch`, periksa objek yang disebutkan sebelum melanjutkan; jangan melewati audit menggunakan `alembic stamp`, menghapus tabel, atau menonaktifkan foreign key.
3. Setelah upgrade dan audit berhasil, jalankan kembali backend. Untuk proses PM2 yang sudah ada: `pm2 restart meow-backend --update-env`.

Pengujian regresi mencakup hasil parser `SHOW CREATE TABLE` tanpa `ON DELETE`, perbedaan aturan foreign key yang sesungguhnya, struktur tidak sesuai, pengulangan deployment lengkap, serta kegagalan koneksi pada beberapa posisi DDL dan pemasangan trigger. Total 488 tes backend lulus; satu pengujian MySQL nyata dilewati karena memerlukan database kosong khusus, dan dua pengujian symlink Windows tidak dijalankan. Tes migrasi memakai simulasi inspector/DDL; penerapan ke database server tetap dilakukan melalui perintah di atas.

### Poin berlaku selamanya — revisi 0016

Checkbox **Berlaku selamanya** tersedia pada reward referral untuk masing-masing pihak, Daily Check-in, setiap game di **Manage Games** (termasuk Roulette), dan event cashback. Jika dicentang, kolom jumlah hari disembunyikan. Jika dilepas, jumlah hari sebelumnya muncul kembali; aturan permanen yang baru dibuka memakai 30 hari sebagai pilihan awal saat diubah menjadi terbatas. Customer melihat keterangan **berlaku selamanya**, bukan **0 hari**. Di API/database, nilai 0 tetap menjadi penanda aturan permanen, sedangkan tanggal kedaluwarsa lot/history disimpan NULL.

Migrasi `20261123_0016` memperbarui empat guard MySQL 5.7 untuk menerima masa berlaku poin permanen pada game/cashback, serta mengizinkan tanggal kedaluwarsa kosong pada catatan hadiah poin Roulette. Saldo, rate, riwayat, tanggal kedaluwarsa lama, snapshot ronde, dan snapshot cashback yang sudah dibuat tidak ditulis ulang. Periode event cashback tetap wajib diisi; periode event menentukan pembelian yang memenuhi syarat, sedangkan checkbox menentukan masa berlaku poin hasilnya. Reward Roulette selain poin tetap mengikuti masa berlaku reward sebelumnya.

Sebelum menerapkan kode backend terbaru, buat backup dan hentikan penulisan aplikasi. Dari direktori backend dengan venv yang biasa digunakan:

```bash
.venv_backend/bin/python -m alembic upgrade head
.venv_backend/bin/python -m mysql.check_integrity
```

Head terbaru menjadi `20261123_0016`. Setelah migrasi dan audit berhasil, jalankan kembali backend, misalnya `pm2 restart meow-backend --update-env`, lalu terapkan frontend terbaru (restart proses development, atau build/deploy ulang jika memakai hosting statis). Ekspor DDL tersedia di `backend/sql/016_optional_point_expiry.sql`. Migrasi dan restart server dilakukan oleh operator, bukan otomatis oleh perubahan kode ini.

Validasi pembaruan: 496 tes backend lulus; pengujian MySQL nyata membutuhkan database kosong khusus dan dua tes symlink Windows tidak dijalankan. Seluruh 254 tes frontend lulus, lalu tiga tes komponen masa berlaku lulus setelah penambahan kasus kolom hari kosong. Tes mencakup poin game/Roulette/cashback permanen, snapshot lama, serta checkbox yang menyembunyikan dan mengembalikan jumlah hari. Empat layar yang diubah juga lolos kompilasi JSX.

### Password dan PIN untuk akun Google/Facebook

Akun yang dibuat melalui Google/Facebook wajib melengkapi password Meow Eyes dan PIN keamanan. Setelah login, akun tanpa password diarahkan ke `/setup-password`, kemudian `/setup-pin` jika PIN belum tersedia. Akun sosial lama juga mengikuti alur ini saat belum lengkap. Password/PIN yang sudah ada dipertahankan; login berikutnya langsung melanjutkan ke tujuan semula. Tujuan lokal seperti checkout atau riwayat pesanan disimpan selama proses ini.

Password baru minimal 8 karakter, maksimal 72 byte UTF-8, dan wajib dikonfirmasi. Backend menyimpan hash bcrypt pada kolom `users.password_hash` yang sudah ada. Endpoint `POST /api/auth/password/setup` hanya dapat dipakai oleh sesi aktif akun sosial yang belum mempunyai password; endpoint menolak penimpaan password. Setelah password dan PIN lengkap, customer juga bisa masuk menggunakan email dan password Meow Eyes. Password akun Google/Facebook tidak diminta.

`GET /api/auth/me` menyertakan `has_password` dan tetap dapat digunakan selama proses pengisian. API privat menolak akun sosial tanpa password/PIN; akses untuk memeriksa akun, membuat password, mengatur PIN sesudah password dibuat, dan keluar tetap tersedia. Akun email/password mengikuti alur yang sudah ada. Tidak diperlukan migrasi database baru untuk perubahan ini. Terapkan kode frontend/backend dan restart prosesnya melalui alur deployment biasa; proses server tidak dijalankan otomatis.

Validasi lokal: 500 tes backend dan 260 tes frontend lulus. Pengujian mencakup Google/Facebook dengan maupun tanpa PIN lama, penolakan akses API sebelum akun lengkap, password/konfirmasi yang tidak sesuai, pencegahan penimpaan password, login email dengan password baru, serta pengalihan ke tujuan awal sesudah pembuatan password. Satu pengujian MySQL nyata dilewati dan dua tes symlink Windows tidak dijalankan.

### Label dan panduan pengisian form

Form admin dan customer memakai label yang tetap terlihat setelah nilai diisi.
Pembaruan mencakup produk/varian, konten artikel dan CMS, banner, FAQ, staf,
Lens Index, voucher/hadiah, newsletter, kontak, pencarian/filter, resep, dan
Meowsurement. Kolom harga mencantumkan rupiah, berat mencantumkan gram, dan
tanggal banner menjelaskan penggunaan waktu lokal perangkat. Format khusus
seperti HEX, indeks lensa, SKU otomatis, dan daftar yang dipisahkan titik koma
memiliki petunjuk. Varian produk ditampilkan dalam kelompok bernomor; form
banner dan hadiah dapat digulir agar tombol simpan tetap terjangkau.

Gunakan `frontend/src/components/FormField.jsx` untuk satu input/select/textarea
baru. Berikan `label` yang menjelaskan data, `hint` bila perlu, dan satu kontrol
sebagai anak langsung. Komponen menghubungkan label dengan ID unik dan mengaitkan
petunjuk melalui `aria-describedby`. Label yang sudah ada memakai `htmlFor`/`id`
atau membungkus kontrolnya. Setiap digit PIN mempunyai nama aksesibel dan satu
legend terlihat untuk kelompok PIN. Upload tersembunyi tetap diwakili tombol
upload yang terlihat dan label yang terkait.

Jalankan pemeriksaan sumber form dari folder `frontend`:

```bash
npm run audit:forms
npm test -- --watchAll=false --runInBand
```

Audit memeriksa kontrol native di source aplikasi, termasuk cabang form/modal
yang belum dibuka. Placeholder dan `aria-label` saja tidak dianggap sebagai
pengganti label terlihat. Primitive generik di `components/ui` diperiksa pada
tempat pemakaiannya. Perubahan ini tidak memerlukan migrasi database.

Validasi: audit 369 kontrol pada 144 berkas source tanpa label yang hilang,
266 tes frontend lulus (44 suite), dan build produksi beserta app-shell offline
berhasil. Build masih menampilkan warning dependensi MediaPipe yang sudah ada
(ekspresi dependency dinamis dan source map vendor tidak tersedia).


### Translate halaman customer dengan ConveyThis

Fitur multilanguage internal sebelumnya sudah dilepas: tidak ada lagi menu
Bahasa & Terjemahan di admin, endpoint localization, kamus UI, cache penerjemah
internal, maupun pemanggilan Google Cloud Translation. Halaman sumber tetap
Bahasa Indonesia. Penerjemahan customer memakai widget JavaScript ConveyThis.

Tombol **Bahasa Indonesia** dan **English** tersedia pada header customer,
halaman login/registrasi, header Meowsurement, serta panel bahasa Virtual
Try-On mobile. Tombol English menunggu konfigurasi/widget yang valid dan baru
menjadi aktif setelah ConveyThis mengonfirmasi pergantian bahasa. Saat layanan
belum tersedia, halaman dan form tetap dapat digunakan dalam bahasa sumber.

#### Aktivasi

1. Buat akun ConveyThis dan tambahkan domain website. Pilih integrasi
   **Other (JavaScript)**, bahasa sumber **Indonesian (`id`)**, dan bahasa tujuan
   **English (`en`)**. Gunakan struktur URL **Default** untuk penerjemahan pada
   halaman yang sama. Domain yang didaftarkan harus sesuai domain akses.
2. Salin **public API key** dari bagian Install. Pada kode embed key berada
   sesudah `api_key=`. Isi di **frontend/.env**, bukan backend:

   ```dotenv
   REACT_APP_CONVEYTHIS_API_KEY=public_key_dari_conveythis
   ```

   Key ini adalah identitas widget publik, berbeda dari secret backend atau
   Client ID login Google. Jangan menempel seluruh tag script ke variabel env.
3. Di dashboard ConveyThis, gunakan teks bahasa penuh/native agar pilihan
   Indonesia dan English dikenali. Jika ingin menempatkan widget/branding
   bawaan di lokasi yang disediakan aplikasi, pilih **Position type: Custom**
   dan ID **meow-conveythis-widget** (tanpa tanda `#`). Branding vendor tetap
   mengikuti pengaturan serta paket ConveyThis.
4. Dari folder frontend, jalankan `npm run build`, lalu deploy hasil build.
   Untuk development `npm start`, hentikan dan jalankan kembali setelah mengubah
   env. Variabel `REACT_APP_*` dibaca saat build/start, bukan saat halaman dibuka.
5. Uji English lalu Bahasa Indonesia pada katalog, detail produk, checkout,
   login, dan Virtual Try-On. Tombol aktif mengikuti event pergantian bahasa
   dari widget, bukan sekadar keberhasilan mengunduh script. Pengujian langsung
   membutuhkan key dan domain yang diterima ConveyThis.

Rujukan vendor: [pemasangan JavaScript](https://www.conveythis.com/help/javascript-integration),
[posisi widget](https://www.conveythis.com/help/change-position),
dan [konfigurasi localhost](https://developers.conveythis.com/getting-started/localhost).
Untuk batas kata, bahasa, domain, dan page views, ikuti paket yang ditampilkan
pada dashboard ConveyThis; aplikasi tidak menyertakan kuota layanan tersendiri.

#### Perilaku dan deployment

SDK dimuat sekali pada halaman customer. Nilai input/select/textarea serta
blok data customer, resep, harga, dan kode produk yang ditandai
`conveythis-no-translate` dipertahankan sebagai nilai asli. Tambahkan
`data-conveythis-private` pada blok data pribadi baru. Konten publik yang
memenuhi aturan penerjemahan diproses oleh layanan eksternal ConveyThis.
Gunakan exclusion tambahan di dashboard vendor jika menambah area privat.

SDK tidak dimuat ketika membuka admin. Perpindahan antara customer dan admin
menggunakan dokumen baru agar observer widget customer tidak berjalan pada DOM
admin. Penggantian bahasa tidak memanggil ulang API cart/checkout dan tidak
mengubah harga atau data transaksi di backend.

Release penggantian ini memerlukan deploy frontend serta restart backend untuk
melepas route localization yang lama. Setelah itu, perubahan public key
ConveyThis cukup diikuti build/deploy frontend. Tidak ada migrasi schema baru.
Key kosong membuat tombol English belum aktif; tidak ada fallback ke Google
Cloud Translation. Data setting/cache lama dengan prefix `i18n.*`, jika pernah
tersimpan, tidak digunakan aplikasi ini.

### Status varian produk pada katalog

Form tambah/edit produk menampilkan jumlah varian total dan aktif. Setiap varian
memiliki checkbox **Aktif di katalog**; varian nonaktif ditandai abu-abu dan tidak
ditampilkan pada halaman customer. Centang checkbox lalu simpan untuk mengaktifkan
kembali varian tersebut. Varian baru aktif secara default. Menyimpan perubahan
produk lainnya mempertahankan status varian yang sudah dipilih.

Aktivasi ulang memakai ID/SKU yang sama dan tidak mengubah stok atau reservasi.
Varian aktif dengan stok habis tetap terlihat; pembelian mengikuti stok tersedia.
Foto utama produk disertakan bersama galeri tambahan tanpa duplikasi, sehingga
satu foto utama dan tiga foto tambahan tampil sebagai empat foto di detail produk.
Perubahan ini tidak memerlukan migrasi database.


### Alamat asal pengiriman melalui superadmin

Buka **Admin > Integrasi > Alamat Asal Pengiriman** (`/admin/integrations`).
Hanya akun `super_admin` yang dapat membaca atau menyimpan pengaturan ini;
endpoint juga menolak admin biasa, staf, dan customer.

Isi nama toko/pengirim, telepon, email opsional, pilih provinsi hingga
kelurahan/desa dari master Everpro, dan isi alamat lengkap. Kode pos mengikuti
kelurahan yang dipilih dan divalidasi ulang oleh backend. Latitude dan longitude
opsional harus diisi berpasangan untuk layanan Instant/Sameday.

Sebelum penyimpanan pertama, data pengirim dari env menjadi fallback agar toko
lama tetap beroperasi. Setelah **Simpan alamat asal**, database menjadi sumber
alamat pengirim; `EVERPRO_ORIGIN_*` dan `EVERPRO_SHIPPER_*` di env tidak lagi
menentukan alamat. Kredensial API/token, mode layanan DROP/PICKUP, dan ukuran
paket tetap merupakan konfigurasi integrasi server.

Alamat disimpan sebagai setting privat `shipping.origin`, tanpa tabel/migrasi
baru. Perubahan berlaku untuk permintaan ongkir baru tanpa restart. Penawaran
ongkir dari alamat asal berbeda ditolak saat checkout dan harus dihitung ulang.
Pesanan yang sudah dibuat serta retry booking memakai snapshot alamat asal pada
penawaran pesanannya, sehingga perubahan toko tidak mengubah pengiriman lama.

Deploy backend dan build/deploy frontend untuk memasang fitur ini; restart
backend sekali untuk memuat kode baru. Setelah itu pengeditan alamat melalui
superadmin tidak memerlukan perubahan env atau restart.


### Berat barang dan urutan checkout

Urutan checkout: Produk Pilihan → Lensa & Resep per Item → Alamat Pengiriman
→ Pengiriman (pilihan kurir/layanan) → Metode Pembayaran.
Total berat barang ditampilkan dalam gram dari backend,
termasuk kuantitas, lensa, dan Add On pada item yang dipilih. Berat untuk
permintaan ongkir ditampilkan terpisah bila berbeda karena batas minimum.
Angka berat lama disembunyikan selama perhitungan ulang agar sesuai tarif baru.
Perubahan ini tidak memerlukan migrasi database.

### Peta alamat dan pencarian titik pengantaran

Peta alamat memakai Leaflet 1.9.4 dengan tile OpenStreetMap. Peta dapat digeser
langsung, diperbesar dengan gulir mouse/cubit dua jari/tombol +/−, dan dipilih
dengan ketukan. Pin dapat diseret. Tombol Lihat titik kembali ke koordinat yang
disimpan; perubahan koordinat manual juga memusatkan peta ke titik baru.
Gunakan Lokasi Saya meminta izin lokasi browser; bila tidak tersedia, pencarian
alamat dan pemilihan manual tetap dapat digunakan. Kolom koordinat tersedia di
bagian Isi koordinat secara manual (opsional).

Isi Cari alamat atau nama tempat lalu tekan Cari, atau gunakan alamat yang
sudah diisi sebagai kata pencarian. Pilih salah satu hasil dan sesuaikan pin.
Pencarian hanya mengganti koordinat, tidak mengganti alamat lengkap maupun
provinsi/kota/kecamatan/kelurahan dari data EVERPRO. Pastikan lokasi pin sesuai
alamat pengiriman. Koordinat tetap opsional untuk layanan yang tidak memerlukannya.

Endpoint login `POST /api/shipping/map-search` meneruskan pencarian eksplisit ke
Photon dengan filter Indonesia, maksimal lima hasil. Tidak ada autocomplete atau
pengiriman otomatis alamat/nama/telepon saat formulir dibuka/diketik. Permintaan
provider menggunakan alamat pencarian yang dimasukkan pengguna. HTTP client
server dapat mencatat URL provider pada level INFO; sesuaikan kebijakan logging
produksi bila tidak ingin kata pencarian tersimpan di log.

Backend membatasi permintaan baru satu per detik per proses dan menyimpan cache
terbatas 128 pencarian selama lima menit. Kegagalan provider tidak menghalangi
penggunaan peta/manual. `MAP_GEOCODING_URL` bersifat opsional, default
`https://photon.komoot.io/api/`, tanpa API key. Server demo publik Photon
ditujukan untuk penggunaan wajar dan tidak menjamin ketersediaan. Untuk trafik
besar, gunakan endpoint Photon yang sesuai kapasitas dan ketentuan penyedia;
rate limit per proses bukan kuota global untuk beberapa worker. Tile OSM juga
mengikuti [kebijakan penyedia tile](https://operations.osmfoundation.org/policies/tiles/).
Lihat [dokumentasi Photon](https://github.com/komoot/photon) dan
[Leaflet](https://leafletjs.com/reference-1.9.4.html).

Pemasangan: jalankan `npm ci` di frontend, build/deploy frontend, dan restart
backend untuk memuat endpoint baru. Tidak ada migrasi database atau kredensial
peta baru yang wajib diisi. Pengaturan ini tidak mengubah sumber data wilayah
dan bearer token EVERPRO.

### Popup promo setiap kunjungan halaman beranda

Terdapat dua menu terpisah di Admin → Konten CMS:

- **Management Banner** (`/admin/banners`) untuk slider/posisi banner biasa.
- **Management Banner Popup** (`/admin/popup-banners`) untuk popup promosi.

Daftar memakai tabel dengan thumbnail kecil desktop/mobile. Tambah dan edit
tetap menyediakan upload, galeri, gambar desktop/mobile, URL tujuan, periode
tayang, perangkat, urutan, dan status aktif. Popup dibuat pada halaman khusus
dan tidak tercampur dengan daftar banner biasa. Filter API diterapkan sebelum
batas jumlah baris agar daftar popup/normal tidak saling menggeser.

Popup hanya muncul ketika halaman beranda `/` dibuka: kunjungan pertama,
refresh, kembali dari halaman lain, atau navigasi beranda yang membuat entry
history baru. Setelah ditutup, popup tidak terbuka berulang pada kunjungan
beranda yang sama. Tidak ada penanda sessionStorage; penanda lama
`meow_promo_popup_seen_v1` diabaikan tanpa perlu menghapus storage akun.

Gambar dimuat sebelum popup dibuka. Gambar mobile digunakan sampai lebar 767 px
dan fallback ke desktop bila kosong/gagal dimuat. Jika ada beberapa popup aktif,
urutan terkecil diprioritaskan, kemudian ID; gambar gagal dilanjutkan ke kandidat
berikutnya. API gagal tidak menghambat beranda. Popup dapat ditutup dengan X,
Escape, atau area luar. Klik banner membuka URL tujuan yang diatur admin.

Halaman selain beranda tidak meminta atau menampilkan popup. Status aktif,
periode, dan perangkat tetap difilter backend. Data banner/tabel tetap sama;
API admin GET `/api/admin/banners-v2` menerima `position=popup` atau
`exclude_position=popup`. Tidak ada migrasi database.

### CRUD Kategori Pilihan Beranda dan gambar latar card

Buka **Admin → Konten CMS → Kategori Pilihan Beranda**
(`/admin/home-categories`). Menu ini mengelola card pada bagian Kategori Pilihan
di beranda. Empat card awal mengikuti konfigurasi lama: Frame, Lensa, Paket
Hemat, dan Leinz Series. Semua dapat diedit atau dihapus melalui halaman ini.

- **Tambah Card**: isi judul, keterangan singkat bila perlu, dan tautan tujuan.
  Tautan dapat berupa path internal seperti `/shop-now?product_type=frame`,
  `/category/nama-kategori`, atau URL HTTP/HTTPS eksternal. Pastikan tautan
  kategori/brand sesuai data katalog toko. URL eksternal dibuka di tab baru.
- **Gambar latar**: unggah dari komputer atau pilih dari galeri melalui picker
  gambar yang sudah digunakan di admin. Gambar bersifat opsional dan mengisi
  card dengan `object-fit: cover`, sehingga tepinya dapat terpotong mengikuti
  ukuran layar. Lapisan gelap membantu keterbacaan judul/keterangan. Bila tidak
  diisi atau gambar gagal dimuat, card menggunakan warna tema dan ikon.
- **Ikon, warna tema, urutan, status**: pilih ikon dan tema, isi urutan 0–9999,
  lalu centang Tampilkan card di beranda. Card aktif ditampilkan menurut urutan
  terkecil, dengan ID sebagai pembanding bila urutannya sama. Maksimal 50 card.
- **Edit/Hapus** tersedia per card. Hapus meminta konfirmasi. Penghapusan card
  hanya menghapus konfigurasi card beranda, bukan master kategori atau produk
  yang dituju. Jika seluruh card dihapus/dinonaktifkan, bagian Kategori Pilihan
  disembunyikan dan card awal tidak dimunculkan ulang.

Pratinjau di form dan daftar admin memakai komponen card yang sama dengan
beranda. Perubahan muncul pada kunjungan/muat ulang beranda berikutnya. Staff
memerlukan permission `setting.view` untuk melihat dan `setting.update` untuk
menambah/mengubah/menghapus. Admin/superadmin memakai aturan akses yang sudah ada.

Data disimpan sebagai koleksi kecil ber-versi pada setting privat
`homepage.category_cards` menggunakan tabel `settings` yang sudah ada. Read
awal menyediakan empat card default; perubahan pertama menyimpan koleksi itu
beserta hasil edit. Snapshot versi dicek saat mutasi untuk mencegah formulir
lama menimpa konfigurasi yang sudah disimpan admin lain. Bila terjadi konflik,
tutup form dan muat ulang sebelum mengedit lagi.

Endpoint admin: `GET/POST /api/admin/home-categories`,
`PUT /api/admin/home-categories/{id}`, dan
`DELETE /api/admin/home-categories/{id}?version=...`. Field publik
`home_categories` pada `GET /api/homepage` hanya berisi card aktif, tanpa versi
setting privat. Judul, panjang teks, ikon, tema, urutan, dan URL divalidasi oleh
backend. Deploy backend terlebih dahulu, restart backend untuk memuat endpoint
baru, kemudian build/deploy frontend. Tidak perlu migrasi database atau
dependency baru.

### Manage Menu pelanggan dan URL Kategori Pilihan

Buka **Admin → Konten CMS → Manage Menu** (`/admin/menus`). Pilih lokasi
**Menu Utama**, **Footer Eksplorasi**, atau **Menu Bawah Mobile**, lalu klik
Tambah Menu. Isi nama, URL tujuan, ikon, urutan, pilihan buka di tab baru, dan
status aktif. Edit dan Hapus tersedia pada tiap baris; penghapusan meminta
konfirmasi. Item dapat dipindahkan ke lokasi lain melalui form edit. Angka urutan
terkecil tampil lebih dahulu pada lokasi yang sama. Maksimal 100 item seluruh
lokasi; menu mobile yang panjang dapat digeser secara horizontal.

Pemilih halaman cepat dapat mengisi URL halaman website atau halaman CMS yang
sudah dipublikasikan. URL juga dapat diketik manual, misalnya `/shop-now`,
`/pages/panduan-belanja`, atau URL lengkap HTTP/HTTPS. URL seperti `javascript:`
dan `//domain` ditolak backend. Meowsurement menggunakan navigasi dokumen penuh
agar aplikasi pengukurannya terbuka dengan benar. URL `/meowsurement/` berlaku
juga ketika dipasang pada card Kategori Pilihan.

Menu lama menjadi data awal yang bisa diedit. Menu aktif dimuat oleh layout
pelanggan untuk tiga lokasi tersebut; menu nonaktif disembunyikan. Semua item
dapat dihapus atau dinonaktifkan untuk menyembunyikan suatu lokasi, tanpa
memunculkan ulang item default. Footer **Bantuan** tetap menampilkan tautan CMS
terbit secara otomatis. Navigasi admin dan aturan aksesnya tetap dikelola oleh
kode aplikasi. Badge jumlah keranjang dan tujuan Masuk pada item Profil mobile
bawaan tetap tersedia.

Frontend memuat satu koleksi melalui `GET /api/menus`, memperbaruinya saat tab
kembali aktif, dan menjaga daftar terakhir jika pembaruan gagal. Bila pemuatan
awal API gagal, navigasi awal menjadi fallback agar website tetap dapat
dinavigasi. Fallback hanya berlaku untuk kegagalan API, bukan respons kosong
yang sengaja dikonfigurasi admin.

API admin: `GET/POST /api/admin/menus`, `PUT /api/admin/menus/{id}`, dan
`DELETE /api/admin/menus/{id}?version=...`. Staff membutuhkan `setting.view`
untuk membaca dan `setting.update` untuk mutasi. Data disimpan pada setting
privat `storefront.menus`. Penyimpanan koleksi versi bersama juga dipakai oleh
Kategori Pilihan agar formulir lama tidak menimpa perubahan admin lain. Konflik
versi meminta admin menutup form dan memuat ulang.

Pada **Kategori Pilihan Beranda**, kolom **URL tujuan card** mengatur tujuan
klik card di beranda. URL dapat diedit pada tambah/edit dan diuji menggunakan
tautan **Uji URL tujuan** di daftar card. Path internal dibuka di website;
URL eksternal dibuka di tab baru. Gambar latar, ikon, dan pengaturan card lain
tetap tersedia.

Deploy backend dan restart untuk memuat endpoint baru, kemudian build/deploy
frontend. Tidak diperlukan migrasi database atau dependency tambahan.

### Banner slider desktop/mobile tanpa crop

Pada **Admin → Banner** (`/admin/banners`), tambah atau edit banner dengan
**Lokasi banner: Hero**. Unggah **Banner desktop (wajib)** dan **Banner versi
mobile (opsional)** melalui picker gambar. Kedua kolom mendukung upload dari
komputer, galeri, atau URL gambar. Pratinjau di bawah kolom menampilkan kedua
versi secara utuh. Pilih **All Device** untuk menggunakan satu banner dengan
dua gambar pada desktop/mobile, kemudian simpan.

Di beranda, elemen `picture` memilih gambar mobile pada layar maksimal 767 px.
Permintaan daftar banner juga menyertakan perangkat berdasarkan lebar layar
saat beranda dimuat, sehingga pengaturan All Device/Desktop/Mobile pada admin
diterapkan oleh API.
Jika gambar mobile kosong, gambar desktop digunakan. Gambar tampil selebar area
banner (`width: 100%`) dengan tinggi mengikuti rasio asli (`height: auto`), tanpa
`object-fit: cover` atau pemaksaan tinggi slider. Banner landscape dan portrait
dapat memiliki tinggi yang berbeda; gunakan rasio konsisten antar-slide pada
masing-masing versi bila ingin pergantian tinggi lebih stabil.

Judul dan tombol tujuan berada di bawah gambar. Tombol navigasi, indikator
slide, dan kontrol autoplay juga berada di luar gambar agar tidak menutupi
materi promo. Hanya slide aktif yang menentukan tinggi slider; slide lain
disembunyikan dari pembaca layar dan fokus keyboard. Banner dengan jenis tautan
None tidak diberi tautan/tombol tujuan. Tampilan awal tanpa banner tetap tersedia.

Field database/API `image_mobile` sudah tersedia; tidak perlu migrasi database
atau perubahan konfigurasi backend. Build/deploy frontend untuk memasang
pembaruan tampilan dan form admin ini.

### Pilihan ikon Lucide dengan pencarian dan pratinjau

Form **Manage Menu** dan **Kategori Pilihan Beranda** memakai pemilih ikon
bersama. Klik **Pilih ikon**, cari nama atau istilah Indonesia seperti kamera,
kacamata, belanja, hati, paket, atau bintang, lalu klik ikon. Nama dan pratinjau
ikon terpilih ditampilkan langsung. Pilihan **Tanpa ikon** tersedia. Koleksi
Lucide 0.516.0 berisi 1.602 ikon, ditampilkan maksimal 48 per halaman agar form
tetap ringan. Pencarian dilakukan lokal tanpa mengirim kueri ke layanan luar.

Ikon lama tetap didukung. Pilihan baru disimpan sebagai `lucide:nama-ikon` dan
divalidasi terhadap daftar nama yang tersedia di backend. SVG/HTML dari input
pengguna tidak diterima. Renderer yang sama digunakan pada menu pelanggan,
preview admin, dan card beranda, sehingga ikon pilihan tampil setelah disimpan.
Koleksi SVG dimuat sebagai chunk lokal saat diperlukan; menu/ikon lama tidak
perlu memuat seluruh koleksi pada kunjungan awal.

Sumber merupakan package `lucide-react` yang sudah terpasang, tanpa dependency
atau API key tambahan. Data/daftar izin yang dihasilkan disimpan pada
`frontend/src/lib/iconCatalog.json` dan
`backend/mysql/data/lucide-icon-names.json`; keduanya harus ikut deploy.
Informasi versi/lisensi Lucide disertakan dalam katalog. Jika versi package
Lucide diperbarui, jalankan `npm run generate:icons` di frontend lalu commit
kedua file hasilnya, tes, dan build kembali.

Deploy backend dan restart untuk memuat daftar izin ikon baru/filter banner,
kemudian build/deploy frontend. Tidak perlu menjalankan migrasi database.
Tombol translate yang sedang dinonaktifkan tetap tersembunyi; ekspor komponen
kosong menjaga kompatibilitas import layout.
