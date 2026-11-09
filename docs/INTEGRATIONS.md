# DOKU Checkout dan Everpro — aktivasi dan operasi

Implementasi ini menggunakan backend FastAPI, tabel relasional MySQL 5.7.24-log, halaman pembayaran DOKU yang di-host oleh penyedia, serta Everpro Open API. Kredensial tidak dikirim ke React. Konfigurasi disimpan di environment backend atau `backend/.env.mysql`, mengikuti contoh `backend/.env.mysql.example`.

**Status verifikasi:** kontrak HTTP, tanda tangan, transaksi SQL, callback berulang, nominal yang tidak cocok, quote yang berubah, dan kegagalan jaringan diuji dengan transport HTTP tiruan dan basis data terisolasi. Tidak ada transaksi, booking kurir, atau callback dari akun merchant sungguhan yang dilakukan dalam workspace ini. Uji sandbox merchant dan uji MySQL aktual tetap harus dijalankan pada lingkungan yang memiliki akses tersebut.

## 1. Pilih mode secara eksplisit

Untuk layanan nyata, gunakan:

```dotenv
PAYMENT_PROVIDER=doku
SHIPPING_PROVIDER=everpro
ENABLE_MOCK_PAYMENTS=0
PUBLIC_FRONTEND_URL=https://toko.example.com
PUBLIC_API_URL=https://api.example.com
```

`PUBLIC_API_URL` adalah origin backend, tanpa `/api`. Domain contoh harus diganti dengan domain toko. Halaman React harus dapat dibuka langsung pada `/payment/{order_number}` melalui konfigurasi fallback SPA hosting.

Untuk pengujian lokal tanpa akun penyedia:

```dotenv
APP_ENV=development
ENABLE_MOCK_PAYMENTS=1
PAYMENT_PROVIDER=mock
SHIPPING_PROVIDER=mock
```

Mode mock ditolak ketika `APP_ENV=production`. Mode `disabled` juga tersedia untuk masing-masing provider. Penyedia yang kredensialnya kosong akan menolak checkout atau penghitungan ongkir dengan respons yang jelas; sistem tidak menggantinya diam-diam dengan harga atau status simulasi.

`GET /api/integrations/status` hanya mengembalikan provider, kesiapan konfigurasi, dan penanda mock. Halaman admin integrasi memakai `GET /api/admin/integrations`, yang menambahkan nama variabel konfigurasi yang belum terisi, alamat webhook, dan antrean rekonsiliasi. Kesiapan konfigurasi **bukan** hasil verifikasi kredensial melalui jaringan.

## 2. DOKU

Isi nilai berikut dari akun merchant sandbox:

| Variabel | Penggunaan |
| --- | --- |
| `DOKU_ENVIRONMENT` | `sandbox` atau `production` |
| `DOKU_CLIENT_ID` | Client ID merchant |
| `DOKU_SECRET_KEY` | Secret key backend, tidak masuk repository |
| `DOKU_PAYMENT_DUE_MINUTES` | Durasi pembayaran, default 60 menit |
| `DOKU_NOTIFICATION_PATH` | Path publik callback; default `/api/webhooks/doku` |
| `DOKU_WEBHOOK_MAX_AGE_SECONDS` | Batas umur tanda tangan, default 172800 detik untuk mengakomodasi retry |

Backend memilih endpoint resmi berdasarkan environment: `https://api-sandbox.doku.com/checkout/v1/payment` atau `https://api.doku.com/checkout/v1/payment`. Kode menghitung digest SHA-256 dari **byte JSON yang benar-benar dikirim**, lalu HMAC-SHA256 untuk header permintaan. Respons yang menyertakan header tanda tangan juga diverifikasi. Komunikasi ke endpoint penyedia selalu menggunakan HTTPS dan tidak mengikuti redirect HTTP secara otomatis.

### Aktivasi dashboard merchant

1. Daftarkan URL notifikasi `https://api.example.com/api/webhooks/doku` di dashboard DOKU. Path yang dilihat DOKU harus sama dengan `DOKU_NOTIFICATION_PATH`. Apabila reverse proxy mengubah prefix, konfigurasi variabel ini dengan path publik dan arahkan request ke route internal tersebut.
2. Aktifkan kanal pembayaran yang disetujui untuk merchant. Adapter ini mengirim tipe `SALE` dan membuka DOKU Checkout. Pengumpulan nomor kartu berlangsung di halaman penyedia.
3. Jika `PUBLIC_API_URL` tersedia, backend juga mengirim `override_notification_url` yang dibentuk dari origin tersebut dan path notifikasi.
4. Lakukan transaksi sandbox dari checkout toko. Gunakan simulator resmi DOKU, lalu pastikan callback mencapai backend melalui HTTPS. Pengalihan browser kembali ke toko hanya membuka status pesanan; pengalihan itu tidak mengubah status menjadi lunas.
5. Setelah verifikasi sandbox, gunakan kredensial production dan `DOKU_ENVIRONMENT=production`. Selesaikan atau rekonsiliasi transaksi yang masih aktif sebelum mengganti lingkungan/akun. Retry yang mendeteksi identitas akun berbeda ditolak.

### Alur pembayaran

Checkout mengunci pengguna dan stok, menghitung ulang harga/promosi, menyimpan snapshot pesanan, serta membuat satu payment intent. Transaksi basis data dikomit sebelum pemanggilan DOKU. Nilai akhir untuk DOKU dibulatkan sekali ke Rupiah utuh dengan `ROUND_HALF_UP`; preview checkout dan nilai tersimpan menggunakan angka yang sama.

`Payment.request_id`, invoice, dan body permintaan tersimpan dipakai kembali pada retry. Backend tidak membuat invoice baru saat koneksi terputus. Jika order sudah tersimpan tetapi DOKU belum mengembalikan link, respons checkout tetap berisi order, `requires_retry: true`, dan pesan `payment_error`. Halaman pembayaran dapat mencoba intent yang sama lagi. Permintaan pembuatan yang masih berjalan diberi jeda 30 detik agar tombol berulang tidak menghasilkan panggilan paralel.

Webhook memverifikasi Client ID, timestamp, signature, path, dan body asli. Akun merchant dan lingkungan yang terautentikasi harus cocok dengan konteks intent pertama; invoice yang kebetulan sama pada akun lain tidak dapat melunasi order lama. Pemeriksaan status menggunakan ikatan akun/lingkungan yang sama. Invoice serta nominal harus cocok dengan payment intent dan order. Currency yang tersedia harus cocok; bila DOKU tidak menyertakan currency pada notifikasi non-SNAP, intent IDR menjadi acuan. `transaction.original_request_id` dicatat dalam payload audit, tetapi tidak dijadikan satu-satunya identitas karena pembayaran melalui Checkout dapat melibatkan permintaan kanal yang berbeda.

Sukses yang valid mengubah pembayaran, konsumsi reservasi stok, kuota Flash Sale, dan penggunaan promosi dalam satu transaksi. Pengiriman baru menjadi intent `pending`; staf kemudian memesan kurir setelah barang siap. Notifikasi ganda tidak mengurangi stok dua kali. `FAILED`, `PENDING`, dan status yang belum dikenali tidak melunasi pesanan. `AUTHORIZE` dan `REFUND` tidak dianggap penerimaan pembayaran `SALE`.

### Status tertunda, kedaluwarsa, dan rekonsiliasi

Pemeriksaan server menggunakan `GET /orders/v1/status/{invoice}` resmi. Tombol periksa status dibatasi paling cepat sekali per 60 detik. Scheduler juga melakukan rekonsiliasi. Pembayaran yang masih dapat dibayar di DOKU tidak dibatalkan hanya karena timer browser atau jam lokal sudah habis.

Reservasi pembayaran nyata dilepas setelah pemeriksaan status yang terautentikasi mengembalikan `EXPIRED`, dan waktu kedaluwarsa penyedia ditambah jeda 60 detik telah berlalu. Notifikasi expired dari satu kanal tidak langsung melepas stok Checkout. Apabila jaringan/status penyedia belum pasti, reservasi tetap tersimpan dan dapat direkonsiliasi; tidak ada invoice pengganti otomatis. Intent yang belum pernah dikirim ke penyedia masih dapat dibatalkan secara lokal.

Jika pembayaran benar-benar diterima setelah stok dilepas, atau ledger stok tidak dapat dikonsumsi, fakta penerimaan uang tetap dicatat. Event diberi status `failed` dengan alasan rekonsiliasi dan pesanan tidak dikirim otomatis. Halaman admin menampilkan jumlah dan identitas event tersebut. Tindak lanjut operator:

1. Buka order dan catat invoice, nominal, waktu, serta alasan event.
2. Periksa invoice melalui endpoint refresh admin dan dashboard DOKU pada akun/lingkungan yang benar. Jangan menganggap redirect pelanggan atau screenshot sebagai pengganti status penyedia.
3. Untuk `payment_amount_or_currency_mismatch`, cocokkan nominal intent dengan transaksi merchant. Pertahankan penahanan fulfillment sampai selisih dijelaskan.
4. Untuk `late_payment_requires_reconciliation`, verifikasi ketersediaan barang. Jika pemenuhan baru diperlukan, lakukan proses operasional pesanan pengganti yang diaudit; jika dana harus dikembalikan, gunakan proses refund merchant yang disetujui. Endpoint ini tidak memalsukan refund atau otomatis mengembalikan stok barang yang mungkin sudah dikirim.
5. Untuk `stock_or_promotion_reconciliation`, perbaiki ledger melalui proses koreksi yang diaudit, lalu gunakan **Periksa pembayaran** di halaman admin atau `POST /api/admin/orders/{id}/payment/refresh`. Respons SUCCESS baru yang lolos pemeriksaan akun, nominal, dan stok mencoba lagi konsumsi reservasi secara atomik. Jika berhasil, order menjadi paid dan hanya flag kegagalan stok/promosi yang selesai ditutup. Payload serta alasan event lama tetap disimpan; log `doku_reconciliation_resolved` menghubungkan event lama dengan event verifikasi penyelesaian. Pengulangan refresh tidak mengonsumsi stok dua kali. Jangan mengubah order menjadi `paid` secara manual untuk melewati pemeriksaan.
6. Untuk `payment_account_or_environment_mismatch`, pulihkan konfigurasi akun/lingkungan asal. Intent legacy tanpa konteks akun harus direkonsiliasi dengan bukti merchant dan proses migrasi yang diaudit; aplikasi tidak mengasumsikan pemilik kredensial baru sebagai pemilik transaksi lama.
7. Simpan catatan penyelesaian kasus selisih nominal, keterlambatan pembayaran, atau refund pada sistem operasional merchant. Flag kasus finansial tersebut tetap membutuhkan tinjauan manual; refresh tidak menghapusnya secara otomatis. Payload audit dan histori event dipertahankan untuk pemeriksaan; tidak ada tombol penghapusan event finansial di aplikasi ini.

## 3. Everpro

Isi konfigurasi berikut dari proses onboarding Everpro:

| Variabel | Penggunaan |
| --- | --- |
| `EVERPRO_CLIENT_KEY`, `EVERPRO_CLIENT_SECRET` | Pertukaran token Bearer server |
| `EVERPRO_ENVIRONMENT` | `sandbox` atau `production` |
| `EVERPRO_BASE_URL` | Sandbox terdokumentasi: `https://client-api-sandbox.everpro.id`; host production harus sesuai onboarding |
| `EVERPRO_WEBHOOK_KEY` | Shared secret header `x-everpro-key` dari onboarding |
| `EVERPRO_ORIGIN_POSTAL_CODE` | Kode pos pengirim, 5 digit |
| `EVERPRO_ORIGIN_SUBDISTRICT` | Kelurahan/desa pengirim |
| `EVERPRO_SHIPPER_NAME`, `EVERPRO_SHIPPER_PHONE`, `EVERPRO_SHIPPER_ADDRESS` | Identitas dan alamat pengirim |
| `EVERPRO_SHIPPER_EMAIL` | Email pengirim, opsional |
| `EVERPRO_SHIPMENT_TYPE` | `DROP` atau `PICKUP` |
| `EVERPRO_PACKAGE_TYPE_ID` | Default 3 untuk fragile; sesuaikan dengan paket |
| `EVERPRO_PACKAGE_LENGTH_CM`, `EVERPRO_PACKAGE_WIDTH_CM`, `EVERPRO_PACKAGE_HEIGHT_CM` | Ukuran kemasan aktual dalam cm |
| `EVERPRO_USE_INSURANCE` | `1` untuk meminta tarif asuransi; default `0` |
| `EVERPRO_QUOTE_TTL_SECONDS` | Masa berlaku quote lokal, default 600 detik |

Tidak ada host production yang ditebak oleh aplikasi. `EVERPRO_ENVIRONMENT=production` membutuhkan `EVERPRO_BASE_URL` yang diberikan Everpro dan menolak host yang mengandung sandbox.

### Ongkir dan data alamat

Alamat checkout menggunakan `postal_code`, `subdistrict` untuk **Kelurahan/Desa**, dan `district` untuk **Kecamatan**. Rate request memakai kode pos dan nama kelurahan, berat paket dalam kilogram, nilai barang, dimensi kemasan, serta tipe pengiriman. Berat produk pada database tetap gram dan dikonversi di batas API.

Adapter menawarkan layanan regular, express, dan cargo dari respons provider yang dapat dipesan menggunakan kontrak alamat tersebut. Layanan instant/same-day yang memerlukan koordinat, serta flat-rate/wood-packing yang memerlukan kontrak booking tambahan, tidak ditampilkan sebagai layanan yang seolah dapat dipesan dengan form kode pos ini.

Setiap pilihan ongkir disimpan sebagai `shipping_quotes` dan diikat kepada pemilik, snapshot item/harga/berat, alamat, akun Everpro, dan konfigurasi asal. Pilihan itu memiliki masa berlaku. Preview dan checkout memvalidasi ulang quote; request tidak menerima harga kirim dari browser. Perubahan item, harga, kuantitas, alamat, akun, atau asal membuat pelanggan perlu menghitung ongkir kembali. Free-shipping voucher mengubah biaya yang dibayar pelanggan; biaya kurir sebenarnya tetap ada dalam quote dan shipment.

### Memesan pengiriman

Setelah pembayaran tervalidasi, admin membuka pesanan dan memilih **Pesan pengiriman** ketika produk sudah siap. Mode `DROP` berarti staf menyerahkan paket ke gerai kurir. Mode `PICKUP` memerlukan slot yang tersedia dari API pickup-times. Slot dipilih pada halaman admin, bukan ditebak berdasarkan jam lokal.

Booking menyimpan body permintaan dan `client_order_no` sebelum request jaringan. Setelah timeout, retry terlebih dahulu mencari order yang sama di Everpro. Jika belum ditemukan, POST menggunakan identitas yang sama; konflik duplikat direkonsiliasi dengan GET. Hasil booking dan penerbitan AWB merupakan dua tahap berbeda: order yang diterima tanpa resi akan ditampilkan menunggu resi dan dapat diperbarui melalui tombol refresh atau scheduler.

Apabila Everpro menghitung ulang tarif saat booking, shipment menyimpan biaya aktual dan log menyimpan selisih. Total yang sudah dibayar pelanggan tetap sama; tidak ada tagihan tambahan tersembunyi. Perubahan tarif perlu diperiksa operator sebelum menyimpulkan profit transaksi.

Konfigurasikan dua webhook pada dashboard/onboarding Everpro:

- AWB: `https://api.example.com/api/webhooks/everpro/awb`
- Tracking: `https://api.example.com/api/webhooks/everpro/tracking`

Keduanya memverifikasi shared secret `x-everpro-key`. Aplikasi tidak mengarang skema HMAC Everpro yang tidak ada pada kontrak publik tersebut. Callback dibatasi ukuran dan dideduplikasi. Invoice/nomor resi harus cocok. Callback yang terlambat tidak menurunkan status delivered kembali ke picked-up. Refresh server membaca tracking resmi dan mengambil label PDF saat tersedia. Scheduler tidak mengirim produk optik otomatis ketika pelanggan baru membayar.

Pesanan Everpro hanya selesai otomatis setelah status delivered terverifikasi dan periode penyelesaian yang dikonfigurasi telah lewat. Status picked-up, gagal pickup, atau paket belum sampai tidak dianggap delivered.

## 4. Endpoint aplikasi untuk UI

Semua path berikut berada di bawah prefix `/api`. Endpoint pelanggan memerlukan sesi pengguna yang sesuai; endpoint admin memerlukan admin atau izin order yang relevan.

| Endpoint | Fungsi |
| --- | --- |
| `GET /integrations/status` | Kesiapan provider tanpa rahasia |
| `POST /checkout/shipping-options` | `{address_id, selected_item_ids}` → pilihan dengan `quote_id` |
| `POST /checkout/preview` | Harga server; sertakan `shipping_quote_id` serta courier/service yang cocok |
| `POST /checkout/confirm` | Body preview + PIN; header `Idempotency-Key` disarankan |
| `GET /payments/{order_number}` | Order dan payment milik pengguna, aman untuk polling UI |
| `POST /orders/{id}/payment/retry` | Melanjutkan intent yang sama |
| `POST /orders/{id}/payment/refresh` | Memeriksa status DOKU melalui backend |
| `GET /shipping/locations?postal_code=40115` | Validasi/pilihan nama lokasi Everpro |
| `GET /admin/integrations` | Konfigurasi dan antrean rekonsiliasi |
| `GET /admin/orders/{id}/shipment/pickup-times` | `{times:[{label,value}], shipment_type}`; `value` Unix UTC |
| `POST /admin/orders/{id}/shipment` | `{}` untuk DROP, atau `{pickup_time: ...}` untuk PICKUP |
| `POST /admin/orders/{id}/shipment/refresh` | Perbarui resi, label, dan tracking |
| `POST /admin/orders/{id}/payment/refresh` | Rekonsiliasi status pembayaran oleh admin |
| `POST /webhooks/doku` | Notifikasi HMAC penyedia, tanpa autentikasi sesi browser |
| `POST /webhooks/everpro/awb` | Callback resi dengan shared key |
| `POST /webhooks/everpro/tracking` | Callback tracking dengan shared key |

Contoh pilihan ongkir dan payload checkout:

```json
{
  "address_id": "alamat-milik-pengguna",
  "selected_item_ids": ["item-keranjang"],
  "shipping_quote_id": "quote-dari-respons-backend",
  "courier_code": "JNE",
  "service_code": "REG23",
  "use_points": 0,
  "pin": "PIN-pengguna"
}
```

PIN pada permintaan nyata harus 6 digit. Contoh di atas menunjukkan struktur, bukan kredensial uji siap pakai. Jangan mencatat PIN, secret, Authorization token, atau data resep pada access log.

## 5. Verifikasi sebelum aktivasi merchant

Jalankan suite backend terisolasi dari `backend`:

```bash
python -m pytest -c pytest-mysql.ini tests_mysql/test_integrations.py -q
```

Uji sandbox akun sendiri harus mencakup pembayaran berhasil, pelanggan mengganti metode setelah gagal, notification retry, refresh setelah callback tertunda, quote berubah/kedaluwarsa, timeout pembuatan pembayaran, booking drop/pickup, AWB yang terbit belakangan, serta tracking delivered. Bandingkan invoice dan nominal pada database dengan dashboard provider. Uji konfigurasi proxy menggunakan path webhook publik yang sebenarnya.

Sediakan satu worker scheduler aktif melalui `SCHEDULER_ENABLED=1`; worker API tambahan dapat menonaktifkannya. Lock SQL dan deduplikasi tetap menjadi pelindung status, tetapi satu scheduler menghindari polling provider yang tidak perlu. Pengujian MySQL aktual dan cutover data mengikuti dokumentasi migrasi yang terpisah.

## Referensi protokol resmi

- [DOKU Checkout backend integration](https://developers.doku.com/accept-payments/doku-checkout/integration-guide/backend-integration)
- [DOKU request signature non-SNAP](https://developers.doku.com/get-started-with-doku-api/signature-component/non-snap/signature-component-from-request-header)
- [DOKU response signature](https://developers.doku.com/get-started-with-doku-api/signature-component/non-snap/signature-componen-from-response-header)
- [DOKU GET signature](https://developers.doku.com/get-started-with-doku-api/signature-component/non-snap/signature-from-api-get-method)
- [DOKU notification handling and Checkout retry behavior](https://developers.doku.com/get-started-with-doku-api/notification/best-practice)
- [DOKU transaction status API](https://developers.doku.com/get-started-with-doku-api/check-status-api/non-snap)
- [DOKU simulator and notifications](https://developers.doku.com/accept-payments/doku-checkout/integration-guide/simulate-payment-and-notification)
- [Everpro Open API](https://developer.everpro.id/)

Referensi ditinjau pada implementasi ini; konfigurasi production dan kanal yang disetujui harus mengikuti akun merchant masing-masing.
