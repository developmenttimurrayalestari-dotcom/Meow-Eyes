# OptiFit — geometri, kualitas dan batas kemampuan

Implementasi: `frontend/src/optifit/vision/`. Versi algoritma:
`optifit-local-geometry-1.0.0`. Semua fungsi bekerja lokal tanpa request jaringan,
model cloud atau API berbayar. Bagian ini adalah spesifikasi engineering dan
rumus, bukan klaim akurasi alat ukur medis. Protokol pembandingan dengan alat
referensi pada [validasi lapangan](FIELD_VALIDATION_PROTOCOL.md) masih harus
dijalankan. Tidak ada hasil studi manusia yang diklaim pada implementasi ini.

## Kemampuan yang benar-benar tersedia

| Bagian | Implementasi |
| --- | --- |
| Pengambilan gambar | getUserMedia, izin eksplisit, kamera belakang ideal, pemilihan perangkat, 5 frame berurutan, 3 frame dipilih berdasarkan detail/cahaya/perubahan gambar |
| Kualitas gambar | Rerata luminance, clipping bayangan/sorotan, variance Laplacian, perubahan thumbnail antar-frame |
| Bantuan pupil | Otsu threshold + connected components di area satu mata yang ditentukan operator; kandidat harus dikonfirmasi |
| Titik manual | Pemilihan titik, drag/ketuk, keyboard, zoom/pan, magnifier, undo/redo, titik otomatis vs koreksi |
| Marker fisik | Transformasi planar empat sudut persegi panjang dengan ukuran fisik diketahui |
| Referensi frame | Skala isotropik dari segmen terukur pada bidang yang diperiksa frontoparalel |
| PD | Proyeksi horizontal masing-masing pupil terhadap garis tengah yang ditandai; protokol jauh/dekat dipisahkan |
| VD | Proyeksi lateral apex kornea ke permukaan belakang lensa sepanjang arah pandang/referensi yang ditandai |
| Pantoscopic | Sudut lateral bidang lensa terhadap vertikal; head pitch dari alat/referensi manual dicatat dan dikurangkan |
| Wrap | Input kanan/kiri dari alat atau metode referensi manual yang didokumentasikan |
| Pengulangan | Median, MAD, outlier, jumlah valid/inlier, rentang dan sample SD; data asli tetap disertakan |

Belum tersedia: detektor wajah, detektor landmark anatomi/frame tervalidasi,
identifikasi pupil anatomis penuh, head-pose 3D, kedipan/occlusion, jarak kamera,
depth, intrinsics kamera, koreksi distorsi optik, rekonstruksi wrap 3D otomatis,
OCR frame tervalidasi. `CAPABILITIES` mencatat setiap kemampuan secara eksplisit.
Mode otomatis penuh dinonaktifkan dengan alasan yang jelas. Tidak ada respons
detektor fiktif yang menyatakan kondisi tersebut telah lolos.

## Koordinat dan pengambilan gambar

`{x,y}` adalah koordinat piksel gambar asli setelah decode/capture, dengan titik
nol kiri atas. Tampilan kamera tidak dicerminkan. Kamera belakang biasanya
menampilkan mata kanan pasien (OD) di sisi kiri gambar; operator tetap wajib
memastikan label sisi. Zoom/pan editor hanya mengubah tampilan, bukan koordinat
tersimpan. Metadata dimensi harus sama dengan dimensi gambar aktual. Editor
memblokir koreksi bila gambar gagal decode atau dimensinya tidak cocok. Review
read-only tetap mengizinkan pemilihan titik, pan/zoom dan perbandingan titik awal
tanpa mengubah data.

CameraCapture mengambil lima frame dengan interval 120 ms, menyimpan analisis
kelimanya dan mempertahankan tiga gambar dengan skor detail/cahaya/stabilitas
gambar tertinggi. Pemilihan tidak melihat nilai PD atau nilai sasaran lain.
Perubahan thumbnail adalah indikator perubahan gambar, bukan bukti landmark
anatomi stabil. Tiga gambar masih harus dianotasi dan dikalibrasi terpisah untuk
menghasilkan repeatability pengukuran.

Analisis luminance/Laplacian memakai thumbnail dengan sisi terpanjang maksimal
320 px agar foto impor dan kamera memakai skala skrining yang sebanding. Gambar
asli untuk kalibrasi dan anotasi tidak diubah oleh fungsi analisis tersebut.

Tombol pengambilan otomatis hanya menunggu tiga sampel gambar yang lolos skrining
dan perubahan kecil sesudah checklist petugas. Ini berbeda dari mode pengukuran
otomatis penuh. Kondisi pupil, frame, refleksi, gaze dan kepala tetap diperiksa
petugas. Bila kondisi fisik berubah, checklist harus diperiksa kembali.

Kamera dibuka hanya setelah tindakan pengguna dengan persetujuan dan checklist
lengkap. Stream yang baru selesai meminta izin setelah modal ditutup langsung
dihentikan. Tab tersembunyi, pagehide, pergantian view, penutupan atau unmount
menghentikan kamera. Sensor orientasi membutuhkan tindakan/izin tersendiri pada
perangkat yang mengharuskannya. Angka beta/gamma ponsel tidak dipakai sebagai
head pitch. Browser tidak menjamin identifikasi kamera utama versus ultra-wide.

## Kalibrasi

### Marker persegi panjang

Input `createCalibration`:

```javascript
{
  method: 'marker',
  image: { width: 1920, height: 1080 },
  corners: [topLeft, topRight, bottomRight, bottomLeft],
  widthMm: /* ukuran fisik terverifikasi */,
  heightMm: /* ukuran fisik terverifikasi */,
  evidence: {
    knownSize: true, fullyVisible: true, samePlane: true, clearEdges: true
  },
  referencePlane: 'Deskripsi bidang referensi yang diperiksa operator'
}
```

Empat titik dipetakan ke `(0,0)`, `(widthMm,0)`, `(widthMm,heightMm)` dan
`(0,heightMm)`. Penyelesaian sistem linear delapan persamaan dengan pivoting
menghasilkan H, dengan koordinat sumber dinormalisasi terhadap ukuran gambar.

`[X,Y,1]ᵀ ∝ H [x,y,1]ᵀ`. Pembagian dengan komponen homogen memberikan X/Y
dalam mm pada **bidang kalibrasi**. Fungsi menolak ukuran nol/tidak diketahui,
marker terpotong, sudut bersilangan/terbalik, segmen terlalu kecil, persamaan
degenerat, dan transformasi yang tidak stabil secara numerik. Deskripsi bidang
fisik `referencePlane` wajib diisi. Titik yang melintasi horizon/singularitas
proyektif marker ditolak, walaupun solver empat sudut berhasil. Pembatasan
numerik ini tidak menyatakan parallax fisik telah hilang.

Screening sudut/sisi marker adalah batas engineering untuk menghindari geometri
ekstrem, bukan toleransi klinis. Empat sudut yang cocok secara matematis tidak
membuktikan bidang fisik sesuai: operator harus memeriksa ukuran nyata,
penempatan marker, keterlihatan dan kesesuaian bidang.

**Homography hanya memetakan bidang.** Marker pada frame tidak otomatis
menyelesaikan perbedaan kedalaman pupil, lensa dan marker. Nilai yang dihitung
tetap proyeksi dengan risiko parallax. Tidak ada estimasi kedalaman atau pose 3D
yang diturunkan dari ukuran pupil populasi atau ukuran wajah bawaan.

### Segmen frame

Gunakan `method:'frame'`, `segment:[p1,p2]`, `lengthMm` dan evidence yang sama,
ditambah `frontoparallel:true`. Skala `s = lengthMm / |p2−p1|`, diikuti rotasi
koordinat agar segmen menjadi sumbu X. Metode ini tidak memperbaiki
foreshortening atau frame yang melengkung; karena itu pemeriksaan bidang wajib
dan skor bukti lebih rendah dibanding marker fisik.

Ukuran A/DBL yang tertulis pada frame harus diverifikasi. Lebar box lensa tidak
boleh disamakan begitu saja dengan jarak antara dua titik kontur yang tidak
mewakili pengukuran box tersebut. OCR tidak digunakan untuk mengisi ukuran.

Kalibrasi gagal mengembalikan `valid:false`, `matrix:null`, serta alasan;
pengukuran tidak mengembalikan nilai mm. Setiap frame mempunyai kalibrasi sendiri.

## Rumus pengukuran

### PD jauh dan dekat

Setelah titik dikonversi dengan H, `v` adalah unit vector garis tengah dari atas
ke bawah. Sumbu horizontal `h=(v.y,−v.x)`. Untuk titik acuan tengah `M`, pupil
kanan `R` dan kiri `L`:

```text
monocular kanan = |(R−M) · h|
monocular kiri  = |(L−M) · h|
binocular      = monocular kanan + monocular kiri
```

Pupil harus berada pada sisi berlawanan dari garis tengah. Sudut garis tengah
mengoreksi orientasi roll dalam proyeksi yang digunakan; ini bukan detektor yaw
atau pitch kepala. Kedua mono-PD dihitung independen dan tidak didapat dengan
membagi binocular menjadi dua.

`measurePD` memerlukan foto frontal dan konfirmasi gaze, landmark dan posisi
kepala. `gaze:'near'` membutuhkan jarak kerja positif dalam cm dan menghasilkan
parameter terpisah `pd_near`. Protokol distance meminta target jauh, bukan layar.
Nilai near tidak dihitung dari rumus pengurangan tetap terhadap distance PD.

Referensi bridge frame dan referensi wajah bukan hal yang identik. Simpan
`pdReference` dan `referencePlane`. Proyeksi pada bidang marker/frame belum
membuktikan jarak pupil 3D. Near centration pada bidang frame juga berbeda dari
jarak pada bidang kornea; laporan harus mempertahankan metode/referensinya.

### Vertex Distance

Hanya `lateral_right` atau `lateral_left`. Titik `C` adalah apex kornea, `B`
adalah titik permukaan belakang lensa, dan `g` unit vector arah pandang/referensi
operator:

```text
VD proyeksi = (B−C) · g
off-axis   = |(B−C) × g|
```

Nilai harus positif menurut arah pandang yang ditandai. Jarak off-axis disimpan
untuk mengungkap ketidaksejajaran titik. Operator wajib memilih permukaan lensa
yang sesuai ray/reference, memeriksa refraksi/refleksi/tepi dan bidang skala.
Rim depan bukan pengganti permukaan belakang lensa. Satu foto frontal ditolak.
Metode ini adalah proyeksi lateral terkalibrasi yang tetap memerlukan verifikasi
alat; tidak menyelesaikan kornea atau permukaan lensa dalam 3D.

### Pantoscopic tilt

Bidang lateral, kalibrasi valid, garis lensa top→bottom dan vertikal top→bottom
diperlukan. Sudut antar-vector dihitung dengan `atan2(cross,dot)`, lalu tanda
disesuaikan arah menuju wajah pada foto. Nilai positif berarti bawah lensa
lebih dekat ke wajah.

```text
sudut terkoreksi = sudut mentah − kontribusi head pitch
```

Head pitch harus dimasukkan secara eksplisit dengan sumber alat atau referensi
manual. Positif berarti kontribusi kepala menunduk sesuai konvensi yang
ditampilkan. Nol bukan nilai otomatis saat sumber tidak tersedia. Simpan sudut
mentah, head pitch, sumber, nilai terkoreksi dan konvensi tanda. Sensor ponsel
tidak dianggap head pitch. Referensi vertikal/posisi normal harus diperiksa.

### Wrap angle

MVP menerima pembacaan independen kanan/kiri menggunakan
`recordManualMeasurement({parameter:'wrap', ...})`. Identitas alat/metode,
konfirmasi operator dan `angleReference` wajib ada. Simpan bidang acuan dan
konvensi tanda. Total adalah jumlah kanan+kiri dan rata-rata merupakan setengah
jumlah tersebut; keduanya diberi nama berbeda agar tidak tertukar dengan format
supplier. Tidak ada inferensi wrap dari wajah atau dari satu foto frontal.

Foto tiga-perempat disimpan sebagai bukti/pendukung review. Foto-foto tersebut
belum otomatis menjadi rekonstruksi metrik: diperlukan korespondensi, intrinsics,
extrinsics, koreksi distorsi dan validasi sebelum pipeline 3D dapat diaktifkan.

### Frame dan decentration

```text
Frame PD = A + DBL
Decentration kanan = Frame PD / 2 − mono-PD kanan
Decentration kiri  = Frame PD / 2 − mono-PD kiri
Total = Frame PD − (mono-PD kanan + mono-PD kiri)
```

Asumsi: kedua box lensa memakai A yang sama dan mono-PD memakai garis tengah
bridge yang sama. Positif menunjukkan decentration ke nasal; negatif ke temporal.
Fungsi tidak menghitung decentration ketika referensinya facial midline tanpa
transformasi bridge yang sesuai. A+DBL sudah dapat ditampilkan sebelum B/ED
lengkap; validasi formulir lengkap tetap dilakukan sebelum pengajuan hasil.
Ambang perbedaan kanan/kiri berasal dari konfigurasi organisasi, bukan angka
klinis yang ditebak. Tidak ada pemaksaan simetri kanan/kiri.

### Resep dan transpose

Input resep berasal dari pemeriksaan profesional. SPH dan CYL harus numerik;
AXIS 1–180 wajib ketika CYL bukan nol. Nol SPH/CYL dipertahankan sebagai angka,
bukan dianggap kolom kosong. ADD opsional. Transpose ekuivalen:

```text
SPH′ = SPH + CYL
CYL′ = −CYL
AXIS′ = AXIS ± 90°, dalam interval 1–180°
```

`transposePrescription` mengembalikan objek asli dan objek transposed yang
terpisah. ADD dipertahankan. Ini hanya perubahan notasi, tidak mengubah kekuatan
karena VD/wrap/pantoscopic dan tidak menimpa resep asli.

## Skor kualitas dan repeatability

`assessQuality` memakai rubrik bukti yang dapat diperiksa: kalibrasi, marker,
detail/cahaya, konfirmasi landmark, frame, pupil/referensi mata, refleksi, gaze,
posisi kepala, jarak, konsistensi skala dan pengulangan. Setiap komponen menyimpan
status dan bobotnya. Skor adalah persentase bobot bukti yang tersedia.

Kategori engineering: `<50` rendah, `50–79` sedang, `≥80` tinggi. Skor kamera
dibatasi 69 selama protokol kamera belum divalidasi, dan menjadi 0 jika kalibrasi
tidak valid. Angka ini adalah aturan produk konservatif, **bukan** tingkat
akurasi atau peluang ukuran benar. Membaca skor 69 tidak berarti akurasi 69%.
Hasil manual dari instrumen juga membutuhkan pemeriksaan dan review; skor tinggi
tidak menyatakan alat tersebut otomatis mempunyai validasi klinis.

Pengukuran kamera tidak memperoleh ketidakpastian dari score. Field `uncertainty`
tetap `null` dan UI menampilkan Tidak tersedia. Tidak ada angka ±mm yang dibuat
tanpa model ketidakpastian yang sah dan data kalibrasi.

`aggregateMeasurements` memerlukan minimal tiga nilai. Median dan median absolute
deviation dihitung. Modified Z-score lebih besar 3.5 menandai outlier ketika MAD
bukan nol. Saat MAD nol, tidak dibuat noise floor palsu dan semua nilai tetap
disertakan. Raw samples dan indeks outlier tetap tersedia; setelah penolakan
harus tersisa setidaknya tiga nilai agar agregat dianggap valid. Sample SD dan
rentang dilaporkan sebagai repeatability pada kumpulan tersebut, bukan akurasi
atau ketidakpastian klinis. Pengujian banyak sesi/perangkat/operator tetap perlu.

Agregat beberapa komponen memakai median setiap komponen. Untuk panto,
median(raw), median(head pitch) dan median(corrected) tidak harus memenuhi
identitas pengurangan yang berlaku pada satu capture. Ketiganya harus diberi
label sebagai ringkasan terpisah; nilai corrected agregat tetap median nilai
corrected per-capture. Jangan menciptakan head pitch baru dari selisih median.
Tripel raw/head pitch/corrected asli setiap capture tetap menjadi jejak sumber.

## Pengujian modul

Dari `frontend/`:

```bash
CI=true npm test -- --watchAll=false --runInBand --no-cache src/optifit/vision
```

Fixture hanya muncul dalam file test. Pengujian mencakup kalibrasi perspektif,
penolakan marker salah, skala frame, PD asimetris/roll/near, VD frontal ditolak,
konvensi panto dua sisi, transposition bolak-balik, decentration, pupil sintetis,
outlier, batas confidence, izin kamera, permintaan kamera terlambat dan undo/redo.
Pengujian geometri sintetis tidak merupakan pembandingan klinis pasien.

## Referensi primer

- [ABDO, A review of spectacle lens dispensing measurements (2024)](https://www.abdo.org.uk/wp-content/uploads/2024/06/DO-July-_-August-2024-CPD-with-References.pdf): frame harus disetel sebelum pengukuran; monocular menangani asimetri; perbedaan proyeksi/near dan parallax perlu diperhatikan.
- [ABDO, OA Corner Part 36](https://www.abdo.org.uk/news/oa-corner-part-36/): definisi PD, near centration, vertex distance dan kebutuhan pemeriksaan petugas kompeten.
- [OpenCV, Basic concepts of the homography](https://docs.opencv.org/4.10.0/d9/dab/tutorial_homography.html): hubungan dua bidang, normalisasi homogen, serta kebutuhan intrinsics untuk pemulihan pose.
- [W3C, Media Capture and Streams](https://www.w3.org/TR/mediacapture-streams/): permission, constraints, capabilities dan actual settings kamera browser.
- [Specsavers, Foundations in Dispensing, Semester 1, halaman tercetak 74](https://publishing.apps.specsavers.com/foundations-in-dispensing-textbook-semester-1.pdf): transpose sphero-cylinder ekuivalen.

Referensi mendukung terminologi/geometri. Referensi tersebut tidak memvalidasi
akurasi perangkat lunak OptiFit ini atau seluruh ponsel yang mungkin digunakan.
