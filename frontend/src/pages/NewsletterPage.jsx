import React, { useEffect, useState } from "react";
import { api, imageSrc } from "../lib/api";
import { Mail, BellRing } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../contexts/AuthContext";

const NewsletterPage = () => {
  const { user } = useAuth();
  const [email, setEmail] = useState("");
  const [subs, setSubs] = useState([]);
  useEffect(() => {
    if (user?.email) setEmail(user.email);
    if (user) {
      api.get("/product-subscriptions").then(({ data }) => setSubs(data.items));
    }
  }, [user]);
  const subscribe = async (e) => {
    e.preventDefault();
    await api.post("/newsletter/subscribe", { email });
    toast.success("Berhasil subscribe newsletter!");
  };
  return (
    <div className="max-w-3xl mx-auto px-4 md:px-6 py-8" data-testid="newsletter-page">
      <div className="bg-meow-midnight text-white rounded-[32px] p-8">
        <Mail className="h-10 w-10 text-meow-amber" />
        <h1 className="font-heading text-3xl md:text-4xl font-black mt-3">Newsletter Meow Eyes</h1>
        <p className="text-white/70 mt-2 text-sm">Update flash sale, koleksi baru, dan reward eksklusif.</p>
        <form onSubmit={subscribe} className="flex flex-col sm:flex-row gap-3 mt-5">
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="flex-1 rounded-full px-5 py-3 outline-none text-meow-midnight" placeholder="email@kamu.com" data-testid="newsletter-page-email" />
          <button type="submit" className="btn-primary" data-testid="newsletter-page-submit">Subscribe</button>
        </form>
      </div>
      {user && (
        <div className="mt-8">
          <h2 className="font-heading text-2xl font-extrabold mb-3 flex items-center gap-2"><BellRing className="h-5 w-5 text-meow-salmon" /> Produk yang Disubscribe</h2>
          {subs.length === 0 ? (
            <p className="bg-white rounded-3xl p-6 text-center text-meow-gray">Belum ada produk yang kamu subscribe.</p>
          ) : (
            <div className="bg-white rounded-3xl divide-y divide-meow-midnight/5">
              {subs.map((s) => (
                <div key={s.id} className="p-4 flex items-center gap-3" data-testid={`prodsub-${s.product.id}`}>
                  <img src={imageSrc(s.product.main_image)} alt="" className="h-12 w-12 rounded-xl object-cover" />
                  <p className="font-bold text-sm">{s.product.name}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NewsletterPage;
