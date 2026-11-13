# Meowsurement: menu pengukuran customer

Pembaruan 10 November 2026. Entry tetap `/meowsurement/`. Setiap sesi baru mengukur satu jenis; sesi lama tetap dapat dibuka dengan lingkup yang tersimpan.

## Rancangan layar

```text
Meowsurement                    Profil & resep | Privasi
Pengukuran baru | Riwayat saya

Pilih pengukuran Anda
[Ikon mata]          [Ikon buku]           [Ikon penggaris]
Jarak pupil jauh     Jarak pupil dekat    Jarak lensa ke mata

[Ikon kemiringan]    [Ikon kacamata]
Kemiringan lensa     Lengkungan frame

Profil & resep (dapat dibuka bila diperlukan)
```

Klik kartu → form khusus jenis tersebut → persiapan singkat dan persetujuan → foto dan penandaan titik → hasil sesuai lingkup. Tombol “Semua jenis pengukuran” kembali ke menu. Kartu tersusun mengikuti lebar layar, menjadi satu kolom pada ponsel sempit.

| Kartu | Field khusus | Foto |
| --- | --- | --- |
| Jarak pupil jauh | Arah pandang jauh, titik pupil dan garis tengah | Depan |
| Jarak pupil dekat | Jarak membaca, titik pupil dan garis tengah | Depan untuk membaca |
| Jarak lensa ke mata | Titik depan mata, belakang lensa, arah pandang | Samping kanan/kiri |
| Kemiringan lensa | Tepi lensa, garis tegak, kemiringan kepala yang benar-benar diukur beserta sumbernya | Samping kanan/kiri |
| Lengkungan frame | Pembacaan alat/metode pemeriksaan dan acuan sudut | Tiga perempat sebagai dokumentasi; foto biasa belum menghitung wrap |

Profil/resep, tanggal, dan pilihan sumber frame tetap tersedia. Jarak membaca hanya muncul untuk PD dekat. Pemeriksaan operator, mode operator, dan pilihan seluruh parameter tidak muncul pada form customer. Pemeriksaan profesional tetap terpisah pada halaman reviewer.

## Sumber ukuran frame dan validasi

```js
if (source === 'catalog') {
  // Wajib pilih produk dan varian aktif dengan A/B/DBL yang lengkap.
  // Kirim ID serta versi; server membaca ukuran katalog yang sebenarnya.
  payload = { product_id, variant_id, expected_spec_version, expected_profile_version };
} else if (source === 'manual') {
  // Produk/varian tidak diperlukan. A, B, DBL wajib angka positif.
  // ED kosong dikirim null, nilai yang diisi harus positif.
  payload = { manual_frame: { a, b, dbl, ed: ed || null, model }, expected_profile_version };
}
```

Sumber default adalah manual; tautan produk dengan `product_id` membuka pilihan katalog setelah kartu dipilih. Server menolak payload campuran, katalog tanpa varian/versi, manual tanpa A/B/DBL, dan nilai nol/negatif. Versi profil/katalog diperiksa untuk mencegah penggunaan data lama. Ukuran disalin ke snapshot sesi dan tidak dapat diganti melalui revisi; perubahan frame memerlukan sesi baru.

**A = lebar mendatar satu lensa, B = tinggi tegak satu lensa, DBL = jarak antar lens box**, mengikuti konvensi optik dan data existing. Label tidak dibalik menjadi A=tinggi/B=lebar. [Referensi pengukuran Essilor](https://www.essilorpro.com/content/dam/essilor-pro/visioffice/Visioffice%20Measurement%20FAQ.pdf). ED adalah diameter efektif bentuk lensa; opsional dan tidak ditebak dari diagonal kotak A/B. Dimensi manual disimpan dua angka desimal. Backend memakai FK nullable dan `spec_scope='manual'`; guard database melarang ID katalog pada sumber manual, dan mewajibkan ID produk/varian pada sumber katalog.

## Ukuran frame sebagai acuan foto

Alur customer sekarang **tanpa kartu atau benda pembanding tambahan**. Ukuran diambil otomatis dari snapshot frame sesi, baik katalog maupun manual:

- Foto depan (PD jauh/dekat): **lebar satu lensa A**. Tandai ujung kiri dan kanan lensa yang sama pada bagian terlebar; jangan memakai lebar seluruh frame, DBL, atau 2A + DBL.
- Foto samping (jarak lensa ke mata/kemiringan): **tinggi satu lensa B**. Tandai ujung atas dan bawah lensa yang sama; jangan memakai A atau panjang tangkai untuk menskalakan foto samping.

Panel **Ukuran frame sebagai acuan** hanya menampilkan nilai sesi; tidak ada pemilih marker atau input panjang yang harus diketik ulang. `frameScaleSpec` menyimpan metode `frame`, `scaleSource=session_frame`, dimensi A/B, panjang nyata, dan sumber acuan. Backend memeriksa dimensi/panjang terhadap snapshot sesi sehingga panjang skala tidak dapat diganti lewat payload.

Customer mengonfirmasi frame yang dipakai sesuai ukuran sesi, kedua ujung terlihat utuh, serta bagian acuan sejajar bidang ukur dan kamera. Dua titik hanya menentukan skala bidang; tidak mengoreksi perspektif, frame melengkung, atau perbedaan kedalaman mata/lensa. Nilai ukuran yang hilang tidak ditebak; foto terlalu miring/terpotong perlu diambil ulang. Hasil tetap estimasi fitting dan memerlukan review.

Saat foto lama dengan acuan marker atau ukuran bebas dibuka untuk diedit, titik pengukuran anatomis tetap tersedia, tetapi titik skala dan konfirmasi lama tidak dipakai ulang sebagai acuan frame. Customer menandai ulang dua ujung frame. Revisi historis tetap tersimpan. Mode petugas/legacy tetap dapat membaca metode lama.

Pengukuran kemiringan tetap memerlukan arah tegak yang diketahui dan nilai kemiringan kepala beserta sumbernya. Keduanya tidak diturunkan atau dianggap nol dari A/B. Wrap tetap memakai hasil alat/pemeriksaan; bukan perkiraan sudut dari satu foto.

## Kamera dan komponen

### Panduan ilustrasi per tahap

`MeasurementIllustrationGuide` menyediakan gambar SVG responsif pada Persiapan, panduan yang dapat dibuka pada Foto, dan contoh penempatan titik pada editor. Tahap panduannya: **Contoh foto → Acuan frame → Tandai titik → Periksa & simpan**. Tombol bernomor menjelaskan posisi masing-masing titik dan menyorot titik contoh pada ilustrasi; panduan tidak menambahkan koordinat ke foto customer.

Gambar mengikuti jenis pengukuran, sisi foto kanan/kiri, dimensi acuan frame, dan garis tengah sesi. PD jauh/dekat memperlihatkan pupil OD/OS dan garis tengah; vertex memperlihatkan depan mata, belakang lensa, serta arah pandang; kemiringan lensa memperlihatkan ujung atas/bawah lensa dan acuan tegak. Dua ujung lebar lensa A atau tinggi lensa B diberi nomor sesuai titik acuan pada editor. Jarak membaca mengikuti nilai sesi. Untuk wrap, panduan hanya memberikan contoh foto tiga perempat dan pencatatan hasil alat; tidak menawarkan titik kamera untuk mengarang hasil sudut.

Ilustrasi merupakan contoh posisi, bukan skala fisik atau hasil pengukuran customer. Foto selfie yang dicerminkan harus diperiksa sebelum menandai OD/OS. Gambar tetap terlihat pada tema terang/gelap dan dapat diperbesar oleh browser tanpa pecah. Tahap kamera tidak menyisipkan panduan di antara preview dan tombol foto.

```text
CustomerMeowsurementApp
├─ MeasurementDashboard                  Lima kartu ikon/judul
├─ CustomerMeasurementSetup              Satu jenis + sumber frame
│  └─ frameInputPayload                  Validasi dan payload sumber
└─ CustomerSession
   ├─ CustomerPreparation                Panduan singkat + persetujuan
   │  └─ MeasurementIllustrationGuide    Contoh foto, acuan A/B, titik, simpan
   ├─ CapturePanel → CameraCapture        Posisi foto sesuai jenis
   ├─ CaptureEditor
   │  ├─ CustomerScaleFields             Acuan A/B otomatis dari sesi
   │  └─ CustomerPhotoChecks             Konfirmasi relevan
   └─ ResultsPanel                       Hasil hanya sesuai lingkup
```

```text
┌──────────────────────────────────┐
│          PREVIEW KAMERA          │
│          Panduan posisi          │
├──────────────────────────────────┤
│       [ Ambil foto ] [Hentikan]   │
└──────────────────────────────────┘
Pilih kamera / pengambilan otomatis
```

Preview dan tombol berada dalam wrapper `.of-camera-station`; `.of-camera-controls` langsung setelah preview, tanpa panel pemeriksaan di antaranya. Tombol minimal tinggi 48 px, membesar mengikuti ruang pada mobile, dan memiliki `touch-action: manipulation`. Kamera tetap memerlukan izin browser. Pengambilan burst yang sudah ada dipertahankan untuk kualitas sampel.

## Migrasi dan pengujian

Head baru `20261110_0004`, menurunkan kewajiban `meowsurement_sessions.product_id` dan memperbarui dua trigger sesi tanpa menulis ulang migrasi 0003, tanpa menghapus tabel/data. ED pada kolom SQL sudah nullable; validasi admin/customer diperbarui. Ikuti [runbook](RUNBOOK.md) sebelum menjalankan backend baru. SQL incremental: `backend/sql/004_optional_customer_frame.sql`. Migrasi pada database toko tidak dijalankan otomatis oleh halaman web.

Regresi mencakup kartu/lingkup field, sumber manual versus katalog, ED kosong, batas angka, payload campuran, snapshot immutable, CHECK/FK SQLite, definisi guard dan replay SQL offline. SQLite dan SQL offline tidak menggantikan pengujian migrasi pada server MySQL target.
