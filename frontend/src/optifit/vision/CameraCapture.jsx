import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Camera, RefreshCw, StopCircle, X } from 'lucide-react';
import { VIEW_LABELS } from './constants';
import { analyseImage, rankBurstSamples } from './quality';

const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const smallAnalysis = source => {
  const canvas = document.createElement('canvas');
  const width = source.videoWidth || source.width; const height = source.videoHeight || source.height;
  const scale = Math.min(1, 320 / Math.max(width, height));
  canvas.width = Math.max(4, Math.round(width * scale));
  canvas.height = Math.max(4, Math.round(height * scale));
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.drawImage(source, 0, 0, canvas.width, canvas.height);
  return analyseImage(context.getImageData(0, 0, canvas.width, canvas.height));
};

export default function CameraCapture({ view = 'frontal', consent = false, checklistComplete = false, onCapture, onCancel, disabled = false, uploadEnabled = false, customerMode = false }) {
  const videoRef = useRef(null); const streamRef = useRef(null); const generation = useRef(0); const mounted = useRef(true);
  const captureRef = useRef(null); const capturingRef = useRef(false); const previousAnalysis = useRef(null); const stableCount = useRef(0);
  const [running, setRunning] = useState(false); const [opening, setOpening] = useState(false); const [capturing, setCapturing] = useState(false);
  const [error, setError] = useState(''); const [analysis, setAnalysis] = useState(null); const [devices, setDevices] = useState([]);
  const [deviceId, setDeviceId] = useState(''); const [metadata, setMetadata] = useState({}); const [autoCapture, setAutoCapture] = useState(false);
  const [orientation, setOrientation] = useState(null); const [sensorEnabled, setSensorEnabled] = useState(false);
  const ready = consent === true && checklistComplete === true && !disabled;

  const stop = useCallback(() => {
    generation.current += 1; capturingRef.current = false; stableCount.current = 0; previousAnalysis.current = null;
    streamRef.current?.getTracks().forEach(track => track.stop()); streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    if (mounted.current) { setRunning(false); setOpening(false); setCapturing(false); setAutoCapture(false); }
  }, []);

  useEffect(() => {
    mounted.current = true;
    const visibility = () => { if (document.hidden) stop(); };
    document.addEventListener('visibilitychange', visibility);
    window.addEventListener('pagehide', stop);
    return () => { mounted.current = false; stop(); document.removeEventListener('visibilitychange', visibility); window.removeEventListener('pagehide', stop); };
  }, [stop]);

  useEffect(() => { stop(); setAnalysis(null); setError(''); }, [view, stop]);
  useEffect(() => { if (!ready) stop(); }, [ready, stop]);

  useEffect(() => {
    if (!sensorEnabled) return undefined;
    const listener = event => setOrientation({ beta: Number.isFinite(event.beta) ? event.beta : null, gamma: Number.isFinite(event.gamma) ? event.gamma : null });
    window.addEventListener('deviceorientation', listener);
    return () => window.removeEventListener('deviceorientation', listener);
  }, [sensorEnabled]);

  const enableSensor = async () => {
    try {
      if (!window.DeviceOrientationEvent) { setError('Sensor orientasi tidak tersedia. Periksa garis horizontal dan posisi ponsel secara manual.'); return; }
      if (typeof window.DeviceOrientationEvent.requestPermission === 'function') {
        const permission = await window.DeviceOrientationEvent.requestPermission();
        if (permission !== 'granted') { setError('Izin sensor ditolak. Pemeriksaan posisi ponsel tetap dapat dilakukan manual.'); return; }
      }
      setSensorEnabled(true); setError('');
    } catch { setError('Sensor orientasi tidak dapat diakses pada browser ini.'); }
  };

  const start = async selectedId => {
    if (!ready || opening) return;
    if (process.env.NODE_ENV === 'production' && !window.isSecureContext) { setError('Kamera memerlukan HTTPS/localhost dan browser yang mendukung getUserMedia. Gunakan gambar dari kamera privat yang disetujui bila kamera browser tidak tersedia.'); return; }
    if (!navigator.mediaDevices?.getUserMedia) { setError('Browser tidak menyediakan akses kamera pada alamat ini. Untuk pengembangan, buka localhost atau izinkan alamat LAN sebagai secure origin di pengaturan browser. Anda tetap dapat menggunakan gambar privat yang disetujui.'); return; }
    stop(); setOpening(true); setError(''); const current = generation.current;
    const desiredId = selectedId || deviceId;
    let stream;
    try {
      const constraints = { audio: false, video: { ...(desiredId ? { deviceId: { exact: desiredId } } : { facingMode: { ideal: 'environment' } }), width: { ideal: 1920, max: 3840 }, height: { ideal: 1080, max: 2160 } } };
      try { stream = await navigator.mediaDevices.getUserMedia(constraints); }
      catch (err) {
        if (err.name !== 'OverconstrainedError' || desiredId) throw err;
        stream = await navigator.mediaDevices.getUserMedia({ audio: false, video: { facingMode: { ideal: 'environment' } } });
      }
      if (!mounted.current || current !== generation.current || document.hidden) { stream.getTracks().forEach(track => track.stop()); return; }
      const track = stream.getVideoTracks()[0];
      const capabilities = track.getCapabilities?.() || {};
      if (capabilities.zoom && capabilities.zoom.min <= 1 && capabilities.zoom.max >= 1) {
        try { await track.applyConstraints({ advanced: [{ zoom: 1 }] }); } catch { /* Actual setting is displayed below; never pretend it changed. */ }
      }
      if (!mounted.current || current !== generation.current || document.hidden) { stream.getTracks().forEach(t => t.stop()); return; }
      streamRef.current = stream;
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      if (!mounted.current || current !== generation.current || document.hidden) { stream.getTracks().forEach(t => t.stop()); return; }
      const settings = track.getSettings();
      setMetadata({ width: settings.width || null, height: settings.height || null, frameRate: settings.frameRate || null, facingMode: settings.facingMode || 'unknown', zoom: settings.zoom ?? null, cameraLabel: track.label || 'Tidak tersedia', mirrored: false, intrinsics: null, depth: null });
      let cameras = [];
      try { cameras = (await navigator.mediaDevices.enumerateDevices?.() || []).filter(device => device.kind === 'videoinput'); } catch { /* Enumeration is optional; a working camera must remain usable. */ }
      if (!mounted.current || current !== generation.current) { stream.getTracks().forEach(t => t.stop()); return; }
      setDevices(cameras); if (settings.deviceId) setDeviceId(settings.deviceId);
      setRunning(true); setOpening(false);
    } catch (err) {
      stream?.getTracks().forEach(track => track.stop());
      if (mounted.current && current === generation.current) {
        setOpening(false); setRunning(false);
        setError(err.name === 'NotAllowedError' ? 'Izin kamera ditolak. Anda tetap dapat menggunakan mode manual dan gambar privat dengan persetujuan pasien.' : `Kamera tidak dapat dibuka: ${err.message || err.name}.`);
      }
    }
  };

  const capture = useCallback(async () => {
    if (!ready || !running || capturingRef.current || !videoRef.current?.videoWidth) return;
    capturingRef.current = true; setCapturing(true); setAutoCapture(false); setError(''); const current = generation.current;
    try {
      const video = videoRef.current; const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth; canvas.height = video.videoHeight;
      if (canvas.width * canvas.height > 24000000) throw new Error('Resolusi melebihi batas 24 MP; pilih kamera/resolusi yang didukung.');
      const context = canvas.getContext('2d'); const samples = [];
      for (let index = 0; index < 5; index += 1) {
        if (!mounted.current || current !== generation.current || document.hidden) throw new Error('Pengambilan dibatalkan karena kamera ditutup atau tab tidak aktif.');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const frameAnalysis = smallAnalysis(canvas);
        samples.push({ index, width: canvas.width, height: canvas.height, dataUrl: canvas.toDataURL('image/jpeg', 0.94), analysis: frameAnalysis, capturedAt: new Date().toISOString() });
        if (index < 4) await wait(120);
      }
      const ranked = rankBurstSamples(samples);
      if (!ranked.valid) throw new Error(ranked.reasons.join(' '));
      const selected = ranked.selectedIndices.map(index => samples[index]);
      const payload = { view, width: canvas.width, height: canvas.height, dataUrl: selected[0].dataUrl,
        chosenIndex: selected[0].index, samples: selected, burstAnalysis: ranked,
        deviceMetadata: { ...metadata, orientation, mainCameraVerifiedByOperator: !customerMode && checklistComplete, sourceWidth: video.videoWidth, sourceHeight: video.videoHeight },
        capturedAt: new Date().toISOString(), rawCoordinatesMirrored: false };
      stop();
      await onCapture?.(payload);
    } catch (err) {
      if (mounted.current) setError(err.message || 'Gambar tidak dapat diambil. Coba lagi.');
    } finally {
      capturingRef.current = false; if (mounted.current) setCapturing(false);
    }
  }, [ready, running, view, metadata, orientation, checklistComplete, customerMode, onCapture, stop]);

  useEffect(() => { captureRef.current = capture; }, [capture]);
  useEffect(() => {
    if (!running) return undefined;
    const timer = setInterval(() => {
      if (capturingRef.current || !videoRef.current?.videoWidth) return;
      try {
        const next = smallAnalysis(videoRef.current); setAnalysis(next);
        const prev = previousAnalysis.current; previousAnalysis.current = next;
        const difference = prev?.signature?.length === next.signature?.length
          ? next.signature.reduce((sum, value, i) => sum + Math.abs(value - prev.signature[i]), 0) / next.signature.length / 255 : 1;
        if (next.usable && difference < 0.025) stableCount.current += 1; else stableCount.current = 0;
        if (autoCapture && ready && stableCount.current >= 3) { stableCount.current = 0; captureRef.current?.(); }
      } catch { setAnalysis(null); }
    }, 500);
    return () => clearInterval(timer);
  }, [running, autoCapture, ready]);

  const frontal = view.startsWith('frontal');
  return <section className="space-y-4" aria-label="Pengambilan gambar fitting" data-testid="optifit-camera">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h3 className="text-lg font-bold">{VIEW_LABELS[view] || view}</h3>
      <button type="button" onClick={() => { stop(); onCancel?.(); }} className="min-h-11 px-3 rounded-lg border" aria-label="Tutup kamera"><X size={18} /></button>
    </div>
    {!ready && <p role="alert" className="rounded-xl bg-amber-50 text-amber-900 p-3">Baca panduan dan simpan persetujuan foto sebelum membuka kamera.</p>}
    <p className="text-sm leading-relaxed">{customerMode ? (frontal ? 'Lihat ke arah yang sesuai panduan dan posisikan kamera sejajar mata. Pastikan kedua mata dan satu lensa frame terlihat utuh.' : 'Ambil sisi wajah sesuai panduan. Minta bantuan orang lain dan pastikan area yang diukur terlihat jelas.') : view === 'frontal' ? 'Pasien melihat target jauh di belakang/samping operator, bukan layar. Kamera sejajar mata, frame utuh. OD pasien berada di kiri gambar kamera belakang.' : view === 'frontal_near' ? 'Catat jarak kerja dan tempatkan target dekat pada jarak tersebut. Hasil disimpan terpisah dari PD jauh.' : 'Ambil sisi pasien sesuai label. Referensi skala harus berada dekat bidang ukur; permukaan belakang lensa dan apex kornea perlu terlihat untuk VD.'}</p>
    <div className="of-camera-station" data-testid="optifit-camera-station">
    <div className="relative overflow-hidden rounded-2xl bg-slate-950 aspect-[4/3] max-h-[65vh]">
      <video ref={videoRef} muted playsInline autoPlay className="w-full h-full object-contain" aria-label="Pratinjau kamera tanpa mirror" />
      <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
        <path d="M200 12V288M12 150H388" stroke="#67e8f9" strokeWidth="1" strokeDasharray="6 6" opacity=".65" />
        {frontal ? <><ellipse cx="200" cy="150" rx="80" ry="116" fill="none" stroke="#e2e8f0" strokeWidth="2" strokeDasharray="9 6" /><path d="M114 126H286M140 110V144M260 110V144" stroke="#fbbf24" fill="none" opacity=".9" /></>
          : <path d="M250 266C180 280 117 220 118 128C120 38 218 19 251 72L272 120L289 145L268 156L267 190C260 220 240 223 241 252" fill="none" stroke="#e2e8f0" strokeWidth="2" strokeDasharray="8 6" transform={view.endsWith('left') ? 'translate(400 0) scale(-1 1)' : undefined} />}
      </svg>
      {!running && <div className="absolute inset-0 grid place-items-center text-slate-200 text-center p-6"><p>{opening ? 'Menunggu izin kamera…' : 'Panduan posisi. Kamera belum aktif.'}</p></div>}
      {capturing && <div role="status" className="absolute bottom-3 left-3 right-3 rounded-lg p-3 bg-slate-950/80 text-white">Mengambil 5 frame; pertahankan posisi…</div>}
    </div>
    <div className="of-camera-controls" data-testid="optifit-camera-controls">
      {!running ? <button type="button" className="min-h-12 px-5 py-3 rounded-xl bg-teal-700 text-white font-semibold disabled:opacity-50 inline-flex gap-2 items-center" disabled={!ready || opening} onClick={() => start()} data-testid="optifit-camera-start"><Camera size={18} />{opening ? 'Membuka…' : 'Buka kamera'}</button>
        : <><button type="button" onClick={capture} disabled={capturing || !ready} className="min-h-12 px-5 py-3 rounded-xl bg-teal-700 text-white font-semibold disabled:opacity-50 inline-flex gap-2 items-center" data-testid="optifit-camera-capture"><Camera size={18} />{capturing ? 'Mengambil…' : customerMode ? 'Ambil foto' : 'Ambil 5 frame'}</button><button type="button" onClick={stop} className="min-h-12 px-4 py-3 border rounded-xl inline-flex gap-2 items-center"><StopCircle size={18} />Hentikan</button></>}
      {!customerMode && <button type="button" className="min-h-12 px-4 py-3 border rounded-xl inline-flex gap-2 items-center" onClick={enableSensor}><RefreshCw size={16} />Aktifkan sensor ponsel</button>}
    </div>
    </div>
    {error && <p role="alert" className="rounded-xl border border-red-300 bg-red-50 text-red-900 p-3 break-words">{error}</p>}
    {!customerMode && <><div className="grid grid-cols-2 gap-2 text-sm" data-testid="optifit-quality-indicators">
      <div className="rounded-lg border p-3">Detail gambar: <strong>{analysis ? analysis.sharpness === 'usable' ? 'Lolos skrining' : 'Perlu diperiksa' : 'Belum tersedia'}</strong></div>
      <div className="rounded-lg border p-3">Cahaya: <strong>{analysis ? ({ usable: 'Lolos skrining', low: 'Terlalu gelap', high: 'Terlalu terang' }[analysis.exposure]) : 'Belum tersedia'}</strong></div>
      <div className="rounded-lg border p-3">Ponsel: <strong>{orientation?.gamma != null ? `γ ${orientation.gamma.toFixed(1)}°, β ${orientation.beta?.toFixed(1) ?? '—'}°` : 'Periksa manual'}</strong></div>
      <div className="rounded-lg border p-3">Jarak kamera: <strong>Tidak terukur otomatis</strong></div>
    </div>
    <p className="text-xs leading-relaxed">Kedipan, pupil tertutup, refleksi, frame terpotong, yaw/pitch kepala dan kedalaman belum dideteksi otomatis. Petugas memeriksa kondisi tersebut; sensor ponsel bukan sudut kepala. Ketajaman gambar tidak membuktikan ketepatan ukuran.</p></>}
    {running && <>
      {devices.length > 1 && <label className="block text-sm">Pilih kamera utama (hindari ultra-wide)
        <select className="block w-full border rounded-lg p-3 mt-1 bg-transparent" value={deviceId} disabled={capturing} onChange={event => { setDeviceId(event.target.value); start(event.target.value); }}>
          {devices.map((device, index) => <option key={device.deviceId} value={device.deviceId}>{device.label || `Kamera ${index + 1}`}</option>)}
        </select>
      </label>}
      {!customerMode && <p className="text-xs">Resolusi: {metadata.width || '—'} × {metadata.height || '—'}; zoom dilaporkan: {metadata.zoom == null ? 'tidak tersedia — periksa manual' : `${metadata.zoom}×`}. Browser tidak menjamin pemilihan lensa utama.</p>}
      <label className="flex items-start gap-3 border rounded-xl p-3"><input type="checkbox" checked={autoCapture} disabled={capturing || !ready} onChange={e => { setAutoCapture(e.target.checked); stableCount.current = 0; }} className="mt-1" /><span>Ambil otomatis setelah gambar stabil. <span className="block text-xs">Pastikan wajah dan frame tetap terlihat jelas; gambar stabil belum menjamin ketepatan ukuran.</span></span></label>
    </>}
    <p className="text-xs">Tiga foto dengan detail dan pencahayaan terbaik disimpan untuk ditandai satu per satu. Kamera berhenti ketika ditutup atau tab tidak aktif. {uploadEnabled ? 'Foto akan disimpan secara privat sesuai persetujuan penyimpanan foto pada sesi ini.' : 'Tidak ada gambar yang dikirim ke server.'}</p>
  </section>;
}
