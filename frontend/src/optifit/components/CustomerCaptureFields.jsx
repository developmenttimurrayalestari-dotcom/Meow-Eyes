import React from 'react';
import { Field, Notice, formatNumber } from './ui';
import { frameScaleReference } from '../domain/frameScale';

export function CustomerScaleFields({ spec, setSpec, calibration, disabled, frame, view }) {
  const reference = frameScaleReference(frame, view);
  const evidenceKeys = ['knownSize', 'fullyVisible', 'samePlane', 'clearEdges', 'frontoparallel'];
  return <section className="of-subcard" data-testid="customer-photo-scale"><h3>Ukuran frame sebagai acuan</h3><p>Tidak perlu kartu atau benda tambahan. Ukuran diambil dari frame yang tersimpan pada sesi ini.</p>
    <div className="of-frame-spec" data-testid="customer-frame-reference"><small>{reference?.label}</small><strong>{reference?.lengthMm == null ? 'Ukuran belum tersedia' : `${formatNumber(reference.lengthMm)} mm`}</strong></div>
    <p>{reference?.dimension === 'a' ? 'Tandai ujung kiri dan kanan pada bagian terlebar satu lensa, sesuai A. Jangan memakai lebar seluruh kacamata atau menambahkan DBL.' : 'Tandai ujung atas dan bawah lensa yang terlihat dari samping, sesuai B. Jangan memakai lebar lensa A atau panjang tangkai sebagai penggantinya.'}</p>
    {reference?.lengthMm == null && <Notice tone="warning">Ukuran frame belum lengkap. Buat sesi baru dengan ukuran frame yang benar; hasil milimeter belum dapat dihitung.</Notice>}
    <label className="of-check"><input type="checkbox" disabled={disabled || reference?.lengthMm == null} checked={evidenceKeys.every(key => spec.evidence?.[key] === true)} onChange={event => { const checked = event.target.checked; setSpec(previous => ({ ...previous, evidence: { ...previous.evidence, ...Object.fromEntries(evidenceKeys.map(key => [key, checked])) } })); }}/><span>Saya memastikan frame yang dipakai sesuai ukuran sesi, kedua ujung terlihat jelas dan utuh, serta bagian acuannya sejajar bidang ukur dan menghadap lurus ke kamera.</span></label>
    <Notice tone={calibration.valid ? 'success' : 'warning'}>{calibration.valid ? 'Acuan ukuran frame siap digunakan.' : 'Tandai kedua ujung acuan pada foto dan konfirmasi posisi frame. Foto yang terlalu miring atau terpotong perlu diambil ulang.'}</Notice>
  </section>;
}

export function CustomerPhotoChecks({ confirmations, setConfirmations, frontal, vertex, panto, headPitchDeg, setHeadPitchDeg, headPitchSource, setHeadPitchSource, inwardDirection, setInwardDirection }) {
  const fields = [['landmarksConfirmed', 'Titik yang saya tandai sudah sesuai dengan foto.'], ['headPoseAcceptable', 'Kepala berada pada posisi nyaman dan tidak berubah saat foto diambil.'],
    ...(frontal ? [['gazeCorrect', 'Arah pandang saya sesuai panduan melihat jauh atau membaca.']] : []),
    ...(vertex ? [['surfaceVisible', 'Bagian depan mata dan permukaan belakang lensa terlihat jelas.']] : []),
    ...(panto ? [['verticalReferenceConfirmed', 'Arah tegak pada foto sudah saya pastikan dari referensi yang diketahui; bukan sekadar tepi layar.']] : [])];
  return <section className="of-subcard"><h3>Pastikan foto dan titik sesuai</h3>{fields.map(([key, label]) => <label key={key} className="of-check"><input type="checkbox" checked={confirmations[key] === true} onChange={event => setConfirmations(previous => ({ ...previous, [key]: event.target.checked }))}/><span>{label}</span></label>)}
    {panto && <><Field label="Kemiringan kepala dari hasil ukur (derajat)"><input type="number" step=".01" min="-89.99" max="89.99" value={headPitchDeg} onChange={event => setHeadPitchDeg(event.target.value)} placeholder="Isi jika Anda memiliki nilainya"/></Field><Field label="Sumber nilai kemiringan kepala"><select value={headPitchSource} onChange={event => setHeadPitchSource(event.target.value)}><option value="">Pilih sumber</option><option value="instrument">Alat ukur</option><option value="manual_reference">Hasil pemeriksaan yang sudah dimiliki</option></select></Field><Field label="Arah wajah pada foto"><select value={inwardDirection} onChange={event => setInwardDirection(event.target.value)}><option value="">Pilih arah</option><option value="left">Menghadap kiri foto</option><option value="right">Menghadap kanan foto</option></select></Field><p className="of-small">Jika nilai kemiringan kepala belum tersedia, simpan foto sebagai draft. Nilai tidak dianggap nol secara otomatis.</p></>}
  </section>;
}
