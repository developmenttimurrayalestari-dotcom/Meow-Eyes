import React, { useState } from "react";
import { ArrowRight, Eye, FileLock2, LockKeyhole, ShieldCheck, Upload } from "lucide-react";
import { vault } from "../storage/vault";
import { Button, Field, Modal, Notice, safeError } from "./ui";

export default function VaultGate({ status, onRefresh }) {
  const [username, setUsername] = useState(status.logins?.[0]?.username || "");
  const [secret, setSecret] = useState("");
  const [confirm, setConfirm] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [organization, setOrganization] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [restore, setRestore] = useState(false);
  const initialized = status.initialized;
  const submit = async event => {
    event.preventDefault(); setError("");
    if (!initialized && secret !== confirm) { setError("Konfirmasi PIN/frasa sandi belum sama."); return; }
    setBusy(true);
    try {
      if (initialized) await vault.unlock(username.trim(), secret);
      else await vault.create({ organization: { name: organization.trim() }, admin: { username: username.trim(), displayName: displayName.trim(), secret } });
      setSecret(""); setConfirm(""); await onRefresh();
    } catch (err) { setError(safeError(err)); }
    finally { setBusy(false); }
  };
  return <main className="of-gate">
    <section className="of-gate-intro">
      <div className="of-wordmark"><span><Eye size={27} /></span><div>OptiFit<strong>Meowsurement</strong></div></div>
      <span className="of-eyebrow">RUANG KERJA FITTING OPTIK</span>
      <h1>Pengukuran yang tercatat.<br /><em>Keputusan yang terverifikasi.</em></h1>
      <p>Catat resep, ambil gambar terkalibrasi, periksa hasil bersama reviewer. Seluruh proses inti tersedia di perangkat Anda.</p>
      <div className="of-gate-points">
        <div><FileLock2 /><span><strong>Data terenkripsi</strong><small>Pasien dan foto disimpan di browser ini.</small></span></div>
        <div><ShieldCheck /><span><strong>Review profesional</strong><small>Kamera membantu fitting, bukan menentukan resep.</small></span></div>
      </div>
      <p className="of-muted of-small">Tidak ada unggahan foto otomatis. Perangkat tanpa depth sensor tetap dapat menggunakan metode marker dan manual.</p>
    </section>
    <section className="of-gate-panel">
      <div className="of-gate-icon"><LockKeyhole size={26} /></div>
      <h2>{initialized ? "Buka ruang kerja" : "Siapkan ruang kerja"}</h2>
      <p className="of-muted">{initialized ? "Masuk dengan akun lokal yang dibuat administrator optik." : "Buat administrator pertama. Tidak ada akun atau password bawaan."}</p>
      <form onSubmit={submit} className="of-form" autoComplete="off">
        {!initialized && <><Field label="Nama optik / organisasi" required><input value={organization} onChange={e => setOrganization(e.target.value)} maxLength={160} required /></Field><Field label="Nama administrator" required><input value={displayName} onChange={e => setDisplayName(e.target.value)} maxLength={120} required /></Field></>}
        <Field label="Username lokal" required>{initialized && status.logins?.length ? <select value={username} onChange={e => setUsername(e.target.value)} required><option value="">Pilih akun</option>{status.logins.map(login => <option key={login.id || login.username} value={login.username}>{login.username}</option>)}</select> : <input value={username} onChange={e => setUsername(e.target.value)} maxLength={80} autoCapitalize="none" spellCheck="false" autoComplete="username" required />}</Field>
        <Field label="PIN atau frasa sandi" required hint={!initialized ? "Frasa sandi minimal 12 karakter disarankan. PIN numerik minimal 10 digit mempunyai kekuatan lebih rendah." : undefined}><input type="password" value={secret} onChange={e => setSecret(e.target.value)} maxLength={256} autoComplete={initialized ? "current-password" : "new-password"} required /></Field>
        {!initialized && <Field label="Ulangi PIN atau frasa sandi" required><input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} maxLength={256} autoComplete="new-password" required /></Field>}
        {error && <Notice tone="danger">{error}</Notice>}
        <Button type="submit" busy={busy} className="of-full">{initialized ? "Buka kunci" : "Buat ruang kerja terenkripsi"}<ArrowRight size={18} /></Button>
      </form>
      <p className="of-small of-muted">Ruang kerja terkunci saat tab disembunyikan atau tidak digunakan. Simpan cadangan terenkripsi: penghapusan data browser dapat menghapus data lokal, dan kunci yang hilang tidak dapat dipulihkan otomatis.</p>
      {!initialized && <Button variant="quiet" onClick={() => setRestore(true)}><Upload size={17} />Pulihkan cadangan terenkripsi</Button>}
      <a className="of-return-link" href="/">Kembali ke Meow Eyes</a>
    </section>
    {restore && <RestoreDialog onClose={() => setRestore(false)} onRestored={async () => { setRestore(false); await onRefresh(); }} />}
  </main>;
}

export function RestoreDialog({ onClose, onRestored, replacing = false }) {
  const [file, setFile] = useState(null); const [secret, setSecret] = useState(""); const [confirmed, setConfirmed] = useState(false);
  const [replaceConfirmation, setReplaceConfirmation] = useState("");
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const submit = async event => {
    event.preventDefault(); if (!file || !confirmed) return;
    if (file.size > 192 * 1024 * 1024) { setError("Berkas cadangan melebihi batas 192 MiB."); return; }
    setBusy(true); setError("");
    try { await vault.restoreBackup(file, secret, { confirmed: true, ...(replacing ? { replaceConfirmation } : {}) }); setSecret(""); await onRestored(); }
    catch (err) { setError(safeError(err)); }
    finally { setBusy(false); }
  };
  return <Modal title="Pulihkan cadangan terenkripsi" onClose={busy ? undefined : onClose}><form onSubmit={submit} className="of-form">
    <Notice>Cadangan diperiksa dan didekripsi sebelum dipasang. Gunakan frasa sandi cadangan, lalu buka kunci dengan akun lokal yang tersimpan di dalamnya.</Notice>
    <Field label="Berkas cadangan" required><input type="file" accept="application/json,.json,.optifit" onChange={e => setFile(e.target.files?.[0] || null)} required /></Field>
    <Field label="Frasa sandi cadangan" required><input type="password" value={secret} onChange={e => setSecret(e.target.value)} autoComplete="off" required maxLength={256} /></Field>
    {replacing && <><Notice tone="warning">Pemulihan mengganti seluruh vault aktif. Buat cadangan kondisi sekarang terlebih dahulu jika masih diperlukan.</Notice><Field label="Ketik GANTI VAULT" required><input value={replaceConfirmation} onChange={e => setReplaceConfirmation(e.target.value)} required autoComplete="off" /></Field></>}
    <label className="of-check"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} /><span>Saya memilih untuk memulihkan data dari cadangan ini.</span></label>
    {error && <Notice tone="danger">{error}</Notice>}
    <div className="of-actions"><Button variant="secondary" onClick={onClose} disabled={busy}>Batal</Button><Button type="submit" busy={busy} disabled={!confirmed || !file || (replacing && replaceConfirmation !== "GANTI VAULT")}>Periksa dan pulihkan</Button></div>
  </form></Modal>;
}
