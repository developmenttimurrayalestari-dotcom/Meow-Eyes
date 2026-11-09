import HtmlContent from "../components/HtmlContent";
import ShareButtons from "../components/ShareButtons";
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, apiError, imageSrc } from "../lib/api";
import { Calendar, Eye, ArrowLeft, Cat } from "lucide-react";

const ArticleDetailPage = () => {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError("");
    api.get(`/articles/${slug}`, { signal: controller.signal }).then(({ data }) => setData(data)).catch((err) => { if (!controller.signal.aborted) setError(apiError(err, "Artikel tidak tersedia.")); });
    return () => controller.abort();
  }, [slug]);
  if (error) return <div className="max-w-xl mx-auto p-8 text-center" role="alert"><p>{error}</p><Link to="/articles" className="btn-secondary inline-block mt-4">Lihat Artikel Lain</Link></div>;
  if (!data) return <div className="min-h-[40vh] flex items-center justify-center"><Cat className="h-10 w-10 text-meow-salmon animate-pulse" /></div>;
  const a = data.article;
  return (
    <div className="max-w-4xl mx-auto px-4 md:px-6 py-8" data-testid="article-detail-page">
      <Link to="/articles" className="inline-flex items-center gap-1 text-meow-salmon font-bold text-sm"><ArrowLeft className="h-4 w-4" /> Kembali</Link>
      {a.thumbnail && (
        <div className="mt-4 aspect-video overflow-hidden rounded-[32px] bg-meow-bg">
          <img src={imageSrc(a.thumbnail)} alt={a.title} className="w-full h-full object-cover" />
        </div>
      )}
      <h1 className="font-heading text-3xl md:text-5xl font-black mt-6" data-testid="article-title">{a.title}</h1>
      <div className="flex items-center gap-3 mt-3 text-sm text-meow-gray">
        <span className="flex items-center gap-1"><Calendar className="h-4 w-4" /> {(a.published_at || "").slice(0, 10)}</span>
        <span>· {a.author_name}</span>
        <span className="flex items-center gap-1"><Eye className="h-4 w-4" /> {a.view_count}</span>
      </div>
      <ShareButtons title={a.title} path={`/articles/${a.slug || slug}`} className="mt-5" />
      <HtmlContent className="prose max-w-none mt-6 text-meow-midnight leading-relaxed" data-testid="article-content" html={a.content} />
      {data.related?.length > 0 && (
        <section className="mt-12">
          <h3 className="font-heading text-2xl font-extrabold mb-4">Artikel Terkait</h3>
          <div className="grid md:grid-cols-2 gap-4">
            {data.related.map((r) => (
              <Link key={r.id} to={`/articles/${r.slug}`} className="bg-white rounded-3xl p-4 flex gap-3 hover:shadow-meow-soft" data-testid={`related-${r.slug}`}>
                {r.thumbnail && <img src={imageSrc(r.thumbnail)} alt="" className="w-24 h-24 rounded-2xl object-cover" />}
                <div>
                  <p className="font-bold line-clamp-2">{r.title}</p>
                  <p className="text-xs text-meow-gray mt-1 line-clamp-2">{r.excerpt}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default ArticleDetailPage;
