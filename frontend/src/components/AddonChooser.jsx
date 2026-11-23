import React, { useEffect, useRef, useState } from 'react';
import { api, apiError, formatIDR, imageSrc } from '../lib/api';

export default function AddonChooser({ quantity, onConfirm, onClose, busy }) {
  const [items, setItems] = useState([]), [selected, setSelected] = useState({});
  const [q, setQ] = useState(''), [page, setPage] = useState(1), [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true), [error, setError] = useState('');
  const closeRef = useRef(), dialogRef = useRef();
  useEffect(() => { const previous = document.activeElement; closeRef.current?.focus(); return () => previous?.focus?.(); }, []);
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError('');
    const timer = setTimeout(() => api.get('/products', { params: { sale_role: 'add_on', q, page, limit: 12 }, signal: controller.signal })
      .then(({ data }) => { if (!controller.signal.aborted) { setItems(data.products || []); setTotal(data.total || 0); } })
      .catch(err => { if (!controller.signal.aborted) setError(apiError(err, 'Add On belum dapat dimuat.')); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); }), 200);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [q, page]);
  useEffect(() => {
    const handler = e => {
      if (e.key === 'Escape' && !busy) onClose();
      if (e.key === 'Tab') {
        const nodes = [...(dialogRef.current?.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled)') || [])];
        const first = nodes[0], last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener('keydown', handler); const old = document.body.style.overflow; document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', handler); document.body.style.overflow = old; };
  }, [busy, onClose]);
  const chosen = Object.values(selected);
  const totalAddons = chosen.reduce((sum, a) => sum + Number(a.price), 0);
  return <div className="fixed inset-0 z-[70] bg-black/60 p-4 grid place-items-center" onClick={() => !busy && onClose()}>
    <section ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="addon-title" className="bg-white rounded-3xl w-full max-w-2xl max-h-[90dvh] flex flex-col" onClick={e => e.stopPropagation()}>
      <div className="p-5 border-b flex items-start gap-3"><div className="flex-1"><h2 id="addon-title" className="font-heading text-xl font-black">Lengkapi paket Anda</h2><p className="text-sm text-meow-gray mt-1">Add On opsional. Setiap pilihan mengikuti jumlah produk utama ({quantity}).</p></div><button ref={closeRef} type="button" disabled={busy} onClick={onClose} aria-label="Tutup pilihan Add On" className="p-2">✕</button></div>
      <div className="p-5 overflow-y-auto space-y-3">
        <label className="block text-sm">Cari Add On<input disabled={busy} value={q} onChange={e => { setQ(e.target.value); setPage(1); }} className="block mt-1 w-full border rounded-xl p-3" /></label>
        {error ? <p role="alert">{error}</p> : loading ? <p role="status">Memuat Add On…</p> : !items.length ? <p>Belum ada Add On tersedia. Anda dapat melanjutkan dengan produk utama.</p> : items.map(p => {
          const choice = selected[p.id]; const variants = (p.variants || []).filter(v => v.is_active !== false && Number(v.stock) - Number(v.reserved || 0) >= quantity);
          const variant = variants.find(v => v.id === choice?.variant_id) || variants[0];
          const price = p.flash_sale_available >= quantity && p.flash_sale_price != null ? p.flash_sale_price : variant?.price_override ?? p.discount_price ?? p.price;
          const choose = v => setSelected(prev => ({ ...prev, [p.id]: { product_id: p.id, variant_id: v.id, name: p.name, price: p.flash_sale_available >= quantity && p.flash_sale_price != null ? p.flash_sale_price : v.price_override ?? p.discount_price ?? p.price } }));
          return <div key={p.id} className={`border rounded-2xl p-3 flex gap-3 ${choice ? 'border-meow-salmon bg-rose-50' : ''}`}>
            <input type="checkbox" aria-label={`Tambahkan ${p.name}`} checked={!!choice} disabled={busy || !variant} onChange={e => { if (e.target.checked) choose(variant); else setSelected(prev => { const next = { ...prev }; delete next[p.id]; return next; }); }} />
            <img src={imageSrc(p.main_image)} alt="" className="h-16 w-16 rounded-xl object-cover" />
            <div className="min-w-0 flex-1"><p className="font-bold text-sm">{p.name}</p><p className="text-meow-salmon text-sm">{formatIDR(price)} / produk</p>
              {!variants.length ? <small>Stok tidak mencukupi</small> : <select aria-label={`Varian ${p.name}`} className="mt-1 border rounded-lg p-1 max-w-full text-sm" disabled={busy} value={variant.id} onChange={e => choose(variants.find(v => v.id === e.target.value))}>{variants.map(v => <option key={v.id} value={v.id}>{[v.color, v.size, v.sku].filter(Boolean).join(' · ')}</option>)}</select>}
            </div>
          </div>;
        })}
        <div className="flex justify-between items-center text-sm"><button type="button" disabled={loading || page === 1} onClick={() => setPage(p => p - 1)}>Sebelumnya</button><span>Halaman {page}</span><button type="button" disabled={loading || page * 12 >= total} onClick={() => setPage(p => p + 1)}>Berikutnya</button></div>
      </div>
      <div className="p-5 border-t space-y-3"><p className="text-sm">{chosen.length} Add On · Tambahan {formatIDR(totalAddons * quantity)}</p><div className="flex flex-wrap gap-2"><button type="button" data-testid="addon-skip" disabled={busy} className="btn-secondary flex-1 text-sm" onClick={() => onConfirm([])}>Tanpa Add On</button><button type="button" disabled={busy || chosen.length > 30} className="btn-primary flex-1 text-sm" onClick={() => onConfirm(chosen.map(({ product_id, variant_id }) => ({ product_id, variant_id })))}>{busy ? 'Menyimpan…' : 'Lanjutkan'}</button></div>{chosen.length > 30 && <p role="alert">Maksimal 30 Add On per paket.</p>}</div>
    </section>
  </div>;
}
