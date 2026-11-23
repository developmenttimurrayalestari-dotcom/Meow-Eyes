import React, { useEffect, useRef, useState } from 'react';

const project = (lat, lng, z) => {
  const size = 256 * 2 ** z, sin = Math.sin(Math.max(-85.0511, Math.min(85.0511, lat)) * Math.PI / 180);
  return { x: (lng + 180) / 360 * size, y: (0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI)) * size };
};
const unproject = (x, y, z) => {
  const size = 256 * 2 ** z;
  return { latitude: Math.atan(Math.sinh(Math.PI * (1 - 2 * y / size))) * 180 / Math.PI, longitude: ((x / size * 360 + 180) % 360 + 360) % 360 - 180 };
};

export default function AddressPinpoint({ value, onChange, disabled }) {
  const valid = value.latitude !== '' && value.longitude !== '' && value.latitude != null && value.longitude != null && Number.isFinite(Number(value.latitude)) && Number.isFinite(Number(value.longitude)) && Math.abs(Number(value.latitude)) <= 90 && Math.abs(Number(value.longitude)) <= 180;
  const [view, setView] = useState({ latitude: valid ? Number(value.latitude) : -2.5, longitude: valid ? Number(value.longitude) : 118, zoom: valid ? 16 : 4 });
  const [width, setWidth] = useState(360), [error, setError] = useState(''), [locating, setLocating] = useState(false);
  const map = useRef(), drag = useRef();
  useEffect(() => {
    if (!window.ResizeObserver) return;
    const observer = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
    observer.observe(map.current); return () => observer.disconnect();
  }, []);
  const center = project(view.latitude, view.longitude, view.zoom), tiles = [];
  const count = 2 ** view.zoom;
  for (let x = Math.floor((center.x - width / 2) / 256); x <= Math.floor((center.x + width / 2) / 256); x++) {
    for (let y = Math.floor((center.y - 128) / 256); y <= Math.floor((center.y + 128) / 256); y++) {
      if (y < 0 || y >= count) continue;
      tiles.push(<img key={`${view.zoom}-${x}-${y}`} draggable="false" alt="" src={`https://tile.openstreetmap.org/${view.zoom}/${((x % count) + count) % count}/${y}.png`} className="absolute h-64 w-64 max-w-none select-none pointer-events-none" style={{ left: x * 256 - center.x + width / 2, top: y * 256 - center.y + 128 }} />);
    }
  }
  const pin = valid ? project(Number(value.latitude), Number(value.longitude), view.zoom) : null;
  const setPoint = point => { onChange({ latitude: point.latitude.toFixed(7), longitude: point.longitude.toFixed(7) }); setError(''); };
  const locate = () => {
    if (!navigator.geolocation) { setError('Lokasi perangkat tidak tersedia. Pilih titik di peta atau isi koordinat.'); return; }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(position => {
      const point = { latitude: position.coords.latitude, longitude: position.coords.longitude };
      setPoint(point); setView({ ...point, zoom: 16 }); setLocating(false);
    }, () => { setError('Lokasi perangkat belum diizinkan. Pilih titik di peta atau isi koordinat.'); setLocating(false); }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
  };
  const pan = (dx, dy) => setView(v => ({ ...unproject(center.x + dx, Math.max(0, Math.min(256 * 2 ** v.zoom, center.y + dy)), v.zoom), zoom: v.zoom }));
  return <fieldset disabled={disabled} className="sm:col-span-2 border rounded-2xl p-3 space-y-3" data-testid="address-pinpoint"><legend className="px-1 font-semibold">Titik pengantaran (opsional)</legend>
    <p className="text-xs text-meow-gray">Diperlukan untuk layanan Instant/Sameday yang memakai titik lokasi. Geser peta, lalu ketuk lokasi alamat tujuan. Titik harus sesuai alamat yang dipilih.</p>
    <div ref={map} tabIndex={disabled ? -1 : 0} role="application" aria-label="Peta titik pengantaran. Panah menggeser, Enter memilih titik tengah." className="relative h-64 w-full overflow-hidden rounded-xl bg-slate-100 touch-none cursor-crosshair border" onKeyDown={e => { if (disabled) return; if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter'].includes(e.key)) e.preventDefault(); if (e.key === 'Enter') setPoint(view); else if (e.key === 'ArrowLeft') pan(-100,0); else if (e.key === 'ArrowRight') pan(100,0); else if (e.key === 'ArrowUp') pan(0,-100); else if (e.key === 'ArrowDown') pan(0,100); }}
      onPointerDown={e => { if (disabled || e.target.closest('button, a')) return; drag.current = { x: e.clientX, y: e.clientY }; e.currentTarget.setPointerCapture?.(e.pointerId); }}
      onPointerCancel={() => { drag.current = null; }}
      onPointerUp={e => { if (!drag.current || disabled) return; const delta = { x: e.clientX - drag.current.x, y: e.clientY - drag.current.y }; drag.current = null; if (Math.hypot(delta.x, delta.y) > 6) pan(-delta.x, -delta.y); else { const rect = e.currentTarget.getBoundingClientRect(); setPoint(unproject(center.x + e.clientX - rect.left - width / 2, Math.max(0, Math.min(count * 256, center.y + e.clientY - rect.top - 128)), view.zoom)); } }}>
      {tiles}
      {pin && <span aria-hidden="true" className="absolute h-5 w-5 rounded-full bg-meow-salmon border-[3px] border-white shadow-lg pointer-events-none" style={{ left: pin.x - center.x + width / 2 - 10, top: pin.y - center.y + 118 }} />}
      <div className="absolute left-2 top-2 flex flex-col bg-white rounded-lg shadow"><button type="button" aria-label="Perbesar peta" onClick={() => setView(v => ({ ...v, zoom: Math.min(18, v.zoom + 1) }))} className="px-3 py-1 text-lg">+</button><button type="button" aria-label="Perkecil peta" onClick={() => setView(v => ({ ...v, zoom: Math.max(2, v.zoom - 1) }))} className="px-3 py-1 text-lg">−</button></div>
      <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer" className="absolute bottom-0 right-0 bg-white/90 px-1 text-[10px]">© OpenStreetMap contributors</a>
    </div>
    <div className="flex flex-wrap gap-2"><button type="button" disabled={locating} onClick={locate} className="text-xs font-bold underline">{locating ? 'Mencari lokasi…' : 'Gunakan Lokasi Saya'}</button>{valid && <button type="button" onClick={() => setView({ latitude: Number(value.latitude), longitude: Number(value.longitude), zoom: 16 })} className="text-xs underline">Lihat titik</button>}<button type="button" onClick={() => onChange({ latitude: '', longitude: '' })} className="text-xs underline">Hapus titik</button></div>
    <div className="grid grid-cols-2 gap-2">{[['latitude','Latitude',-90,90],['longitude','Longitude',-180,180]].map(([key,label,min,max]) => <label key={key} className="text-xs">{label}<input type="number" min={min} max={max} step="any" value={value[key] ?? ''} onChange={e => onChange({ ...value, [key]: e.target.value })} className="block w-full mt-1 border rounded-lg p-2" /></label>)}</div>
    {error && <p role="status" className="text-xs text-amber-700">{error}</p>}
  </fieldset>;
}
