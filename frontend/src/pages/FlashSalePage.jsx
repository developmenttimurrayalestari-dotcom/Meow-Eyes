import React, { useEffect, useState } from "react";
import { Clock3, Zap } from "lucide-react";
import { api } from "../lib/api";
import ProductsPage from "./ProductsPage";

export default function FlashSalePage() {
  const [campaigns, setCampaigns] = useState([]);
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    let active = true;
    const load = () => api.get("/flash-sales/active").then(({ data }) => { if (active) setCampaigns(data.flash_sales || []); }).catch(() => {});
    load();
    const clock = window.setInterval(() => setNow(Date.now()), 1000);
    const refresh = window.setInterval(load, 60000);
    return () => { active = false; clearInterval(clock); clearInterval(refresh); };
  }, []);
  return (
    <ProductsPage title="Flash Sale" badge="flashsale" intro="Harga spesial untuk produk dalam promo yang sedang berlangsung. Harga dan sisa kuota diperiksa kembali saat checkout.">
      <div className="grid md:grid-cols-2 gap-3 mb-6" data-testid="flash-sale-campaigns">
        {campaigns.filter((campaign) => new Date(campaign.end_at).getTime() > now).map((campaign) => {
          const seconds = Math.max(0, Math.floor((new Date(campaign.end_at).getTime() - now) / 1000));
          return <div key={campaign.id} className="rounded-2xl bg-meow-salmon/10 border border-meow-salmon/20 p-4 flex flex-wrap items-center gap-3">
            <Zap className="h-5 w-5 text-meow-salmon" />
            <span className="font-bold flex-1">{campaign.name || campaign.title || "Promo Flash Sale"}</span>
            <span className="flex items-center gap-1.5 text-xs font-mono" aria-label="Sisa waktu promo"><Clock3 className="h-4 w-4" />
              {Math.floor(seconds / 3600)}j {Math.floor((seconds % 3600) / 60)}m {seconds % 60}d
            </span>
          </div>;
        })}
      </div>
    </ProductsPage>
  );
}
