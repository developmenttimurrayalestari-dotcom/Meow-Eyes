from pathlib import Path
root = Path(__file__).resolve().parents[2]
p = root / 'docs/optifit/CUSTOMER_FLOW.md'
s = p.read_text(encoding='utf-8')
start = s.index('## Ukuran pembanding pada foto')
end = s.index('## Kamera dan komponen', start)
s = s[:start] + '''## Ukuran frame sebagai acuan foto

Alur customer sekarang **tanpa kartu atau benda pembanding tambahan**. Ukuran diambil otomatis dari snapshot frame sesi, baik katalog maupun manual:

- Foto depan (PD jauh/dekat): **lebar satu lensa A**. Tandai ujung kiri dan kanan lensa yang sama pada bagian terlebar; jangan memakai lebar seluruh frame, DBL, atau 2A + DBL.
- Foto samping (jarak lensa ke mata/kemiringan): **tinggi satu lensa B**. Tandai ujung atas dan bawah lensa yang sama; jangan memakai A atau panjang tangkai untuk menskalakan foto samping.

Panel **Ukuran frame sebagai acuan** hanya menampilkan nilai sesi; tidak ada pemilih marker atau input panjang yang harus diketik ulang. `frameScaleSpec` menyimpan metode `frame`, `scaleSource=session_frame`, dimensi A/B, panjang nyata, dan sumber acuan. Backend memeriksa dimensi/panjang terhadap snapshot sesi sehingga panjang skala tidak dapat diganti lewat payload.

Customer mengonfirmasi frame yang dipakai sesuai ukuran sesi, kedua ujung terlihat utuh, serta bagian acuan sejajar bidang ukur dan kamera. Dua titik hanya menentukan skala bidang; tidak mengoreksi perspektif, frame melengkung, atau perbedaan kedalaman mata/lensa. Nilai ukuran yang hilang tidak ditebak; foto terlalu miring/terpotong perlu diambil ulang. Hasil tetap estimasi fitting dan memerlukan review.

Saat foto lama dengan acuan marker atau ukuran bebas dibuka untuk diedit, titik pengukuran anatomis tetap tersedia, tetapi titik skala dan konfirmasi lama tidak dipakai ulang sebagai acuan frame. Customer menandai ulang dua ujung frame. Revisi historis tetap tersimpan. Mode petugas/legacy tetap dapat membaca metode lama.

Pengukuran kemiringan tetap memerlukan arah tegak yang diketahui dan nilai kemiringan kepala beserta sumbernya. Keduanya tidak diturunkan atau dianggap nol dari A/B. Wrap tetap memakai hasil alat/pemeriksaan; bukan perkiraan sudut dari satu foto.

''' + s[end:]
s = s.replace('Contoh foto → Pembanding → Tandai titik → Periksa & simpan', 'Contoh foto → Acuan frame → Tandai titik → Periksa & simpan')
s = s.replace('sisi foto kanan/kiri, metode pembanding, dan acuan garis tengah sesi', 'sisi foto kanan/kiri, dimensi acuan frame, dan garis tengah sesi')
s = s.replace('Pembanding empat sudut memiliki urutan kiri atas → kanan atas → kanan bawah → kiri bawah sesuai tampilan foto; pembanding bagian kacamata memakai dua ujung panjang yang benar-benar diketahui.', 'Dua ujung lebar lensa A atau tinggi lensa B diberi nomor sesuai titik acuan pada editor.')
s = s.replace('Contoh foto, pembanding, titik, simpan', 'Contoh foto, acuan A/B, titik, simpan').replace('Ukuran pembanding relevan', 'Acuan A/B otomatis dari sesi')
p.write_text(s, encoding='utf-8')
p = root / 'frontend/src/optifit/components/CustomerCaptureFields.jsx'
s = p.read_text(encoding='utf-8').replace('Pembanding yang sudah diukur</option>', 'Hasil pemeriksaan yang sudah dimiliki</option>')
p.write_text(s, encoding='utf-8')
