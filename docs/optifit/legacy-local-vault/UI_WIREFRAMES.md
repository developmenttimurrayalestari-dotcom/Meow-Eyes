> Arsip implementasi vault lokal sebelumnya. Dokumen ini tidak menjadi petunjuk alur customer saat ini. Gunakan [dokumentasi aktif](../README.md).

# Meowsurement — rancangan layar

Dokumen rancangan ini disusun sebelum implementasi antarmuka. Rute modul adalah
`/meowsurement`. Seluruh layar memakai bahasa Indonesia, label OD/OS yang
eksplisit, kontrol sentuh besar, dan tema terang/gelap. Data contoh tidak dimuat
pada aplikasi produksi.

## Kerangka aplikasi

Header menampilkan nama Meowsurement, nama optik, indikator “Tersimpan
terenkripsi di perangkat”, status jaringan, nama/peran pengguna, pilihan tema,
dan tombol **Kunci**. Navigasi desktop di sisi kiri berubah menjadi baris
navigasi pada layar kecil. Menu utama: **Pasien**, **Riwayat**, **Review**,
**Pengaturan**, dan **Audit** sesuai peran. Informasi pasien tidak ditempatkan
pada judul tab, URL, localStorage, atau notifikasi browser.

Pada saat terkunci, seluruh tampilan pasien dilepas dari DOM dan kamera
dihentikan. Kunci otomatis bekerja setelah tidak ada aktivitas dan ketika tab
disembunyikan. Perlindungan thumbnail recent-apps sistem operasi tidak dapat
dijamin oleh website; antarmuka tidak mengklaim kemampuan native tersebut.

## 1. Penyiapan ruang kerja lokal

Urutan vertikal: nama optik; nama administrator; username; PIN/frasa sandi;
konfirmasi rahasia; penjelasan penyimpanan lokal; persetujuan memahami cadangan;
tombol **Buat ruang kerja terenkripsi**. Tidak ada akun atau password bawaan.
Panjang dan kekuatan kredensial mengikuti validasi vault. Kesalahan ditampilkan
dekat form tanpa mencatat rahasia pada log.

Pilihan **Pulihkan cadangan terenkripsi** tersedia terpisah, dengan pemilihan
berkas dan frasa sandi cadangan. Proses ini memerlukan tindakan sadar pengguna.

## 2. Buka kunci

Logo/nama modul; username yang tersedia; input rahasia; tombol **Buka kunci**;
status jeda percobaan jika ada; penjelasan bahwa kehilangan kunci tidak dapat
diatasi dengan membaca database terenkripsi. Form tidak menampilkan daftar
pasien sebelum pengguna berhasil masuk.

## 3. Daftar pasien

Judul **Pasien**, kolom pencarian lokal, tombol **Tambah pasien**, lalu kartu
atau tabel berisi nomor rekam, nama, dan tanggal pemeriksaan terakhir. Status
kosong menawarkan pendaftaran pasien pertama, tanpa memasukkan data dummy.
Pencarian tidak memanggil server.

Form pasien mewajibkan nama lengkap dan tanggal pemeriksaan. ID dan nomor
rekam dibuat aplikasi. Kolom opsional: tanggal lahir, jenis kelamin, telepon,
alamat, email, pekerjaan, keluhan, catatan, dan foto profil dengan persetujuan
tersendiri. Jika akun Meow Eyes tersedia, pengguna memilih tindakan **Gunakan
profil akun**; aplikasi memperlihatkan isian hasil salinan untuk diperiksa.

## 4. Detail pasien dan riwayat

Header berisi nama, nomor rekam, tanggal pemeriksaan, **Ubah data**, dan **Sesi
baru** sesuai peran. Bagian data pasien dan riwayat sesi ditampilkan terpisah.
Setiap sesi memperlihatkan tanggal, operator, versi algoritma, status, dan
tombol **Buka**. Administrator mempunyai tindakan hapus permanen dengan alasan
dan konfirmasi nomor rekam; tindakan ini tidak menyerupai tombol biasa.

## 5. Data sesi: resep dan frame

Stepper: **Data → Persiapan → Foto → Titik & kalibrasi → Hasil → Review**.
Form resep memiliki card Mata Kanan (OD) dan Mata Kiri (OS), dengan SPH, CYL,
Axis, dan ADD. Keterangan tetap: nilai ini dimasukkan dari resep; kamera tidak
mengukur kekuatan lensa. Transpose cylinder, bila dipilih, menjadi tampilan
turunan dan tidak menimpa resep asli.

Form frame berisi merek/model, A, B, DBL, dan ED dalam mm. Definisi tiap ukuran
tersedia melalui bantuan yang dapat dibuka. Card **Frame PD = A + DBL** muncul
sebagai nilai turunan. Jarak kerja near PD diisi terpisah; tidak mengubah atau
menggantikan protokol distance PD.

## 6. Persiapan dan persetujuan

Checklist memuat posisi frame/temple/nose pad, natural head posture, pupil dan
frame terlihat, rambut/refleksi, cahaya, kebersihan kamera, main camera,
ketinggian kamera, larangan ultra-wide, zoom, dan referensi kalibrasi. Tombol
**Semua persiapan siap** hanya mencentang persiapan teknis. Persetujuan pasien
tetap menjadi checkbox terpisah.

Pilihan foto: **Simpan terenkripsi untuk review** atau **Hapus foto setelah
landmark tersimpan**. Tampilan menjelaskan pengaruh penghapusan terhadap review
gambar. Foto tidak diunggah secara default. **Lihat contoh posisi** menampilkan
panduan diagram/grafik sederhana; **Batalkan** menghentikan alur tanpa membuka
kamera. Disclaimer alat bantu fitting tetap terlihat.

## 7. Wizard foto

Posisi ditampilkan sebagai daftar: frontal distance, tiga-perempat kiri,
tiga-perempat kanan, lateral kanan, lateral kiri, serta frontal near opsional.
Setiap posisi mempunyai instruksi khusus, overlay panduan, crosshair, tombol
**Mulai kamera**, **Ambil rangkaian foto**, **Ambil ulang**, dan **Selesai**.
Permission kamera baru diminta setelah klik dan persetujuan terpenuhi.

Indikator yang dihitung dari gambar meliputi pencahayaan, ketajaman, dan
stabilitas rangkaian. Indikator yang belum dapat diukur pada perangkat atau
algoritma saat ini diberi label **Belum tersedia — periksa operator**. Tidak
ada nilai jarak, head pose, kedipan, atau depth sensor palsu. Kesalahan kamera
memiliki pesan yang dapat ditindaklanjuti dan pilihan foto lokal yang diambil
dengan protokol yang sama.

Rangkaian mempertahankan beberapa frame nyata, termasuk skor dan pemilihan
gambar, agar pengulangan dapat diperiksa. Perhitungan repeatability hanya
menggunakan frame yang sudah ditandai serta memenuhi syarat; satu frame tidak
ditampilkan seolah hasil beberapa pengukuran.

## 8. Titik dan kalibrasi

Pemilih posisi dan sampel berada di atas gambar. Panel gambar mendukung zoom,
pan, magnifier, pemilihan titik, geser atau tap untuk menempatkan titik,
undo/redo, reset ke titik awal, dan perbandingan sebelum/sesudah. OD/OS selalu
mengacu pada pasien, bukan sisi layar.

Panel kanan/bawah berisi daftar titik yang perlu ditandai dan metode kalibrasi.
Marker: empat sudut dan ukuran fisik yang diketahui. Referensi frame: dua titik
bagian yang diketahui beserta panjang fisik dan konfirmasi bidang/perspektif.
Kalibrasi gagal tidak menghasilkan nilai final dalam mm.

Bagian lateral membedakan apex kornea, permukaan belakang lensa, arah pandang,
sumbu lensa, serta referensi vertikal. Koreksi pantoscopic menyimpan head pitch
dan sumbernya. Wrap angle menggunakan input dari alat/metode referensi manual
sampai rekonstruksi multi-view mempunyai kalibrasi dan validasi yang memadai.

Sebelum **Simpan koreksi**, operator memilih alasan: landmark salah, refleksi,
rimless, mata tertutup, marker tidak tepat, posisi lensa, atau lainnya. Data
awal tetap berada pada revisi sebelumnya; perubahan baru tidak menimpanya.

## 9. Hasil dan revisi

Card terpisah menampilkan distance PD, near PD/jarak kerja, wrap, vertex
distance, pantoscopic, frame, resep, confidence, dan catatan. Hasil kanan/kiri
ditampilkan eksplisit. Confidence selalu disertai metode, faktor kualitas,
alasan penurunan, dan keterangan bukan probabilitas ketepatan klinis. Jika
ketidakpastian tidak dapat dihitung, tampilkan **Tidak tersedia**.

Nilai belum lengkap diberi tanda **Belum diukur**, bukan nol. Layar menampilkan
Frame PD serta decentration masing-masing lensa dari monocular PD. Konvensi
tanda pantoscopic positif adalah bagian bawah lensa lebih dekat ke pipi.
Riwayat revisi menyediakan pilihan versi, operator, waktu, alasan, dan
perbandingan tanpa membuat data awal dapat diedit.

## 10. Review

Reviewer melihat data, hasil, kualitas, metode, foto yang diizinkan, dan
riwayat revisi. Tindakan tersedia: **Setujui** atau **Perlu diukur ulang**,
beserta catatan wajib. Pemeriksaan profesional/manual harus dinyatakan secara
eksplisit ketika kebijakan kualitas mengharuskannya. Reviewer tidak mengubah
data asli. Revisi setelah review memerlukan proses review baru.

## 11. Laporan dan ekspor

Dialog ekspor memuat PDF, CSV, JSON, atau cetak; nomor laporan; status; checkbox
persetujuan mengekspor data pasien; dan thumbnail opt-in hanya ketika persetujuan
foto laporan tersedia. Draft dan hasil yang belum disetujui tetap berlabel
status tersebut pada dokumen. Ekspor dicatat pada audit setelah tindakan
pengguna. Tidak ada ekspor otomatis ketika halaman hasil dibuka.

## 12. Pengaturan, pengguna, cadangan dan audit

Administrator mengelola identitas optik, akun/peran lokal, kunci otomatis,
retensi foto/data, konfigurasi referensi kalibrasi, dan cadangan terenkripsi.
Penghapusan berdasarkan retensi selalu memperlihatkan tindakan serta akibatnya.
Pengguna mempunyai alur ganti kredensial yang tidak menampilkan kunci dekripsi.
Audit menampilkan jenis tindakan, aktor, waktu, target, alasan, dan status
integritas rantai. UI tidak memberikan editor atau tombol hapus audit biasa.

## Keadaan umum

- Loading: tombol terkait dinonaktifkan dengan label tindakan yang berjalan.
- Error: teks ringkas berbahasa Indonesia tanpa data rahasia/stack trace.
- Offline: fungsi lokal tetap tersedia; layanan akun/server yang memerlukan
  koneksi ditandai secara eksplisit.
- Tidak berizin: aksi tidak ditawarkan dan service vault tetap menolak mutasi.
- Tidak ada kamera/depth: mode foto/manual tetap tersedia sesuai protokol.
- Data belum lengkap: dapat disimpan sebagai draft, tetapi tidak disamakan
  dengan hasil yang disetujui.
