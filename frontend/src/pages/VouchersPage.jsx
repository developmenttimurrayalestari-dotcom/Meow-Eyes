import React, { useEffect, useState } from "react";
import { api, formatIDR } from "../lib/api";
import { Ticket, Copy } from "lucide-react";
import { toast } from "sonner";

const VouchersPage = () => {
  const [vouchers, setVouchers] = useState([]);
  useEffect(() => {
    api.get("/vouchers/active").then(({ data }) => setVouchers(data.vouchers));
  }, []);
  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    toast.success(`Kode ${code} disalin`);
  };
  return (
    <div className="max-w-3xl mx-auto px-4 md:px-6 py-8" data-testid="vouchers-page">
      <div className="text-center mb-6">
        <Ticket className="h-10 w-10 mx-auto text-meow-amber" />
        <h1 className="font-heading text-3xl md:text-4xl font-black mt-2">Voucher Aktif</h1>
        <p className="text-meow-gray text-sm mt-1">Salin kode dan pakai saat checkout.</p>
      </div>
      <div className="space-y-3">
        {vouchers.map((v) => (
          <div key={v.id} className="bg-white rounded-3xl p-5 flex items-center gap-4" data-testid={`voucher-${v.code}`}>
            <div className="h-14 w-14 rounded-2xl bg-meow-amber/20 grid place-items-center text-meow-amber">
              <Ticket className="h-6 w-6" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-heading font-extrabold">{v.name}</p>
              <p className="text-xs text-meow-gray">
                {v.discount_type === "percent" ? `${v.discount_value}% diskon, max ${formatIDR(v.max_discount || 0)}` :
                 v.discount_type === "nominal" ? `Potongan ${formatIDR(v.discount_value)}` :
                 "Gratis ongkir"}
                {" · Min "}{formatIDR(v.min_purchase || 0)}
              </p>
              <p className="text-xs text-meow-gray mt-1">Berlaku s/d {v.end_at.slice(0, 10)}</p>
            </div>
            <button onClick={() => copyCode(v.code)} className="px-3 py-2 bg-meow-midnight text-white rounded-full text-xs font-bold flex items-center gap-1" data-testid={`copy-voucher-${v.code}`}>
              {v.code} <Copy className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default VouchersPage;
