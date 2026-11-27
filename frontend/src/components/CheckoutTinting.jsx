import React, { useState } from 'react';
import { ChevronDown, Palette, X } from 'lucide-react';
import { api, apiError, formatIDR } from '../lib/api';
import FormField from './FormField';
import TintingSwatch, { TintingDetails, TINTING_GROUPS } from './TintingSwatch';

function TintingPicker({ item, colors, load, loading, loadError, onSaved, onDirtyChange, disabled }) {
  const [open,setOpen]=useState(false), [search,setSearch]=useState(''), [kind,setKind]=useState(''), [group,setGroup]=useState('');
  const [busy,setBusy]=useState(false), [error,setError]=useState(''), [pending,setPending]=useState(undefined);
  const current = pending === undefined ? item.tinting?.id || null : pending;
  const save = async tintingId => {
    if (busy || disabled) return;
    setBusy(true);setError('');setPending(tintingId);onDirtyChange(`tinting:${item.id}`,true);
    try {
      const {data}=await api.patch(`/cart/${encodeURIComponent(item.id)}/tinting`,{tinting_id:tintingId});
      onSaved(data.cart_item);setPending(undefined);onDirtyChange(`tinting:${item.id}`,false);
      setOpen(false);
    } catch (err) { setError(apiError(err,'Pilihan tinting belum berhasil disimpan. Coba simpan kembali.')); }
    finally { setBusy(false); }
  };
  const filtered=(colors || []).filter(color => (!kind || color.kind === kind) && (!group || color.group === group)
    && `${color.code} ${color.name}`.toLowerCase().includes(search.toLowerCase().trim()));
  return <div className="rounded-2xl border border-meow-midnight/10 p-4 space-y-3" data-testid={`tinting-${item.id}`}>
    <div className="flex items-start justify-between gap-3"><div><h3 className="font-bold text-sm">{item.product.name}</h3>
      <p className="text-xs text-meow-gray">{item.quantity > 1 ? `Satu warna berlaku untuk seluruh ${item.quantity} produk pada baris ini. Biaya dihitung × ${item.quantity}.` : 'Pilih satu warna tinting untuk produk ini (opsional).'}</p>
    </div>{item.tinting && <button type="button" onClick={()=>save(null)} disabled={disabled || busy} className="shrink-0 text-xs text-red-600 underline" aria-label={`Hapus tinting ${item.product.name}`}>Hapus tinting</button>}</div>
    <TintingDetails tinting={item.tinting} />
    <button type="button" disabled={disabled || busy} aria-expanded={open} onClick={()=>{setOpen(value=>!value);if (!colors && !loading) load();}}
      className="flex min-h-10 items-center gap-2 text-sm font-bold text-meow-salmon" data-testid={`choose-tinting-${item.id}`}>
      <Palette className="h-4 w-4" />{item.tinting ? 'Ganti warna tinting' : 'Pilih warna tinting'}<ChevronDown className={`h-4 w-4 ${open ? 'rotate-180' : ''}`} />
    </button>
    {open && <div className="space-y-3">
      <fieldset disabled={disabled || busy} className="grid sm:grid-cols-3 gap-3">
        <FormField label="Cari nama atau kode warna"><input type="search" value={search} onChange={event=>setSearch(event.target.value)} className="rounded-xl border px-3 py-2 text-sm" placeholder="Contoh: Black atau 04S" /></FormField>
        <FormField label="Jenis warna"><select value={kind} onChange={event=>setKind(event.target.value)} className="rounded-xl border px-3 py-2 text-sm"><option value="">Semua jenis</option><option value="solid">Solid</option><option value="gradient">Gradasi</option></select></FormField>
        <FormField label="Kelompok warna"><select value={group} onChange={event=>setGroup(event.target.value)} className="rounded-xl border px-3 py-2 text-sm"><option value="">Semua kelompok</option>{Object.entries(TINTING_GROUPS).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></FormField>
      </fieldset>
      {loading && <p role="status" className="text-sm">Memuat warna tinting…</p>}
      {loadError && <p role="alert" className="text-sm text-red-600">{loadError} <button type="button" onClick={load} disabled={loading} className="underline">Coba lagi</button></p>}
      {colors && <fieldset disabled={disabled || busy} className="min-w-0"><legend className="mb-2 text-xs font-semibold">Pilihan warna ({filtered.length})</legend>
        {!filtered.length && <p className="text-sm text-meow-gray">Tidak ada warna yang sesuai pencarian.</p>}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-[30rem] overflow-y-auto p-0.5">
          {filtered.map(color=><label key={color.id} className={`cursor-pointer rounded-2xl border p-3 space-y-3 ${current===color.id ? 'border-meow-salmon bg-meow-salmon/5 ring-1 ring-meow-salmon' : 'border-meow-midnight/10 bg-white'}`}>
            <div className="flex items-center justify-between gap-2"><input type="radio" name={`tinting-${item.id}`} checked={current===color.id} onChange={()=>save(color.id)} className="shrink-0" /><span className="min-w-0 break-all text-xs font-semibold">{color.code}</span></div>
            <TintingSwatch color={color}/><span className="block text-xs font-bold">{color.name}</span>
            <span className="block text-xs text-meow-gray">{color.kind==='gradient'?'Gradasi':'Solid'} · {TINTING_GROUPS[color.group]}</span>
            <span className="block text-sm font-bold text-meow-salmon">+ <span className="conveythis-no-translate notranslate" translate="no">{formatIDR(color.additional_price)}</span></span>
          </label>)}
        </div>
      </fieldset>}
    </div>}
    {busy && <p role="status" className="text-xs">Menyimpan tinting dan memperbarui harga…</p>}
    {error && <div role="alert" className="text-sm text-red-600 space-y-2"><p>{error}</p><div className="flex gap-4"><button type="button" onClick={()=>save(pending)} disabled={disabled || busy} className="underline">Coba simpan lagi</button><button type="button" onClick={()=>save(null)} disabled={disabled || busy} className="underline flex items-center gap-1"><X size={13}/>Tanpa tinting</button></div></div>}
  </div>;
}

export default function CheckoutTinting({ items, onSaved, onDirtyChange, disabled }) {
  const [colors,setColors]=useState(null), [loading,setLoading]=useState(false), [error,setError]=useState('');
  const load = async () => {
    if (loading) return;
    setLoading(true);setError('');
    try { const {data}=await api.get('/tinting');setColors(data.items || []); }
    catch(err) { setError(apiError(err,'Warna tinting belum dapat dimuat.')); }
    finally { setLoading(false); }
  };
  const eligible=items.filter(item=>['frame','lens','package'].includes(item.product.product_type) && item.product.sale_role!=='add_on');
  if (!eligible.length) return null;
  return <section className="bg-white rounded-3xl p-5 md:p-6 space-y-4" data-testid="checkout-tinting">
    <div><h2 className="font-heading font-extrabold text-xl flex items-center gap-2"><Palette className="h-5 w-5 text-meow-salmon"/>Tinting Lensa (Opsional)</h2>
      <p className="mt-1 text-sm text-meow-gray">Tambahkan warna solid atau gradasi untuk masing-masing item. Biaya tinting dihitung terpisah dari lensa dan Add On, per produk untuk sepasang lensa.</p>
      <p className="mt-1 text-xs text-meow-gray">Warna layar merupakan ilustrasi; hasil lensa dapat berbeda karena pencahayaan, bahan lensa, dan coating.</p></div>
    {eligible.map(item=><TintingPicker key={item.id} item={item} colors={colors} load={load} loading={loading} loadError={error} onSaved={onSaved} onDirtyChange={onDirtyChange} disabled={disabled}/>)}
  </section>;
}
