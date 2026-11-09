import React, { useState } from "react";
import { Copy, Check, Share2 } from "lucide-react";
import { toast } from "sonner";
import { copyText } from "../lib/api";

export default function ShareButtons({ title, path, className = "" }) {
  const [copied, setCopied] = useState(false);
  const url = new URL(path || window.location.pathname, window.location.origin).href;
  const encodedUrl = encodeURIComponent(url);
  const links = [
    ["WhatsApp", `https://wa.me/?text=${encodeURIComponent(`${title}\n${url}`)}`],
    ["Facebook", `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`],
    ["X", `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodedUrl}`],
    ["LinkedIn", `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`],
  ];
  const copy = async () => {
    try {
      await copyText(url);
      setCopied(true);
      toast.success("Tautan berhasil disalin");
    } catch {
      toast.error("Tautan belum tersalin. Salin alamat halaman dari browser Anda.");
    }
  };
  return (
    <section aria-label="Bagikan halaman" className={`flex flex-wrap items-center gap-2 text-xs ${className}`} data-testid="social-share">
      <span className="font-bold mr-1">Bagikan:</span>
      {links.map(([name, href]) => (
        <a key={name} href={href} target="_blank" rel="noopener noreferrer" aria-label={`Bagikan ke ${name}`}
          className="rounded-full px-3 py-2 border border-meow-midnight/15 bg-white hover:border-meow-salmon focus-visible:outline-meow-salmon">{name}</a>
      ))}
      <button type="button" onClick={copy} className="inline-flex items-center gap-1.5 rounded-full px-3 py-2 bg-meow-midnight text-white" data-testid="copy-link">
        {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
        {copied ? "Tautan disalin" : "Copy Link"}
      </button>
      {navigator.share && <button type="button" className="p-2 rounded-full border border-meow-midnight/15" aria-label="Opsi berbagi lainnya"
        onClick={() => navigator.share({ title, url }).catch((error) => { if (error.name !== "AbortError") toast.error("Menu berbagi belum tersedia."); })}>
        <Share2 className="h-4 w-4" />
      </button>}
    </section>
  );
}
