import React, { useCallback, useEffect, useState } from "react";
import { api, formatIDR } from "../../lib/api";
import { toast } from "sonner";
import { Download, RefreshCw, Truck, X } from "lucide-react";
import { adminError, inputClass } from "./adminUtils";

const STATUSES = ["all", "pending_payment", "paid", "processing", "shipped", "completed", "cancelled", "expired"];

function PrescriptionDetails({ prescription }) {
  if (!prescription) return null;
  const download = async () => {
    try {
      const response = await api.get(`/prescriptions/uploads/${prescription.attachment_upload_id}`, { responseType: "blob" });
      const type = response.data.type;
      const extension = type === "image/png" ? "png" : type === "image/webp" ? "webp" : "jpg";
      const url = URL.createObjectURL(response.data);
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = `resep.${extension}`;
      document.body.appendChild(anchor); anchor.click(); anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch { toast.error("Lampiran resep belum dapat diunduh atau akses tidak diizinkan"); }
  };
  return <div className="bg-zinc-50 rounded-xl p-3 mt-2 space-y-2 text-xs">
    <p className="font-bold">Resep saat checkout</p>
    <table className="w-full text-left"><thead><tr>{["Mata", "SPH", "CYL", "AXIS", "ADD"].map(label => <th key={label} className="py-1">{label}</th>)}</tr></thead><tbody>{[["od", "Kanan (OD)"], ["os", "Kiri (OS)"]].map(([key, label]) => <tr key={key}><th className="font-medium py-1">{label}</th>{["sph", "cyl", "axis", "add"].map(measure => <td key={measure}>{prescription[`${key}_${measure}`] ?? "—"}</td>)}</tr>)}</tbody></table>
    <p>PD: {prescription.pd_right != null ? `Kanan ${prescription.pd_right} / Kiri ${prescription.pd_left} mm` : `${prescription.pd || prescription.pd_total || "—"} mm`}</p>
    {prescription.notes && <p className="whitespace-pre-wrap">Catatan: {prescription.notes}</p>}
    {prescription.attachment_upload_id && <button type="button" onClick={download} className="text-meow-salmon font-bold inline-flex items-center gap-1"><Download size={13} /> Unduh foto resep</button>}
  </div>;
}

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [tab, setTab] = useState("all");
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [pickup, setPickup] = useState(null);
  const [pickupTime, setPickupTime] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const { data } = await api.get("/admin/orders", { params: tab === "all" ? {} : { status: tab } });
      setOrders(data.orders || []);
      return data.orders || [];
    } catch (err) { setError(adminError(err, "Pesanan belum dapat dimuat.")); return []; }
    finally { setLoading(false); }
  }, [tab]);
  useEffect(() => { load(); }, [load]);
  const open = order => { setDetail(order); setPickup(null); setPickupTime(""); setError(""); };
  const setStatus = async status => {
    setBusy(true);
    try {
      await api.post(`/admin/orders/${detail.id}/status`, { status });
      toast.success("Status diperbarui"); const refreshed = await load(); setDetail(refreshed.find(o => o.id === detail.id) || null);
    } catch (err) { toast.error(adminError(err)); }
    finally { setBusy(false); }
  };
  const prepareShipment = async () => {
    setBusy(true); setError("");
    try { const { data } = await api.get(`/admin/orders/${detail.id}/shipment/pickup-times`); setPickup(data); setPickupTime(""); }
    catch (err) { setError(adminError(err, "Pengiriman belum dapat disiapkan.")); }
    finally { setBusy(false); }
  };
  const shipmentAction = async refresh => {
    if (!refresh && pickup?.shipment_type === "PICKUP" && !pickupTime) return setError("Pilih jadwal penjemputan terlebih dahulu.");
    setBusy(true); setError("");
    try {
      const body = !refresh && pickup?.shipment_type === "PICKUP" ? { pickup_time: Number(pickupTime) } : {};
      const { data } = await api.post(`/admin/orders/${detail.id}/shipment${refresh ? "/refresh" : ""}`, body);
      if (data.order) setDetail(data.order);
      setPickup(null); await load();
      toast.success(data.reconciliation_required ? "Permintaan tercatat; konfirmasi penyedia masih diperlukan" : refresh ? "Status pengiriman diperbarui" : "Permintaan pengiriman tercatat");
    } catch (err) { setError(adminError(err, "Permintaan pengiriman belum berhasil.")); }
    finally { setBusy(false); }
  };
  const canBook = detail?.shipment_provider === "everpro" && detail?.payment_status === "paid" && ["paid", "processing"].includes(detail.status) && !detail.tracking_number;
  return <div data-testid="admin-orders" className="space-y-4">
    <header className="flex justify-between items-center"><h1 className="font-heading text-3xl font-black">Pesanan</h1><button type="button" disabled={loading || busy} onClick={load} className="btn-secondary text-sm inline-flex items-center gap-2"><RefreshCw size={15} /> Perbarui</button></header>
    <div className="flex gap-2 overflow-x-auto pb-2" data-testid="admin-order-tabs">{STATUSES.map(status => <button key={status} onClick={() => setTab(status)} className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap ${tab === status ? "bg-meow-midnight text-white" : "bg-white border border-zinc-200"}`} data-testid={`admin-tab-${status}`}>{status.replaceAll("_", " ")}</button>)}</div>
    {error && !detail && <p role="alert" className="bg-red-50 text-red-700 rounded-xl p-3">{error}</p>}
    <div className="bg-white rounded-3xl border border-zinc-200 overflow-x-auto"><table className="w-full text-sm" data-testid="admin-orders-table"><thead className="bg-meow-bg text-xs uppercase text-meow-gray"><tr>{["Order #", "Customer", "Tanggal", "Total", "Pembayaran", "Status", "Aksi"].map(label => <th key={label} className="text-left px-4 py-3">{label}</th>)}</tr></thead><tbody>{orders.map(order => <tr key={order.id} className="border-t border-zinc-100" data-testid={`admin-order-${order.order_number}`}><td className="px-4 py-3 font-mono text-xs">{order.order_number}</td><td className="px-4 py-3">{order.address?.recipient}</td><td className="px-4 py-3">{order.created_at?.slice(0, 10)}</td><td className="px-4 py-3 font-bold whitespace-nowrap">{formatIDR(order.total)}</td><td className="px-4 py-3 text-xs">{order.payment_status}</td><td className="px-4 py-3 text-xs">{order.status}</td><td className="px-4 py-3"><button onClick={() => open(order)} className="text-meow-salmon font-bold text-xs" data-testid={`admin-detail-${order.order_number}`}>Detail</button></td></tr>)}</tbody></table>{loading ? <p role="status" className="text-center p-6 text-meow-gray">Memuat pesanan…</p> : orders.length === 0 && <p className="text-center text-meow-gray p-8">Tidak ada pesanan pada status ini.</p>}</div>
    {detail && <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={() => !busy && setDetail(null)}><section role="dialog" aria-modal="true" aria-labelledby="admin-order-title" className="bg-white rounded-3xl p-6 max-w-2xl w-full max-h-[92vh] overflow-y-auto space-y-4" onClick={e => e.stopPropagation()} data-testid="admin-order-detail-modal">
      <div className="flex justify-between gap-4"><div><h2 id="admin-order-title" className="font-heading font-extrabold text-xl">{detail.order_number}</h2><p className="text-xs text-meow-gray mt-1">{new Date(detail.created_at).toLocaleString("id-ID")} · {detail.status} · {detail.payment_status}</p></div><button type="button" disabled={busy} onClick={() => setDetail(null)} aria-label="Tutup"><X /></button></div>
      {error && <p role="alert" className="bg-red-50 text-red-700 rounded-xl p-3 text-sm">{error}</p>}
      <div className="text-sm rounded-xl border p-3"><p className="font-bold">{detail.address?.recipient} · {detail.address?.phone}</p><p className="text-meow-gray mt-1">{[detail.address?.street, detail.address?.subdistrict, detail.address?.district, detail.address?.city, detail.address?.province, detail.address?.postal_code].filter(Boolean).join(", ")}</p></div>
      <ul className="divide-y">{(detail.items || []).map(item => <li key={item.id} className="py-3"><div className="flex justify-between text-sm gap-3"><span>{item.product_name} × {item.quantity}</span><strong>{formatIDR(item.subtotal)}</strong></div>{(item.components || []).map(component => <p key={component.id} className="text-xs text-meow-gray mt-1">{component.product_name || component.role} {component.variant_name || ""}</p>)}<PrescriptionDetails prescription={item.prescription} /></li>)}</ul>
      <p className="font-bold text-lg">Total: {formatIDR(detail.total)}</p>
      {detail.payment_provider === "doku" && <section className="rounded-xl bg-zinc-50 p-3 space-y-2 text-sm"><p>Pembayaran DOKU: <strong>{detail.payment_status}</strong></p>{detail.payment_reconciliation_required && <p className="text-amber-800">Perlu pemeriksaan pembayaran dan ledger sebelum pemenuhan dilanjutkan.</p>}<button type="button" disabled={busy} className="text-meow-salmon font-bold disabled:opacity-50" onClick={async () => { setBusy(true); setError(""); try { const { data } = await api.post(`/admin/orders/${detail.id}/payment/refresh`); if (data.order) setDetail(data.order); await load(); toast.success("Status pembayaran diperiksa"); } catch (err) { setError(adminError(err)); } finally { setBusy(false); } }}>Periksa status DOKU</button></section>}
      <section className="rounded-2xl border p-4 space-y-3"><h3 className="font-bold flex items-center gap-2"><Truck size={18} /> Pengiriman</h3><p className="text-sm">{(detail.shipping_courier || detail.courier_code)?.toUpperCase()} {detail.shipping_service || detail.service_code} · {detail.shipment_provider || "Belum dipesan"}</p><p className="text-sm">Resi: <strong>{detail.tracking_number || "Menunggu penerbitan"}</strong></p>{detail.carrier_status && <p className="text-sm text-meow-gray">{detail.carrier_status}</p>}{detail.shipment_label_url && /^https:\/\//i.test(detail.shipment_label_url) && <a href={detail.shipment_label_url} target="_blank" rel="noopener noreferrer" className="text-sm text-meow-salmon font-bold inline-block">Buka label pengiriman</a>}
        <div className="flex flex-wrap gap-2">{canBook && <button type="button" disabled={busy} onClick={prepareShipment} className="btn-primary text-sm disabled:opacity-50">Siapkan pengiriman</button>}{detail.shipment_provider === "everpro" && <button type="button" disabled={busy} onClick={() => shipmentAction(true)} className="btn-secondary text-sm disabled:opacity-50">Perbarui resi & pelacakan</button>}</div>
        {pickup && <div className="bg-zinc-50 rounded-xl p-3 space-y-3"><p className="text-sm font-bold">{pickup.shipment_type === "PICKUP" ? "Jadwal penjemputan paket" : "Pengiriman drop-off"}</p>{pickup.shipment_type === "PICKUP" ? <label className="block text-xs">Jadwal tersedia<select value={pickupTime} onChange={e => setPickupTime(e.target.value)} className={`${inputClass} mt-1`}><option value="">Pilih jadwal</option>{(pickup.times || []).map(time => <option key={time.value} value={time.value}>{time.label}</option>)}</select>{!pickup.times?.length && <span className="text-amber-800 block mt-2">Belum ada jadwal tersedia. Periksa kembali nanti.</span>}</label> : <p className="text-xs text-meow-gray">Setelah pemesanan terkonfirmasi, serahkan paket ke gerai kurir sesuai layanan yang dipilih.</p>}<button type="button" disabled={busy || (pickup.shipment_type === "PICKUP" && !pickupTime)} onClick={() => shipmentAction(false)} className="btn-primary text-sm disabled:opacity-50">{busy ? "Memproses…" : "Pesan pengiriman"}</button></div>}
      </section>
      <div className="flex flex-wrap gap-2">{detail.status === "paid" && <button type="button" disabled={busy} onClick={() => setStatus("processing")} className="btn-secondary text-sm" data-testid={`admin-set-processing-${detail.order_number}`}>Mulai proses pesanan</button>}{detail.status === "shipped" && <button type="button" disabled={busy} onClick={() => setStatus("completed")} className="btn-secondary text-sm" data-testid={`admin-set-completed-${detail.order_number}`}>Tandai selesai</button>}{detail.status === "pending_payment" && detail.payment_provider !== "doku" && <button type="button" disabled={busy} onClick={() => setStatus("cancelled")} className="text-sm font-bold text-red-600">Batalkan pesanan</button>}</div>
      <button type="button" disabled={busy} onClick={() => setDetail(null)} className="w-full btn-secondary text-sm">Tutup</button>
    </section></div>}
  </div>;
}
