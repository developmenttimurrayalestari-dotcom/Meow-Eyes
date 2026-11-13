# Poin, Games, Cashback, RMA, dan Virtual Try-On

## Halaman dan komponen

| Fitur | Lokasi |
| --- | --- |
| Manage Konversi Poin | `/admin/points/conversion` |
| Monitoring Poin Customer | `/admin/points/customers` |
| Parent Manage Games dan submenu dinamis | `/admin/games`, `/admin/games/:key` |
| Pengaturan hadiah Roulette | `/admin/games/roulette`; URL lama dialihkan |
| Konfigurasi 20 level Puzzle Geser | `/admin/games/slide-puzzle` |
| Event Cashback Pembelian | `/admin/cashback-events` |
| Review RMA dan alamat retur toko | `/admin/returns` |
| Permainan | `/games`, `/games/:key`, `/roulette` |
| Saldo, nilai rupiah, dan riwayat poin | `/points` |
| Pengajuan penggantian | bagian Pengembalian di `/orders/:id` |
| Katalog kamera Virtual Try-On | `/virtual-try-on`, tersedia di navigasi utama |

`AdminLoyalty` menyediakan form konversi, monitor wallet, event, konfigurasi game, dan editor level. Menu games berasal dari API; penambahan game dengan engine yang tersedia langsung menambahkan submenu. Engine baru dapat ditambahkan pada registry model, replay server, dan renderer frontend. Game Puzzle lama dan Tetris dinonaktifkan tanpa menghapus skor historis.

`GamesRoundPage` meminta sesi server sebelum memasang `SpaceWarGame`, `MatchingGame`, atau `SlidePuzzle`. `VirtualTryOnPage` mempertahankan instance `TryOnStudio` ketika katalog mengganti aset; varian dan stok produk yang dipilih dipakai saat memasukkan barang ke keranjang. `OrderReturns` dan `AdminReturns` memakai komponen video privat, instruksi retur, dan timeline yang sama.

VTO mobile memakai preview setinggi viewport (`100dvh`) dengan gambar kamera `object-fit: cover`. Pilihan frame, pencarian, kontrol kamera, dan kartu Beli melayang di atas preview. Header toko, navigasi bawah, dan WhatsApp disembunyikan selama mode ini; semuanya dipulihkan saat keluar atau kembali ke ukuran desktop. Koordinat frame diproyeksikan mengikuti crop kamera, termasuk saat orientasi berubah, tanpa membuka ulang stream. Tampilan portrait/landscape dan pemulihan navigasi telah diperiksa di browser dengan kamera sintetis; 22 pengujian terkait dan build produksi lulus.

## Nilai poin tetap

Sesuai konfirmasi, **semua poin termasuk cashback mempertahankan rate asal**. Contoh: 50 poin pada rate Rp100 tetap bernilai Rp5.000 walaupun rate baru Rp250. Poin yang diperoleh sesudah perubahan memakai Rp250. Nilai wallet adalah penjumlahan setiap lot, bukan saldo dikali rate terbaru.

- `point_settings` menyimpan rate aktif dan versi; setiap perubahan ditambahkan pada `point_rate_versions`.
- `point_lots` menyimpan asal, jumlah diperoleh/tersisa, rate, versi, dan kedaluwarsa setiap perolehan.
- `point_history` menyimpan delta, saldo, rate dan nilai rupiah setiap kejadian. Trigger MySQL mencegah perubahan dan penghapusan riwayat.
- Checkout memakai poin yang paling cepat kedaluwarsa terlebih dahulu, lalu poin tanpa kedaluwarsa. `point_redemptions` menyimpan alokasi ke setiap lot.
- Pembatalan pembayaran mengembalikan alokasi ke lot asal dengan rate dan tanggal kedaluwarsa yang sama. Poin yang sudah melewati masa berlaku langsung dicatat hangus.
- Saldo lama dimigrasikan pada rate tetap Rp100 yang digunakan aplikasi sebelumnya. `point_logs` lama tetap dipertahankan dan disalin ke riwayat baru; selisih saldo dicatat sebagai rekonsiliasi.
- Kedaluwarsa diproses setiap lima menit serta sebelum membaca wallet, menerima poin, atau checkout. Semua mutasi memakai transaksi dan kunci customer yang sama.

Admin tidak mengedit saldo secara langsung. Monitoring menampilkan diperoleh, digunakan bersih setelah pengembalian poin, hangus, sisa, dan rincian rate.

## Aturan permainan

Setiap game memiliki cooldown dalam detik (form admin memakai jam), masa berlaku poin, durasi maksimal 10–600 detik, batas poin, dan poin per unit. Nilai awal: jeda 24 jam, kedaluwarsa 30 hari, durasi 180 detik, maksimal 50 poin. Hadiah Roulette yang sudah ada dipertahankan dengan batas awal minimal sebesar hadiah poin aktif tertinggi.

Sesi menyimpan seed, aturan, rate dan versi saat mulai. Sesi aktif dapat dibuka kembali, dan satu customer hanya memiliki satu sesi aktif per game. Endpoint skor mentah lama mengembalikan 410. Browser mengirim langkah/kontrol; server memainkan ulang dan memeriksa durasi, kepemilikan, batas waktu, hasil dan idempotensi. Ini menolak skor buatan dan pemberian ganda; replay deterministik bukan pengganti deteksi bot.

- **Match Meow Pairs:** delapan pasangan. Poin = pasangan terselesaikan × poin per unit, dibatasi konfigurasi.
- **Puzzle Geser:** level 1–20, 2–6 baris dan kolom. Gambar diunggah melalui image picker admin. Acakan berasal dari langkah legal sehingga dapat diselesaikan. Poin = nomor level × poin per unit, dibatasi konfigurasi.
- **Space War:** world integer 16000 × 10000 pada 30 tick/detik. Pesawat hanya bergerak atas/bawah, laser otomatis, tiga nyawa, invulnerability pendek setelah tabrakan. Kecepatan alien naik setiap 30 detik dan jumlah satu kelompok naik setiap 60 detik. Ronde selesai pada habis nyawa, waktu maksimal, atau batas poin. Nilai 0 pada batas poin berarti tidak memberikan poin; durasi tetap membatasi ronde.
- **Roulette:** pemilihan hadiah acak di server. Cooldown dan expiry poin memakai aturan game. Hadiah voucher/pengiriman tetap mengikuti alur reward yang sudah ada.

Source PNG, atlas, manifest dan prompt: [`frontend/public/games/space-war/ASSETS.md`](../frontend/public/games/space-war/ASSETS.md).

## Cashback

Event memiliki nama, waktu mulai/akhir berzona waktu, persentase, status aktif, dan masa berlaku poin. Jika event tumpang tindih, persentase tertinggi dipakai. Total akhir pesanan termasuk ongkir menjadi dasar cashback. Poin bulat dihitung ke bawah: `floor(total × persen / 100 / rate)`.

Event dan rate disalin saat pesanan dibuat; edit event/rate sesudahnya tidak mengubah transaksi tersebut. Poin diberikan sekali setelah pembayaran lunas dan pesanan selesai, termasuk penyelesaian otomatis scheduler. Masa berlaku dimulai saat poin dikreditkan. Cashback merupakan hadiah pascatransaksi untuk pembelian berikutnya. Prioritas diskon Flash Sale saat checkout tetap berlaku.

## Alur penggantian barang

`draft → submitted → approved → return_sent → received → replacement_shipped → completed`.

Draf dapat dibatalkan customer; pengajuan yang dikirim dapat ditolak admin dengan alasan. Pengajuan membutuhkan pesanan lunas yang sudah diterima/selesai, jumlah klaim tidak melebihi jumlah dibeli setelah memperhitungkan klaim aktif lain, dan video unboxing MP4/WebM maksimal 100 MB. Batas awal pengajuan tujuh hari adalah pengaturan toko dan dapat diubah admin.

Video disimpan di `PRIVATE_UPLOAD_ROOT/return-evidence` atau direktori privat backend bawaan. URL hanya dapat dibuka customer pemilik, admin, atau staff berizin `order.view`. Berkas dicek tipe, signature container dan ukuran, diberi nama acak, serta tidak diekspos melalui public uploads. Review admin tetap menentukan isi bukti.

Sebelum menyetujui klaim, lengkapi nama penerima, telepon, dan alamat retur toko di `/admin/returns`. Approval menyalin instruksi, kode klaim dan batas kirim balik; tidak membuat resi fiktif. Customer memasukkan resi retur sebenarnya. Admin menandai barang diterima, lalu memasukkan kurir dan resi pengganti sebenarnya. Pengiriman pengganti mengurangi stok varian seluruh komponen pesanan secara atomik, satu kali. Barang rusak yang diterima tidak otomatis menjadi stok jual.

Pesanan finansial asli tetap dipertahankan; penyelesaian klaim berupa produk pengganti. Fitur ini tidak menjalankan refund uang atau pembelian label kurir otomatis.

## Migrasi dan menjalankan aplikasi

Head skema: `20261111_0005`, 14 tabel baru. Backup dan hentikan writer aplikasi sebelum DDL karena MySQL 5.7 melakukan implicit commit. Upgrade tidak menghapus transaksi lama. Jangan memakai `stamp` untuk melewati pemasangan tabel/trigger.

```powershell
cd backend
python -m alembic upgrade head
python -m mysql.check_integrity
python -m uvicorn server:app --host 0.0.0.0 --port 8001
```

Jalankan satu instance backend pada port yang sama. Jika backend sudah berjalan, hentikan proses lama sebelum menjalankan kode terbaru. Frontend memakai proses development yang sudah ada atau `npm run build` untuk deployment. Jangan membuka video bukti melalui file statis publik.

SQL incremental tersedia di `backend/sql/005_loyalty_games_returns.sql`. Source migrasi memiliki DDL dan trigger yang dibekukan, bukan impor metadata aplikasi pada waktu upgrade. Downgrade ditolak agar riwayat poin dan RMA tidak hilang.

## Validasi pada 11 November 2026

Migrasi telah diterapkan pada database toko: 93 tabel aplikasi, 154 trigger, 139 aturan integritas. Jumlah baris tabel lama selain definisi game tetap, saldo customer tetap, dan selisih rekonsiliasi wallet nol. Empat game terdaftar dan 20 level telah diinisialisasi. Backup penuh sebelum pemasangan: `backend/private/backups/loyalty-before-0005-20261111T032444Z.sql`; laporan pemasangan berada di `backend/private/loyalty-migration-report.json`.

Pada MySQL 5.7 yang digunakan, pembungkus `REPLACE(UUID(),...)` di `INSERT SELECT` dapat menghasilkan ID berulang. Backfill memakai SHA-256 dari ID sumber sehingga identitas selalu bergantung pada baris asal. Percobaan awal terhenti sebelum data seed ter-commit; semua tabel baru diperiksa kosong dan strukturnya diverifikasi sebelum dilanjutkan tanpa menghapus tabel. Opsi pemulihan `-x resume_empty_loyalty=true` hanya boleh dipakai setelah review dan menolak tabel tidak kosong, struktur, indeks, foreign key, atau collation yang berbeda. Jangan menjalankannya sebagai cara melewati audit.

Pengujian backend terisolasi: **337 lulus**, satu uji MySQL disposable dilewati karena database uji khusus tidak dikonfigurasi, dan dua uji symlink tidak dijalankan karena Windows tidak memberikan hak membuat symlink. Uji baru mencakup snapshot rate, expiry, pengembalian poin, idempotensi ronde, cooldown, replay, cashback, klaim wajib video, batas jumlah, kepemilikan berkas, dan stok penggantian. Uji struktur lama telah diperbarui untuk memasukkan 14 tabel baru.

Uji browser pada build produksi memakai API simulasi dan kamera sintetis: pergantian frame mempertahankan kamera, varian keranjang benar, submenu game dinamis, perubahan jeda 3 jam menjadi 10800 detik, nilai wallet mengikuti lot, dan Space War menyelesaikan ronde waktu nyata dengan kontrol mobile. Laporan: `backend/private/loyalty-browser-report.json`. Uji ini tidak membuat pesanan, pembayaran, atau pemesanan kurir nyata.

Seluruh **184 pengujian frontend pada 28 suite lulus** dan build produksi berhasil. Peringatan build yang tersisa berasal dari dependency dan source map MediaPipe yang tidak disertakan paket. Pemeriksaan pada backend aktif memverifikasi readiness, katalog VTO, empat game, 20 level, penolakan akses privat tanpa login, serta trigger `point_history`, `point_rate_versions`, dan snapshot `point_lots`. Probe trigger selalu di-rollback. Laporan: `backend/private/loyalty-live-report.json`; ringkasan publik: `docs/qa/loyalty-results.json`.
