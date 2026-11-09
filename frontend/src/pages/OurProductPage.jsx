import HtmlContent from "../components/HtmlContent";
import ShareButtons from "../components/ShareButtons";
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, apiError, formatIDR, imageSrc } from "../lib/api";
import { GraduationCap, Sparkles, ChevronRight, Cat } from "lucide-react";

const TABS = [
  { key: "frame_shape", label: "Bentuk Frame" },
  { key: "material", label: "Material" },
  { key: "lens_type", label: "Jenis Lensa" },
  { key: "lens_index", label: "Index Lensa" },
  { key: "buying_guide", label: "Buying Guide" },
];

export const OurProductPage = () => {
  const [tab, setTab] = useState("frame_shape");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError("");
    api.get("/knowledge", { params: { type: tab }, signal: controller.signal }).then(({ data }) => setItems(data.items || [])).catch((err) => { if (!controller.signal.aborted) setError(apiError(err)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [tab]);
  return (
    <div className="max-w-7xl mx-auto px-4 md:px-6 py-8" data-testid="our-product-page">
      <div className="text-center mb-6">
        <GraduationCap className="h-10 w-10 mx-auto text-meow-mint" />
        <h1 className="font-heading text-4xl md:text-5xl font-black mt-2">Our Product Knowledge</h1>
        <p className="text-meow-gray mt-2">Pelajari lebih dalam tentang frame, material, dan lensa Meow Eyes.</p>
      </div>
      <div className="flex gap-2 overflow-x-auto no-scrollbar mb-6" data-testid="knowledge-tabs">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-full text-sm font-bold whitespace-nowrap ${tab === t.key ? "bg-meow-midnight text-white" : "bg-white border border-meow-midnight/10"}`}
            data-testid={`kn-tab-${t.key}`}>
            {t.label}
          </button>
        ))}
      </div>
      {loading && <p role="status" className="py-8 text-center text-meow-gray">Memuat pengetahuan produk…</p>}
      {error && <p role="alert" className="py-8 text-center text-red-600">{error}</p>}
      {!loading && !error && !items.length && <p className="py-8 text-center text-meow-gray">Belum ada konten pada kategori ini.</p>}
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${loading || error ? "hidden" : ""}`} data-testid="knowledge-grid">
        {items.map((k) => (
          <Link key={k.id} to={`/our-product/${k.slug}`} className="meow-card overflow-hidden block" data-testid={`kn-${k.slug}`}>
            <div className="aspect-video overflow-hidden bg-meow-bg">
              {k.image && <img src={imageSrc(k.image)} alt={k.title} className="w-full h-full object-cover hover:scale-105 transition duration-500" />}
            </div>
            <div className="p-5">
              <p className="font-heading font-extrabold text-lg">{k.title}</p>
              <p className="text-sm text-meow-gray mt-1 line-clamp-2">{k.description}</p>
              <div className="flex items-center gap-1 mt-3 text-sm text-meow-salmon font-bold">
                Baca detail <ChevronRight className="h-4 w-4" />
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export const OurProductDetailPage = () => {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError("");
    api.get(`/knowledge/${slug}`, { signal: controller.signal }).then(({ data }) => setData(data)).catch((err) => { if (!controller.signal.aborted) setError(apiError(err, "Konten tidak tersedia.")); });
    return () => controller.abort();
  }, [slug]);
  if (error) return <div className="max-w-xl mx-auto p-8 text-center" role="alert"><p>{error}</p><Link to="/our-product" className="btn-secondary inline-block mt-4">Lihat Product Knowledge</Link></div>;
  if (!data) return <div className="min-h-[40vh] flex items-center justify-center"><Cat className="h-10 w-10 text-meow-salmon animate-pulse" /></div>;
  const k = data.knowledge;
  return (
    <div className="max-w-5xl mx-auto px-4 md:px-6 py-8" data-testid="knowledge-detail-page">
      <Link to="/our-product" className="text-meow-salmon font-bold text-sm">← Semua Knowledge</Link>
      <h1 className="font-heading text-3xl md:text-5xl font-black mt-3" data-testid="kn-title">{k.title}</h1>
      {k.image && <div className="mt-4 aspect-[21/9] rounded-[32px] overflow-hidden"><img src={imageSrc(k.image)} alt="" className="w-full h-full object-cover" /></div>}
      <p className="mt-4 text-meow-gray text-lg">{k.description}</p>

      <ShareButtons title={k.title} path={`/our-product/${k.slug || slug}`} className="mt-5" />
      <div className="mt-6 grid md:grid-cols-3 gap-4">
        {k.face_shape_recommendation && (
          <div className="bg-white rounded-3xl p-5" data-testid="kn-face-shape">
            <p className="text-xs uppercase tracking-wider text-meow-salmon font-bold">Cocok untuk wajah</p>
            <p className="mt-2 font-bold">{k.face_shape_recommendation}</p>
          </div>
        )}
        {k.style_recommendation && (
          <div className="bg-white rounded-3xl p-5">
            <p className="text-xs uppercase tracking-wider text-meow-amber font-bold">Style</p>
            <p className="mt-2 font-bold">{k.style_recommendation}</p>
          </div>
        )}
        {(k.pros?.length > 0 || k.cons?.length > 0) && (
          <div className="bg-white rounded-3xl p-5">
            <p className="text-xs uppercase tracking-wider text-meow-mint font-bold">Kelebihan / Kekurangan</p>
            <ul className="mt-2 text-sm space-y-1">
              {k.pros?.map((p, i) => <li key={i} className="text-meow-mint">✓ {p}</li>)}
              {k.cons?.map((c, i) => <li key={i} className="text-red-500">✗ {c}</li>)}
            </ul>
          </div>
        )}
      </div>

      <HtmlContent className="mt-6 bg-white rounded-3xl p-6" html={k.content} data-testid="kn-content" />

      {data.related_products?.length > 0 && (
        <section className="mt-8">
          <h3 className="font-heading text-2xl font-extrabold mb-3">Produk Terkait</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {data.related_products.map((p) => (
              <Link key={p.id} to={`/products/${p.slug}`} className="meow-card overflow-hidden block">
                <img src={imageSrc(p.main_image)} alt="" className="w-full aspect-square object-cover" />
                <div className="p-3">
                  <p className="font-bold text-sm line-clamp-1">{p.name}</p>
                  <p className="text-meow-salmon font-bold text-sm">{formatIDR(p.discount_price || p.price)}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      <div className="mt-8 text-center">
        <Link to="/shop-now" className="btn-primary inline-flex items-center gap-2" data-testid="kn-shop-cta">
          <Sparkles className="h-4 w-4" /> Lihat Semua Produk
        </Link>
      </div>
    </div>
  );
};
