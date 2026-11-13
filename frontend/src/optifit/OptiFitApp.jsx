import React, { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, ClipboardCheck, Eye, FileClock, Fingerprint, LockKeyhole, Moon, Settings2, ShieldCheck, Sun, UsersRound, Wifi, WifiOff } from "lucide-react";
import { vault } from "./storage/vault";
import { currentSessionData, latestRevision, STATUS_LABELS } from "./domain/workflow";
import { ALGORITHM_VERSION } from "./vision";
import VaultGate from "./components/VaultGate";
import { PatientDetail, PatientForm, PatientList } from "./components/Patients";
import SessionDataForm from "./components/SessionDataForm";
import { CaptureEditor, CapturePanel, CaptureViewer, Preparation } from "./components/CaptureWorkflow";
import { ResultsPanel, ReviewQueue } from "./components/Results";
import Settings, { AuditPanel, ROLE_LABELS } from "./components/Settings";
import { Button, DISCLAIMER, Field, Modal, Notice, StatusBadge, readableDate, safeError } from "./components/ui";
import "./optifit.css";

const NAV = [["patients", "Pasien", UsersRound], ["history", "Riwayat", FileClock], ["review", "Review", ClipboardCheck], ["settings", "Pengaturan", Settings2], ["audit", "Audit", Fingerprint]];

export default function OptiFitApp({ customerProfile = null, loadCustomerProfile = null, loadFrameCatalog = null, offlineStatus = {} }) {
  const [state, setState] = useState(null); const [actor, setActor] = useState(null); const [status, setStatus] = useState({ initialized: false, logins: [], locked: true });
  const [loading, setLoading] = useState(true); const [fatal, setFatal] = useState(""); const [page, setPage] = useState("patients"); const [patientId, setPatientId] = useState(null); const [sessionId, setSessionId] = useState(null);
  const [patientForm, setPatientForm] = useState(null); const [newSession, setNewSession] = useState(false); const [online, setOnline] = useState(navigator.onLine);
  const [theme, setTheme] = useState(() => { try { return localStorage.getItem("optifit-theme") || (window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light"); } catch { return "light"; } });
  const refreshSequence = useRef(0); const mounted = useRef(true);
  const refresh = useCallback(async () => {
    const sequence = ++refreshSequence.current;
    const next = vault.getState(); const user = vault.getUser();
    if (mounted.current) {
      setState(next); setActor(user);
      if (!next) { setPatientId(null); setSessionId(null); setPatientForm(null); setNewSession(false); setPage("patients"); }
    }
    try { const meta = await vault.status(); if (mounted.current && sequence === refreshSequence.current) { setStatus(meta); setFatal(""); } }
    catch (err) { if (mounted.current && sequence === refreshSequence.current) setFatal(safeError(err)); }
    finally { if (mounted.current && sequence === refreshSequence.current) setLoading(false); }
  }, []);
  useEffect(() => {
    mounted.current = true; const unsubscribe = vault.subscribe(() => { void refresh(); }); void refresh();
    const hidden = () => { if (document.hidden) vault.lock("hidden"); };
    const pagehide = () => vault.lock("page-hidden");
    const activity = () => vault.touch();
    const connection = () => setOnline(navigator.onLine);
    document.addEventListener("visibilitychange", hidden); window.addEventListener("pagehide", pagehide);
    document.addEventListener("pointerdown", activity, { passive: true }); document.addEventListener("keydown", activity);
    window.addEventListener("online", connection); window.addEventListener("offline", connection);
    return () => { mounted.current = false; unsubscribe(); document.removeEventListener("visibilitychange", hidden); window.removeEventListener("pagehide", pagehide); document.removeEventListener("pointerdown", activity); document.removeEventListener("keydown", activity); window.removeEventListener("online", connection); window.removeEventListener("offline", connection); vault.lock("module-unmounted"); };
  }, [refresh]);
  useEffect(() => { try { localStorage.setItem("optifit-theme", theme); } catch {} document.documentElement.style.colorScheme = theme; return () => { document.documentElement.style.colorScheme = ""; }; }, [theme]);
  useEffect(() => { const oldTitle = document.title; document.title = "Meowsurement"; return () => { document.title = oldTitle; }; }, []);
  const openPatient = id => { setPatientId(id); setSessionId(null); setPage("patients"); };
  const openSession = id => { const session = state.sessions.find(s => s.id === id); if (session) { setPatientId(session.patientId); setSessionId(id); setPage("patients"); } };
  const patient = state?.patients.find(p => p.id === patientId);
  const session = state?.sessions.find(s => s.id === sessionId);
  const saveSession = async (data, options) => {
    const saved = await vault.createSession({ patientId: patient.id, raw: { ...data, examinationDate: options.examinationDate }, examinationDate: options.examinationDate, algorithmVersion: ALGORITHM_VERSION, device: { model: data.deviceModel || "Tidak tersedia", platform: navigator.userAgentData?.platform || navigator.platform || "Tidak tersedia" }, consents: data.consents });
    setNewSession(false); setSessionId(saved.id);
  };
  return <div className={`of-app of-theme-${theme}`} data-testid="optifit-app">
    {loading ? <div className="of-loading" role="status"><ShieldCheck size={30} /><p>Memeriksa ruang kerja terenkripsi…</p></div> : fatal ? <main className="of-gate-panel of-error-screen"><h1>Ruang kerja belum dapat dibuka</h1><Notice tone="danger">{fatal}</Notice><p>Gunakan HTTPS atau localhost dan browser yang mengizinkan WebCrypto serta IndexedDB. Data tidak dialihkan ke penyimpanan tanpa enkripsi.</p><Button onClick={refresh}>Coba kembali</Button></main> : !state || !actor ? <VaultGate key={status.initialized ? "unlock" : "setup"} status={status} onRefresh={refresh} /> : <>
      <header className="of-app-header"><a className="of-wordmark" href="/meowsurement/" aria-label="Meowsurement"><span><Eye size={25} /></span><div><strong>Meowsurement</strong></div></a><div className="of-header-status"><span className="of-secure"><ShieldCheck size={15} />Lokal & terenkripsi</span><span title={offlineStatus.reason || ""}>{online ? <Wifi size={15} /> : <WifiOff size={15} />}{online ? "Online" : "Offline"} · {offlineStatus.ready ? "aplikasi siap offline" : "cache offline belum siap"}</span></div><div className="of-header-actions"><button type="button" className="of-icon-button" aria-label={theme === "dark" ? "Gunakan tema terang" : "Gunakan tema gelap"} onClick={() => setTheme(v => v === "dark" ? "light" : "dark")}>{theme === "dark" ? <Sun size={21} /> : <Moon size={21} />}</button><Button variant="secondary" onClick={() => vault.lock("manual")}><LockKeyhole size={17} />Kunci</Button></div></header>
      <div className="of-workspace"><aside className="of-sidebar"><div className="of-organization"><span className="of-eyebrow">RUANG KERJA</span><strong>{state.organization.name}</strong><small>{actor.displayName} · {ROLE_LABELS[actor.role]}</small></div><nav aria-label="Navigasi OptiFit">{NAV.map(([key, label, Icon]) => <button type="button" key={key} className={page === key ? "active" : ""} onClick={() => { setPage(key); setPatientId(null); setSessionId(null); }}><Icon size={20} /><span>{label}</span></button>)}</nav><div className="of-sidebar-note"><LockKeyhole size={21} /><p>Foto dan resep berada di vault perangkat ini. Tidak ada unggahan otomatis.</p></div><a href="/" className="of-store-link">← Ke Meow Eyes</a></aside>
        <main className="of-main" id="optifit-main">
          {page === "patients" && session && patient ? <SessionWorkspace key={session.id} state={state} actor={actor} session={session} patient={patient} onBack={() => setSessionId(null)} loadFrameCatalog={loadFrameCatalog} /> : page === "patients" && patient ? <PatientDetail patient={patient} state={state} actor={actor} onBack={() => setPatientId(null)} onEdit={() => setPatientForm(patient)} onNewSession={() => setNewSession(true)} onOpenSession={openSession} onDeleted={() => { setPatientId(null); setSessionId(null); }} /> : page === "patients" ? <PatientList state={state} actor={actor} onOpen={openPatient} onCreate={() => setPatientForm({})} /> : null}
          {page === "history" && <HistoryPanel state={state} onOpen={openSession} />}
          {page === "review" && <ReviewQueue state={state} onOpen={openSession} />}
          {page === "settings" && <><Notice>{offlineStatus.reason || "Status kesiapan offline akan tersedia setelah instalasi application shell."}</Notice><Settings state={state} actor={actor} onRefresh={refresh} /></>}
          {page === "audit" && <AuditPanel state={state} />}
          <footer className="of-module-footer"><ShieldCheck size={18} /><p>{DISCLAIMER}</p></footer>
        </main>
      </div>
      {patientForm && <PatientForm patient={patientForm.id ? patientForm : null} customerProfile={customerProfile} loadCustomerProfile={loadCustomerProfile} onClose={() => setPatientForm(null)} onSaved={saved => { setPatientForm(null); openPatient(saved.id); }} />}
      {newSession && patient && <Modal title={`Sesi baru · ${patient.fullName}`} wide onClose={() => setNewSession(false)}><SessionDataForm examinationDate={patient.examinationDate} onSave={saveSession} onCancel={() => setNewSession(false)} loadFrameCatalog={loadFrameCatalog} /></Modal>}
    </>}
  </div>;
}

function SessionWorkspace({ state, actor, session, patient, onBack, loadFrameCatalog }) {
  const [tab, setTab] = useState(() => session.status === "draft" && !currentSessionData(state, session).consents?.capture && actor.role !== "reviewer" ? "prepare" : "results"); const [selectedRevisionId, setSelectedRevisionId] = useState(null); const [captureId, setCaptureId] = useState(null);
  const revision = selectedRevisionId ? state.revisions.find(r => r.id === selectedRevisionId && r.sessionId === session.id) : latestRevision(state, session);
  const data = revision?.data || currentSessionData(state, session); const readOnly = revision?.id !== session.currentRevisionId;
  const canEdit = !readOnly && actor.role !== "reviewer";
  const save = async (next, reason) => { await vault.appendRevision(session.id, { data: next, reason, expectedRevisionId: revision.id }); setSelectedRevisionId(null); };
  const captures = data.captures || []; const selectedCapture = captures.find(c => c.id === captureId);
  const tabs = [["data", "1. Data"], ["prepare", "2. Persiapan"], ["capture", "3. Foto & titik"], ["results", "4. Hasil & review"], ["versions", "Riwayat revisi"]];
  if (!revision) return <Notice tone="danger">Revisi sesi tidak dapat ditemukan. Buka ulang riwayat pasien.</Notice>;
  return <>
    <Button variant="quiet" onClick={onBack}><ArrowLeft size={17} />Riwayat pasien</Button>
    <div className="of-page-heading"><div><span className="of-eyebrow">{patient.recordNumber}</span><h1>Pengukuran fitting</h1><p>{patient.fullName} · {readableDate(session.examinationDate)}</p></div><StatusBadge status={session.status} labels={STATUS_LABELS} /></div>
    <div className="of-session-toolbar"><Field label="Versi data yang ditampilkan"><select value={selectedRevisionId || session.currentRevisionId} onChange={e => { setSelectedRevisionId(e.target.value === session.currentRevisionId ? null : e.target.value); setCaptureId(null); }}>{state.revisions.filter(r => r.sessionId === session.id).map((r, index) => <option value={r.id} key={r.id}>Revisi {index + 1} · {readableDate(r.createdAt)} · {r.reason.slice(0, 75)}{r.id === session.currentRevisionId ? " (terbaru)" : ""}</option>)}</select></Field><small>Algoritma {session.algorithmVersion}<br />Operator {session.operatorName || state.users.find(u => u.id === session.createdBy)?.displayName || "Tercatat pada audit"}</small></div>
    {readOnly && <Notice>Anda sedang melihat revisi historis yang tidak dapat diubah. Pilih revisi terbaru untuk melanjutkan pengukuran atau review.</Notice>}
    <nav className="of-stepper" aria-label="Tahapan pengukuran">{tabs.map(([key, label]) => <button key={key} type="button" className={tab === key ? "active" : ""} onClick={() => setTab(key)}>{label}</button>)}</nav>
    {tab === "data" && (canEdit ? <section className="of-card"><h2>Revisi data sesi</h2><Notice>Perubahan hanya disimpan melalui tombol simpan. Resep dan frame awal tetap ada di riwayat.</Notice><SessionDataForm key={revision.id} data={data} examinationDate={session.examinationDate} editing onSave={async (next, options) => { await save(next, options.reason); setTab("prepare"); }} onCancel={() => setTab("results")} loadFrameCatalog={loadFrameCatalog} /></section> : <ReadonlyData data={data} />)}
    {tab === "prepare" && <Preparation key={revision.id} data={data} disabled={!canEdit} onSave={async (next, reason) => { await save(next, reason); setTab("capture"); }} />}
    {tab === "capture" && <CapturePanel data={data} session={session} patient={patient} onSave={save} onAnnotate={setCaptureId} disabled={!canEdit} />}
    {tab === "results" && <ResultsPanel state={state} patient={patient} session={session} revision={revision} data={data} actor={actor} onSave={save} readOnly={readOnly} />}
    {tab === "versions" && <section className="of-card"><h2>Riwayat revisi</h2><p className="of-muted">Nilai awal dan revisi sebelumnya tidak ditimpa oleh koreksi berikutnya.</p><div className="of-timeline">{state.revisions.filter(r => r.sessionId === session.id).map((r, index) => <article key={r.id}><span>{index + 1}</span><div><strong>{r.reason}</strong><p>{r.actorName || state.users.find(u => u.id === r.actorId)?.displayName || "Operator"} · {readableDate(r.createdAt)}</p><Button variant="quiet" onClick={() => { setSelectedRevisionId(r.id === session.currentRevisionId ? null : r.id); setTab("results"); }}>Lihat hasil revisi</Button></div></article>)}</div></section>}
    {selectedCapture && (canEdit && !selectedCapture.contextInvalidated && selectedCapture.photoRetained !== false ? <CaptureEditor key={selectedCapture.id} capture={selectedCapture} data={data} settings={state.settings} onClose={() => setCaptureId(null)} onSave={save} /> : <CaptureViewer key={selectedCapture.id} capture={selectedCapture} onClose={() => setCaptureId(null)} />)}
  </>;
}

function HistoryPanel({ state, onOpen }) {
  return <><div className="of-page-heading"><div><span className="of-eyebrow">CATATAN FITTING</span><h1>Riwayat sesi</h1><p>Semua sesi yang dapat diakses akun ini.</p></div><FileClock size={32} /></div><section className="of-card">{state.sessions.length ? <div className="of-session-list">{[...state.sessions].reverse().map(session => <button key={session.id} className="of-session-row" type="button" onClick={() => onOpen(session.id)}><FileClock size={23} /><span className="of-grow"><strong>{state.patients.find(p => p.id === session.patientId)?.fullName || "Pasien"}</strong><small>{readableDate(session.examinationDate)} · {session.algorithmVersion}</small></span><StatusBadge status={session.status} labels={STATUS_LABELS} /><span>→</span></button>)}</div> : <div className="of-empty"><FileClock size={36} /><h3>Belum ada sesi</h3><p>Daftarkan pasien dan buat sesi pengukuran pertama.</p></div>}</section></>;
}

function ReadonlyData({ data }) {
  return <section className="of-card"><h2>Data sesi tersimpan</h2><div className="of-grid-two">{[["od", "Mata Kanan (OD)"], ["os", "Mata Kiri (OS)"]].map(([eye, label]) => <div className="of-subcard" key={eye}><h3>{label}</h3>{["sph", "cyl", "axis", "add"].map(field => <div className="of-metric-row" key={field}><span>{field.toUpperCase()}</span><strong>{data.prescription?.[eye]?.[field] ?? "Belum dicatat"}</strong></div>)}</div>)}</div><h3>Frame</h3><p>{data.frame?.brand} {data.frame?.model}</p><div className="of-grid-four">{["a", "b", "dbl", "ed"].map(key => <div key={key}><small>{key.toUpperCase()}</small><strong className="of-block">{data.frame?.[key] ?? "Belum dicatat"} mm</strong></div>)}</div><p className="of-prewrap">{data.notes}</p></section>;
}
