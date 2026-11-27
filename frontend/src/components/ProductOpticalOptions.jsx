import React, { useEffect, useState, useRef } from 'react';
import { api, apiError, formatIDR } from '../lib/api';
import FormField from './FormField';
import PrescriptionPhotoInput from './PrescriptionPhotoInput';
import PrescriptionDetails from './PrescriptionDetails';
import { profilePrescriptionValues } from './PrescriptionForm';
import { TintingPicker } from './CheckoutTinting';

export const emptyOptical = () => ({lens_index_id:'',lens_type:'',prescription:{notes:''},file:null,tinting:null,replace_lens_product:false});
const labels={clear:'Clear',uv420:'UV420',photochromic:'Photochromic','uv420-photochromic':'UV420 + Photochromic'};
const control='w-full rounded-xl border border-meow-midnight/10 bg-white px-3 py-2.5 text-sm';

export default function ProductOpticalOptions({product,quantity,value,onChange,disabled,onBusyChange}) {
  const [options,setOptions]=useState(null),[error,setError]=useState(''),[type,setType]=useState('');
  const [colors,setColors]=useState(null),[loadingColors,setLoadingColors]=useState(false),[colorError,setColorError]=useState('');
  const [profileError,setProfileError]=useState(''),[profileLoading,setProfileLoading]=useState(false);
  const alive=useRef(true);
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
  useEffect(()=>{
    const controller=new AbortController();setOptions(null);setError('');setType('');
    api.get(`/products/${product.id}/optical-options`,{signal:controller.signal}).then(({data})=>{if(!controller.signal.aborted)setOptions(data);})
      .catch(err=>{if(!controller.signal.aborted)setError(apiError(err,'Pilihan lensa belum dapat dimuat.'));});
    return()=>controller.abort();
  },[product.id]);
  const groups=[];
  for(const index of options?.items || []) {
    const types=(index.lens_types || []).filter(kind=>kind.is_active!==false && kind.code);
    for(const kind of types){const key=kind.code || kind.id;let group=groups.find(group=>group.key===key);if(!group){group={key,name:labels[key] || kind.name,items:[]};groups.push(group);}group.items.push(index);}
  }
  const inferred=groups.find(group=>group.items.some(index=>index.id===value.lens_index_id))?.key || '';
  const activeType=type || inferred;
  const activeGroup=groups.find(group=>group.key===activeType);
  const selected=(options?.items || []).find(index=>index.id===value.lens_index_id);
  const useProfile=async()=>{
    if(disabled||profileLoading)return;setProfileLoading(true);setProfileError('');onBusyChange?.(true);
    try{const{data}=await api.get('/customer/profile');if(!alive.current)return;if(!data.profile?.prescription?.id)throw new Error('missing');
      onChange({...value,prescription:profilePrescriptionValues(data.profile.prescription),file:null});
    }catch(err){if(alive.current)setProfileError(apiError(err,'Resep profil belum tersedia. Anda bisa menambahkan catatan atau foto.'));}
    finally{if(alive.current){setProfileLoading(false);onBusyChange?.(false);}}
  };
  const loadColors=async()=>{if(loadingColors)return;setLoadingColors(true);setColorError('');try{const{data}=await api.get('/tinting');setColors(data.items||[]);}catch(err){setColorError(apiError(err,'Warna tinting belum dapat dimuat.'));}finally{setLoadingColors(false);}};
  return <div className="space-y-4" data-testid="product-optical-options">
    <section className="rounded-3xl border bg-meow-amber/10 p-4 space-y-4">
      <div><h2 className="font-bold text-lg">Lensa & Resep per Item (Opsional)</h2><p className="mt-1 text-xs text-meow-gray">Pilih jenis lensa dahulu, kemudian indeksnya. Frame boleh dibeli tanpa lensa. Satu konfigurasi berlaku untuk seluruh jumlah produk pada baris ini.</p></div>
      {['frame','package'].includes(product.product_type) && <>
        <FormField label="Jenis lensa (opsional)"><select value={activeType} disabled={disabled||profileLoading||!options} className={control} data-testid="product-lens-type"
          onChange={event=>{setType(event.target.value);onChange({...value,lens_type:event.target.value,lens_index_id:'',replace_lens_product:true});}}>
          <option value="">{!options?'Memuat jenis lensa…':value.lens_index_id&&!inferred?'Pilihan lensa lama — pilih jenis untuk mengganti':product.product_type==='frame'?'Tanpa lensa / beli frame saja':'Tanpa pilihan tambahan'}</option>
          {groups.map(group=><option key={group.key} value={group.key}>{group.name}</option>)}
        </select></FormField>
        {activeGroup && <FormField label="Indeks lensa"><select value={value.lens_index_id} disabled={disabled||profileLoading} className={control} data-testid="product-lens-index"
          onChange={event=>{setType(activeType);onChange({...value,lens_type:activeType,lens_index_id:event.target.value,replace_lens_product:true});}}>
          <option value="">Pilih indeks lensa</option>
          {activeGroup.items.map(index=><option key={index.id} value={index.id}>{`Indeks ${index.index_value} — ${product.product_type==='package'?'Termasuk paket':formatIDR(index.additional_price)} · ${index.name}`}</option>)}
        </select></FormField>}
        {activeType&&!value.lens_index_id&&<p className="text-xs text-amber-700">Pilih indeks sebelum menambahkan produk ke keranjang.</p>}
        {selected&&<p className="text-xs font-semibold">Lensa dipilih: {selected.name} · {product.product_type==='package'?'Termasuk harga paket':`+${formatIDR(selected.additional_price)} / produk`}</p>}
        {value.lens_index_id&&options&&!selected&&<p className="text-xs text-amber-700">Pilihan sebelumnya: {value.lens_index_name || 'lensa lama'}. Pilih jenis dan indeks baru untuk menggantinya, atau hapus pilihan lensa.</p>}
        {product.product_type==='frame'&&value.lens_index_id&&<button type="button" disabled={disabled||profileLoading} className="underline text-xs" onClick={()=>{setType('');onChange({...value,lens_type:'',lens_index_id:'',replace_lens_product:true});}}>Tanpa lensa / beli frame saja</button>}
        {options&&!groups.length&&<p className="text-xs text-meow-gray">Pilihan kombinasi lensa belum tersedia untuk produk ini. Anda tetap dapat melanjutkan tanpa pilihan tambahan.</p>}
        {product.product_type==='package'&&<p className="text-xs text-meow-gray">Pilihan lensa mengikuti Jenis Lensa paket. Harga lensa sudah termasuk paket; tinting tetap dihitung terpisah.</p>}
        {error&&<p role="alert" className="text-xs text-red-600">{error}</p>}
      </>}
      <button type="button" disabled={disabled||profileLoading} onClick={useProfile} className="btn-secondary text-xs">{profileLoading?'Memuat resep…':'Gunakan resep dari Profil'}</button>
      {profileError&&<p role="alert" className="text-xs text-red-600">{profileError}</p>}
      <FormField label="Catatan resep (opsional)"><textarea rows={3} maxLength={10000} value={value.prescription?.notes || ''} disabled={disabled||profileLoading} className={control} onChange={event=>onChange({...value,prescription:{...value.prescription,notes:event.target.value}})}/></FormField>
      {(value.prescription?.attachment_upload_id || Object.entries(value.prescription || {}).some(([key,v])=>key!=='notes'&&key!=='attachment_upload_id'&&v!==''&&v!=null)) && <div className="rounded-xl bg-white p-3 space-y-2"><PrescriptionDetails prescription={value.prescription}/>
        {value.prescription.attachment_upload_id&&<button type="button" disabled={disabled||profileLoading} className="underline text-xs" onClick={()=>onChange({...value,prescription:{...value.prescription,attachment_upload_id:null}})}>Hapus foto tersimpan</button>}
        <button type="button" disabled={disabled||profileLoading} className="block underline text-xs" onClick={()=>onChange({...value,prescription:{notes:value.prescription.notes,attachment_upload_id:value.prescription.attachment_upload_id}})}>Gunakan catatan/foto saja (hapus ukuran)</button>
      </div>}
      <PrescriptionPhotoInput file={value.file} disabled={disabled||profileLoading} onChange={file=>onChange({...value,file,prescription:{...value.prescription,attachment_upload_id:null}})}/>
      <p className="text-xs text-meow-gray">Pilihan, catatan, dan foto disimpan bersama produk saat Tambah ke Cart / Beli Sekarang.</p>
    </section>
    <section className="rounded-3xl border bg-white p-4 space-y-3"><h2 className="font-bold text-lg">Tinting Lensa (Opsional)</h2>
      <p className="text-xs text-meow-gray">Warna merupakan ilustrasi. Biaya tinting per produk dihitung terpisah dari harga lensa.</p>
      <TintingPicker item={{id:product.id,product,quantity,tinting:value.tinting}} colors={colors} loading={loadingColors} load={loadColors} loadError={colorError} disabled={disabled||profileLoading} onSelect={tinting=>onChange({...value,tinting})}/>
    </section>
  </div>;
}
