from pathlib import Path

root = Path(__file__).resolve().parents[2]
def edit(name, changes):
    p = root / name
    value = p.read_text(encoding='utf-8')
    for old, new in changes:
        assert old in value, (name, old[:90])
        value = value.replace(old, new)
    p.write_text(value, encoding='utf-8')

edit('frontend/src/optifit/components/CaptureWorkflow.jsx', [
    ("import MeasurementIllustrationGuide from './MeasurementIllustrationGuide';", "import MeasurementIllustrationGuide from './MeasurementIllustrationGuide';\nimport { customerFrameCapture, frameScaleReference, frameScaleSpec } from '../domain/frameScale';"),
    ('calibrationSpec: { method: "marker", widthMm: null, heightMm: null, lengthMm: null, referencePlane: "", evidence: {} }', 'calibrationSpec: customerMode ? frameScaleSpec(data.frame, view) : { method: "marker", widthMm: null, heightMm: null, lengthMm: null, referencePlane: "", evidence: {} }'),
    ('export function CaptureEditor({ capture, data, settings, onClose, onSave, customerMode = false }) {', 'export function CaptureEditor({ capture, data, settings, onClose, onSave, customerMode = false }) {\n  const initialCustomer = customerMode ? customerFrameCapture(capture, data.frame) : null;\n  const frameReference = frameScaleReference(data.frame, capture.view);'),
    ('useState(capture.points || {}); const [automaticPoints, setAutomaticPoints] = useState(capture.automaticPoints || {});', 'useState(initialCustomer?.points || capture.points || {}); const [automaticPoints, setAutomaticPoints] = useState(initialCustomer?.automaticPoints || capture.automaticPoints || {});'),
    ('useState({ ...(capture.calibrationSpec || { method: "marker", evidence: {} }), referencePlane: capture.calibrationSpec?.referencePlane || (customerMode ? \'Pembanding sejajar bagian yang diukur pada foto, dikonfirmasi customer\' : \'\') }); const [confirmations, setConfirmations] = useState(capture.confirmations || {});', 'useState(initialCustomer?.spec || capture.calibrationSpec || { method: "marker", evidence: {}, referencePlane: "" }); const [confirmations, setConfirmations] = useState(initialCustomer?.confirmations || capture.confirmations || {});'),
    ('...(spec.method === "marker" ? [["markerTL",', '...(customerMode ? [["scaleStart", frameReference?.start], ["scaleEnd", frameReference?.end]] : spec.method === "marker" ? [["markerTL",'),
    ('[spec.method, frontal, lateral, vertex, panto, customerMode, data.frame?.pdReference]', '[spec.method, frontal, lateral, vertex, panto, customerMode, data.frame?.pdReference, frameReference?.start, frameReference?.end]'),
    ('<CustomerScaleFields spec={spec} setSpec={setSpec} calibration={calibration} disabled={busy}/>', '<CustomerScaleFields spec={spec} setSpec={setSpec} calibration={calibration} disabled={busy} frame={data.frame} view={capture.view}/>'),
    ('Tandai titik pada foto dan isi ukuran pembanding agar jarak dapat dihitung dalam milimeter.', 'Tandai dua ujung acuan frame dan titik pengukuran pada foto. Ukuran frame sesi dipakai otomatis untuk menghitung jarak dalam milimeter.'),
    ('{customerMode && <MeasurementIllustrationGuide data={data} view={capture.view}', '{customerMode && initialCustomer?.changed && !documentationOnly && <Notice>Foto lama tetap tersimpan. Tandai ulang dua ujung acuan frame dan konfirmasi posisinya untuk memakai alur baru; titik pembanding lama tidak digunakan otomatis.</Notice>}\n    {customerMode && <MeasurementIllustrationGuide data={data} view={capture.view}'),
    ('Tandai titik & ukuran pembanding', 'Tandai titik & acuan frame'),
])
edit('frontend/src/optifit/components/CustomerPreparation.jsx', [
    ('Siapkan benda pembanding yang ukurannya sudah Anda ukur. Letakkan sejajar dengan bagian yang akan diukur dan pastikan terlihat jelas pada foto.', 'Pakai frame yang sesuai data sesi. Lebar lensa A menjadi acuan foto depan, dan tinggi lensa B menjadi acuan foto samping. Pastikan bagian tersebut terlihat utuh; tidak perlu kartu atau benda tambahan.'),
    ('Saya sudah menyiapkan posisi dan benda pembanding sesuai panduan.', 'Saya sudah memakai frame sesuai ukuran sesi dan menyiapkan posisi foto sesuai panduan.'),
])
edit('frontend/src/optifit/vision/CameraCapture.jsx', [
    ('Pastikan kedua mata dan pembanding terlihat jelas.', 'Pastikan kedua mata dan satu lensa frame terlihat utuh.'),
    ('Pastikan wajah dan benda pembanding tetap terlihat jelas;', 'Pastikan wajah dan frame tetap terlihat jelas;'),
])
edit('frontend/src/optifit/components/CustomerMeasurementSetup.jsx', [
    ('<fieldset className="of-frame-source">', '<Notice>Ukuran frame ini menjadi acuan pengukuran foto. Gunakan frame yang sama saat difoto; tidak perlu benda pembanding tambahan.</Notice>\n    <fieldset className="of-frame-source">'),
])
