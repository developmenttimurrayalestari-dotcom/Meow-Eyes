import React, { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useLocation, Link } from "react-router-dom";
import { api, apiError, copyText, formatIDR } from "../lib/api";
import { Copy, CheckCircle2, CreditCard, RefreshCw, ExternalLink, Clock3 } from "lucide-react";
import { toast } from "sonner";
import PurchaseRatings from "../components/PurchaseRatings";

const safePaymentUrl = (value) => {
  try { const url = new URL(value); return url.protocol === "https:" ? url.href : ""; } catch { return ""; }
};

export default function PaymentPage() {
  const { orderNumber } = useParams();
  const location = useLocation();
  const [order, setOrder] = useState(location.state?.order || null);
  const [payment, setPayment] = useState(location.state?.payment || null);
  const [flags, setFlags] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(location.state?.payment_error || "");
  const [busy, setBusy] = useState(false);
  const [nextCheck, setNextCheck] = useState(0);
  const [now, setNow] = useState(Date.now());
  const mounted = useRef(true);
  const orderRef = useRef(order);
  orderRef.current = order;

  const load = useCallback(async (quiet = false) => {
    try {
      const { data } = await api.get(`/payments/${encodeURIComponent(orderNumber)}`);
      if (!mounted.current) return;
      setOrder(data.order); setPayment(data.payment); if (!quiet) setError(data.payment_error || "");
    } catch (err) { if (mounted.current && !quiet) setError(apiError(err, "Informasi pembayaran belum dapat dimuat.")); }
    finally { if (mounted.current) setLoading(false); }
  }, [orderNumber]);
  useEffect(() => {
    mounted.current = true;
    load();
    api.get("/integrations/status").then(({ data }) => { if (mounted.current) setFlags(data); }).catch(() => {});
    const tick = window.setInterval(() => setNow(Date.now()), 1000);
    const poll = window.setInterval(() => {
      const current = orderRef.current;
      if (!document.hidden && (!current || ((current.payment_status !== "paid" || current.payment_reconciliation_required) && !["cancelled", "expired", "refunded"].includes(current.status)))) load(true);
    }, 5000);
    const onFocus = () => load(true);
    window.addEventListener("focus", onFocus);
    return () => { mounted.current = false; clearInterval(tick); clearInterval(poll); window.removeEventListener("focus", onFocus); };
  }, [load]);

  const refresh = async () => {
    if (!order || busy) return;
    setBusy(true); setError("");
    try {
      const { data } = await api.post(`/orders/${order.id}/payment/refresh`);
      if (data.order) { setOrder(data.order); setPayment(data.payment); }
      await load(); setNextCheck(Date.now() + 60000);
    } catch (err) { setError(apiError(err, "Status pembayaran belum dapat diperiksa. Halaman akan tetap memperbarui status secara otomatis.")); setNextCheck(Date.now() + 60000); }
    finally { setBusy(false); }
  };
  const retry = async () => {
    if (!order || busy) return;
    setBusy(true); setError("");
    try {
      const { data } = await api.post(`/orders/${order.id}/payment/retry`);
      setOrder(data.order); setPayment(data.payment);
      if (data.payment_error) setError(data.payment_error);
    } catch (err) { setError(apiError(err, "Tautan pembayaran belum berhasil disiapkan. Pesanan Anda tetap tersimpan.")); }
    finally { setBusy(false); }
  };
  const simulate = async () => {
    setBusy(true); setError("");
    try { await api.post(`/payment/confirm/${encodeURIComponent(orderNumber)}`); await load(); }
    catch (err) { setError(apiError(err)); }
    finally { setBusy(false); }
  };
  if (loading && !order) return <p role="status" className="text-center py-16">Memuat pembayaran…</p>;
  if (!order) return <div className="max-w-xl mx-auto p-8 text-center" role="alert"><p>{error || "Pesanan tidak ditemukan."}</p><button type="button" onClick={() => load()} className="btn-secondary mt-4">Coba lagi</button><Link to="/orders" className="block mt-3 underline">Lihat pesanan saya</Link></div>;
  const needsVerification = Boolean(order.payment_reconciliation_required);
  const paid = order.payment_status === "paid" && !needsVerification;
  const vaNumber = payment?.virtual_account_number || payment?.va_number;
  const closed = ["cancelled", "expired", "refunded"].includes(order.status) || order.payment_status === "refunded";
  const mock = Boolean(flags?.payment?.mock && payment?.mock && payment?.provider === "doku-mock");
  const paymentUrl = safePaymentUrl(payment?.payment_url || order.payment_url);
  const expiry = payment?.expires_at || order.reservation_expires_at;
  const expiryPassed = expiry && new Date(expiry).getTime() <= now;
  const cooldown = Math.max(0, Math.ceil((nextCheck - now) / 1000));
  return <div className="max-w-3xl mx-auto px-4 md:px-6 py-8" data-testid="payment-page">
    <h1 className="font-heading text-3xl md:text-4xl font-black mb-2">Pembayaran</h1>
    <p className="text-sm text-meow-gray">Pesanan #{order.order_number}</p>
    {needsVerification ? <section className="rounded-3xl p-6 mt-6 border border-amber-200 bg-amber-50" data-testid="payment-verification-pending"><h2 className="font-heading text-xl font-black">Pembayaran Sedang Diperiksa</h2><p className="mt-2 text-sm">Informasi pembayaran telah diterima dan memerlukan pemeriksaan oleh tim toko. Tunggu pembaruan status sebelum melakukan pembayaran lagi.</p><Link to={`/orders/${order.id}`} className="btn-secondary mt-4 inline-block">Lihat Detail Pesanan</Link></section> : paid ? <section className="bg-white rounded-3xl p-8 mt-6 text-center" data-testid="payment-paid">
      <CheckCircle2 className="h-16 w-16 mx-auto text-meow-mint" /><h2 className="font-heading text-2xl font-black mt-3">Pembayaran Berhasil</h2>
      <p className="text-meow-gray text-sm mt-2">Pembayaran telah terkonfirmasi. Anda dapat melihat perkembangan pesanan dan memberikan rating di bawah.</p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center mt-6"><Link to={`/orders/${order.id}`} className="btn-primary">Lihat Detail Pesanan</Link><Link to="/shop-now" className="btn-secondary">Belanja Lagi</Link></div>
    </section> : closed ? <section className="bg-white rounded-3xl p-8 mt-6 text-center"><h2 className="font-heading text-2xl font-black">{order.status === "expired" ? "Waktu Pembayaran Berakhir" : order.payment_status === "refunded" ? "Pembayaran Dikembalikan" : "Pesanan Dibatalkan"}</h2><p className="text-sm text-meow-gray mt-2">Tautan pembayaran untuk pesanan ini tidak dapat digunakan.</p><Link to={`/orders/${order.id}`} className="btn-secondary mt-5 inline-block">Lihat Detail Pesanan</Link></section>
      : <section className="bg-white rounded-3xl p-6 md:p-8 mt-6">
        <h2 className="font-bold flex items-center gap-2 text-meow-salmon"><CreditCard className="h-5 w-5" />{mock ? "Pembayaran Demo" : "Pembayaran melalui DOKU"}</h2>
        <p className="text-xs text-meow-gray mt-5">TOTAL TAGIHAN</p><p className="font-heading font-black text-3xl" data-testid="payment-total">{formatIDR(order.total)}</p>
        {expiry && <p className={`flex items-center gap-2 text-sm mt-3 ${expiryPassed ? "text-amber-700" : "text-meow-gray"}`}><Clock3 className="h-4 w-4 shrink-0" />{expiryPassed ? "Batas waktu terlewati; menunggu konfirmasi status pembayaran." : `Bayar sebelum ${new Date(expiry).toLocaleString("id-ID")}`}</p>}
        {vaNumber && <div className="mt-4 p-4 bg-meow-bg rounded-2xl flex items-center justify-between gap-3"><div><p className="text-xs text-meow-gray">Nomor Virtual Account</p><p className="font-mono font-bold">{vaNumber}</p></div><button type="button" aria-label="Salin nomor virtual account" onClick={async () => { try { await copyText(vaNumber); toast.success("Nomor disalin"); } catch { toast.error("Nomor belum tersalin."); } }} className="p-2"><Copy className="h-4 w-4" /></button></div>}
        {mock ? <div className="mt-5 p-4 bg-meow-amber/15 rounded-2xl text-sm"><p className="font-bold">Mode Demo</p><p className="text-meow-gray mt-1">Tombol ini mensimulasikan pembayaran untuk pengujian.</p><button type="button" onClick={simulate} disabled={busy} className="btn-primary w-full mt-4 disabled:opacity-50">{busy ? "Memproses…" : "Simulasikan Pembayaran"}</button></div>
          : <><p className="text-sm text-meow-gray mt-4">Pilih metode pembayaran pada halaman DOKU. Status pesanan akan diperbarui setelah pembayaran dikonfirmasi.</p>
            {paymentUrl && !expiryPassed ? <a href={paymentUrl} className="btn-primary w-full mt-5 flex items-center justify-center gap-2" data-testid="doku-pay-link">Bayar dengan DOKU<ExternalLink className="h-4 w-4" /></a>
              : !expiryPassed && <button type="button" onClick={retry} disabled={busy || !flags?.payment?.ready} className="btn-primary w-full mt-5 disabled:opacity-50">{busy ? "Menyiapkan…" : "Siapkan Tautan Pembayaran"}</button>}
            {!flags?.payment?.ready && <p className="text-sm text-amber-700 mt-3">Pembayaran sementara belum tersedia. Pesanan Anda tetap tersimpan.</p>}
            <button type="button" onClick={refresh} disabled={busy || cooldown > 0} className="btn-secondary w-full mt-3 inline-flex items-center justify-center gap-2 disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${busy ? "animate-spin" : ""}`} />{cooldown ? `Periksa lagi dalam ${cooldown} dtk` : "Sudah Bayar? Periksa Status"}</button>
          </>}
        <p className="text-xs text-meow-gray mt-4 text-center" aria-live="polite">Status: {order.payment_status === "pending" ? "Menunggu pembayaran" : order.payment_status}. Halaman memperbarui status secara otomatis.</p>
      </section>}
    {error && <div role="alert" className="mt-4 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-sm">{error}</div>}
    {paid && <PurchaseRatings orderId={order.id} />}
    {!paid && <Link to={`/orders/${order.id}`} className="block text-center mt-5 text-sm font-bold text-meow-salmon">Lihat Detail Pesanan →</Link>}
  </div>;
}
