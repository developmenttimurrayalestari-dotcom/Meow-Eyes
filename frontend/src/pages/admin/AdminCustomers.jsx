import FormField from "../../components/FormField";
import React, { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { Mail } from "lucide-react";
import { toast } from "sonner";

export { default as AdminUsers } from "./CustomerManagement";

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
          <FormField label="Subjek email"><input required placeholder="Subjek" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="camp-subject" /></FormField>
          <FormField label="Isi email"><textarea required placeholder="Isi email" rows={6} value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="camp-body" /></FormField>
          <FormField label="Kelompok penerima"><select value={form.segment} onChange={(e) => setForm({ ...form, segment: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none">
            <option value="all">Semua subscriber</option>
            <option value="active">Customer aktif</option>
            <option value="dormant">Belum belanja</option>
          </select></FormField>
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
