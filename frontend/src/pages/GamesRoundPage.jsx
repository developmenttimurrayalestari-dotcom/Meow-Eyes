import React, { useEffect, useRef, useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import { api, apiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import SpaceWarGame from '../components/games/SpaceWarGame';
import { MatchingGame, SlidePuzzle } from '../components/games/BoardGames';
import '../styles/engagement.css';

export default function GamesRoundPage() {
  const { key } = useParams(), { user, refreshMe } = useAuth();
  const [game, setGame] = useState(null), [round, setRound] = useState(null), [levels, setLevels] = useState([]), [level, setLevel] = useState(1);
  const [error, setError] = useState(''), [busy, setBusy] = useState(false), [result, setResult] = useState(null), [seconds, setSeconds] = useState(0), pending = useRef(null), submitting = useRef(false);
  useEffect(() => { setRound(null); setResult(null); setGame(null); setError(''); api.get('/games').then(({ data }) => setGame(data.games.find(g => g.key === key) || false)).catch(e => setError(apiError(e))); api.get('/games/puzzle-levels').then(({ data }) => setLevels(data.levels)).catch(() => {}); }, [key]);
  useEffect(() => { if (!round || result) return; const tick = () => setSeconds(Math.max(0, round.snapshot.max_duration_seconds - Math.floor((Date.now() - new Date(round.started_at).getTime()) / 1000))); tick(); const id = setInterval(tick, 1000); return () => clearInterval(id); }, [round, result]);
  const start = async () => {
    setBusy(true); setError(''); pending.current = null; setResult(null);
    try { const { data } = await api.post(`/games/${key}/start`, { level: Number(level) }); setRound(data); }
    catch (e) { setError(apiError(e)); } finally { setBusy(false); }
  };
  const finish = async transcript => {
    pending.current = transcript; if (submitting.current) return; submitting.current = true; setBusy(true); setError('');
    try { const { data } = await api.post(`/game-sessions/${round.id}/finish`, transcript); setResult(data); if (refreshMe) await refreshMe(); }
    catch (e) { setError(apiError(e)); } finally { submitting.current = false; setBusy(false); }
  };
  if (game?.rule.engine === 'roulette') return <Navigate to="/roulette" replace />;
  return <div className="max-w-6xl mx-auto px-4 py-6">
    <Link to="/games" className="text-sm underline">Kembali ke Games</Link>
    <h1 className="font-heading text-3xl font-black mt-4">{game?.name || 'Meow Games'}</h1>
    {error && <p role="alert" className="my-4 rounded-xl bg-red-50 text-red-700 p-4">{error}</p>}
    {game === false && <p className="mt-4">Permainan tidak tersedia.</p>}
    {game && !round && <div className="bg-white rounded-3xl p-6 mt-5 space-y-4">
      <p>{game.description || 'Mainkan ronde untuk mengumpulkan poin belanja.'}</p>
      <p className="text-sm">Maksimal {game.rule.max_points} poin · waktu {game.rule.max_duration_seconds} detik · poin berlaku {game.rule.expiry_days} hari · jeda bermain {game.rule.cooldown_seconds / 3600} jam.</p>
      {game.rule.engine === 'slide_puzzle' && <label className="block">Pilih level <select value={level} onChange={e => setLevel(e.target.value)} className="loyalty-input ml-2">{levels.map(l => <option key={l.level} value={l.level}>Level {l.level} · {l.rows} × {l.columns}</option>)}</select></label>}
      {user ? <button className="btn-primary" disabled={busy} onClick={start}>{busy ? 'Menyiapkan…' : 'Mulai Bermain'}</button> : <Link className="btn-primary inline-block" to={`/login?redirect=${encodeURIComponent('/games/' + key)}`}>Masuk untuk Bermain</Link>}
    </div>}
    {round && !result && <div className="mt-5 bg-white rounded-3xl p-3 sm:p-5"><p className="text-sm font-bold mb-3">Sisa waktu: {seconds} detik {busy ? '· Menyimpan hasil…' : ''}</p>
      {round.snapshot.engine === 'space_war' ? <SpaceWarGame key={round.id} round={round} onFinish={finish} /> : seconds > 0 ? round.snapshot.engine === 'matching' ? <MatchingGame key={round.id} round={round} onFinish={finish} /> : <SlidePuzzle key={round.id} round={round} onFinish={finish} /> : <p>Waktu ronde habis. Tunggu jeda bermain untuk mencoba lagi.</p>}
      {error && pending.current && <button className="btn-secondary mt-3" disabled={busy} onClick={() => finish(pending.current)}>Coba Simpan Hasil Lagi</button>}
    </div>}
    {result && <div role="status" className="bg-meow-mint/10 p-8 rounded-3xl mt-5 text-center"><h2 className="text-2xl font-black">Ronde selesai!</h2><p className="mt-3">Skor {result.score} · +{result.points_awarded} poin</p><p className="text-sm mt-1">Poin berlaku {round.snapshot.expiry_days} hari dan mempertahankan rate saat ronde dimulai.</p><Link to="/points" className="btn-primary inline-block mt-4">Lihat Poin</Link></div>}
  </div>;
}
