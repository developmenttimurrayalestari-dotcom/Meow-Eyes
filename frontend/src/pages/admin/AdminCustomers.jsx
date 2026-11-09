import React, { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { Users, Mail, Search } from "lucide-react";
import { toast } from "sonner";

export const AdminUsers = () => {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const load = useCallback(() => api.get("/admin/users", { params: { q } }).then(({ data }) => setItems(data.users)), [q]);
  useEffect(() => { load(); }, [load]);
  const toggle = async (uid) => { await api.post(`/admin/users/${uid}/toggle-active`); load(); };
  const reset = async (uid) => { await api.post(`/admin/users/${uid}/reset-pin`); toast.success("PIN direset"); };

  return (
    <div data-testid="admin-users">
      <h1 className="font-heading text-3xl font-black mb-4 flex items-center gap-2"><Users /> Pelanggan</h1>
      <div className="flex items-center bg-white border border-zinc-200 rounded-full px-4 py-2 mb-4 max-w-md">
        <Search className="h-4 w-4 text-meow-gray mr-2" />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari nama atau email..." className="bg-transparent flex-1 outline-none text-sm" data-testid="user-search" />
      </div>
      <div className="bg-white rounded-3xl border border-zinc-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-meow-bg text-xs uppercase text-meow-gray">
            <tr>
              <th className="text-left px-4 py-3">Nama</th>
              <th className="text-left px-4 py-3">Email</th>
              <th className="text-left px-4 py-3">Role</th>
              <th className="text-left px-4 py-3">Poin</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-right px-4 py-3">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.user_id} className="border-t border-zinc-100" data-testid={`user-row-${u.user_id}`}>
                <td className="px-4 py-3 font-bold">{u.name}</td>
                <td className="px-4 py-3">{u.email}</td>
                <td className="px-4 py-3 text-xs uppercase">{u.role}</td>
                <td className="px-4 py-3">{u.points_balance}</td>
                <td className="px-4 py-3 text-xs">{u.is_active ? "Aktif" : "Off"}</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => toggle(u.user_id)} className="text-xs text-meow-salmon font-bold mr-2" data-testid={`toggle-${u.user_id}`}>Toggle</button>
                  <button onClick={() => reset(u.user_id)} className="text-xs text-meow-amber font-bold" data-testid={`reset-pin-${u.user_id}`}>Reset PIN</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const AdminNewsletter = () => {
  const [subs, setSubs] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [form, setForm] = useState({ subject: "", body: "", segment: "all" });

  const load = () => {
    api.get("/admin/newsletter/subscribers").then(({ data }) => setSubs(data.subscribers));
    api.get("/admin/newsletter/campaigns").then(({ data }) => setCampaigns(data.campaigns));
  };
  useEffect(() => { load(); }, []);

  const send = async (e) => {
    e.preventDefault();
    await api.post("/admin/newsletter/campaigns", form);
    toast.success("Campaign terkirim (mock)");
    setForm({ subject: "", body: "", segment: "all" });
    load();
  };

  return (
    <div data-testid="admin-newsletter">
      <h1 className="font-heading text-3xl font-black mb-4 flex items-center gap-2"><Mail /> Newsletter</h1>
      <div className="grid lg:grid-cols-3 gap-4">
        <form onSubmit={send} className="bg-white rounded-3xl border border-zinc-200 p-5 space-y-3" data-testid="campaign-form">
          <p className="font-heading font-extrabold">Kirim Campaign</p>
          <input required placeholder="Subjek" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="camp-subject" />
          <textarea required placeholder="Isi email" rows={6} value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="camp-body" />
          <select value={form.segment} onChange={(e) => setForm({ ...form, segment: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none">
            <option value="all">Semua subscriber</option>
            <option value="active">Customer aktif</option>
            <option value="dormant">Belum belanja</option>
          </select>
          <button type="submit" className="w-full btn-primary text-sm" data-testid="camp-send">Kirim</button>
        </form>
        <div className="lg:col-span-2 bg-white rounded-3xl border border-zinc-200 p-5">
          <p className="font-heading font-extrabold mb-3">Subscriber ({subs.length})</p>
          <div className="max-h-96 overflow-y-auto divide-y text-sm">
            {subs.slice(0, 100).map((s) => (
              <div key={s.id} className="py-2 flex justify-between" data-testid={`sub-row-${s.email}`}>
                <span>{s.email}</span>
                <span className="text-xs text-meow-gray">{s.created_at.slice(0, 10)}</span>
              </div>
            ))}
          </div>
          <p className="font-heading font-extrabold mt-5 mb-3">Campaign Sebelumnya</p>
          <div className="space-y-2 text-sm">
            {campaigns.slice(0, 10).map((c) => (
              <div key={c.id} className="bg-meow-bg rounded-xl p-3" data-testid={`campaign-${c.id}`}>
                <p className="font-bold">{c.subject}</p>
                <p className="text-xs text-meow-gray">Sent {c.sent_count} · {c.created_at.slice(0, 10)}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
