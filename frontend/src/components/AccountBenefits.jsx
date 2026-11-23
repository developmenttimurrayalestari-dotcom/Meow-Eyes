import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, apiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

export default function AccountBenefits() {
  const { user, refreshMe } = useAuth();
  const [data, setData] = useState(null), [error, setError] = useState(''), [busy, setBusy] = useState(false), [retryAt, setRetryAt] = useState(0);
  const [now, setNow] = useState(Date.now());
  const [contact, setContact] = useState({ name: user.name, email: user.email || '', phone: user.phone || '' });
  const load = useCallback(async () => {
    try { const response = await api.get('/account/benefits'); setData(response.data); setError(''); }
    catch (err) { setError(apiError(err, 'Layanan akun belum dapat dimuat.')); }
  }, []);
  useEffect(() => { load(); const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, [load]);
  const action = async (url) => {
    if (busy) return; setBusy(true); setError('');
    try {
      await api.post(url);
      if (url.includes('resend')) { setRetryAt(Date.now() + 60000); toast.success('Email verifikasi dikirim. Periksa inbox atau spam.'); }
      else { await load(); await refreshMe(); toast.success('Check-in berhasil. Poin ditambahkan ke akun Anda.'); }
    } catch (err) { setError(apiError(err)); if (err.response?.status === 429) setRetryAt(Date.now() + Number(err.response.headers?.['retry-after'] || 60) * 1000); }
    finally { setBusy(false); }
  };
  const saveContact = async e => {
    e.preventDefault(); if (busy) return; setBusy(true); setError('');
    try { await api.patch('/account/contact', { name: contact.name, email: contact.email || null, phone: contact.phone || null }); await load(); await refreshMe(); toast.success('Data akun disimpan. Verifikasi ulang jika email berubah.'); }
    catch (err) { setError(apiError(err)); } finally { setBusy(false); }
  };
  const link = data?.referral_code ? `${window.location.origin}/register?ref=${encodeURIComponent(data.referral_code)}` : '';
  const countdown = Math.max(0, Math.ceil((retryAt - now) / 1000));
  return <section className="mt-6 space-y-4" data-testid="account-benefits">
    <div className="bg-white rounded-3xl p-5 border border-meow-midnight/10"><h2 className="font-heading text-xl font-black">Email & Kontak Akun</h2>
      <p className="text-sm my-3">{data?.email_verified_at ? `Email terverifikasi · ${new Date(data.email_verified_at).toLocaleDateString('id-ID')}` : 'Email belum terverifikasi. Verifikasi diperlukan untuk voucher member baru.'}</p>
      {!data?.email_verified_at && <button type="button" disabled={busy || countdown > 0 || !data?.email || !data?.email_delivery_ready} onClick={() => action('/auth/verification/resend')} className="btn-secondary text-sm disabled:opacity-50">{countdown ? `Kirim ulang dalam ${countdown} dtk` : 'Kirim Ulang Verifikasi'}</button>}
      {data && !data.email_delivery_ready && !data.email_verified_at && <p className="text-xs mt-2 text-amber-700">Pengiriman email sedang disiapkan toko.</p>}
      <details className="mt-4 text-sm"><summary className="cursor-pointer font-bold">Ubah nama, email, atau kontak</summary><form onSubmit={saveContact} className="mt-3 space-y-3"><fieldset disabled={busy} className="grid sm:grid-cols-2 gap-3">{[['name','Nama lengkap','text'],['email','Email','email'],['phone','Nomor kontak','tel']].map(([key,label,type]) => <label key={key}>{label}<input type={type} required={key !== 'phone'} value={contact[key]} onChange={e => setContact({ ...contact, [key]: e.target.value })} className="w-full mt-1 border rounded-xl p-2" /></label>)}</fieldset><button disabled={busy} className="btn-primary text-sm">Simpan Kontak</button></form></details>
    </div>
    {data?.config.checkin_enabled && <div className="bg-amber-50 rounded-3xl p-5 border border-amber-100"><div className="flex flex-wrap justify-between items-center gap-3"><div><h2 className="font-heading text-xl font-black">Daily Check-in</h2><p className="text-sm mt-1">{data.checkin_today ? 'Anda sudah check-in hari ini.' : 'Ambil poin harian Anda.'} Pergantian hari pukul 00.00 WIB.</p></div><button type="button" disabled={busy || data.checkin_today} className="btn-primary text-sm disabled:opacity-50" onClick={() => action('/account/check-in')}>{data.checkin_today ? 'Sudah Check-in' : 'Check-in Sekarang'}</button></div><div className="flex gap-2 mt-4 overflow-x-auto pb-1">{(data.config.use_streak ? data.config.streak_points : Array(7).fill(data.config.daily_points)).map((points, i) => <div key={i} className="flex-none min-w-[56px] rounded-xl bg-white p-2 text-center text-xs"><span className="block text-meow-gray">Hari {i+1}</span><strong>{points} poin</strong></div>)}</div><p className="text-xs mt-3">Streak terakhir: {data.last_checkin?.streak || 0} hari · {data.config.checkin_expiry_days === 0 ? 'Poin berlaku selamanya.' : `Poin berlaku ${data.config.checkin_expiry_days} hari.`}</p></div>}
    {data?.config.referral_enabled && <div className="bg-white rounded-3xl p-5 border border-meow-midnight/10"><h2 className="font-heading text-xl font-black">Ajak Teman</h2><p className="text-sm my-2">Kode <strong>{data.referral_code}</strong> · {data.referral_count} teman terdaftar.</p><p className="text-xs text-meow-gray">Reward diberikan {data.config.referral_trigger === 'registration' ? 'setelah teman mendaftar' : 'setelah transaksi pertama teman selesai'}.</p><input aria-label="Link referral" readOnly value={link} onFocus={e => e.target.select()} className="mt-3 w-full border rounded-xl p-2 text-xs" /><button type="button" className="btn-secondary text-sm mt-3" onClick={async () => { try { await navigator.clipboard.writeText(link); toast.success('Link disalin'); } catch { toast.error('Pilih dan salin link di atas.'); } }}>Salin Link Referral</button></div>}
    {error && <div role="alert" className="text-sm text-red-600"><p>{error}</p>{!data && <button type="button" onClick={load} className="underline mt-2">Coba lagi</button>}</div>}
    <Link to="/vouchers" className="inline-block text-sm font-bold text-meow-salmon">Lihat voucher Anda →</Link>
  </section>;
}
