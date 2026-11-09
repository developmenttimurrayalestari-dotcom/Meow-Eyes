import HtmlContent from "../components/HtmlContent";
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { Cat } from "lucide-react";

// Fetches CMS page by slug (privacy, terms, refund, shipping, about) or falls back to hard-coded.
const StaticPage = ({ pageKey, slug: slugOverride }) => {
  const params = useParams();
  const slug = slugOverride || params.slug || pageKey;
  const [page, setPage] = useState(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    setPage(null); setNotFound(false);
    api.get(`/pages/${slug}`).then(({ data }) => setPage(data.page)).catch(() => setNotFound(true));
  }, [slug]);

  if (notFound) {
    return (
      <div className="max-w-3xl mx-auto py-12 text-center" data-testid="static-notfound">
        <p className="font-heading font-black text-2xl">Halaman tidak ditemukan</p>
        <Link to="/" className="text-meow-salmon underline mt-3 inline-block">← Kembali</Link>
      </div>
    );
  }
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
