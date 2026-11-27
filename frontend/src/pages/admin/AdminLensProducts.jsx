import React, { useCallback, useEffect, useState } from 'react';
import { api, apiError, formatIDR } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import FormField from '../../components/FormField';
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';

const control='rounded-xl border bg-meow-bg px-3 py-2.5 text-sm';
const empty={lens_type:'clear',index_value:'1.61',additional_price:'',name:'',is_active:true,sort_order:0};
export default function AdminLensProducts(){
  const{user}=useAuth();const allowed=action=>user?.role!=='staff'||user.permissions?.includes(`product.${action}`);
  const[data,setData]=useState({version:0,types:[],items:[]}),[loading,setLoading]=useState(true),[error,setError]=useState('');
  const[form,setForm]=useState(null),[formError,setFormError]=useState(''),[saving,setSaving]=useState(false),[search,setSearch]=useState('');
  const load=useCallback(async()=>{setLoading(true);setError('');try{const{data}=await api.get('/admin/lens-products');setData(data);}catch(err){setError(apiError(err,'Daftar produk lensa belum dapat dimuat.'));}finally{setLoading(false);}},[]);
  useEffect(()=>{load();},[load]);
  const edit=item=>{const kind=item.lens_types?.length===1?item.lens_types[0].code:'';setForm({...empty,id:item.id,
    lens_type:data.types.some(type=>type.code===kind)?kind:'',index_value:item.index_value,additional_price:item.additional_price,
    name:item.name.replace(/^.+ · Indeks 1\.\d{2}(?: — )?/,''),is_active:item.is_active,sort_order:item.sort_order,version:data.version});setFormError('');};
  const save=async event=>{event.preventDefault();if(saving)return;setSaving(true);setFormError('');
    try{const{id,...body}=form;const{data}=id?await api.put(`/admin/lens-products/${encodeURIComponent(id)}`,body):await api.post('/admin/lens-products',body);setData(data);setForm(null);toast.success('Produk lensa disimpan');}
    catch(err){setFormError(apiError(err,'Produk lensa belum berhasil disimpan.'));}finally{setSaving(false);}};
  const remove=async item=>{if(!window.confirm(`Nonaktifkan ${item.name}? Riwayat pesanan tetap disimpan.`))return;setSaving(true);setError('');
    try{const{data:next}=await api.delete(`/admin/lens-products/${encodeURIComponent(item.id)}`,{params:{version:data.version}});setData(next);}catch(err){setError(apiError(err,'Produk lensa belum dapat dinonaktifkan.'));}finally{setSaving(false);}};
  return <div className="space-y-5" data-testid="admin-lens-products">
    <div className="flex flex-wrap justify-between gap-3"><div><h1 className="font-heading font-black text-3xl">Produk Lensa & Harga</h1><p className="mt-2 text-sm text-meow-gray">Satu entri untuk satu kombinasi jenis dan indeks. Contoh: Clear 1.61 dan UV420 1.61 dapat memiliki harga berbeda. Harga per produk untuk sepasang lensa; Paket tetap termasuk harga lensa.</p></div>
      <div className="flex gap-2"><button type="button" onClick={load} disabled={loading||saving} className="btn-secondary text-sm">Muat ulang</button>{allowed('create')&&<button type="button" disabled={loading||saving||!data.types.length} onClick={()=>{setForm({...empty,version:data.version});setFormError('');}} className="btn-primary text-sm">Tambah Produk Lensa</button>}</div></div>
    <p className="text-sm text-meow-gray">Jenis tambahan dapat dibuat melalui <a href="/admin/categories" className="underline">Master Kategori → Jenis Lensa</a>. Periksa dan klasifikasikan entri lama sebelum digunakan.</p>
    <FormField label="Cari nama, jenis, atau indeks lensa"><input type="search" value={search} onChange={event=>setSearch(event.target.value)} className={control}/></FormField>
    {error&&<p role="alert" className="text-red-600 text-sm">{error}</p>}{loading?<p role="status">Memuat produk lensa…</p>:<div className="overflow-x-auto rounded-2xl border bg-white"><table className="w-full text-sm"><caption className="sr-only">Daftar jenis, indeks, dan harga lensa</caption><thead><tr>{['Nama','Jenis','Indeks','Harga / produk','Status','Aksi'].map(label=><th key={label} className="p-3 text-left">{label}</th>)}</tr></thead><tbody>
      {data.items.filter(item=>`${item.name} ${item.index_value} ${item.lens_types.map(type=>type.name).join(' ')}`.toLowerCase().includes(search.toLowerCase())).map(item=><tr key={item.id} className="border-t"><td className="p-3">{item.name}</td><td className="p-3">{item.lens_types.length?item.lens_types.map(type=>type.name).join(', '):'Belum diklasifikasikan'}</td><td className="p-3">{item.index_value}</td><td className="p-3 whitespace-nowrap">{formatIDR(item.additional_price)}</td><td className="p-3">{item.is_active?'Aktif':'Nonaktif'}</td><td className="p-3"><div className="flex gap-3">{allowed('update')&&<button type="button" disabled={saving} onClick={()=>edit(item)} className="font-bold text-meow-salmon" aria-label={`Edit lensa ${item.name}`}>Edit</button>}{allowed('delete')&&item.is_active&&<button type="button" disabled={saving} onClick={()=>remove(item)} className="text-red-600">Nonaktifkan</button>}</div></td></tr>)}
    </tbody></table>{!data.items.length&&<p className="p-5 text-sm">Belum ada kombinasi lensa. Tambahkan jenis, indeks, dan harga jualnya.</p>}</div>}
    <Dialog open={!!form} onOpenChange={open=>{if(!open&&!saving)setForm(null);}}><DialogContent className="max-h-[90dvh] overflow-y-auto"><DialogTitle>{form?.id?'Edit Produk Lensa':'Tambah Produk Lensa'}</DialogTitle><DialogDescription>Harga kombinasi ini akan dipakai pada pilihan lensa detail produk.</DialogDescription>
      {form&&<form onSubmit={save} className="space-y-4" data-testid="lens-product-form"><fieldset disabled={saving} className="space-y-4">
        <FormField label="Jenis lensa"><select required value={form.lens_type} onChange={event=>setForm({...form,lens_type:event.target.value})} className={control}><option value="">Pilih jenis lensa</option>{data.types.map(type=><option key={type.code} value={type.code}>{type.name}</option>)}</select></FormField>
        <FormField label="Indeks lensa" hint="Format dua desimal, misalnya 1.61 atau 1.67."><input required pattern="1\.[0-9]{2}" list="lens-index-values" value={form.index_value} onChange={event=>setForm({...form,index_value:event.target.value})} className={control}/></FormField>
        <datalist id="lens-index-values">{['1.50','1.56','1.60','1.61','1.67','1.74'].map(value=><option key={value} value={value}/>)}</datalist>
        <FormField label="Harga lensa (Rp / produk)"><input required type="number" min={0} max={1000000000} step="0.01" value={form.additional_price} onChange={event=>setForm({...form,additional_price:event.target.value===''?'':Number(event.target.value)})} className={control}/></FormField>
        <FormField label="Keterangan nama (opsional)" hint="Misalnya nama merek atau seri; jenis dan indeks otomatis ditambahkan pada nama."><input value={form.name} maxLength={120} onChange={event=>setForm({...form,name:event.target.value})} className={control}/></FormField>
        <FormField label="Urutan tampilan"><input required type="number" min={0} max={9999} value={form.sort_order} onChange={event=>setForm({...form,sort_order:Number(event.target.value)})} className={control}/></FormField>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={event=>setForm({...form,is_active:event.target.checked})}/>Aktif</label>
      </fieldset>{formError&&<p role="alert" className="text-red-600 text-sm">{formError}</p>}<div className="flex gap-2"><button type="button" disabled={saving} onClick={()=>setForm(null)} className="btn-secondary flex-1">Batal</button><button type="submit" disabled={saving} className="btn-primary flex-1">{saving?'Menyimpan…':'Simpan'}</button></div></form>}
    </DialogContent></Dialog>
  </div>;
}
