import React,{useEffect,useMemo,useRef,useState} from 'react';
import { Icon,X } from 'lucide-react';
import AppIcon from './AppIcon';
import FormField from './FormField';
import { iconName,iconSearchText,loadIconCatalog } from '../lib/iconLibrary';
const PAGE_SIZE=48;

export default function IconPicker({label='Ikon',value='none',onChange,disabled=false,allowNone=true}) {
  const [open,setOpen]=useState(false),[catalog,setCatalog]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[retry,setRetry]=useState(0);
  const [query,setQuery]=useState(''),[page,setPage]=useState(0);
  const search=useRef(null),trigger=useRef(null);
  useEffect(()=>{
    if(!open)return;
    let active=true;setBusy(true);setError('');
    loadIconCatalog().then(data=>{if(active){setCatalog(data);setBusy(false);}}).catch(()=>{if(active){setError('Koleksi ikon belum dapat dimuat. Silakan coba lagi.');setBusy(false);}});
    search.current?.focus();return()=>{active=false;};
  },[open,retry]);
  const names=useMemo(()=>Object.keys(catalog?.icons||{}).map(name=>({name,search:iconSearchText(name)})),[catalog]);
  const results=useMemo(()=>{const tokens=query.toLowerCase().replace(/[:_-]/g,' ').trim().split(/\s+/).filter(Boolean);return names.filter(item=>tokens.every(token=>item.search.includes(token)));},[names,query]);
  const pages=Math.max(1,Math.ceil(results.length/PAGE_SIZE));
  const close=()=>{setOpen(false);trigger.current?.focus();};
  const choose=name=>{onChange(name);close();};
  return <fieldset disabled={disabled} className="min-w-0 space-y-2 rounded-xl border p-3" data-testid="icon-picker"><legend className="px-1 text-xs font-semibold">{label}</legend>
    <div className="flex items-center gap-3"><span className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-meow-bg border" data-testid="selected-icon-preview"><AppIcon name={value} className="h-6 w-6 text-meow-midnight"/></span><span className="min-w-0 flex-1 break-words text-xs">{!value||value==='none'?'Tanpa ikon':iconName(value)}</span><button ref={trigger} type="button" disabled={disabled} onClick={()=>{setOpen(current=>!current);setQuery('');setPage(0);}} className="btn-secondary px-3 py-2 text-xs" aria-expanded={open}>Pilih ikon</button></div>
    {open&&<div className="space-y-3" onKeyDown={event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();close();}}}>
      <FormField label="Cari ikon" hint="Cari nama ikon atau kata seperti kamera, kacamata, belanja, hati, atau paket."><input ref={search} type="search" value={query} onChange={event=>{setQuery(event.target.value);setPage(0);}} placeholder="camera, heart, belanja…" className="rounded-xl border px-3 py-2 text-sm"/></FormField>
      {busy&&<p role="status" className="text-xs">Memuat koleksi Lucide…</p>}
      {error&&<div role="alert" className="text-xs text-red-600"><p>{error}</p><button type="button" onClick={()=>setRetry(current=>current+1)} className="underline">Coba lagi</button></div>}
      {!busy&&!error&&catalog&&<><p className="text-xs text-meow-gray">{results.length.toLocaleString('id-ID')} hasil dari {names.length.toLocaleString('id-ID')} ikon Lucide</p>
        <div role="group" aria-label="Pilihan ikon" className="grid grid-cols-4 sm:grid-cols-6 gap-2 max-h-64 overflow-y-auto">{results.slice(page*PAGE_SIZE,(page+1)*PAGE_SIZE).map(({name})=><button key={name} type="button" title={name} aria-label={`Pilih ikon ${name}`} aria-pressed={iconName(value)===name} onClick={()=>choose('lucide:'+name)} className={`min-w-0 rounded-lg border p-2 flex flex-col items-center gap-1 hover:bg-meow-bg ${iconName(value)===name?'border-meow-salmon bg-rose-50':''}`}><Icon iconNode={catalog.icons[name]} className="h-6 w-6" aria-hidden="true"/><span className="text-[9px] truncate w-full">{name}</span></button>)}</div>
        {!results.length&&<p role="status" className="text-xs">Ikon tidak ditemukan. Coba kata pencarian lain.</p>}
        <div className="flex justify-between gap-2 text-xs"><button type="button" disabled={page===0} onClick={()=>setPage(current=>current-1)}>Sebelumnya</button><span>{page+1} / {pages}</span><button type="button" disabled={page+1>=pages} onClick={()=>setPage(current=>current+1)}>Berikutnya</button></div>
      </>}
      <div className="flex justify-between gap-2">{allowNone&&<button type="button" onClick={()=>choose('none')} className="text-xs underline">Tanpa ikon</button>}<button type="button" onClick={close} className="text-xs font-bold inline-flex gap-1 items-center"><X className="h-3 w-3"/>Tutup pilihan ikon</button></div>
    </div>}
  </fieldset>;
}
