import React, { useEffect, useState } from "react";
import { api, apiError, formatIDR } from "../lib/api";
import { Link } from 'react-router-dom';
import { Ticket, Copy } from "lucide-react";
import { toast } from "sonner";

const VouchersPage = () => {
  const [vouchers, setVouchers] = useState([]);
  useEffect(() => {
    api.get("/vouchers/active").then(({ data }) => setVouchers(data.vouchers));
  }, []);
  const copyCode = (code) => {
    navigator.clipboard?.writeText(code).then(() => toast.success(`Kode ${code} disalin`)).catch(() => toast.info(`Gunakan kode ${code} di checkout`));
  };
  const claim = async v => {
    try { await api.post(`/vouchers/${v.id}/claim`); setVouchers(current => current.map(item => item.id === v.id ? { ...item, claimed: true } : item)); toast.success(`Voucher diklaim. Kode: ${v.code}`); }
    catch (err) { toast.error(apiError(err)); }
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
              {v.audience === 'new_member' && <p className="text-xs text-amber-700 mt-1">Member baru · Email terverifikasi · Transaksi pertama · Sekali per akun</p>}
              {v.eligibility_reason && <p className="text-xs text-red-600 mt-1">{v.eligibility_reason} <Link to="/profile" className="underline">Buka Profil</Link></p>}
              <p className="text-xs text-meow-gray">
                {v.discount_type === "percent" ? `${v.discount_value}% diskon, max ${formatIDR(v.max_discount || 0)}` :
                 v.discount_type === "nominal" ? `Potongan ${formatIDR(v.discount_value)}` :
                 "Gratis ongkir"}
                {" · Min "}{formatIDR(v.min_purchase || 0)}
              </p>
              <p className="text-xs text-meow-gray mt-1">Berlaku s/d {v.end_at.slice(0, 10)}</p>
            </div>
            <button disabled={v.eligible === false} onClick={() => v.audience === 'new_member' && !v.claimed ? claim(v) : copyCode(v.code)} className="px-3 py-2 bg-meow-midnight text-white rounded-full text-xs font-bold flex items-center gap-1 disabled:opacity-40" data-testid={`copy-voucher-${v.code}`}>
              {v.audience === 'new_member' && !v.claimed ? 'Klaim Voucher' : v.code} <Copy className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default VouchersPage;
