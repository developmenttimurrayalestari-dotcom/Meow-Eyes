import React, { useCallback, useEffect, useState } from "react";
import { CheckCircle2, AlertCircle, Plug, RefreshCw, Copy } from "lucide-react";
import { toast } from "sonner";
import { api, API_BASE } from "../../lib/api";
import { adminError } from "./adminUtils";

export default function AdminIntegrations() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { const { data } = await api.get("/admin/integrations"); setStatus(data); }
    catch (err) { setError(adminError(err, "Status integrasi belum dapat dimuat.")); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const endpointUrl = path => {
    try { return new URL(path, new URL(API_BASE, window.location.origin).origin).href; }
    catch { return path; }
  };
  return <div className="max-w-5xl space-y-6" data-testid="admin-integrations">
    <header className="flex flex-wrap justify-between gap-4"><div><h1 className="font-heading text-3xl font-black flex items-center gap-3"><Plug /> Integrasi</h1><p className="mt-2 text-sm text-meow-gray">Kesiapan pembayaran DOKU dan pengiriman Everpro.</p></div><button onClick={load} disabled={loading} className="btn-secondary inline-flex items-center gap-2"><RefreshCw size={16} className={loading ? "animate-spin" : ""} /> Periksa kembali</button></header>
    {error && <p role="alert" className="rounded-2xl bg-red-50 text-red-700 p-4">{error}</p>}
    {!status && loading && <p role="status">Memuat status integrasi…</p>}
    {status && <>
      <div className="grid md:grid-cols-2 gap-5">{[["payment", "Pembayaran"], ["shipping", "Pengiriman"]].map(([key, label]) => {
        const item = status[key] || {};
        return <section key={key} className="bg-white rounded-3xl border border-zinc-200 p-6 space-y-4"><div className="flex gap-3 items-start">{item.ready && !item.mock ? <CheckCircle2 className="text-emerald-600 shrink-0" /> : <AlertCircle className="text-amber-600 shrink-0" />}<div><h2 className="font-heading text-xl font-bold">{label} · {(item.provider || "Belum dipilih").toUpperCase()}</h2><p className="text-sm text-meow-gray mt-1">{item.mock ? "Mode simulasi pengembangan" : item.ready ? "Konfigurasi tersedia" : "Konfigurasi belum lengkap"}</p></div></div><dl className="text-sm space-y-2"><div className="flex justify-between gap-4"><dt className="text-meow-gray">Lingkungan</dt><dd className="font-bold">{item.environment || (item.mock ? "development / test" : "—")}</dd></div>{item.shipment_type && <div className="flex justify-between"><dt className="text-meow-gray">Penyerahan paket</dt><dd className="font-bold">{item.shipment_type}</dd></div>}</dl>{item.missing?.length > 0 && <div className="rounded-xl bg-amber-50 p-3 text-sm"><p className="font-bold mb-1">Variabel server yang perlu diisi:</p><ul className="list-disc pl-5 space-y-1">{item.missing.map(name => <li key={name} className="font-mono text-xs break-all">{name}</li>)}</ul></div>}<p className="text-xs text-meow-gray">Status ini memeriksa konfigurasi. Verifikasi transaksi dan pengiriman melalui sandbox penyedia sebelum mengaktifkan layanan produksi.</p></section>;
      })}</div>
      <section className="bg-white rounded-3xl border border-zinc-200 p-6 space-y-4"><h2 className="font-heading text-xl font-bold">URL notifikasi penyedia</h2><p className="text-sm text-meow-gray">Daftarkan URL HTTPS publik berikut pada dashboard penyedia. Status pembayaran dan resi diperbarui setelah notifikasi berhasil diverifikasi.</p><div className="space-y-3">{Object.entries(status.webhooks || {}).map(([name, path]) => <div key={name} className="rounded-xl bg-zinc-50 p-3"><p className="font-bold text-xs mb-1">{name.replaceAll("_", " ").toUpperCase()}</p><div className="flex items-start gap-3"><code className="text-xs break-all flex-1">{endpointUrl(path)}</code><button type="button" aria-label={`Salin URL ${name}`} onClick={async () => { try { await navigator.clipboard.writeText(endpointUrl(path)); toast.success("URL disalin"); } catch { toast.error("Salin URL secara manual dari teks di atas"); } }}><Copy size={16} /></button></div></div>)}</div></section>
      {status.reconciliation && <section className="bg-white rounded-3xl border border-zinc-200 p-6"><h2 className="font-heading text-xl font-bold mb-4">Perlu ditinjau</h2><div className="grid sm:grid-cols-2 gap-4"><div className="rounded-xl bg-zinc-50 p-4"><p className="text-2xl font-black">{status.reconciliation.payment_events_failed || 0}</p><p className="text-sm text-meow-gray">Notifikasi pembayaran gagal diproses</p></div><div className="rounded-xl bg-zinc-50 p-4"><p className="text-2xl font-black">{status.reconciliation.shipments_pending || 0}</p><p className="text-sm text-meow-gray">Pengiriman menunggu konfirmasi</p></div></div>{status.reconciliation.events?.length > 0 && <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr><th className="p-2">Pesanan</th><th className="p-2">Penyedia</th><th className="p-2">Alasan pemeriksaan</th><th className="p-2">Waktu</th></tr></thead><tbody>{status.reconciliation.events.map(event => <tr key={event.id} className="border-t"><td className="p-2 font-mono break-all">{event.order_id || "—"}</td><td className="p-2">{event.provider}</td><td className="p-2">{event.reason || "Perlu ditinjau"}</td><td className="p-2 whitespace-nowrap">{event.received_at ? new Date(event.received_at).toLocaleString("id-ID") : "—"}</td></tr>)}</tbody></table><p className="text-xs text-meow-gray mt-2">Tinjau riwayat pada detail pesanan dan panduan rekonsiliasi sebelum melakukan koreksi.</p></div>}</section>}
    </>}
  </div>;
}
