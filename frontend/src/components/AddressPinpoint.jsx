import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { api, apiError } from '../lib/api';

const validPoint = (value) => value.latitude !== '' && value.longitude !== '' && value.latitude != null && value.longitude != null && Number.isFinite(Number(value.latitude)) && Number.isFinite(Number(value.longitude)) && Math.abs(Number(value.latitude)) <= 90 && Math.abs(Number(value.longitude)) <= 180;
const pinIcon = L.divIcon({ className: '', html: '<span style="display:block;margin:11px;width:22px;height:22px;background:#ff656b;border:3px solid white;border-radius:50%;box-shadow:0 2px 8px #0008"></span>', iconSize: [44, 44], iconAnchor: [22, 22] });

export default function AddressPinpoint({ value, onChange, disabled = false, searchHint = '' }) {
  const searchId = useId();
  const container = useRef(null), map = useRef(null), marker = useRef(null);
  const latest = useRef({ value, onChange, disabled });
  latest.current = { value, onChange, disabled };
  const alive = useRef(false), request = useRef(null);
  const [query, setQuery] = useState(''), [results, setResults] = useState([]);
  const [error, setError] = useState(''), [searching, setSearching] = useState(false), [locating, setLocating] = useState(false);
  const [searched, setSearched] = useState(false);
  const valid = validPoint(value);
  const choose = useCallback((lat, lng) => {
    if (!alive.current || latest.current.disabled) return;
    const point = L.latLng(lat, lng).wrap();
    latest.current.onChange({ latitude: point.lat.toFixed(7), longitude: point.lng.toFixed(7) });
    setError('');
  }, []);
  useEffect(() => {
    alive.current = true;
    const initial = latest.current.value;
    const hasPoint = validPoint(initial);
    const instance = L.map(container.current, { scrollWheelZoom: true, touchZoom: true, dragging: true, keyboard: true, zoomControl: false, worldCopyJump: true });
    map.current = instance;
    instance.setView(hasPoint ? [Number(initial.latitude), Number(initial.longitude)] : [-2.5, 118], hasPoint ? 16 : 4);
    L.control.zoom({ zoomInTitle: 'Perbesar peta', zoomOutTitle: 'Perkecil peta' }).addTo(instance);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(instance);
    instance.on('click', (event) => choose(event.latlng.lat, event.latlng.lng));
    const observer = window.ResizeObserver ? new ResizeObserver(() => instance.invalidateSize()) : null;
    observer?.observe(container.current);
    return () => { alive.current = false; request.current?.abort(); observer?.disconnect(); instance.remove(); map.current = null; marker.current = null; };
  }, [choose]); // Map events read the current callback and disabled state from latest.
  useEffect(() => {
    if (!map.current) return;
    if (!valid) { marker.current?.remove(); marker.current = null; return; }
    const point = [Number(value.latitude), Number(value.longitude)];
    if (!marker.current) {
      marker.current = L.marker(point, { icon: pinIcon, draggable: !disabled, title: 'Geser titik pengantaran', autoPan: true }).addTo(map.current);
      marker.current.on('dragend', () => { const position = marker.current.getLatLng(); choose(position.lat, position.lng); });
    } else marker.current.setLatLng(point);
    map.current.setView(point, Math.max(16, map.current.getZoom()));
  }, [value.latitude, value.longitude, valid, choose, disabled]);
  useEffect(() => {
    const instance = map.current;
    if (!instance) return;
    for (const key of ['dragging', 'touchZoom', 'scrollWheelZoom', 'doubleClickZoom', 'boxZoom', 'keyboard']) instance[key]?.[disabled ? 'disable' : 'enable']();
    marker.current?.dragging?.[disabled ? 'disable' : 'enable']();
    if (disabled) { request.current?.abort(); setSearching(false); }
  }, [disabled, valid]);
  const editQuery = (text) => {
    request.current?.abort(); setSearching(false); setQuery(text); setResults([]); setSearched(false);
  };
  const search = async () => {
    if (disabled || searching) return;
    const text = (query.trim() || searchHint.trim()).slice(0, 200);
    if (text.length < 3) { setError('Ketik minimal 3 karakter nama jalan, tempat, atau alamat.'); return; }
    request.current?.abort(); const controller = new AbortController(); request.current = controller;
    setSearching(true); setError(''); setResults([]); setSearched(false);
    try {
      const { data } = await api.post('/shipping/map-search', { query: text }, { signal: controller.signal });
      if (!alive.current || controller.signal.aborted) return;
      setResults(data.results || []); setSearched(true);
    } catch (err) {
      if (alive.current && !controller.signal.aborted) setError(apiError(err, 'Pencarian belum tersedia. Pilih titik di peta atau gunakan lokasi saya.'));
    } finally { if (alive.current && request.current === controller) setSearching(false); }
  };
  const locate = () => {
    if (!navigator.geolocation) { setError('Lokasi perangkat tidak tersedia. Pilih titik di peta atau isi koordinat.'); return; }
    setLocating(true);
    navigator.geolocation.getCurrentPosition((position) => {
      if (!alive.current) return;
      choose(position.coords.latitude, position.coords.longitude); setLocating(false);
    }, () => { if (alive.current) { setError('Lokasi perangkat belum diizinkan. Pilih titik di peta atau cari alamat.'); setLocating(false); } }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
  };
  return <fieldset disabled={disabled} className="sm:col-span-2 border rounded-2xl p-3 space-y-3 min-w-0" data-testid="address-pinpoint">
    <legend className="px-1 font-semibold">Titik pengantaran (opsional)</legend>
    <p className="text-xs text-meow-gray">Untuk Instant/Sameday. Cari alamat atau tempat terdekat, lalu geser pin ke lokasi tujuan. Titik harus sesuai wilayah alamat pengiriman yang dipilih.</p>
    <div className="space-y-1">
      <label htmlFor={searchId} className="block text-xs font-semibold">Cari alamat atau nama tempat</label>
      <div className="flex gap-2">
        <input id={searchId} type="search" value={query} maxLength={200} onChange={(event) => editQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); search(); } }} placeholder="Contoh: Jalan Rawa Kepiting, Jakarta Timur" className="min-w-0 flex-1 border rounded-xl p-2" />
        <button type="button" disabled={disabled || searching} onClick={search} className="btn-secondary px-4 py-2 text-xs disabled:opacity-50">{searching ? 'Mencari…' : 'Cari'}</button>
      </div>
      {searchHint && <button type="button" disabled={disabled || searching} onClick={() => editQuery(searchHint.slice(0, 200))} className="text-xs underline">Gunakan alamat yang diisi sebagai kata pencarian</button>}
      <p className="text-xs text-meow-gray">Pencarian dikirim ke layanan peta hanya setelah menekan Cari.</p>
    </div>
    {searching && <p role="status" className="text-xs">Mencari alamat…</p>}
    {results.length > 0 && <ul aria-label="Hasil pencarian alamat" className="border rounded-xl max-h-48 overflow-y-auto divide-y">{results.map((result, index) => <li key={index}><button type="button" className="text-left w-full p-3 text-xs hover:bg-slate-50" onClick={() => { choose(result.latitude, result.longitude); setResults([]); setSearched(false); }}>{result.label}</button></li>)}</ul>}
    {searched && !results.length && <p role="status" className="text-xs">Alamat belum ditemukan. Coba nama jalan, tempat terdekat, dan nama kota; atau pilih titik langsung di peta.</p>}
    <div ref={container} inert={disabled ? true : undefined} tabIndex={disabled ? -1 : 0} role="application" aria-label="Peta titik pengantaran. Geser peta atau pin, cubit atau gulir untuk zoom. Enter memilih titik tengah." className="relative z-0 h-80 sm:h-96 w-full rounded-xl bg-slate-100 border" onKeyDown={(event) => { if (event.key === 'Enter' && !disabled && event.target === container.current) { event.preventDefault(); const point = map.current.getCenter(); choose(point.lat, point.lng); } }} />
    <p className="text-xs text-meow-gray">Geser peta dengan jari/mouse. Cubit dengan dua jari atau gunakan +/− untuk zoom. Ketuk peta untuk memasang pin, lalu seret pin agar lebih tepat.</p>
    <div className="flex flex-wrap gap-3 text-xs">
      <button type="button" disabled={disabled || locating} onClick={locate} className="font-bold underline">{locating ? 'Mencari lokasi…' : 'Gunakan Lokasi Saya'}</button>
      {valid && <button type="button" onClick={() => map.current?.setView([Number(value.latitude), Number(value.longitude)], 17)} className="underline">Lihat titik</button>}
      <button type="button" onClick={() => onChange({ latitude: '', longitude: '' })} className="underline">Hapus titik</button>
      <a href="https://photon.komoot.io/" target="_blank" rel="noreferrer" className="text-meow-gray underline">Pencarian: Photon / OpenStreetMap</a>
    </div>
    <details><summary className="text-xs cursor-pointer">Isi koordinat secara manual (opsional)</summary><div className="grid grid-cols-2 gap-2 mt-2">{[['latitude', 'Latitude', -90, 90], ['longitude', 'Longitude', -180, 180]].map(([key, label, min, max]) => <label key={key} className="text-xs">{label}<input type="number" min={min} max={max} step="any" value={value[key] ?? ''} onChange={(event) => onChange({ ...value, [key]: event.target.value })} className="block w-full mt-1 border rounded-lg p-2" /></label>)}</div></details>
    {error && <p role="status" className="text-xs text-amber-700">{error}</p>}
  </fieldset>;
}
