# Layar dan flow Meowsurement terintegrasi

> Pembaruan 10 November 2026: [menu kartu, form khusus, frame manual, ED opsional, dan kamera](CUSTOMER_FLOW.md). Head terbaru `20261110_0004`; SQL 004 melengkapi migrasi 0003 di bawah. Sesi manual memakai `product_id`/`variant_id` NULL dan `spec_scope=manual`.

## Profil customer — `/profile`

Informasi akun tetap menggunakan nama/email Meow Eyes. Form identitas berisi telepon, tanggal lahir, gender, alamat; form resep berisi tanggal pemeriksaan, tabel OD/OS dengan SPH/CYL/AXIS/ADD, PD opsional, dan catatan. Status di atas form menjelaskan data yang belum lengkap. Tombol Simpan profil & resep dapat menyimpan draft. Tombol Lanjut ke Meowsurement aktif sesudah data wajib lengkap dan tersimpan.

Tujuan produk/varian yang dibuka sebelumnya dipertahankan melalui returnTo lokal tervalidasi. Tidak ada form organisasi, administrator lokal, operator, atau tambah pasien.

## Frame admin — aksi Meowsurement pada katalog produk

Satu dialog memuat spesifikasi dasar: A, B, DBL, ED, panjang tangkai, simetris, aktif, dan catatan sumber. Tiap varian memiliki pilihan mengikuti spesifikasi produk atau override lengkap. Semua ukuran berlabel mm. Form menjelaskan kelengkapan sebelum aktivasi dan menolak penyimpanan bila data awal gagal dibaca atau versi telah berubah.

## Detail produk

Blok Meowsurement menampilkan dimensi efektif varian aktif dan status kesiapan. Tombol membawa ID produk serta ID varian ke entry pengukuran dengan navigasi dokumen penuh. Frame tanpa spesifikasi tetap terlihat sebagai belum siap; ukuran tidak dibuat dari teks size.

## Entry pengukuran — `/meowsurement/`

Header Meow Eyes menampilkan link profil/resep, tema, dan tombol Privasi. Setelah login/gate profil, kartu resep terisi otomatis dan hanya dibaca. Katalog frame menyediakan pencarian, pilihan produk/varian, ukuran efektif, dan pagination. Customer menentukan tanggal serta parameter pengukuran, kemudian membuat sesi.

## Sesi pengukuran

Empat tahap: Profil & frame; Persiapan; Foto & titik; Hasil & review. Resep dan dimensi adalah snapshot sesi. Riwayat revisi dapat dipilih dan revisi lama bersifat baca saja. Customer dapat mengubah lingkup/notes dan kondisi yang relevan dengan alasan revisi, mengambil/anotasi sampel, mencatat alat referensi, mengajukan review, dan mengekspor.

Persetujuan menyimpan hasil terpisah dari upload foto privat. Teks menjelaskan kapan foto hanya tersedia pada dokumen yang sedang terbuka. Pilihan thumbnail laporan default mati. Tidak ada tombol membuat pasien atau akun baru di dalam modul.

## Riwayat saya

Daftar hanya memuat sesi customer terautentikasi, frame, tanggal, status, dan akses revisi. Pagination memungkinkan riwayat lebih dari 15 sesi. Data diambil dari backend, sehingga reload memperoleh kembali hasil yang sudah disimpan.

## Review dashboard — `/admin/meowsurement`

Tabel customer, frame, tanggal/revisi, status, dan tombol Buka review. Filter status dan pagination 15 sesi tersedia. Entry review menggunakan login admin/staf website yang sama. Petugas tidak diminta melengkapi resep pribadinya; form edit customer dimatikan. Keputusan harus ditujukan ke revisi aktif dengan catatan dan bukti sesuai policy server.

## Kondisi gagal

| Kondisi | Tampilan/aksi |
| --- | --- |
| Belum login / sesi berakhir | Login website dengan tujuan lokal terjaga |
| Profil belum lengkap | Halaman profil dan daftar field yang harus diisi |
| Frame belum diaktifkan/lengkap | Pesan ukuran kurang; Mulai pengukuran tidak aktif |
| Versi data berubah | Pesan konflik; reload eksplisit sebelum menyimpan |
| Jaringan terputus | Pesan bahwa perubahan belum tersimpan; tidak ada fallback lokal diam-diam |
| Tab disembunyikan | Data dimask, kamera berhenti; lanjut memeriksa sesi akun |
| Foto RAM sudah hilang setelah reload | Hasil/landmark tetap tersedia; ambil ulang jika perlu koreksi visual |
| Tidak mempunyai izin sesi/review | Akses ditolak backend; ID di URL tidak memberi izin |
