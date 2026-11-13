# OptiFit — protokol validasi lapangan sebelum klaim akurasi

**Status: protokol disiapkan; studi manusia, pembandingan alat referensi, dan validasi antar-perangkat belum dilaksanakan.** Dokumen ini tidak berisi hasil pasien, toleransi klinis yang diasumsikan, sertifikasi, atau angka akurasi. Pengujian software dan geometri sintetis harus dilaporkan terpisah dari studi ini.

Versi yang dinilai harus dicatat dengan versi aplikasi, hash build, versi `optifit-local-geometry-1.0.0`, versi protokol, konfigurasi skrining, serta tanggal. Dokumen ini melengkapi [DESIGN.md](DESIGN.md) dan [MEASUREMENTS.md](MEASUREMENTS.md). Pengelola studi dan tenaga optik yang bertanggung jawab melengkapi keputusan yang masih terbuka sebelum perekrutan.

## 1. Tujuan dan ruang lingkup

Evaluasi apakah metode manual dan kamera dengan bantuan petugas memberikan hasil yang sesuai untuk tujuan fitting yang ditetapkan, pada perangkat, populasi, kondisi frame, dan prosedur yang benar-benar diuji. Penggunaan tanpa petugas, pengukuran kekuatan resep dari foto, rekonstruksi wrap otomatis, dan generalisasi ke semua ponsel tidak termasuk ruang lingkup implementasi saat ini.

Tetapkan populasi dan pengecualian sebelum studi. Jangan menganggap hasil pada orang dewasa berlaku pada anak, pasien yang tidak dapat mempertahankan fixation, atau kondisi mata yang tidak terwakili. Tinjauan etika, persetujuan partisipan, kewenangan petugas, privasi dan kebutuhan regulasi mengikuti tempat studi dan tujuan penggunaan yang dipilih. Persetujuan di aplikasi untuk mengambil foto tidak otomatis menggantikan persyaratan pelaksanaan studi.

Kamera menghasilkan proyeksi pada bidang kalibrasi. Nama parameter dan objek ukur harus sama pada OptiFit dan alat pembanding. Definisi profesional membedakan PD jauh, near centration pada bidang frame dan jarak kerja, serta jarak apex kornea ke permukaan belakang lensa. Lihat [ABDO, OA Corner Part 36](https://www.abdo.org.uk/news/oa-corner-part-36/).

## 2. Definisi hasil dan alat referensi

| Hasil | Kondisi dan acuan yang harus cocok | Bukti referensi yang dicatat |
| --- | --- | --- |
| Distance mono-PD OD/OS | Target jauh, posisi kepala natural, garis tengah yang didefinisikan, bidang pupil atau proyeksi frame dijelaskan | Pembacaan independen tiap mata oleh petugas kompeten; ID alat/metode, resolusi, kalibrasi dan bidang referensi |
| Near mono-PD / centration OD/OS | Target nyata pada jarak kerja tercatat; titik nol jarak kerja dan bidang pengukuran konsisten | Alat/metode near yang sesuai dan jarak kerja aktual; bukan pengurangan konstanta dari distance PD |
| VD kanan/kiri | Frame dalam posisi pemakaian; apex kornea ke permukaan belakang lensa pada ray/referensi yang sama | Alat/metode VD yang dapat mengidentifikasi kedua permukaan tersebut; bukan rim depan frame |
| Pantoscopic kanan/kiri | Posisi kepala, vertikal acuan, arah positif dan prosedur head pitch dicatat | Alat sudut/metode referensi sesuai; raw, kontribusi head pitch, dan corrected disimpan terpisah |
| Wrap kanan/kiri | Bidang acuan, per-sisi versus total, serta arah tanda ditetapkan | Pembacaan manual alat/metode wrap; kemampuan kamera 3D belum tersedia |
| A, B, DBL, ED dan decentration | Boxing frame yang sama, unit mm, ukuran kiri/kanan dan asumsi simetri jelas | Alat ukur frame atau tracer dengan prosedur terverifikasi; ED tidak diganti dengan A atau diagonal tebakan |

Inventaris alat memuat produsen/model, nomor seri atau ID lokal, tanggal dan status kalibrasi, resolusi, ketidakpastian dari sertifikat bila tersedia, prosedur zero/check sebelum sesi, petugas, dan catatan drift/kerusakan. Instrumen yang belum diketahui ketidakpastiannya jangan disebut sebagai nilai benar tanpa kualifikasi. Bila acuan merupakan prosedur manual, ukur juga repeatability dan variasi antar-petugas prosedur itu.

Jangan membandingkan proyeksi pupil pada marker frame dengan pembacaan bidang kornea seolah keduanya objek ukur yang identik. Bila tidak dapat disamakan, tetapkan analisis keterbatasan metode yang berbeda; jangan menyamarkan selisihnya sebagai error algoritma murni atau memasukkan offset populasi.

## 3. Keputusan yang dipraregistrasikan

Isi dan setujui tabel berikut sebelum melihat data konfirmatori. Nilai yang belum diputuskan tetap **belum ditetapkan**, bukan nol atau nilai contoh.

| Keputusan | Pemilik keputusan dan isi yang diperlukan |
| --- | --- |
| Tujuan penggunaan | Penanggung jawab optik: parameter wajib, jenis dispensing/lensa, populasi dan batas pemakaian |
| Toleransi per-parameter | Penanggung jawab optik dan reviewer studi: batas bias, agreement individual dan repeatability dalam mm/derajat, alasan kebutuhan fitting, serta kaitan dengan ketidakpastian referensi |
| Endpoint utama | Statistikawan dan penanggung jawab: metrik utama, unit analisis, OD/OS, protokol distance/near, manual/kamera, dan aturan beberapa endpoint |
| Ukuran sampel | Perhitungan dari presisi interval atau power yang dipilih, varians pilot yang relevan, korelasi repeated measures, subgroup dan allowance kegagalan |
| Rencana pengulangan | Jumlah subjek, sesi/hari, operator, perangkat dan reset posisi yang benar-benar independen; bedakan dari burst frame |
| Kegagalan dan eksklusi | Kondisi teknis gagal, pengecualian terencana, jumlah percobaan ulang, semua penyebut, dan penanganan missing data |
| Analisis statistik | Metode interval, agreement, repeated measures, subgroup, proportional bias, dan sensitivity analysis |
| Gate penerimaan | Kriteria lulus untuk setiap parameter/perangkat/protokol; ketidakpastian yang masih diperbolehkan; tindakan jika satu gate gagal |
| Pembekuan versi | Hash build, parameter algoritma, checklist, metode kalibrasi, instruksi operator, dan pencatatan setiap perubahan |

Pilot dapat dipakai untuk memperkirakan varians dan memperbaiki prosedur, tetapi data yang dipakai untuk menyetel threshold tidak boleh diperlakukan sebagai holdout konfirmatori independen. Simpan pemisahan pilot dan konfirmatori. Rencanakan ukuran sampel berdasarkan subjek independen dan ketepatan estimasi yang dibutuhkan. Lima foto satu burst tidak setara lima subjek. Tidak ada jumlah subjek universal yang membuktikan kelayakan semua parameter/perangkat.

## 4. Rancangan pengumpulan berpasangan

1. Jelaskan studi dan catat consent. Gunakan ID studi pseudonim. Simpan daftar identitas terpisah sesuai prosedur tempat studi; ekspor foto nonaktif secara default.
2. Setel frame ke posisi pemakaian, pastikan temple/nose pad sesuai, catat model, bahan, ukuran dan jenis lensa. Pemeriksaan fitting sebelum pengukuran mengikuti praktik yang dibahas dalam [ABDO CPD 2024](https://www.abdo.org.uk/wp-content/uploads/2024/06/DO-July-_-August-2024-CPD-with-References.pdf).
3. Catat objek ukur, target jauh/dekat, jarak kerja, marker nyata beserta ukuran yang telah diperiksa, posisi bidang referensi, jenis kamera dan kondisi cahaya. Verifikasi label OD/OS bersama partisipan/petugas.
4. Urutan OptiFit dan referensi diacak atau diseimbangkan sesuai rencana. Pembaca referensi tidak melihat nilai OptiFit; operator OptiFit tidak menggeser landmark untuk mendekati nilai referensi. Simpan timestamp keduanya.
5. Ambil lima frame dan pertahankan tiga berdasarkan skrining gambar. Anotasi dan kalibrasi setiap foto secara terpisah; simpan semua analisis pemilihan, hash foto, kandidat awal, koreksi dan alasan. Jika gambar identik atau titik disalin tanpa pemeriksaan, jangan hitung sebagai pengulangan independen.
6. Ulangi dengan reset posisi kamera/marker dan penempatan frame sesuai rencana studi. Uji sesi/hari berbeda secara terpisah dari variasi dalam satu burst.
7. Operator lain melakukan penempatan ulang dan anotasi tanpa melihat hasil sebelumnya. Bedakan variasi pengambilan, variasi anotasi pada foto yang sama, variasi pengaturan frame, dan variasi alat referensi.
8. Simpan hasil gagal beserta alasan, bukan hanya hasil yang tampak baik. Catat retake, fallback manual, durasi pekerjaan dan kesulitan operator.

Pengulangan pembacaan manual wrap menguji alat/prosedur manual dan pencatatan OptiFit. Hasil itu tidak memvalidasi rekonstruksi wrap kamera yang belum ada.

## 5. Matriks kondisi yang harus diwakili

| Kelompok | Variasi yang direncanakan dan dicatat |
| --- | --- |
| Perangkat | Model ponsel/tablet, OS dan versi browser, kamera/lensa aktual, resolusi, zoom yang dilaporkan, kamera belakang/depan, portrait/landscape |
| Operator | Pengalaman, pelatihan, penempatan ulang, operator pengambil foto versus pemberi landmark, reviewer independen |
| Partisipan | Rentang geometri wajah/PD yang relevan, asimetri, warna kulit dan iris yang beragam, variasi area kelopak/bulu mata; kategori tidak diasumsikan dari ras |
| Frame | Full rim, half rim, rimless, tipis/tebal, metal/plastic/mixed, transparan/mengilap, bentuk dan lengkung yang bervariasi |
| Lensa | Demo lens versus lensa resep, tint/refleksi/coating, tepi atau permukaan belakang yang sulit dilihat; kondisi yang tidak dapat diukur dicatat |
| Cahaya | Merata, redup, terang, bayangan dan backlight; jenis sumber, arah dan ukuran objektif bila alat tersedia |
| Penghalang | Rambut, refleksi, kedipan, kelopak, area pupil sebagian tertutup dan marker terpotong |
| Posisi | Head yaw/pitch/roll, kemiringan ponsel, jarak kamera, posisi marker, perubahan depth antara marker dan area ukur |
| Alur | Mode manual, kandidat pupil yang dikoreksi, impor foto, online/offline, kamera ditolak, tab ditutup dan pengambilan ulang |

Kondisi terlarang seperti marker terpotong atau mata tidak terlihat menjadi pengujian **penolakan/fallback**, bukan kondisi yang dipaksa mengeluarkan angka. Laporkan distribusi dan jumlah kegagalan per-kelompok. Hasil agregat yang baik tidak cukup untuk menyimpulkan dukungan pada kelompok dengan sampel tidak memadai. Catat kondisi yang belum diuji sebagai keterbatasan cakupan.

## 6. Checklist kalibrasi, foto impor dan mirror

- Ukuran fisik marker diketahui melalui pengukuran yang dapat ditelusuri; cetakan dapat berubah skala. Jangan menyamakan nominal file desain dengan ukuran cetakan tanpa memeriksa ukuran nyata.
- Marker utuh, empat sudut ditandai berurutan TL/TR/BR/BL, tidak bersilangan, tepi jelas dan bidangnya dijelaskan. Segmen frame harus mewakili panjang nyata yang diukur, dengan bidang frontoparalel yang diperiksa.
- Homography memetakan bidang. Empat titik yang tepat tidak membuktikan pupil, lensa dan marker berada pada depth sama. Catat offset/ketidaksesuaian bidang; gunakan referensi manual bila proyeksi tidak memadai. Landmarks pada singularitas atau sisi lain horizon proyektif ditolak oleh software. Dasar geometri: [OpenCV homography](https://docs.opencv.org/4.10.0/d9/dab/tutorial_homography.html).
- Gunakan foto asli dengan decode/orientasi yang konsisten. Setelah normalisasi EXIF ke piksel aktual, simpan dimensi aktual dan hash gambar tersebut. Jangan menempelkan koordinat dari file sebelum rotasi/crop/resize pada file sesudahnya.
- Cocokkan dimensi metadata dengan naturalWidth/naturalHeight. Ketidaksamaan memblokir koreksi pada editor. Mengubah foto mensyaratkan kalibrasi dan landmark baru; zoom/pan tampilan editor tidak mengubah ukuran foto.
- Periksa mirror dengan objek/penanda asimetris yang diketahui sebelum memakai konfigurasi kamera. Kamera depan dapat memiliki preview berbeda dari file asli. Pengaturan `facingMode` browser tidak menjamin pemilihan lensa fisik; simpan actual settings dan verifikasi pada perangkat ([W3C Media Capture](https://www.w3.org/TR/mediacapture-streams/)).
- Tentukan OD/OS dari sisi pasien, bukan label kiri/kanan layar. Pada gambar frontal kamera belakang yang tidak dicerminkan, OD biasanya berada di kiri gambar. Verifikasi ulang saat memakai kamera depan, file impor, atau gambar yang pernah diedit. Jika asal/mirror tidak dapat dipastikan, ambil ulang.
- Ukuran wajah rata-rata, diameter iris asumsi, dimensi layar, EXIF focal length saja, dan jumlah piksel tanpa referensi nyata tidak menjadi skala mm.
- Foto layar/screenshot atau foto terkompresi tanpa provenance tidak otomatis memenuhi protokol. Periksa semua transformasi dan referensi fisik; ambil ulang bila hubungan koordinat atau kelayakan permukaan tidak dapat diverifikasi.

## 7. Analisis yang direncanakan

Analisis per-parameter, sisi, metode, jarak kerja, perangkat dan referensi bidang. Jangan menggabungkan near/distance, sisi OD/OS yang dipertukarkan, atau raw/corrected panto. Pertahankan baris per-capture dan relasi ke hasil agregat serta revisinya.

Untuk hasil berpasangan, definisikan selisih `OptiFit − referensi`, laporkan bias, distribusi selisih dan interval yang sesuai. Rencanakan plots selisih terhadap rerata, limits of agreement beserta interval estimasinya, dan pemeriksaan proportional bias/heteroskedastisitas. Korelasi tinggi sendiri tidak menguji agreement. Pendekatan perbandingan metode dibahas oleh [Bland & Altman 1986](https://pubmed.ncbi.nlm.nih.gov/2868172/).

Pengukuran berulang dari orang yang sama berkorelasi; metode analisis harus mempertahankan struktur subjek/sesi/operator/perangkat. Gunakan model repeated measures atau resampling pada unit independen yang ditentukan statistikawan, bukan menganggap seluruh frame sebagai pengamatan independen. Rujukan: [Bland & Altman 1999](https://pubmed.ncbi.nlm.nih.gov/10501650/).

Pisahkan repeatability dalam sesi, reproducibility antar-sesi/operator/perangkat, kesalahan anotasi dan variasi referensi. Laporkan jumlah peserta, pasangan valid, nilai yang ditolak, retake, fallback dan alasan eksklusi dengan penyebut jelas. Hitung juga sensitivity analysis tanpa penghilangan outlier. Simpan hasil outlier asli; jangan memilih satu frame yang paling mendekati alat referensi.

Algoritma saat ini menggunakan median/MAD dan modified-Z untuk ringkasan engineering. Kebijakan MAD nol mempertahankan seluruh nilai. SD tiga sampel bukan ketidakpastian pengukuran total. Anggaran ketidakpastian kelak harus mempertimbangkan referensi fisik, penempatan/kalibrasi, anotasi, distorsi, parallax, pose dan repeatability, beserta korelasi yang relevan. NIST membedakan evaluasi komponen berbasis seri observasi dari evaluasi dengan informasi lain; lihat [NIST TN 1297 bagian 2](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-2-classification-components-uncertainty).

Selama anggaran tersebut belum tersedia dan tervalidasi, `uncertainty` tetap `null`/“Tidak tersedia”. Skor kualitas engineering 0–100 bukan probabilitas benar, interval keyakinan, atau persentase akurasi. Batas skor kamera 69 saat ini hanya menahan label kualitas tinggi pada metode yang belum divalidasi; angka itu bukan hasil studi klinis. Perubahan cap/threshold memerlukan versi serta bukti baru.

## 8. Fallback manual dan penanganan ketidaksesuaian

Hentikan pengukuran kamera untuk parameter terkait jika bidang/skala tidak dapat diverifikasi, mirror/sisi tidak pasti, pupil/permukaan belakang lensa tidak dapat ditandai, panto tidak mempunyai referensi head pitch, kualitas rendah berulang, atau nilai berkonflik dengan pembacaan independen.

Gunakan alat/prosedur manual yang sesuai oleh petugas kompeten. Catat nilai kanan/kiri independen, identitas alat/metode, unit, bidang, konvensi tanda, jarak kerja near dan reviewer. Simpan perbedaan antara kamera dan manual sebagai bukti investigasi. Jangan menimpa revisi atau menambahkan offset untuk memaksa persetujuan. Koreksi frame/target, ambil ulang, dan lanjutkan review sesuai prosedur tempat praktik. Resep asli tidak berubah; transpose hanya mengubah notasi ekuivalen.

Jika parameter wajib belum mempunyai hasil yang dapat diterima, sesi tetap belum layak disetujui. Foto tiga-perempat dapat mendukung review visual, tetapi tidak mengaktifkan wrap 3D. Quality sedang tidak menggantikan pembacaan referensi independen yang diminta workflow kamera.

## 9. Laporan, release gate dan status saat ini

Laporan studi harus menyertakan protokol/versi, penanggung jawab, alur peserta, matriks perangkat/kondisi, provenance alat referensi, data berpasangan pseudonim, code analisis, interval hasil, missing/failures, deviasi protokol, keterbatasan, serta keputusan per-parameter terhadap kriteria yang ditetapkan sebelumnya. Versi berikutnya dinilai ulang bila algoritma, model deteksi, transformasi foto, perangkat yang didukung atau tujuan penggunaan berubah secara material.

| Bagian | Status yang boleh dinyatakan pada implementasi ini |
| --- | --- |
| Rumus dan penolakan input | Ada implementasi serta pengujian software; lihat log tes proyek |
| Kamera/editor browser | Ada implementasi; pemeriksaan perangkat fisik mengikuti matriks studi |
| Dataset pasien dan pembandingan alat | Belum tersedia/belum dilaksanakan dalam pekerjaan ini |
| Bias, agreement, repeatability lapangan | Belum diukur; tidak ada nilai yang boleh diisi sebagai hasil |
| Toleransi dan besar sampel konfirmatori | Harus ditetapkan penanggung jawab studi sebelum pengumpulan data |
| Ketidakpastian klinis dan generalisasi | Belum tervalidasi; `null`, cakupan penggunaan dibatasi |
| Deteksi wajah/head pose/depth/wrap 3D otomatis | Belum tersedia; tidak dianggap lulus melalui pengujian manual |
| Persetujuan/sertifikasi untuk klaim klinis | Tidak diberikan oleh dokumen atau pengujian software ini |

Setelah bukti tersedia, reviewer yang berwenang memutuskan cakupan rilis yang didukung. Hasil gagal juga dicantumkan dalam laporan internal, dengan langkah perbaikan dan studi ulang yang diperlukan. Tidak ada klaim akurasi atau status “validasi selesai” sebelum laporan tersebut benar-benar ada.
