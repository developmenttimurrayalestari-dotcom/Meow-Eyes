# Validasi alur customer — 10 November 2026

Rancangan dan struktur komponen: [CUSTOMER_FLOW.md](CUSTOMER_FLOW.md).

| Pemeriksaan | Hasil |
| --- | --- |
| Jest `src/optifit` dan `FrameSpecificationEditor.test.jsx` | 11 suite, 108 tes lulus |
| Pytest Meowsurement, manual frame, schema, migrasi opsional, dan migrasi umum | 55 tes lulus |
| `npm run build` | Berhasil, termasuk app shell Meowsurement |
| Edge headless 390×844, API mock dan kamera canvas simulasi | Lulus, tidak ada page error |
| `git diff --check` dengan pengenalan CRLF | Lulus pada berkas tracked dalam cakupan |

Browser memeriksa lima kartu tanpa form awal, tidak ada overflow horizontal di menu mobile, input manual tanpa produk dan tanpa ED, PD dekat dengan jarak membaca, vertex tanpa jarak membaca, pemilihan katalog/varian tanpa ED, persetujuan foto, capture burst, pembukaan penandaan, kontrol langsung di bawah preview dengan tinggi minimal 48 px, dan metadata yang tidak mengklaim pemeriksaan operator bagi customer.

Artefak lokal QA tersedia di `backend/private/meowsurement-flow-browser-report.json`, serta `meowsurement-menu-mobile.png`, `meowsurement-manual-mobile.png`, dan `meowsurement-camera-mobile.png`. Semuanya memakai data QA dan API mock; tidak menulis database toko.

Tes backend menjalankan transaksi relasional SQLite, validasi HTTP, FK/CHECK, snapshot immutable, sumber frame yang saling eksklusif, serta replay SQL offline.

Atas permintaan pengguna pada 10 November 2026, migrasi kemudian diterapkan langsung pada MySQL toko dari `20261109_0003` ke **`20261110_0004`**. Backend lokal dihentikan sementara; backup lengkap dibuat di `backend/private/backups/meowsurement-before-0004-20261110T040509Z.sql` (693.518 byte). Audit penuh lulus: 117 trigger, 123 aturan baris, tanpa issue. Jumlah baris seluruh tabel sebelum/sesudah sama; tetap 79 tabel aplikasi. Backend dinyalakan kembali pada port 8001 dan `/api/health/ready` mengembalikan `ok: true`, `reason: ready`. Laporan perbandingan ada di `backend/private/backups/meowsurement-after-0004-20261110T040509Z.json`. Backup belum diuji melalui restore; audit ini tidak menguji seluruh transaksi aplikasi pada MySQL.

Build masih menghasilkan peringatan dependency expression dinamis, source map MediaPipe yang tidak tersedia, dan database Browserslist yang lama. Peringatan tersebut tidak menghentikan build.

## Panduan ilustrasi

Pembaruan panduan bergambar diuji dengan 22 tes frontend dalam empat suite (panduan ilustrasi, aplikasi customer, field pembanding, dan kamera); semuanya lulus. Build produksi berhasil. Edge headless dengan API/kamera simulasi memeriksa ilustrasi kelima jenis pengukuran pada mobile 390×844, tampilan desktop 1280×900 dan tema gelap, navigasi tahap, pemilihan nomor titik, pergantian metode pembanding, serta memastikan contoh panduan tidak memasukkan koordinat ke foto customer. Tidak ada page error atau penulisan database toko. Screenshot QA tersedia di `backend/private/meowsurement-guide-*-mobile.png` dan `meowsurement-guide-pd-desktop-dark.png`.

## Alur terbaru: acuan frame otomatis

Alur customer berikutnya mengganti pilihan pembanding dengan ukuran frame sesi: A untuk foto depan dan B untuk samping. Seluruh 116 tes frontend dalam 13 suite lulus; 13 tes backend Meowsurement/manual-frame/acuan-frame lulus menggunakan SQLite. Regresi memeriksa nilai A/B yang sesuai, tanpa fallback ukuran fiktif, penolakan panjang/dimensi yang diubah pada payload acuan sesi, serta reset titik skala dan konfirmasi foto lama saat beralih metode. Build berhasil dengan peringatan dependency yang sama. Browser dengan API/kamera simulasi memastikan acuan depan 52 mm dan samping 40 mm terisi otomatis, tidak ada pemilih marker atau input panjang ulang, panduan memakai dua titik frame, serta kontrol capture tetap menempel pada preview. Tidak ada page error atau perubahan database toko. Tidak diperlukan migrasi skema baru; backend yang berjalan tanpa reload perlu dimulai ulang untuk memuat validasi baru.
