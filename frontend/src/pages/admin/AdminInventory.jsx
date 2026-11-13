import React, { useCallback, useEffect, useState } from 'react';
import { api, apiError } from '../../lib/api';
import { toast } from 'sonner';

export default function AdminInventory() {
  const [items,setItems]=useState([]),[deleted,setDeleted]=useState([]),[editing,setEditing]=useState(null);
  const [kind,setKind]=useState('receipt_stock'),[quantity,setQuantity]=useState(''),[ttb,setTtb]=useState(''),[note,setNote]=useState('');
  const [q,setQ]=useState(''),[error,setError]=useState(''),[formError,setFormError]=useState(''),[loading,setLoading]=useState(true),[saving,setSaving]=useState(false);
  const load=useCallback(async()=>{
    setLoading(true);setError('');
    try {
      const {data}=await api.get('/admin/inventory');
      if(!Array.isArray(data.items)||!Array.isArray(data.deleted_items)){
        setItems([]);setDeleted([]);
        setError('Backend Inventory masih memakai versi lama. Restart backend secara manual, lalu muat ulang halaman ini.');return;
      }
      setItems(data.items);setDeleted(data.deleted_items);
    }
    catch(e){setError(apiError(e,'Inventory belum dapat dimuat.'));}
    finally{setLoading(false);}
  },[]);
  useEffect(()=>{load();window.addEventListener('focus',load);return()=>window.removeEventListener('focus',load);},[load]);
  const open=item=>{setEditing(item);setKind('receipt_stock');setQuantity('');setTtb('');setNote('');setFormError('');};
  const adjust=async event=>{
    event.preventDefault();if(saving)return;
    const amount=Number(quantity);
    if(!Number.isInteger(amount)||amount<1||amount>2147483647){setFormError('Jumlah harus bilangan bulat lebih dari nol.');return;}
    if(!ttb.trim()){setFormError('Nomor TTB wajib diisi.');return;}
    if(kind==='issue_stock'&&amount>editing.stock-editing.reserved){setFormError('Jumlah Issue Stock melebihi stok tersedia.');return;}
    setSaving(true);setFormError('');
    try {
      await api.post(`/admin/products/${editing.product_id}/stock`,{variant_id:editing.variant_id||null,adjustment_type:kind,quantity:amount,ttb_number:ttb.trim(),note});
      toast.success('Penyesuaian stok berhasil disimpan');setEditing(null);await load();
    }catch(e){setFormError(apiError(e,'Penyesuaian stok gagal. Silakan coba kembali.'));}
    finally{setSaving(false);}
  };
  const filter=rows=>rows.filter(row=>`${row.sku} ${row.name} ${row.variant_label}`.toLowerCase().includes(q.toLowerCase()));
  const table=(rows,archived=false)=><div className="bg-white rounded-3xl border border-zinc-200 overflow-x-auto">
    <table className="w-full text-sm" data-testid={archived?'inventory-deleted-table':'inventory-table'}>
      <thead className="bg-meow-bg text-xs uppercase tracking-wider text-meow-gray"><tr>
        {['SKU','Produk','Varian','Stok','Reserved','Tersedia','Status','Aksi'].map(title=><th key={title} className="text-left px-4 py-3 whitespace-nowrap">{title}</th>)}
      </tr></thead>
      <tbody>{rows.map((item,i)=>{
        const low=item.stock-item.reserved<=item.min_alert;
        const disabled=archived||item.can_adjust===false;
        return <tr key={`${item.product_id}-${item.variant_id||'initial'}`} aria-disabled={disabled} className={`border-t ${archived?'bg-zinc-100 text-zinc-400':low?'bg-red-50':''}`} data-testid={archived?`inv-deleted-row-${i}`:`inv-row-${i}`}>
          <td className="px-4 py-3 font-mono text-xs">{item.sku}</td><td className="px-4 py-3">{item.name}</td>
          <td className="px-4 py-3 text-xs">{item.variant_label}</td><td className="px-4 py-3 font-bold">{item.stock}</td>
          <td className="px-4 py-3">{item.reserved}</td><td className="px-4 py-3">{item.stock-item.reserved}{!archived&&low&&<span className="text-red-500 ml-1" title="Stok rendah">⚠</span>}</td>
          <td className="px-4 py-3 text-xs whitespace-nowrap">{archived?'Produk dihapus':item.variant_active===false?'Varian nonaktif':!item.variant_id?'Belum diinisialisasi':item.product_active===false?'Produk nonaktif':'Aktif'}</td>
          <td className="px-4 py-3"><button type="button" disabled={disabled||loading||saving} onClick={()=>open(item)} className="text-xs text-meow-salmon font-bold whitespace-nowrap disabled:text-zinc-400 disabled:cursor-not-allowed" data-testid={archived?`inv-deleted-adjust-${i}`:`inv-adjust-${i}`}>{archived?'Tidak tersedia':!item.variant_id?'Inisialisasi Stok':'Adjust'}</button></td>
        </tr>;
      })}</tbody>
    </table>
    {!rows.length&&<p className="p-6 text-center text-sm text-meow-gray">{loading?'Memuat inventory...':'Tidak ada item.'}</p>}
  </div>;
  return <div data-testid="admin-inventory" className="space-y-4">
    <div className="flex flex-wrap justify-between items-center gap-3"><h1 className="font-heading text-3xl font-black">Inventory</h1><button type="button" onClick={load} disabled={loading||saving} className="btn-secondary text-sm">Muat Ulang</button></div>
    <p className="text-sm text-meow-gray">Gunakan Receipt Stock untuk stok awal atau penambahan barang, dan Issue Stock untuk pengeluaran barang.</p>
    <input aria-label="Cari inventory" placeholder="Cari nama produk / SKU / varian" value={q} onChange={e=>setQ(e.target.value)} className="w-full max-w-md rounded-xl border bg-white px-4 py-2"/>
    {error&&<p role="alert" className="rounded-xl bg-red-50 text-red-700 p-4">{error}</p>}
    <section><h2 className="font-bold mb-3">Stok Produk ({filter(items).length})</h2>{table(filter(items))}</section>
    <section><h2 className="font-bold mb-2">Stok Produk yang Dihapus ({filter(deleted).length})</h2><p className="text-xs text-meow-gray mb-3">Data stok disimpan untuk riwayat. Baris abu-abu tidak dapat diubah.</p>{table(filter(deleted),true)}</section>
    {editing&&<div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={()=>!saving&&setEditing(null)}>
      <form onSubmit={adjust} onClick={e=>e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="stock-title" className="bg-white rounded-3xl p-6 max-w-md w-full max-h-[90dvh] overflow-y-auto space-y-3">
        <h3 id="stock-title" className="font-heading font-extrabold text-lg">Adjust Stok: {editing.name}</h3>
        <p className="text-xs text-meow-gray">{editing.sku} · Stok: {editing.stock} · Reserved: {editing.reserved} · Tersedia: {editing.stock-editing.reserved}</p>
        {formError&&<p role="alert" className="text-sm text-red-700">{formError}</p>}
        <label className="block text-sm font-semibold">Jenis Adjust Stock<select aria-label="Jenis Adjust Stock" required value={kind} disabled={saving} onChange={e=>setKind(e.target.value)} className="block w-full rounded-xl bg-meow-bg px-3 py-2 mt-1" data-testid="inv-kind"><option value="receipt_stock">Receipt Stock — Tambah stok</option><option value="issue_stock">Issue Stock — Kurangi stok</option></select></label>
        <label className="block text-sm font-semibold">Nomor TTB<input required maxLength={128} value={ttb} disabled={saving} onChange={e=>setTtb(e.target.value)} className="block w-full rounded-xl bg-meow-bg px-3 py-2 mt-1" data-testid="inv-ttb"/></label>
        <label className="block text-sm font-semibold">Jumlah<input required type="number" min="1" step="1" max={kind==='issue_stock'?editing.stock-editing.reserved:2147483647} value={quantity} disabled={saving} onChange={e=>setQuantity(e.target.value)} className="block w-full rounded-xl bg-meow-bg px-3 py-2 mt-1" data-testid="inv-quantity"/></label>
        <label className="block text-sm">Catatan (opsional)<textarea value={note} disabled={saving} onChange={e=>setNote(e.target.value)} className="block w-full rounded-xl bg-meow-bg px-3 py-2 mt-1" data-testid="inv-note"/></label>
        <div className="flex gap-2"><button type="button" disabled={saving} onClick={()=>setEditing(null)} className="btn-secondary flex-1">Batal</button><button disabled={saving} className="btn-primary flex-1" data-testid="inv-save">{saving?'Menyimpan...':'Simpan'}</button></div>
      </form>
    </div>}
  </div>;
}
