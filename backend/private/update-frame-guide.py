from pathlib import Path
root = Path(__file__).resolve().parents[2]
def edit(name, changes):
    p = root / name
    content = p.read_text(encoding='utf-8')
    for old, new in changes:
        assert old in content, (name, old[:90])
        content = content.replace(old, new)
    p.write_text(content, encoding='utf-8')

edit('frontend/src/optifit/domain/measurementGuides.js', [
    ('  const [x, y, w, h] = rect;\n', ''),
    ('target bacaan tidak menutupi mata atau benda pembanding.', 'target bacaan tidak menutupi mata atau frame.'),
])
edit('frontend/src/optifit/components/MeasurementIllustrationGuide.jsx', [
    ("method = 'marker'", "method = 'frame'"),
    ('Benda pembanding harus terlihat utuh dan ukuran aslinya diketahui.', 'Pakai frame yang sama dengan data sesi. Tepi lensa harus terlihat utuh.'),
    ('const [x, y, w, h] = guide.rect;', ''),
    ('{referenceVisible && guide.method === \'marker\' && <rect x={mirror(x + (!guide.frontal && guide.left ? w : 0))} y={y} width={w} height={h} rx="2" fill="#fff" stroke="#168773" strokeWidth="2"/>}', ''),
    ("'M173 108h74' : `M${mirror(194)} 105H${mirror(278)}`", "'M173 135h70' : `M${mirror(299)} 113L${mirror(287)} 177`"),
    ('{stage === \'scale\' && !wrap && (guide.method === \'marker\' ? <g stroke="#168773" fill="none" strokeWidth="1.5">\n      <path d={`M${mirror(x)} ${y - 16}H${mirror(x + w)}m0-4v8M${mirror(x)} ${y - 20}v8`}/>\n      <text x={mirror(x + w / 2)} y={y - 23} textAnchor="middle" fill="#176f60" stroke="none" fontSize="12">Lebar</text>\n      <path d={`M${mirror(x + w + 18)} ${y}v${h}m-4 0h8M${mirror(x + w + 18) - 4} ${y}h8`}/>\n      <text x={mirror(x + w + 21)} y={y + h / 2 + 4} textAnchor={guide.left && !guide.frontal ? \'end\' : \'start\'} fill="#176f60" stroke="none" fontSize="12">Tinggi</text>\n    </g> : <text x={mirror(guide.frontal ? 210 : 236)} y="88" textAnchor="middle" fill="#176f60" fontSize="12">Panjang yang diukur</text>)}', '{stage === \'scale\' && !wrap && <text x={mirror(guide.frontal ? 210 : 350)} y="88" textAnchor="middle" fill="#176f60" fontSize="13">{guide.frontal ? \'Lebar lensa A\' : \'Tinggi lensa B\'}</text>}'),
    ('const callout = guide.kind === \'vertex\' && ({ cornea: [270, 100], backLens: [324, 108], gazeStart: [242, 166], gazeEnd: [378, 166] })[point.key];', 'const callout = !guide.frontal && ({ scaleStart: [335, 70], scaleEnd: [330, 222], cornea: [270, 100], backLens: [324, 108], gazeStart: [242, 166], gazeEnd: [378, 166], lensTop: [270, 90], lensBottom: [260, 200] })[point.key];'),
    ('M${mirror(305)} 108L${mirror(290)} 180', 'M${mirror(299)} 113L${mirror(287)} 177'),
])
