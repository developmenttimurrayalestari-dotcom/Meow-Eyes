import React, { useId, useState } from 'react';
import { BookOpen, ChevronDown } from 'lucide-react';
import { measurementGuide } from '../domain/measurementGuides';

export default function MeasurementIllustrationGuide(props) {
  const { data, view, method = 'frame', initialStage = 'photo', collapsible = false } = props;
  const guide = measurementGuide({ parameters: data.requiredParameters, pdReference: data.frame?.pdReference, workingDistanceCm: data.workingDistanceCm, view, method });
  const content = <GuideContent key={`${guide.kind}-${view}-${method}-${initialStage}`} guide={guide} initialStage={initialStage}/>;
  return collapsible ? <details className="of-illustration-guide of-illustration-fold" data-testid="measurement-illustration-guide"><summary><BookOpen size={18}/><span>Panduan gambar: posisi foto & titik ukur</span><ChevronDown size={17}/></summary>{content}</details>
    : <section className="of-illustration-guide" aria-label="Panduan gambar pengukuran" data-testid="measurement-illustration-guide">{content}</section>;
}

function GuideContent({ guide, initialStage }) {
  const id = useId();
  const [stage, setStage] = useState(guide.stages.some(([key]) => key === initialStage) ? initialStage : 'photo');
  const [selected, setSelected] = useState(null);
  const points = stage === 'scale' ? guide.points.filter(point => point.group === 'reference') : stage === 'points' || stage === 'review' ? guide.points : [];
  const active = points.find(point => point.key === selected) || points[0];
  const text = stage === 'photo' ? guide.photo : stage === 'scale' ? guide.scale : stage === 'points' ? 'Ikuti urutan nomor berikut. Pilih nama titik untuk melihat penjelasannya, lalu tempatkan titik tersebut pada foto Anda.' : guide.review;
  return <div className="of-illustration-content">
    <div className="of-illustration-heading"><span className="of-eyebrow">PANDUAN BERGAMBAR</span><strong>{guide.side}{guide.kind === 'wrap' ? ' · tiga perempat' : ''}</strong></div>
    <div className="of-illustration-steps" role="group" aria-label="Tahapan panduan gambar">{guide.stages.map(([key, title], index) => <button key={key} type="button" aria-pressed={stage === key} onClick={() => { setStage(key); setSelected(null); }}><span>{index + 1}</span>{title}</button>)}</div>
    <p id={`${id}-caption`} className="of-illustration-caption">{text}</p>
    <div className="of-illustration-layout"><figure>
      <GuideDrawing guide={guide} stage={stage} points={points} active={active?.key} captionId={`${id}-caption`}/>
      <figcaption>Ilustrasi contoh, bukan foto atau ukuran Anda. Titik tidak ditambahkan otomatis ke foto.</figcaption>
    </figure><div className="of-illustration-instructions">
      {points.length > 0 ? <><div className="of-illustration-legend" role="group" aria-label="Contoh penempatan titik">{points.map(point => <button type="button" key={point.key} aria-pressed={active?.key === point.key} onClick={() => setSelected(point.key)} data-guide-point={point.key}><span className={point.group === 'reference' ? 'is-reference' : ''}>{guide.points.indexOf(point) + 1}</span>{point.label}</button>)}</div><p className="of-illustration-detail" aria-live="polite"><strong>{active.label}</strong>{active.detail}</p></> : <ul className="of-illustration-tips"><li>Cahaya merata, mata dan kacamata terlihat jelas.</li><li>Kamera sejajar area yang diukur. Minta bantuan orang lain bila perlu.</li><li>{guide.kind === 'wrap' ? 'Siapkan hasil pemeriksaan sudut; foto hanya dokumentasi.' : 'Pakai frame yang sama dengan data sesi. Tepi lensa harus terlihat utuh.'}</li></ul>}
      {guide.kind === 'pantoscopic' && <p className="of-small of-muted">Kemiringan kepala harus berasal dari pengukuran, bukan dianggap nol. Garis tegak contoh bukan pengganti acuan nyata pada foto.</p>}
      {guide.frontal && <p className="of-small of-muted">OD = mata kanan Anda, OS = mata kiri Anda. Ilustrasi depan tidak dicerminkan; periksa foto selfie sebelum menandai.</p>}
    </div></div>
  </div>;
}

function FrontFace() {
  return <g>
    <path d="M169 274v-28q-57 0-71 44h304q-14-44-71-44v28" fill="#c5ded8"/>
    <ellipse cx="250" cy="145" rx="99" ry="118" fill="#f3d7bf" stroke="#ba8870" strokeWidth="2"/>
    <path d="M152 121q-11-105 94-109 105-2 103 109l-22-38q-39 2-71-30-45 37-92 34Z" fill="#3e4654"/>
    <path d="M186 121q23-16 43 0m42 0q23-16 43 0" fill="none" stroke="#805d4b" strokeWidth="3"/>
    <ellipse cx="208" cy="135" rx="14" ry="8" fill="white"/><ellipse cx="292" cy="135" rx="14" ry="8" fill="white"/>
    <circle cx="208" cy="135" r="6" fill="#263f48"/><circle cx="292" cy="135" r="6" fill="#263f48"/>
    <path d="m250 142-9 40h18m-31 30q22 12 44 0" fill="none" stroke="#ba8870" strokeWidth="3" strokeLinecap="round"/>
    <g fill="#e8f4f4" fillOpacity=".25" stroke="#244a51" strokeWidth="4"><rect x="171" y="108" width="74" height="50" rx="15"/><rect x="255" y="108" width="74" height="50" rx="15"/><path d="M245 122q5-5 10 0M153 116l18 4m158 0 18-4" fill="none"/></g>
  </g>;
}

function SideFace({ left }) {
  return <g transform={left ? 'translate(520 0) scale(-1 1)' : undefined}>
    <path d="M168 274v-34l76-9 12 43 59 16H112Z" fill="#c5ded8"/>
    <path d="M177 239q-42-40-34-112 4-87 83-94 53-4 66 48l-6 30 37 43-24 10q7 50-26 67l-44 6-6 40h-57Z" fill="#f3d7bf" stroke="#ba8870" strokeWidth="2"/>
    <path d="M146 165q-36-125 61-141 65-10 86 58l-35-4-48 47-18 72Z" fill="#3e4654"/>
    <ellipse cx="194" cy="154" rx="15" ry="24" fill="#ecc5a8" stroke="#ba8870" strokeWidth="2"/>
    <path d="M260 131q16-8 22 8-8 8-20 2" fill="white" stroke="#805d4b" strokeWidth="2"/>
    <path d="m273 132 3 11" stroke="#263f48" strokeWidth="3"/>
    <path d="m194 105 111 3-15 72" fill="none" stroke="#244a51" strokeWidth="4"/>
    <path d="m299 113-12 64" fill="none" stroke="#83b7ba" strokeWidth="3"/>
  </g>;
}

function ThreeQuarterFace({ left }) {
  return <g transform={left ? 'translate(520 0) scale(-1 1)' : undefined}>
    <path d="M184 246q-57 0-71 44h263q-15-44-74-44l-6-28h-98Z" fill="#c5ded8"/>
    <path d="M169 129q-4-92 74-102 82-8 82 95l-4 24 21 22-26 9q-7 76-70 82-77-3-77-130Z" fill="#f3d7bf" stroke="#ba8870" strokeWidth="2"/>
    <path d="M168 164q-47-126 59-146 83-15 103 98l-35-30q-43-3-65-29-19 42-43 50l-2 57Z" fill="#3e4654"/>
    <ellipse cx="178" cy="157" rx="13" ry="23" fill="#ecc5a8" stroke="#ba8870" strokeWidth="2"/>
    <path d="m282 137 12 38-17 4m-33 37q26 12 47-2" fill="none" stroke="#ba8870" strokeWidth="3"/>
    <ellipse cx="229" cy="138" rx="12" ry="8" fill="white"/><circle cx="231" cy="138" r="5" fill="#244a51"/>
    <ellipse cx="295" cy="133" rx="9" ry="7" fill="white"/><circle cx="297" cy="133" r="4" fill="#244a51"/>
    <g fill="#e8f4f4" fillOpacity=".25" stroke="#244a51" strokeWidth="4"><path d="m199 112 60 3-2 45-53-4Z"/><path d="m275 113 40-7 1 45-36 7Z"/><path d="m259 123 16-2m-97-7 21 5" fill="none"/></g>
  </g>;
}

function GuideDrawing({ guide, stage, points, active, captionId }) {
  const id = useId();
  const mirror = x => !guide.frontal && guide.left ? 520 - x : x;
  
  const wrap = guide.kind === 'wrap';
  const referenceVisible = !wrap;
  return <svg viewBox="0 0 520 300" role="img" aria-labelledby={`${id}-title`} aria-describedby={captionId} className="of-guide-drawing" data-testid={`guide-drawing-${guide.kind}`}>
    <title id={`${id}-title`}>{guide.side}: {stage === 'photo' ? 'contoh pengambilan foto' : 'contoh posisi titik'}</title>
    <rect width="520" height="300" rx="20" fill="#f2f7f5"/>
    {wrap ? <ThreeQuarterFace left={guide.left}/> : guide.frontal ? <FrontFace/> : <SideFace left={guide.left}/>}
    
    {referenceVisible && guide.method === 'frame' && <path d={guide.frontal ? 'M173 135h70' : `M${mirror(299)} 113L${mirror(287)} 177`} stroke="#168773" strokeWidth="5"/>}
    {stage === 'scale' && !wrap && <text x={mirror(guide.frontal ? 210 : 350)} y="88" textAnchor="middle" fill="#176f60" fontSize="13">{guide.frontal ? 'Lebar lensa A' : 'Tinggi lensa B'}</text>}
    {stage === 'photo' && <g>
      <path d={guide.frontal || wrap ? 'M345 135h80' : guide.left ? 'M130 140H65' : 'M330 140h85'} stroke="#6b9294" strokeWidth="2" strokeDasharray="5 5"/>
      <g transform={`translate(${!guide.frontal && guide.left ? 27 : 425} 102)`}><rect width="46" height="71" rx="9" fill="#244a51"/><rect x="5" y="6" width="36" height="56" rx="5" fill="#dcece9"/><circle cx="23" cy="67" r="2" fill="white"/><circle cx="23" cy="29" r="9" fill="none" stroke="#168773" strokeWidth="2"/></g>
      <text x={!guide.frontal && guide.left ? 50 : 448} y="195" textAnchor="middle" fill="#244a51" fontSize="13">Kamera</text>
      {guide.kind === 'near_pd' && <g transform="translate(30 211)" fill="none" stroke="#d96070" strokeWidth="3"><path d="M0 0q20-8 40 0 20-8 40 0v49q-20-8-40 0-20-8-40 0ZM40 0v49"/><text x="40" y="69" textAnchor="middle" stroke="none" fill="#244a51" fontSize="13">Target bacaan</text></g>}
      {guide.kind === 'distance_pd' && <g transform="translate(43 113)"><path d="m0 15 13-11 13 11v24H0Z" fill="#d1e5df" stroke="#168773" strokeWidth="2"/><text x="13" y="64" textAnchor="middle" fill="#244a51" fontSize="13">Lihat jauh</text></g>}
    </g>}
    {stage !== 'photo' && !wrap && <g fill="none" strokeWidth="2" strokeDasharray="5 4">
      {guide.frontal && stage !== 'scale' && <><path d="M250 101v79" stroke="#ed6174"/><path d="M208 135h84" stroke="#244a51"/></>}
      {guide.kind === 'vertex' && stage !== 'scale' && <path d={`M${mirror(250)} 140H${mirror(367)}`} stroke="#ed6174"/>}
      {guide.kind === 'pantoscopic' && stage !== 'scale' && <><path d={`M${mirror(365)} 98v99`} stroke="#6b9294"/><path d={`M${mirror(299)} 113L${mirror(287)} 177`} stroke="#ed6174"/></>}
    </g>}
    {points.map(point => {
      const callout = !guide.frontal && ({ scaleStart: [335, 70], scaleEnd: [330, 222], cornea: [270, 100], backLens: [324, 108], gazeStart: [242, 166], gazeEnd: [378, 166], lensTop: [270, 90], lensBottom: [260, 200] })[point.key];
      const cx = callout ? mirror(callout[0]) : point.x, cy = callout ? callout[1] : point.y;
      const color = point.group === 'reference' ? '#168773' : '#d84b62';
      return <g key={point.key} data-illustration-point={point.key} aria-hidden="true">
        {callout && <><path d={`M${point.x} ${point.y}L${cx} ${cy}`} stroke={color} strokeWidth="1.5"/><circle cx={point.x} cy={point.y} r="3" fill={color}/></>}
        <circle cx={cx} cy={cy} r={active === point.key ? 13 : 10} fill={color} stroke="white" strokeWidth={active === point.key ? 3 : 2}/>
        <text x={cx} y={cy + 4} textAnchor="middle" fill="white" fontSize="12" fontWeight="700">{guide.points.indexOf(point) + 1}</text>
      </g>;
    })}
    {stage === 'review' && <g transform="translate(438 230)"><circle r="25" fill="#168773"/><path d="m-12 0 8 9 17-18" fill="none" stroke="white" strokeWidth="4"/></g>}
  </svg>;
}
