> Arsip implementasi vault lokal sebelumnya. Dokumen ini tidak menjadi petunjuk alur customer saat ini. Gunakan [dokumentasi aktif](../README.md).

# Meowsurement — pemasangan dan operasi

Panduan ini mengikuti implementasi React yang ada pada `frontend/src/optifit/`.
Route aplikasi adalah **`/meowsurement/`**. Data pasien, resep, sesi, revisi,
review dan foto disimpan dalam vault IndexedDB terenkripsi pada browser yang
dipakai. Backend toko tetap FastAPI dengan target **Oracle MySQL 5.7.24-log**.
Penambahan modul lokal ini tidak menerapkan migrasi baru pada server MySQL.

Baca [SECURITY.md](SECURITY.md) untuk batas keamanan lokal,
[MEASUREMENTS.md](MEASUREMENTS.md) untuk metode yang tersedia, serta
[FIELD_VALIDATION_PROTOCOL.md](FIELD_VALIDATION_PROTOCOL.md) sebelum menggunakan
hasil kamera untuk keputusan fitting. Panduan pemasangan tidak membuktikan
akurasi klinis atau kompatibilitas semua perangkat.

## 1. Prasyarat

- Node.js dan npm sesuai `frontend/package.json`: Node `>=20 <25`, npm `>=10`.
  Gunakan versi yang konsisten pada development dan build, serta lockfile npm
  yang disertakan. Jangan mengganti dependensi saat menyiapkan deployment ini.
- Akses jaringan untuk `npm ci`, pengambilan dependensi, dan pemasangan pertama
  aset aplikasi. Sesudah aset siap, proses inti OptiFit dapat berjalan lokal.
- Browser yang mengizinkan WebCrypto dan IndexedDB. Kamera dan service worker
  memerlukan **HTTPS atau localhost**. HTTP pada alamat IP LAN ponsel tidak
  sama dengan localhost pada ponsel; gunakan origin HTTPS yang dipercaya.
- Perangkat/browser profile khusus yang dikelola organisasi, kapasitas lokal
  memadai, dan tempat backup terenkripsi yang berwenang. Jangan memakai mode
  incognito/private sebagai penyimpanan operasional yang harus bertahan.

Alamat origin mencakup skema, host dan port. `localhost`, `127.0.0.1`, port
development, subdomain produksi dan browser profile lain mempunyai ruang
penyimpanan berbeda. Vault yang tidak terlihat pada origin baru tidak berarti
data pada origin lama telah dipindahkan atau terhapus.

## 2. Menjalankan development

Dari root proyek:

```bash
cd frontend
npm ci
npm start
```

Buka `http://localhost:3000/meowsurement/`, atau port yang dilaporkan dev server
bila konfigurasi lokal mengubahnya. Tidak ada backend yang diperlukan untuk
membuat vault, memasukkan pasien/resep secara lokal, anotasi, perhitungan,
review, backup atau laporan.

Jika akan memakai impor profil/katalog toko, siapkan `frontend/.env` dari
`.env.example` **hanya bila belum mempunyai konfigurasi lokal**. Contoh yang
disertakan memakai `REACT_APP_BACKEND_URL=http://localhost:8001`. Jalankan
backend toko dengan konfigurasi MySQL yang sudah ditetapkan dalam
[panduan rilis toko](../FEATURES_AND_RELEASE.md). Menjalankan OptiFit lokal saja
tidak memerlukan perintah Alembic, seed, perubahan akun DB, atau impor MongoDB.

Service worker produksi sengaja tidak didaftarkan oleh development build.
Status “cache offline belum siap” pada `npm start` adalah perilaku yang
diharapkan. Gunakan production build untuk menguji offline, bukan menyimpulkan
kegagalan dari dev server.

Untuk memeriksa modul setelah perubahan kode:

```bash
CI=true npm test -- --watchAll=false --runInBand src/optifit
```

Perintah tersebut merupakan pengujian software. Pengujian kamera fisik,
ketepatan pengukuran dan studi manusia mengikuti protokol terpisah.

## 3. Membuat production build

Tetapkan konfigurasi frontend sebelum build. `REACT_APP_BACKEND_URL` kosong
menggunakan API pada origin yang sama; nilai berupa origin backend menggunakan
alamat tersebut untuk tindakan impor yang eksplisit. Nilai `REACT_APP_*` masuk
ke bundle publik: jangan menaruh password MySQL, rahasia DOKU/Everpro, passphrase
vault, token pribadi atau kunci enkripsi di sana.

Dari `frontend/`:

```bash
npm ci
npm run build
```

Script build menjalankan `craco build`, lalu
`node scripts/build-optifit-offline.cjs`. Generator memeriksa aset yang
diperlukan, membuat daftar aset dari build, serta menulis service worker dengan
versi hash konten ke **`build/meowsurement/sw.js`**. Kegagalan generator membuat
build gagal; jangan menerbitkan build parsial.

Artefak yang harus ikut dihosting:

- Seluruh `frontend/build/`, termasuk `index.html`, `/static/` dan chunk dinamis.
- `/logo-meow.jpg`.
- `/meowsurement/manifest.webmanifest`.
- `/meowsurement/sw.js` hasil generator.
- `/meowsurement/fonts/DejaVuSans.ttf` dan `DejaVuSans-Bold.ttf` untuk PDF lokal.

Deploy struktur build pada **root origin**, karena URL aset dan scope pada kode
bersifat root-relative. Menaruh semuanya di `/tools/` atau mengganti path
`/meowsurement/` tanpa menyesuaikan kode/generator bukan deployment yang didukung
oleh konfigurasi saat ini. Gunakan release directory atomik atau mekanisme
setara agar HTML, manifest aset, chunk dan service worker berasal dari build
yang sama. Pertahankan aset hash versi sebelumnya selama masih diperlukan oleh
tab lama; jangan menghapus storage browser sebagai cara melakukan upgrade.

## 4. Kontrak hosting, MIME dan route SPA

Konfigurasikan web server/reverse proxy dengan aturan berikut. Ini kontrak
deployment yang harus diterapkan pada hosting yang dipilih, bukan konfigurasi
server yang telah diterapkan oleh pekerjaan ini.

| URL/jenis request | Respons yang diperlukan | Kebijakan cache yang disarankan |
| --- | --- | --- |
| `/meowsurement` | Redirect ke `/meowsurement/` atau HTML entry yang benar | Jangan cache redirect secara tidak terkendali saat konfigurasi berubah |
| `/meowsurement/` | `index.html`, status 200, `text/html` | `no-cache` agar pemasangan/pembaruan mengambil entry yang sesuai |
| Route navigasi OptiFit di bawah `/meowsurement/` | Fallback SPA ke `index.html` | HTML revalidated; bukan respons API atau data pasien |
| `/meowsurement/sw.js` | Berkas JS aktual, status 200, MIME JavaScript, tanpa redirect | `Cache-Control: no-cache, max-age=0, must-revalidate` |
| `/meowsurement/manifest.webmanifest` | JSON manifest aktual, `application/manifest+json` | Revalidate untuk pembaruan metadata |
| `/static/...js` dan `/static/...css` | Berkas aktual dengan MIME JavaScript/`text/css` | Aset bernama hash dapat memakai cache panjang/immutable |
| Font TTF, logo dan aset tetap lainnya | Berkas aktual dengan MIME yang sesuai, misalnya `font/ttf` dan `image/jpeg` | Revalidate atau versi sesuai kebijakan rilis |
| Aset statis yang tidak ada | 404, bukan `index.html` yang dikembalikan sebagai sukses | Hindari menyimpan fallback HTML sebagai script/font |
| `/api/...` | Proxy ke backend yang ditetapkan; tanpa fallback SPA | API tidak dimasukkan ke cache service worker OptiFit |

**Periksa route `/meowsurement/` secara eksplisit.** Direktori tersebut memang
ada untuk manifest/font/service worker, tetapi tidak memiliki entry HTML sendiri
pada source. Static server generik yang hanya menampilkan direktori atau mencari
`meowsurement/index.html` dapat menghasilkan directory listing/403. Server harus
mengembalikan root `index.html` untuk entry aplikasi. Service worker dipasang
dengan scope `/meowsurement/`; jangan memperluasnya ke root toko.

Pemasangan worker mengambil aset tanpa credential dan menolak redirect. Jika
hosting menambahkan login gateway di depan aset, sesuaikan arsitektur akses
secara sadar: halaman login HTML, redirect atau aset yang hanya bisa diambil
dengan cookie tidak memenuhi kontrak generator saat ini. Clinical data tetap
berada dalam vault; menyediakan shell statis tidak menyediakan isi vault.

Atur HTTPS dan MIME dengan benar sebelum mengaktifkan `nosniff`. Gunakan
`Referrer-Policy: no-referrer` pada ruang kerja privat. Tinjau CSP dan
Permissions Policy terhadap kamera lokal, object URL gambar privat, font PDF,
dynamic chunks, serta iframe cetak yang benar-benar digunakan. Uji kebijakan
hosting tersebut pada perangkat sasaran; jangan menerbitkan policy yang
memblokir fungsi lalu menonaktifkan enkripsi atau permission checks untuk
mengatasinya. Hindari injeksi analytics, chat widget, tag manager dan skrip
pihak ketiga pada halaman privat.

### Batas origin

Entry OptiFit tidak memasang komponen storefront, WhatsApp atau permintaan
storefront otomatis. **Pemisahan route bukan pemisahan origin keamanan.** Skrip
lain pada origin yang sama masih berada dalam batas kepercayaan browser yang
sama. Untuk isolasi lebih kuat, gunakan origin/subdomain khusus yang dikelola,
tanpa skrip toko yang tidak diperlukan, dan tetap host aplikasi pada
`/meowsurement/` dengan aset root-relative yang diperlukan.

Origin khusus tidak mempunyai token login toko dari origin lama. Impor profil
pelanggan saat ini memakai token toko pada localStorage origin yang sama;
fitur itu tidak otomatis bekerja lintas origin. Jangan menyalin token manual
ke browser sebagai prosedur instalasi. Gunakan modul lokal tanpa impor profil
atau siapkan integrasi autentikasi lintas origin yang ditinjau tersendiri.
Katalog publik dapat memakai endpoint backend yang dikonfigurasi bila CORS
mengizinkan origin tersebut. Perpindahan origin juga memerlukan backup/restore
yang disengaja untuk memindahkan vault.

## 5. Pemasangan pertama dan verifikasi offline

1. Buka production URL melalui HTTPS dalam browser profile yang akan dipakai.
   Tunggu halaman selesai dimuat dan status **“aplikasi siap offline”**. Alur
   registrasi mempunyai timeout; jika belum siap, tetap online dan muat ulang.
2. Pada browser developer tools, periksa worker aktif dengan scope
   `/meowsurement/` serta tidak adanya 404, redirect aset, MIME JS/CSS yang salah
   atau font PDF yang hilang. Nama cache shell diawali `optifit-shell-`.
3. Buka **Pengaturan → Penyimpanan perangkat → Minta penyimpanan persisten**.
   Browser dapat menolak permintaan. Persistensi bukan pengganti backup.
4. Dengan data uji yang jelas bukan pasien nyata, putuskan jaringan lalu muat
   ulang `/meowsurement/`. Buka vault dengan akun lokal, buka sesi tersimpan,
   buat revisi dan uji laporan PDF. Pastikan informasi pasien tidak berubah
   menjadi data contoh ketika offline.
5. Periksa bahwa tindakan impor profil/katalog memberi pesan memerlukan koneksi.
   Tidak ada antrean sinkronisasi data klinis yang akan dikirim diam-diam saat
   jaringan kembali.
6. Uji close/reopen browser pada origin yang sama, lalu buka vault lagi. Uji
   backup/restore di profile uji terpisah sebelum mempercayakan data operasional.

Worker hanya menyimpan app shell dan daftar aset statis hasil build. Ia tidak
mencache API, request non-GET, URL dengan query, respons lintas origin, atau
foto pasien. Penghapusan cache shell dan penghapusan IndexedDB adalah operasi
berbeda; tombol browser “clear site data” bisa menghapus keduanya. Jangan
menggunakannya sebagai langkah pemecahan masalah sebelum backup teruji tersedia.

Pembaruan service worker menunggu tab lama ditutup; kode tidak memaksa reload
ketika pasien terbuka. Setelah rilis baru: simpan revisi, buat backup sesuai
prosedur, kunci vault, tutup semua tab/PWA OptiFit, lalu buka kembali saat online.
Periksa kesiapan offline lagi. Cache shell versi lama dibersihkan saat aktivasi;
data vault tidak dihapus oleh generator atau worker.

## 6. Bootstrap administrator dan pemisahan review

Pada browser/origin yang belum mempunyai vault, layar **Siapkan ruang kerja**
meminta nama organisasi, nama administrator, username dan kredensial. Tidak ada
akun atau password bawaan. Gunakan frasa sandi kuat minimal 12 karakter. Kode
juga menerima PIN 10–32 digit dengan penolakan pola sederhana, tetapi PIN
memiliki ruang tebakan lebih kecil. Spasi awal/akhir tidak diterima.

Sesudah administrator masuk, buka **Pengaturan → Pengguna lokal** dan buat akun
operator serta **Viewer / Reviewer** yang terpisah. Operator bekerja pada pasien
yang menjadi kewenangannya; reviewer membaca dan membuat keputusan, tanpa
menimpa data mentah. Reviewer harus berbeda dari operator/pembuat revisi yang
dinilai. Mengganti peran pada orang yang sama bukan pemisahan reviewer.

Alur operasional: identitas pasien → resep dari pemeriksaan profesional → data
frame → lingkup/mode pengukuran → persiapan dan consent → pengambilan/anotasi
atau pembacaan alat manual → hasil → pengajuan review → keputusan reviewer →
ekspor laporan. Semua koreksi menambah revisi beserta alasan. Persetujuan suatu
revisi tidak otomatis berlaku pada revisi berikutnya.

Kamera memerlukan consent dan checklist yang tersimpan. Mode Manual tidak
menawarkan pencarian kandidat pupil; Semi-otomatis menyediakan kandidat lokal
yang wajib diperiksa. Mode otomatis penuh tidak diaktifkan dengan hasil palsu.
Kualitas rendah memblokir persetujuan final. Kamera membutuhkan minimal tiga
foto berbeda yang ditelusuri, pengulangan valid dan verifikasi referensi sesuai
workflow. Review tetap pekerjaan petugas yang kompeten.

## 7. Kredensial, backup dan pemulihan

Vault mengunci saat tab disembunyikan/pagehide serta setelah idle timeout;
default lima menit, pengaturan admin 1–30 menit. Selesaikan dan simpan perubahan
sebelum berpindah aplikasi. Lock membersihkan tampilan/kamera, tetapi browser
tidak menjamin pemblokiran screenshot sistem operasi atau semua salinan memori.

Administrator membuat **cadangan terenkripsi** melalui Pengaturan. Gunakan
frasa sandi cadangan nonnumerik minimal 12 karakter, berbeda dari penyimpanan
file cadangannya. Backup berisi seluruh workspace dan foto yang tersimpan,
dengan batas MVP 192 MiB. Catat tanggal, origin, perangkat dan pemilik backup
dalam prosedur organisasi, tanpa menaruh passphrase pada nama file.

Untuk restore ke browser/origin kosong, pilih **Pulihkan cadangan terenkripsi**
pada layar awal, pilih file dan masukkan frasa sandi backup. Untuk mengganti
vault yang sudah berisi data, administrator harus membuka vault, membuat backup
kondisi sekarang bila diperlukan, lalu mengonfirmasi teks **`GANTI VAULT`**.
Restore memvalidasi isi sebelum mengganti data; setelah selesai vault terkunci
dan pengguna masuk memakai kredensial akun yang terdapat di backup.

**Tidak tersedia pemulihan password melalui email/server atau master password
bawaan.** Frasa sandi backup tidak menjadi pengganti kredensial login lokal
setelah restore pada UI ini. Administrator yang masih dapat masuk dapat
mengelola kredensial pengguna, tetapi bila seluruh akses admin hilang jangan
menghapus atau mengedit ciphertext untuk mencoba membuka data. Amankan backup
dan ikuti prosedur pemulihan organisasi. File tanpa rahasia yang diperlukan
tidak dapat dipulihkan otomatis oleh aplikasi.

Uji restore berkala pada profile terpisah. Membuka JSON backup di editor hanya
memeriksa file envelope, bukan membuktikan data berhasil dipulihkan. Laporan
PDF/CSV/JSON yang diekspor berbeda dari backup: laporan dapat berisi data pasien
terbaca dan harus disimpan/dikirim oleh pihak yang berwenang. Thumbnail laporan
mati secara default dan memerlukan consent serta konfirmasi khusus.

Default retensi foto adalah 30 hari; admin dapat menetapkan 1–3650 hari untuk
foto baru. Tanggal kedaluwarsa yang telah tercatat tetap melekat pada foto lama.
Retensi diperiksa saat vault dibuka, bukan sebagai tugas ketika browser mati.
Penghapusan lokal tidak menghapus backup atau laporan yang sebelumnya diekspor.

## 8. Integrasi toko dan batas database

Adapter `integration.js` hanya dipanggil melalui tindakan impor yang
dikonfirmasi:

| Tindakan | Akses yang dilakukan | Batasnya |
| --- | --- | --- |
| Ambil profil Meow Eyes | `GET /api/auth/me` dengan Bearer token login toko pada origin yang sama | Read-only; bukan login ke vault dan tidak memindahkan seluruh data akun |
| Ambil katalog frame | `GET /api/products?product_type=frame...` | Identitas produk; dimensi tetap harus diukur/dikonfirmasi petugas |
| Simpan pasien, resep, foto, hasil dan revisi | Vault lokal terenkripsi | Tidak memanggil endpoint sinkronisasi klinis |

Request impor memakai `cache: no-store`, credential cookie tidak disertakan,
dan mempunyai timeout. Mode lokal tetap tersedia saat backend tidak aktif.
Pembacaan katalog atau foto komersial produk tidak membuktikan ukuran fisik
kalibrasi. Tidak ada upload otomatis gambar, resep, laporan atau training data.

Konfigurasi backend berada dalam `backend/.env.mysql`, mengikuti contoh
`.env.mysql.example`, termasuk kredensial DB dan provider yang tetap berada di
server. Target kompatibilitas server tetap MySQL 5.7.24-log. Skema server untuk
sinkronisasi klinis merupakan pengembangan terpisah; pekerjaan OptiFit ini
tidak menjalankan DDL, mengimpor pasien ke MySQL, atau mengaktifkan sync default.

## 9. Validasi perangkat sebelum penggunaan

Lakukan matriks pada [FIELD_VALIDATION_PROTOCOL.md](FIELD_VALIDATION_PROTOCOL.md)
dengan versi build, ponsel, OS, browser, kamera/lensa, orientasi dan konfigurasi
hosting yang sebenarnya. Uji front/back camera dan mirror, label OD/OS, ukuran
foto asli, izin ditolak, kamera terganggu, rotasi, lock saat capture, cahaya,
refleksi, rimless/frame mengilap, pupil tertutup, serta kapasitas/restore lokal.

Periksa skala fisik dan bidang marker; tanpa kalibrasi yang valid jangan
menampilkan mm. Verifikasi target jauh versus near dan jarak kerja, permukaan
belakang lensa pada VD, referensi vertikal/head pitch pada panto. Wrap saat ini
dicatat dari alat/metode manual. Jangan mengaktifkan depth/head-pose/rekonstruksi
3D melalui penggantian label atau angka default.

Toleransi, besar sampel dan penerimaan klinis ditetapkan petugas berwenang lewat
protokol sebelum studi, bukan dari angka unit test. Jika kondisi tidak sesuai,
gunakan pengukuran alat/manual dan review. Skor kualitas adalah bukti teknik;
ketidakpastian tetap “Tidak tersedia” sampai anggarannya benar-benar divalidasi.

## 10. Pemecahan masalah tanpa menghilangkan data

| Gejala | Pemeriksaan/tindakan |
| --- | --- |
| Halaman kosong atau chunk gagal dimuat | Pastikan seluruh build dipasang konsisten; periksa status/MIME JS dan fallback SPA; kembali online dan muat ulang |
| `/meowsurement/` menampilkan daftar direktori/403 | Terapkan entry SPA eksplisit ke root `index.html`; jangan mengubah path aset |
| Cache offline belum siap | Pastikan production build, HTTPS/localhost, worker/script yang benar, seluruh aset/font tersedia tanpa redirect; muat ulang online |
| Kamera tidak dapat dibuka | Periksa izin origin, secure context, kamera sedang dipakai aplikasi lain, perangkat yang dipilih; gunakan mode manual/impor privat sesuai consent |
| Vault tidak terlihat setelah pindah URL/browser | Periksa origin, port dan profile; data tidak tersinkron otomatis. Kembali ke origin lama atau restore backup secara sengaja |
| Penyimpanan penuh | Simpan backup, periksa retensi foto dan kapasitas perangkat; jangan menghapus IndexedDB sebagai langkah pertama |
| Tidak dapat login setelah restore | Gunakan akun dan kredensial asli dari backup, bukan frasa sandi envelope backup |
| PDF gagal saat offline | Pastikan font DejaVu dan chunk laporan ikut build/cache; selesaikan pemasangan online kemudian uji ulang |
| Impor profil/katalog gagal | Periksa jaringan, alamat backend, CORS, sesi toko yang masih valid untuk profil; mode lokal tidak membutuhkan impor |
| Sesi tidak dapat disetujui | Baca alasan workflow; lengkapi referensi, konteks, sampel, kualitas dan reviewer independen. Jangan mengganti status lewat DevTools |

Catat langkah reproduksi, versi build/perangkat, pesan error dan status jaringan
tanpa menyalin foto/resep pasien ke tiket teknis. Hasil deployment, browser QA
dan studi perangkat harus dilaporkan menurut bukti yang benar-benar dijalankan.
