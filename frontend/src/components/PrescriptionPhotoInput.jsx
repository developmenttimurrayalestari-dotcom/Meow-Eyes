import React, { useEffect, useId, useState } from "react";
import { FileImage, Upload, X } from "lucide-react";

export default function PrescriptionPhotoInput({ file, onChange, disabled = false }) {
  const inputId = useId();
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!file) { setPreview(""); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  const choose = (event) => {
    const next = event.target.files?.[0];
    event.target.value = "";
    if (!next) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(next.type) || !next.size || next.size > 8 * 1024 * 1024) {
      setError("Gunakan foto JPG, PNG, atau WebP berukuran maksimal 8 MB.");
      return;
    }
    setError("");
    onChange(next);
  };
  return <div className="pt-3 space-y-3" data-testid="product-prescription-photo">
    <p className="text-sm font-bold">Upload foto resep kacamata (opsional)</p>
    <p className="text-xs text-meow-gray">Pastikan angka resep untuk mata kanan dan kiri terlihat jelas.</p>
    <label htmlFor={inputId} className={`flex flex-col items-center gap-2 rounded-2xl border-2 border-dashed border-meow-midnight/20 bg-white/80 px-4 py-5 text-center ${disabled ? "opacity-60" : "cursor-pointer hover:border-meow-salmon focus-within:border-meow-salmon"}`}>
      <Upload className="h-6 w-6 text-meow-salmon" aria-hidden="true" />
      <span className="text-sm font-bold">{file ? "Ganti foto resep" : "Pilih foto resep"}</span>
      <span id={`${inputId}-hint`} className="text-xs text-meow-gray">JPG, PNG, atau WebP · maksimal 8 MB</span>
      <input id={inputId} type="file" accept="image/jpeg,image/png,image/webp" aria-label="Upload foto resep kacamata" aria-describedby={`${inputId}-hint`} onChange={choose} disabled={disabled} className="sr-only" />
    </label>
    {file && <div className="rounded-2xl bg-white p-3 space-y-2">
      {preview && <img src={preview} alt="Pratinjau foto resep kacamata" className="max-h-52 w-full rounded-xl object-contain" />}
      <div className="flex items-center gap-2 text-xs"><FileImage className="h-4 w-4 shrink-0" /><span className="break-all min-w-0">{file.name}</span><button type="button" disabled={disabled} aria-label="Hapus foto resep" onClick={() => { onChange(null); setError(""); }} className="ml-auto p-2 rounded-full hover:bg-meow-bg disabled:opacity-50"><X className="h-4 w-4" /></button></div>
      <p className="text-xs text-meow-gray">Foto akan diunggah secara privat saat Anda menambahkan produk ke keranjang.</p>
    </div>}
    {error && <p role="alert" className="text-xs text-red-600">{error}</p>}
    <p className="text-xs text-meow-gray">Belum punya fotonya? Anda dapat melampirkannya saat checkout.</p>
  </div>;
}
