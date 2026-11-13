# Keamanan dan privasi Meowsurement customer

Dokumen ini menjelaskan implementasi akun/server yang aktif pada `/meowsurement/`. Vault lokal versi sebelumnya tidak menjadi sumber autentikasi atau persistence untuk alur customer ini. Tidak ada klaim sertifikasi keamanan atau enkripsi end-to-end.

## Identitas dan otorisasi

Autentikasi menggunakan `current_user` website Meow Eyes. `user_id` tidak diterima sebagai penentu pemilik dari request customer. Setiap pembacaan dan mutasi sesi, revisi, foto, dan ekspor memeriksa kepemilikan pada backend. Customer lain tidak dapat membuka sesi dengan mengganti ID; API merespons 404.

Petugas review menggunakan akun web `admin`/`super_admin`, atau `staff` dengan `meowsurement.review`. Hak produk memakai permission dashboard yang sudah ada. Customer tidak mendapatkan hak review hanya dari field lokal, query URL, atau status yang dikirim client. Akun reviewer tidak diwajibkan mengisi resep pribadinya untuk melihat sesi customer.

Review independen tidak boleh dilakukan pemilik sesi atau pembuat revisi. Approval membutuhkan revisi aktif, hasil yang lolos policy, catatan dan evidence. Customer tidak dapat menyimpan status approved di JSON. API dan trigger melindungi riwayat; otorisasi tidak bergantung pada menyembunyikan tombol.

## Sumber data dan integritas

Profil/resep diambil dari akun; frame dari produk/varian aktif. Composite foreign key memastikan resep milik customer dan varian milik produk. Snapshot identitas/resep/frame dibuat server dan immutable pada sesi. Revisi hanya menambahkan versi baru dengan alasan; UPDATE/DELETE terhadap history ditolak guard MySQL.

Version checking berlaku pada profil, spesifikasi agregat produk, dan revisi aktif. Versi tertinggal menghasilkan 409. Meowsurement tidak mengambil resep checkout lama sebagai resep aktif tanpa pilihan profil yang jelas, dan tidak mengubah snapshot resep dalam order.

Payload anotasi dibatasi 2 MiB, kedalaman/jumlah node dibatasi, angka non-finite ditolak, dan data URL/blob inline tidak diterima. Captures/hasil/sumber bukti mempunyai relasi yang diikat ke revisi yang sama. Server memvalidasi scope, konteks, kalibrasi, source hashes, perhitungan planar dan aggregate. Flag valid/approved dari client bukan bukti klinis.

## Data di browser

State profil, resep dan sesi berada di memori frontend selama digunakan. Tidak dibuat database pasien IndexedDB baru dan data tersebut tidak ditulis ke localStorage. Token login website mengikuti mekanisme autentikasi e-commerce yang sudah ada; preferensi tema disimpan lokal. Ini tidak mengubah arsitektur session/token website secara keseluruhan.

Tombol Privasi dan tab tersembunyi memask tampilan; kamera/unmounted views serta object URL dibersihkan. Melanjutkan memvalidasi sesi website lewat bootstrap. Request yang selesai setelah lock/pergantian akun ditolak oleh guard generasi, sehingga tidak dapat memunculkan data lama atau melanjutkan download laporan. Bila identitas berubah, state dan foto sementara akun sebelumnya dibuang.

Mask bukan penghapusan forensik RAM, logout server, atau PIN lokal baru. Browser/OS masih mengendalikan memori dan screenshot. Kelola keamanan perangkat dan akses origin website sesuai deployment.

## Persetujuan dan foto

Persetujuan pengambilan gambar/penyimpanan hasil harus disimpan sebelum capture. Upload foto membutuhkan pilihan `consents.uploadPhotos === true` di revisi aktif dan consent multipart eksplisit. Secara default foto disimpan hanya di RAM dan tidak diunggah. Setelah reload, hasil/titik yang sudah disimpan tetap tersedia, tetapi foto sementara tidak dapat dipulihkan.

Upload JPEG/PNG/WEBP dibatasi 8 MiB, minimal 16 piksel per sisi dan maksimal 20 megapiksel, satu frame, serta decode yang valid. Server melakukan pemeriksaan izin sebelum membaca/decode gambar, membersihkan metadata dan menulis ulang JPEG. `source_sha256` mengikat bytes sumber; `sha256` memverifikasi bytes hasil normalisasi. Nilainya dapat berbeda secara sah.

Berkas ditulis menggunakan ID acak dalam `MEOWSUREMENT_PRIVATE_ROOT`, mode file terbatas, di luar root upload publik. Database menyimpan nama berkas internal, bukan URL publik. API foto memeriksa owner/reviewer, expiry, tombstone, ukuran dan digest sebelum mengembalikan gambar. Path dan extension tidak berasal dari nama file customer. Tidak ada mount static atas direktori privat.

`local_*` hanya referensi metadata foto ephemeral di browser. ID tersebut tidak dapat dipakai untuk mengambil foto server atau mengekspor thumbnail persisten. Capture server tetap menyimpan koordinat/metode/provenans tanpa mengarang aset foto yang tidak diunggah.

## Retensi

Foto privat berlaku 30 hari sejak upload. Endpoint menolak foto kedaluwarsa segera berdasarkan waktu server. Job `expire-meowsurement-photos` berjalan setiap 60 menit pada worker scheduler yang diaktifkan, menghapus bytes kedaluwarsa serta mempertahankan tombstone/hash/audit dan hubungan history. Job dapat dijalankan melalui endpoint admin scheduler; jika scheduler dinonaktifkan, operator wajib menjadwalkannya sendiri.

DELETE oleh pemilik menghapus akses, menyimpan tombstone, dan mencoba menghapus bytes. Cleanup mengulangi penghapusan yang belum berhasil. Backup database/storage mempunyai retensi terpisah dan tidak otomatis terhapus oleh DELETE aplikasi.

Retensi foto tidak menghapus akun, profil, resep, landmark, hasil, review, atau audit. Pengelolaan retensi data lain mengikuti kebijakan toko/deployment, bukan perkiraan otomatis dari lama penyimpanan foto.

## Jaringan dan deployment

Respons API Meowsurement/profile memakai `Cache-Control: private, no-store, max-age=0`, `Pragma: no-cache`, dan variasi Cookie/Authorization. Service worker hanya menyimpan daftar aset statis; API/gambar/hasil privat tidak masuk cache. Entry pengukuran tidak memuat font eksternal, tracker storefront atau tombol share data pengukuran.

Gunakan HTTPS dan konfigurasi origin/CORS sesuai template backend. Database, volume foto, backup, log dan akun DBA mengikuti kontrol infrastruktur. Penyimpanan file/server pada implementasi ini tidak boleh disebut terenkripsi end-to-end; gunakan enkripsi disk/volume dan backup yang sesuai bila diperlukan. Alur customer membutuhkan jaringan untuk login, profil, katalog dan penyimpanan.

## Laporan dan audit

Ekspor PDF/CSV/JSON/print memerlukan konfirmasi serta audit server untuk revisi yang dipilih sebelum unduh/cetak. Foto default tidak disertakan; thumbnail membutuhkan consent revisi, ID foto yang benar-benar menjadi bukti sesi, masih tersedia, dan pilihan ekspor eksplisit. CSV menetralkan formula dan output cetak meng-escape teks.

Audit menyimpan aktor akun, tindakan, waktu server, sesi/revisi dan detail terbatas; tidak menyimpan bytes foto. Guard database mempertahankan append-only. Ini tidak melindungi dari administrator database yang mempunyai wewenang mengubah schema/trigger atau backup; akses DBA tetap bagian batas kepercayaan.

## Data lokal lama

Kode kompatibilitas vault lokal tetap berada di source tetapi tidak dipasang pada entry produksi. Tidak ada penghapusan IndexedDB atau unggah diam-diam. Bila pengguna sebelumnya menyimpan pasien lokal, pemilik dan consent harus dipetakan secara terpisah sebelum impor server. Rancangan SQL 0003 bukan alat pemindah backup lokal.

Bukti otomasi yang sudah dijalankan, termasuk ownership, immutable snapshots, consent foto, purge, konflik dan ekspor, dirangkum pada [VALIDATION](VALIDATION.md).
