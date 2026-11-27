import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { api, apiError, formatIDR, imageSrc } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import ProductCard from "../components/ProductCard";
import HtmlContent from "../components/HtmlContent";
import VirtualTryOn from "../components/VirtualTryOn";
import ProductMeowsurement from "../components/ProductMeowsurement";
import ProductOpticalOptions, { emptyOptical } from '../components/ProductOpticalOptions';
import { prescriptionValues } from '../components/PrescriptionForm';
import AddonChooser from '../components/AddonChooser';
import { ChevronRight, Heart, Truck, ShieldCheck, Sparkles, Star, BellRing, Cat } from "lucide-react";
import { toast } from "sonner";
import { isTryOnProduct } from '../lib/tryOnProducts';

const ProductDetailPage = () => {

  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, refreshCartCount } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  const [purchaseIntent, setPurchaseIntent] = useState(null);
  const [selectedImg, setSelectedImg] = useState(0);
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [qty, setQty] = useState(1);
  const location = useLocation();
  const editCartId = new URLSearchParams(location.search).get('cart_item_id') || '';
  const [optical,setOptical] = useState(emptyOptical);
  const [opticalBusy,setOpticalBusy] = useState(false);
  const [uploadedPhoto,setUploadedPhoto] = useState(null);
  const [editItem,setEditItem] = useState(null);
  useEffect(() => {
    const controller=new AbortController();
    setData(null);setError('');setQty(1);setSelectedImg(0);setSelectedVariant(null);
    setOptical(emptyOptical());setOpticalBusy(false);setUploadedPhoto(null);setEditItem(null);setPurchaseIntent(null);
    const load=async()=>{
      try {
        const {data:response}=await api.get(`/products/${slug}`,{signal:controller.signal});
        let item=null;
        if(editCartId){const {data:cart}=await api.get('/cart',{signal:controller.signal});item=cart.items?.find(item=>item.id===editCartId&&item.product.id===response.product.id);if(!item)throw new Error('cart item missing');}
        if(controller.signal.aborted)return;
        setData(response);setSelectedVariant(response.product.variants?.find(variant=>variant.id===item?.variant_id)||response.product.variants?.[0]||null);
        if(item){setQty(item.quantity);setEditItem(item);setOptical({...emptyOptical(),lens_index_id:item.lens_index?.id||'',lens_index_name:item.lens_index?.name||'',prescription:prescriptionValues(item.prescription),tinting:item.tinting||null});}
      }catch(err){if(!controller.signal.aborted)setError(apiError(err,'Produk atau item keranjang belum dapat dimuat.'));}
    };
    load();return()=>controller.abort();
  },[slug,editCartId]);

  if (error) return <div className="max-w-xl mx-auto p-8 text-center" role="alert"><p>{error}</p><Link to="/shop-now" className="btn-secondary inline-block mt-4">{"Kembali ke Shop Now"}</Link></div>;

  if (!data) {
    return <div className="min-h-screen flex items-center justify-center"><Cat className="h-10 w-10 text-meow-salmon animate-pulse" /></div>;
  }
  const p = data.product;
  const gallery = [...new Set([p.main_image, ...(p.gallery || [])].filter(Boolean))];
  const flashAvailable = Number(p.flash_sale_available ?? (data.flash_item ? Math.max(0, Number(data.flash_item.quota) - Number(data.flash_item.sold || 0) - Number(data.flash_item.reserved || 0)) : 0));
  const hasFlash = Boolean(data.flash_item && flashAvailable >= qty);
  const price = hasFlash ? data.flash_item.flash_price : selectedVariant?.price_override ?? p.discount_price ?? p.price;
  const hasDiscount = p.discount_price && p.discount_price < p.price;
  const stock = selectedVariant ? Math.max(0, (selectedVariant.stock || 0) - (selectedVariant.reserved || 0)) : 0;
  const opticalEligible=['frame','lens','package'].includes(p.product_type)&&(p.sale_role||'main')==='main';
  const incompleteLens=Boolean(optical.lens_type&&!optical.lens_index_id);
  const addToCart = async (addons = []) => {
    if(!user){navigate('/login');return false;}
    if(adding||opticalBusy)return false;
    if(stock<=0||qty>stock){toast.error('Jumlah melebihi stok yang tersedia');return false;}
    if(incompleteLens){toast.error('Pilih indeks lensa terlebih dahulu');return false;}
    setAdding(true);
    try{
      const prescription={...optical.prescription};
      if(optical.file){
        let uploadId=uploadedPhoto?.file===optical.file?uploadedPhoto.id:null;
        if(!uploadId){const upload=new FormData();upload.append('file',optical.file);const{data}=await api.post('/uploads/prescription',upload);uploadId=data.id;setUploadedPhoto({file:optical.file,id:uploadId});}
        prescription.attachment_upload_id=uploadId;
      }
      if(editCartId){
        await api.patch(`/cart/${encodeURIComponent(editCartId)}/configuration`,{variant_id:selectedVariant?.id,quantity:qty,
          lens_index_id:optical.lens_index_id||null,prescription,tinting_id:optical.tinting?.id||null,replace_lens_product:optical.replace_lens_product});
      }else{
        await api.post('/cart',{product_id:p.id,variant_id:selectedVariant?.id,quantity:qty,addons,
          ...(opticalEligible?{lens_index_id:optical.lens_index_id||null,prescription:Object.values(prescription).some(value=>value!==''&&value!=null)?prescription:null,tinting_id:optical.tinting?.id||null}:{})});
      }
      toast.success(editCartId?'Pilihan produk diperbarui':'Ditambahkan ke keranjang');refreshCartCount();return true;
    }catch(err){toast.error(apiError(err,'Pilihan produk belum berhasil disimpan'));return false;}
    finally{setAdding(false);}
  };

  const beginPurchase = async (intent) => {
    if (!user) {navigate('/login');return;}
    if(editCartId){if(await addToCart()){const previous=location.state?.checkout_item_ids;const ids=Array.isArray(previous)&&previous.includes(editCartId)?[...new Set(previous.filter(id=>typeof id==='string'))]:[editCartId];navigate('/checkout',{state:{selected_item_ids:ids}});}return;}
    if(incompleteLens){toast.error('Pilih indeks lensa terlebih dahulu');return;}
    if ((p.sale_role || 'main') === 'main') {setPurchaseIntent(intent);return;}
    if (await addToCart()) {if (intent === 'buy') navigate('/cart');}
  };
  const confirmAddons = async (addons) => {
    if (await addToCart(addons)) {const intent = purchaseIntent;setPurchaseIntent(null);if (intent === 'buy') navigate('/cart');}
  };

  const toggleWishlist = async () => {
    if (!user) {navigate("/login");return;}
    try {
      await api.post(`/wishlist/${p.id}`);
      toast.success("Disimpan ke wishlist");
    } catch {
      toast.error("Gagal menyimpan wishlist");
    }
  };

  const subscribeProduct = async () => {
    if (!user) {navigate("/login");return;}
    try {
      await api.post(`/products/${p.id}/subscribe`);
      toast.success("Kami akan beritahu kalau stok / harga berubah");
    } catch {/* noop */}
  };

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 py-6" data-testid="product-detail-page">
      {/* Breadcrumb */}
      <nav aria-label={"Breadcrumb"} className="flex flex-wrap items-center gap-2 text-sm text-meow-gray mb-6" data-testid="pd-breadcrumb">
        <Link to="/" className="hover:text-meow-salmon">{"Home"}</Link>
        <ChevronRight className="h-3 w-3" /><Link to="/shop-now" className="hover:text-meow-salmon">{"Shop Now"}</Link>
        {(data.breadcrumb || []).map((b) =>
        <React.Fragment key={b.id}>
            <ChevronRight className="h-3 w-3" />
            <Link to={`/category/${b.slug}`} className="hover:text-meow-salmon">{b?.["name"]}</Link>
          </React.Fragment>
        )}
        <ChevronRight className="h-3 w-3" />
        <span aria-current="page" className="text-meow-midnight font-semibold">{p?.["name"]}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Gallery */}
        <div className="lg:col-span-7">
          <div className="rounded-[32px] overflow-hidden bg-white aspect-square" data-testid="gallery-main">
            <img src={imageSrc(gallery[selectedImg])} alt={p?.["name"]} className="w-full h-full object-cover" />
          </div>
          <div className="flex flex-wrap gap-2 mt-3" data-testid="gallery-thumbs">
            {gallery.map((g, i) =>
            <button key={i} onClick={() => setSelectedImg(i)}
            className={`h-20 w-20 rounded-2xl overflow-hidden border-2 ${i === selectedImg ? "border-meow-salmon" : "border-transparent"}`}
            data-testid={`thumb-${i}`}>
                <img src={imageSrc(g)} alt="" className="w-full h-full object-cover" />
              </button>
            )}
          </div>
          {isTryOnProduct(p) && <VirtualTryOn productId={p.id} variantId={selectedVariant?.id} productName={p.name} />}
          {p.product_type === "frame" && <ProductMeowsurement productId={p.id} variantId={selectedVariant?.id} />}
        </div>

        {/* Info */}
        <div className="lg:col-span-5 space-y-5">
          {data.brand &&
          <p className="text-xs uppercase tracking-[0.2em] font-bold text-meow-salmon" data-testid="pd-brand">{data.brand?.["name"]}</p>
          }
          <h1 className="font-heading text-3xl md:text-4xl font-black" data-testid="pd-name">{p?.["name"]}</h1>
          <div className="flex items-center gap-4 text-sm text-meow-gray">
            <span className="flex items-center gap-1"><Star className="h-4 w-4 text-meow-amber fill-meow-amber" />{p.rating_count ? Number(p.rating_avg || 0).toFixed(1) : "Belum ada rating"} ({p.rating_count || 0}{" ulasan)"}</span>
            <span>•</span>
            <span>{"Terjual "}{p.sold_count || 0}</span>
          </div>

          <div className="bg-white rounded-3xl p-5 border border-meow-midnight/5" data-testid="pd-price-card">
            {hasFlash && <p className="text-xs font-bold uppercase tracking-wider text-meow-salmon mb-1">{"⚡ Flash Sale"}</p>}
            <div className="flex items-baseline gap-3">
              <p className="font-heading font-black text-3xl text-meow-salmon" data-testid="pd-price"><span className="conveythis-no-translate notranslate" translate="no" data-conveythis-private="">{formatIDR(price)}</span></p>
              {(hasDiscount || hasFlash) &&
              <p className="text-meow-gray line-through text-base"><span className="conveythis-no-translate notranslate" translate="no" data-conveythis-private="">{formatIDR(p.price)}</span></p>
              }
            </div>
            {data.flash_item && <p className="text-xs text-meow-gray mt-2">{"Kuota promo tersedia: "}{flashAvailable}. {qty > flashAvailable ? "Jumlah pilihan melebihi kuota promo; harga reguler berlaku." : "Harga dan kuota diperiksa kembali saat checkout."}</p>}
          </div>

          {p.variants?.length > 0 &&
          <div>
              <p className="text-sm font-bold mb-2">{"Pilih Varian:"}</p>
              <div className="flex flex-wrap gap-2" data-testid="variant-list">
                {p.variants.map((v) =>
              <button key={v.id} disabled={adding||opticalBusy||Boolean(purchaseIntent)} onClick={() => {setSelectedVariant(v);setQty((current) => Math.max(1, Math.min(current, Number(v.stock || 0) - Number(v.reserved || 0))));}}
              className={`px-4 py-2 rounded-full border-2 text-sm font-semibold ${selectedVariant?.id === v.id ? "border-meow-salmon bg-meow-salmon/10 text-meow-salmon" : "border-meow-midnight/10 hover:border-meow-midnight"}`}
              data-testid={`variant-${v.sku}`}>
                    {v.color_hex && <span className="inline-block h-3 w-3 rounded-full mr-2 align-middle" style={{ background: v.color_hex }} />}
                    {[v?.["color"], v?.["size"], v?.["lens_type"]].filter(Boolean).join(" · ")}
                  </button>
              )}
              </div>
            </div>
          }

          <div className="flex items-center gap-4">
            <p className="text-sm font-bold">{"Jumlah:"}</p>
            <div className="flex items-center bg-meow-bg rounded-full">
              <button disabled={adding||opticalBusy||Boolean(purchaseIntent)} onClick={() => setQty(Math.max(1, qty - 1))} className="px-3 py-1.5 font-bold" data-testid="qty-minus">-</button>
              <span className="px-3 py-1.5 font-bold" data-testid="qty-display">{qty}</span>
              <button disabled={qty >= stock||adding||opticalBusy||Boolean(purchaseIntent)} onClick={() => setQty(Math.min(stock, qty + 1))} className="px-3 py-1.5 font-bold" data-testid="qty-plus">+</button>
            </div>
            <p className="text-xs text-meow-gray">{"Stok: "}{stock}</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button onClick={() => beginPurchase('cart')} disabled={adding || opticalBusy || incompleteLens || stock <= 0} className="btn-secondary disabled:opacity-50" data-testid="add-to-cart-btn">{editCartId?"Perbarui Pilihan":"+ Tambah ke Cart"}</button>
            <button onClick={() => beginPurchase('buy')} disabled={adding || opticalBusy || incompleteLens || stock <= 0} className="btn-primary disabled:opacity-50" data-testid="buy-now-btn">{"Beli Sekarang"}</button>
          </div>
          {opticalEligible && <ProductOpticalOptions key={`${p.id}:${editCartId}`} product={p} quantity={qty} value={optical} onChange={setOptical} disabled={adding||Boolean(purchaseIntent)} onBusyChange={setOpticalBusy}/>}
          {editItem?.lens_product&&!optical.replace_lens_product&&<p className="text-xs text-meow-gray">Lensa lama: {editItem.lens_product.name}. <button type="button" disabled={adding||opticalBusy} className="underline" onClick={()=>setOptical({...optical,lens_type:'',lens_index_id:'',replace_lens_product:true})}>Hapus lensa lama / beli frame saja</button></p>}
          <div className="flex gap-2 text-xs">
            <button onClick={toggleWishlist} className="flex items-center gap-1 text-meow-gray hover:text-meow-salmon" data-testid="add-wishlist-btn">
              <Heart className="h-4 w-4" />{" Wishlist"}
            </button>
            <button onClick={subscribeProduct} className="flex items-center gap-1 text-meow-gray hover:text-meow-salmon" data-testid="subscribe-btn">
              <BellRing className="h-4 w-4" />{" Notify saya"}
            </button>
          </div>

          <div className="bg-white rounded-3xl p-5 grid grid-cols-3 gap-3 text-center text-xs" data-testid="pd-perks">
            <div><Truck className="h-5 w-5 mx-auto text-meow-mint" /><p className="mt-1 font-bold">{"Cek Ongkir Realtime"}</p></div>
            <div><ShieldCheck className="h-5 w-5 mx-auto text-meow-amber" /><p className="mt-1 font-bold">{"Garansi 12 Bulan"}</p></div>
            <div><Sparkles className="h-5 w-5 mx-auto text-meow-salmon" /><p className="mt-1 font-bold">{"Dapat Poin"}</p></div>
          </div>
        </div>
      </div>

      {/* Description */}
      <section className="mt-10 grid lg:grid-cols-3 gap-6" data-testid="pd-desc-section">
        <div className="lg:col-span-2 bg-white rounded-3xl p-6">
          <h3 className="font-heading text-2xl font-extrabold mb-3">{"Tentang Produk"}</h3>
          <HtmlContent html={p?.["description"]} className="text-meow-gray leading-relaxed" data-testid="product-description" />
        </div>
        <div className="bg-white rounded-3xl p-6">
          <h3 className="font-heading text-xl font-extrabold mb-3">{"Spesifikasi"}</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-meow-gray">{"SKU"}</dt><dd className="font-bold"><span className="conveythis-no-translate notranslate" translate="no" data-conveythis-private="">{p.sku}</span></dd></div>
            <div className="flex justify-between"><dt className="text-meow-gray">{"Berat"}</dt><dd className="font-bold">{p.weight_gram}{"g"}</dd></div>
            {p.dimension && <div className="flex justify-between"><dt className="text-meow-gray">{"Dimensi"}</dt><dd className="font-bold">{p.dimension}</dd></div>}
            {Object.entries(p.spec || {}).map(([k, v]) =>
            <div key={k} className="flex justify-between gap-2">
                <dt className="text-meow-gray">{k}</dt><dd className="font-bold text-right">{String(v)}</dd>
              </div>
            )}
          </dl>
        </div>
      </section>

      {/* Reviews */}
      {data.reviews?.length > 0 &&
      <section className="mt-10" data-testid="pd-reviews-section">
          <h3 className="font-heading text-2xl font-extrabold mb-4">{"Ulasan Pembeli"}</h3>
          <div className="grid md:grid-cols-2 gap-4">
            {data.reviews.map((r) =>
          <div key={r.id} className="bg-white rounded-3xl p-5">
                <div className="flex items-center justify-between">
                  <p className="font-bold"><span className="conveythis-no-translate notranslate" translate="no" data-conveythis-private="">{r.user_name}</span></p>
                  <div className="flex">
                    {[...Array(5)].map((_, i) =>
                <Star key={i} className={`h-4 w-4 ${i < r.rating ? "text-meow-amber fill-meow-amber" : "text-meow-midnight/10"}`} />
                )}
                  </div>
                </div>
                <p className="text-sm text-meow-gray mt-2 leading-relaxed">{r.body}</p>
              </div>
          )}
          </div>
        </section>
      }

      {/* Related */}
      {purchaseIntent && <AddonChooser quantity={qty} busy={adding} onConfirm={confirmAddons} onClose={() => setPurchaseIntent(null)} />}
      {data.related?.length > 0 &&
      <section className="mt-12" data-testid="pd-related-section">
          <h3 className="font-heading text-2xl font-extrabold mb-4">{"Produk Terkait"}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {data.related.slice(0, 4).map((r) => <ProductCard key={r.id} product={r} />)}
          </div>
        </section>
      }
    </div>);

};

export default ProductDetailPage;
