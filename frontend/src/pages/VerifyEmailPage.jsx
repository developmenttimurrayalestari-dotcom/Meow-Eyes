import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { api, apiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function VerifyEmailPage() {

  const { refreshMe } = useAuth();
  const [token] = useState(() => new URLSearchParams(window.location.hash.slice(1)).get('token') || '');
  const [busy, setBusy] = useState(false),[done, setDone] = useState(false),[error, setError] = useState('');
  const confirm = async () => {
    setBusy(true);setError('');
    try {await api.post('/auth/verification/confirm', { token });setDone(true);window.history.replaceState(null, '', window.location.pathname);await refreshMe();}
    catch (err) {setError(apiError(err, 'Email belum berhasil diverifikasi.'));} finally {setBusy(false);}
  };
  return <main className="min-h-screen bg-meow-bg grid place-items-center p-5"><section className="bg-white rounded-3xl p-8 max-w-lg w-full"><h1 className="text-2xl font-heading font-black">{"Verifikasi Email"}</h1>{done ? <p className="mt-4">{"Email berhasil diverifikasi. Voucher member baru dapat diklaim untuk transaksi pertama."}</p> : <><p className="my-4">{"Tekan tombol untuk mengonfirmasi alamat email akun Meow Eyes Anda."}</p><button disabled={busy || !token} onClick={confirm} className="btn-primary disabled:opacity-50">{busy ? "Memverifikasi…" : "Verifikasi Email Saya"}</button>{!token && <p role="alert" className="mt-3">{"Tautan tidak lengkap. Kirim ulang verifikasi melalui profil akun."}</p>}</>}{error && <p role="alert" className="mt-4 text-red-600">{error}</p>}<Link to="/profile" className="block mt-5 underline">{"Buka Profil Akun"}</Link></section></main>;
}
