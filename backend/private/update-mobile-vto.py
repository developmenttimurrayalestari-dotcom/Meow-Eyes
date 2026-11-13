from pathlib import Path

page = r'''import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Info, Search, ShoppingCart, X } from 'lucide-react';
import { api, apiError, formatIDR, imageSrc } from '../lib/api';
import { TryOnStudio } from '../components/VirtualTryOn';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';
import '../styles/engagement.css';

export const VTO_MOBILE_QUERY = '(max-width: 767px), (max-height: 500px) and (pointer: coarse)';

export default function VirtualTryOnPage() {
  const { user, refreshCartCount } = useAuth(), navigate = useNavigate();
  const [products, setProducts] = useState([]), [selected, setSelected] = useState(null);
  const [variantId, setVariantId] = useState(''), [q, setQ] = useState('');
  const [offset, setOffset] = useState(0), [next, setNext] = useState(null);
  const [error, setError] = useState(''), [busy, setBusy] = useState(false), [loading, setLoading] = useState(true);
  const [searchOpen, setSearchOpen] = useState(false), [tipsOpen, setTipsOpen] = useState(false);
  const searchRef = useRef(null);

  useEffect(() => {
    const viewport = window.matchMedia?.(VTO_MOBILE_QUERY);
    if (!viewport) return undefined;
    const sync = () => document.documentElement.classList.toggle('vto-mobile-active', viewport.matches);
    sync();
    viewport.addEventListener?.('change', sync);
    return () => {
      viewport.removeEventListener?.('change', sync);
      document.documentElement.classList.remove('vto-mobile-active');
    };
  }, []);

  useEffect(() => { if (searchOpen) searchRef.current?.focus(); }, [searchOpen]);
  useEffect(() => {
    const controller = new AbortController(); setLoading(true);
    const timer = setTimeout(() => api.get('/try-on/catalog', { params: { q, offset }, signal: controller.signal }).then(({ data }) => {
      setProducts(data.products); setNext(data.next_offset);
      setSelected(previous => previous || data.products[0] || null);
    }).catch(e => { if (!controller.signal.aborted) setError(apiError(e)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); }), 200);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [q, offset]);
  useEffect(() => {
    const available = selected?.variants?.find(v => v.stock > v.reserved);
    setVariantId(available?.id || selected?.variants?.[0]?.id || '');
  }, [selected]);

  const variant = selected?.variants?.find(v => v.id === variantId);
  const stock = variant ? variant.stock - variant.reserved : 0;
  const assets = useMemo(() => (selected?.try_on_assets || [])
    .filter(a => !a.variant_id || a.variant_id === variantId)
    .sort((a, b) => Number(Boolean(b.variant_id)) - Number(Boolean(a.variant_id))), [selected, variantId]);
  // Swapping frame assets keeps the camera component and its stream mounted.
  const studioAssets = assets.length ? assets : selected?.try_on_assets || [];
  const price = selected ? (selected.flash_sale_price ?? variant?.price_override ?? selected.discount_price ?? selected.price) : 0;
  const buy = async () => {
    if (!user) { navigate('/login?redirect=/virtual-try-on'); return; }
    if (!variant || stock < 1 || busy) return;
    setBusy(true); setError('');
    try {
      await api.post('/cart', { product_id: selected.id, variant_id: variant.id, quantity: 1 });
      await refreshCartCount(); toast.success('Frame ditambahkan ke keranjang');
    } catch (e) { setError(apiError(e)); } finally { setBusy(false); }
  };

  const productCard = selected && <div className="vto-product-card rounded-2xl bg-white/95 backdrop-blur p-3 sm:p-4 shadow-lg flex items-end justify-between gap-3">
    <div className="min-w-0 flex-1">
      <p className="vto-product-sku text-xs text-meow-gray truncate">{variant?.sku || selected.sku || 'Frame Meow Eyes'}</p>
      <h2 className="font-bold sm:text-lg truncate">{selected.name}</h2>
      <p className="vto-product-description text-xs line-clamp-2">{(selected.short_description || selected.description || '').replace(/<[^>]+>/g, ' ').slice(0, 160)}</p>
      <p className="text-meow-salmon font-black mt-1">{formatIDR(price)}</p>
      {selected.variants?.length > 1 && <label className="text-xs block mt-1">Varian
        <select aria-label="Varian frame" className="rounded border px-2 py-1 w-full max-w-48" value={variantId} onChange={e => setVariantId(e.target.value)}>
          {selected.variants.map(v => <option key={v.id} value={v.id}>{v.label || v.name || v.sku}{v.stock <= v.reserved ? ' · Habis' : ''}</option>)}
        </select>
      </label>}
      {!assets.length && <p className="text-xs text-amber-700">Pratinjau varian ini belum tersedia; menampilkan contoh produk.</p>}
    </div>
    <button onClick={buy} disabled={busy || stock < 1} className="btn-primary shrink-0 disabled:opacity-50">{busy ? 'Menambah…' : stock > 0 ? 'Beli' : 'Habis'}</button>
  </div>;

  return <div className="vto-page max-w-[1600px] mx-auto px-3 md:px-6 py-5">
    <div className="vto-desktop-header flex items-center justify-between gap-3 mb-4">
      <div><h1 className="text-2xl md:text-3xl font-black">Virtual Try-On</h1><p className="text-sm text-meow-gray">Pilih frame di samping, lalu coba langsung dengan kamera.</p></div>
      <Link to="/cart" className="btn-secondary text-sm">Keranjang</Link>
    </div>

    <div className="vto-mobile-toolbar">
      <Link to="/shop-now" aria-label="Kembali ke toko" className="vto-tool-button"><ArrowLeft aria-hidden="true" size={20} /></Link>
      <h1>Virtual Try-On</h1>
      <button type="button" className="vto-tool-button" aria-label="Panduan kamera" aria-expanded={tipsOpen} aria-controls="vto-camera-tips" onClick={() => setTipsOpen(!tipsOpen)}><Info aria-hidden="true" size={20} /></button>
      <Link to="/cart" aria-label="Keranjang belanja" className="vto-tool-button"><ShoppingCart aria-hidden="true" size={20} /></Link>
    </div>
    {tipsOpen && <div id="vto-camera-tips" className="vto-mobile-tips" role="region" aria-label="Panduan kamera">
      <div className="flex justify-between items-center gap-3"><strong>Panduan Kamera</strong><button type="button" className="vto-tool-button" aria-label="Tutup panduan" onClick={() => setTipsOpen(false)}><X aria-hidden="true" size={18} /></button></div>
      <p>Hadapkan wajah ke kamera dengan kedua mata terlihat dan pencahayaan cukup. Geser daftar frame untuk mencoba model lain.</p>
      <p>Video dan foto diproses di perangkat Anda dan tidak diunggah. Kamera berhenti ketika Anda keluar atau tab tidak aktif.</p>
      <p>Try-on adalah pratinjau gaya frame, bukan pengukuran ukuran atau PD.</p>
    </div>}
    {error && <div role="alert" className="vto-page-error p-3 mb-4 bg-red-50 rounded-xl text-red-700 flex items-start gap-2"><p className="flex-1">{error}</p><button type="button" aria-label="Tutup pesan" onClick={() => setError('')}><X size={18} /></button></div>}

    <div className="vto-layout">
      <section className="vto-camera-section min-w-0">
        {studioAssets.length ? <TryOnStudio assets={studioAssets} name={selected.name} immersive stageOverlay={productCard} />
          : <div className="vto-immersive-stage bg-white rounded-2xl grid place-items-center p-8 text-center">{loading ? 'Memuat katalog frame…' : 'Frame untuk Virtual Try-On belum tersedia. Admin dapat menerbitkan aset try-on terlebih dahulu.'}</div>}
      </section>
      <aside className="vto-catalog" aria-label="Pilihan frame">
        <div className="vto-catalog-heading"><h2 className="text-sm font-bold">Pilih Frame</h2><button type="button" className="vto-search-toggle vto-tool-button" aria-label={searchOpen ? 'Tutup pencarian frame' : 'Cari frame'} aria-expanded={searchOpen} aria-controls="vto-catalog-search" onClick={() => setSearchOpen(!searchOpen)}>{searchOpen ? <X size={18} /> : <Search size={18} />}</button></div>
        <div id="vto-catalog-search" className="vto-catalog-search" data-open={searchOpen}>
          <label htmlFor="vto-frame-query" className="sr-only">Cari frame berdasarkan nama atau kode</label>
          <input ref={searchRef} id="vto-frame-query" value={q} onChange={e => { setQ(e.target.value); setOffset(0); }} placeholder="Cari nama / kode" className="loyalty-input w-full" />
        </div>
        <div className="vto-product-list">{products.map(product => <button type="button" key={product.id} onClick={() => { setSelected(product); setError(''); setSearchOpen(false); }} aria-pressed={selected?.id === product.id} className={`vto-frame-option text-left rounded-2xl border-2 overflow-hidden bg-white shrink-0 ${selected?.id === product.id ? 'border-meow-salmon' : 'border-transparent'}`}>
          <img className="w-full aspect-[4/3] object-cover" src={imageSrc(product.main_image)} alt="" />
          <div className="p-3"><p className="text-sm font-bold line-clamp-2">{product.name}</p><p className="text-xs text-meow-salmon mt-1">{formatIDR(product.flash_sale_price ?? product.discount_price ?? product.price)}</p></div>
        </button>)}</div>
        {!loading && !products.length && <p className="vto-catalog-empty">Frame tidak ditemukan.</p>}
        {(offset > 0 || next != null) && <div className="vto-catalog-pagination flex gap-3 text-xs mt-3"><button disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 30))}>Sebelumnya</button><button disabled={next == null} onClick={() => setOffset(next)}>Berikutnya</button></div>}
      </aside>
    </div>
  </div>;
}
'''
Path('../frontend/src/pages/VirtualTryOnPage.jsx').write_text(page, encoding='utf-8')
