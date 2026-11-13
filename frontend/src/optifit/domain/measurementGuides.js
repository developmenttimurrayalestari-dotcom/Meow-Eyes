import { measurementType } from './customerFlow';

export function measurementGuide({ parameters, view, pdReference = 'facial_midline', workingDistanceCm = 40 }) {
  const method = 'frame';
  const kind = measurementType(parameters).id;
  const frontal = kind === 'distance_pd' || kind === 'near_pd';
  const left = view?.endsWith('_left');
  const side = frontal ? 'Dari depan' : `${left ? 'Sisi kiri (OS)' : 'Sisi kanan (OD)'}`;
  const point = (key, label, detail, x, y, group = 'measurement') => ({ key, label, detail, x: !frontal && left ? 520 - x : x, y, group });
  const rect = frontal ? [231, 51, 38, 28] : [207, 197, 44, 32];
  const reference = [
    point('scaleStart', frontal ? 'A: ujung kiri satu lensa' : 'B: ujung atas lensa', frontal ? 'Tandai tepi kiri bagian terlebar satu lensa, sesuai ukuran A. Pilih tepi lensa, bukan sisi luar bingkai.' : 'Tandai ujung atas lensa yang terlihat dari samping, sesuai tinggi B pada data frame. Jangan memakai panjang tangkai.', frontal ? 173 : 299, frontal ? 135 : 113, 'reference'),
    point('scaleEnd', frontal ? 'A: ujung kanan lensa yang sama' : 'B: ujung bawah lensa yang sama', frontal ? 'Tandai tepi kanan lensa yang sama, sejajar ujung pertama. A adalah lebar satu lensa; bukan lebar dua lensa ditambah DBL.' : 'Tandai ujung bawah lensa yang sama, sesuai B. Ukuran diambil otomatis dari frame sesi; tidak perlu memasukkan ukuran benda lain.', frontal ? 243 : 287, frontal ? 135 : 177, 'reference'),
  ];
  const center = pdReference === 'frame_bridge' ? 'kacamata' : 'wajah';
  const measurements = frontal ? [
    point('rightPupil', 'Pusat pupil kanan (OD)', 'Pilih pusat lingkaran hitam mata kanan Anda, bukan pantulan lampu. Pada foto depan yang tidak dicerminkan, mata kanan Anda tampak di kiri gambar.', 208, 135),
    point('leftPupil', 'Pusat pupil kiri (OS)', 'Pilih pusat lingkaran hitam mata kiri Anda. Pastikan kanan/kiri mengikuti mata Anda; periksa apakah foto dicerminkan.', 292, 135),
    point('midlineTop', `Garis tengah ${center}: atas`, `Tandai titik atas pada garis tengah ${center}. Garis ini menjadi acuan pengukuran masing-masing mata.`, 250, 101),
    point('midlineBottom', `Garis tengah ${center}: bawah`, `Tandai titik bawah pada garis tengah ${center} yang sama. Kedua titik membentuk garis acuan, bukan titik pupil tambahan.`, 250, 180),
  ] : kind === 'vertex' ? [
    point('cornea', 'Bagian depan mata', 'Tandai bagian paling depan permukaan mata yang terlihat dari samping. Jika tidak terlihat jelas, ambil ulang foto; jangan menebaknya.', 282, 140),
    point('backLens', 'Permukaan belakang lensa', 'Tandai permukaan lensa yang menghadap mata, sesuai arah pandang. Jangan memakai rim atau bingkai depan sebagai penggantinya.', 294, 140),
    point('gazeStart', 'Arah pandang: awal', 'Letakkan titik awal pada garis arah pandang mata. Garis ini digunakan untuk arah pengukuran jarak.', 250, 140),
    point('gazeEnd', 'Arah pandang: depan', 'Letakkan titik berikutnya di depan mata pada arah pandang yang sama. Urutan harus menuju ke depan wajah.', 367, 140),
  ] : kind === 'pantoscopic' ? [
    point('lensTop', 'Lensa: ujung atas', 'Tandai ujung atas lensa yang tampak dari samping, pada garis kemiringan lensa. Dapat berimpit dengan titik awal B.', 299, 113),
    point('lensBottom', 'Lensa: ujung bawah', 'Tandai ujung bawah lensa yang sama. Urutannya atas lalu bawah, jangan tertukar. Dapat berimpit dengan titik akhir B.', 287, 177),
    point('verticalTop', 'Garis tegak: atas', 'Tandai titik atas pada benda acuan yang benar-benar tegak di dalam foto. Tepi layar bukan bukti benda tegak.', 365, 98),
    point('verticalBottom', 'Garis tegak: bawah', 'Tandai titik bawah pada acuan tegak yang sama. Nilai kemiringan kepala tetap perlu hasil ukur beserta sumbernya.', 365, 197),
  ] : [];
  const photo = kind === 'distance_pd' ? 'Foto dari depan dengan kamera sejajar mata. Lihat benda yang jauh di belakang atau di samping kamera, bukan layar ponsel.'
    : kind === 'near_pd' ? `Foto dari depan sambil melihat benda bacaan pada jarak ${workingDistanceCm} cm dari mata. Pastikan target bacaan tidak menutupi mata atau frame.`
      : kind === 'wrap' ? 'Minta bantuan untuk mengambil foto tiga perempat kanan dan kiri, dengan kacamata pada posisi pemakaian. Foto ini untuk dokumentasi.'
        : 'Minta bantuan untuk mengambil foto tepat dari samping, sejajar mata. Pertahankan posisi kepala yang nyaman dan tampilkan area lensa serta mata dengan jelas.';
  return { kind, frontal, left, side, method, rect, points: kind === 'wrap' ? [] : [...reference, ...measurements], photo,
    stages: kind === 'wrap' ? [['photo', 'Contoh foto'], ['review', 'Catat & simpan']] : [['photo', 'Contoh foto'], ['scale', 'Acuan frame'], ['points', 'Tandai titik'], ['review', 'Periksa & simpan']],
    scale: frontal ? 'Lebar satu lensa (A) dari frame sesi menjadi acuan foto depan. Tandai dua ujung lebarnya pada lensa yang sama. Pakai frame sesuai data sesi, menghadap lurus dan terlihat utuh. Tidak perlu benda tambahan.' : 'Tinggi satu lensa (B) dari frame sesi menjadi acuan foto samping. Tandai ujung atas dan bawah lensa yang sama. Pastikan bagian acuan tidak terpotong atau memendek karena sudut foto. Tidak perlu benda tambahan.',
    review: kind === 'wrap' ? 'Masukkan hasil sudut kanan/kiri dari alat atau pemeriksaan yang Anda miliki pada tahap Hasil. Catat alat dan acuan sudutnya. Aplikasi tidak menghitung sudut lengkungan dari foto biasa.' : 'Bandingkan kembali titik pada foto asli. Periksa skala dan arah kanan/kiri, lalu simpan setiap sampel. Ulangi pada foto lain; hasil akhir tetap memerlukan review.' };
}
