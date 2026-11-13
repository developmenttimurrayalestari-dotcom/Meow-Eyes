import React, { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, FileClock, Glasses, LockKeyhole, Moon, RefreshCw, ShieldCheck, Sun, UserRound } from 'lucide-react';
import { serverWorkspace, workspaceError } from './storage/serverWorkspace';
import { setWorkspace } from './storage/workspace';
import { clearReportResources } from './reports';
import { currentSessionData, latestRevision, PARAMETER_LABELS, STATUS_LABELS } from './domain/workflow';
import { invalidateChangedMeasurementContext } from './domain/measurementContext';
import { CaptureEditor, CapturePanel, CaptureViewer, Preparation } from './components/CaptureWorkflow';
import { ResultsPanel } from './components/Results';
import { Button, DISCLAIMER, Field, Notice, StatusBadge, formatNumber, readableDate } from './components/ui';
import './optifit.css';
import './customer.css';
import NewMeasurement from './components/CustomerMeasurementSetup';
import MeasurementDashboard from './components/MeasurementDashboard';
import CustomerPreparation from './components/CustomerPreparation';
import { MEASUREMENT_TYPES, measurementType } from './domain/customerFlow';

function currentReturn() { return window.location.pathname + window.location.search; }
export function customerProfileURL() { return '/profile?required=meowsurement&returnTo=' + encodeURIComponent(currentReturn()); }
function loginURL() { return '/login?returnTo=' + encodeURIComponent(currentReturn()); }
const websiteReviewer = bootstrap => typeof bootstrap?.can_review === 'boolean' ? bootstrap.can_review : ['admin','super_admin'].includes(bootstrap?.user?.role) || (bootstrap?.user?.role === 'staff' && bootstrap.user.permissions?.includes('meowsurement.review'));

export default function CustomerMeowsurementApp({ store = serverWorkspace, navigate = url => window.location.assign(url), reviewSessionId = new URLSearchParams(window.location.search).get('review_session') }) {
  const [state,setState] = useState(store.getState()); const [bootstrap,setBootstrap] = useState(store.getBootstrap());
  const [loading,setLoading] = useState(true); const [error,setError] = useState(''); const [view,setView] = useState(reviewSessionId?'session':'menu');
  const [selectedType, setSelectedType] = useState(MEASUREMENT_TYPES[0]);
  const [sessionId,setSessionId] = useState(reviewSessionId || null); const [online,setOnline] = useState(navigator.onLine);
  const [theme,setTheme] = useState(()=>{try{return localStorage.getItem('optifit-theme') || 'light';}catch{return 'light';}});
  const mounted = useRef(false); const started = useRef(false); const generation = useRef(0);
  const refreshState = () => { if(mounted.current){setState(store.getState());setBootstrap(store.getBootstrap());} };
  const initialize = async () => {
    const sequence=++generation.current;setLoading(true);setError('');
    try {
      const body=await store.bootstrap();if(!mounted.current || sequence!==generation.current)return;
      if(reviewSessionId) {
        if(!websiteReviewer(body)) throw new Error('Halaman review memerlukan izin petugas Meow Eyes.');
        await store.loadSession(reviewSessionId);setSessionId(reviewSessionId);setView('session');
      } else {
        if(!body.ready) { navigate(customerProfileURL());return; }
        await store.listSessions();
        if(sessionId) await store.loadSession(sessionId);
      }
      if(mounted.current && sequence===generation.current){refreshState();started.current=true;}
    } catch(err) {
      if(!mounted.current || sequence!==generation.current)return;
      if(err?.response?.status===401) { store.clear('session-expired');navigate(loginURL());return; }
      setError(workspaceError(err,'Meowsurement memerlukan koneksi ke akun Meow Eyes. Coba kembali setelah terhubung.'));
    } finally {if(mounted.current && sequence===generation.current)setLoading(false);}
  };
  useEffect(()=>{
    mounted.current=true;setWorkspace(store);
    const unsubscribe=store.subscribe(refreshState);
    void initialize();
    const hidden=()=>{if(document.hidden){store.lock('privacy');clearReportResources();}};
    const unauthorized=()=>{store.clear('session-expired');clearReportResources();navigate(loginURL());};
    const tokenChanged=event=>{if(event.key==='meow_token'){store.clear('account-changed');clearReportResources();navigate('/meowsurement/');}};
    const connection=()=>setOnline(navigator.onLine);
    document.addEventListener('visibilitychange',hidden);window.addEventListener('meow:unauthorized',unauthorized);window.addEventListener('storage',tokenChanged);
    window.addEventListener('online',connection);window.addEventListener('offline',connection);
    return()=>{mounted.current=false;generation.current+=1;unsubscribe();document.removeEventListener('visibilitychange',hidden);window.removeEventListener('meow:unauthorized',unauthorized);window.removeEventListener('storage',tokenChanged);window.removeEventListener('online',connection);window.removeEventListener('offline',connection);store.lock('page-exit');clearReportResources();};
    // Entry has one authenticated workspace for the lifetime of the document.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[store]);
  useEffect(()=>{try{localStorage.setItem('optifit-theme',theme);}catch{}},[theme]);
  const openSession=async id=>{setError('');setLoading(true);try{await store.loadSession(id);setSessionId(id);setView('session');}catch(err){setError(workspaceError(err));}finally{setLoading(false);}};
  const profile=bootstrap?.profile;const actor=store.getUser();
  const session=state?.sessions.find(s=>s.id===sessionId);
  const patient=state?.sessionPatients[sessionId];
  const pause=()=>{store.lock('privacy');clearReportResources();};
  return <div className={'of-app of-theme-'+theme+' of-customer-app'} data-testid="customer-meowsurement">
    <header className="of-customer-header"><a href="/" className="of-wordmark"><img src="/logo-meow.jpg" alt="Meow Eyes" /><div>Meow Eyes<strong>Meowsurement</strong></div></a><div className="of-header-actions"><a href={customerProfileURL()} className="of-button of-button-quiet"><UserRound size={18}/>Profil & resep</a><button type="button" className="of-icon-button" aria-label={theme==='dark'?'Gunakan tema terang':'Gunakan tema gelap'} onClick={()=>setTheme(t=>t==='dark'?'light':'dark')}>{theme==='dark'?<Sun size={20}/>:<Moon size={20}/>}</button>{actor && <Button variant="secondary" onClick={pause}><LockKeyhole size={17}/>Privasi</Button>}</div></header>
    <main className="of-customer-main">
      {loading ? <section className="of-card of-loading" role="status"><RefreshCw className="of-spin"/><p>Mengambil data akun Meow Eyes…</p></section> : !state || !actor ? <section className="of-card of-customer-gate"><ShieldCheck size={36}/><h1>{started.current?'Tampilan pengukuran disembunyikan':'Hubungkan akun Meow Eyes'}</h1><p>{started.current?'Lanjutkan untuk memeriksa sesi akun yang sedang aktif dan membuka kembali data Anda.':'Meowsurement menggunakan profil, resep, dan login customer Meow Eyes.'}</p>{error && <Notice tone="danger">{error}</Notice>}<Button onClick={initialize}>{started.current?'Lanjutkan Meowsurement':'Coba kembali'}</Button><a href={loginURL()}>Masuk ke Meow Eyes</a></section> : <>
        {!online && <Notice tone="warning">Koneksi terputus. Pengolahan gambar dapat berlangsung di perangkat, tetapi penyimpanan perubahan memerlukan koneksi. Jangan menutup halaman sebelum perubahan berhasil tersimpan.</Notice>}
        {error && <Notice tone="danger">{error}</Notice>}
        {!reviewSessionId && <nav className="of-customer-tabs" aria-label="Meowsurement customer"><Button variant={['menu','new'].includes(view)?'primary':'secondary'} onClick={()=>{setView('menu');setSessionId(null);}}><Glasses size={18}/>Pengukuran baru</Button><Button variant={view==='history'?'primary':'secondary'} onClick={()=>setView('history')}><FileClock size={18}/>Riwayat saya</Button><Button variant="quiet" onClick={initialize}><RefreshCw size={17}/>Muat ulang data akun</Button></nav>}
        {view==='menu' && !reviewSessionId && <><div className="of-page-heading"><div><span className="of-eyebrow">MEOWSUREMENT</span><h1>Pilih pengukuran Anda</h1><p>Mulai dari satu jenis pengukuran. Frame toko tidak wajib; ukuran frame dapat diisi sendiri.</p></div></div><MeasurementDashboard onSelect={type=>{setSelectedType(type);setView('new');}}/><details className="of-card"><summary>Profil & resep {profile?.name}</summary><ProfileSummary profile={profile}/></details></>}
        {view==='new' && !reviewSessionId && <><Button variant="quiet" onClick={()=>setView('menu')}><ArrowLeft size={17}/>Semua jenis pengukuran</Button><NewMeasurement key={selectedType.id} type={selectedType} store={store} profile={profile} onCreated={detail=>{setSessionId(detail.session.id);setView('session');}}/></>}
        {view==='history' && <CustomerHistory state={state} store={store} onOpen={openSession}/>}
        {view==='session' && session && patient && <CustomerSession key={session.id} state={state} session={session} patient={patient} actor={actor} store={store} reviewerMode={!!reviewSessionId} onBack={()=>setView('history')}/>}
        {view==='session' && (!session || !patient) && <Notice tone="warning">Sesi belum tersedia. Muat ulang data akun untuk mengambil kembali hasil yang tersimpan.</Notice>}
      </>}
      <footer className="of-module-footer"><ShieldCheck size={19}/><p>{DISCLAIMER}</p></footer>
    </main>
  </div>;
}

export function ProfileSummary({profile}) {
  if(!profile)return null;
  return <section className="of-card of-profile-snapshot" data-testid="measurement-profile-snapshot"><div className="of-section-heading"><div><span className="of-eyebrow">OTOMATIS DARI PROFIL</span><h2>{profile.name}</h2><p>{profile.phone} · Tanggal lahir {readableDate(profile.birth_date)}</p></div><a href={customerProfileURL()} className="of-button of-button-secondary">Ubah di profil <ArrowRight size={17}/></a></div><PrescriptionSummary prescription={profile.prescription}/><p className="of-small of-muted">Tanggal resep: {readableDate(profile.prescription?.date)}. Resep merupakan input pemeriksaan profesional; kamera tidak menentukan SPH/CYL/AXIS/ADD.</p></section>;
}
function PrescriptionSummary({prescription={}}) {
  const pdReference=[['pd_total','total'],['pd_right','OD'],['pd_left','OS']].filter(([key])=>prescription[key]!=null).map(([key,label])=>label+' '+formatNumber(prescription[key])+' mm').join(' · ');
  return <><div className="of-grid-two">{[['od','Mata Kanan (OD)'],['os','Mata Kiri (OS)']].map(([side,title])=><div className="of-rx-summary" key={side}><strong>{title}</strong><div className="of-grid-four">{['sph','cyl','axis','add'].map(key=><span key={key}><small>{key.toUpperCase()}</small><b data-testid={'rx-'+side+'-'+key}>{prescription?.[side]?.[key]==null?'—':formatNumber(prescription[side][key])}</b></span>)}</div></div>)}</div>{pdReference&&<p className="of-small of-muted">PD pada resep: {pdReference}. Nilai referensi resep; hasil pengukuran sesi dicatat terpisah.</p>}</>;
}

export { NewMeasurement };
function ParameterChoices({parameters,onChange,distance,setDistance,disabled=false}) {
  return <><h3>Parameter yang diperiksa</h3><div className="of-checkbox-grid">{Object.entries(PARAMETER_LABELS).map(([key,label])=><label className="of-check" key={key}><input type="checkbox" disabled={disabled} checked={parameters.includes(key)} onChange={event=>onChange(event.target.checked?[...parameters,key]:parameters.filter(value=>value!==key))}/><span>{label}</span></label>)}</div>{parameters.includes('near_pd') && <Field label="Jarak kerja PD dekat (cm)" required><input type="number" min="1" step="0.1" disabled={disabled} value={distance} onChange={event=>setDistance(event.target.value)} required/></Field>}</>;
}
function CustomerHistory({state,store,onOpen}) {
  const [busy,setBusy]=useState(false);const [error,setError]=useState('');const pagination=state.sessionPagination||{page:1,total_pages:1};
  const go=async page=>{setBusy(true);setError('');try{await store.listSessions({page});}catch(err){setError(workspaceError(err));}finally{setBusy(false);}};
  return <><div className="of-page-heading"><div><span className="of-eyebrow">TERSIMPAN PADA AKUN ANDA</span><h1>Riwayat Meowsurement</h1><p>Setiap sesi mempertahankan resep, frame, dan revisinya sendiri.</p></div></div><section className="of-card">{error&&<Notice tone="danger">{error}</Notice>}{state.sessions.length?<div className="of-session-list">{[...state.sessions].sort((a,b)=>String(b.createdAt).localeCompare(String(a.createdAt))).map(session=><button className="of-session-row" key={session.id} type="button" onClick={()=>onOpen(session.id)}><Glasses size={24}/><span className="of-grow"><strong>{session.frameName || session.frameSnapshot?.model || 'Sesi pengukuran'}</strong><small>{readableDate(session.examinationDate)} · {session.id.slice(-10)}</small></span><StatusBadge status={session.status} labels={STATUS_LABELS}/><ArrowRight size={18}/></button>)}</div>:<div className="of-empty"><FileClock size={36}/><h3>Belum ada sesi pengukuran</h3><p>Pilih Pengukuran baru, lalu pilih jenis pengukuran dan sumber ukuran frame Anda.</p></div>}{pagination.total_pages>1&&<div className="of-actions"><Button variant="secondary" disabled={busy||pagination.page<=1} onClick={()=>go(pagination.page-1)}>Riwayat sebelumnya</Button><span>Halaman {pagination.page} dari {pagination.total_pages}</span><Button variant="secondary" disabled={busy||pagination.page>=pagination.total_pages} onClick={()=>go(pagination.page+1)}>Riwayat berikutnya</Button></div>}</section></>;
}
function CustomerSession({state,session,patient,actor,store,reviewerMode,onBack}) {
  const [tab,setTab]=useState(reviewerMode?'results':'prepare');const [revisionId,setRevisionId]=useState(null);const [captureId,setCaptureId]=useState(null);
  const revision=revisionId?state.revisions.find(r=>r.id===revisionId&&r.sessionId===session.id):latestRevision(state,session);
  const data=revision?.data || currentSessionData(state,session);const historical=revision?.id!==session.currentRevisionId;
  const owner=(session.createdBy || session.customerId || session.userId)===actor.id;const canEdit=owner&&!reviewerMode&&!historical;
  const selectedCapture=(data.captures||[]).find(c=>c.id===captureId);
  const save=async(next,reason)=>{await store.appendRevision(session.id,{data:next,reason,expectedRevisionId:revision.id});setRevisionId(null);};
  if(!revision)return <Notice tone="danger">Revisi sesi tidak ditemukan. Muat ulang sesi ini.</Notice>;
  return <>{reviewerMode?<a href="/admin/meowsurement" className="of-return-link">← Kembali ke review Meow Eyes</a>:<Button variant="quiet" onClick={onBack}><ArrowLeft size={17}/>Riwayat saya</Button>}
    <div className="of-page-heading"><div><span className="of-eyebrow">{reviewerMode?'REVIEW OLEH PETUGAS MEOW EYES':'PENGUKURAN CUSTOMER'}</span><h1>{reviewerMode ? data.frame?.model || 'Sesi Meowsurement' : measurementType(data.requiredParameters).title}</h1><p>{patient.fullName} · {readableDate(session.examinationDate)}</p></div><StatusBadge status={session.status} labels={STATUS_LABELS}/></div>
    <Field label="Revisi pengukuran"><select value={revisionId || session.currentRevisionId} onChange={event=>{setRevisionId(event.target.value===session.currentRevisionId?null:event.target.value);setCaptureId(null);}}>{state.revisions.filter(r=>r.sessionId===session.id).map((item,index)=><option key={item.id} value={item.id}>Revisi {index+1} · {item.reason}{item.id===session.currentRevisionId?' (terbaru)':''}</option>)}</select></Field>
    {historical && <Notice>Revisi historis dibuka dalam mode baca saja. Resep dan spesifikasi yang terlihat adalah snapshot sesi ini.</Notice>}
    <nav className="of-stepper" aria-label="Tahapan Meowsurement">{[['data','1. Profil & frame'],['prepare','2. Persiapan'],['capture','3. Foto & titik'],['results','4. Hasil & review']].map(([key,label])=><button key={key} type="button" className={tab===key?'active':''} onClick={()=>setTab(key)}>{label}</button>)}</nav>
    {tab==='data' && <><section className="of-card"><h2>Resep otomatis dari profil</h2><PrescriptionSummary prescription={data.prescription}/><p>{data.prescription?.notes}</p><Notice>Data sesi ini disalin dari profil customer saat pengukuran dimulai. Untuk resep baru, perbarui profil dan buat sesi baru.</Notice>{!reviewerMode && <a href={customerProfileURL()} className="of-button of-button-secondary">Buka profil & resep</a>}<h2>{data.frame?.sourceScope==='manual'?'Frame ukuran sendiri':'Frame dari toko'}</h2><p>{data.frame?.brand} · {data.frame?.model}</p><div className="of-grid-four">{[['a','A'],['b','B'],['dbl','DBL'],['ed','ED']].map(([key,label])=><div key={key}><small>{label}</small><strong className="of-block">{formatNumber(data.frame?.[key])} mm</strong></div>)}</div><p className="of-small of-muted">{data.frame?.sourceScope === 'manual' ? 'Ukuran yang Anda masukkan saat memulai sesi. Buat sesi baru jika frame atau ukurannya berubah.' : 'Ukuran mengikuti produk/varian terpilih saat sesi dibuat.'}</p></section>{reviewerMode && <SessionParameters key={revision.id} data={data} disabled={!canEdit} onSave={save}/>}</>}
    {tab==='prepare' && (reviewerMode ? <Preparation key={revision.id} data={data} serverMode disabled={!canEdit} onSave={async(next,reason)=>{await save(next,reason);setTab('capture');}}/> : <CustomerPreparation key={revision.id} data={data} disabled={!canEdit} onSave={async(next,reason)=>{await save(next,reason);setTab('capture');}}/>)}
    {tab==='capture' && <CapturePanel customerMode={!reviewerMode} data={data} session={session} patient={patient} disabled={!canEdit} onSave={save} onAnnotate={setCaptureId}/>}
    {tab==='results' && <ResultsPanel state={state} patient={patient} session={session} revision={revision} data={data} actor={actor} readOnly={historical} onSave={save} customerMode={!reviewerMode} canEdit={canEdit}/>}
    {selectedCapture && (canEdit&&!selectedCapture.contextInvalidated&&selectedCapture.photoRetained!==false?<CaptureEditor customerMode={!reviewerMode} key={selectedCapture.id} capture={selectedCapture} data={data} settings={state.settings} onClose={()=>setCaptureId(null)} onSave={save}/>:<CaptureViewer key={selectedCapture.id} capture={selectedCapture} onClose={()=>setCaptureId(null)}/>)}
  </>;
}
function SessionParameters({data,disabled,onSave}) {
  const [parameters,setParameters]=useState(data.requiredParameters||['distance_pd']);const [distance,setDistance]=useState(data.workingDistanceCm||40);const [notes,setNotes]=useState(data.notes||'');const [reason,setReason]=useState('');const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const submit=async event=>{event.preventDefault();if(disabled||!parameters.length)return;setBusy(true);setError('');try{await onSave(invalidateChangedMeasurementContext(data,{...data,requiredParameters:parameters,workingDistanceCm:Number(distance),notes}),reason);}catch(err){setError(workspaceError(err));}finally{setBusy(false);}};
  return <section className="of-card"><form onSubmit={submit} className="of-form"><ParameterChoices parameters={parameters} onChange={setParameters} distance={distance} setDistance={setDistance} disabled={disabled}/><Field label="Catatan pengukuran"><textarea value={notes} onChange={event=>setNotes(event.target.value)} maxLength={6000} disabled={disabled}/></Field>{!disabled && <><Field label="Alasan perubahan pengukuran" required><textarea value={reason} onChange={event=>setReason(event.target.value)} minLength={5} maxLength={1000} required/></Field><Notice>Perubahan jarak kerja membatalkan hasil yang menggunakan jarak sebelumnya. Hasil lama tetap tersimpan pada revisinya.</Notice>{error&&<Notice tone="danger">{error}</Notice>}<Button type="submit" busy={busy} disabled={!parameters.length}>Simpan revisi pengukuran</Button></>}</form></section>;
}
