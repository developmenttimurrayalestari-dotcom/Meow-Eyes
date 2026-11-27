import React from 'react';
import { api, apiError } from '../lib/api';
import { toast } from 'sonner';

export default function PrescriptionDetails({ prescription }) {
  if (!prescription) return <p className="text-xs text-meow-gray">Tanpa resep.</p>;
  const download=async()=>{
    try { const {data}=await api.get(`/prescriptions/uploads/${encodeURIComponent(prescription.attachment_upload_id)}`,{responseType:'blob'});
      const url=URL.createObjectURL(data);const link=document.createElement('a');link.href=url;link.download='resep-kacamata';link.click();setTimeout(()=>URL.revokeObjectURL(url),5000);
    } catch(err) { toast.error(apiError(err,'Foto resep belum dapat diunduh.')); }
  };
  const keys=['od_sph','od_cyl','od_axis','od_add','os_sph','os_cyl','os_axis','os_add','pd_total','pd_right','pd_left'];
  return <div className="text-xs space-y-1 conveythis-no-translate notranslate" translate="no" data-conveythis-private="" data-testid="prescription-details">
    <p className="font-semibold">Resep</p>
    {keys.filter(key=>prescription[key]!=null && prescription[key]!=='').map(key=><p key={key}>{key.replace(/_/g,' ').toUpperCase()}: {prescription[key]}</p>)}
    {prescription.notes && <p className="whitespace-pre-wrap break-words">Catatan: {prescription.notes}</p>}
    {prescription.attachment_upload_id && <button type="button" onClick={download} className="underline">Lihat / unduh foto resep</button>}
    {!prescription.notes&&!prescription.attachment_upload_id&&!keys.some(key=>prescription[key]!=null&&prescription[key]!=='')&&<p>Tanpa catatan atau foto resep.</p>}
  </div>;
}
