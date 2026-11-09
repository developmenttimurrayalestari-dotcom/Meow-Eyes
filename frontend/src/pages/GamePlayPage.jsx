import React, { useEffect, useState, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { Cat, Sparkles, Award, RotateCcw } from "lucide-react";
import { toast } from "sonner";

const ICONS = ["🐱", "👓", "🎀", "✨", "🐾", "🎯", "💎", "🌸"];

// Matching card game
const MatchingGame = ({ onScore }) => {
  const buildDeck = () => {
    const set = [...ICONS, ...ICONS].slice(0, 16);
    return set.map((emoji, i) => ({ id: i, emoji, flipped: false, matched: false }))
      .sort(() => Math.random() - 0.5);
  };
  const [deck, setDeck] = useState(buildDeck());
  const [first, setFirst] = useState(null);
  const [moves, setMoves] = useState(0);
  const [done, setDone] = useState(false);
  const submittedRef = useRef(false);

  const reset = () => {
    setDeck(buildDeck());
    setFirst(null); setMoves(0); setDone(false); submittedRef.current = false;
  };

  const click = (idx) => {
    if (deck[idx].flipped || deck[idx].matched || done) return;
    const next = [...deck];
    next[idx].flipped = true;
    setDeck(next);
    if (first === null) {
      setFirst(idx);
    } else {
      setMoves((m) => m + 1);
      if (next[first].emoji === next[idx].emoji) {
        next[first].matched = true;
        next[idx].matched = true;
        setDeck(next);
        setFirst(null);
        if (next.every((c) => c.matched)) {
          setDone(true);
          const score = Math.max(60, 800 - moves * 25);
          if (!submittedRef.current) {
            submittedRef.current = true;
            onScore(score);
          }
        }
      } else {
        const f = first;
        setTimeout(() => {
          const back = [...next];
          back[f].flipped = false;
          back[idx].flipped = false;
          setDeck(back);
          setFirst(null);
        }, 700);
      }
    }
  };

  return (
    <div data-testid="matching-game">
      <div className="flex justify-center gap-4 mb-4 text-sm font-bold">
        <span>Langkah: {moves}</span>
        <span>Pasangan: {deck.filter((c) => c.matched).length / 2}/8</span>
      </div>
      <div className="grid grid-cols-4 gap-2 max-w-md mx-auto">
        {deck.map((c, i) => (
          <button key={c.id} onClick={() => click(i)} className={`aspect-square rounded-2xl text-3xl font-bold ${c.flipped || c.matched ? "bg-meow-amber text-meow-midnight" : "bg-meow-midnight text-meow-amber"}`} data-testid={`card-${i}`}>
            {c.flipped || c.matched ? c.emoji : "?"}
          </button>
        ))}
      </div>
      {done && (
        <div className="mt-6 text-center" data-testid="game-done">
          <Award className="h-10 w-10 mx-auto text-meow-amber" />
          <p className="font-heading font-black text-2xl mt-2">Selesai!</p>
          <button onClick={reset} className="btn-gamified mt-4" data-testid="play-again-btn">
            <RotateCcw className="inline h-4 w-4 mr-2" /> Main Lagi
          </button>
        </div>
      )}
    </div>
  );
};

// Falling-icon catcher game (substitute for tetris/puzzle)
const CatchGame = ({ onScore }) => {
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(30);
  const [items, setItems] = useState([]);
  const [running, setRunning] = useState(false);
  const submittedRef = useRef(false);

  useEffect(() => {
    if (!running) return;
    const tick = setInterval(() => {
      setItems((prev) => prev.map((it) => ({ ...it, y: it.y + 4 })).filter((it) => it.y < 100));
      if (Math.random() < 0.4) {
        setItems((prev) => [
          ...prev,
          { id: Math.random(), x: Math.random() * 90, y: 0,
            emoji: ICONS[Math.floor(Math.random() * ICONS.length)],
            bad: Math.random() < 0.18 },
        ]);
      }
    }, 90);
    const timer = setInterval(() => setTime((t) => t - 1), 1000);
    return () => { clearInterval(tick); clearInterval(timer); };
  }, [running]);

  useEffect(() => {
    if (time <= 0 && running) {
      setRunning(false);
      if (!submittedRef.current) {
        submittedRef.current = true;
        onScore(score);
      }
    }
  }, [time, running, score, onScore]);

  const start = () => {
    setScore(0); setTime(30); setItems([]); setRunning(true); submittedRef.current = false;
  };
  const tap = (it) => {
    if (!running) return;
    if (it.bad) setScore((s) => Math.max(0, s - 20));
    else setScore((s) => s + 30);
    setItems((prev) => prev.filter((x) => x.id !== it.id));
  };

  return (
    <div data-testid="catch-game">
      <div className="flex justify-between max-w-md mx-auto mb-3 text-sm font-bold">
        <span>Skor: {score}</span>
        <span>Waktu: {time}s</span>
      </div>
      <div className="relative max-w-md mx-auto h-96 bg-meow-midnight rounded-3xl overflow-hidden" data-testid="catch-area">
        {!running && (
          <div className="absolute inset-0 grid place-items-center text-white">
            <div className="text-center">
              <p className="font-heading font-black text-xl">Tap ikon yang turun!</p>
              <p className="text-xs text-white/70 mt-1">Hindari yang berwarna merah</p>
              <button onClick={start} className="btn-gamified mt-3" data-testid="start-catch">
                ▶ Mulai
              </button>
            </div>
          </div>
        )}
        {items.map((it) => (
          <button key={it.id} onClick={() => tap(it)}
            className={`absolute text-3xl transition-transform ${it.bad ? "drop-shadow-[0_0_8px_red]" : ""}`}
            style={{ left: `${it.x}%`, top: `${it.y}%` }} data-testid={`falling-${it.id}`}>
            {it.bad ? "💀" : it.emoji}
          </button>
        ))}
      </div>
      {!running && time === 0 && (
        <div className="text-center mt-4">
          <p className="font-heading font-black text-2xl">Skor akhirmu: {score}</p>
          <button onClick={start} className="btn-gamified mt-2" data-testid="catch-replay">▶ Main lagi</button>
        </div>
      )}
    </div>
  );
};

const GamePlayPage = () => {
  const { key } = useParams();
  const { user, refreshMe } = useAuth();
  const navigate = useNavigate();

  const submitScore = async (score) => {
    try {
      const { data } = await api.post(`/games/${key}/submit`, { score });
      toast.success(`Skor ${score}! Dapat ${data.points_awarded} poin`);
      refreshMe();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Gagal submit skor");
    }
  };

  if (!user) {
    navigate("/login");
    return null;
  }

  let title = "Game";
  let GameComponent = MatchingGame;
  if (key === "matching") { title = "Match Meow Pairs"; GameComponent = MatchingGame; }
  else if (key === "puzzle") { title = "Meow Puzzle (Catch)"; GameComponent = CatchGame; }
  else if (key === "tetris") { title = "Glasses Tetris (Catch)"; GameComponent = CatchGame; }
  else return <div className="p-8 text-center"><Link to="/games" className="underline">Kembali ke daftar game</Link></div>;

  return (
    <div className="max-w-3xl mx-auto px-4 md:px-6 py-8" data-testid="game-play-page">
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-heading text-2xl md:text-3xl font-black">{title}</h1>
        <Link to="/games" className="text-sm text-meow-gray hover:text-meow-salmon">← Daftar Game</Link>
      </div>
      <div className="bg-white rounded-3xl p-6">
        <p className="text-sm text-meow-gray mb-4">
          Poinmu saat ini: <strong className="text-meow-salmon">{user.points_balance}</strong>
        </p>
        <GameComponent onScore={submitScore} />
      </div>
    </div>
  );
};

export default GamePlayPage;
