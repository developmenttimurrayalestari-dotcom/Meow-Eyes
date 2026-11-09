import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Camera, CameraOff, Glasses, ImagePlus, RotateCcw, SlidersHorizontal } from "lucide-react";
import { api, imageSrc } from "../lib/api";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "./ui/dialog";
import TryOnModel from "./TryOnModel";

const clamp = (value, min, max) => Math.min(max, Math.max(min, Number(value) || 0));
export const assetFit = (asset) => ({
  width: clamp(45 * Number(asset.scale || 1), 5, 95),
  x: clamp(50 + Number(asset.offset_x || 0) * 100, 0, 100),
  y: clamp(45 + Number(asset.offset_y || 0) * 100, 0, 100),
  pitch: clamp(asset.rotation_x, -180, 180), yaw: clamp(asset.rotation_y, -180, 180), roll: clamp(asset.rotation_z, -180, 180), depth: clamp(asset.offset_z, -5, 5),
});

export function TryOnStudio({ assets, name }) {
  const [assetId, setAssetId] = useState(assets[0]?.id);
  const asset = assets.find((item) => item.id === assetId) || assets[0];
  const [fit, setFit] = useState(() => assetFit(asset));
  const [photo, setPhoto] = useState("");
  const [cameraOn, setCameraOn] = useState(false);
  const [cameraBusy, setCameraBusy] = useState(false);
  const [error, setError] = useState("");
  const [modelError, setModelError] = useState("");
  const [modelLoading, setModelLoading] = useState(asset.asset_type !== "image");
  const [forceImage, setForceImage] = useState(false);
  const streamRef = useRef(null);
  const videoRef = useRef(null);
  const photoRef = useRef("");
  const requestRef = useRef(0);
  const alive = useRef(true);
  const stageRef = useRef(null);
  const stopCamera = useCallback(() => {
    requestRef.current += 1;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false); setCameraBusy(false);
  }, []);
  useEffect(() => {
    alive.current = true;
    const visibility = () => { if (document.hidden) stopCamera(); };
    document.addEventListener("visibilitychange", visibility);
    return () => {
      alive.current = false; requestRef.current += 1;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      if (photoRef.current) URL.revokeObjectURL(photoRef.current);
      document.removeEventListener("visibilitychange", visibility);
    };
  }, [stopCamera]);
  useEffect(() => { setFit(assetFit(asset)); setModelError(""); setForceImage(false); setModelLoading(asset.asset_type !== "image"); }, [asset]);
  const startCamera = async () => {
    if (!navigator.mediaDevices?.getUserMedia || !window.isSecureContext) { setError("Kamera memerlukan HTTPS dan izin browser. Anda juga dapat menggunakan foto dari perangkat."); return; }
    stopCamera();
    const requestId = ++requestRef.current;
    setCameraBusy(true); setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 960 } }, audio: false });
      if (!alive.current || requestId !== requestRef.current) { stream.getTracks().forEach((track) => track.stop()); return; }
      streamRef.current = stream;
      if (photoRef.current) { URL.revokeObjectURL(photoRef.current); photoRef.current = ""; }
      setPhoto("");
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      if (alive.current && requestId === requestRef.current) setCameraOn(true);
    } catch (err) {
      if (alive.current && requestId === requestRef.current) { stopCamera(); setError(err.name === "NotAllowedError" ? "Izin kamera belum diberikan. Izinkan kamera melalui browser, atau pilih foto." : "Kamera belum dapat diakses. Coba lagi atau pilih foto dari perangkat."); }
    } finally { if (alive.current && requestId === requestRef.current) setCameraBusy(false); }
  };
  const choosePhoto = async (event) => {
    const file = event.target.files?.[0]; event.target.value = "";
    if (!file) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size > 10 * 1024 * 1024) { setError("Pilih foto JPG, PNG, atau WebP berukuran maksimal 10 MB."); return; }
    stopCamera(); setError("");
    const url = URL.createObjectURL(file);
    const photoRequest = ++requestRef.current;
    try {
      const img = new Image();
      await new Promise((resolve, reject) => { img.onload = resolve; img.onerror = reject; img.src = url; });
      if (img.naturalWidth * img.naturalHeight > 20000000) throw new Error("large");
      if (!alive.current || photoRequest !== requestRef.current) { URL.revokeObjectURL(url); return; }
      if (photoRef.current) URL.revokeObjectURL(photoRef.current);
      photoRef.current = url; setPhoto(url);
    } catch { URL.revokeObjectURL(url); if (alive.current) setError("Foto tidak dapat dibaca atau melebihi 20 megapiksel. Pilih foto yang lebih kecil."); }
  };
  const model = asset.asset_type !== "image" && !forceImage;
  const overlayUrl = model ? "" : imageSrc(asset.asset_type === "image" ? asset.source_url : asset.preview_url);
  const move = (event) => {
    if (!event.isPrimary || !stageRef.current) return;
    const rect = stageRef.current.getBoundingClientRect();
    setFit((current) => ({ ...current, x: clamp((event.clientX - rect.left) / rect.width * 100, 0, 100), y: clamp((event.clientY - rect.top) / rect.height * 100, 0, 100) }));
  };
  return <div className="grid lg:grid-cols-[minmax(0,1fr)_260px] gap-5">
    <div>
      <div ref={stageRef} className="relative aspect-[4/3] rounded-2xl bg-slate-100 overflow-hidden touch-none cursor-move" data-testid="try-on-stage"
        onPointerDown={(event) => { if (!event.isPrimary) return; event.currentTarget.setPointerCapture(event.pointerId); move(event); }}
        onPointerMove={(event) => { if (event.currentTarget.hasPointerCapture(event.pointerId)) move(event); }}
        onPointerUp={(event) => { if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId); }}>
        <video ref={videoRef} autoPlay playsInline muted className={`absolute inset-0 w-full h-full object-contain -scale-x-100 ${cameraOn ? "" : "invisible"}`} aria-label="Pratinjau kamera lokal" />
        {photo && <img src={photo} alt="Foto lokal untuk mencoba frame" className="absolute inset-0 h-full w-full object-contain" draggable="false" />}
        {!cameraOn && !photo && <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 pointer-events-none"><svg viewBox="0 0 200 250" className="h-4/5 w-3/5" aria-hidden="true"><ellipse cx="100" cy="112" rx="66" ry="92" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="5 5" /><path d="M33 112H167 M100 40V185" stroke="currentColor" strokeWidth="1" strokeDasharray="3 6" /></svg><span className="absolute bottom-4 text-xs">Pilih kamera atau foto untuk mencoba frame</span></div>}
        {model ? <TryOnModel key={asset.id} asset={asset} fit={fit} onReady={() => setModelLoading(false)} onError={(message) => { setModelLoading(false); setModelError(message); }} />
          : overlayUrl && <img src={overlayUrl} alt={`Pratinjau frame ${name}`} draggable="false" onError={() => setModelError("Gambar frame belum dapat dimuat. Pilih aset lain atau coba lagi nanti.")}
            className="absolute pointer-events-none select-none" style={{ width: `${fit.width}%`, left: `${fit.x}%`, top: `${fit.y}%`, transform: `translate(-50%, -50%) perspective(800px) rotateX(${fit.pitch}deg) rotateY(${fit.yaw}deg) rotate(${fit.roll}deg)` }} />}
        {modelLoading && model && <span role="status" className="absolute top-3 left-3 text-xs rounded-full bg-white/90 px-3 py-2">Memuat model 3D…</span>}
      </div>
      <div className="flex flex-wrap gap-2 mt-3">
        {cameraOn ? <button type="button" onClick={stopCamera} className="btn-secondary text-xs py-2 px-4 inline-flex items-center gap-2"><CameraOff className="h-4 w-4" />Hentikan Kamera</button>
          : <button type="button" onClick={startCamera} disabled={cameraBusy} className="btn-primary text-xs py-2 px-4 inline-flex items-center gap-2 disabled:opacity-50" data-testid="try-on-camera"><Camera className="h-4 w-4" />{cameraBusy ? "Meminta izin…" : "Mulai Kamera"}</button>}
        <label className="btn-secondary text-xs py-2 px-4 inline-flex items-center gap-2 cursor-pointer"><ImagePlus className="h-4 w-4" />Gunakan Foto<input type="file" accept="image/jpeg,image/png,image/webp" onChange={choosePhoto} className="sr-only" data-testid="try-on-photo" /></label>
      </div>
      <p className="text-xs text-meow-gray mt-3">Video dan foto Anda diproses di browser ini dan tidak diunggah. Kamera berhenti saat jendela try-on ditutup atau tab tidak aktif.</p>
      {error && <p role="alert" className="text-sm text-red-600 mt-3">{error}</p>}
      {modelError && <div role="alert" className="rounded-xl p-3 mt-3 bg-amber-50 text-sm"><p>{modelError}</p>{model && asset.preview_url && <button type="button" onClick={() => { setForceImage(true); setModelError(""); }} className="underline font-bold mt-2">Gunakan Gambar Pratinjau</button>}</div>}
    </div>
    <div className="space-y-4">
      <h3 className="font-bold flex items-center gap-2 text-sm"><SlidersHorizontal className="h-4 w-4" />Sesuaikan Frame</h3>
      {assets.length > 1 && <label className="block text-xs font-semibold">Tampilan frame<select value={asset.id} onChange={(event) => setAssetId(event.target.value)} className="block w-full mt-1 rounded-xl p-2 bg-meow-bg">{assets.map((item, index) => <option key={item.id} value={item.id}>Tampilan {index + 1} · {item.asset_type === "image" ? "Gambar" : "3D"}</option>)}</select></label>}
      <p className="text-xs text-meow-gray">Hadapkan wajah ke depan. Geser frame pada pratinjau, lalu atur ukuran dan kemiringan agar sejajar dengan mata Anda.</p>
      {[["width", "Lebar", 5, 95, "%"], ["x", "Posisi horizontal", 0, 100, "%"], ["y", "Posisi vertikal", 0, 100, "%"], ["roll", "Kemiringan", -180, 180, "°"], ["yaw", "Putar kanan / kiri", -90, 90, "°"], ["pitch", "Putar atas / bawah", -90, 90, "°"]].map(([key, label, min, max, unit]) => <label key={key} className="block text-xs font-semibold"><span className="flex justify-between gap-2">{label}<span className="tabular-nums text-meow-gray">{Math.round(fit[key])}{unit}</span></span><input type="range" min={min} max={max} step="1" value={fit[key]} onChange={(event) => setFit((current) => ({ ...current, [key]: Number(event.target.value) }))} className="w-full mt-2 accent-meow-salmon" /></label>)}
      <button type="button" onClick={() => setFit(assetFit(asset))} className="text-xs font-bold inline-flex items-center gap-1.5 underline"><RotateCcw className="h-3.5 w-3.5" />Atur ulang</button>
      <p className="text-xs text-meow-gray border-t pt-3">Pratinjau ini menggunakan penyesuaian manual untuk melihat gaya frame. Ukuran visual bukan pengukuran ukuran frame atau PD.</p>
    </div>
  </div>;
}

export default function VirtualTryOn({ productId, variantId, productName }) {
  const [allAssets, setAllAssets] = useState([]);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const controller = new AbortController(); setAllAssets([]); setOpen(false);
    api.get(`/products/${productId}/try-on`, { signal: controller.signal }).then(({ data }) => setAllAssets(data.assets || [])).catch(() => {});
    return () => controller.abort();
  }, [productId]);
  const assets = useMemo(() => allAssets.filter((asset) => !asset.variant_id || asset.variant_id === variantId).sort((a, b) => Number(Boolean(b.variant_id)) - Number(Boolean(a.variant_id)) || Number(a.sort_order || 0) - Number(b.sort_order || 0)), [allAssets, variantId]);
  if (!assets.length) return null;
  return <Dialog open={open} onOpenChange={setOpen}>
    <DialogTrigger asChild><button type="button" className="w-full mt-4 btn-secondary inline-flex items-center justify-center gap-2" data-testid="open-virtual-try-on"><Glasses className="h-5 w-5" />Virtual Try-On · Coba Frame</button></DialogTrigger>
    <DialogContent className="max-w-5xl w-[calc(100%-1rem)] max-h-[92dvh] overflow-y-auto rounded-3xl p-4 sm:p-6">
      <div className="pr-6"><DialogTitle className="font-heading font-black text-2xl">Virtual Try-On</DialogTitle><DialogDescription className="mt-1">{productName} · Coba dengan kamera atau foto Anda</DialogDescription></div>
      {open && <TryOnStudio key={`${productId}-${variantId || "all"}`} assets={assets} name={productName} />}
    </DialogContent>
  </Dialog>;
}
