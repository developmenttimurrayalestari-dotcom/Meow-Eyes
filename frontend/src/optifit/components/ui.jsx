import React, { useEffect, useId, useRef } from "react";
import { AlertTriangle, CheckCircle2, Info, LoaderCircle, X } from "lucide-react";

export const DISCLAIMER = "Pengukuran kamera merupakan alat bantu fitting dan harus diverifikasi tenaga optik yang kompeten. Hasil berkualitas rendah bukan hasil final. Aplikasi tidak menggantikan pemeriksaan refraksi atau kesehatan mata; kamera tidak menentukan SPH, CYL, Axis, atau ADD.";

export function Field({ label, hint, children, className = "", required = false }) {
  const id = useId();
  return <div className={`of-field ${className}`}>
    <label htmlFor={id}>{label}{required && <span aria-hidden="true"> *</span>}</label>
    {React.isValidElement(children) ? React.cloneElement(children, { id, "aria-describedby": hint ? `${id}-help` : undefined, "aria-label": children.props["aria-label"] || label }) : children}
    {hint && <small id={`${id}-help`}>{hint}</small>}
  </div>;
}

export function Button({ children, variant = "primary", busy = false, className = "", ...props }) {
  return <button type="button" {...props} disabled={props.disabled || busy} className={`of-button of-button-${variant} ${className}`}>
    {busy && <LoaderCircle size={17} className="of-spin" aria-hidden="true" />}{children}
  </button>;
}

export function Notice({ children, tone = "info", className = "" }) {
  const Icon = tone === "success" ? CheckCircle2 : tone === "danger" || tone === "warning" ? AlertTriangle : Info;
  return <div className={`of-notice of-notice-${tone} ${className}`} role={tone === "danger" ? "alert" : undefined}>
    <Icon size={19} aria-hidden="true" /><div>{children}</div>
  </div>;
}

export function EmptyState({ icon: Icon = Info, title, children, action }) {
  return <div className="of-empty"><span className="of-empty-icon"><Icon size={30} /></span><h3>{title}</h3><p>{children}</p>{action}</div>;
}

export function Modal({ title, onClose, children, wide = false }) {
  const panel = useRef(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  const titleId = useId();
  useEffect(() => {
    const previous = document.activeElement;
    const focusable = () => [...(panel.current?.querySelectorAll('button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href],[tabindex="0"]') || [])].filter(e => e.getClientRects().length);
    const first = focusable()[0] || panel.current;
    first?.focus();
    const onKey = event => {
      if (event.key === "Escape") { event.preventDefault(); onCloseRef.current?.(); }
      if (event.key !== "Tab") return;
      const controls = focusable();
      if (!controls.length) { event.preventDefault(); return; }
      if (event.shiftKey && (document.activeElement === controls[0] || document.activeElement === panel.current)) { event.preventDefault(); controls.at(-1).focus(); }
      else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0].focus(); }
    };
    const node = panel.current;
    node?.addEventListener("keydown", onKey);
    return () => { node?.removeEventListener("keydown", onKey); if (previous?.isConnected) previous.focus(); };
  }, []);
  return <div className="of-modal-backdrop">
    <section ref={panel} tabIndex={-1} className={`of-modal ${wide ? "of-modal-wide" : ""}`} role="dialog" aria-modal="true" aria-labelledby={titleId}>
      <header className="of-modal-heading"><h2 id={titleId}>{title}</h2><button type="button" aria-label="Tutup dialog" onClick={onClose} className="of-icon-button"><X size={22} /></button></header>
      <div className="of-modal-content">{children}</div>
    </section>
  </div>;
}

export function Help({ title, children }) {
  return <details className="of-help"><summary><Info size={15} />{title}</summary><p>{children}</p></details>;
}

export function StatusBadge({ status, labels = {} }) {
  return <span className={`of-status of-status-${status || "draft"}`}>{labels[status] || status || "Draft"}</span>;
}

export const todayLocal = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
};
export const readableDate = value => {
  if (!value) return "—";
  const date = new Date(value.length === 10 ? `${value}T12:00:00` : value);
  return Number.isNaN(date.valueOf()) ? "—" : new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", ...(value.length > 10 ? { timeStyle: "short" } : {}) }).format(date);
};
export const asNumber = value => value === "" || value == null ? null : Number(value);
export const formatNumber = (value, digits = 2) => typeof value === "number" && Number.isFinite(value) ? new Intl.NumberFormat("id-ID", { maximumFractionDigits: digits }).format(value) : "Belum diukur";
export const safeError = error => typeof error?.message === "string" && error.message.length < 500 ? error.message : "Tindakan belum berhasil. Periksa isian lalu coba kembali.";
export const makeId = () => crypto.randomUUID();

export async function normalizedImage(file) {
  if (!["image/jpeg", "image/png", "image/webp"].includes(file?.type) || file.size > 8 * 1024 * 1024) throw new Error("Gunakan foto JPG, PNG, atau WebP maksimal 8 MiB.");
  const url = URL.createObjectURL(file);
  try {
    const image = await new Promise((resolve, reject) => { const img = new Image(); img.onload = () => resolve(img); img.onerror = () => reject(new Error("Foto tidak dapat dibaca.")); img.src = url; });
    if (!image.naturalWidth || !image.naturalHeight || image.naturalWidth * image.naturalHeight > 20000000) throw new Error("Dimensi foto harus valid dan tidak melebihi 20 megapiksel.");
    const canvas = document.createElement("canvas"); canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Browser tidak dapat memproses foto.");
    context.drawImage(image, 0, 0);
    const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.92));
    if (!blob || blob.size > 8 * 1024 * 1024) throw new Error("Hasil normalisasi foto melebihi kapasitas 8 MiB. Gunakan foto dengan resolusi lebih rendah.");
    return { blob, width: canvas.width, height: canvas.height, dataUrl: canvas.toDataURL("image/jpeg", 0.92), imageData: context.getImageData(0, 0, canvas.width, canvas.height) };
  } finally { URL.revokeObjectURL(url); }
}

export function dataUrlBlob(dataUrl) {
  const match = /^data:(image\/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)$/.exec(dataUrl || "");
  if (!match) throw new Error("Data foto tidak valid.");
  const binary = atob(match[2]); const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return new Blob([bytes], { type: match[1] });
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob); const link = document.createElement("a");
  link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
