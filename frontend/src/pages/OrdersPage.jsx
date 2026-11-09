import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatIDR, imageSrc } from "../lib/api";
import { Package, Clock, Truck, CheckCircle2, XCircle, AlertCircle } from "lucide-react";

const STATUS_META = {
  pending_payment: { label: "Menunggu Bayar", color: "bg-yellow-100 text-yellow-700", Icon: Clock },
  paid: { label: "Sudah Dibayar", color: "bg-meow-mint/20 text-meow-mint", Icon: CheckCircle2 },
  processing: { label: "Diproses", color: "bg-blue-100 text-blue-700", Icon: Package },
  shipped: { label: "Dikirim", color: "bg-indigo-100 text-indigo-700", Icon: Truck },
  completed: { label: "Selesai", color: "bg-meow-green/20 text-meow-green", Icon: CheckCircle2 },
  cancelled: { label: "Dibatalkan", color: "bg-red-100 text-red-600", Icon: XCircle },
  expired: { label: "Expired", color: "bg-gray-100 text-gray-600", Icon: AlertCircle },
};

const OrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [tab, setTab] = useState("all");

  useEffect(() => {
    const params = tab !== "all" ? { status: tab } : {};
    api.get("/orders", { params }).then(({ data }) => setOrders(data.orders));
  }, [tab]);

  return (
    <div className="max-w-5xl mx-auto px-4 md:px-6 lg:px-8 py-8" data-testid="orders-page">
      <h1 className="font-heading text-3xl md:text-4xl font-black mb-6">Pesanan Saya</h1>
      <div className="flex gap-2 overflow-x-auto no-scrollbar pb-3 mb-4" data-testid="orders-tabs">
        {["all", "pending_payment", "processing", "shipped", "completed", "cancelled"].map((s) => (
          <button key={s} onClick={() => setTab(s)}
            className={`px-4 py-2 rounded-full text-sm font-bold whitespace-nowrap ${tab === s ? "bg-meow-midnight text-white" : "bg-white text-meow-midnight border border-meow-midnight/10"}`}
            data-testid={`tab-${s}`}>
            {s === "all" ? "Semua" : STATUS_META[s]?.label}
          </button>
        ))}
      </div>
      {orders.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center">
          <Package className="h-16 w-16 mx-auto text-meow-midnight/30" />
          <p className="font-heading font-black text-2xl mt-3">Belum ada pesanan</p>
          <Link to="/products" className="btn-primary mt-4 inline-block">Mulai Belanja</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((o) => {
            const meta = STATUS_META[o.status] || { label: o.status, color: "bg-gray-100", Icon: Package };
            const Icon = meta.Icon;
            return (
              <Link key={o.id} to={`/orders/${o.id}`} className="block bg-white rounded-3xl p-5 hover:shadow-meow-soft" data-testid={`order-${o.order_number}`}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs text-meow-gray">{o.created_at.slice(0, 10)}</p>
                    <p className="font-bold">{o.order_number}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1 ${meta.color}`}>
                    <Icon className="h-3 w-3" /> {meta.label}
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-3">
                  <img src={imageSrc(o.items[0]?.main_image)} alt="" className="w-14 h-14 rounded-xl object-cover" />
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-sm line-clamp-1">{o.items[0]?.product_name}</p>
                    {o.items.length > 1 && <p className="text-xs text-meow-gray">+{o.items.length - 1} item lainnya</p>}
                  </div>
                  <p className="font-heading font-extrabold text-meow-salmon">{formatIDR(o.total)}</p>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default OrdersPage;
