import React, { useEffect, useState } from "react";
import { api, formatIDR } from "../../lib/api";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import {
  TrendingUp, ShoppingBag, Users, Package, Wallet, AlertTriangle,
  Truck, Mail, Target,
} from "lucide-react";

const COLORS = ["#FF6B6B", "#FCA311", "#2A9D8F", "#0B192C", "#06D6A0", "#FFD166", "#FF8FA3", "#94A3B8"];

const StatCard = ({ icon: Icon, label, value, sub, color = "text-meow-salmon", testid }) => (
  <div className="bg-white rounded-3xl p-5 border border-zinc-200" data-testid={testid}>
    <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-meow-gray font-bold">
      <Icon className={`h-4 w-4 ${color}`} /> {label}
    </div>
    <p className="font-heading text-2xl md:text-3xl font-black mt-2">{value}</p>
    {sub && <p className="text-xs text-meow-gray mt-1">{sub}</p>}
  </div>
);

const AdminDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [salesChart, setSalesChart] = useState({ labels: [], datasets: [] });
  const [orderStatus, setOrderStatus] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [paymentChart, setPaymentChart] = useState([]);
  const [rouletteChart, setRouletteChart] = useState([]);
  const [gameChart, setGameChart] = useState([]);

  useEffect(() => {
    api.get("/admin/dashboard/summary").then(({ data }) => setSummary(data)).catch(() => setSummary({}));
    api.get("/admin/dashboard/sales-chart", { params: { days: 14 } }).then(({ data }) => setSalesChart(data)).catch(() => {});
    api.get("/admin/dashboard/order-status-chart").then(({ data }) => setOrderStatus(data.items)).catch(() => {});
    api.get("/admin/dashboard/top-products").then(({ data }) => setTopProducts(data.items)).catch(() => {});
    api.get("/admin/dashboard/payment-chart").then(({ data }) => setPaymentChart(data.items)).catch(() => {});
    api.get("/admin/dashboard/roulette-chart").then(({ data }) => setRouletteChart(data.items)).catch(() => {});
    api.get("/admin/dashboard/game-chart").then(({ data }) => setGameChart(data.items)).catch(() => {});
  }, []);

  if (!summary) return <div className="p-8" data-testid="dashboard-loading">Memuat dashboard...</div>;
  const s = summary || {};

  const salesData = salesChart.labels.map((l, i) => ({
    name: l,
    Revenue: salesChart.datasets[0]?.data[i] || 0,
    Orders: salesChart.datasets[1]?.data[i] || 0,
  }));

  return (
    <div data-testid="admin-dashboard">
      <h1 className="font-heading text-3xl md:text-4xl font-black mb-1">Dashboard</h1>
      <p className="text-meow-gray text-sm mb-6">Ringkasan performa marketplace Meow Eyes</p>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <StatCard icon={Wallet} label="Penjualan Hari Ini" value={formatIDR(s.sales_today || 0)} sub={`${s.orders_today || 0} order`} testid="stat-sales-today" />
        <StatCard icon={TrendingUp} label="Penjualan Bulan Ini" value={formatIDR(s.sales_month || 0)} sub={`${s.orders_month || 0} order`} color="text-meow-amber" testid="stat-sales-month" />
        <StatCard icon={ShoppingBag} label="Order Pending" value={s.pending_payment || 0} color="text-yellow-500" testid="stat-pending" />
        <StatCard icon={Package} label="Order Selesai" value={s.paid_orders || 0} color="text-meow-mint" testid="stat-paid" />
        <StatCard icon={Users} label="Total Pelanggan" value={s.total_users || 0} color="text-meow-midnight" testid="stat-users" />
        <StatCard icon={Package} label="Produk Aktif" value={s.total_products || 0} testid="stat-products" />
        <StatCard icon={AlertTriangle} label="Stok Rendah" value={s.low_stock || 0} color="text-red-500" testid="stat-lowstock" />
        <StatCard icon={Mail} label="Subscriber" value={s.subscribers || 0} color="text-meow-mint" testid="stat-subs" />
      </div>

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-3xl p-6 border border-zinc-200" data-testid="sales-chart-card">
          <p className="font-heading font-extrabold text-lg mb-3">Penjualan 14 Hari Terakhir</p>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <LineChart data={salesData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v, name) => name === "Revenue" ? formatIDR(v) : v} />
                <Legend />
                <Line type="monotone" dataKey="Revenue" stroke="#FF6B6B" strokeWidth={2.5} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="Orders" stroke="#FCA311" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-zinc-200" data-testid="order-status-chart-card">
          <p className="font-heading font-extrabold text-lg mb-3">Status Order</p>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={orderStatus} dataKey="count" nameKey="status" innerRadius={45} outerRadius={80}>
                  {orderStatus.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-zinc-200" data-testid="top-products-card">
          <p className="font-heading font-extrabold text-lg mb-3">Produk Terlaris</p>
          <div className="space-y-2">
            {topProducts.slice(0, 7).map((p, i) => (
              <div key={p.id} className="flex items-center gap-3" data-testid={`top-prod-${i}`}>
                <span className="font-bold w-5">{i + 1}.</span>
                <img src={p.main_image} alt="" className="h-10 w-10 rounded-xl object-cover" />
                <p className="flex-1 text-sm font-bold line-clamp-1">{p.name}</p>
                <span className="text-meow-salmon font-extrabold">{p.sold_count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-zinc-200" data-testid="payment-chart-card">
          <p className="font-heading font-extrabold text-lg mb-3">Status Pembayaran</p>
          <div style={{ width: "100%", height: 220 }}>
            <ResponsiveContainer>
              <BarChart data={paymentChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#FCA311" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-zinc-200" data-testid="roulette-chart-card">
          <p className="font-heading font-extrabold text-lg mb-3"><Target className="inline h-4 w-4" /> Roulette Reward</p>
          <div style={{ width: "100%", height: 220 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={rouletteChart} dataKey="count" nameKey="_id" outerRadius={75}>
                  {rouletteChart.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-zinc-200" data-testid="game-chart-card">
          <p className="font-heading font-extrabold text-lg mb-3">Aktivitas Game</p>
          <div style={{ width: "100%", height: 220 }}>
            <ResponsiveContainer>
              <BarChart data={gameChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="_id" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="plays" fill="#2A9D8F" radius={[6, 6, 0, 0]} name="Plays" />
                <Bar dataKey="points" fill="#FF6B6B" radius={[6, 6, 0, 0]} name="Points" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
