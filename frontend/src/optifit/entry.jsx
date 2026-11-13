import React, { useEffect } from 'react';
import CustomerMeowsurementApp from './CustomerMeowsurementApp';
import { prepareOffline } from './offline';
import { serverWorkspace } from './storage/serverWorkspace';
import { setWorkspace } from './storage/workspace';
import { clearReportResources } from './reports';

class PrivateErrorBoundary extends React.Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { serverWorkspace.lock('application-error'); clearReportResources(); }
  render() {
    if (this.state.failed) return <main style={{ padding: 32, fontFamily: 'system-ui', maxWidth: 600 }}><h1>Tampilan pengukuran disembunyikan</h1><p>Aplikasi tidak dapat melanjutkan tampilan ini. Muat ulang untuk menghubungkan kembali akun Meow Eyes dan mengambil data yang sudah tersimpan.</p><button onClick={() => window.location.reload()}>Muat ulang</button></main>;
    return this.props.children;
  }
}
function PrivateWorkspace() {
  useEffect(() => {
    // Only static assets may be cached. Profile, prescriptions, photos and API
    // responses remain private and require the existing website session.
    void prepareOffline();
    const leaving = () => { serverWorkspace.lock('page-exit'); clearReportResources(); };
    window.addEventListener('pagehide', leaving);
    return () => window.removeEventListener('pagehide', leaving);
  }, []);
  return <CustomerMeowsurementApp />;
}
export function mountOptiFit(root) {
  if (window.location.pathname === '/meowsurement') window.history.replaceState(null, '', '/meowsurement/' + window.location.search);
  setWorkspace(serverWorkspace);
  document.title = 'Meowsurement - Meow Eyes';
  document.documentElement.lang = 'id';
  const description = document.querySelector('meta[name="description"]'); if (description) description.content = 'Pengukuran fitting dengan resep dari profil customer dan spesifikasi frame Meow Eyes.';
  const referrer = document.querySelector('meta[name="referrer"]'); if (referrer) referrer.content = 'no-referrer';
  const theme = document.querySelector('meta[name="theme-color"]'); if (theme) theme.content = '#176b5b';
  if (!document.querySelector('link[rel="manifest"]')) { const manifest = document.createElement('link'); manifest.rel = 'manifest'; manifest.href = '/meowsurement/manifest.webmanifest'; document.head.appendChild(manifest); }
  root.render(<React.StrictMode><PrivateErrorBoundary><PrivateWorkspace /></PrivateErrorBoundary></React.StrictMode>);
}
