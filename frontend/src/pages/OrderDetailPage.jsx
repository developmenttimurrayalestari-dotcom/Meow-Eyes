import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, apiError, formatIDR, imageSrc } from "../lib/api";
import { Cat } from "lucide-react";
import PurchaseRatings from "../components/PurchaseRatings";
import OrderReturns from '../components/Returns';

const OrderDetailPage = () => {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setData(null); setError("");
    const controller = new AbortController();
    api.get(`/orders/${id}`, { signal: controller.signal }).then(({ data }) => setData(data)).catch((err) => { if (!controller.signal.aborted) setError(apiError(err)); });
    return () => controller.abort();
  }, [id]);

  if (error) return <div role="alert" className="max-w-xl mx-auto p-8 text-center"><p>{error}</p><Link to="/orders" className="btn-secondary inline-block mt-3">Daftar Pesanan</Link></div>;
  if (!data) return <div className="min-h-[40vh] flex items-center justify-center"><Cat className="h-10 w-10 text-meow-salmon animate-pulse" /></div>;
  const o = data.order;

  return (
    <div className="max-w-4xl mx-auto px-4 md:px-6 py-8" data-testid="order-detail-page">
      <div className="flex items-center gap-2 text-sm text-meow-gray mb-4">
        <Link to="/orders" className="hover:text-meow-salmon">← Daftar Pesanan</Link>
      </div>
      <h1 className="font-heading text-3xl md:text-4xl font-black">Detail Pesanan</h1>
      <p className="text-sm text-meow-gray" data-testid="order-number">{o.order_number}</p>

      {o.payment_reconciliation_required && <p role="status" className="mt-4 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-sm">Informasi pembayaran sedang diperiksa oleh tim toko. Tunggu pembaruan status sebelum melakukan pembayaran lagi.</p>}
      <div className="grid md:grid-cols-3 gap-6 mt-6">
        <div className="md:col-span-2 space-y-5">
          <div className="bg-white rounded-3xl p-6" data-testid="items-section">
            <h3 className="font-heading font-extrabold text-lg mb-3">Produk</h3>
            <div className="divide-y divide-meow-midnight/5">
              {(o.items || []).map((it, i) => (
                <div key={i} className="flex gap-3 py-3">
                  <img src={imageSrc(it.main_image)} alt="" className="w-16 h-16 rounded-xl object-cover" />
                  <div className="flex-1">
                    <p className="font-bold">{it.product_name}</p>
                    {it.variant_label && <p className="text-xs text-meow-gray">{it.variant_label}</p>}
                    <p className="text-sm">{it.quantity} × {formatIDR(it.unit_price)}</p>
                  </div>
                  <p className="font-bold text-meow-salmon">{formatIDR(it.subtotal)}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-3xl p-6" data-testid="shipping-detail">
            <h3 className="font-heading font-extrabold text-lg mb-3">Pengiriman</h3>
            <div className="text-sm space-y-1">
              <p><span className="text-meow-gray">Kurir:</span> <span className="font-bold uppercase">{o.shipping_courier}</span> — {o.shipping_service}</p>
              <p><span className="text-meow-gray">Resi:</span> <span className="font-mono font-bold">{o.tracking_number || "-"}</span></p>
              <p className="text-meow-gray pt-2 border-t mt-2">
                <span className="font-bold text-meow-midnight">{o.address?.recipient}</span> · {o.address?.phone}<br />
                {o.address?.street}, {o.address?.city}, {o.address?.province} {o.address?.postal_code}
              </p>
            </div>
            {data.tracking && (
              <div className="mt-5">
                <p className="text-xs font-bold uppercase tracking-wider text-meow-gray mb-2">Riwayat Pengiriman</p>
                <ul className="space-y-2 text-sm" data-testid="tracking-list">
                  {data.tracking.map((t, i) => (
                    <li key={i} className="flex gap-2">
                      <div className={`h-2 w-2 mt-2 rounded-full ${i === 0 ? "bg-meow-salmon" : "bg-meow-midnight/30"}`} />
                      <div>
                        <p>{t.status}</p>
                        <p className="text-xs text-meow-gray">{new Date(t.time).toLocaleString("id-ID")}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="bg-white rounded-3xl p-6 sticky top-24" data-testid="order-summary">
            <h3 className="font-heading font-extrabold text-lg mb-3">Ringkasan</h3>
            <dl className="text-sm space-y-1.5">
              <Row label="Subtotal" v={formatIDR(o.subtotal)} />
              <Row label="Voucher" v={`-${formatIDR(o.voucher_discount)}`} />
              <Row label={`Poin (${o.points_used})`} v={`-${formatIDR(o.points_discount)}`} />
              <Row label="Roulette" v={`-${formatIDR(o.roulette_discount)}`} />
              <Row label="Ongkir" v={formatIDR(o.shipping_cost)} />
              <div className="border-t mt-2 pt-2 flex justify-between font-bold">
                <dt>Total</dt><dd className="text-meow-salmon">{formatIDR(o.total)}</dd>
              </div>
            </dl>
            <p className="text-xs text-meow-gray mt-3">
              Status: <span className="font-bold text-meow-midnight">{o.status}</span><br />
              Bayar: <span className="font-bold">{o.payment_status}</span>
            </p>
          </div>
        </div>
      </div>
      {o.payment_status === "paid" && !o.payment_reconciliation_required && <PurchaseRatings orderId={o.id} />}
      <OrderReturns order={o} />
      {o.status === "pending_payment" && <Link to={`/payment/${o.order_number}`} className="btn-primary inline-block mt-6">Lanjutkan Pembayaran</Link>}
    </div>
  );
};

const Row = ({ label, v }) => (
  <div className="flex justify-between"><dt className="text-meow-gray">{label}</dt><dd className="font-bold">{v}</dd></div>
);

export default OrderDetailPage;
