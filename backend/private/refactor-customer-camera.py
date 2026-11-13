from pathlib import Path
root = Path(__file__).resolve().parents[2]
path = root / 'frontend/src/optifit/vision/CameraCapture.jsx'
text = path.read_text(encoding='utf-8')
text = text.replace('disabled = false, uploadEnabled = false })', 'disabled = false, uploadEnabled = false, customerMode = false })')
start = text.rindex('    <div className="flex flex-wrap gap-2">')
end = text.index('    <p className="text-xs">Tiga frame', start)
controls = text[start:end].strip().replace('className="flex flex-wrap gap-2"', 'className="of-camera-controls" data-testid="optifit-camera-controls"')
controls = controls.replace("{capturing ? 'Mengambil…' : 'Ambil 5 frame'}", "{capturing ? 'Mengambil…' : customerMode ? 'Ambil foto' : 'Ambil 5 frame'}")
controls = controls.replace('<button type="button" className="min-h-12 px-4 py-3 border rounded-xl inline-flex gap-2 items-center" onClick={enableSensor}>', '{!customerMode && <button type="button" className="min-h-12 px-4 py-3 border rounded-xl inline-flex gap-2 items-center" onClick={enableSensor}>').replace('Aktifkan sensor ponsel</button>', 'Aktifkan sensor ponsel</button>}')
text = text[:start] + text[end:]
text = text.replace('    <div className="relative overflow-hidden rounded-2xl bg-slate-950 aspect-[4/3] max-h-[65vh]">', '    <div className="of-camera-station" data-testid="optifit-camera-station">\n    <div className="relative overflow-hidden rounded-2xl bg-slate-950 aspect-[4/3] max-h-[65vh]">')
insert = text.index('    {error && <p role="alert"')
text = text[:insert] + '    ' + controls + '\n    </div>\n' + text[insert:]
start = text.index('    <div className="grid grid-cols-2 gap-2 text-sm"')
end = text.index('    {running && <>', start)
text = text[:start] + '    {!customerMode && <>' + text[start:end].strip() + '</>}\n' + text[end:]
text = text.replace('Persetujuan pasien dan checklist persiapan wajib lengkap sebelum kamera dibuka.', 'Baca panduan dan simpan persetujuan foto sebelum membuka kamera.')
text = text.replace('Kelayakan posisi tetap berdasarkan checklist petugas; ini bukan mode pengukuran otomatis penuh.', 'Pastikan wajah dan benda pembanding tetap terlihat jelas; gambar stabil belum menjamin ketepatan ukuran.')
text = text.replace("{view === 'frontal' ? 'Pasien", "{customerMode ? (frontal ? 'Lihat ke arah yang sesuai panduan dan posisikan kamera sejajar mata. Pastikan kedua mata dan pembanding terlihat jelas.' : 'Ambil sisi wajah sesuai panduan. Minta bantuan orang lain dan pastikan area yang diukur terlihat jelas.') : view === 'frontal' ? 'Pasien")
text = text.replace('<p className="text-xs">Resolusi:', '{!customerMode && <p className="text-xs">Resolusi:').replace('Browser tidak menjamin pemilihan lensa utama.</p>', 'Browser tidak menjamin pemilihan lensa utama.</p>}')
path.write_text(text, encoding='utf-8')
