import React, { useCallback, useEffect, useState } from "react";
import { api, API_BASE } from "../../lib/api";
import { Plus, Trash2, Edit2, FileText, BookOpen, Ticket } from "lucide-react";
import { toast } from "sonner";
import ImagePicker, { resolveImageUrl } from "../../components/ImagePicker";
import RichTextEditor from "../../components/RichTextEditor";
import { hasRichContent } from "../../lib/richContent";
import { cmsPagePath } from "../../lib/cmsPages";
import PublicationButton from "./PublicationButton";
import { adminError, localDateTime, utcDateTime } from "./adminUtils";

// ---------- Admin Articles ----------
export const AdminArticles = () => {
  const [articles, setArticles] = useState([]);
  const [cats, setCats] = useState([]);
  const [editing, setEditing] = useState(null);
  const load = () => api.get("/admin/articles").then(({ data }) => setArticles(data.articles));
  useEffect(() => {
    load();
    api.get("/admin/article-categories").then(({ data }) => setCats(data.categories));
  }, []);
  const del = async (id) => { if (confirm("Hapus artikel?")) { await api.delete(`/admin/articles/${id}`); load(); } };
  const submit = async (e) => {
    e.preventDefault();
    if (!hasRichContent(editing.content)) { toast.error("Isi konten artikel terlebih dahulu."); return; }
    try {
      if (editing.id) await api.put(`/admin/articles/${editing.id}`, editing);
      else await api.post("/admin/articles", editing);
      toast.success("Tersimpan"); setEditing(null); load();
    } catch (err) { toast.error(err?.response?.data?.detail || "Gagal"); }
  };
  return (
    <div data-testid="admin-articles">
      <div className="flex justify-between mb-4">
        <h1 className="font-heading text-3xl font-black flex items-center gap-2"><FileText /> Artikel</h1>
        <button onClick={() => setEditing({ title: "", content: "", status: "published", tags: [] })} className="btn-primary text-sm" data-testid="add-article-btn">
          <Plus className="inline h-4 w-4 mr-1" /> Artikel Baru
        </button>
      </div>
      <div className="bg-white rounded-3xl border border-zinc-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-meow-bg text-xs uppercase text-meow-gray">
            <tr>
              <th className="text-left px-4 py-3">Judul</th>
              <th className="text-left px-4 py-3">Kategori</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Views</th>
              <th className="text-left px-4 py-3">Publish</th>
              <th className="text-right px-4 py-3">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {articles.map((a) => (
              <tr key={a.id} className="border-t border-zinc-100" data-testid={`article-row-${a.slug}`}>
                <td className="px-4 py-3 font-bold">{a.title}</td>
                <td className="px-4 py-3 text-xs">{cats.find(c => c.id === a.category_id)?.name || "-"}</td>
                <td className="px-4 py-3 text-xs"><span className="block mb-1">{a.status}</span><PublicationButton resource="articles" id={a.id} status={a.status} onSaved={load} /></td>
                <td className="px-4 py-3">{a.view_count}</td>
                <td className="px-4 py-3 text-xs">{(a.published_at || "").slice(0, 10)}</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={async () => { const { data } = await api.get(`/admin/articles/${a.id}`); setEditing(data.article); }} className="p-1 text-meow-amber" data-testid={`edit-article-${a.slug}`}><Edit2 className="h-4 w-4" /></button>
                  <button onClick={() => del(a.id)} className="p-1 text-red-500" data-testid={`del-article-${a.slug}`}><Trash2 className="h-4 w-4" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4 overflow-y-auto" onClick={() => setEditing(null)}>
          <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-5xl w-full min-w-0 space-y-3 max-h-[90vh] overflow-y-auto" data-testid="article-form">
            <h3 className="font-heading font-extrabold text-xl">{editing.id ? "Edit" : "Buat"} Artikel</h3>
            <input required placeholder="Judul" value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="art-title" />
            <select value={editing.category_id || ""} onChange={(e) => setEditing({ ...editing, category_id: e.target.value || null })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="art-cat">
              <option value="">-- Kategori --</option>
              {cats.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <ImagePicker
              label="Thumbnail Artikel"
              value={editing.thumbnail || ""}
              onChange={(url) => setEditing({ ...editing, thumbnail: url })}
              testId="art-thumbnail-picker"
            />
            <input placeholder="Excerpt (ringkasan)" value={editing.excerpt || ""} onChange={(e) => setEditing({ ...editing, excerpt: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <RichTextEditor key={editing.id || 'new-article'} label="Konten artikel" value={editing.content || ""} onChange={(content) => setEditing(current => ({ ...current, content }))} testId="art-content" />
            <select value={editing.status} onChange={(e) => setEditing({ ...editing, status: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none">
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="unpublished">Unpublished</option>
              <option value="archived">Archived</option>
            </select>
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setEditing(null)} className="btn-secondary flex-1">Batal</button>
              <button type="submit" className="btn-primary flex-1" data-testid="art-save">Simpan</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

// ---------- Admin Knowledge ----------
export const AdminKnowledge = () => {
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const load = () => api.get("/admin/knowledge").then(({ data }) => setItems(data.items));
  useEffect(() => { load(); }, []);
  const del = async (id) => { if (confirm("Hapus?")) { await api.delete(`/admin/knowledge/${id}`); load(); } };
  const submit = async (e) => {
    e.preventDefault();
    try {
      if (editing.id) await api.put(`/admin/knowledge/${editing.id}`, editing);
      else await api.post("/admin/knowledge", editing);
      toast.success("Tersimpan"); setEditing(null); load();
    } catch (err) { toast.error(err?.response?.data?.detail || "Gagal"); }
  };
  return (
    <div data-testid="admin-knowledge">
      <div className="flex justify-between mb-4">
        <h1 className="font-heading text-3xl font-black flex items-center gap-2"><BookOpen /> Product Knowledge</h1>
        <button onClick={() => setEditing({ knowledge_type: "frame_shape", title: "", content: "", status: "draft", is_published: false, pros: [], cons: [] })} className="btn-primary text-sm" data-testid="add-knowledge-btn">
          <Plus className="inline h-4 w-4 mr-1" /> Knowledge Baru
        </button>
      </div>
      <div className="bg-white rounded-3xl border border-zinc-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-meow-bg text-xs uppercase text-meow-gray">
            <tr>
              <th className="text-left px-4 py-3">Judul</th>
              <th className="text-left px-4 py-3">Tipe</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-right px-4 py-3">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {items.map((k) => (
              <tr key={k.id} className="border-t border-zinc-100" data-testid={`kn-row-${k.slug}`}>
                <td className="px-4 py-3 font-bold">{k.title}</td>
                <td className="px-4 py-3 text-xs">{k.knowledge_type}</td>
                <td className="px-4 py-3 text-xs"><span className="block mb-1">{k.status || (k.is_published ? "published" : "draft")}</span><PublicationButton resource="knowledge" id={k.id} status={k.status || (k.is_published ? "published" : "draft")} onSaved={load} /></td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => setEditing({ ...k })} className="p-1 text-meow-amber"><Edit2 className="h-4 w-4" /></button>
                  <button onClick={() => del(k.id)} className="p-1 text-red-500"><Trash2 className="h-4 w-4" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editing && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4 overflow-y-auto" onClick={() => setEditing(null)}>
          <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-5xl w-full min-w-0 space-y-3 max-h-[90vh] overflow-y-auto" data-testid="knowledge-form">
            <h3 className="font-heading font-extrabold text-xl">{editing.id ? "Edit" : "Buat"} Knowledge</h3>
            <select value={editing.knowledge_type} onChange={(e) => setEditing({ ...editing, knowledge_type: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none">
              <option value="frame_shape">Frame Shape</option>
              <option value="material">Material</option>
              <option value="lens_type">Lens Type</option>
              <option value="lens_index">Lens Index</option>
              <option value="buying_guide">Buying Guide</option>
            </select>
            <input required placeholder="Judul" value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <ImagePicker
              label="Gambar Ilustrasi"
              value={editing.image || ""}
              onChange={(url) => setEditing({ ...editing, image: url })}
              testId="knowledge-image-picker"
            />
            <input placeholder="Deskripsi singkat" value={editing.description || ""} onChange={(e) => setEditing({ ...editing, description: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <input placeholder="Cocok untuk wajah" value={editing.face_shape_recommendation || ""} onChange={(e) => setEditing({ ...editing, face_shape_recommendation: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <input placeholder="Style" value={editing.style_recommendation || ""} onChange={(e) => setEditing({ ...editing, style_recommendation: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <RichTextEditor key={editing.id || 'new-knowledge'} label="Konten product knowledge" value={editing.content || ""} onChange={(content) => setEditing(current => ({ ...current, content }))} testId="knowledge-content" />
            <input placeholder="Kelebihan (pisah dengan ;)" value={(editing.pros || []).join(";")} onChange={(e) => setEditing({ ...editing, pros: e.target.value.split(";").map(x => x.trim()).filter(Boolean) })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <input placeholder="Kekurangan (pisah dengan ;)" value={(editing.cons || []).join(";")} onChange={(e) => setEditing({ ...editing, cons: e.target.value.split(";").map(x => x.trim()).filter(Boolean) })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <label className="block text-sm font-bold">Status publikasi<select value={editing.status || (editing.is_published ? "published" : "draft")} onChange={(e) => setEditing({ ...editing, status: e.target.value, is_published: e.target.value === "published" })} className="w-full px-3 py-2 mt-1 rounded-xl bg-meow-bg"><option value="draft">Draft</option><option value="published">Published</option><option value="unpublished">Unpublished</option><option value="archived">Archived</option></select></label>
            <div className="flex gap-2"><button type="button" onClick={() => setEditing(null)} className="btn-secondary flex-1">Batal</button><button type="submit" className="btn-primary flex-1">Simpan</button></div>
          </form>
        </div>
      )}
    </div>
  );
};

// ---------- Admin Reviews ----------
export const AdminReviewsMod = () => {
  const [reviews, setReviews] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [tab, setTab] = useState("all");
  const load = useCallback(() => {
    const params = tab !== "all" ? { status: tab } : {};
    api.get("/admin/reviews", { params }).then(({ data }) => setReviews(data.reviews));
    api.get("/admin/reviews/analytics").then(({ data }) => setAnalytics(data));
  }, [tab]);
  useEffect(() => { load(); }, [load]);
  const moderate = async (rid, action) => {
    await api.post(`/admin/reviews/${rid}/moderate`, { action });
    toast.success("Review " + action); load();
  };
  return (
    <div data-testid="admin-reviews">
      <h1 className="font-heading text-3xl font-black mb-4">Moderasi Review</h1>
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {["total", "pending", "approved", "rejected"].map((k) => (
            <div key={k} className="bg-white rounded-2xl p-4 text-center border border-zinc-200" data-testid={`rev-stat-${k}`}>
              <p className="text-xs uppercase text-meow-gray">{k}</p>
              <p className="font-heading font-black text-2xl">{analytics[k]}</p>
            </div>
          ))}
        </div>
      )}
      <div className="flex gap-2 mb-3">
        {["all", "pending", "approved", "rejected", "hidden"].map((s) => (
          <button key={s} onClick={() => setTab(s)} className={`px-3 py-1.5 rounded-full text-xs font-bold ${tab === s ? "bg-meow-midnight text-white" : "bg-white border border-zinc-200"}`} data-testid={`rev-tab-${s}`}>
            {s}
          </button>
        ))}
      </div>
      <div className="space-y-3">
        {reviews.map((r) => (
          <div key={r.id} className="bg-white rounded-3xl p-4 border border-zinc-200" data-testid={`review-row-${r.id}`}>
            <div className="flex justify-between items-start">
              <div>
                <p className="font-bold">{r.user_name} · ⭐ {r.rating}/5</p>
                <p className="text-xs text-meow-gray">{r.product_name} · {r.created_at?.slice(0, 10)}</p>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${r.status === "approved" ? "bg-meow-mint/20 text-meow-mint" : r.status === "pending" ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-500"}`}>{r.status}</span>
            </div>
            <p className="text-sm mt-2 text-meow-gray">{r.body}</p>
            <div className="flex gap-2 mt-3">
              {r.status !== "approved" && <button onClick={() => moderate(r.id, "approve")} className="px-3 py-1 bg-meow-mint text-white rounded-full text-xs font-bold" data-testid={`approve-${r.id}`}>Approve</button>}
              {r.status !== "rejected" && <button onClick={() => moderate(r.id, "reject")} className="px-3 py-1 bg-red-500 text-white rounded-full text-xs font-bold" data-testid={`reject-${r.id}`}>Reject</button>}
              {r.status !== "hidden" && <button onClick={() => moderate(r.id, "hide")} className="px-3 py-1 bg-zinc-500 text-white rounded-full text-xs font-bold">Hide</button>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ---------- Admin Banners V2 ----------
export const AdminBannersV2 = () => {
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);
  const load = () => api.get("/admin/banners-v2").then(({ data }) => setItems([...(data.banners || [])].sort((a, b) => a.sort_order - b.sort_order || a.id.localeCompare(b.id))));
  useEffect(() => { load(); }, []);
  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing.id) await api.put(`/admin/banners-v2/${editing.id}`, editing);
      else await api.post("/admin/banners-v2", editing);
      toast.success("Banner tersimpan"); setEditing(null); await load();
    } catch (err) { toast.error(adminError(err)); }
    finally { setSaving(false); }
  };
  return (
    <div data-testid="admin-banners">
      <div className="flex justify-between mb-4">
        <h1 className="font-heading text-3xl font-black">Banner Management</h1>
        <button onClick={() => setEditing({ title: "", image_desktop: "", link_type: "internal", link_url: "/", position: "hero", target_device: "all", sort_order: 0, is_active: true })} className="btn-primary text-sm" data-testid="add-banner-btn"><Plus className="inline h-4 w-4 mr-1" /> Banner Baru</button>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        {items.map((b) => (
          <div key={b.id} className="bg-white rounded-3xl border border-zinc-200 p-4" data-testid={`banner-${b.id}`}>
            <img src={resolveImageUrl(b.image_desktop)} alt="" className="aspect-video object-cover rounded-2xl w-full" />
            <p className="font-bold mt-2">{b.title}</p>
            <p className="text-xs text-meow-gray">Urutan {b.sort_order} · {b.position} · {b.link_url || "Tanpa tautan"} · {b.is_active ? "Aktif" : "Off"}</p>
            <div className="flex gap-2 mt-2">
              <button onClick={() => setEditing({ ...b })} className="text-xs text-meow-amber font-bold">Edit</button>
              <button onClick={async () => { await api.delete(`/admin/banners-v2/${b.id}`); load(); }} className="text-xs text-red-500 font-bold" data-testid={`del-banner-${b.id}`}>Hapus</button>
            </div>
          </div>
        ))}
      </div>
      {editing && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4 overflow-y-auto" onClick={() => setEditing(null)}>
          <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-lg w-full space-y-3" data-testid="banner-form">
            <h3 className="font-heading font-extrabold text-xl">Banner</h3>
            <input required placeholder="Judul" value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <ImagePicker
              label="Image Desktop (wajib)"
              value={editing.image_desktop || ""}
              onChange={(url) => setEditing({ ...editing, image_desktop: url })}
              testId="banner-image-desktop-picker"
            />
            <ImagePicker
              label="Image Mobile (opsional)"
              value={editing.image_mobile || ""}
              onChange={(url) => setEditing({ ...editing, image_mobile: url })}
              testId="banner-image-mobile-picker"
            />
            <div className="grid grid-cols-2 gap-2">
              <select value={editing.position} onChange={(e) => setEditing({ ...editing, position: e.target.value })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none">
                <option value="hero">Hero</option><option value="promo">Promo</option>
                <option value="shop_now">Shop Now</option><option value="article">Article</option>
                <option value="footer">Footer</option>
              </select>
              <select value={editing.target_device} onChange={(e) => setEditing({ ...editing, target_device: e.target.value })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none">
                <option value="all">All Device</option><option value="desktop">Desktop</option><option value="mobile">Mobile</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <select value={editing.link_type} onChange={(e) => setEditing({ ...editing, link_type: e.target.value })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none">
                <option value="internal">Internal</option><option value="external">External</option>
                <option value="shop_now">Shop Now</option><option value="category">Category</option>
                <option value="article">Article</option><option value="flash_sale">Flash Sale</option>
                <option value="none">None</option>
              </select>
              <label className="text-xs font-bold">URL tujuan<input aria-label="URL tujuan banner" placeholder="/shop-now atau https://..." value={editing.link_url || ""} onChange={(e) => setEditing({ ...editing, link_url: e.target.value })} className="w-full px-3 py-2 mt-1 rounded-xl bg-meow-bg outline-none" /></label>
            </div>
            <input placeholder="Alt text (SEO)" value={editing.alt_text || ""} onChange={(e) => setEditing({ ...editing, alt_text: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <div className="grid grid-cols-2 gap-2">
              <input type="datetime-local" placeholder="Mulai" value={localDateTime(editing.start_at)} onChange={(e) => setEditing({ ...editing, start_at: utcDateTime(e.target.value) })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" />
              <input type="datetime-local" placeholder="Selesai" value={localDateTime(editing.end_at)} onChange={(e) => setEditing({ ...editing, end_at: utcDateTime(e.target.value) })} className="px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            </div>
            <label className="block text-sm font-bold">Urutan tampilan<input type="number" min="0" step="1" required value={editing.sort_order} onChange={(e) => setEditing({ ...editing, sort_order: Number(e.target.value) })} className="w-full px-3 py-2 mt-1 rounded-xl bg-meow-bg outline-none" /><span className="text-xs font-normal text-meow-gray">Angka lebih kecil tampil lebih dahulu.</span></label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={editing.is_active} onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })} /> Aktif
            </label>
            <div className="flex gap-2"><button type="button" onClick={() => setEditing(null)} className="btn-secondary flex-1">Batal</button><button type="submit" disabled={saving} className="btn-primary flex-1 disabled:opacity-50">{saving ? "Menyimpan…" : "Simpan"}</button></div>
          </form>
        </div>
      )}
    </div>
  );
};

// ---------- Admin FAQs, Pages, Contact Setting ----------
export const AdminFAQs = () => {
  const [items, setItems] = useState([]);
  const [cats, setCats] = useState([]);
  const [editing, setEditing] = useState(null);
  const load = () => api.get("/admin/faqs").then(({ data }) => { setItems(data.items); setCats(data.categories); });
  useEffect(() => { load(); }, []);
  const submit = async (e) => {
    e.preventDefault();
    if (editing.id) await api.put(`/admin/faqs/${editing.id}`, editing);
    else await api.post("/admin/faqs", editing);
    toast.success("Tersimpan"); setEditing(null); load();
  };
  return (
    <div data-testid="admin-faqs">
      <div className="flex justify-between mb-4">
        <h1 className="font-heading text-3xl font-black">FAQ Management</h1>
        <button onClick={() => setEditing({ question: "", answer: "", is_active: true, sort_order: 0 })} className="btn-primary text-sm" data-testid="add-faq-btn"><Plus className="inline h-4 w-4 mr-1" /> FAQ Baru</button>
      </div>
      <div className="space-y-2">
        {items.map((f) => (
          <div key={f.id} className="bg-white rounded-2xl p-4 border border-zinc-200" data-testid={`faq-row-${f.id}`}>
            <p className="font-bold">{f.question}</p>
            <p className="text-sm text-meow-gray mt-1">{f.answer}</p>
            <p className="text-xs text-meow-gray mt-1">{cats.find(c => c.id === f.category_id)?.name || "-"} · {f.is_active ? "Aktif" : "Off"}</p>
            <div className="flex gap-2 mt-2">
              <button onClick={() => setEditing({ ...f })} className="text-xs text-meow-amber font-bold">Edit</button>
              <button onClick={async () => { await api.delete(`/admin/faqs/${f.id}`); load(); }} className="text-xs text-red-500 font-bold">Hapus</button>
            </div>
          </div>
        ))}
      </div>
      {editing && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={() => setEditing(null)}>
          <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-md w-full space-y-3" data-testid="faq-form">
            <input required placeholder="Pertanyaan" value={editing.question} onChange={(e) => setEditing({ ...editing, question: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="faq-q" />
            <textarea required rows={4} placeholder="Jawaban" value={editing.answer} onChange={(e) => setEditing({ ...editing, answer: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="faq-a" />
            <select value={editing.category_id || ""} onChange={(e) => setEditing({ ...editing, category_id: e.target.value || null })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none">
              <option value="">-- Kategori --</option>
              {cats.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={editing.is_active} onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })} /> Aktif</label>
            <div className="flex gap-2"><button type="button" onClick={() => setEditing(null)} className="btn-secondary flex-1">Batal</button><button type="submit" className="btn-primary flex-1">Simpan</button></div>
          </form>
        </div>
      )}
    </div>
  );
};

export const AdminPages = () => {
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const load = () => api.get("/admin/pages").then(({ data }) => setItems(data.pages));
  useEffect(() => { load(); }, []);
  const submit = async (e) => {
    e.preventDefault();
    if (!hasRichContent(editing.content)) { toast.error("Isi konten halaman terlebih dahulu."); return; }
    try {
      if (editing.id) await api.put(`/admin/pages/${editing.id}`, editing);
      else await api.post("/admin/pages", editing);
      toast.success("Tersimpan"); setEditing(null); load();
    } catch (err) { toast.error(adminError(err)); }
  };
  return (
    <div data-testid="admin-pages">
      <div className="flex justify-between mb-4">
        <h1 className="font-heading text-3xl font-black">CMS Pages (Privacy, Terms, dll)</h1>
        <button onClick={() => setEditing({ page_type: "custom", title: "", content: "", status: "published" })} className="btn-primary text-sm" data-testid="add-page-btn"><Plus className="inline h-4 w-4 mr-1" /> Halaman Baru</button>
      </div>
      <div className="space-y-2">
        {items.map((p) => (
          <div key={p.id} className="bg-white rounded-2xl p-4 border border-zinc-200 flex justify-between" data-testid={`page-row-${p.slug}`}>
            <div>
              <p className="font-bold">{p.title} <span className="text-xs text-meow-gray">v{p.version}</span></p>
              <p className="text-xs text-meow-gray break-all">{cmsPagePath(p.slug)} · {p.page_type} · {p.status}</p>
              {p.status === 'published' ? <a href={cmsPagePath(p.slug)} target="_blank" rel="noopener noreferrer" className="inline-block mt-1 text-xs font-bold text-meow-salmon underline" data-testid={`open-page-${p.slug}`}>Buka halaman ↗</a> : <p className="mt-1 text-xs text-meow-gray">Publikasikan halaman agar dapat dibuka pengunjung dan muncul di footer.</p>}
            </div>
            <div>
              <button onClick={() => setEditing({ ...p })} className="text-xs text-meow-amber font-bold mr-2">Edit</button>
              <button onClick={async () => { await api.delete(`/admin/pages/${p.id}`); load(); }} className="text-xs text-red-500 font-bold">Hapus</button>
            </div>
          </div>
        ))}
      </div>
      {editing && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4 overflow-y-auto" onClick={() => setEditing(null)}>
          <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-5xl w-full min-w-0 space-y-3 max-h-[90vh] overflow-y-auto" data-testid="page-form">
            <select value={editing.page_type} onChange={(e) => setEditing({ ...editing, page_type: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none">
              <option value="about">About</option>
              <option value="privacy_policy">Privacy Policy</option>
              <option value="terms_conditions">Terms & Conditions</option>
              <option value="refund_policy">Refund Policy</option>
              <option value="shipping_policy">Shipping Policy</option>
              <option value="custom">Custom</option>
            </select>
            <input required placeholder="Title" value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <RichTextEditor key={editing.id || 'new-page'} label="Konten halaman" value={editing.content || ''} onChange={(content) => setEditing(current => ({ ...current, content }))} testId="page-content-editor" />
            <select value={editing.status} onChange={(e) => setEditing({ ...editing, status: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none">
              <option value="draft">Draft</option><option value="published">Published</option><option value="archived">Archived</option>
            </select>
            <div className="flex gap-2"><button type="button" onClick={() => setEditing(null)} className="btn-secondary flex-1">Batal</button><button type="submit" className="btn-primary flex-1">Simpan</button></div>
          </form>
        </div>
      )}
    </div>
  );
};

export const AdminContactSetting = () => {
  const [form, setForm] = useState(null);
  const [messages, setMessages] = useState([]);
  useEffect(() => {
    api.get("/admin/contact-setting").then(({ data }) => setForm(data.contact || {}));
    api.get("/admin/contact-messages").then(({ data }) => setMessages(data.messages || []));
  }, []);
  const save = async () => { await api.put("/admin/contact-setting", form); toast.success("Contact setting tersimpan"); };
  if (!form) return null;
  return (
    <div data-testid="admin-contact-setting">
      <h1 className="font-heading text-3xl font-black mb-4">Contact Setting</h1>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white rounded-3xl p-6 border border-zinc-200 space-y-3">
          <p className="font-heading font-extrabold text-lg">Informasi Toko</p>
          {[["store_name", "Nama Toko"], ["address", "Alamat"], ["email", "Email"], ["phone", "Telepon"],
            ["whatsapp", "WhatsApp (628xxx)"], ["operational_hours", "Jam Operasional"],
            ["instagram", "Instagram URL"], ["facebook", "Facebook URL"], ["tiktok", "TikTok URL"]].map(([k, l]) => (
            <input key={k} placeholder={l} value={form[k] || ""} onChange={(e) => setForm({ ...form, [k]: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid={`cs-${k}`} />
          ))}
          <button onClick={save} className="btn-primary w-full" data-testid="cs-save">Simpan</button>
        </div>
        <div className="bg-white rounded-3xl p-6 border border-zinc-200" data-testid="contact-messages">
          <p className="font-heading font-extrabold text-lg mb-3">Pesan Masuk ({messages.length})</p>
          <div className="max-h-96 overflow-y-auto divide-y">
            {messages.map((m) => (
              <div key={m.id} className="py-3">
                <p className="font-bold text-sm">{m.name} · {m.email}</p>
                <p className="text-xs text-meow-gray">{m.subject || "-"} · {m.created_at.slice(0, 10)}</p>
                <p className="text-sm mt-1">{m.message}</p>
              </div>
            ))}
            {messages.length === 0 && <p className="text-sm text-meow-gray text-center py-6">Belum ada pesan.</p>}
          </div>
        </div>
      </div>
    </div>
  );
};

// ---------- Admin Staff ----------
export const AdminStaff = () => {
  const [items, setItems] = useState([]);
  const [perms, setPerms] = useState([]);
  const [creating, setCreating] = useState(null);
  const [editingPerms, setEditingPerms] = useState(null);
  const load = () => api.get("/admin/staff").then(({ data }) => setItems(data.staff));
  useEffect(() => {
    load();
    api.get("/admin/permissions").then(({ data }) => setPerms(data.permissions));
  }, []);
  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/admin/staff", creating);
      toast.success("Staff dibuat");
      setCreating(null); load();
    } catch (err) { toast.error(err?.response?.data?.detail || "Gagal"); }
  };
  const savePerms = async () => {
    await api.put(`/admin/staff/${editingPerms.user_id}/permissions`, { permissions: editingPerms.permissions });
    toast.success("Permission diperbarui"); setEditingPerms(null); load();
  };
  return (
    <div data-testid="admin-staff">
      <div className="flex justify-between mb-4">
        <h1 className="font-heading text-3xl font-black">Staff Management</h1>
        <button onClick={() => setCreating({ email: "", name: "", password: "", role: "staff", pin: "000000", permissions: [] })} className="btn-primary text-sm" data-testid="add-staff-btn"><Plus className="inline h-4 w-4 mr-1" /> Staff Baru</button>
      </div>
      <div className="bg-white rounded-3xl border border-zinc-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-meow-bg text-xs uppercase text-meow-gray">
            <tr><th className="text-left px-4 py-3">Nama</th><th className="text-left px-4 py-3">Email</th><th className="text-left px-4 py-3">Role</th><th className="text-left px-4 py-3">Permissions</th><th className="text-right px-4 py-3">Aksi</th></tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.user_id} className="border-t border-zinc-100" data-testid={`staff-${u.user_id}`}>
                <td className="px-4 py-3 font-bold">{u.name}</td>
                <td className="px-4 py-3">{u.email}</td>
                <td className="px-4 py-3 text-xs uppercase">{u.role}</td>
                <td className="px-4 py-3 text-xs">{(u.permissions || []).length}</td>
                <td className="px-4 py-3 text-right">
                  {u.role === "staff" && <button onClick={() => setEditingPerms({ ...u })} className="text-xs text-meow-amber font-bold" data-testid={`perms-${u.user_id}`}>Perms</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {creating && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={() => setCreating(null)}>
          <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-md w-full space-y-3" data-testid="staff-form">
            <h3 className="font-heading font-extrabold text-xl">Staff Baru</h3>
            <input required placeholder="Nama" value={creating.name} onChange={(e) => setCreating({ ...creating, name: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="st-name" />
            <input required type="email" placeholder="Email" value={creating.email} onChange={(e) => setCreating({ ...creating, email: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="st-email" />
            <input required type="password" placeholder="Password (min 8)" value={creating.password} onChange={(e) => setCreating({ ...creating, password: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="st-pwd" />
            <select value={creating.role} onChange={(e) => setCreating({ ...creating, role: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none">
              <option value="staff">Staff</option><option value="admin">Admin (butuh super_admin)</option>
            </select>
            <div className="flex gap-2"><button type="button" onClick={() => setCreating(null)} className="btn-secondary flex-1">Batal</button><button type="submit" className="btn-primary flex-1">Buat</button></div>
          </form>
        </div>
      )}
      {editingPerms && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={() => setEditingPerms(null)}>
          <div onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-lg w-full space-y-3 max-h-[80vh] overflow-y-auto" data-testid="perms-form">
            <h3 className="font-heading font-extrabold text-xl">Permissions: {editingPerms.name}</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {perms.map((p) => (
                <label key={p.name} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={(editingPerms.permissions || []).includes(p.name)}
                    onChange={(e) => {
                      const set = new Set(editingPerms.permissions || []);
                      if (e.target.checked) set.add(p.name); else set.delete(p.name);
                      setEditingPerms({ ...editingPerms, permissions: Array.from(set) });
                    }} data-testid={`perm-${p.name}`} />
                  <span>{p.display_name}</span>
                </label>
              ))}
            </div>
            <div className="flex gap-2"><button onClick={() => setEditingPerms(null)} className="btn-secondary flex-1">Batal</button><button onClick={savePerms} className="btn-primary flex-1" data-testid="perms-save">Simpan</button></div>
          </div>
        </div>
      )}
    </div>
  );
};

// ---------- Admin Import ----------
export const AdminImport = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [committing, setCommitting] = useState(false);
  const [result, setResult] = useState(null);

  const downloadTemplate = () => {
    const token = localStorage.getItem("meow_token");
    fetch(`${API_BASE}/admin/products/import/template`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then((r) => r.blob()).then((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "meoweyes_product_import_template.xlsx"; a.click();
      URL.revokeObjectURL(url);
    });
  };

  const doPreview = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    try {
      const token = localStorage.getItem("meow_token");
      const r = await fetch(`${API_BASE}/admin/products/import/preview`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail);
      setPreview(data);
    } catch (err) { toast.error(err.message); }
  };
  const doCommit = async () => {
    if (!file) return;
    setCommitting(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const token = localStorage.getItem("meow_token");
      const r = await fetch(`${API_BASE}/admin/products/import/commit`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail);
      setResult(data);
      toast.success(`Import selesai: ${data.created} baru, ${data.updated} update`);
    } catch (err) { toast.error(err.message); }
    finally { setCommitting(false); }
  };
  return (
    <div data-testid="admin-import">
      <h1 className="font-heading text-3xl font-black mb-4">Import Produk (Excel)</h1>
      <div className="bg-white rounded-3xl p-6 border border-zinc-200 space-y-3">
        <p className="text-sm text-meow-gray">Upload file .xlsx dengan multi-baris per warna untuk membuat produk + varian sekaligus.</p>
        <button onClick={downloadTemplate} className="btn-secondary text-sm" data-testid="dl-template-btn">📥 Download Template</button>
        <div className="flex items-center gap-3">
          <input type="file" accept=".xlsx" onChange={(e) => { setFile(e.target.files?.[0]); setPreview(null); setResult(null); }} data-testid="import-file" />
          {file && <button onClick={doPreview} className="btn-secondary text-sm" data-testid="preview-btn">Preview</button>}
        </div>
        {preview && (
          <div>
            <p className="font-bold">Preview: {preview.valid}/{preview.total} baris valid</p>
            <div className="max-h-60 overflow-y-auto bg-meow-bg rounded-2xl p-3 text-xs mt-2">
              {preview.rows.map((r, i) => (
                <div key={i} className={r.errors.length ? "text-red-500" : ""}>
                  Baris {r.row}: {r.data.product_name} · {r.data.variant_color} · Rp{r.data.variant_price}
                  {r.errors.length > 0 && <span> ❌ {r.errors.join(", ")}</span>}
                </div>
              ))}
            </div>
            <button onClick={doCommit} disabled={committing} className="btn-primary text-sm mt-3" data-testid="commit-btn">
              {committing ? "Mengimpor..." : "✅ Import Sekarang"}
            </button>
          </div>
        )}
        {result && (
          <div className="bg-meow-mint/10 rounded-2xl p-3 text-sm" data-testid="import-result">
            <p className="font-bold">Import selesai!</p>
            <p>Baru: {result.created} · Update: {result.updated}</p>
            {result.errors?.length > 0 && (
              <div>
                <p className="text-red-500 font-bold mt-2">Error:</p>
                <ul className="text-xs">{result.errors.map((e, i) => <li key={i}>{e}</li>)}</ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ---------- Admin Lens Indexes ----------
export const AdminLensIndexes = () => {
  const [items, setItems] = useState([]);
  const [lensTypes, setLensTypes] = useState([]);
  const [creating, setCreating] = useState(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const load = async () => {
    try {
      const [indexes, categories] = await Promise.all([api.get('/admin/lens/indexes'), api.get('/admin/categories')]);
      setItems(indexes.data.items || []);
      setLensTypes((categories.data.categories || []).filter(category => category.group_type === 'lens_type'));
      setError('');
    } catch (err) { setError(adminError(err, 'Data Lens Index belum dapat dimuat.')); }
  };
  useEffect(() => { load(); }, []);
  const submit = async (e) => {
    e.preventDefault();
    setSaving(true); setError('');
    try {
      if (creating.id) await api.put(`/admin/lens/indexes/${creating.id}`, creating);
      else await api.post('/admin/lens/indexes', creating);
      toast.success('Lens Index tersimpan'); setCreating(null); await load();
    } catch (err) { setError(adminError(err, 'Lens Index belum berhasil disimpan.')); }
    finally { setSaving(false); }
  };
  return (
    <div data-testid="admin-lens-indexes">
      <div className="flex justify-between mb-4">
        <h1 className="font-heading text-3xl font-black">Lens Indexes</h1>
        <button onClick={() => { setError(''); setCreating({ name: "", index_value: "1.60", lens_type_ids: [], additional_price: 0, is_active: true, sort_order: 0 }); }} className="btn-primary text-sm"><Plus className="inline h-4 w-4 mr-1" /> Index Baru</button>
      </div>
      <p className="text-sm text-meow-gray mb-4">Hubungkan setiap Lens Index dengan satu atau beberapa Jenis Lensa. Pilihan pada Paket mengikuti Jenis Lensa produk dan sudah termasuk harga paket. Pada Frame, harga Lens Index ditambahkan per produk.</p>
      {error && !creating && <p role="alert" className="text-sm text-red-600 mb-3">{error}</p>}
      <div className="bg-white rounded-3xl border border-zinc-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-meow-bg text-xs uppercase text-meow-gray">
            <tr><th className="text-left px-4 py-3">Nama</th><th className="text-left px-4 py-3">Index</th><th className="text-left px-4 py-3">Jenis Lensa</th><th className="text-left px-4 py-3">Harga Lensa</th><th className="text-left px-4 py-3">Range</th><th className="text-left px-4 py-3">Status</th><th className="text-right px-4 py-3">Aksi</th></tr>
          </thead>
          <tbody>
            {items.map((li) => (
              <tr key={li.id} className="border-t border-zinc-100" data-testid={`lens-idx-${li.id}`}>
                <td className="px-4 py-3 font-bold">{li.name}</td>
                <td className="px-4 py-3">{li.index_value}</td>
                <td className="px-4 py-3">{li.lens_types?.map(type => type.name).join(', ') || <span className="text-amber-700">Belum dihubungkan</span>}</td>
                <td className="px-4 py-3">Rp {(li.additional_price || 0).toLocaleString("id-ID")}</td>
                <td className="px-4 py-3 text-xs">{li.recommended_power_range}</td>
                <td className="px-4 py-3">{li.is_active ? 'Aktif' : 'Nonaktif'}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-3">
                    <button type="button" aria-label={`Edit Lens Index ${li.name}`} onClick={() => { setError(''); setCreating({ ...li, lens_type_ids: li.lens_type_ids || [] }); }}><Edit2 className="h-4 w-4" /></button>
                    <button type="button" aria-label={`Nonaktifkan Lens Index ${li.name}`} disabled={!li.is_active} onClick={async () => { try { await api.delete(`/admin/lens/indexes/${li.id}`); await load(); } catch (err) { setError(adminError(err, 'Lens Index belum dapat dinonaktifkan.')); } }} className="text-red-500 text-xs disabled:opacity-30"><Trash2 className="h-4 w-4" /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {creating && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={() => { if (!saving) setCreating(null); }}>
          <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-lg w-full max-h-[90dvh] overflow-y-auto space-y-3" aria-label="Form Lens Index">
            <h2 className="font-bold text-lg">{creating.id ? 'Edit Lens Index' : 'Lens Index Baru'}</h2>
            {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
            <fieldset disabled={saving} className="space-y-3">
            <input required placeholder="Nama (e.g. 1.60 Ultra Thin)" value={creating.name} onChange={(e) => setCreating({ ...creating, name: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <input required placeholder="Index value (1.50, 1.56, 1.60...)" value={creating.index_value} onChange={(e) => setCreating({ ...creating, index_value: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <input placeholder="Range (mis. -4.00 s/d +4.00)" value={creating.recommended_power_range || ""} onChange={(e) => setCreating({ ...creating, recommended_power_range: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <fieldset className="border rounded-xl p-3 space-y-2">
              <legend className="text-sm font-bold px-1">Jenis Lensa</legend>
              {lensTypes.filter(type => type.is_active || creating.lens_type_ids.includes(type.id)).map(type => <label key={type.id} className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={creating.lens_type_ids.includes(type.id)} onChange={event => setCreating({ ...creating, lens_type_ids: event.target.checked ? [...creating.lens_type_ids, type.id] : creating.lens_type_ids.filter(id => id !== type.id) })} />
                {type.name}{!type.is_active ? ' (nonaktif)' : ''}
              </label>)}
              {!lensTypes.length && <p className="text-xs text-meow-gray">Tambahkan Jenis Lensa pada halaman kategori terlebih dahulu.</p>}
              <p className="text-xs text-meow-gray">Pilih minimal satu agar Lens Index tersedia untuk Paket yang sesuai. Tanpa Jenis Lensa, Lens Index hanya tersedia untuk Frame.</p>
            </fieldset>
            <label className="block text-xs font-semibold">Harga Lensa (tambahan per Frame)
              <input type="number" min="0" step="0.01" required value={creating.additional_price} onChange={(e) => setCreating({ ...creating, additional_price: Number(e.target.value) })} className="block w-full mt-1 px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            </label>
            <input placeholder="Deskripsi" value={creating.description || ""} onChange={(e) => setCreating({ ...creating, description: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={creating.is_active} onChange={event => setCreating({ ...creating, is_active: event.target.checked })} />Aktif</label>
            <div className="flex gap-2"><button type="button" onClick={() => setCreating(null)} className="btn-secondary flex-1">Batal</button><button type="submit" className="btn-primary flex-1">{saving ? 'Menyimpan…' : 'Simpan'}</button></div>
            </fieldset>
          </form>
        </div>
      )}
    </div>
  );
};
