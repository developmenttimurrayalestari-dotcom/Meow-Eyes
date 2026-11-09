import React, { useEffect, useState } from "react";
import { api, formatIDR } from "../../lib/api";
import { toast } from "sonner";
import { Plus, Trash2, Ticket, Zap, Target } from "lucide-react";

export const AdminVouchers = () => {
  const [items, setItems] = useState([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({
    code: "", name: "", discount_type: "percent", discount_value: 10,
    min_purchase: 0, max_discount: 100000, quota: 100,
    start_at: new Date().toISOString(),
    end_at: new Date(Date.now() + 30 * 86400000).toISOString(),
    is_active: true,
  });
  const load = () => api.get("/admin/vouchers").then(({ data }) => setItems(data.vouchers));
  useEffect(() => { load(); }, []);
  const submit = async (e) => {
    e.preventDefault();
    await api.post("/admin/vouchers", form);
    toast.success("Voucher dibuat");
    setShow(false); load();
  };
  return (
    <div data-testid="admin-vouchers">
      <div className="flex justify-between mb-4">
        <h1 className="font-heading text-3xl font-black flex items-center gap-2"><Ticket /> Voucher</h1>
        <button onClick={() => setShow(true)} className="btn-primary text-sm" data-testid="add-voucher-btn"><Plus className="inline h-4 w-4 mr-1" /> Voucher Baru</button>
      </div>
      <div className="bg-white rounded-3xl border border-zinc-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-meow-bg text-xs uppercase text-meow-gray">
            <tr>
              <th className="text-left px-4 py-3">Code</th>
              <th className="text-left px-4 py-3">Nama</th>
              <th className="text-left px-4 py-3">Tipe</th>
              <th className="text-left px-4 py-3">Nilai</th>
              <th className="text-left px-4 py-3">Min</th>
              <th className="text-left px-4 py-3">Used/Quota</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-right px-4 py-3">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {items.map((v) => (
              <tr key={v.id} className="border-t border-zinc-100" data-testid={`voucher-row-${v.code}`}>
                <td className="px-4 py-3 font-mono">{v.code}</td>
                <td className="px-4 py-3">{v.name}</td>
                <td className="px-4 py-3 text-xs">{v.discount_type}</td>
                <td className="px-4 py-3">{v.discount_type === "percent" ? `${v.discount_value}%` : formatIDR(v.discount_value)}</td>
                <td className="px-4 py-3">{formatIDR(v.min_purchase || 0)}</td>
                <td className="px-4 py-3">{v.used_count}/{v.quota}</td>
                <td className="px-4 py-3 text-xs">{v.is_active ? "Aktif" : "Nonaktif"}</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={async () => { await api.delete(`/admin/vouchers/${v.id}`); load(); }} className="text-red-500" data-testid={`del-voucher-${v.code}`}><Trash2 className="h-4 w-4" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {show && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={() => setShow(false)}>
          <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-md w-full space-y-3" data-testid="voucher-form">
            <h3 className="font-heading font-extrabold text-xl">Voucher Baru</h3>
            <input placeholder="Kode (otomatis jika kosong)" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="v-code" />
            <input required placeholder="Nama" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="v-name" />
            <select value={form.discount_type} onChange={(e) => setForm({ ...form, discount_type: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="v-type">
              <option value="percent">Percent</option>
              <option value="nominal">Nominal</option>
              <option value="free_shipping">Free Shipping</option>
            </select>
            <input type="number" placeholder="Nilai" value={form.discount_value} onChange={(e) => setForm({ ...form, discount_value: Number(e.target.value) })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <input type="number" placeholder="Min purchase" value={form.min_purchase} onChange={(e) => setForm({ ...form, min_purchase: Number(e.target.value) })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <input type="number" placeholder="Quota" value={form.quota} onChange={(e) => setForm({ ...form, quota: Number(e.target.value) })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShow(false)} className="btn-secondary flex-1">Batal</button>
              <button type="submit" className="btn-primary flex-1" data-testid="v-save">Simpan</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export { default as AdminFlashSales } from "./AdminFlashSales";

export const AdminRoulette = () => {
  const [rewards, setRewards] = useState([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ label: "", type: "points", value: 50, color: "#FCA311", probability: 0.1, is_active: true });
  const load = () => api.get("/admin/roulette/rewards").then(({ data }) => setRewards(data.rewards));
  useEffect(() => { load(); }, []);
  const submit = async (e) => { e.preventDefault(); await api.post("/admin/roulette/rewards", form); toast.success("Reward dibuat"); setShow(false); load(); };
  return (
    <div data-testid="admin-roulette">
      <div className="flex justify-between mb-4">
        <h1 className="font-heading text-3xl font-black flex items-center gap-2"><Target /> Roulette</h1>
        <button onClick={() => setShow(true)} className="btn-primary text-sm" data-testid="add-reward-btn"><Plus className="inline h-4 w-4 mr-1" /> Reward Baru</button>
      </div>
      <div className="bg-white rounded-3xl border border-zinc-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-meow-bg text-xs uppercase text-meow-gray">
            <tr>
              <th className="text-left px-4 py-3">Label</th>
              <th className="text-left px-4 py-3">Tipe</th>
              <th className="text-left px-4 py-3">Nilai</th>
              <th className="text-left px-4 py-3">Probabilitas</th>
              <th className="text-left px-4 py-3">Warna</th>
              <th className="text-right px-4 py-3">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {rewards.map((r) => (
              <tr key={r.id} className="border-t border-zinc-100" data-testid={`reward-row-${r.id}`}>
                <td className="px-4 py-3 font-bold">{r.label}</td>
                <td className="px-4 py-3 text-xs">{r.type}</td>
                <td className="px-4 py-3">{r.value}</td>
                <td className="px-4 py-3">{(r.probability * 100).toFixed(0)}%</td>
                <td className="px-4 py-3"><span className="inline-block h-4 w-4 rounded-full" style={{ background: r.color }} /></td>
                <td className="px-4 py-3 text-right">
                  <button onClick={async () => { await api.delete(`/admin/roulette/rewards/${r.id}`); load(); }} className="text-red-500"><Trash2 className="h-4 w-4" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {show && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={() => setShow(false)}>
          <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-md w-full space-y-3" data-testid="reward-form">
            <h3 className="font-heading font-extrabold text-xl">Reward Baru</h3>
            <input required placeholder="Label" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none">
              <option value="points">Points</option>
              <option value="discount">Discount</option>
              <option value="free_shipping">Free Shipping</option>
              <option value="voucher">Voucher</option>
              <option value="nothing">Nothing</option>
            </select>
            <input type="number" placeholder="Value" value={form.value} onChange={(e) => setForm({ ...form, value: Number(e.target.value) })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <input type="number" step="0.01" placeholder="Probability 0-1" value={form.probability} onChange={(e) => setForm({ ...form, probability: Number(e.target.value) })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <input placeholder="Color hex" value={form.color} onChange={(e) => setForm({ ...form, color: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" />
            <div className="flex gap-2"><button type="button" onClick={() => setShow(false)} className="btn-secondary flex-1">Batal</button><button type="submit" className="btn-primary flex-1">Simpan</button></div>
          </form>
        </div>
      )}
    </div>
  );
};
