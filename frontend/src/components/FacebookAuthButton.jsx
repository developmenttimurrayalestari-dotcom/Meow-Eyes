import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { api, apiError } from '../lib/api';
import { authDestination, navigateAfterAuthentication, rememberAuthReturn } from '../lib/authReturn';
import { loadFacebookIdentity } from '../lib/facebookIdentity';

export default function FacebookAuthButton({ returnTo = '', disabled = false }) {

  const { loginWithFacebook } = useAuth();
  const navigate = useNavigate();
  const [phase, setPhase] = useState('loading'),[error, setError] = useState(''),[attempt, setAttempt] = useState(0);
  const sdk = useRef(null),live = useRef(false),busy = useRef(false);
  useEffect(() => {
    let disposed = false;live.current = true;
    const controller = new AbortController();setPhase('loading');setError('');
    (async () => {
      try {
        const { data } = await api.get('/auth/facebook/config', { signal: controller.signal });
        if (disposed) return;
        if (!data?.enabled) {setPhase('unconfigured');return;}
        const fb = await loadFacebookIdentity();if (disposed) return;
        fb.init({ appId: data.app_id, version: data.version, cookie: false, xfbml: false, autoLogAppEvents: false });
        sdk.current = fb;setPhase('ready');
      } catch (err) {if (!disposed) {setError(apiError(err, err.message || 'Facebook gagal dimuat'));setPhase('error');}}
    })();
    return () => {disposed = true;live.current = false;controller.abort();};
  }, [attempt]);
  const login = () => {
    if (!sdk.current || disabled || busy.current) return;
    busy.current = true;setPhase('busy');setError('');
    let handled = false;
    try {
      // Keep FB.login directly within the click gesture so browsers allow its popup.
      sdk.current.login((response) => {
        if (!live.current || handled) return;
        handled = true;
        const token = response?.authResponse?.accessToken;
        if (!token) {busy.current = false;setPhase('ready');setError('Login Facebook dibatalkan atau izin belum diberikan.');return;}
        (async () => {
          try {
            const user = await loginWithFacebook(token);if (!live.current) return;
            rememberAuthReturn('');toast.success(`Selamat datang, ${user.name}!`);
            navigateAfterAuthentication(authDestination(returnTo, user.has_pin, user), navigate);
          } catch (err) {if (live.current) {setError(apiError(err, 'Gagal masuk dengan Facebook'));setPhase('ready');}} finally
          {busy.current = false;}
        })();
      }, { scope: 'public_profile,email', auth_type: 'rerequest' });
    } catch {busy.current = false;setPhase('error');setError('Jendela Facebook gagal dibuka. Silakan coba lagi.');}
  };
  return <div className="mt-3" data-testid="facebook-login">
    <button type="button" onClick={login} disabled={disabled || phase !== 'ready'} data-testid="facebook-login-btn"
    className="w-full flex items-center justify-center gap-3 rounded-full bg-[#1877F2] px-4 py-3 font-bold text-white disabled:opacity-50">
      <span aria-hidden="true" className="text-xl">{"f"}</span>{phase === 'busy' ? "Memverifikasi akun Facebook..." : "Masuk dengan Facebook"}
    </button>
    {phase === 'unconfigured' && <p className="mt-2 text-center text-sm text-meow-gray">{"Login Facebook belum tersedia."}</p>}
    {error && <p role="alert" className="mt-2 text-center text-sm text-red-600">{error}</p>}
    {phase === 'error' && <button type="button" onClick={() => setAttempt((value) => value + 1)} className="mt-2 w-full text-sm font-bold text-meow-salmon">{"Muat ulang Facebook"}</button>}
  </div>;
}
