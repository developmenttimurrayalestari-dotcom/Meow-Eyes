import React from "react";
import { FileBarChart, Download } from "lucide-react";
import { API_BASE } from "../../lib/api";

const REPORTS = [
  { key: "sales", label: "Laporan Penjualan", desc: "Order, voucher, poin, total bayar" },
  { key: "inventory", label: "Laporan Inventory", desc: "Stok semua produk dan varian" },
  { key: "flash-sales", label: "Laporan Flash Sale", desc: "Performa flash sale + revenue" },
  { key: "roulette", label: "Laporan Roulette", desc: "Riwayat spin, reward, status" },
  { key: "games", label: "Laporan Mini Games", desc: "Skor & poin yang dibagikan" },
  { key: "newsletter", label: "Subscriber Newsletter", desc: "Daftar subscriber aktif" },
  { key: "users", label: "Laporan Pelanggan", desc: "Daftar user & metadata" },
  { key: "points", label: "Laporan Poin", desc: "Earn / redeem / refund poin" },
];

const AdminReports = () => {
  const download = (key) => {
    const token = localStorage.getItem("meow_token");
    fetch(`${API_BASE}/admin/export/${key}`, {
      headers: { Authorization: `Bearer ${token}` },
      credentials: "include",
    }).then((r) => r.blob()).then((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `${key}-${Date.now()}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    });
  };

  return (
    <div data-testid="admin-reports">
      <h1 className="font-heading text-3xl font-black mb-1 flex items-center gap-2"><FileBarChart /> Laporan & Export</h1>
      <p className="text-sm text-meow-gray mb-6">Unduh laporan Excel langsung dari server.</p>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {REPORTS.map((r) => (
          <div key={r.key} className="bg-white rounded-3xl border border-zinc-200 p-5" data-testid={`report-card-${r.key}`}>
            <p className="font-heading font-extrabold text-lg">{r.label}</p>
            <p className="text-sm text-meow-gray mt-1">{r.desc}</p>
            <button onClick={() => download(r.key)} className="btn-primary text-sm mt-4 inline-flex items-center gap-1" data-testid={`download-${r.key}`}>
              <Download className="h-4 w-4" /> Unduh Excel
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AdminReports;
