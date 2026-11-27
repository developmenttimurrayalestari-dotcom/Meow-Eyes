import React, { useCallback, useEffect, useState } from 'react';
import { Palette, Plus, RefreshCw } from 'lucide-react';
import { api, apiError, formatIDR } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import FormField from '../../components/FormField';
import TintingSwatch, { TINTING_GROUPS } from '../../components/TintingSwatch';
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';

const control='w-full rounded-xl border border-meow-midnight/10 bg-meow-bg px-3 py-2.5 text-sm';
const empty={code:'',name:'',kind:'solid',group:'fashion',hex_color:'#808080',mid_hex_color:null,bottom_hex_color:'#FFFFFF',
  additional_price:60000,is_active:true,requires_sample:false,source_note:'',sort_order:0};

function HexField({label,value,onChange}) {
  return <div className="flex items-end gap-2"><label className="block shrink-0 space-y-1 text-xs font-semibold">Palet<input type="color" aria-label={`Pilih ${label.toLowerCase()}`} value={/^#[\da-f]{6}$/i.test(value || '')?value:'#FFFFFF'} onChange={event=>onChange(event.target.value.toUpperCase())} className="mb-0.5 block h-11 w-12 rounded-lg border bg-white p-1"/></label>
    <FormField label={label} hint="HEX #RRGGBB; kosongkan bila belum tersedia."><input value={value || ''} maxLength={7} pattern="#[0-9A-Fa-f]{6}" placeholder="#A1B2C3" onChange={event=>onChange(event.target.value || null)} className={control}/></FormField></div>;
}

export default function AdminTinting() {
  const {user}=useAuth();
  const permission=key=>user?.role!=='staff'||user.permissions?.includes(`product.${key}`);
  const [items,setItems]=useState([]),[version,setVersion]=useState(0),[loading,setLoading]=useState(true),[loaded,setLoaded]=useState(false),[error,setError]=useState('');
  const [editing,setEditing]=useState(null),[saving,setSaving]=useState(false),[formError,setFormError]=useState('');
  const [search,setSearch]=useState(''),[kind,setKind]=useState(''),[group,setGroup]=useState('');
  const apply=useCallback(data=>{setItems(data.items);setVersion(data.version);},[]);
  const load=useCallback(async()=>{setLoading(true);setError('');try{const {data}=await api.get('/admin/tinting');apply(data);setLoaded(true);}catch(err){setError(apiError(err,'Master tinting belum dapat dimuat.'));}finally{setLoading(false);}},[apply]);
  useEffect(()=>{load();},[load]);
  const edit=item=>{setEditing({...item,version});setFormError('');};
  const set=(key,value)=>setEditing(previous=>({...previous,[key]:value}));
  const save=async event=>{
    event.preventDefault();if(saving)return;setSaving(true);setFormError('');
    try{const {id,...body}=editing;const {data}=id?await api.put(`/admin/tinting/${encodeURIComponent(id)}`,body):await api.post('/admin/tinting',body);apply(data);setEditing(null);toast.success('Warna tinting disimpan');}
    catch(err){setFormError(apiError(err,'Warna tinting belum berhasil disimpan.'));}finally{setSaving(false);}
  };
  const remove=async item=>{
    if(!window.confirm(`Hapus warna ${item.code} — ${item.name}? Riwayat tinting pesanan tetap disimpan.`))return;
    setSaving(true);setError('');try{const {data}=await api.delete(`/admin/tinting/${encodeURIComponent(item.id)}`,{params:{version}});apply(data);toast.success('Warna tinting dihapus');}
    catch(err){setError(apiError(err,'Warna tinting belum berhasil dihapus.'));}finally{setSaving(false);}
  };
  const filtered=items.filter(item=>(!kind||item.kind===kind)&&(!group||item.group===group)&&`${item.code} ${item.name}`.toLowerCase().includes(search.toLowerCase().trim()));
  return <div className="space-y-5" data-testid="admin-tinting">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="font-heading text-3xl font-black flex items-center gap-2"><Palette/>Manage Tinting</h1>
      <p className="mt-2 text-sm text-meow-gray">Atur kode, nama, warna HEX, jenis gradasi, dan harga tambahan layanan tinting. Harga dihitung per produk untuk sepasang lensa; perubahan tidak mengubah pesanan yang sudah dibuat.</p></div>
      <div className="flex gap-2"><button type="button" onClick={load} disabled={loading||saving} className="btn-secondary text-sm"><RefreshCw className="mr-1 inline h-4 w-4"/>Muat ulang</button>
        {permission('create')&&<button type="button" disabled={!loaded||loading||saving} onClick={()=>edit({...empty,sort_order:Math.min(9999,Math.max(-1,...items.map(item=>item.sort_order))+1)})} className="btn-primary text-sm" data-testid="add-tinting"><Plus className="mr-1 inline h-4 w-4"/>Tambah Warna</button>}</div></div>
    <div className="grid sm:grid-cols-3 gap-3"><FormField label="Cari kode atau nama tinting"><input type="search" value={search} onChange={event=>setSearch(event.target.value)} className={control}/></FormField>
      <FormField label="Filter jenis warna"><select value={kind} onChange={event=>setKind(event.target.value)} className={control}><option value="">Semua jenis</option><option value="solid">Solid</option><option value="gradient">Gradasi</option></select></FormField>
      <FormField label="Filter kelompok warna"><select value={group} onChange={event=>setGroup(event.target.value)} className={control}><option value="">Semua kelompok</option>{Object.entries(TINTING_GROUPS).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></FormField></div>
    {error&&<p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {loading?<p role="status">Memuat master tinting…</p>:loaded&&<><p className="text-sm text-meow-gray">{items.filter(item=>item.is_active).length} aktif dari {items.length} warna. Menampilkan {filtered.length} warna.</p>
      {!filtered.length&&<p>Belum ada warna yang sesuai pencarian.</p>}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-6 gap-3">{filtered.map(item=><article key={item.id} className="flex min-w-0 flex-col gap-4 rounded-2xl border bg-white p-3" data-testid={`admin-tinting-${item.id}`}>
        <div className="flex items-center justify-between gap-1 text-xs"><strong className="min-w-0 break-all">{item.code}</strong><span className={`shrink-0 rounded px-2 py-1 ${item.is_active?'bg-emerald-50 text-emerald-700':'bg-gray-100 text-gray-600'}`}>{item.is_active?'Aktif':'Nonaktif'}</span></div>
        <TintingSwatch color={item}/><h2 className="text-sm font-bold">{item.name}</h2><p className="text-xs text-meow-gray">{item.kind==='gradient'?'Gradasi':'Solid'} · {TINTING_GROUPS[item.group]}</p>
        <p className="text-sm font-bold text-meow-salmon">{formatIDR(item.additional_price)}</p>
        {(!item.hex_color||item.requires_sample)&&<p className="text-xs text-amber-700">{item.requires_sample?'Memerlukan sampel fisik':'Warna HEX belum tersedia'}</p>}
        <div className="mt-auto flex flex-wrap gap-3 border-t pt-3">{permission('update')&&<button type="button" onClick={()=>edit(item)} disabled={saving} className="text-xs font-bold text-meow-midnight" aria-label={`Edit tinting ${item.code}`}>Edit</button>}
          {permission('delete')&&<button type="button" onClick={()=>remove(item)} disabled={saving} className="text-xs text-red-600" aria-label={`Hapus tinting ${item.code}`}>Hapus</button>}</div>
      </article>)}</div></>}
    <Dialog open={!!editing} onOpenChange={open=>{if(!open&&!saving)setEditing(null);}}><DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-2xl"><DialogTitle>{editing?.id?'Edit Warna Tinting':'Tambah Warna Tinting'}</DialogTitle><DialogDescription>Pratinjau warna akan ditampilkan sebagai kartu pada checkout.</DialogDescription>
      {editing&&<form onSubmit={save} className="space-y-4" data-testid="tinting-form"><fieldset disabled={saving} className="space-y-4">
        <div className="grid sm:grid-cols-2 gap-3"><FormField label="Kode warna" hint="Kode unik, misalnya 04S atau 04G."><input required value={editing.code} maxLength={32} pattern="[A-Za-z0-9_-]+" onChange={event=>set('code',event.target.value)} className={control}/></FormField>
          <FormField label="Nama warna tinting"><input required value={editing.name} maxLength={120} onChange={event=>set('name',event.target.value)} className={control}/></FormField>
          <FormField label="Jenis warna"><select value={editing.kind} onChange={event=>set('kind',event.target.value)} className={control}><option value="solid">Solid</option><option value="gradient">Gradasi</option></select></FormField>
          <FormField label="Kelompok warna"><select value={editing.group} onChange={event=>set('group',event.target.value)} className={control}>{Object.entries(TINTING_GROUPS).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></FormField></div>
        <HexField label={editing.kind==='gradient'?'HEX warna atas':'HEX warna solid'} value={editing.hex_color} onChange={value=>set('hex_color',value)}/>
        {editing.kind==='gradient'&&<><HexField label="HEX warna tengah (opsional)" value={editing.mid_hex_color} onChange={value=>set('mid_hex_color',value)}/><HexField label="HEX warna bawah" value={editing.bottom_hex_color} onChange={value=>set('bottom_hex_color',value)}/></>}
        <div className="grid sm:grid-cols-2 gap-3"><FormField label="Harga tambahan tinting (Rp / produk)" hint="Harga jual untuk sepasang lensa; dikalikan jumlah produk pada checkout."><input required type="number" min={0} max={1000000000} step={1} value={editing.additional_price} onChange={event=>set('additional_price',event.target.value===''?'':Number(event.target.value))} className={control}/></FormField>
          <FormField label="Urutan tampilan"><input required type="number" min={0} max={9999} step={1} value={editing.sort_order} onChange={event=>set('sort_order',event.target.value===''?'':Number(event.target.value))} className={control}/></FormField></div>
        <label className="flex gap-2 text-sm"><input type="checkbox" checked={editing.requires_sample} onChange={event=>setEditing(current=>({...current,requires_sample:event.target.checked,is_active:event.target.checked?false:current.is_active}))}/>Memerlukan sampel lensa fisik (belum dijual lewat checkout)</label>
        <label className="flex gap-2 text-sm"><input type="checkbox" checked={editing.is_active} onChange={event=>set('is_active',event.target.checked)} disabled={editing.requires_sample}/>Aktif dan tampil pada checkout</label>
        <FormField label="Catatan referensi internal (opsional)"><textarea rows={3} maxLength={2000} value={editing.source_note} onChange={event=>set('source_note',event.target.value)} className={control}/></FormField>
        <div className="rounded-2xl border bg-meow-bg p-4 space-y-3"><p className="text-xs font-semibold">Pratinjau warna (ilustrasi)</p><TintingSwatch color={editing}/><p className="text-center text-sm font-bold">{editing.code} · {editing.name}</p></div>
      </fieldset>{formError&&<p role="alert" className="text-sm text-red-600">{formError}</p>}<div className="flex gap-2"><button type="button" disabled={saving} onClick={()=>setEditing(null)} className="btn-secondary flex-1">Batal</button><button type="submit" disabled={saving} className="btn-primary flex-1">{saving?'Menyimpan…':'Simpan'}</button></div></form>}
    </DialogContent></Dialog>
  </div>;
}
