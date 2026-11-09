import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Mail, Phone, MapPin, MessageCircle, Instagram, Facebook, ExternalLink, Send } from "lucide-react";
import { toast } from "sonner";

const ContactPage = () => {
  const [info, setInfo] = useState({});
  const [faqs, setFaqs] = useState([]);
  const [form, setForm] = useState({ name: "", email: "", phone: "", subject: "", message: "" });
  const [sending, setSending] = useState(false);

  useEffect(() => {
    api.get("/contact/info").then(({ data }) => setInfo(data.contact || {}));
    api.get("/faqs").then(({ data }) => setFaqs(data.items || []));
  }, []);

  const send = async (e) => {
    e.preventDefault();
    setSending(true);
    try {
      await api.post("/contact/send", form);
      toast.success("Pesan berhasil dikirim, kami akan segera menghubungi kamu!");
      setForm({ name: "", email: "", phone: "", subject: "", message: "" });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Gagal mengirim");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 md:px-6 py-8" data-testid="contact-page">
      <div className="text-center mb-8">
        <MessageCircle className="h-10 w-10 mx-auto text-meow-salmon" />
        <h1 className="font-heading text-4xl md:text-5xl font-black mt-2">Hubungi Meow Eyes</h1>
        <p className="text-meow-gray mt-2">Kami senang mendengar kabar dari kamu.</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Info kontak */}
        <div className="bg-white rounded-[32px] p-6 md:p-8 space-y-5" data-testid="contact-info">
          <div className="flex items-start gap-3">
            <div className="h-10 w-10 rounded-2xl bg-meow-salmon/15 grid place-items-center"><MapPin className="h-5 w-5 text-meow-salmon" /></div>
            <div><p className="font-bold">Alamat</p><p className="text-sm text-meow-gray">{info.address || "-"}</p></div>
          </div>
          <div className="flex items-start gap-3">
            <div className="h-10 w-10 rounded-2xl bg-meow-amber/15 grid place-items-center"><Mail className="h-5 w-5 text-meow-amber" /></div>
            <div><p className="font-bold">Email</p><a href={`mailto:${info.email}`} className="text-sm text-meow-gray hover:text-meow-salmon">{info.email || "-"}</a></div>
          </div>
          <div className="flex items-start gap-3">
            <div className="h-10 w-10 rounded-2xl bg-meow-mint/15 grid place-items-center"><Phone className="h-5 w-5 text-meow-mint" /></div>
            <div>
              <p className="font-bold">Telepon</p>
              <p className="text-sm text-meow-gray">{info.phone || "-"}</p>
              {info.whatsapp && (
                <a href={`https://wa.me/${info.whatsapp}`} target="_blank" rel="noreferrer" className="text-sm text-meow-green font-bold" data-testid="contact-whatsapp">
                  WhatsApp: +{info.whatsapp} <ExternalLink className="inline h-3 w-3" />
                </a>
              )}
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="h-10 w-10 rounded-2xl bg-meow-midnight text-meow-amber grid place-items-center">🐱</div>
            <div><p className="font-bold">Jam Operasional</p><p className="text-sm text-meow-gray">{info.operational_hours || "-"}</p></div>
          </div>
          <div className="flex gap-3 pt-3 border-t">
            {info.instagram && <a href={info.instagram} target="_blank" rel="noreferrer" className="p-2 bg-meow-bg rounded-full" data-testid="social-ig"><Instagram className="h-5 w-5" /></a>}
            {info.facebook && <a href={info.facebook} target="_blank" rel="noreferrer" className="p-2 bg-meow-bg rounded-full" data-testid="social-fb"><Facebook className="h-5 w-5" /></a>}
            {info.tiktok && <a href={info.tiktok} target="_blank" rel="noreferrer" className="p-2 bg-meow-bg rounded-full font-bold text-sm" data-testid="social-tt">TT</a>}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={send} className="bg-meow-midnight text-white rounded-[32px] p-6 md:p-8 space-y-3" data-testid="contact-form">
          <h3 className="font-heading font-extrabold text-2xl">Kirim Pesan</h3>
          <input required placeholder="Nama" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-4 py-3 rounded-2xl text-meow-midnight outline-none" data-testid="cf-name" />
          <div className="grid grid-cols-2 gap-2">
            <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="px-4 py-3 rounded-2xl text-meow-midnight outline-none" data-testid="cf-email" />
            <input placeholder="No HP" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="px-4 py-3 rounded-2xl text-meow-midnight outline-none" data-testid="cf-phone" />
          </div>
          <input placeholder="Subjek" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} className="w-full px-4 py-3 rounded-2xl text-meow-midnight outline-none" data-testid="cf-subject" />
          <textarea required rows={5} placeholder="Pesan kamu..." value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} className="w-full px-4 py-3 rounded-2xl text-meow-midnight outline-none" data-testid="cf-message" />
          <button type="submit" disabled={sending} className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-60" data-testid="cf-submit">
            <Send className="h-4 w-4" /> {sending ? "Mengirim..." : "Kirim Pesan"}
          </button>
        </form>
      </div>

      {/* FAQ */}
      <section className="mt-12" data-testid="contact-faqs">
        <h2 className="font-heading text-3xl font-extrabold mb-4">FAQ</h2>
        <div className="space-y-3">
          {faqs.map((f) => (
            <details key={f.id} className="bg-white rounded-3xl p-5 cursor-pointer" data-testid={`faq-${f.id}`}>
              <summary className="font-bold list-none flex justify-between items-center">
                <span>{f.question}</span>
                <span className="text-meow-salmon">＋</span>
              </summary>
              <p className="text-sm text-meow-gray mt-3 leading-relaxed">{f.answer}</p>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
};

export default ContactPage;
