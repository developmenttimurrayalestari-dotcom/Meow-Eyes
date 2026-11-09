import React, { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { AlertTriangle, Plus, Minus } from "lucide-react";
import { toast } from "sonner";

const AdminInventory = () => {
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const [delta, setDelta] = useState(0);
  const [note, setNote] = useState("");
  const load = () => api.get("/admin/inventory").then(({ data }) => setItems(data.items));
  useEffect(() => { load(); }, []);

  const adjust = async () => {
    try {
      await api.post(`/admin/products/${editing.product_id}/stock`, {
        variant_id: editing.sku ? items.find((x) => x.sku === editing.sku)?.variant_id : null,
        delta, note,
      });
      toast.success("Stok di-update");
      setEditing(null); setDelta(0); setNote(""); load();
    } catch (err) { toast.error("Gagal"); }
  };

  return (
    <div data-testid="admin-inventory">
      <h1 className="font-heading text-3xl font-black mb-4">Inventory</h1>
      <div className="bg-white rounded-3xl border border-zinc-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-meow-bg text-xs uppercase tracking-wider text-meow-gray">
            <tr>
              <th className="text-left px-4 py-3">SKU</th>
              <th className="text-left px-4 py-3">Produk</th>
              <th className="text-left px-4 py-3">Varian</th>
              <th className="text-right px-4 py-3">Stok</th>
              <th className="text-right px-4 py-3">Reserved</th>
              <th className="text-right px-4 py-3">Min Alert</th>
              <th className="text-right px-4 py-3">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it, i) => {
              const low = (it.stock - it.reserved) <= it.min_alert;
              return (
                <tr key={i} className={`border-t border-zinc-100 ${low ? "bg-red-50" : ""}`} data-testid={`inv-row-${i}`}>
                  <td className="px-4 py-3 font-mono text-xs">{it.sku}</td>
                  <td className="px-4 py-3">{it.name}</td>
                  <td className="px-4 py-3 text-xs">{it.variant_label}</td>
                  <td className="px-4 py-3 text-right font-bold">{it.stock}</td>
                  <td className="px-4 py-3 text-right">{it.reserved}</td>
                  <td className="px-4 py-3 text-right text-xs">{low && <AlertTriangle className="inline h-3 w-3 text-red-500" />}{it.min_alert}</td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => setEditing(it)} className="text-xs text-meow-salmon font-bold" data-testid={`inv-adjust-${i}`}>Adjust</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {editing && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={() => setEditing(null)}>
          <div className="bg-white rounded-3xl p-6 max-w-sm w-full" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-heading font-extrabold text-lg mb-2">Adjust Stok: {editing.name}</h3>
            <p className="text-xs text-meow-gray">{editing.variant_label} · stok saat ini: {editing.stock}</p>
            <input type="number" placeholder="Delta (+/-)" value={delta} onChange={(e) => setDelta(Number(e.target.value))} className="w-full mt-3 px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="inv-delta" />
            <input placeholder="Catatan" value={note} onChange={(e) => setNote(e.target.value)} className="w-full mt-2 px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="inv-note" />
            <div className="flex gap-2 mt-3">
              <button onClick={() => setEditing(null)} className="btn-secondary flex-1">Batal</button>
              <button onClick={adjust} className="btn-primary flex-1" data-testid="inv-save">Simpan</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminInventory;
