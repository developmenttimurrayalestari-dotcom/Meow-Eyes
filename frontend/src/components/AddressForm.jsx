import React, { useState } from "react";
import { api, apiError } from "../lib/api";
import { toast } from "sonner";

export default function AddressForm({ onSaved, onCancel, defaultAddress = false }) {
  const [form, setForm] = useState({ label: "Rumah", recipient: "", phone: "", street: "", city: "", province: "", district: "", subdistrict: "", postal_code: "", is_default: defaultAddress });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const save = async (event) => {
    event.preventDefault(); setSaving(true); setError("");
    try {
      const payload = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, typeof value === "string" ? value.trim() : value]));
      const { data } = await api.post("/addresses", payload);
      toast.success("Alamat tersimpan"); onSaved(data.address);
    } catch (err) { setError(apiError(err, "Alamat belum berhasil disimpan.")); }
    finally { setSaving(false); }
  };
  return <form onSubmit={save} className="space-y-3 text-sm" data-testid="address-form">
    <fieldset disabled={saving} className="grid sm:grid-cols-2 gap-3">
      {[
        ["label", "Label alamat", "Rumah / Kantor", "off"],
        ["recipient", "Nama penerima", "Nama lengkap", "shipping name"],
        ["phone", "Nomor telepon", "08…", "shipping tel"],
        ["postal_code", "Kode pos", "5 digit kode pos", "shipping postal-code"],
        ["province", "Provinsi", "Provinsi", "shipping address-level1"],
        ["city", "Kota / Kabupaten", "Kota / Kabupaten", "shipping address-level2"],
        ["district", "Kecamatan (opsional)", "Kecamatan", "shipping address-level3"],
        ["subdistrict", "Kelurahan / Desa (opsional)", "Kelurahan / Desa", "shipping address-level4"],
      ].map(([key, label, placeholder, autoComplete]) => <label key={key} className="block text-xs font-semibold">
        {label}
        <input required={!["district", "subdistrict"].includes(key)} type={key === "phone" ? "tel" : "text"} inputMode={key === "postal_code" ? "numeric" : undefined}
          pattern={key === "postal_code" ? "[0-9]{5}" : undefined} maxLength={key === "postal_code" ? 5 : key === "phone" ? 32 : 255}
          name={key} autoComplete={autoComplete} value={form[key]} onChange={(event) => set(key, event.target.value)} placeholder={placeholder}
          className="block w-full mt-1 px-3 py-2.5 rounded-xl bg-meow-bg border border-meow-midnight/10 focus:border-meow-salmon outline-none" data-testid={`addr-${key}`} />
      </label>)}
      <label className="sm:col-span-2 block text-xs font-semibold">Alamat lengkap
        <textarea required name="street" autoComplete="shipping street-address" value={form.street} onChange={(event) => set("street", event.target.value)} rows={2} maxLength={2000}
          placeholder="Nama jalan, nomor rumah, RT/RW, dan petunjuk pengiriman"
          className="block w-full mt-1 px-3 py-2.5 rounded-xl bg-meow-bg border border-meow-midnight/10 focus:border-meow-salmon outline-none" data-testid="addr-street" />
      </label>
      <label className="sm:col-span-2 flex items-center gap-2 text-xs"><input type="checkbox" checked={form.is_default} onChange={(event) => set("is_default", event.target.checked)} /> Jadikan alamat utama</label>
    </fieldset>
    {error && <p role="alert" className="text-red-600">{error}</p>}
    <div className="flex gap-2">
      <button type="button" onClick={onCancel} disabled={saving} className="flex-1 btn-secondary py-2">Batal</button>
      <button type="submit" disabled={saving} className="flex-1 btn-primary py-2 disabled:opacity-50" data-testid="addr-save">{saving ? "Menyimpan…" : "Simpan Alamat"}</button>
    </div>
  </form>;
}
