import HtmlContent from "../components/HtmlContent";
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { Cat } from "lucide-react";

// Canonical CMS URLs use /pages/:slug; legacy policy aliases can resolve by type.
const StaticPage = ({ pageKey, slug: slugOverride, pageType }) => {
  const params = useParams();
  const slug = slugOverride || params.slug || pageKey;
  const [page, setPage] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(false), [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setPage(null); setNotFound(false); setError(false);
    const load = async () => {
      try {
        let response;
        try { response = await api.get(`/pages/${encodeURIComponent(slug)}`, { signal: controller.signal }); }
        catch (err) {
          if (err.response?.status !== 404 || !pageType || controller.signal.aborted) throw err;
          const { data } = await api.get('/pages', { signal: controller.signal });
          const match = data.pages?.find(item => item.page_type === pageType);
          if (!match) throw err;
          response = await api.get(`/pages/${encodeURIComponent(match.slug)}`, { signal: controller.signal });
        }
        if (!controller.signal.aborted) setPage(response.data.page);
      } catch (err) {
        if (!controller.signal.aborted) {
          if (err.response?.status === 404) setNotFound(true);
          else setError(true);
        }
      }
    };
    void load();
    return () => controller.abort();
  }, [slug, pageType, reload]);

  if (notFound) {
    return (
      <div className="max-w-3xl mx-auto py-12 text-center" data-testid="static-notfound">
        <p className="font-heading font-black text-2xl">Halaman tidak ditemukan atau belum dipublikasikan</p>
        <Link to="/" className="text-meow-salmon underline mt-3 inline-block">← Kembali</Link>
      </div>
    );
  }
  if (error) return <div className="max-w-3xl mx-auto py-12 px-4 text-center" role="alert"><p>Halaman belum dapat dimuat. Periksa koneksi dan coba lagi.</p><button type="button" onClick={() => setReload(value => value + 1)} className="btn-secondary mt-4">Coba lagi</button></div>;
  if (!page) return <div className="min-h-[40vh] flex items-center justify-center"><Cat className="h-10 w-10 text-meow-salmon animate-pulse" /></div>;

  return (
    <div className="max-w-3xl mx-auto px-4 md:px-6 py-12" data-testid={`static-${page.slug}`}>
      <h1 className="font-heading text-4xl font-black mb-6" data-testid="page-title">{page.title}</h1>
      <HtmlContent className="bg-white rounded-3xl p-6 md:p-8 prose max-w-none" html={page.content} data-testid="page-content" />
      <Link to="/" className="inline-block mt-6 text-meow-salmon font-bold">← Kembali ke Beranda</Link>
    </div>
  );
};

export default StaticPage;
