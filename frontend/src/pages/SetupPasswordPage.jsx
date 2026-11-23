import React, { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { api, apiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { authDestination, navigateAfterAuthentication, requestedAuthReturn } from '../lib/authReturn';

export default function SetupPasswordPage() {
  const { user, refreshMe, logout } = useAuth();
  const location = useLocation(), navigate = useNavigate();
  const [password, setPassword] = useState(''), [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const returnTo = requestedAuthReturn(location);
  if (user?.has_password) return <Navigate to={authDestination(returnTo, user.has_pin, user)} replace />;
  const save = async event => {
    event.preventDefault();
    if (busy) return;
    setError('');
    if (password !== confirm) { setError('Konfirmasi password tidak cocok.'); return; }
    if (new TextEncoder().encode(password).length > 72) { setError('Password maksimal 72 byte UTF-8.'); return; }
    setBusy(true);
    try {
      await api.post('/auth/password/setup', { password, confirm_password: confirm });
      const fresh = await refreshMe();
      if (!fresh) { setError('Password tersimpan. Muat ulang halaman untuk melanjutkan.'); return; }
      navigateAfterAuthentication(authDestination(returnTo, fresh.has_pin, fresh), navigate);
    } catch (err) { setError(apiError(err, 'Password belum berhasil disimpan.')); }
    finally { setBusy(false); }
  };
  return <main className="min-h-screen bg-meow-bg flex items-center justify-center p-6" data-testid="setup-password-page">
    <section className="max-w-md w-full bg-white rounded-[32px] shadow-meow-soft p-8">
      <Shield className="h-10 w-10 text-meow-salmon mb-4" />
      <h1 className="font-heading text-3xl font-black">Buat Password Akun</h1>
      <p className="mt-3 text-sm text-meow-gray">Lengkapi keamanan akun setelah masuk melalui Google/Facebook. Buat password baru untuk akun Meow Eyes agar Anda juga bisa masuk menggunakan email dan password.</p>
      <form onSubmit={save} className="mt-6 space-y-4">
        <fieldset disabled={busy} className="space-y-4">
          <label className="block text-sm">Password baru<input required type="password" autoComplete="new-password" minLength={8} maxLength={72} value={password} onChange={e => setPassword(e.target.value)} className="block w-full mt-1 rounded-xl border p-3" /></label>
          <label className="block text-sm">Konfirmasi password<input required type="password" autoComplete="new-password" minLength={8} maxLength={72} value={confirm} onChange={e => setConfirm(e.target.value)} className="block w-full mt-1 rounded-xl border p-3" /></label>
          <p className="text-xs text-meow-gray">Minimal 8 karakter. Setelah password tersimpan, lengkapi PIN 6 digit jika belum dibuat.</p>
          {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
          <button type="submit" className="btn-primary w-full">{busy ? 'Menyimpan…' : 'Simpan Password & Lanjut'}</button>
        </fieldset>
      </form>
      <button type="button" disabled={busy} className="mt-5 text-sm underline" onClick={async () => { await logout(); navigate('/login', { replace: true }); }}>Keluar</button>
    </section>
  </main>;
}
