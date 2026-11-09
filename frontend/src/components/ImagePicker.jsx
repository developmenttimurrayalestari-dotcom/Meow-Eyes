import React, { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Upload, Image as ImageIcon, X, Link as LinkIcon, Loader2 } from "lucide-react";

/**
 * Reusable image picker used everywhere in the CMS.
 *
 * Props:
 *   value       — current URL string (or "")
 *   onChange    — (url) => void
 *   label       — optional field label rendered above the picker
 *   placeholder — optional placeholder for the URL input fallback
 *   testId      — data-testid prefix (defaults to "image-picker")
 *
 * Behaviour:
 *   • Shows a small preview of the current image
 *   • Two entry modes: "Upload dari Komputer" (drag or click) & "Pilih dari Galeri"
 *   • URL paste fallback still available for external assets
 *   • Backend absolute URLs (starting with `/api/`) are prefixed with
 *     REACT_APP_BACKEND_URL when previewed so images render on the storefront too
 */
const backend = process.env.REACT_APP_BACKEND_URL || "";

// Turn a stored value (may be a relative `/api/uploads-files/...` path or a
// full external URL) into something the <img> tag can render.
export const resolveImageUrl = (url) => {
  if (!url) return "";
  if (/^https?:\/\//i.test(url)) return url;
  if (url.startsWith("/api/")) return `${backend}${url}`;
  return url;
};

const ImagePicker = ({ value, onChange, label, placeholder = "Paste URL gambar…", testId = "image-picker" }) => {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState("upload"); // upload | gallery
  const [uploading, setUploading] = useState(false);
  const [gallery, setGallery] = useState([]);
  const [galleryLoading, setGalleryLoading] = useState(false);
  const [q, setQ] = useState("");
  const [urlInput, setUrlInput] = useState(value || "");
  const fileRef = useRef(null);

  useEffect(() => { setUrlInput(value || ""); }, [value]);

  const loadGallery = async () => {
    try {
      setGalleryLoading(true);
      const { data } = await api.get(`/uploads`, { params: { limit: 60, q: q || undefined } });
      setGallery(data.items || []);
    } catch {
      setGallery([]);
    } finally {
      setGalleryLoading(false);
    }
  };

  useEffect(() => {
    if (open && tab === "gallery") loadGallery();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, tab]);

  const doUpload = async (file) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) { toast.error("File harus berupa gambar"); return; }
    if (file.size > 8 * 1024 * 1024) { toast.error("Ukuran maksimum 8MB"); return; }
    try {
      setUploading(true);
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await api.post("/uploads", fd, { headers: { "Content-Type": "multipart/form-data" } });
      onChange(data.url);
      toast.success("Gambar berhasil diupload");
      setOpen(false);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Upload gagal");
    } finally {
      setUploading(false);
    }
  };

  const pickFromGallery = (item) => {
    onChange(item.url);
    setOpen(false);
    toast.success("Gambar dipilih dari galeri");
  };

  const applyUrl = () => {
    onChange(urlInput.trim());
    setOpen(false);
  };

  const preview = resolveImageUrl(value);

  return (
    <div className="space-y-1.5" data-testid={testId}>
      {label && <label className="text-xs font-semibold text-meow-midnight/70 uppercase tracking-wide">{label}</label>}
      <div className="flex items-stretch gap-2">
        {/* Preview */}
        <div className="h-16 w-16 shrink-0 rounded-xl bg-meow-bg border border-meow-midnight/10 flex items-center justify-center overflow-hidden">
          {preview ? (
            <img src={preview} alt="preview" className="h-full w-full object-cover" data-testid={`${testId}-preview`} />
          ) : (
            <ImageIcon className="h-5 w-5 text-meow-gray/50" />
          )}
        </div>
        <div className="flex-1 flex flex-col gap-1.5 justify-center">
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="w-full text-left px-3 py-2 rounded-xl bg-meow-bg text-sm font-semibold text-meow-midnight hover:bg-meow-amber/20 transition flex items-center gap-2"
            data-testid={`${testId}-open`}
          >
            <Upload className="h-4 w-4" />
            {value ? "Ganti gambar…" : "Pilih gambar dari komputer atau galeri…"}
          </button>
          {value && (
            <div className="flex items-center gap-2 text-[11px] text-meow-gray truncate">
              <span className="truncate">{value}</span>
              <button
                type="button"
                onClick={() => onChange("")}
                className="text-meow-salmon font-bold shrink-0"
                aria-label="Hapus gambar"
                data-testid={`${testId}-clear`}
              >
                Hapus
              </button>
            </div>
          )}
        </div>
      </div>

      {open && (
        <div className="fixed inset-0 z-[60] bg-black/50 flex items-end sm:items-center justify-center p-3 sm:p-6" onClick={() => setOpen(false)}>
          <div className="bg-white rounded-3xl w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl" onClick={(e) => e.stopPropagation()} data-testid={`${testId}-modal`}>
            <div className="p-4 border-b border-meow-midnight/10 flex items-center justify-between">
              <p className="font-heading font-black text-lg">Pilih Gambar</p>
              <button type="button" onClick={() => setOpen(false)} className="p-2 rounded-full hover:bg-meow-bg" aria-label="Tutup">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="px-4 pt-3 flex gap-2 border-b border-meow-midnight/10">
              {[
                { k: "upload", label: "Upload dari Komputer", icon: Upload },
                { k: "gallery", label: "Pilih dari Galeri", icon: ImageIcon },
                { k: "url", label: "Paste URL", icon: LinkIcon },
              ].map((t) => (
                <button
                  key={t.k}
                  type="button"
                  onClick={() => setTab(t.k)}
                  className={`inline-flex items-center gap-2 px-3 py-2 text-sm font-bold rounded-t-xl transition ${
                    tab === t.k ? "bg-meow-amber/25 text-meow-midnight" : "text-meow-gray hover:text-meow-midnight"
                  }`}
                  data-testid={`${testId}-tab-${t.k}`}
                >
                  <t.icon className="h-4 w-4" /> {t.label}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              {tab === "upload" && (
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => { e.preventDefault(); doUpload(e.dataTransfer.files?.[0]); }}
                  className="border-2 border-dashed border-meow-midnight/20 rounded-2xl p-10 text-center bg-meow-bg/40"
                  data-testid={`${testId}-dropzone`}
                >
                  {uploading ? (
                    <div className="flex flex-col items-center gap-3 text-meow-midnight">
                      <Loader2 className="h-8 w-8 animate-spin" />
                      <p className="text-sm font-semibold">Mengupload…</p>
                    </div>
                  ) : (
                    <>
                      <Upload className="h-10 w-10 mx-auto text-meow-salmon" />
                      <p className="font-heading font-bold text-lg mt-3">Drag & drop gambar disini</p>
                      <p className="text-sm text-meow-gray mt-1">atau</p>
                      <button
                        type="button"
                        onClick={() => fileRef.current?.click()}
                        className="mt-3 px-5 py-2 rounded-full bg-meow-salmon text-white font-bold text-sm hover:opacity-90"
                        data-testid={`${testId}-choose-file`}
                      >
                        Pilih dari komputer
                      </button>
                      <p className="text-[11px] text-meow-gray mt-4">
                        Format: JPG, PNG, WEBP, GIF, SVG · Maks 8MB
                      </p>
                      <input
                        ref={fileRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => doUpload(e.target.files?.[0])}
                      />
                    </>
                  )}
                </div>
              )}

              {tab === "gallery" && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <input
                      value={q}
                      onChange={(e) => setQ(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") loadGallery(); }}
                      placeholder="Cari nama file…"
                      className="flex-1 px-3 py-2 rounded-xl bg-meow-bg outline-none text-sm"
                      data-testid={`${testId}-gallery-search`}
                    />
                    <button
                      type="button"
                      onClick={loadGallery}
                      className="px-3 py-2 rounded-xl bg-meow-midnight text-white text-sm font-bold"
                    >
                      Cari
                    </button>
                  </div>
                  {galleryLoading ? (
                    <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-meow-salmon" /></div>
                  ) : gallery.length === 0 ? (
                    <p className="text-center text-sm text-meow-gray py-10">Belum ada file di galeri. Upload dulu di tab pertama.</p>
                  ) : (
                    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
                      {gallery.map((it) => (
                        <button
                          key={it.id}
                          type="button"
                          onClick={() => pickFromGallery(it)}
                          className="group relative aspect-square rounded-xl overflow-hidden bg-meow-bg border border-meow-midnight/10 hover:border-meow-salmon focus:border-meow-salmon focus:outline-none"
                          title={it.filename}
                          data-testid={`${testId}-gallery-item-${it.id}`}
                        >
                          <img src={resolveImageUrl(it.url)} alt={it.filename} className="w-full h-full object-cover" loading="lazy" />
                          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-meow-midnight/90 to-transparent p-1.5 text-[10px] text-white truncate opacity-0 group-hover:opacity-100">
                            {it.filename}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {tab === "url" && (
                <div className="space-y-3">
                  <label className="text-xs font-semibold text-meow-midnight/70 uppercase tracking-wide">Alamat gambar (URL)</label>
                  <input
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder={placeholder}
                    className="w-full px-3 py-3 rounded-xl bg-meow-bg outline-none text-sm"
                    data-testid={`${testId}-url-input`}
                  />
                  <p className="text-[11px] text-meow-gray">Gunakan URL publik (https://…) untuk gambar dari CDN eksternal.</p>
                  <div className="flex justify-end gap-2 pt-2">
                    <button type="button" onClick={() => setOpen(false)} className="px-4 py-2 text-sm font-bold rounded-full text-meow-midnight hover:bg-meow-bg">Batal</button>
                    <button type="button" onClick={applyUrl} className="px-4 py-2 text-sm font-bold rounded-full bg-meow-midnight text-white" data-testid={`${testId}-url-apply`}>Gunakan URL</button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImagePicker;
