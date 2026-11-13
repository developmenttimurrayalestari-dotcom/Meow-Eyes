import React, { useEffect, useState } from "react";
import { useSearchParams, useParams, useLocation, Link } from "react-router-dom";
import { api, apiError } from "../lib/api";
import MasterCatalogFilters from "../components/MasterCatalogFilters";
import ProductCard from "../components/ProductCard";
import { Filter, X, ChevronRight } from "lucide-react";
import CatalogPagination, { catalogPage, PAGE_SIZE } from "../components/CatalogPagination";

const SORTS = [
  { value: "newest", label: "Terbaru" },
  { value: "bestseller", label: "Terlaris" },
  { value: "price_asc", label: "Harga Terendah" },
  { value: "price_desc", label: "Harga Tertinggi" },
  { value: "rating", label: "Rating Terbaik" },
  { value: "discount", label: "Diskon Terbesar" },
];
const FilterPanel = ({ params, setParam, brands, categories, setMasterFilter }) => (
  <div className="space-y-6 text-sm">
    <MasterCatalogFilters categories={categories} params={params} onChange={setMasterFilter} />
    <div>
      <p className="font-bold mb-2 text-xs uppercase tracking-wider text-meow-salmon">Brand</p>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {brands.map((b) => (
          <label key={b.id} className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio" name="brand_id" value={b.id}
              checked={params.brand_id === b.id}
              onChange={(e) => setParam("brand_id", e.target.value)}
              data-testid={`filter-brand-${b.slug}`}
            />
            {b.name}
          </label>
        ))}
        {params.brand_id && (
          <button onClick={() => setParam("brand_id", null)} className="text-xs underline">Hapus brand</button>
        )}
      </div>
    </div>
    <div>
      <p className="font-bold mb-2 text-xs uppercase tracking-wider text-meow-salmon">Rentang Harga</p>
      <div className="grid grid-cols-2 gap-2">
        <input data-testid="filter-min-price" type="number" placeholder="Min" value={params.min_price || ""}
          onChange={(e) => setParam("min_price", e.target.value || null)}
          className="px-3 py-2 rounded-xl bg-meow-bg border-2 border-transparent focus:border-meow-salmon focus:bg-white outline-none" />
        <input data-testid="filter-max-price" type="number" placeholder="Max" value={params.max_price || ""}
          onChange={(e) => setParam("max_price", e.target.value || null)}
          className="px-3 py-2 rounded-xl bg-meow-bg border-2 border-transparent focus:border-meow-salmon focus:bg-white outline-none" />
      </div>
    </div>
  </div>
);

const ProductsPage = ({ title, intro, badge: fixedBadge, children }) => {
  const location = useLocation();
  const isNewArrival = location.pathname === "/new-arrival";
  const [search, setSearch] = useSearchParams();
  const { slug } = useParams();
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [brands, setBrands] = useState([]);
  const [masterCategories, setMasterCategories] = useState([]);
  const [masterError, setMasterError] = useState("");
  const [category, setCategory] = useState(null);
  const [breadcrumb, setBreadcrumb] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const [showMobileFilter, setShowMobileFilter] = useState(false);

  const params = Object.fromEntries(search.entries());
  const page = catalogPage(params.page);
  const queryKey = search.toString();

  const setParam = (key, value) => {
    const next = new URLSearchParams(search);
    if (value === null || value === "" || value === undefined) next.delete(key);
    else next.set(key, value);
    next.set("page", "1");
    setSearch(next);
  };

  const setMasterFilter = ids => {
    const next = new URLSearchParams(search);
    next.delete('product_type'); next.delete('segment');
    if (ids.length) next.set('category_ids', ids.join(',')); else next.delete('category_ids');
    next.set('page', '1'); setSearch(next);
  };
  useEffect(() => {
    const controller = new AbortController(); setMasterError('');
    api.get('/categories', { signal: controller.signal }).then(({ data }) => setMasterCategories(data.categories || []))
      .catch(e => { if (!controller.signal.aborted) setMasterError(apiError(e, 'Filter master belum dapat dimuat.')); });
    return () => controller.abort();
  }, [reload]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const q = Object.fromEntries(new URLSearchParams(queryKey));
    q.limit = PAGE_SIZE;
    q.page = page;
    if (slug) q.category_slug = slug;
    if (isNewArrival) q.new_arrival = true;
    if (fixedBadge) q.badge = fixedBadge;
    api.get("/products", { params: q, signal: controller.signal }).then(({ data }) => {
      setProducts(data.products || []);
      setTotal(data.total || 0);
      const lastPage = Math.max(1, Math.ceil((data.total || 0) / PAGE_SIZE));
      if (page > lastPage) {
        const next = new URLSearchParams(queryKey);
        next.set("page", String(lastPage));
        setSearch(next, { replace: true });
      }
    }).catch((err) => {
      if (!controller.signal.aborted) { setProducts([]); setError(apiError(err, "Produk belum dapat dimuat.")); }
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [queryKey, slug, isNewArrival, fixedBadge, page, setSearch, reload]);

  useEffect(() => {
    api.get("/brands").then(({ data }) => setBrands(data.brands || [])).catch(() => {});
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setCategory(null); setBreadcrumb([]);
    if (slug) {
      api.get(`/categories/${slug}`, { signal: controller.signal }).then(({ data }) => {
        setCategory(data.category); setBreadcrumb(data.breadcrumb || []);
      }).catch(() => {});
    }
    return () => controller.abort();
  }, [slug]);
  const flashListing = fixedBadge === "flashsale" || params.badge === "flashsale";
  useEffect(() => {
    if (!flashListing) return;
    const refresh = () => { if (!document.hidden) setReload((value) => value + 1); };
    const timer = window.setInterval(refresh, 60000);
    window.addEventListener("focus", refresh);
    return () => { clearInterval(timer); window.removeEventListener("focus", refresh); };
  }, [flashListing]);

  const goToPage = (nextPage) => {
    const next = new URLSearchParams(search);
    next.set("page", String(nextPage));
    setSearch(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 py-8" data-testid="products-page">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-sm text-meow-gray mb-4" data-testid="breadcrumb">
        <Link to="/" className="hover:text-meow-salmon">Home</Link>
        {breadcrumb.map((b, i) => (
          <React.Fragment key={b.id}>
            <ChevronRight className="h-3 w-3" />
            <Link to={`/category/${b.slug}`} className={i === breadcrumb.length - 1 ? "text-meow-midnight font-semibold" : "hover:text-meow-salmon"}>
              {b.name}
            </Link>
          </React.Fragment>
        ))}
        {!slug && params.q && (
          <>
            <ChevronRight className="h-3 w-3" />
            <span className="text-meow-midnight font-semibold">Cari: {params.q}</span>
          </>
        )}
      </nav>

      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6">
        <div>
          <h1 className="font-heading text-3xl md:text-4xl font-black" data-testid="products-title">
            {title || (isNewArrival ? "New Arrival" : category ? category.name : params.q ? `Hasil: "${params.q}"` : location.pathname.startsWith("/shop-now") ? "Shop Now" : "Semua Produk")}
          </h1>
          <p className="text-meow-gray text-sm mt-1" aria-live="polite">{loading ? "Memuat produk…" : `${total} produk ditemukan`}</p>
          {(intro || isNewArrival) && <p className="text-sm text-meow-gray mt-2 max-w-xl">{intro || "Temukan koleksi terbaru yang dipilih untuk Anda."}</p>}
          {isNewArrival && <Link to="/new-arrival?product_type=frame" className="inline-block mt-3 text-sm font-bold text-meow-salmon underline">New Arrival · Frame →</Link>}
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowMobileFilter(true)} className="md:hidden flex items-center gap-2 px-4 py-2 bg-meow-midnight text-white rounded-full text-sm" data-testid="open-filter-mobile">
            <Filter className="h-4 w-4" /> Filter
          </button>
          <select
            data-testid="sort-select"
            value={params.sort || "newest"}
            onChange={(e) => setParam("sort", e.target.value)}
            className="px-4 py-2 rounded-full bg-white border-2 border-meow-midnight/10 text-sm font-semibold"
          >
            {SORTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>
      </div>

      {masterError && <p role="alert" className="bg-amber-50 p-3 rounded-xl my-3 text-sm">{masterError} <button className="underline" onClick={() => setReload(value => value + 1)}>Muat ulang filter</button></p>}
      {children}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Sidebar */}
        <aside className="hidden md:block md:col-span-3 bg-white rounded-3xl p-6 self-start sticky top-40" data-testid="filter-sidebar">
          <FilterPanel params={params} setParam={setParam} brands={brands} categories={masterCategories} setMasterFilter={setMasterFilter} />
        </aside>

        {/* Mobile drawer */}
        {showMobileFilter && (
          <div className="md:hidden fixed inset-0 bg-black/50 z-[70]" onClick={() => setShowMobileFilter(false)}>
            <div className="absolute right-0 top-0 bottom-0 w-80 bg-white p-6 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-center mb-6">
                <p className="font-heading font-black text-xl">Filter</p>
                <button onClick={() => setShowMobileFilter(false)} data-testid="close-filter-mobile"><X className="h-5 w-5" /></button>
              </div>
              <FilterPanel params={params} setParam={setParam} brands={brands} categories={masterCategories} setMasterFilter={setMasterFilter} />
            </div>
          </div>
        )}

        {/* Product grid */}
        <div className="md:col-span-9">
          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="aspect-square bg-meow-midnight/5 rounded-3xl animate-pulse" />
              ))}
            </div>
          ) : error ? (
            <div role="alert" className="text-center p-8 bg-white rounded-3xl"><p>{error}</p><button type="button" className="btn-secondary mt-3" onClick={() => setReload((value) => value + 1)}>Coba lagi</button></div>
          ) : products.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-3xl">
              <p className="font-heading font-black text-2xl">Tidak ada produk ditemukan</p>
              <p className="text-meow-gray mt-2">Coba ubah filter atau kata kunci pencarian.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4" data-testid="products-grid">
              {products.map((p) => <ProductCard key={p.id} product={p} />)}
            </div>
          )}
          {!error && <CatalogPagination page={page} total={total} onChange={goToPage} disabled={loading} />}
        </div>
      </div>
    </div>
  );
};

export default ProductsPage;
