import React, { useEffect, useState } from "react";
import { api, apiError } from "../lib/api";
import { MapPin, Plus, Trash2, Check } from "lucide-react";
import { toast } from "sonner";
import AddressForm from "../components/AddressForm";

const AddressesPage = () => {
  const [items, setItems] = useState([]);
  const [show, setShow] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [error, setError] = useState("");
  const fetchData = () => api.get("/addresses").then(({ data }) => { setItems(data.addresses); setError(""); }).catch((err) => setError(apiError(err)));
  useEffect(() => { fetchData(); }, []);
  const remove = async (id) => {
    try { await api.delete(`/addresses/${id}`); fetchData(); } catch (err) { toast.error(apiError(err)); }
  };
  const setDefault = async (id) => {
    try { await api.patch(`/addresses/${id}/default`); fetchData(); } catch (err) { toast.error(apiError(err)); }
  };
  return (
    <div className="max-w-3xl mx-auto px-4 md:px-6 py-8" data-testid="addresses-page">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-3xl md:text-4xl font-black">Alamat Saya</h1>
        <button onClick={() => { setEditingAddress(null); setShow(!show); }} className="btn-primary text-sm" data-testid="add-address-btn">
          <Plus className="inline h-4 w-4 mr-1" /> Tambah
        </button>
      </div>
      {show && <div className="bg-white rounded-3xl p-6 mb-4"><AddressForm key={editingAddress?.id || 'new'} initialAddress={editingAddress} onCancel={() => { setShow(false); setEditingAddress(null); }} onSaved={() => { setShow(false); setEditingAddress(null); fetchData(); }} defaultAddress={!items.length} /></div>}
      {error && <p role="alert" className="text-red-600 mb-4">{error}</p>}
      {items.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center"><MapPin className="h-10 w-10 mx-auto text-meow-midnight/30" /><p className="mt-2 font-bold">Belum ada alamat</p></div>
      ) : (
        <div className="space-y-3">
          {items.map((a) => (
            <div key={a.id} className="bg-white rounded-3xl p-5 flex items-start gap-4" data-testid={`address-card-${a.id}`}>
              <MapPin className="h-5 w-5 text-meow-salmon mt-0.5" />
              <div className="flex-1">
                <p className="font-bold">{a.label} · {a.recipient}</p>
                <p className="text-sm text-meow-gray">{a.phone}</p>
                <p className="text-sm text-meow-gray">{[a.street, a.subdistrict, a.district, a.city, a.province, a.postal_code].filter(Boolean).join(', ')}</p>
                {a.is_default && <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded-full bg-meow-mint/20 text-meow-mint font-bold">Default</span>}
              </div>
              <div className="flex flex-col gap-2">
                <button type="button" onClick={() => { setEditingAddress(a); setShow(true); }} className="text-xs font-bold text-meow-salmon" data-testid={`edit-address-${a.id}`}>Ubah</button>
                {!a.is_default && <button onClick={() => setDefault(a.id)} className="text-xs font-bold text-meow-mint" data-testid={`set-default-${a.id}`}><Check className="h-3 w-3 inline" /> Set Default</button>}
                <button onClick={() => remove(a.id)} className="text-xs text-red-500" data-testid={`del-address-${a.id}`}><Trash2 className="h-3 w-3 inline" /> Hapus</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AddressesPage;
