import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export const PAGE_SIZE = 15;
export const catalogPage = (value) => /^\d+$/.test(String(value || "")) ? Math.max(1, Math.min(1000000, Number(value))) : 1;

export default function CatalogPagination({ page, total, onChange, disabled = false }) {
  const count = Math.max(1, Math.ceil(total / PAGE_SIZE));
  if (total <= PAGE_SIZE) return null;
  const pages = [...new Set([1, page - 1, page, page + 1, count])].filter((p) => p >= 1 && p <= count).sort((a, b) => a - b);
  return (
    <nav className="mt-8 flex flex-wrap items-center justify-center gap-2" aria-label="Halaman produk" data-testid="catalog-pagination">
      <button type="button" aria-label="Halaman sebelumnya" disabled={disabled || page <= 1} onClick={() => onChange(page - 1)}
        className="p-2.5 rounded-xl bg-white disabled:opacity-40 border border-meow-midnight/10"><ChevronLeft className="h-5 w-5" /></button>
      {pages.map((p, i) => (
        <React.Fragment key={p}>
          {i > 0 && p - pages[i - 1] > 1 && <span className="px-1" aria-hidden="true">…</span>}
          <button type="button" onClick={() => onChange(p)} disabled={disabled} aria-label={`Halaman ${p}`} aria-current={p === page ? "page" : undefined}
            className={`min-w-11 h-11 px-3 rounded-xl font-bold border ${p === page ? "bg-meow-midnight text-white border-meow-midnight" : "bg-white border-meow-midnight/10"}`}>{p}</button>
        </React.Fragment>
      ))}
      <button type="button" aria-label="Halaman berikutnya" disabled={disabled || page >= count} onClick={() => onChange(page + 1)}
        className="p-2.5 rounded-xl bg-white disabled:opacity-40 border border-meow-midnight/10"><ChevronRight className="h-5 w-5" /></button>
      <p className="w-full text-center text-xs text-meow-gray mt-2">Halaman {page} dari {count} · Maksimal {PAGE_SIZE} produk per halaman</p>
    </nav>
  );
}
