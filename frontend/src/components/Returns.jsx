import React, { useEffect, useState } from 'react';
import { api, apiError } from '../lib/api';
import '../styles/engagement.css';

export const RETURN_STATUS = { draft: 'Draf · menunggu video', submitted: 'Menunggu review', approved: 'Disetujui · kirim barang ke toko', return_sent: 'Barang retur dikirim', received: 'Barang diterima toko', replacement_shipped: 'Produk pengganti dikirim', completed: 'Penggantian selesai', rejected: 'Ditolak', cancelled: 'Dibatalkan' };
export function PrivateVideo({ evidence }) {
  const [url, setUrl] = useState(''), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  useEffect(() => { setUrl(''); setError(''); }, [evidence.id]);
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);
  const load = async () => { setBusy(true); setError(''); try { const { data } = await api.get(evidence.url, { responseType: 'blob' }); setUrl(URL.createObjectURL(data)); } catch (e) { setError(apiError(e, 'Video belum dapat dibuka.')); } finally { setBusy(false); } };
  return <div className="my-3">{url ? <video controls playsInline preload="metadata" src={url} className="w-full max-h-80 rounded-xl bg-black" aria-label="Video bukti unboxing" /> : <button type="button" className="btn-secondary text-sm" disabled={busy} onClick={load}>{busy ? 'Memuat video…' : 'Lihat Video Unboxing'}</button>}{error && <p role="alert">{error}</p>}</div>;
}
export function ReturnInstructions({ instructions }) {
  if (!instructions) return null;
  return <div className="rounded-xl bg-teal-50 p-4 text-sm space-y-1"><strong>Instruksi Pengembalian · {instructions.reference}</strong><p>Kirim ke: {instructions.recipient} · {instructions.phone}</p><p className="whitespace-pre-line">{instructions.address}</p><p>Kirim sebelum {new Date(instructions.ship_before).toLocaleDateString('id-ID')}</p><p>{instructions.notes}</p><p>Penggantian produk dikirim setelah barang retur diterima dan diperiksa toko.</p></div>;
}
export function ReturnTimeline({ entries }) {
  return <ol className="text-xs mt-4 space-y-2">{entries.map(entry => <li key={entry.id} className="border-l-2 pl-3"><strong>{RETURN_STATUS[entry.status] || entry.status}</strong><p>{entry.note}</p><p className="text-meow-gray">{new Date(entry.created_at).toLocaleString('id-ID')}</p></li>)}</ol>;
}
export function TrackingForm({ onSubmit, label = 'Simpan Pengiriman', busy }) {
  const [courier, setCourier] = useState(''), [tracking, setTracking] = useState('');
  return <form onSubmit={e => { e.preventDefault(); onSubmit({ courier, tracking }); }} className="space-y-3 mt-4"><label className="block text-sm">Kurir<input required maxLength="128" className="loyalty-input block w-full mt-1" value={courier} onChange={e => setCourier(e.target.value)} /></label><label className="block text-sm">Nomor resi<input required maxLength="128" className="loyalty-input block w-full mt-1" value={tracking} onChange={e => setTracking(e.target.value)} /></label><button disabled={busy} className="btn-primary text-sm">{label}</button></form>;
}
export default function OrderReturns({ order }) {
  const [data, setData] = useState(null), [error, setError] = useState(''), [busy, setBusy] = useState(false), [show, setShow] = useState(false), [reason, setReason] = useState(''), [items, setItems] = useState({});
  const load = async () => { try { const { data } = await api.get(`/orders/${order.id}/returns`); setData(data); } catch (e) { setError(apiError(e)); } };
  useEffect(() => { load(); /* order identity is stable across detail rendering */ }, [order.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const action = async (caseId, status, fields = {}) => { setBusy(true); setError(''); try { await api.post(`/returns/${caseId}/status`, { status, ...fields }); await load(); } catch (e) { setError(apiError(e)); } finally { setBusy(false); } };
  const create = async e => { e.preventDefault(); setBusy(true); setError(''); try { await api.post(`/orders/${order.id}/returns`, { reason, items: Object.entries(items).filter(([, quantity]) => quantity > 0).map(([order_item_id, quantity]) => ({ order_item_id, quantity })) }); setShow(false); setReason(''); setItems({}); await load(); } catch (e) { setError(apiError(e)); } finally { setBusy(false); } };
  const upload = async (caseId, file) => {
    if (!file) return;
    if (!['video/mp4', 'video/webm'].includes(file.type) || file.size > 100 * 1024 * 1024) { setError('Pilih video MP4 atau WebM maksimal 100 MB.'); return; }
    setBusy(true); setError(''); const body = new FormData(); body.append('file', file);
    try { await api.post(`/returns/${caseId}/evidence`, body); await load(); } catch (e) { setError(apiError(e)); } finally { setBusy(false); }
  };
  return <section className="bg-white rounded-3xl p-6 mt-5"><h2 className="text-xl font-bold">Pengembalian & Penggantian Produk</h2><p className="text-sm text-meow-gray mt-2">Ajukan penggantian barang dengan video unboxing. Solusi klaim berupa produk baru.</p>{error && <p role="alert" className="my-3 text-red-700">{error}</p>}
    {data?.eligible && <button onClick={() => setShow(!show)} className="btn-secondary mt-4 text-sm">Ajukan Penggantian</button>}{data?.deadline && <p className="text-xs mt-3">Batas pengajuan: {new Date(data.deadline).toLocaleString('id-ID')}</p>}
    {show && <form onSubmit={create} className="mt-4 space-y-4"><p className="text-sm font-bold">Pilih barang dan jumlah yang bermasalah</p>{order.items.map(item => <label key={item.id} className="flex gap-3 items-center text-sm"><input aria-label={`Jumlah retur ${item.product_name}`} className="loyalty-input w-20" type="number" min="0" max={item.quantity} value={items[item.id] || 0} onChange={e => setItems({ ...items, [item.id]: Number(e.target.value) })} /><span>{item.product_name} (dibeli {item.quantity})</span></label>)}<label className="block text-sm">Jelaskan masalah barang<textarea required minLength="10" maxLength="4000" className="loyalty-input w-full mt-1" value={reason} onChange={e => setReason(e.target.value)} /></label><button className="btn-primary" disabled={busy}>Lanjut Upload Video</button></form>}
    {data?.cases.map(claim => <article key={claim.id} className="border rounded-2xl p-4 mt-5"><h3 className="font-bold">{claim.reference}</h3><p className="text-sm text-meow-salmon font-semibold mt-1">{RETURN_STATUS[claim.status]}</p><p className="text-sm my-3">{claim.reason}</p><ul className="text-sm mb-3">{claim.items.map(item => <li key={item.id}>{item.product_name} · {item.quantity} buah</li>)}</ul><ReturnInstructions instructions={claim.instructions} />{claim.evidence.map(e => <PrivateVideo key={e.id} evidence={e} />)}
      {claim.status === 'draft' && <div className="space-y-3 mt-3">{!claim.evidence.length && <label className="block text-sm">Video unboxing (wajib, MP4/WebM, maksimal 100 MB)<input type="file" accept="video/mp4,video/webm" disabled={busy} className="block mt-2" onChange={e => upload(claim.id, e.target.files?.[0])} /></label>}<div className="flex flex-wrap gap-3"><button disabled={busy || !claim.evidence.length} className="btn-primary text-sm" onClick={() => action(claim.id, 'submitted')}>Kirim Pengajuan</button><button disabled={busy} className="btn-secondary text-sm" onClick={() => action(claim.id, 'cancelled')}>Batalkan Draf</button></div></div>}
      {claim.status === 'approved' && <TrackingForm busy={busy} onSubmit={fields => action(claim.id, 'return_sent', fields)} label="Saya Sudah Mengirim Barang" />}
      {claim.return_tracking && <p className="text-sm mt-3">Retur: {claim.return_courier} · {claim.return_tracking}</p>}{claim.replacement_tracking && <p className="text-sm mt-2 font-bold">Produk pengganti: {claim.replacement_courier} · {claim.replacement_tracking}</p>}<ReturnTimeline entries={claim.timeline} />
    </article>)}
  </section>;
}
