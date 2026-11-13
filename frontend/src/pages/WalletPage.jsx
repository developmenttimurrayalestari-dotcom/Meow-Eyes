import React, { useEffect, useState } from 'react';
import { api, apiError, formatIDR } from '../lib/api';
export function WalletDetails({ wallet }) {
  if (!wallet) return null;
  return <div className="space-y-4"><div className="bg-meow-midnight text-white p-6 rounded-3xl"><p>Saldo Poin</p><p className="text-4xl font-black" data-testid="points-balance">{wallet.balance}</p><p className="mt-2">Nilai potongan {formatIDR(wallet.value)}</p><p className="text-xs mt-2 text-white/70">Nilai setiap perolehan dikunci pada rate asalnya.</p></div>
    <h2 className="text-xl font-bold">Poin yang Tersedia</h2>
    {(wallet.lots || []).map(l => <div className="p-4 rounded-2xl bg-white border" key={l.id}><strong>{l.remaining} poin</strong> · {formatIDR(l.rate_snapshot)} / poin<p className="text-xs mt-1">{l.source} · {l.expires_at ? `Berlaku sampai ${new Date(l.expires_at).toLocaleString('id-ID')}` : 'Tanpa kedaluwarsa'}</p></div>)}
    <h2 className="text-xl font-bold">Riwayat Poin</h2><div className="bg-white rounded-2xl divide-y" data-testid="point-logs">{wallet.logs?.length ? wallet.logs.map(l => <div key={l.id} className="p-4 flex justify-between gap-3"><div><p className="font-semibold">{l.note || l.type.replaceAll('_', ' ')}</p><p className="text-xs text-meow-gray">{new Date(l.created_at).toLocaleString('id-ID')} · rate {formatIDR(l.rate_snapshot)}</p></div><strong>{l.delta > 0 ? '+' : ''}{l.delta}</strong></div>) : <p className="p-4">Belum ada aktivitas poin.</p>}</div>
  </div>;
}
export default function WalletPage() {
  const [wallet, setWallet] = useState(null), [error, setError] = useState('');
  useEffect(() => { api.get('/points/logs').then(({ data }) => setWallet(data)).catch(e => setError(apiError(e))); }, []);
  return <div className="max-w-3xl mx-auto px-4 py-8"><h1 className="text-3xl font-black mb-6">Poin Saya</h1>{error && <p role="alert">{error}</p>}<WalletDetails wallet={wallet} /></div>;
}
