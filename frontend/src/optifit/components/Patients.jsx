import React, { useEffect, useState } from "react";
import { ArrowLeft, CalendarDays, ClipboardPlus, Download, FileClock, Pencil, Plus, Search, Trash2, UserRound, UsersRound } from "lucide-react";
import { vault } from "../storage/vault";
import { STATUS_LABELS } from "../domain/workflow";
import { Button, EmptyState, Field, Modal, Notice, StatusBadge, normalizedImage, readableDate, safeError, todayLocal } from "./ui";

const patientFields = ["id", "fullName", "customerId", "examinationDate", "birthDate", "sex", "phone", "address", "email", "occupation", "complaint", "notes", "photoConsent", "profilePhotoId"];
const patientPayload = value => Object.fromEntries(patientFields.filter(key => value[key] !== undefined).map(key => [key, value[key]]));

export function PatientList({ state, actor, onOpen, onCreate }) {
  const [query, setQuery] = useState("");
  const patients = state.patients.filter(p => !p.deletedAt && `${p.fullName} ${p.recordNumber || ""}`.toLocaleLowerCase("id").includes(query.toLocaleLowerCase("id"))).sort((a, b) => (b.updatedAt || b.createdAt || "").localeCompare(a.updatedAt || a.createdAt || ""));
  const canEdit = actor.role !== "reviewer";
  return <>
    <div className="of-page-heading"><div><span className="of-eyebrow">RUANG KERJA LOKAL</span><h1>Pasien</h1><p>Catatan fitting yang tersimpan di perangkat ini.</p></div>{canEdit && <Button onClick={onCreate}><Plus size={19} />Tambah pasien</Button>}</div>
    <div className="of-stats-row"><div><span>Pasien aktif</span><strong>{state.patients.filter(p => !p.deletedAt).length}</strong></div><div><span>Sesi pengukuran</span><strong>{state.sessions.length}</strong></div><div><span>Menunggu review</span><strong>{state.sessions.filter(s => s.status === "pending_review" || s.status === "needs_verification").length}</strong></div></div>
    <section className="of-card">
      <div className="of-search"><Search size={20} /><input aria-label="Cari pasien atau nomor rekam" placeholder="Cari nama pasien atau nomor rekam…" value={query} onChange={e => setQuery(e.target.value)} autoComplete="off" /></div>
      {!patients.length ? <EmptyState icon={UsersRound} title={query ? "Pasien belum ditemukan" : "Mulai dari pasien pertama"} action={canEdit && !query ? <Button onClick={onCreate}>Daftarkan pasien</Button> : null}>{query ? "Coba nama atau nomor rekam lainnya." : "Identitas dan resep tersimpan terenkripsi. Tidak ada data pasien contoh."}</EmptyState> : <div className="of-patient-list">{patients.map(patient => {
        const sessions = state.sessions.filter(s => s.patientId === patient.id).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
        return <button key={patient.id} type="button" className="of-patient-row" onClick={() => onOpen(patient.id)} data-testid={`optifit-patient-${patient.id}`}><span className="of-avatar"><UserRound size={23} /></span><span className="of-grow"><strong>{patient.fullName}</strong><small>{patient.recordNumber}</small></span><span className="of-patient-meta"><small>{sessions.length} sesi</small><span>{readableDate(patient.examinationDate)}</span></span><span className="of-row-arrow">→</span></button>;
      })}</div>}
    </section>
  </>;
}

export function PatientForm({ patient = null, onClose, onSaved, customerProfile, loadCustomerProfile }) {
  const [values, setValues] = useState(() => ({ fullName: "", examinationDate: todayLocal(), birthDate: "", sex: "", phone: "", address: "", email: "", occupation: "", complaint: "", notes: "", photoConsent: false, ...patient }));
  const [savedId, setSavedId] = useState(patient?.id || null);
  const [file, setFile] = useState(null); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const [profileConsent, setProfileConsent] = useState(false);
  const set = (key, value) => setValues(v => ({ ...v, [key]: value }));
  const loadProfile = async () => {
    if (!profileConsent) return; setBusy(true); setError("");
    try {
      const result = loadCustomerProfile ? await loadCustomerProfile({ confirmed: true }) : customerProfile;
      const profile = result?.user || result?.profile || result;
      if (!profile) throw new Error("Profil Meow Eyes belum tersedia. Anda tetap dapat mengisi data secara manual.");
      setValues(v => ({ ...v, customerId: profile.id || profile.user_id || null, fullName: profile.name || profile.full_name || v.fullName, email: profile.email || v.email, phone: profile.phone || v.phone, address: typeof profile.address === "string" ? profile.address : v.address, birthDate: profile.date_of_birth || profile.birth_date || v.birthDate, sex: profile.gender || v.sex }));
    } catch (err) { setError(safeError(err)); } finally { setBusy(false); }
  };
  const submit = async event => {
    event.preventDefault(); setBusy(true); setError("");
    try {
      if (!values.fullName.trim()) throw new Error("Nama lengkap wajib diisi.");
      if (values.birthDate && values.birthDate > todayLocal()) throw new Error("Tanggal lahir tidak boleh berada di masa depan.");
      if (file && !values.photoConsent) throw new Error("Persetujuan foto profil harus diberikan sebelum foto disimpan.");
      let saved = await vault.savePatient(patientPayload({ ...values, id: savedId || undefined, fullName: values.fullName.trim(), ...(!values.photoConsent ? { profilePhotoId: null } : {}) }));
      setSavedId(saved.id);
      if (file) {
        const image = await normalizedImage(file);
        const photoId = await vault.putPhoto({ patientId: saved.id, blob: image.blob, consent: true, metadata: { purpose: "profile", width: image.width, height: image.height } });
        saved = await vault.savePatient(patientPayload({ ...saved, profilePhotoId: photoId, photoConsent: true }));
        setFile(null);
      } else if (!values.photoConsent && patient?.profilePhotoId) {
        await vault.deletePhoto(patient.profilePhotoId, { reason: "Persetujuan foto profil dicabut oleh pasien." });
        saved = await vault.savePatient(patientPayload({ ...saved, profilePhotoId: null }));
      }
      onSaved(saved);
    } catch (err) { setError(safeError(err)); } finally { setBusy(false); }
  };
  return <Modal title={patient ? "Ubah data pasien" : "Daftarkan pasien"} onClose={busy ? undefined : onClose} wide><form onSubmit={submit} autoComplete="off" className="of-form">
    <p className="of-muted">{patient?.recordNumber ? `Nomor rekam: ${patient.recordNumber}` : "ID pasien dan nomor rekam dibuat otomatis saat disimpan."}</p>
    {(customerProfile || loadCustomerProfile) && <details className="of-import-panel"><summary><Download size={17} />Gunakan profil pelanggan Meow Eyes</summary><label className="of-check"><input type="checkbox" checked={profileConsent} onChange={e => setProfileConsent(e.target.checked)} /><span>Saya mengizinkan pengambilan profil akun untuk isian pasien ini. Data hasil salinan akan saya periksa.</span></label><Button variant="secondary" disabled={!profileConsent || busy} onClick={loadProfile}>Ambil profil akun</Button></details>}
    <div className="of-grid-two"><Field label="Nama lengkap pasien" required><input value={values.fullName} onChange={e => set("fullName", e.target.value)} maxLength={160} required /></Field><Field label="Tanggal pemeriksaan" required><input type="date" value={values.examinationDate} onChange={e => set("examinationDate", e.target.value)} required /></Field></div>
    <details className="of-details" open={Boolean(patient)}><summary>Data tambahan pasien <small>Opsional</small></summary><div className="of-grid-two">
      <Field label="Tanggal lahir"><input type="date" value={values.birthDate || ""} onChange={e => set("birthDate", e.target.value)} max={todayLocal()} /></Field>
      <Field label="Jenis kelamin"><select value={values.sex || ""} onChange={e => set("sex", e.target.value)}><option value="">Tidak dicatat</option><option value="male">Laki-laki</option><option value="female">Perempuan</option><option value="other">Lainnya / pilihan pasien</option></select></Field>
      <Field label="Nomor telepon"><input type="tel" value={values.phone || ""} onChange={e => set("phone", e.target.value)} maxLength={30} /></Field><Field label="Email"><input type="email" value={values.email || ""} onChange={e => set("email", e.target.value)} maxLength={254} /></Field>
      <Field label="Pekerjaan"><input value={values.occupation || ""} onChange={e => set("occupation", e.target.value)} maxLength={160} /></Field><Field label="Alamat"><textarea rows={2} value={values.address || ""} onChange={e => set("address", e.target.value)} maxLength={2000} /></Field>
      <Field label="Keluhan utama"><textarea rows={2} value={values.complaint || ""} onChange={e => set("complaint", e.target.value)} maxLength={4000} /></Field><Field label="Catatan pasien"><textarea rows={2} value={values.notes || ""} onChange={e => set("notes", e.target.value)} maxLength={4000} /></Field>
    </div></details>
    <div className="of-photo-consent"><label className="of-check"><input type="checkbox" checked={!!values.photoConsent} onChange={e => set("photoConsent", e.target.checked)} /><span>Pasien menyetujui penyimpanan foto profil terenkripsi di perangkat ini.</span></label>{values.photoConsent && <Field label="Foto profil opsional" hint="JPEG, PNG, WebP, maksimal 8 MiB dan 20 megapiksel. Foto tidak diunggah."><input type="file" accept="image/jpeg,image/png,image/webp" onChange={e => setFile(e.target.files?.[0] || null)} /></Field>}</div>
    {error && <Notice tone="danger">{error}</Notice>}
    <div className="of-actions"><Button variant="secondary" onClick={onClose} disabled={busy}>Batal</Button><Button type="submit" busy={busy}>Simpan pasien</Button></div>
  </form></Modal>;
}

export function PatientDetail({ patient, state, actor, onBack, onEdit, onNewSession, onOpenSession, onDeleted }) {
  const [deleteOpen, setDeleteOpen] = useState(false);
  const sessions = state.sessions.filter(s => s.patientId === patient.id).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return <>
    <Button variant="quiet" onClick={onBack}><ArrowLeft size={17} />Semua pasien</Button>
    <div className="of-page-heading"><div><span className="of-eyebrow">{patient.recordNumber}</span><h1>{patient.fullName}</h1><p><CalendarDays size={16} /> Pemeriksaan {readableDate(patient.examinationDate)}</p></div><div className="of-actions">{actor.role !== "reviewer" && <><Button variant="secondary" onClick={onEdit}><Pencil size={17} />Ubah data</Button><Button onClick={onNewSession}><ClipboardPlus size={18} />Sesi baru</Button></>}</div></div>
    <section className="of-card of-patient-summary"><PrivateProfile patient={patient} /><div className="of-grid-three of-grow">{[["Tanggal lahir", readableDate(patient.birthDate)], ["Telepon", patient.phone], ["Email", patient.email], ["Alamat", patient.address], ["Keluhan utama", patient.complaint], ["Catatan", patient.notes]].map(([label, value]) => <div key={label}><small className="of-label">{label}</small><p>{value || "Tidak dicatat"}</p></div>)}</div></section>
    <section className="of-card"><div className="of-section-heading"><h2>Riwayat pengukuran</h2><span className="of-count">{sessions.length}</span></div>{sessions.length ? <div className="of-session-list">{sessions.map(session => <button key={session.id} className="of-session-row" onClick={() => onOpenSession(session.id)} type="button"><FileClock size={22} /><span className="of-grow"><strong>{readableDate(session.examinationDate || session.createdAt)}</strong><small>{state.users.find(u => u.id === session.createdBy)?.displayName || "Operator lokal"} · {session.algorithmVersion}</small></span><StatusBadge status={session.status} labels={STATUS_LABELS} /><span>→</span></button>)}</div> : <EmptyState icon={FileClock} title="Belum ada sesi pengukuran">Mulai sesi untuk mencatat resep, frame dan pengukuran fitting pasien ini.</EmptyState>}</section>
    {actor.role === "admin" && <div className="of-danger-zone"><p>Penghapusan permanen menghapus data dan foto pasien dari vault ini. Cadangan yang telah diekspor perlu dikelola terpisah.</p><Button variant="danger" onClick={() => setDeleteOpen(true)}><Trash2 size={17} />Hapus pasien permanen</Button></div>}
    {deleteOpen && <DeletePatient patient={patient} onClose={() => setDeleteOpen(false)} onDeleted={onDeleted} />}
  </>;
}

function PrivateProfile({ patient }) {
  const [url, setUrl] = useState(null);
  useEffect(() => {
    let active = true; let objectUrl;
    setUrl(null);
    if (patient.profilePhotoId && patient.photoConsent) vault.getPhoto(patient.profilePhotoId).then(blob => { if (active) { objectUrl = URL.createObjectURL(blob); setUrl(objectUrl); } }).catch(() => {});
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [patient.profilePhotoId, patient.photoConsent]);
  return <span className="of-profile-avatar">{url ? <img src={url} alt="Profil pasien dengan persetujuan" /> : <UserRound size={36} />}</span>;
}

function DeletePatient({ patient, onClose, onDeleted }) {
  const [confirmation, setConfirmation] = useState(""); const [reason, setReason] = useState(""); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const submit = async event => { event.preventDefault(); setBusy(true); setError(""); try { await vault.deletePatient(patient.id, { confirmation, reason }); onDeleted(); } catch (err) { setError(safeError(err)); } finally { setBusy(false); } };
  return <Modal title="Hapus pasien permanen" onClose={busy ? undefined : onClose}><form onSubmit={submit} className="of-form"><Notice tone="danger">Data pasien, sesi, dan foto di vault ini akan dihapus. Tindakan tidak dapat dibatalkan melalui aplikasi.</Notice><Field label={`Ketik nomor rekam ${patient.recordNumber}`} required><input value={confirmation} onChange={e => setConfirmation(e.target.value)} required autoComplete="off" /></Field><Field label="Alasan penghapusan" required><textarea value={reason} onChange={e => setReason(e.target.value)} required minLength={5} maxLength={1000} /></Field>{error && <Notice tone="danger">{error}</Notice>}<div className="of-actions"><Button variant="secondary" onClick={onClose} disabled={busy}>Batal</Button><Button type="submit" variant="danger" busy={busy} disabled={confirmation !== patient.recordNumber || !reason.trim()}>Hapus permanen</Button></div></form></Modal>;
}
