import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, apiError, imageSrc } from "../lib/api";
import { BookOpen, Calendar, Search } from "lucide-react";

const ArticleListPage = () => {
  const [articles, setArticles] = useState([]);
  const [cats, setCats] = useState([]);
  const [q, setQ] = useState("");
  const [catSlug, setCatSlug] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError("");
    const params = {};
    if (q) params.q = q;
    if (catSlug) params.category_slug = catSlug;
    api.get("/articles", { params, signal: controller.signal }).then(({ data }) => setArticles(data.articles || [])).catch((err) => { if (!controller.signal.aborted) setError(apiError(err)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [q, catSlug]);
  useEffect(() => {
    api.get("/articles/categories").then(({ data }) => setCats(data.categories)).catch(() => {});
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-6 py-8" data-testid="articles-page">
      <div className="text-center mb-8">
        <BookOpen className="h-10 w-10 mx-auto text-meow-salmon" />
        <h1 className="font-heading text-4xl md:text-5xl font-black mt-2">Article & News</h1>
        <p className="text-meow-gray mt-2">Tips, panduan, dan cerita seputar dunia kacamata.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-3 mb-6">
        <div className="flex-1 flex items-center bg-white border-2 border-transparent focus-within:border-meow-salmon rounded-full px-5 py-2.5">
          <Search className="h-4 w-4 text-meow-gray mr-2" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari artikel..." className="flex-1 outline-none bg-transparent text-sm" data-testid="article-search" />
        </div>
        <select value={catSlug} onChange={(e) => setCatSlug(e.target.value)} className="px-4 py-2 rounded-full bg-white border-2 border-meow-midnight/10 text-sm font-semibold" data-testid="article-cat-filter">
          <option value="">Semua Kategori</option>
          {cats.map((c) => <option key={c.id} value={c.slug}>{c.name}</option>)}
        </select>
      </div>

      {loading ? <p role="status" className="py-8 text-center">Memuat artikel…</p> : error ? <p role="alert" className="text-red-600 text-center py-8">{error}</p> : articles.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center text-meow-gray">Belum ada artikel.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="articles-grid">
          {articles.map((a) => (
            <Link key={a.id} to={`/articles/${a.slug}`} className="meow-card overflow-hidden block" data-testid={`article-${a.slug}`}>
              <div className="aspect-[16/10] overflow-hidden bg-meow-bg">
                {a.thumbnail && <img src={imageSrc(a.thumbnail)} alt={a.title} className="w-full h-full object-cover hover:scale-105 transition duration-500" />}
              </div>
              <div className="p-5">
                <p className="text-xs uppercase tracking-wider text-meow-salmon font-bold">{a.author_name}</p>
                <h3 className="font-heading font-extrabold text-lg mt-1 line-clamp-2">{a.title}</h3>
                <p className="text-sm text-meow-gray line-clamp-2 mt-2">{a.excerpt}</p>
                <div className="flex items-center justify-between mt-3 text-xs text-meow-gray">
                  <span className="flex items-center gap-1"><Calendar className="h-3 w-3" /> {(a.published_at || a.created_at || "").slice(0, 10)}</span>
                  <span>{a.view_count || 0}× dibaca</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default ArticleListPage;
