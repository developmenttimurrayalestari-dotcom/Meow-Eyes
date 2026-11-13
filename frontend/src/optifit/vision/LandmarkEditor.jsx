import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Crosshair, Hand, RotateCcw, Undo2, Redo2, Search, ZoomIn, ZoomOut } from 'lucide-react';
import { suggestPupil } from './quality';

const clone = value => JSON.parse(JSON.stringify(value || {}));
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const bounded = (value, max) => Math.min(max - 1, Math.max(0, value));
const isPoint = value => value && Number.isFinite(value.x) && Number.isFinite(value.y);

export default function LandmarkEditor({ image, points = {}, automaticPoints = {}, onChange, onAutomaticPoints, pointDefinitions = [], disabled = false, allowAutomatic = true }) {
  const svgRef = useRef(null); const imageRef = useRef(null); const currentRef = useRef(points); const dragRef = useRef(null);
  const historyRef = useRef([clone(points)]); const historyIndex = useRef(0);
  const [selected, setSelected] = useState(pointDefinitions[0]?.key || ''); const [zoom, setZoom] = useState(1); const [pan, setPan] = useState({ x: 0, y: 0 });
  const [mode, setMode] = useState('point'); const [hover, setHover] = useState(null); const [historyState, setHistoryState] = useState({ index: 0, length: 1 });
  const [before, setBefore] = useState(false); const [error, setError] = useState(''); const [detection, setDetection] = useState(null); const [loadingImage, setLoadingImage] = useState(false);
  const [verifiedImage, setVerifiedImage] = useState(null);
  const width = Number(image?.width) || 1; const height = Number(image?.height) || 1;
  const definitionsKey = pointDefinitions.map(definition => definition.key).join('|');
  const source = typeof image?.dataUrl === 'string' ? image.dataUrl : '';
  let localBlob = false;
  try { localBlob = source.startsWith('blob:') && new URL(source).origin === window.location.origin; } catch { /* Not a local object URL. */ }
  const imageValid = (/^data:image\/(png|jpeg|webp);base64,/i.test(source) || localBlob) && Number.isInteger(width) && Number.isInteger(height) && width >= 4 && height >= 4 && width * height <= 24000000;
  const imageVerified = verifiedImage?.source === source && verifiedImage?.width === width && verifiedImage?.height === height;
  const canEdit = !disabled && imageVerified;
  currentRef.current = points;

  useEffect(() => {
    historyRef.current = [clone(currentRef.current)]; historyIndex.current = 0; setHistoryState({ index: 0, length: 1 });
    setZoom(1); setPan({ x: 0, y: 0 }); setBefore(false); setError(''); setDetection(null); dragRef.current = null;
  }, [image?.dataUrl]);
  useEffect(() => {
    if (!definitionsKey.split('|').includes(selected)) setSelected(definitionsKey.split('|')[0] || '');
  }, [definitionsKey, selected]);

  useEffect(() => {
    setVerifiedImage(null);
    if (!imageValid) { imageRef.current = null; setLoadingImage(false); return undefined; }
    let active = true; const element = new Image(); setLoadingImage(true);
    element.onload = () => {
      if (!active) return;
      if (element.naturalWidth !== width || element.naturalHeight !== height) { setError('Dimensi metadata tidak sama dengan gambar. Kalibrasi dan koordinat tidak boleh dipakai pada gambar yang telah diubah ukurannya.'); imageRef.current = null; }
      else { imageRef.current = element; setVerifiedImage({ source, width, height }); }
      setLoadingImage(false);
    };
    element.onerror = () => { if (active) { imageRef.current = null; setVerifiedImage(null); setError('Gambar privat tidak dapat dibaca.'); setLoadingImage(false); } };
    element.src = image.dataUrl;
    return () => { active = false; imageRef.current = null; element.onload = null; element.onerror = null; };
  }, [image?.dataUrl, source, imageValid, width, height]);

  const emit = useCallback(next => { currentRef.current = next; onChange?.(next); }, [onChange]);
  const commit = useCallback((next, previous = currentRef.current) => {
    if (same(next, previous)) return;
    let history = historyRef.current.slice(0, historyIndex.current + 1);
    if (!same(history[history.length - 1], previous)) history.push(clone(previous));
    history.push(clone(next));
    if (history.length > 100) history = history.slice(history.length - 100);
    historyRef.current = history; historyIndex.current = history.length - 1;
    setHistoryState({ index: historyIndex.current, length: history.length }); emit(next);
  }, [emit]);

  const coordinate = event => {
    const svg = svgRef.current; if (!svg) return null;
    const matrix = svg.getScreenCTM(); if (!matrix) return null;
    const p = svg.createSVGPoint(); p.x = event.clientX; p.y = event.clientY;
    const actual = p.matrixTransform(matrix.inverse());
    return { x: bounded((actual.x - pan.x) / zoom, width), y: bounded((actual.y - pan.y) / zoom, height), svgX: actual.x, svgY: actual.y };
  };

  const down = event => {
    if (event.button > 0 || (mode !== 'pan' && (!canEdit || before))) return;
    const p = coordinate(event); if (!p) return;
    event.currentTarget.setPointerCapture?.(event.pointerId);
    if (mode === 'pan') dragRef.current = { kind: 'pan', pointerId: event.pointerId, start: p, pan: { ...pan } };
    else if (selected) {
      const previous = clone(currentRef.current);
      dragRef.current = { kind: 'point', pointerId: event.pointerId, previous, key: selected };
      emit({ ...currentRef.current, [selected]: { x: p.x, y: p.y } });
    }
    event.preventDefault();
  };
  const move = event => {
    const p = coordinate(event); if (!p) return;
    setHover({ x: p.x, y: p.y }); const drag = dragRef.current;
    if (!drag || (drag.kind === 'point' && (!canEdit || before))) return;
    if (drag.kind === 'pan') setPan({ x: drag.pan.x + p.svgX - drag.start.svgX, y: drag.pan.y + p.svgY - drag.start.svgY });
    else emit({ ...currentRef.current, [drag.key]: { x: p.x, y: p.y } });
  };
  const up = event => {
    const drag = dragRef.current; dragRef.current = null;
    if (drag?.kind === 'point' && canEdit && !before) commit(clone(currentRef.current), drag.previous);
    try { event.currentTarget.releasePointerCapture?.(event.pointerId); } catch { /* The browser may already have released it. */ }
  };
  const cancelDrag = () => {
    if (dragRef.current?.kind === 'point') emit(dragRef.current.previous);
    dragRef.current = null;
  };

  const undo = () => {
    if (historyIndex.current <= 0 || !canEdit) return;
    historyIndex.current -= 1; emit(clone(historyRef.current[historyIndex.current]));
    setHistoryState({ index: historyIndex.current, length: historyRef.current.length });
  };
  const redo = () => {
    if (historyIndex.current >= historyRef.current.length - 1 || !canEdit) return;
    historyIndex.current += 1; emit(clone(historyRef.current[historyIndex.current]));
    setHistoryState({ index: historyIndex.current, length: historyRef.current.length });
  };
  const shiftPoint = event => {
    if (!canEdit || before || !selected || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key) || !isPoint(points[selected])) return;
    const amount = event.shiftKey ? 10 : 1; const p = { ...points[selected] };
    if (event.key === 'ArrowLeft') p.x -= amount;
    if (event.key === 'ArrowRight') p.x += amount;
    if (event.key === 'ArrowUp') p.y -= amount;
    if (event.key === 'ArrowDown') p.y += amount;
    p.x = bounded(p.x, width); p.y = bounded(p.y, height); commit({ ...points, [selected]: p }); event.preventDefault();
  };

  const findPupil = () => {
    if (!canEdit || !allowAutomatic) return;
    setError('');
    if (!imageRef.current || !isPoint(points[selected])) { setError('Klik perkiraan pusat pupil terlebih dahulu untuk menentukan area pencarian satu mata.'); return; }
    if (!/pupil/i.test(selected)) { setError('Pilih titik pupil OD atau OS untuk bantuan kandidat.'); return; }
    try {
      const canvas = document.createElement('canvas'); canvas.width = width; canvas.height = height;
      const context = canvas.getContext('2d', { willReadFrequently: true }); context.drawImage(imageRef.current, 0, 0);
      const radius = Math.max(12, Math.round(Math.min(width, height) * 0.055));
      const p = points[selected];
      const candidate = suggestPupil(context.getImageData(0, 0, width, height), { x: Math.max(0, p.x - radius), y: Math.max(0, p.y - radius), width: 2 * radius, height: 2 * radius });
      setDetection(candidate);
      if (candidate.found) {
        onAutomaticPoints?.({ ...automaticPoints, [selected]: candidate.candidate }, { pointKey: selected, detection: candidate });
        commit({ ...currentRef.current, [selected]: candidate.candidate });
      }
    } catch { setError('Kandidat tidak dapat diproses. Tentukan titik secara manual.'); }
  };

  const visiblePoints = before ? automaticPoints : points;
  const lines = useMemo(() => [
    ['markerTL', 'markerTR'], ['markerTR', 'markerBR'], ['markerBR', 'markerBL'], ['markerBL', 'markerTL'],
    ['referenceStart', 'referenceEnd'], ['segmentStart', 'segmentEnd'], ['scaleStart', 'scaleEnd'], ['midlineTop', 'midlineBottom'],
    ['rightPupil', 'leftPupil'], ['cornea', 'backLens'], ['gazeStart', 'gazeEnd'],
    ['lensTop', 'lensBottom'], ['verticalTop', 'verticalBottom'],
  ].filter(([a, b]) => isPoint(visiblePoints[a]) && isPoint(visiblePoints[b])), [visiblePoints]);

  if (!imageValid) return <p role="alert" className="p-4 border border-red-300 rounded-xl">Gunakan gambar privat JPEG, PNG atau WebP beserta dimensi asli yang valid (maksimal 24 MP).</p>;

  return <section className="space-y-3" aria-label="Koreksi titik ukur" data-testid="optifit-landmark-editor">
    <div className="flex flex-wrap gap-2 items-end">
      <label className="block flex-1 min-w-[180px] text-sm font-medium">Titik yang dipilih
        <select className="block w-full mt-1 p-3 border rounded-lg bg-transparent" value={selected} onChange={event => setSelected(event.target.value)} data-testid="optifit-point-select">
          {pointDefinitions.map(definition => <option key={definition.key} value={definition.key}>{definition.label}</option>)}
        </select>
      </label>
      <button type="button" aria-pressed={mode === 'point'} disabled={!canEdit} className="min-h-12 px-3 border rounded-lg inline-flex items-center gap-2 disabled:opacity-40" onClick={() => setMode('point')}><Crosshair size={18} />Titik</button>
      <button type="button" aria-pressed={mode === 'pan'} className="min-h-12 px-3 border rounded-lg inline-flex items-center gap-2" onClick={() => setMode('pan')}><Hand size={18} />Geser gambar</button>
    </div>
    <p className="text-xs">Pilih label lalu ketuk/geser titik. Tombol pan menggeser gambar. Tombol panah mengoreksi 1 piksel; Shift + panah 10 piksel. Koordinat selalu disimpan terhadap gambar asli tanpa mirror.</p>
    <div className="relative overflow-hidden rounded-xl border bg-slate-900" style={{ aspectRatio: `${width} / ${height}`, maxHeight: '65vh', minHeight: 240 }}>
      <svg ref={svgRef} viewBox={`0 0 ${width} ${height}`} className="w-full h-full" style={{ touchAction: 'none', cursor: mode === 'pan' ? 'grab' : 'crosshair', maxHeight: '65vh', minHeight: 240 }}
        role="application" aria-label="Gambar dan titik fitting. Pilih titik pada daftar lalu klik atau gunakan tombol panah." tabIndex={0}
        onKeyDown={shiftPoint} onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={cancelDrag} onPointerLeave={() => { if (!dragRef.current) setHover(null); }}>
        <g transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
          <image href={image.dataUrl} width={width} height={height} />
          {lines.map(([a, b]) => <line key={`${a}-${b}`} x1={visiblePoints[a].x} y1={visiblePoints[a].y} x2={visiblePoints[b].x} y2={visiblePoints[b].y} stroke={a.startsWith('marker') ? '#fbbf24' : '#34d399'} strokeWidth={Math.max(width / 700, 1) / zoom} strokeDasharray={a.includes('midline') || a.includes('gaze') ? `${width / 100 / zoom} ${width / 150 / zoom}` : undefined} />)}
          {pointDefinitions.map(definition => {
            const p = visiblePoints[definition.key]; if (!isPoint(p)) return null;
            const auto = automaticPoints[definition.key]; const unchangedAuto = isPoint(auto) && Math.abs(auto.x - p.x) < 0.001 && Math.abs(auto.y - p.y) < 0.001;
            const radius = Math.max(width / 110, 5) / zoom; const color = unchangedAuto ? '#fbbf24' : '#22d3ee';
            return <g key={definition.key}>
              <circle cx={p.x} cy={p.y} r={radius} fill="none" stroke={selected === definition.key ? '#fff' : color} strokeWidth={Math.max(width / 350, 1.5) / zoom} />
              <path d={`M${p.x - radius * 1.6} ${p.y}H${p.x + radius * 1.6}M${p.x} ${p.y - radius * 1.6}V${p.y + radius * 1.6}`} stroke={color} strokeWidth={Math.max(width / 500, 1) / zoom} />
              <text x={p.x + radius * 2} y={p.y - radius * 1.8} fontSize={Math.max(width / 58, 12) / zoom} fill="white" stroke="#0f172a" strokeWidth={Math.max(width / 1100, 0.3) / zoom} paintOrder="stroke">{definition.shortLabel || definition.label}</text>
            </g>;
          })}
        </g>
      </svg>
      {loadingImage && <div className="absolute left-2 top-2 bg-slate-950/80 text-white text-xs p-2 rounded">Membaca gambar privat…</div>}
      {hover && <div className="absolute bottom-2 right-2 w-28 h-28 rounded-full overflow-hidden border-2 border-white shadow-lg pointer-events-none" aria-label="Kaca pembesar">
        <svg viewBox={`${hover.x - width / 24} ${hover.y - width / 24} ${width / 12} ${width / 12}`} className="w-full h-full bg-slate-900">
          <image href={image.dataUrl} width={width} height={height} />
          <path d={`M${hover.x - width / 60} ${hover.y}H${hover.x + width / 60}M${hover.x} ${hover.y - width / 60}V${hover.y + width / 60}`} stroke="#22d3ee" strokeWidth={width / 1200} />
        </svg>
      </div>}
    </div>
    <div className="flex flex-wrap gap-2 items-center">
      <button type="button" className="min-h-11 px-3 border rounded-lg" onClick={() => setZoom(value => Math.max(1, value - 0.5))} aria-label="Perkecil gambar"><ZoomOut size={18} /></button>
      <label className="text-sm flex items-center gap-2">Zoom <input aria-label="Perbesaran gambar" type="range" min="1" max="6" step="0.25" value={zoom} onChange={event => setZoom(Number(event.target.value))} className="w-24" /><span>{zoom.toFixed(2)}×</span></label>
      <button type="button" className="min-h-11 px-3 border rounded-lg" onClick={() => setZoom(value => Math.min(6, value + 0.5))} aria-label="Perbesar gambar"><ZoomIn size={18} /></button>
      <button type="button" className="min-h-11 px-3 border rounded-lg text-sm" onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}>Atur tampilan</button>
      <button type="button" className="min-h-11 px-3 border rounded-lg disabled:opacity-40" onClick={undo} disabled={!canEdit || historyState.index === 0} aria-label="Undo koreksi"><Undo2 size={18} /></button>
      <button type="button" className="min-h-11 px-3 border rounded-lg disabled:opacity-40" onClick={redo} disabled={!canEdit || historyState.index >= historyState.length - 1} aria-label="Redo koreksi"><Redo2 size={18} /></button>
    </div>
    <div className="flex flex-wrap gap-2">
      {allowAutomatic && <button type="button" className="min-h-11 px-3 border rounded-lg text-sm inline-flex items-center gap-2 disabled:opacity-40" disabled={!canEdit || loadingImage || !/pupil/i.test(selected)} onClick={findPupil}><Search size={16} />Cari kandidat pupil di area titik</button>}
      <button type="button" className="min-h-11 px-3 border rounded-lg text-sm inline-flex items-center gap-2 disabled:opacity-40" disabled={!canEdit || !Object.keys(automaticPoints).length} onClick={() => { setBefore(false); commit({ ...currentRef.current, ...clone(automaticPoints) }); }}><RotateCcw size={16} />Reset ke titik awal otomatis</button>
      <button type="button" className="min-h-11 px-3 border rounded-lg text-sm disabled:opacity-40" aria-pressed={before} disabled={!Object.keys(automaticPoints).length} onClick={() => setBefore(value => !value)}>{before ? 'Lihat sesudah koreksi' : 'Bandingkan titik otomatis'}</button>
    </div>
    <p className="text-xs">Kuning: kandidat otomatis yang belum dikonfirmasi. Biru: penempatan/koreksi operator. Label tanpa titik masih belum ditandai. Titik awal dan koreksi disimpan sebagai revisi terpisah ketika Anda menyimpan sesi.</p>
    {isPoint(points[selected]) && <div className="text-xs" role="status">{pointDefinitions.find(p => p.key === selected)?.label}: x {points[selected].x.toFixed(2)}, y {points[selected].y.toFixed(2)} piksel asli.</div>}
    {detection && <p role="status" className="text-sm border rounded-lg p-3">{detection.reasons.join(' ')}</p>}
    {error && <p role="alert" className="text-sm border border-red-300 text-red-800 bg-red-50 rounded-lg p-3">{error}</p>}
  </section>;
}
