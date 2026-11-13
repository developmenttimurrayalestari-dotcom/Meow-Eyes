import React, { useEffect, useState } from "react";
import { ArrowRight, ChevronLeft, ChevronRight, ClipboardCheck, RefreshCw } from "lucide-react";
import { api } from "../../lib/api";
import { profileRequestError } from "../../lib/customerProfile";
import { useAuth } from "../../contexts/AuthContext";

const statusLabels = {
  draft: "Draf", pending_review: "Menunggu review", needs_verification: "Perlu verifikasi",
  needs_remeasure: "Perlu ukur ulang", approved: "Disetujui",
};
const dateLabel = value => {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
};

export default function AdminMeowsurement() {
  const { user } = useAuth();
  const allowed = ["admin", "super_admin"].includes(user?.role) || (user?.role === "staff" && user?.permissions?.includes("meowsurement.review"));
  const [status, setStatus] = useState(""), [page, setPage] = useState(1), [reload, setReload] = useState(0);
  const [data, setData] = useState({ sessions: [], total: 0, total_pages: 0 }), [loading, setLoading] = useState(true), [error, setError] = useState("");
  useEffect(() => {
    if (!allowed) { setLoading(false); return undefined; }
    const controller = new AbortController(); setLoading(true); setError("");
    api.get("/admin/meowsurement/sessions", { params: { page, page_size: 15, ...(status ? { status } : {}) }, signal: controller.signal, withCredentials: true })
      .then(({ data: response }) => { if (!controller.signal.aborted) setData(response); })
      .catch(err => { if (!controller.signal.aborted) setError(profileRequestError(err, "Daftar pengukuran belum dapat dimuat.")); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [allowed, page, status, reload]);
  const totalPages = Math.max(1, data.total_pages || Math.ceil((data.total || 0) / 15));
  return <div data-testid="admin-meowsurement-page">
    <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
      <div><h1 className="font-heading font-black text-3xl flex items-center gap-2"><ClipboardCheck className="h-7 w-7" />Review Meowsurement</h1><p className="text-sm text-meow-gray mt-2">Tinjau hasil pengukuran customer memakai profil, resep, dan spesifikasi frame yang tersimpan saat sesi dibuat.</p></div>
      {allowed && <button type="button" onClick={() => setReload(value => value + 1)} disabled={loading} className="btn-secondary inline-flex items-center gap-2 disabled:opacity-50"><RefreshCw className={"h-4 w-4 " + (loading ? "animate-spin" : "")} />Muat ulang</button>}
    </div>
    {!allowed ? <p role="alert" className="p-5 rounded-2xl bg-white border border-meow-midnight/10">Akun Anda belum memiliki izin untuk mereview Meowsurement. Minta administrator web memberikan izin review pada akun staf Anda.</p> : <>
      <div className="bg-white border border-meow-midnight/10 rounded-2xl p-4 mb-5 flex flex-wrap items-end justify-between gap-3"><label className="block text-sm font-semibold">Status pengukuran<select aria-label="Status pengukuran" value={status} onChange={event => { setStatus(event.target.value); setPage(1); }} className="block mt-2 px-3 py-2 rounded-xl bg-meow-bg border border-meow-midnight/10"><option value="">Menunggu review & verifikasi</option>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><p className="text-sm text-meow-gray">15 sesi per halaman</p></div>
      {error ? <p role="alert" className="rounded-2xl p-5 bg-red-50 border border-red-200 text-red-800">{error}</p> : loading ? <p role="status" className="p-6 text-meow-gray">Memuat sesi pengukuran…</p> : data.sessions?.length ? <div className="rounded-2xl bg-white border border-meow-midnight/10 overflow-hidden">
        <div className="overflow-x-auto"><table className="w-full min-w-[680px] text-sm"><thead className="bg-meow-bg text-left"><tr>{["Customer", "Frame", "Tanggal & revisi", "Status", "Tindakan"].map(label => <th key={label} className="px-4 py-3 font-semibold">{label}</th>)}</tr></thead><tbody>{data.sessions.map(session => <tr key={session.id} className="border-t border-meow-midnight/10" data-testid={"measurement-review-" + session.id}>
          <td className="px-4 py-4 font-semibold">{session.customerName || "Customer"}</td>
          <td className="px-4 py-4">{session.frameName || "Frame"}</td>
          <td className="px-4 py-4">{dateLabel(session.examinationDate || session.createdAt)}<span className="block text-xs text-meow-gray mt-1">Revisi {session.revisionNumber || 1}</span></td>
          <td className="px-4 py-4"><span className={"inline-block rounded-full px-3 py-1 text-xs font-semibold " + (session.status === "approved" ? "bg-meow-mint/20" : "bg-meow-amber/20")}>{statusLabels[session.status] || session.status}</span></td>
          <td className="px-4 py-4"><a href={"/meowsurement/?review_session=" + encodeURIComponent(session.id)} className="text-meow-salmon font-bold inline-flex items-center gap-1" data-testid={"open-measurement-review-" + session.id}>Buka review<ArrowRight className="h-4 w-4" /></a></td>
        </tr>)}</tbody></table></div>
        <div className="p-4 border-t border-meow-midnight/10 flex flex-wrap justify-between items-center gap-3"><p className="text-sm text-meow-gray">{data.total || 0} sesi · Halaman {page} dari {totalPages}</p><div className="flex gap-2"><button type="button" aria-label="Halaman sebelumnya" disabled={page <= 1} onClick={() => setPage(value => value - 1)} className="p-2 border rounded-xl disabled:opacity-40"><ChevronLeft className="h-4 w-4" /></button><button type="button" aria-label="Halaman berikutnya" disabled={page >= totalPages} onClick={() => setPage(value => value + 1)} className="p-2 border rounded-xl disabled:opacity-40"><ChevronRight className="h-4 w-4" /></button></div></div>
      </div> : <p className="p-8 rounded-2xl text-center bg-white border border-meow-midnight/10 text-meow-gray">Belum ada sesi untuk status ini.</p>}
    </>}
  </div>;
}
