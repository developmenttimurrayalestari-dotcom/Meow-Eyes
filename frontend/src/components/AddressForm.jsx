import React, { useState } from "react";
import { api, apiError } from "../lib/api";
import { toast } from "sonner";
import EverproRegionFields from './EverproRegionFields';

export default function AddressForm({ onSaved, onCancel, defaultAddress = false, initialAddress = null }) {
  const [form, setForm] = useState({ label: initialAddress?.label || 'Rumah', recipient: initialAddress?.recipient || '', phone: initialAddress?.phone || '', street: initialAddress?.street || '', is_default: initialAddress?.is_default ?? defaultAddress });
  const [region, setRegion] = useState({ province_id: '', city_id: '', district_id: '', subdistrict_id: '', postal_code: '' });
  const ready = ['province_id', 'city_id', 'district_id', 'subdistrict_id'].every(key => region[key]) && /^\d{5}$/.test(region.postal_code);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const save = async (event) => {
    event.preventDefault(); if (!ready || saving) { setError('Pilih provinsi sampai kelurahan/desa dari data EVERPRO.'); return; } setSaving(true); setError("");
    try {
      const payload = { ...Object.fromEntries(Object.entries(form).map(([key, value]) => [key, typeof value === "string" ? value.trim() : value])),
        ...Object.fromEntries(['province', 'city', 'district', 'subdistrict', 'postal_code'].map(key => [key, region[key]])), everpro_destination_id: region.subdistrict_id,
        everpro_location: Object.fromEntries(['province_id', 'city_id', 'district_id', 'subdistrict_id'].map(key => [key, region[key]])) };
      const { data } = initialAddress ? await api.patch('/addresses/' + encodeURIComponent(initialAddress.id), payload) : await api.post("/addresses", payload);
      toast.success(initialAddress ? 'Alamat diperbarui' : "Alamat tersimpan"); onSaved(data.address);
    } catch (err) { setError(apiError(err, "Alamat belum berhasil disimpan.")); }
    finally { setSaving(false); }
  };
  return <form onSubmit={save} className="space-y-3 text-sm" data-testid="address-form">
    <fieldset disabled={saving} className="grid sm:grid-cols-2 gap-3">
      {[
        ["label", "Label alamat", "Rumah / Kantor", "off"],
        ["recipient", "Nama penerima", "Nama lengkap", "shipping name"],
        ["phone", "Nomor telepon", "08…", "shipping tel"],
      ].map(([key, label, placeholder, autoComplete]) => <label key={key} className="block text-xs font-semibold">
        {label}
        <input required type={key === "phone" ? "tel" : "text"}
          pattern={key === 'phone' ? '(?:\\+?62|08)[0-9]{8,12}' : undefined} minLength={key === 'recipient' ? 3 : 1} maxLength={key === 'phone' ? 15 : key === 'label' ? 100 : 255}
          name={key} autoComplete={autoComplete} value={form[key]} onChange={(event) => set(key, event.target.value)} placeholder={placeholder}
          className="block w-full mt-1 px-3 py-2.5 rounded-xl bg-meow-bg border border-meow-midnight/10 focus:border-meow-salmon outline-none" data-testid={`addr-${key}`} />
      </label>)}
      <EverproRegionFields value={region} onChange={setRegion} initialAddress={initialAddress}/>
      <label className="sm:col-span-2 block text-xs font-semibold">Alamat lengkap
        <textarea required name="street" autoComplete="shipping street-address" value={form.street} onChange={(event) => set("street", event.target.value)} rows={2} minLength={3} maxLength={250}
          placeholder="Nama jalan, nomor rumah, RT/RW, dan petunjuk pengiriman"
          className="block w-full mt-1 px-3 py-2.5 rounded-xl bg-meow-bg border border-meow-midnight/10 focus:border-meow-salmon outline-none" data-testid="addr-street" />
      </label>
      <label className="sm:col-span-2 flex items-center gap-2 text-xs"><input type="checkbox" checked={form.is_default} onChange={(event) => set("is_default", event.target.checked)} /> Jadikan alamat utama</label>
    </fieldset>
    {error && <p role="alert" className="text-red-600">{error}</p>}
    <div className="flex gap-2">
      <button type="button" onClick={onCancel} disabled={saving} className="flex-1 btn-secondary py-2">Batal</button>
      <button type="submit" disabled={saving || !ready} className="flex-1 btn-primary py-2 disabled:opacity-50" data-testid="addr-save">{saving ? "Menyimpan…" : initialAddress ? 'Simpan Perubahan' : "Simpan Alamat"}</button>
    </div>
  </form>;
}
