import React, { useEffect, useState } from 'react';
import { api, apiError } from '../../lib/api';
import FormField from '../../components/FormField';
import EverproRegionFields from '../../components/EverproRegionFields';
import { inputClass } from './adminUtils';

export default function ShippingOriginForm({ onSaved }) {
  const [form, setForm] = useState(null), [initial, setInitial] = useState(null);
  const [error, setError] = useState(''), [message, setMessage] = useState(''), [busy, setBusy] = useState(false);
  const load = async () => {
    setError('');
    try {
      const {data} = await api.get('/admin/shipping-origin');
      const value = {province_id:'', city_id:'', district_id:'', subdistrict_id:'', province:'', city:'', district:'', ...data.origin};
      setForm(value); setInitial(value);
    } catch (e) { setError(apiError(e, 'Alamat asal belum dapat dimuat.')); }
  };
  useEffect(() => { void load(); }, []);
  const save = async event => {
    event.preventDefault(); setBusy(true); setError(''); setMessage('');
    try {
      const {data} = await api.put('/admin/shipping-origin', form);
      setForm(data.origin); setInitial(data.origin); setMessage('Alamat asal pengiriman disimpan. Ongkir baru memakai alamat ini.');
      onSaved?.();
    } catch (e) { setError(apiError(e, 'Alamat asal belum berhasil disimpan.')); }
    finally { setBusy(false); }
  };
  return <section className="rounded-3xl border bg-white p-6 space-y-4" data-testid="shipping-origin-form">
    <h2 className="text-xl font-bold">Alamat Asal Pengiriman</h2>
    <p className="text-sm text-meow-gray">Khusus superadmin. Pilih lokasi toko/gudang tempat barang dikirim. Pesanan yang sudah dibuat memakai alamat asal yang tersimpan pada pesanannya.</p>
    {error && <p role="alert" className="text-sm text-red-600">{error} <button type="button" onClick={load} className="underline">Muat ulang</button></p>}
    {message && <p role="status" className="text-sm text-emerald-700">{message}</p>}
    {!form ? !error && <p role="status">Memuat alamat asal...</p> : <form onSubmit={save}>
      <fieldset disabled={busy} className="grid sm:grid-cols-2 gap-4">
        {[['name','Nama pengirim / toko','text'], ['phone','Telepon pengirim','tel'], ['email','Email pengirim (opsional)','email']].map(([key,label,type]) => <FormField key={key} label={label}><input className={inputClass} type={type} required={key !== 'email'} value={form[key] || ''} maxLength={key === 'phone' ? 15 : key === 'name' ? 100 : 254} onChange={e => setForm({...form,[key]:e.target.value})} /></FormField>)}
        <EverproRegionFields value={form} onChange={next => setForm(previous => next.subdistrict_id !== previous.subdistrict_id ? {...next, latitude:null, longitude:null} : next)} initialAddress={initial} />
        <FormField label="Alamat lengkap pengirim" hint="Jalan, nomor bangunan, RT/RW, serta patokan toko/gudang." className="sm:col-span-2"><textarea required minLength={3} maxLength={250} className={inputClass} rows={3} value={form.address || ''} onChange={e => setForm({...form,address:e.target.value})} /></FormField>
        {[['latitude','Latitude',-90,90],['longitude','Longitude',-180,180]].map(([key,label,min,max]) => <FormField key={key} label={`${label} (opsional)`} hint="Isi kedua koordinat untuk layanan Instant/Sameday."><input className={inputClass} type="number" min={min} max={max} step="any" value={form[key] ?? ''} onChange={e => setForm({...form,[key]:e.target.value === '' ? null : Number(e.target.value)})} /></FormField>)}
        <button type="submit" className="btn-primary sm:col-span-2">{busy ? 'Menyimpan...' : 'Simpan alamat asal'}</button>
      </fieldset>
    </form>}
  </section>;
}
