import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, apiError, imageSrc } from "../lib/api";
import ProductCard from "../components/ProductCard";
import { Sparkles, Cat, Zap, Gift, Mail, ChevronRight, ChevronLeft, Glasses, Layers, Package2, Pause, Play } from "lucide-react";
import { toast } from "sonner";

const Section = ({ title, subtitle, action, children, testid }) => (
  <section className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 my-12" data-testid={testid}>
    <div className="flex items-end justify-between mb-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] text-meow-salmon font-bold">{subtitle}</p>
        <h2 className="font-heading text-2xl md:text-3xl lg:text-4xl font-extrabold mt-1">{title}</h2>
      </div>
      {action}
    </div>
    {children}
  </section>
);

const FlashCountdown = ({ endIso }) => {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const remaining = Math.max(0, new Date(endIso).getTime() - now);
  const h = Math.floor(remaining / 3600000);
  const m = Math.floor((remaining % 3600000) / 60000);
  const s = Math.floor((remaining % 60000) / 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return (
    <div className="flex gap-2 items-center font-mono" data-testid="flash-countdown">
      {[h, m, s].map((v, i) => (
        <React.Fragment key={i}>
          <span className="bg-meow-midnight text-white px-2.5 py-1 rounded-lg font-bold tabular-nums">{pad(v)}</span>
          {i < 2 && <span className="text-meow-midnight font-bold">:</span>}
        </React.Fragment>
      ))}
    </div>
  );
};

// Default slide (the original marketing copy) rendered as the first slide.
const DefaultHeroSlide = () => (
  <div className="absolute inset-0 rounded-[36px] bg-gradient-to-br from-meow-amber/40 via-meow-bg to-meow-salmon/30 p-8 md:p-12 flex flex-col justify-center">
    <div className="absolute -top-10 -right-10 w-72 h-72 rounded-full bg-meow-salmon/30 blur-3xl pointer-events-none" />
    <p className="text-xs uppercase tracking-[0.3em] text-meow-salmon font-bold">Marketplace Kacamata #1 Indonesia</p>
    <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-black mt-3 tracking-tighter leading-[1.05]">
      Lihat dunia <br className="hidden md:block" />
      dengan <span className="text-meow-salmon">tatapan meow</span>.
    </h1>
    <p className="mt-4 max-w-md text-meow-gray leading-relaxed">
      Ratusan frame Leinz, Cat Eye, Round, Square hingga lensa anti radiasi.
      Spin roulette dapat voucher, main mini games dapat poin — semua di Meow Eyes.
    </p>
    <div className="flex flex-wrap gap-3 mt-6">
      <Link to="/products" className="btn-primary inline-flex items-center gap-2" data-testid="hero-shop-btn">
        <Sparkles className="h-4 w-4" /> Belanja Sekarang
      </Link>
      <Link to="/roulette" className="btn-secondary inline-flex items-center gap-2" data-testid="hero-roulette-btn">
        🎯 Spin Roulette
      </Link>
    </div>
  </div>
);

// One banner slide — full-bleed image with a title/CTA overlay.
const HeroCta = () => (
  <span className="btn-primary inline-flex items-center gap-2">
    <Sparkles className="h-4 w-4" /> Lihat Selengkapnya
  </span>
);

const bannerDestination = (value) => {
  if (!value || typeof value !== "string") return null;
  if (value.startsWith("/") && !value.startsWith("//") && !value.includes("\\")) return { path: value, external: false };
  try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) && !url.username && !url.password ? { path: url.href, external: true } : null; } catch { return null; }
};
const BannerSlide = ({ banner }) => {
  const img = banner.image_desktop || banner.image_mobile || banner.image;
  const destination = bannerDestination(banner.link_url || banner.destination_url);
  const Wrapper = destination ? destination.external ? "a" : Link : "div";
  const props = destination ? destination.external ? { href: destination.path, target: "_blank", rel: "noopener noreferrer" } : { to: destination.path } : {};
  return <Wrapper {...props} className="absolute inset-0 rounded-[36px] overflow-hidden group" data-testid={`hero-banner-${banner.id}`} aria-label={destination ? banner.alt_text || banner.title : undefined}>
    {img && <picture>{banner.image_mobile && <source media="(max-width: 767px)" srcSet={imageSrc(banner.image_mobile)} />}<img src={imageSrc(img)} alt={banner.alt_text || banner.title || "Banner toko"} className="absolute inset-0 w-full h-full object-cover" loading="lazy" /></picture>}
    <div className="absolute inset-0 bg-gradient-to-tr from-meow-midnight/70 via-meow-midnight/30 to-transparent" />
    <div className="relative h-full flex flex-col justify-end p-8 md:p-12 text-white">
      <p className="text-xs uppercase tracking-[0.3em] text-meow-amber font-bold">Promo Spesial</p>
      <h2 className="font-heading text-3xl sm:text-4xl lg:text-5xl font-black mt-3 tracking-tighter leading-[1.05] max-w-2xl">{banner.title}</h2>
      {destination && <div className="mt-6" data-testid={`hero-banner-cta-${banner.id}`}><HeroCta /></div>}
    </div>
  </Wrapper>;
};

const HeroSlider = ({ banners }) => {
  const slides = banners.length ? banners.map((banner) => ({ type: "banner", id: banner.id, banner })) : [{ type: "default", id: "default" }];
  const [idx, setIdx] = useState(0);
  const pausedRef = useRef(false);
  const [autoPlay, setAutoPlay] = useState(!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
  const totalSlides = slides.length;

  useEffect(() => {
    if (totalSlides <= 1 || !autoPlay) return;
    const t = setInterval(() => {
      if (!pausedRef.current) setIdx((i) => (i + 1) % totalSlides);
    }, 6000);
    return () => clearInterval(t);
  }, [totalSlides, autoPlay]);
  useEffect(() => { setIdx(0); }, [totalSlides]);

  const goto = (i) => setIdx((i + totalSlides) % totalSlides);

  return (
    <div
      className="relative rounded-[36px] overflow-hidden w-full h-[380px] md:h-[480px] lg:h-[520px]"
      onMouseEnter={() => { pausedRef.current = true; }}
      onMouseLeave={() => { pausedRef.current = false; }}
      onFocusCapture={() => { pausedRef.current = true; }}
      onBlurCapture={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) pausedRef.current = false; }}
      role="region" aria-label="Banner promosi" aria-roledescription="carousel"
      data-testid="hero-slider"
    >
      {slides.map((s, i) => (
        <div
          key={s.id}
          className={`absolute inset-0 transition-opacity duration-700 ease-out ${i === idx ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"}`}
          aria-hidden={i !== idx} inert={i !== idx}
        >
          {s.type === "default" ? <DefaultHeroSlide /> : <BannerSlide banner={s.banner} />}
        </div>
      ))}

      {totalSlides > 1 && (
        <>
          {/* Prev/Next controls */}
          <button
            type="button"
            onClick={() => goto(idx - 1)}
            className="absolute left-3 top-1/2 -translate-y-1/2 z-20 h-9 w-9 rounded-full bg-white/80 hover:bg-white text-meow-midnight backdrop-blur-sm flex items-center justify-center shadow-md transition"
            aria-label="Slide sebelumnya"
            data-testid="hero-prev"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <button
            type="button"
            onClick={() => goto(idx + 1)}
            className="absolute right-3 top-1/2 -translate-y-1/2 z-20 h-9 w-9 rounded-full bg-white/80 hover:bg-white text-meow-midnight backdrop-blur-sm flex items-center justify-center shadow-md transition"
            aria-label="Slide berikutnya"
            data-testid="hero-next"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
          <button type="button" onClick={() => setAutoPlay((value) => !value)} aria-label={autoPlay ? "Jeda pergantian banner" : "Putar banner otomatis"} className="absolute bottom-4 right-4 z-20 bg-white/90 rounded-full p-2">{autoPlay ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}</button>
          {/* Dots */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex gap-2">
            {slides.map((_, i) => (
              <button
                key={i}
                type="button"
                onClick={() => goto(i)}
                className={`h-2 rounded-full transition-all ${i === idx ? "w-8 bg-meow-salmon" : "w-2 bg-white/70 hover:bg-white"}`}
                aria-label={`Ke slide ${i + 1}`}
                data-testid={`hero-dot-${i}`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
};

const HomePage = () => {
  const [data, setData] = useState(null);
  const [flashSales, setFlashSales] = useState([]);
  const [heroBanners, setHeroBanners] = useState([]);
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    setError("");
    (async () => {
      const [hp, fs, bn] = await Promise.all([
        api.get("/homepage"),
        api.get("/flash-sales/active").catch(() => ({ data: { flash_sales: [] } })),
        api.get("/banners?position=hero").catch(() => ({ data: { banners: [] } })),
      ]);
      setData(hp.data);
      setFlashSales(fs.data.flash_sales || []);
      // Sort banners by sort_order asc for a stable slide sequence
      const banners = (bn.data.banners || [])
        .slice()
        .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));
      setHeroBanners(banners);
    })().catch((err) => setError(apiError(err, "Halaman toko belum dapat dimuat.")));
  }, [reload]);

  const handleNewsletter = async (e) => {
    e.preventDefault();
    try {
      await api.post("/newsletter/subscribe", { email });
      toast.success("Berhasil berlangganan newsletter!");
      setEmail("");
    } catch {
      toast.error("Email tidak valid");
    }
  };

  if (error) return <div role="alert" className="max-w-xl mx-auto py-16 px-4 text-center"><p>{error}</p><button type="button" onClick={() => setReload((value) => value + 1)} className="btn-secondary mt-4">Coba lagi</button></div>;
  if (!data) {
    return <div className="min-h-screen flex items-center justify-center"><Cat className="h-10 w-10 text-meow-salmon animate-pulse" /></div>;
  }

  return (
    <div data-testid="home-page">
      {/* Hero */}
      <section className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 pt-8 md:pt-12" data-testid="hero-section">
        {heroBanners.length > 0 && <h1 className="sr-only">Meow Eyes · Koleksi Kacamata dan Lensa</h1>}
        <HeroSlider banners={heroBanners} />
      </section>

      {/* Category tiles */}
      <Section title="Kategori Pilihan" subtitle="Jenis Produk" testid="category-tiles-section">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
          {[
            { slug: "frame", title: "Frame", desc: "Stylish & premium", icon: Glasses, bg: "bg-meow-salmon/15", color: "text-meow-salmon" },
            { slug: "lensa", title: "Lensa", desc: "Blue Cut, Photochromic", icon: Layers, bg: "bg-meow-amber/15", color: "text-meow-amber" },
            { slug: "paket-frame-lensa", title: "Paket Hemat", desc: "Frame + Lensa", icon: Package2, bg: "bg-meow-mint/15", color: "text-meow-mint" },
            { slug: "leinz", title: "Leinz Series", desc: "Best of 2026", icon: Sparkles, bg: "bg-meow-midnight/10", color: "text-meow-midnight" },
          ].map((c) => (
            <Link key={c.slug} to={`/category/${c.slug}`} className={`${c.bg} meow-card p-6 hover:scale-[1.02] transition`} data-testid={`category-tile-${c.slug}`}>
              <c.icon className={`h-8 w-8 ${c.color}`} />
              <p className="font-heading font-extrabold text-xl mt-3">{c.title}</p>
              <p className="text-xs text-meow-gray mt-1">{c.desc}</p>
            </Link>
          ))}
        </div>
      </Section>

      {/* Flash sale products */}
      {flashSales.length > 0 && flashSales[0].items?.length > 0 && (
        <Section title={flashSales[0].name} subtitle="⚡ Flash Sale berakhir segera" testid="flash-sale-section"
          action={<Link to="/flash-sale" className="text-meow-salmon font-bold text-sm" data-testid="see-all-flash">Lihat Semua →</Link>}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {flashSales[0].items.slice(0, 4).map((p) => <ProductCard key={p.id} product={p} />)}
          </div>
        </Section>
      )}

      {/* Best seller */}
      <Section title="Paling Sering Dipesan" subtitle="Best Seller" testid="bestseller-section"
        action={<Link to="/products?sort=bestseller" className="text-meow-salmon font-bold text-sm" data-testid="see-all-bestseller">Lihat Semua →</Link>}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {data.bestsellers.slice(0, 8).map((p) => <ProductCard key={p.id} product={p} />)}
        </div>
      </Section>

      {/* Newest */}
      <Section title="Koleksi Terbaru" subtitle="Baru Tiba" testid="newest-section"
        action={<Link to="/new-arrival" className="text-meow-salmon font-bold text-sm">Lihat Semua →</Link>}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {data.newest.slice(0, 8).map((p) => <ProductCard key={p.id} product={p} />)}
        </div>
      </Section>

      {/* Newsletter */}
      <section className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 my-16" data-testid="newsletter-section">
        <div className="rounded-[36px] bg-meow-midnight text-white p-8 md:p-14 grid md:grid-cols-2 gap-8 items-center">
          <div>
            <Mail className="h-10 w-10 text-meow-amber" />
            <h3 className="font-heading text-3xl md:text-4xl font-black mt-3">Jadilah yang pertama tahu</h3>
            <p className="mt-2 text-white/70">Promo eksklusif, peluncuran koleksi baru, flash sale, dan reward roulette — langsung ke inbox kamu.</p>
          </div>
          <form onSubmit={handleNewsletter} className="flex flex-col sm:flex-row gap-3" data-testid="newsletter-form">
            <input
              data-testid="newsletter-email"
              type="email" required
              value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="email@kamu.com"
              className="flex-1 rounded-full bg-white text-meow-midnight px-5 py-4 outline-none font-medium"
            />
            <button type="submit" className="btn-primary" data-testid="newsletter-submit">Subscribe</button>
          </form>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
