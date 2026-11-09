import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api, apiError, formatIDR, imageSrc } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import ProductCard from "../components/ProductCard";
import VirtualTryOn from "../components/VirtualTryOn";
import { PrescriptionFields, prescriptionValues } from "../components/PrescriptionForm";
import { ChevronRight, Heart, Truck, ShieldCheck, Sparkles, Star, BellRing, Cat } from "lucide-react";
import { toast } from "sonner";

const ProductDetailPage = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, refreshCartCount } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  const [selectedImg, setSelectedImg] = useState(0);
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [qty, setQty] = useState(1);
  // Lens bundle state
  const [wantLens, setWantLens] = useState(false);
  const [lensOptions, setLensOptions] = useState({ lens_products: [], lens_indexes: [] });
  const [lensProductId, setLensProductId] = useState("");
  const [lensIndexId, setLensIndexId] = useState("");
  const [rx, setRx] = useState(() => prescriptionValues());
  // Recommended bundle picks (Basic / Popular / Premium)
  const [bundlePicks, setBundlePicks] = useState([]);
  const [bundleFor, setBundleFor] = useState("");
  const [bundleLoading, setBundleLoading] = useState(false);
  const [bundleError, setBundleError] = useState("");
  const [bundleReload, setBundleReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(""); setQty(1); setRx(prescriptionValues());
    setSelectedImg(0); setSelectedVariant(null);
    setWantLens(false); setLensProductId(""); setLensIndexId("");
    setLensOptions({ lens_products: [], lens_indexes: [] }); setBundlePicks([]);
    api.get(`/products/${slug}`, { signal: controller.signal }).then(({ data: response }) => {
      setData(response);
      if (response.product.variants?.length > 0) setSelectedVariant(response.product.variants[0]);
      if (response.product.product_type === "frame") {
        api.get(`/lens/options-for-frame/${response.product.id}`, { signal: controller.signal }).then(({ data: options }) => setLensOptions(options)).catch(() => {});
      }
    }).catch((err) => { if (!controller.signal.aborted) setError(apiError(err, "Produk belum dapat dimuat.")); });
    return () => controller.abort();
  }, [slug]);

  const frameId = data?.product?.product_type === "frame" ? data.product.id : null;
  const variantId = selectedVariant?.id;
  const currentBundleKey = frameId && variantId ? `${frameId}:${variantId}` : "";
  useEffect(() => {
    const controller = new AbortController();
    setBundlePicks([]); setBundleFor(""); setBundleError("");
    if (!frameId || !variantId) { setBundleLoading(false); return () => controller.abort(); }
    setBundleLoading(true);
    api.get(`/lens/recommended-bundle/${frameId}`, { params: { variant_id: variantId }, signal: controller.signal }).then(({ data: response }) => {
      if (controller.signal.aborted) return;
      if (response.frame?.variant_id !== variantId) { setBundleError("Paket belum tersedia untuk varian ini. Coba muat ulang rekomendasi."); return; }
      setBundlePicks(response.picks || []); setBundleFor(`${frameId}:${variantId}`);
    }).catch((err) => { if (!controller.signal.aborted) setBundleError(apiError(err, "Rekomendasi paket belum dapat dimuat.")); })
      .finally(() => { if (!controller.signal.aborted) setBundleLoading(false); });
    return () => controller.abort();
  }, [frameId, variantId, bundleReload]);
  const bundleCurrent = Boolean(currentBundleKey && bundleFor === currentBundleKey);

  if (error) return <div className="max-w-xl mx-auto p-8 text-center" role="alert"><p>{error}</p><Link to="/shop-now" className="btn-secondary inline-block mt-4">Kembali ke Shop Now</Link></div>;

  if (!data) {
    return <div className="min-h-screen flex items-center justify-center"><Cat className="h-10 w-10 text-meow-salmon animate-pulse" /></div>;
  }
  const p = data.product;
  const gallery = p.gallery?.length ? p.gallery : [p.main_image];
  const flashAvailable = Number(p.flash_sale_available ?? (data.flash_item ? Math.max(0, Number(data.flash_item.quota) - Number(data.flash_item.sold || 0) - Number(data.flash_item.reserved || 0)) : 0));
  const hasFlash = Boolean(data.flash_item && flashAvailable >= qty);
  const price = hasFlash ? data.flash_item.flash_price : selectedVariant?.price_override ?? p.discount_price ?? p.price;
  const hasDiscount = p.discount_price && p.discount_price < p.price;
  const stock = selectedVariant ? Math.max(0, (selectedVariant.stock || 0) - (selectedVariant.reserved || 0)) : 0;
  const selectedLens = lensOptions.lens_products?.find((lens) => lens.id === lensProductId);
  const selectedLensVariant = selectedLens?.variants?.find((variant) => variant.is_active !== false);
  const lensStock = selectedLensVariant ? Math.max(0, Number(selectedLensVariant.stock || 0) - Number(selectedLensVariant.reserved || 0)) : 0;

  const addToCart = async () => {
    if (!user) { navigate("/login"); return false; }
    if (stock <= 0 || qty > stock) { toast.error("Jumlah melebihi stok yang tersedia"); return false; }
    if (wantLens && !lensProductId) { toast.error("Pilih jenis lensa terlebih dahulu"); return false; }
    if (wantLens && (!selectedLensVariant || lensStock < qty)) { toast.error("Stok lensa tidak cukup untuk jumlah yang dipilih"); return false; }
    if (adding) return false;
    setAdding(true);
    try {
      const body = {
        product_id: p.id,
        variant_id: selectedVariant?.id,
        quantity: qty,
      };
      if (wantLens && lensProductId) {
        body.lens_product_id = lensProductId;
        body.lens_variant_id = selectedLensVariant.id;
        body.lens_index_id = lensIndexId || null;
        if (Object.values(rx).some((v) => v)) body.prescription = { ...rx };
      }
      await api.post("/cart", body);
      toast.success(wantLens && lensProductId ? "Frame + Lensa ditambahkan ke keranjang" : "Ditambahkan ke keranjang");
      refreshCartCount();
      return true;
    } catch (e) {
      toast.error(apiError(e, "Gagal menambahkan"));
      return false;
    } finally { setAdding(false); }
  };

  const buyNow = async () => {
    if (await addToCart()) navigate("/cart");
  };

  // One-click checkout for a curated Basic / Popular / Premium bundle pick.
  const buyBundle = async (pick) => {
    if (!user) { navigate("/login"); return; }
    if (adding || !bundleCurrent || bundleLoading || pick.frame_variant_id !== variantId || !pick.available || !pick.lens_variant_id) { toast.error("Paket belum tersedia untuk varian ini"); return; }
    if (stock <= 0) { toast.error("Stok habis"); return; }
    setAdding(true);
    try {
      await api.post("/cart", {
        product_id: p.id,
        variant_id: pick.frame_variant_id,
        quantity: 1,
        lens_product_id: pick.lens_product_id,
        lens_variant_id: pick.lens_variant_id,
        lens_index_id: pick.lens_index_id,
      });
      refreshCartCount();
      toast.success(`Paket ${pick.label} ditambahkan ke keranjang`);
      navigate("/cart");
    } catch (e) {
      toast.error(apiError(e, "Gagal menambahkan paket"));
    } finally { setAdding(false); }
  };

  const toggleWishlist = async () => {
    if (!user) { navigate("/login"); return; }
    try {
      await api.post(`/wishlist/${p.id}`);
      toast.success("Disimpan ke wishlist");
    } catch {
      toast.error("Gagal menyimpan wishlist");
    }
  };

  const subscribeProduct = async () => {
    if (!user) { navigate("/login"); return; }
    try {
      await api.post(`/products/${p.id}/subscribe`);
      toast.success("Kami akan beritahu kalau stok / harga berubah");
    } catch { /* noop */ }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 py-6" data-testid="product-detail-page">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-sm text-meow-gray mb-6" data-testid="pd-breadcrumb">
        <Link to="/" className="hover:text-meow-salmon">Home</Link>
        <ChevronRight className="h-3 w-3" /><Link to="/shop-now" className="hover:text-meow-salmon">Shop Now</Link>
        {(data.breadcrumb || []).map((b) => (
          <React.Fragment key={b.id}>
            <ChevronRight className="h-3 w-3" />
            <Link to={`/category/${b.slug}`} className="hover:text-meow-salmon">{b.name}</Link>
          </React.Fragment>
        ))}
        <ChevronRight className="h-3 w-3" />
        <span aria-current="page" className="text-meow-midnight font-semibold">{p.name}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Gallery */}
        <div className="lg:col-span-7">
          <div className="rounded-[32px] overflow-hidden bg-white aspect-square" data-testid="gallery-main">
            <img src={imageSrc(gallery[selectedImg])} alt={p.name} className="w-full h-full object-cover" />
          </div>
          <div className="flex gap-2 mt-3" data-testid="gallery-thumbs">
            {gallery.map((g, i) => (
              <button key={i} onClick={() => setSelectedImg(i)}
                className={`h-20 w-20 rounded-2xl overflow-hidden border-2 ${i === selectedImg ? "border-meow-salmon" : "border-transparent"}`}
                data-testid={`thumb-${i}`}>
                <img src={imageSrc(g)} alt="" className="w-full h-full object-cover" />
              </button>
            ))}
          </div>
          {p.product_type === "frame" && <VirtualTryOn productId={p.id} variantId={selectedVariant?.id} productName={p.name} />}
        </div>

        {/* Info */}
        <div className="lg:col-span-5 space-y-5">
          {data.brand && (
            <p className="text-xs uppercase tracking-[0.2em] font-bold text-meow-salmon" data-testid="pd-brand">{data.brand.name}</p>
          )}
          <h1 className="font-heading text-3xl md:text-4xl font-black" data-testid="pd-name">{p.name}</h1>
          <div className="flex items-center gap-4 text-sm text-meow-gray">
            <span className="flex items-center gap-1"><Star className="h-4 w-4 text-meow-amber fill-meow-amber" />{p.rating_count ? Number(p.rating_avg || 0).toFixed(1) : "Belum ada rating"} ({p.rating_count || 0} ulasan)</span>
            <span>•</span>
            <span>Terjual {p.sold_count || 0}</span>
          </div>

          <div className="bg-white rounded-3xl p-5 border border-meow-midnight/5" data-testid="pd-price-card">
            {hasFlash && <p className="text-xs font-bold uppercase tracking-wider text-meow-salmon mb-1">⚡ Flash Sale</p>}
            <div className="flex items-baseline gap-3">
              <p className="font-heading font-black text-3xl text-meow-salmon" data-testid="pd-price">{formatIDR(price)}</p>
              {(hasDiscount || hasFlash) && (
                <p className="text-meow-gray line-through text-base">{formatIDR(p.price)}</p>
              )}
            </div>
            {data.flash_item && <p className="text-xs text-meow-gray mt-2">Kuota promo tersedia: {flashAvailable}. {qty > flashAvailable ? "Jumlah pilihan melebihi kuota promo; harga reguler berlaku." : "Harga dan kuota diperiksa kembali saat checkout."}</p>}
          </div>

          {p.variants?.length > 0 && (
            <div>
              <p className="text-sm font-bold mb-2">Pilih Varian:</p>
              <div className="flex flex-wrap gap-2" data-testid="variant-list">
                {p.variants.map((v) => (
                  <button key={v.id} onClick={() => { setSelectedVariant(v); setQty((current) => Math.max(1, Math.min(current, Number(v.stock || 0) - Number(v.reserved || 0)))); }}
                    className={`px-4 py-2 rounded-full border-2 text-sm font-semibold ${selectedVariant?.id === v.id ? "border-meow-salmon bg-meow-salmon/10 text-meow-salmon" : "border-meow-midnight/10 hover:border-meow-midnight"}`}
                    data-testid={`variant-${v.sku}`}>
                    {v.color_hex && <span className="inline-block h-3 w-3 rounded-full mr-2 align-middle" style={{ background: v.color_hex }} />}
                    {[v.color, v.size, v.lens_type].filter(Boolean).join(" · ")}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center gap-4">
            <p className="text-sm font-bold">Jumlah:</p>
            <div className="flex items-center bg-meow-bg rounded-full">
              <button onClick={() => setQty(Math.max(1, qty - 1))} className="px-3 py-1.5 font-bold" data-testid="qty-minus">-</button>
              <span className="px-3 py-1.5 font-bold" data-testid="qty-display">{qty}</span>
              <button disabled={qty >= stock} onClick={() => setQty(Math.min(stock, qty + 1))} className="px-3 py-1.5 font-bold" data-testid="qty-plus">+</button>
            </div>
            <p className="text-xs text-meow-gray">Stok: {stock}</p>
          </div>

          {/* Recommended One-Click Bundle Picks */}
          {p.product_type === "frame" && variantId && (bundleLoading || !bundleCurrent || bundleError || bundlePicks.length > 0) && (
            <div className="rounded-3xl p-5 bg-gradient-to-br from-meow-salmon/10 via-white to-meow-amber/10 border border-meow-salmon/20" data-testid="bundle-picks">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="h-5 w-5 text-meow-salmon" />
                <p className="font-heading text-lg font-black">Paket Rekomendasi</p>
                <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-meow-salmon text-white font-bold uppercase tracking-wider">Hemat 1-Klik</span>
              </div>
              <p className="text-xs text-meow-gray mb-4">Satu frame + satu lensa + index untuk varian yang dipilih. Harga dan stok diperiksa kembali saat checkout.</p>
              {bundleError ? <p role="alert" className="text-xs text-red-600">{bundleError} <button type="button" onClick={() => setBundleReload((value) => value + 1)} className="underline font-bold">Coba lagi</button></p> : (!bundleCurrent || bundleLoading) ? <p role="status" className="text-xs text-meow-gray" data-testid="bundle-loading">Memperbarui harga paket untuk varian ini…</p> : null}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(bundleCurrent && !bundleLoading ? bundlePicks : []).map((pick) => {
                  const featured = pick.tier === "popular";
                  return (
                    <div
                      key={pick.tier}
                      className={`rounded-2xl p-4 flex flex-col border-2 transition-all ${
                        featured ? "border-meow-salmon bg-white shadow-lg" : "border-meow-midnight/10 bg-white/60"
                      }`}
                      data-testid={`bundle-pick-${pick.tier}`}
                    >
                      <div className="flex items-start justify-between mb-1">
                        <p className="font-black text-sm">{pick.label}</p>
                        {featured && (
                          <span className="text-[9px] px-2 py-0.5 rounded-full bg-meow-salmon text-white font-bold uppercase">Populer</span>
                        )}
                      </div>
                      <p className="text-xs text-meow-gray leading-snug mb-3">{pick.tagline}</p>
                      <ul className="text-xs space-y-1 mb-3">
                        <li className="flex gap-1"><span className="text-meow-mint">▪</span> {pick.lens_product_name}</li>
                        <li className="flex gap-1"><span className="text-meow-mint">▪</span> Index {pick.lens_index_name}</li>
                      </ul>
                      <div className="mt-auto">
                        <p className="font-heading text-xl font-black text-meow-salmon" data-testid={`bundle-total-${pick.tier}`}>{formatIDR(pick.bundle_total)}</p>
                        {pick.savings > 0 && (
                          <p className="text-[11px] text-meow-mint font-bold">Hemat {formatIDR(pick.savings)}</p>
                        )}
                        <button
                          onClick={() => buyBundle(pick)}
                          disabled={adding || !bundleCurrent || bundleLoading || !pick.available || pick.frame_variant_id !== variantId}
                          className={`mt-3 w-full py-2 rounded-full text-xs font-bold transition-transform hover:scale-[1.02] disabled:opacity-40 ${
                            featured ? "bg-meow-salmon text-white" : "bg-meow-midnight text-white"
                          }`}
                          data-testid={`bundle-buy-${pick.tier}`}
                        >
                          {pick.available ? "Ambil Paket Ini" : "Stok Paket Habis"}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Frame + Lens picker */}
          {p.product_type === "frame" && lensOptions.lens_products?.length > 0 && (
            <div className="bg-meow-amber/10 rounded-3xl p-4" data-testid="lens-picker">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={wantLens} onChange={(e) => setWantLens(e.target.checked)} data-testid="want-lens-checkbox" />
                <span className="font-bold">🐱 Tambahkan Lensa (Bundle Hemat)</span>
              </label>
              {wantLens && (
                <div className="mt-3 space-y-2">
                  <select value={lensProductId} onChange={(e) => setLensProductId(e.target.value)} className="w-full px-3 py-2 rounded-xl bg-white outline-none text-sm" data-testid="lens-product-select">
                    <option value="">— Pilih Jenis Lensa —</option>
                    {lensOptions.lens_products.map((lens) => {
                      const variant = lens.variants?.find((item) => item.is_active !== false);
                      const available = variant ? Math.max(0, Number(variant.stock || 0) - Number(variant.reserved || 0)) : 0;
                      const lensPrice = variant?.price_override ?? lens.discount_price ?? lens.price;
                      return <option key={lens.id} value={lens.id} disabled={!available}>{lens.name} — {formatIDR(lensPrice)}{!available ? " · Stok habis" : ""}</option>;
                    })}
                  </select>
                  {lensProductId && (
                    <select value={lensIndexId} onChange={(e) => setLensIndexId(e.target.value)} className="w-full px-3 py-2 rounded-xl bg-white outline-none text-sm" data-testid="lens-index-select">
                      <option value="">— Pilih Index Lensa (Opsional) —</option>
                      {lensOptions.lens_indexes.map((li) => (
                        <option key={li.id} value={li.id}>{li.name} (+{formatIDR(li.additional_price)}) — {li.recommended_power_range}</option>
                      ))}
                    </select>
                  )}
                  {lensProductId && (
                    <details className="text-xs text-meow-gray">
                      <summary className="cursor-pointer font-bold py-2">Input resep kacamata (opsional)</summary>
                      <div className="mt-2"><PrescriptionFields value={rx} onChange={setRx} idPrefix="product-rx" /></div>
                      <p className="mt-2">Anda dapat mengisi kembali resep dan melampirkan fotonya saat checkout.</p>
                    </details>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <button onClick={addToCart} disabled={adding || stock <= 0} className="btn-secondary disabled:opacity-50" data-testid="add-to-cart-btn">+ Tambah ke Cart</button>
            <button onClick={buyNow} disabled={adding || stock <= 0} className="btn-primary disabled:opacity-50" data-testid="buy-now-btn">Beli Sekarang</button>
          </div>
          <div className="flex gap-2 text-xs">
            <button onClick={toggleWishlist} className="flex items-center gap-1 text-meow-gray hover:text-meow-salmon" data-testid="add-wishlist-btn">
              <Heart className="h-4 w-4" /> Wishlist
            </button>
            <button onClick={subscribeProduct} className="flex items-center gap-1 text-meow-gray hover:text-meow-salmon" data-testid="subscribe-btn">
              <BellRing className="h-4 w-4" /> Notify saya
            </button>
          </div>

          <div className="bg-white rounded-3xl p-5 grid grid-cols-3 gap-3 text-center text-xs" data-testid="pd-perks">
            <div><Truck className="h-5 w-5 mx-auto text-meow-mint" /><p className="mt-1 font-bold">Cek Ongkir Realtime</p></div>
            <div><ShieldCheck className="h-5 w-5 mx-auto text-meow-amber" /><p className="mt-1 font-bold">Garansi 12 Bulan</p></div>
            <div><Sparkles className="h-5 w-5 mx-auto text-meow-salmon" /><p className="mt-1 font-bold">Dapat Poin</p></div>
          </div>
        </div>
      </div>

      {/* Description */}
      <section className="mt-10 grid lg:grid-cols-3 gap-6" data-testid="pd-desc-section">
        <div className="lg:col-span-2 bg-white rounded-3xl p-6">
          <h3 className="font-heading text-2xl font-extrabold mb-3">Tentang Produk</h3>
          <p className="text-meow-gray leading-relaxed">{p.description}</p>
        </div>
        <div className="bg-white rounded-3xl p-6">
          <h3 className="font-heading text-xl font-extrabold mb-3">Spesifikasi</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-meow-gray">SKU</dt><dd className="font-bold">{p.sku}</dd></div>
            <div className="flex justify-between"><dt className="text-meow-gray">Berat</dt><dd className="font-bold">{p.weight_gram}g</dd></div>
            {p.dimension && <div className="flex justify-between"><dt className="text-meow-gray">Dimensi</dt><dd className="font-bold">{p.dimension}</dd></div>}
            {Object.entries(p.spec || {}).map(([k, v]) => (
              <div key={k} className="flex justify-between gap-2">
                <dt className="text-meow-gray">{k}</dt><dd className="font-bold text-right">{String(v)}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* Reviews */}
      {data.reviews?.length > 0 && (
        <section className="mt-10" data-testid="pd-reviews-section">
          <h3 className="font-heading text-2xl font-extrabold mb-4">Ulasan Pembeli</h3>
          <div className="grid md:grid-cols-2 gap-4">
            {data.reviews.map((r) => (
              <div key={r.id} className="bg-white rounded-3xl p-5">
                <div className="flex items-center justify-between">
                  <p className="font-bold">{r.user_name}</p>
                  <div className="flex">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className={`h-4 w-4 ${i < r.rating ? "text-meow-amber fill-meow-amber" : "text-meow-midnight/10"}`} />
                    ))}
                  </div>
                </div>
                <p className="text-sm text-meow-gray mt-2 leading-relaxed">{r.body}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Related */}
      {data.related?.length > 0 && (
        <section className="mt-12" data-testid="pd-related-section">
          <h3 className="font-heading text-2xl font-extrabold mb-4">Produk Terkait</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {data.related.slice(0, 4).map((r) => <ProductCard key={r.id} product={r} />)}
          </div>
        </section>
      )}
    </div>
  );
};

export default ProductDetailPage;
