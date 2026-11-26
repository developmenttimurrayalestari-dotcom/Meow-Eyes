import React, { useCallback, useEffect, useState } from 'react';
import { Plus, RefreshCw } from 'lucide-react';
import { api, apiError } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import FormField from '../../components/FormField';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '../../components/ui/dialog';
import { MENU_LOCATIONS } from '../../components/StorefrontMenus';
import { toast } from 'sonner';
import { cmsPagePath } from '../../lib/cmsPages';
import IconPicker from '../../components/IconPicker';
import AppIcon from '../../components/AppIcon';

const blank = { label:'',url:'/',location:'header',icon:'none',sort_order:0,is_active:true,new_tab:false };
const controls = 'w-full rounded-xl border border-meow-midnight/10 bg-meow-bg px-3 py-2.5 outline-none focus:border-meow-salmon';
const quickPages = [['Beranda','/'],['Shop Now','/shop-now'],['New Arrival','/new-arrival'],['Meowsurement','/meowsurement/'],['Virtual Try-On','/virtual-try-on'],['Our Product','/our-product'],['Article','/articles'],['Flash Sale','/flash-sale'],['Games','/games'],['Contact','/contact']];

export default function AdminMenus() {
  const { user }=useAuth();
  const canEdit=user?.role!=='staff'||user.permissions?.includes('setting.update');
  const [items,setItems]=useState([]),[version,setVersion]=useState(0),[location,setLocation]=useState('header');
  const [loading,setLoading]=useState(true),[loaded,setLoaded]=useState(false),[saving,setSaving]=useState(false);
  const [error,setError]=useState(''),[formError,setFormError]=useState(''),[editing,setEditing]=useState(null),[pages,setPages]=useState([]);
  const apply=useCallback(data=>{setItems(data.items);setVersion(data.version);},[]);
  const load=useCallback(async()=>{
    setLoading(true);setError('');
    try{const{data}=await api.get('/admin/menus');apply(data);setLoaded(true);}catch(err){setError(apiError(err,'Menu belum dapat dimuat.'));}finally{setLoading(false);}
  },[apply]);
  useEffect(()=>{load();const controller=new AbortController();api.get('/pages',{signal:controller.signal}).then(({data})=>{if(!controller.signal.aborted)setPages(data.pages||[]);}).catch(()=>{});return()=>controller.abort();},[load]);
  const edit=item=>{setEditing({...item,version});setFormError('');};
  const set=(key,value)=>setEditing(current=>({...current,[key]:value}));
  const changed=data=>{apply(data);window.dispatchEvent(new Event('meow:menus-updated'));};
  const save=async event=>{
    event.preventDefault();if(saving)return;setSaving(true);setFormError('');
    try{const{id,...body}=editing;const{data}=id?await api.put('/admin/menus/'+encodeURIComponent(id),body):await api.post('/admin/menus',body);changed(data);setLocation(body.location);setEditing(null);toast.success('Menu tersimpan');}
    catch(err){setFormError(apiError(err,'Menu belum berhasil disimpan.'));}finally{setSaving(false);}
  };
  const remove=async item=>{
    if(!window.confirm(`Hapus menu "${item.label}"?`))return;setSaving(true);setError('');
    try{const{data}=await api.delete('/admin/menus/'+encodeURIComponent(item.id),{params:{version}});changed(data);toast.success('Menu dihapus');}
    catch(err){setError(apiError(err,'Menu belum berhasil dihapus.'));}finally{setSaving(false);}
  };
  const visible=items.filter(item=>item.location===location).sort((a,b)=>a.sort_order-b.sort_order||a.id.localeCompare(b.id));
  return <div className="space-y-5" data-testid="admin-menus">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="font-heading font-black text-3xl">Manage Menu</h1><p className="text-sm text-meow-gray mt-2">Atur navigasi halaman pelanggan berdasarkan lokasi. Urutan terkecil ditampilkan lebih dahulu. Maksimal 100 item untuk seluruh lokasi.</p></div>
      <div className="flex gap-2"><button type="button" className="btn-secondary text-sm" disabled={loading||saving} onClick={load}><RefreshCw className="inline h-4 w-4 mr-1"/>Muat ulang</button>{canEdit&&<button type="button" data-testid="add-menu" disabled={!loaded||loading||saving||items.length>=100} onClick={()=>edit({...blank,location,sort_order:Math.min(9999,Math.max(-1,...visible.map(item=>item.sort_order))+1)})} className="btn-primary text-sm"><Plus className="inline h-4 w-4 mr-1"/>Tambah Menu</button>}</div>
    </div>
    <div role="group" aria-label="Lokasi menu" className="flex flex-wrap gap-2">{Object.entries(MENU_LOCATIONS).map(([key,label])=><button type="button" key={key} aria-pressed={location===key} onClick={()=>setLocation(key)} className={`rounded-xl px-4 py-2 text-sm font-bold ${location===key?'bg-meow-midnight text-white':'bg-white border'}`}>{label}</button>)}</div>
    <p className="text-xs text-meow-gray">Footer Eksplorasi berada di bagian bawah website. Tautan halaman CMS pada bagian Bantuan tetap mengikuti halaman yang dipublikasikan. Item nonaktif tidak ditampilkan kepada pelanggan.</p>
    {error&&<p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {loading?<p role="status">Memuat menu…</p>:loaded&&<div className="rounded-2xl bg-white border overflow-x-auto"><table className="w-full text-sm text-left"><thead><tr className="border-b bg-meow-bg"><th className="p-3">Nama Menu</th><th className="p-3">URL Tujuan</th><th className="p-3">Urutan</th><th className="p-3">Status</th>{canEdit&&<th className="p-3">Aksi</th>}</tr></thead><tbody>{visible.map(item=><tr key={item.id} className="border-b" data-testid={`menu-row-${item.id}`}><td className="p-3 font-bold"><span className="inline-flex items-center gap-2"><AppIcon name={item.icon} className="h-5 w-5 shrink-0"/>{item.label}</span></td><td className="p-3"><span className="break-all">{item.url}</span>{item.new_tab&&<span className="block text-xs text-meow-gray">Buka di tab baru</span>}</td><td className="p-3">{item.sort_order}</td><td className="p-3">{item.is_active?'Aktif':'Nonaktif'}</td>{canEdit&&<td className="p-3"><div className="flex gap-3"><button type="button" disabled={saving} onClick={()=>edit(item)} className="font-bold text-meow-salmon" aria-label={`Edit menu ${item.label}`}>Edit</button><button type="button" disabled={saving} onClick={()=>remove(item)} className="font-bold text-red-600" aria-label={`Hapus menu ${item.label}`}>Hapus</button></div></td>}</tr>)}{!visible.length&&<tr><td className="p-6 text-meow-gray" colSpan={canEdit?5:4}>Belum ada menu pada lokasi ini. Tambahkan menu untuk menampilkannya.</td></tr>}</tbody></table></div>}
    <Dialog open={!!editing} onOpenChange={open=>{if(!open&&!saving)setEditing(null);}}><DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-xl"><DialogTitle>{editing?.id?'Edit Menu':'Tambah Menu'}</DialogTitle><DialogDescription>Isi nama dan URL tujuan menu. URL dapat mengarah ke halaman website atau situs eksternal.</DialogDescription>
      {editing&&<form onSubmit={save} className="space-y-4" data-testid="menu-form"><fieldset disabled={saving} className="space-y-4">
        <FormField label="Nama menu"><input required maxLength={80} value={editing.label} onChange={event=>set('label',event.target.value)} className={controls}/></FormField>
        <FormField label="Lokasi menu"><select value={editing.location} onChange={event=>set('location',event.target.value)} className={controls}>{Object.entries(MENU_LOCATIONS).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></FormField>
        <FormField label="Pilih halaman cepat (opsional)" hint="Memilih halaman akan mengisi URL tujuan di bawah. Anda tetap bisa mengetik URL sendiri."><select value="" onChange={event=>{if(event.target.value)set('url',event.target.value);}} className={controls}><option value="">Pilih halaman…</option><optgroup label="Halaman website">{quickPages.map(([label,url])=><option key={url} value={url}>{label}</option>)}</optgroup>{pages.length>0&&<optgroup label="Halaman CMS terbit">{pages.map(page=><option key={page.id||page.slug} value={cmsPagePath(page.slug)}>{page.title}</option>)}</optgroup>}</select></FormField>
        <FormField label="URL tujuan menu" hint="Contoh: /shop-now, /pages/panduan-belanja, atau https://example.com/promo. Gunakan /meowsurement/ untuk Meowsurement."><input required maxLength={2048} data-testid="menu-url" value={editing.url} onChange={event=>set('url',event.target.value)} className={controls}/></FormField>
        <IconPicker label="Ikon menu" value={editing.icon} onChange={value=>set('icon',value)} disabled={saving}/>
        <FormField label="Urutan tampilan" hint="Angka 0–9999; lebih kecil tampil lebih dahulu pada lokasi yang sama."><input required type="number" min={0} max={9999} step={1} value={editing.sort_order} onChange={event=>set('sort_order',event.target.value===''?'':Number(event.target.value))} className={controls}/></FormField>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={editing.new_tab} onChange={event=>set('new_tab',event.target.checked)}/>Buka tautan di tab baru</label>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={editing.is_active} onChange={event=>set('is_active',event.target.checked)}/>Menu aktif</label>
      </fieldset>{formError&&<p role="alert" className="text-sm text-red-600">{formError}</p>}<div className="flex gap-2"><button type="button" disabled={saving} className="btn-secondary flex-1" onClick={()=>setEditing(null)}>Batal</button><button type="submit" disabled={saving} className="btn-primary flex-1">{saving?'Menyimpan…':'Simpan'}</button></div></form>}
    </DialogContent></Dialog>
  </div>;
}
