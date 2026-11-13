from pathlib import Path

root = Path(__file__).resolve().parents[2]
def edit(name, replacements):
    path = root / name
    value = path.read_text(encoding='utf-8')
    for old, new in replacements:
        assert old in value, (name, old[:100])
        value = value.replace(old, new)
    path.write_text(value, encoding='utf-8')

edit('frontend/src/optifit/components/Results.jsx', [
    ('<h3>Catatan operator</h3>', "<h3>{customerMode ? 'Catatan Anda' : 'Catatan operator'}</h3>"),
    ('<Field label="Parameter alat referensi"><select', '<Field label={customerMode ? "Jenis pengukuran" : "Parameter alat referensi"}><select disabled={customerMode}'),
    ('<Field label="Referensi bidang dan konvensi sudut"', '{(!customerMode || angular) && <Field label="Referensi bidang dan konvensi sudut"'),
    ('required={parameter === "wrap"} maxLength={2000} /></Field>', 'required={parameter === "wrap"} maxLength={2000} /></Field>}'),
    ('dikonfirmasi operator.`', 'dikonfirmasi pengguna.`'),
])
edit('frontend/src/optifit/CustomerMeowsurementApp.jsx', [
    ('ArrowRight, Camera, CheckCircle2, FileClock', 'ArrowRight, FileClock'),
    ('formatNumber, readableDate, todayLocal', 'formatNumber, readableDate'),
    ("<h1>{data.frame?.model || 'Sesi Meowsurement'}</h1>", "<h1>{reviewerMode ? data.frame?.model || 'Sesi Meowsurement' : measurementType(data.requiredParameters).title}</h1>"),
    ('Ukuran mengikuti produk/varian terpilih dan tidak diedit melalui halaman pengukuran customer.', "{data.frame?.sourceScope === 'manual' ? 'Ukuran yang Anda masukkan saat memulai sesi. Buat sesi baru jika frame atau ukurannya berubah.' : 'Ukuran mengikuti produk/varian terpilih saat sesi dibuat.'}"),
    ('Pilih Pengukuran baru untuk menggunakan resep dari profil dan frame katalog.', 'Pilih Pengukuran baru, lalu pilih jenis pengukuran dan sumber ukuran frame Anda.'),
])
edit('frontend/src/pages/admin/FrameSpecificationEditor.jsx', [
    ('ED — diameter efektif"', 'ED — diameter efektif (opsional)"'),
    ('setelah A/B/DBL/ED diperiksa.', 'setelah A/B/DBL diperiksa. ED opsional.'),
])
edit('frontend/src/optifit/components/SessionDataForm.jsx', [
    ('ED — diameter efektif"', 'ED — diameter efektif (opsional)"'),
])
edit('frontend/src/optifit/CustomerMeowsurementApp.test.jsx', [
    ("expect(host.textContent).toContain('Frame Catalog');", "expect(host.querySelectorAll('[data-testid^=\"measurement-card-\"]')).toHaveLength(5);expect(host.querySelector('form')).toBeNull();"),
])
edit('frontend/src/pages/admin/FrameSpecificationEditor.test.jsx', [
    ('completeFrameSpecification({ ...base, ed: null })).toBe(false)', 'completeFrameSpecification({ ...base, ed: null })).toBe(true)'),
])
