from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'frontend/src/optifit/components/CaptureWorkflow.jsx'
s = p.read_text(encoding='utf-8')
s = s.replace('<CaptureCard key={capture.id}', '<CaptureCard customerMode={customerMode} key={capture.id}')
s = s.replace('function CaptureCard({ capture, index, onOpen, disabled, readOnly })', 'function CaptureCard({ capture, index, onOpen, disabled, readOnly, customerMode = false })')
s = s.replace(': "Tandai titik & kalibrasi"}', ': customerMode ? "Tandai titik & ukuran pembanding" : "Tandai titik & kalibrasi"}')
s = s.replace('<Notice>OD/OS mengacu pada mata Anda. Semua titik memakai koordinat gambar asli; periksa pencerminan foto yang diimpor. Nilai mm hanya tampil bila kalibrasi valid.</Notice>', '<Notice>{customerMode ? "Kanan/kiri mengikuti mata Anda. Tandai titik pada foto dan isi ukuran pembanding agar jarak dapat dihitung dalam milimeter." : "OD/OS mengacu pada mata pasien. Semua titik memakai koordinat gambar asli; periksa pencerminan foto yang diimpor. Nilai mm hanya tampil bila kalibrasi valid."}</Notice>')
p.write_text(s, encoding='utf-8')
