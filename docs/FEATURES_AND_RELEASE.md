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

| Tahap | Hasil implementasi | Lokasi utama |
| --- | --- | --- |
| 3. Checkout dan rating | Resep per item frame+lensa: SPH, CYL, AXIS, ADD untuk OD/OS, PD total atau kanan/kiri, catatan, dan foto privat. Snapshot resep disimpan pada pesanan. Rating produk/lensa dan transaksi tersedia sesudah pembayaran terkonfirmasi. | `/checkout`, `/payment/:orderNumber`, `/orders/:id` |
| 4. Flash Sale | Keanggotaan kampanye aktif menjadi sumber daftar dan harga promo. Pembuatan berdasarkan kategori, pilihan subkategori, persentase/potongan/harga tetap, kuota, jadwal, serta produk manual. | `/flash-sale`, `/admin/flash-sales` |
| 5. Storefront | Pagination 15 item, filter dan halaman pada URL, breadcrumb detail, menu New Arrival, kategori Frame New Arrival, tombol WhatsApp global, tombol berbagi serta Copy Link. | `/shop-now`, `/products`, `/new-arrival`, artikel dan Product Knowledge |
| 6. CMS | Publish/Unpublish, urutan dan URL banner, nomor/pesan WhatsApp, pengelolaan aset try-on, penambahan konten knowledge idempoten. | `/admin/articles`, `/admin/knowledge`, `/admin/banners`, `/admin/whatsapp`, `/admin/try-on` |
| 7. Virtual Try-On | Pratinjau menggunakan kamera yang diizinkan pelanggan atau foto lokal, aset gambar transparan maupun GLB/GLTF, pengaturan posisi/skala/rotasi, serta penanganan perangkat yang tidak mendukung kamera/WebGL. | Halaman detail frame dengan aset published |
| 8. DOKU | Hosted Checkout, penandatanganan request, verifikasi notifikasi, pemeriksaan nilai/identitas pesanan, proses ulang idempoten dan rekonsiliasi status. | Backend integrasi, halaman pembayaran, `/admin/integrations` |
| 9. Everpro | Tarif dari API, quote tersimpan dan dibatasi masa berlaku, booking sesudah dibayar, pilihan DROP/PICKUP, resi, pelacakan, callback terverifikasi dan pembaruan status. | Checkout, admin detail pesanan, `/admin/integrations` |

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
cocok dimaterialisasi saat kampanye dibuat. Tombol **Tambahkan produk kategori
terbaru** memasukkan produk baru yang memenuhi aturan tanpa mereset harga,
kuota terjual, atau reservasi produk yang sudah tercatat. Aturan kategori
kampanye yang sudah dibuat tetap dipertahankan; gunakan kampanye baru untuk
mengganti aturan tersebut. Harga, kuota, keaktifan item dan metadata kampanye
dapat dikelola tanpa mengganti identitas item.

Kuota yang sedang direservasi tidak boleh ditimpa atau diturunkan melewati
jumlah terjual dan dipesan. Jadwal di form menggunakan waktu lokal perangkat
admin; API dan database menyimpan waktu UTC. Kampanye yang dinonaktifkan admin
tidak otomatis diaktifkan ulang oleh scheduler.

### Konten, banner, dan New Arrival

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

Migrasi head tetap `20261106_0002`; tabel fitur telah disiapkan pada fondasi
sebelumnya. Kedua revisi historis tidak diubah. Pengujian nyata terhadap MySQL
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

Admin memilih produk frame, varian opsional, sumber gambar publik transparan
atau URL model GLB/GLTF, preview, urutan, dan status. Aset published tersedia pada
halaman produk. Gunakan sumber HTTPS/CORS yang dapat diakses browser. Model
GLTF dengan tekstur/buffer eksternal memerlukan sumber dependensi yang valid;
GLB dengan aset tertanam lebih mudah dikelola.

Pratinjau kamera/foto menggunakan penyesuaian manual. Ini tidak mengklaim
pelacakan landmark wajah otomatis atau pengukuran ukuran fisik yang presisi.
Foto lokal tidak dikirim ke server oleh antarmuka try-on. Kamera hanya dibuka
setelah tindakan pelanggan dan stream dihentikan ketika tampilan ditutup.

Skala awal adalah pengali lebar frame, offset X/Y berupa proporsi area preview,
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
