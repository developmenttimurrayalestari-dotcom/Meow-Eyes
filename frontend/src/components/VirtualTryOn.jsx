import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Camera, CameraOff, Glasses, ImagePlus } from "lucide-react";
import { api, imageSrc } from "../lib/api";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "./ui/dialog";
import TryOnModel from "./TryOnModel";
import useTryOnTracking from "../hooks/useTryOnTracking";

export function TryOnStudio({ assets, name, immersive = false, stageOverlay = null, stageFooter = null }) {
  const [assetId, setAssetId] = useState(assets[0]?.id);
  const asset = assets.find((item) => item.id === assetId) || assets[0];
  const [trackingRetry, setTrackingRetry] = useState(0);
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
  const photoElementRef = useRef(null);
  const tracking = useTryOnTracking({ videoRef, photoRef: photoElementRef, stageRef, cameraOn, photo, asset, retry: trackingRetry });
  const fit = tracking.fit || { width: 0, x: 50, y: 50, pitch: 0, yaw: 0, roll: 0, depth: 0 };
  const frameVisible = Boolean((cameraOn || photo) && tracking.fit);
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
  useEffect(() => { setModelError(""); setForceImage(false); setModelLoading(asset.asset_type !== "image"); }, [asset]);
  const startCamera = async () => {
    if (process.env.NODE_ENV === "production" && !window.isSecureContext) { setError("Kamera memerlukan HTTPS dan izin browser. Anda juga dapat menggunakan foto dari perangkat."); return; }
    if (!navigator.mediaDevices?.getUserMedia) { setError("Browser tidak menyediakan akses kamera pada alamat ini. Untuk pengembangan, buka localhost atau izinkan alamat LAN sebagai secure origin di pengaturan browser. Anda juga dapat menggunakan foto dari perangkat."); return; }
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
  const cameraControls = <div className={`flex flex-wrap gap-2 ${immersive ? 'vto-camera-controls' : 'mt-3'}`}>
    {cameraOn ? <button type="button" onClick={stopCamera} className="btn-secondary text-xs py-2 px-4 inline-flex items-center gap-2"><CameraOff className="h-4 w-4" />Hentikan Kamera</button>
      : <button type="button" onClick={startCamera} disabled={cameraBusy} className="btn-primary text-xs py-2 px-4 inline-flex items-center gap-2 disabled:opacity-50" data-testid="try-on-camera"><Camera className="h-4 w-4" />{cameraBusy ? "Meminta izin…" : "Mulai Kamera"}</button>}
    <label className="btn-secondary text-xs py-2 px-4 inline-flex items-center gap-2 cursor-pointer"><ImagePlus className="h-4 w-4" />Gunakan Foto<input type="file" accept="image/jpeg,image/png,image/webp" onChange={choosePhoto} className="sr-only" data-testid="try-on-photo" /></label>
  </div>;
  return <div className={immersive ? 'vto-studio' : 'space-y-4'}>
    <div className={immersive ? 'vto-preview' : undefined}>
      {immersive && cameraControls}
      <div ref={stageRef} className={immersive ? 'vto-immersive-stage relative rounded-2xl bg-slate-100 overflow-hidden' : 'relative aspect-[4/3] rounded-2xl bg-slate-100 overflow-hidden'} data-testid="try-on-stage">
        <video ref={videoRef} autoPlay playsInline muted className={`absolute inset-0 w-full h-full object-contain -scale-x-100 ${cameraOn ? "" : "invisible"}`} aria-label="Pratinjau kamera lokal" />
        {photo && <img ref={photoElementRef} src={photo} alt="Foto lokal untuk mencoba frame" className="absolute inset-0 h-full w-full object-contain" draggable="false" />}
        {!cameraOn && !photo && <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 pointer-events-none"><svg viewBox="0 0 200 250" className="h-4/5 w-3/5" aria-hidden="true"><ellipse cx="100" cy="112" rx="66" ry="92" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="5 5" /><path d="M33 112H167 M100 40V185" stroke="currentColor" strokeWidth="1" strokeDasharray="3 6" /></svg><span className="absolute bottom-4 text-xs">Pilih kamera atau foto untuk mencoba frame</span></div>}
        <div className={`absolute inset-0 pointer-events-none ${frameVisible ? "" : "invisible"}`} data-testid="try-on-tracked-frame" aria-hidden={!frameVisible}>
        {model ? (cameraOn || photo) && <TryOnModel key={asset.id} asset={asset} fit={fit} onReady={() => setModelLoading(false)} onError={(message) => { setModelLoading(false); setModelError(message); }} />
          : overlayUrl && <img src={overlayUrl} alt={`Pratinjau frame ${name}`} draggable="false" onError={() => setModelError("Gambar frame belum dapat dimuat. Pilih aset lain atau coba lagi nanti.")}
            className="absolute pointer-events-none select-none" style={{ width: `${fit.width}%`, left: `${fit.x}%`, top: `${fit.y}%`, transform: `translate(-50%, -50%) perspective(800px) rotateX(${fit.pitch}deg) rotateY(${fit.yaw}deg) rotate(${fit.roll}deg)` }} />}
        </div>
        {modelLoading && model && (cameraOn || photo) && <span role="status" className="absolute top-3 left-3 text-xs rounded-full bg-white/90 px-3 py-2">Memuat model 3D…</span>}
        {stageOverlay && <div className={`absolute inset-x-3 bottom-3 z-10 ${immersive ? 'vto-product-overlay' : ''}`}>{stageOverlay}</div>}
      </div>
      {stageFooter}
      {!immersive && cameraControls}
      <p className={`text-xs text-meow-gray mt-3 ${immersive ? 'vto-privacy-note' : ''}`}>Video dan foto Anda diproses di browser ini dan tidak diunggah. Kamera berhenti saat jendela try-on ditutup atau tab tidak aktif.</p>
      {(error || modelError) && <div className={immersive ? 'vto-studio-feedback' : undefined}>
        {error && <p role="alert" className="text-sm text-red-600 mt-3">{error}</p>}
        {modelError && <div role="alert" className="rounded-xl p-3 mt-3 bg-amber-50 text-sm"><p>{modelError}</p>{model && asset.preview_url && <button type="button" onClick={() => { setForceImage(true); setModelError(""); }} className="underline font-bold mt-2">Gunakan Gambar Pratinjau</button>}</div>}
      </div>}
    </div>
    <div className={`space-y-3 rounded-2xl bg-meow-bg p-4 ${immersive ? 'vto-tracking-panel text-sm' : ''}`}>
      <h3 className="vto-tracking-title font-bold text-sm">Frame menyesuaikan wajah secara otomatis</h3>
      {assets.length > 1 && <label className="block text-xs font-semibold">Tampilan frame<select value={asset.id} onChange={(event) => setAssetId(event.target.value)} className="block w-full mt-1 rounded-xl p-2 bg-meow-bg">{assets.map((item, index) => <option key={item.id} value={item.id}>Tampilan {index + 1} · {item.asset_type === "image" ? "Gambar" : "3D"}</option>)}</select></label>}
      <p className="vto-tracking-instructions text-xs text-meow-gray">Hadapkan wajah ke kamera dengan kedua mata terlihat dan pencahayaan cukup. Posisi, ukuran, dan kemiringan frame akan mengikuti wajah Anda.</p>
      <p role="status" className="text-sm font-semibold" data-testid="try-on-tracking-status">{tracking.state === "loading" ? "Menyiapkan deteksi wajah…" : tracking.state === "tracking" ? immersive ? "Wajah terdeteksi" : "Wajah terdeteksi · frame mengikuti mata Anda" : tracking.state === "searching" ? immersive ? "Hadapkan wajah ke kamera" : "Wajah belum terdeteksi. Hadapkan wajah ke kamera atau pilih foto wajah yang jelas." : tracking.state === "error" ? "Deteksi wajah belum dapat dijalankan. Coba muat ulang deteksi." : immersive ? "Mulai kamera atau pilih foto" : "Mulai kamera atau pilih foto untuk mendeteksi wajah."}</p>
      {tracking.state === "error" && <button type="button" onClick={() => setTrackingRetry(value => value + 1)} className="text-xs font-bold underline">Muat ulang deteksi</button>}
      <p className="vto-disclaimer text-xs text-meow-gray border-t pt-3">Pratinjau gaya frame mengikuti wajah; bukan pengukuran ukuran frame atau PD.</p>
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
