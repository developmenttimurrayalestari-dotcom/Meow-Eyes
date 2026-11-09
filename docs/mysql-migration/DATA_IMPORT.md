# Step 2 — Konversi data MongoDB dan seeder MySQL

Target: **MySQL 5.7.24-log**, skema Alembic `20261106_0002`.

Kode ini menyediakan konversi dari **ekspor lokal yang sudah dibekukan**.
Paket proyek tidak menyertakan ekspor database produksi. Karena itu, hasil
pengujian menggunakan fixture sintetis dan **bukan** bukti data produksi sudah
dipindahkan. Importer tidak menerima URI MongoDB dan tidak membuka koneksi ke
server sumber.

## 1. Bentuk input

Simpan satu file per koleksi dalam satu direktori. Nama file harus persis
`<nama_koleksi>.json`, `.jsonl`, atau `.ndjson`. Format yang diterima:

- Satu array JSON berisi dokumen, seperti keluaran `mongoexport --jsonArray`.
- Satu dokumen JSON per baris, seperti keluaran standar `mongoexport`.
- Extended JSON v2 untuk `$oid`, `$date`, `$numberInt`, `$numberLong`,
  `$numberDecimal`, dan `$numberDouble` yang bernilai finite.

Gunakan `--jsonFormat=canonical` saat menyiapkan ekspor agar tipe angka/tanggal
tetap eksplisit. MongoDB mendokumentasikan perbedaan canonical/relaxed dan
opsi array dalam [dokumentasi mongoexport](https://www.mongodb.com/docs/database-tools/mongoexport/)
dan [catatan fidelitas tipe](https://www.mongodb.com/docs/database-tools/mongoexport/mongoexport-behavior/).
Importer hanya mendukung tipe yang diperlukan model aplikasi ini; tipe BSON
lain, BSON dump, arsip terkompresi, dan kunci Extended JSON yang ambigu ditolak.
`mongoexport` bukan pengganti backup server yang lengkap.

Semua **37 koleksi** harus mempunyai file. File `[]` berarti koleksi memang
kosong menurut ekspor sumber. **Jangan membuat file kosong untuk menutupi
koleksi yang belum berhasil diekspor.** Mode `--allow-partial` tersedia untuk
subset yang ditinjau secara sengaja dan menghasilkan peringatan; mode ini
bukan bukti migrasi seluruh database.

```text
addresses, article_categories, articles, banners_v2, brands, cart_items,
categories, cms_banners, cms_pages, contact_messages, contact_settings,
faq_categories, faqs, flash_sales, game_scores, games, lens_indexes,
newsletter_campaigns, newsletter_subscribers, order_status_logs, orders,
payment_logs, point_logs, product_knowledges, product_reviews,
product_subscriptions, products, roulette_rewards, roulette_spins,
shipment_logs, stock_movements, stock_reservations, uploads, user_sessions,
users, vouchers, wishlists
```

File koleksi tambahan dan dua file berbeda untuk koleksi yang sama memblokir
impor. Simpan laporan, manifest backup, dan berkas lain **di luar** direktori
input. Input dibaca penuh ke memori; ekspor besar memerlukan uji kapasitas dan
penyesuaian strategi ETL sebelum menjalankannya. Metadata unggahan dipindahkan,
tetapi byte gambar/file di disk atau object storage harus disalin dan
diverifikasi melalui prosedur backup media tersendiri.

## 2. Dry-run tanpa koneksi database

Dari direktori `backend` dengan environment Python proyek aktif:

```bash
python -m mysql.import_mongo /private/export-meow \
  --report /private/reports/meow-preflight.json
```

Tanpa `--apply` atau `--target-check`, perintah ini tidak membutuhkan kredensial
MySQL, tidak membuka database target, dan tidak menulis data aplikasi. Validasi
relasional memakai SQLite sementara di memori, metadata skema yang sama, serta
pemeriksaan akuntansi sumber. Tidak ada file SQLite yang disimpan.

Laporan berisi checksum dataset, jumlah per koleksi/tabel, referensi record
bermasalah, kode masalah, jumlah order/stok/poin/voucher, dan batas validasi.
Laporan tidak memuat kata sandi, PIN, session token, alamat lengkap, ukuran
resep, atau isi payload pembayaran. Simpan laporan dan ekspor asli di lokasi
yang aksesnya dibatasi.

Kesalahan menghasilkan exit code `2` dan `ready_for_apply=false`. Peringatan
yang diketahui tidak membuat nilai bisnis diubah; penerapannya tetap
membutuhkan `--acknowledge-warnings` setelah laporan ditinjau. Flag tersebut
**tidak** mengabaikan kesalahan.

Nilai eksplisit yang bertentangan dengan alias atau hasil normalisasi juga
memblokir impor: urutan variant versus posisi array, field banner lama versus
field relasional, prescription ID versus resep inline, serta tautan/flag
verifikasi review versus bukti order. ID child kosong tidak diganti dengan ID
baru; ID deterministik hanya dibuat bila field itu memang tidak ada di sumber.

## 3. Pemetaan dan kebijakan pelestarian

| Sumber | Hasil dan kebijakan |
| --- | --- |
| `users`, `user_sessions`, `addresses` | ID aplikasi, hash bcrypt, saldo, peran dan alamat dipertahankan. Permission menjadi `user_permissions`. Token sesi menjadi SHA-256; waktu kedaluwarsa tidak diperpanjang. `_id` Mongo digunakan sebagai identitas provenance, bukan pengganti ID aplikasi. |
| `products`, `categories`, `brands`, `lens_indexes` | Variants, kategori, gambar berurutan, segments dan badges menjadi baris relasional. ID variant dan SKU asli dipertahankan. Parent kategori diperiksa dari referensi dan siklus. |
| `cart_items` | Bundle ID lensa/index dipertahankan. Resep lama `od_sph`, `os_sph`, `od_cyl`, `os_cyl`, `pd`, `notes` menjadi `prescriptions` dan `prescription_eyes`; nilai kosong menjadi tidak diketahui, bukan nol. AXIS/ADD dan PD per mata juga dikenali jika sumber sudah memilikinya. |
| `orders` | Snapshot alamat dan item disimpan tersendiri. Harga, label produk, subtotal dan total berasal dari transaksi lama; tidak dihitung ulang menggunakan katalog saat ini. ID child yang dahulu tidak ada dibuat deterministik dari ID order dan posisi item. |
| Field pembayaran/pengiriman pada `orders` | Dipindahkan ke snapshot `payments`/`shipments` dengan ID/request ID deterministik. Provider dari log digunakan hanya jika tidak ambigu; selain itu label `legacy-import` digunakan. Snapshot ini bukan bukti panggilan API baru. `paid_at`, `shipped_at` dan waktu lain yang tidak ada di sumber tetap null. |
| `order_status_logs`, `stock_reservations`, `stock_movements` | Referensi, status, kuantitas dan waktu asli dipertahankan. `admin` dipetakan ke `admin_id`. Referensi item boleh null bila sumber memang tidak mencatatnya. |
| `payment_logs`, `shipment_logs` | Log dipertahankan terpisah tanpa mengarang tautan attempt yang ambigu. Snapshot JSON dengan angka Decimal menggunakan string desimal exact. Kunci yang menyerupai credential memblokir impor sampai operator menyediakan ekspor yang telah direduksi secara eksplisit. |
| `vouchers`, `orders.voucher_code` | Definisi dan counter dipertahankan; dibuat `voucher_redemptions` dari hubungan order yang terverifikasi. Status pending menjadi reserved; paid/processing/shipped/completed menjadi redeemed; cancelled/expired/refunded menjadi released. |
| `flash_sales` | Item kampanye menjadi `flash_sale_items`. Harga/quota/sold asli dipertahankan; alokasi penjualan lama yang tidak tercatat tidak direkonstruksi. |
| `games`, `game_scores`, `roulette_rewards`, `roulette_spins`, `point_logs` | Catatan dan saldo asli dipertahankan. `orders.roulette_reward_id` sebenarnya berisi **spin ID**; menjadi `roulette_redemptions`, dengan pemeriksaan pemilik dan `used_order_id`. Tidak ada hadiah, poin, atau game historis yang dibuat untuk menutupi gap. |
| `product_reviews` | Foto menjadi `product_review_images`. Review dengan order diverifikasi terhadap pemilik, status completed dan baris produk. Review tanpa order tetap unverified dan dilaporkan. Konflik `status` dengan `is_approved` memblokir impor. |
| `wishlists`, `product_subscriptions`, `newsletter_subscribers`, `newsletter_campaigns` | Menjadi tabel bernama sama dengan kunci/refensi relasional; duplikat tidak digabung diam-diam. |
| `articles`, `article_categories` | HTML, SEO dan status dipertahankan; tags menjadi `article_tags`. |
| `product_knowledges` | `is_published` menjadi status; pros/cons dan related products menjadi tabel child berurutan. Konflik state memblokir impor. |
| `faq_categories`, `faqs`, `cms_pages`, `contact_messages`, `uploads` | Field lama dipindahkan ke tabel terkait, dengan validasi tipe, panjang, referensi dan status. |
| `cms_banners`, `banners_v2` | Keduanya masuk ke `banners`; `image`/`link` lama menjadi `image_desktop`/`link_url`, reference V2 menjadi FK sesuai jenis link. Semua ID dipertahankan. ID bentrok memblokir impor; konten dengan judul serupa tidak dihapus/digabung otomatis. |
| `contact_settings` | Satu record konfigurasi toko; lebih dari satu singleton memblokir impor. Nomor WhatsApp dipindahkan ke `whatsapp_settings`. Default chat text tetap kosong dan floating feature tetap belum diaktifkan; tidak mengarang pesan baru. |

**Aturan angka:** nilai keuangan menggunakan Decimal dengan skala dua,
`ROUND_HALF_UP`. Setiap pembulatan yang mengubah nilai dilaporkan sebagai
peringatan. Integer pecahan, NaN/Infinity, overflow, data terlalu panjang dan
tanggal tanpa zona waktu memblokir impor. Timestamp aware dikonversi ke UTC.
Timestamp yang diwajibkan tetapi hilang tidak diganti dengan waktu impor.
`updated_at` child baru dapat mengikuti timestamp parent yang diketahui.

**Batas historis:** implementasi lama tidak menyimpan rincian lensa dan resep
sebagai snapshot item order. Importer tidak membangun rincian tersebut dari
keranjang/katalog sekarang. Setiap order mendapat peringatan
`legacy_bundle_details_unknown`. Counters rating/sold yang tidak sama dengan
review/pembelian tercatat dipertahankan sebagai cache lama dan dilaporkan;
tidak dibuat review atau transaksi fiktif.

## 4. Rekonsiliasi sebelum menulis

Pemeriksaan sumber mencakup:

- Identitas, field tak dikenal, tipe, referensi FK dan unique key, termasuk
  deteksi konservatif bentrok case/accent/trailing-space.
- Kuantitas dan harga item terhadap subtotal; subtotal terhadap total order
  dengan rumus checkout legacy yang diaudit.
- Kuantitas reserved variant terhadap seluruh reservation aktif; item pending
  terhadap reservation milik order yang sama; status dan expiry pending.
  Reservation aktif tanpa variant inventori memblokir impor karena pembayaran
  tidak dapat diselesaikan dengan aman; reference null pada riwayat yang sudah
  resolved tetap dipertahankan tanpa mengarang identitas stok.
- Saldo pengguna terhadap log poin terakhir dan kontinuitas antar log.
  Saldo awal tanpa riwayat dilaporkan sebagai keterbatasan, tidak dibuatkan log.
- `used_count` voucher terhadap order aktif/terbayar yang merujuknya; penggunaan
  roulette terhadap pemilik, order dan flag used.
- Kepemilikan dan kelayakan review; referensi uploaded-by/author/admin.

Validasi offline bukan implementasi lengkap collation MySQL
`utf8mb4_unicode_ci`, trigger, atau locking InnoDB. MySQL tetap menjadi otoritas
terakhir. Error SQL saat apply menggagalkan seluruh chunk transaksi yang
bersangkutan. Aplikasi tetap harus dihentikan sampai seluruh run terverifikasi.

## 5. Persiapan target dan pemeriksaan read-only

Gunakan database MySQL baru dengan skema hasil Alembic. Jangan mengimpor ke
database demo atau menggabungkannya langsung dengan data bisnis yang sudah ada.
Importer hanya menerima target kosong atau resume persis dari run yang sama.

```bash
python -m alembic upgrade head
python -m mysql.check_integrity
python -m mysql.import_mongo /private/export-meow \
  --target-check \
  --report /private/reports/meow-target-preflight.json
```

`--target-check` memeriksa koneksi, versi, head Alembic, guard trigger,
emptiness/provenance, dan drift record tanpa mengubah target. Gunakan akun
migrasi/DBA dengan hak melihat metadata trigger. Audit tidak membuktikan
keberadaan/effective privileges semua akun trigger definer; persiapan akun
stabil tetap mengikuti panduan Step 1.

Hentikan seluruh penulis aplikasi lama dan baru, scheduler, worker, proses
admin, serta import lain. Bekukan ekspor setelah penulis sumber berhenti,
simpan backup, dan tinjau kembali hasil preflight sebelum cutover.

## 6. Apply dan resume

Setelah target dan laporan sudah ditinjau:

```bash
python -m mysql.import_mongo /private/export-meow \
  --apply \
  --writers-stopped \
  --acknowledge-warnings \
  --source-label meow-reviewed-export \
  --report /private/reports/meow-apply.json
```

`--acknowledge-warnings` hanya diperlukan bila ada warning; contoh di atas
menyertakannya karena order lama memiliki batas snapshot yang diketahui.

Perilaku checkpoint:

1. Importer mengambil advisory lock MySQL untuk mencegah dua importer berjalan
   bersamaan pada database yang sama. Lock ini tidak menghentikan writer aplikasi;
   writer tetap harus dihentikan operator.
2. Semua tabel/row ditulis berurutan menurut FK; kategori parent lebih dahulu.
3. Setiap chunk (default 200 row, batas 1–1000) menulis row dan
   `migration_records` dalam **transaksi yang sama**.
4. `migration_runs` menyimpan checksum ekspor, revisi skema dan status progress.
   `migration_issues` menyimpan penjelasan yang sudah disanitasi.
5. Sebelum resume, semua row yang sudah diimpor dicocokkan lagi dengan nilai
   yang diharapkan dan checksum sumber. Row yang berubah/hilang, row tambahan,
   atau ekspor yang berubah memblokir resume. Tidak ada overwrite otomatis.
6. Setelah semua row selesai, jumlah per tabel dan setiap nilai row diverifikasi
   lagi. Run menjadi completed dan provenance menjadi verified.

Jika proses terputus, pertahankan ekspor yang **sama persis** dan ulangi perintah
yang sama. Run ID diturunkan deterministik dari checksum ekspor. Jika operator
menentukan `--run-id`, gunakan ID yang sama pada resume. Chunk yang terputus
rollback, sedangkan chunk terdahulu tetap tercatat dan diverifikasi sebelum
dilewati. Jangan menghapus record provenance untuk mencoba memaksa resume.

Importer tidak mempunyai fitur reset/drop untuk rollback. Sebelum cutover,
rollback berarti kembali menggunakan sumber lama yang tetap disimpan dan
meninggalkan target gagal untuk diagnosis; target baru dapat disiapkan dari
backup/prosedur DBA yang disetujui. Setelah aplikasi mulai menulis ke MySQL,
rollback memerlukan rekonsiliasi transaksi baru, bukan sekadar mengganti DSN.

## 7. Seeder demo MySQL

`seed.py` dan `seed_content.py` tidak lagi memakai Motor/PyMongo. Eksekusi selalu
eksplisit; startup API tidak menjalankan seed. Seeder ditolak di production.

Untuk database pengembangan kosong, sediakan lewat environment:

```text
APP_ENV=development
DEMO_ADMIN_PASSWORD=<password demo admin, 8–72 byte UTF-8>
DEMO_CUSTOMER_PASSWORD=<password demo customer, 8–72 byte UTF-8>
DEMO_STAFF_PASSWORD=<password demo staff, 8–72 byte UTF-8>
DEMO_CHECKOUT_PIN=<enam digit>
```

Variabel demo dibaca dari environment proses; tidak ada password/PIN default
di source. Kemudian jalankan:

```bash
python seed.py --demo
```

Paket demo lengkap membuat 163 dokumen contoh yang dinormalisasi menjadi 393
row aplikasi, lalu satu marker versi internal. Termasuk 20 produk asli, akun
`admin@meoweyes.id`, `customer@meoweyes.id`, `staff@meoweyes.id`, kategori,
promo dan konten asli. Password berasal dari variabel di atas. Data dan klaim
konten contoh bukan data/ketentuan operasional produksi.

Tiga bentrok SKU dari rumus seed lama diperbaiki dengan SKU demo deterministik
yang unik. Ini hanya berlaku untuk fixture demo; importer data nyata tetap
memblokir SKU bentrok. Rating/sold counters sintetis sumber tetap diberi label
demo dan tidak dibuatkan riwayat pembelian fiktif.

Eksekusi berikutnya menemukan marker versi dan menjadi no-op; password,
permission, tanggal promo, serta perubahan operator tidak ditimpa.
`python seed_content.py --demo` menyediakan fixture konten saja jika tabel CMS
masih kosong. Seed lengkap sudah mencakup konten; jangan menjalankan seed CMS
lebih dahulu bila nantinya ingin seed lengkap pada database yang sama.

## 8. Pengujian yang disediakan

```bash
python -m pytest -c pytest-mysql.ini tests_mysql/test_importer.py -q
```

Fixture pengujian mengisi semua 37 koleksi, termasuk order pending/completed,
reservation, pembayaran/pengiriman, review terverifikasi, pergerakan poin,
banner kedua versi dan resep keranjang. Pengujian memeriksa pelestarian hash,
token hashing, uang Decimal, child IDs stabil, semua mapping, informasi sensitif
yang tidak masuk laporan, penolakan data bermasalah, apply+resume, simulasi
interupsi di tengah chunk, drift target dan perlindungan data lama saat seed.

Hasil ini menggunakan SQLite dan tidak menggantikan rehearsal ekspor asli pada
MySQL **5.7.24-log**. Rehearsal tersebut, checksum file media, counts produksi,
durasi migrasi, dan rencana cutover aktual tetap menunggu ekspor/akses target
yang diberikan secara resmi.
