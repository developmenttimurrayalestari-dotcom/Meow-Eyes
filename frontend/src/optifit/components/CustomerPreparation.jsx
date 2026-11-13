import React, { useState } from 'react';
import { Camera, ShieldCheck } from 'lucide-react';
import { measurementType } from '../domain/customerFlow';
import { Button, Notice, safeError } from './ui';
import MeasurementIllustrationGuide from './MeasurementIllustrationGuide';

export default function CustomerPreparation({ data, onSave, disabled = false }) {
  const type = measurementType(data.requiredParameters);
  const [ready, setReady] = useState(data.preparation?.includes('customer_ready') || false);
  const [consent, setConsent] = useState(data.consents?.capture === true);
  const [upload, setUpload] = useState(data.consents?.uploadPhotos === true);
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const save = async () => {
    setBusy(true); setError('');
    try { await onSave({ ...data, preparation: ['customer_ready'], consents: { capture: consent, retainPhotos: true, uploadPhotos: upload, thumbnail: false, confirmedAt: new Date().toISOString() } }, 'Customer membaca panduan dan menyimpan persetujuan foto.'); }
    catch (err) { setError(safeError(err)); } finally { setBusy(false); }
  };
  return <section className="of-card" data-testid="customer-preparation"><div className="of-section-heading"><div><h2>Siapkan foto {type.title.toLowerCase()}</h2><p>Ikuti panduan singkat berikut sebelum membuka kamera.</p></div><ShieldCheck size={28}/></div>
    <MeasurementIllustrationGuide data={data}/>
    <ol className="of-customer-guide"><li>Gunakan tempat yang terang. Pastikan area mata dan kacamata tidak tertutup rambut atau pantulan cahaya.</li>
      <li>{type.id === 'distance_pd' ? 'Posisikan kamera sejajar mata dan lihat benda yang jauh, bukan layar ponsel. Minta bantuan orang lain bila diperlukan.' : type.id === 'near_pd' ? `Lihat benda bacaan pada jarak ${data.workingDistanceCm} cm dari mata. Posisi foto dari depan.` : 'Minta bantuan orang lain untuk mengambil foto dari sisi kanan dan kiri. Pertahankan posisi kepala yang nyaman dan kacamata pada posisi pemakaian.'}</li>
      <li>{type.id === 'wrap' ? 'Siapkan hasil pengukuran sudut dari alat atau pemeriksaan yang sudah Anda miliki.' : 'Pakai frame yang sesuai data sesi. Lebar lensa A menjadi acuan foto depan, dan tinggi lensa B menjadi acuan foto samping. Pastikan bagian tersebut terlihat utuh; tidak perlu kartu atau benda tambahan.'}</li>
    </ol>
    <label className="of-check"><input type="checkbox" checked={ready} disabled={disabled} onChange={event => setReady(event.target.checked)}/><span>Saya sudah memakai frame sesuai ukuran sesi dan menyiapkan posisi foto sesuai panduan.</span></label>
    <label className="of-check"><input type="checkbox" checked={consent} disabled={disabled} onChange={event => setConsent(event.target.checked)}/><span>Saya menyetujui pengambilan foto dan penyimpanan hasil pengukuran pada akun saya.</span></label>
    <label className="of-check"><input type="checkbox" checked={upload} disabled={disabled} onChange={event => setUpload(event.target.checked)}/><span>Simpan juga foto secara privat di akun saya (opsional).</span></label>
    <Notice>{upload ? 'Foto disimpan secara privat agar dapat dibuka kembali.' : 'Foto tetap di perangkat selama halaman terbuka. Hasil dan titik ukur disimpan pada akun, tetapi foto tidak diunggah.'}</Notice>
    {error && <Notice tone="danger">{error}</Notice>}<Button disabled={disabled || !ready || !consent} busy={busy} onClick={save}><Camera size={18}/>Lanjut ke kamera</Button>
  </section>;
}
