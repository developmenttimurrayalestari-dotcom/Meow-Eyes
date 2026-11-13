import React, { useEffect, useState, useRef } from "react";
import { api } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { Target, Sparkles, Cat } from "lucide-react";
import { toast } from "sonner";
import { motion } from "framer-motion";

const RoulettePage = () => {
  const { user, refreshMe } = useAuth();
  const [rewards, setRewards] = useState([]);
  const [spinning, setSpinning] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [lastWin, setLastWin] = useState(null);
  const [history, setHistory] = useState([]);
  const wheelRef = useRef(null);

  const load = async () => {
    const { data } = await api.get("/roulette/rewards");
    setRewards(data.rewards);
  };
  const loadHistory = async () => {
    try {
      const { data } = await api.get("/roulette/my-rewards");
      setHistory(data.spins || []);
    } catch { /* not logged in */ }
  };

  useEffect(() => { load(); if (user) loadHistory(); }, [user]);

  const spin = async () => {
    if (!user) {
      toast.error("Login dulu untuk spin");
      return;
    }
    if (spinning) return;
    setSpinning(true);
    setLastWin(null);
    try {
      const { data } = await api.post("/roulette/spin");
      const idx = rewards.findIndex((r) => r.id === data.reward.id);
      const slice = 360 / rewards.length;
      const stopAngle = 360 * 5 + (360 - (idx * slice + slice / 2));
      setRotation((prev) => prev + stopAngle);
      setTimeout(() => {
        setSpinning(false);
        setLastWin(data.reward);
        loadHistory();
        refreshMe();
        toast.success(`Selamat! Kamu dapat ${data.reward.label}`);
      }, 4200);
    } catch (err) {
      setSpinning(false);
      toast.error(err?.response?.data?.detail || "Gagal spin");
    }
  };

  if (rewards.length === 0) {
    return <div className="min-h-[40vh] flex items-center justify-center"><Cat className="h-10 w-10 text-meow-salmon animate-pulse" /></div>;
  }

  const slice = 360 / rewards.length;

  return (
    <div className="max-w-4xl mx-auto px-4 md:px-6 py-8" data-testid="roulette-page">
      <div className="text-center mb-6">
        <Target className="h-10 w-10 mx-auto text-meow-roulette" />
        <h1 className="font-heading text-4xl md:text-5xl font-black mt-2">Meow Roulette</h1>
        <p className="text-meow-gray mt-2">Spin & dapatkan voucher, poin, atau gratis ongkir!</p>
        <p className="text-xs text-meow-salmon font-bold mt-3">Jeda bermain dan masa berlaku poin mengikuti pengaturan Roulette.</p>
      </div>

      <div className="bg-white rounded-[40px] p-8 grid md:grid-cols-2 gap-8 items-center">
        {/* Wheel */}
        <div className="flex justify-center" data-testid="roulette-wheel-wrap">
          <div className="relative w-72 h-72">
            <motion.div
              ref={wheelRef}
              animate={{ rotate: rotation }}
              transition={{ duration: 4.2, ease: [0.16, 0.92, 0.27, 1.0] }}
              className="absolute inset-0 rounded-full border-[8px] border-meow-midnight overflow-hidden"
              style={{
                background: `conic-gradient(${rewards.map((r, i) => `${r.color} ${i * slice}deg ${(i + 1) * slice}deg`).join(", ")})`,
              }}
              data-testid="roulette-wheel"
            >
              {rewards.map((r, i) => (
                <div key={r.id}
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 origin-[0%_0%] text-[10px] font-extrabold text-white"
                  style={{ transform: `translate(-50%, -50%) rotate(${i * slice + slice / 2}deg) translate(0, -100px) rotate(${-(i * slice + slice / 2)}deg)` }}>
                  {r.label.slice(0, 12)}
                </div>
              ))}
            </motion.div>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 h-12 w-12 rounded-full bg-meow-midnight grid place-items-center border-4 border-white">
              <Cat className="h-6 w-6 text-meow-amber" />
            </div>
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-20 w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[20px] border-t-meow-salmon" />
          </div>
        </div>

        {/* Action */}
        <div>
          <button onClick={spin} disabled={spinning} className="w-full btn-gamified text-lg disabled:opacity-50" data-testid="spin-btn">
            {spinning ? "Berputar..." : "🎯 SPIN SEKARANG"}
          </button>
          <p className="text-xs text-meow-gray mt-3">
            {user ? `Poinmu: ${user.points_balance}` : "Login dulu untuk spin"}
          </p>
          {lastWin && (
            <div className="mt-5 p-4 rounded-2xl bg-meow-amber/20 text-center" data-testid="roulette-last-win">
              <Sparkles className="h-6 w-6 mx-auto text-meow-amber" />
              <p className="font-heading font-black text-xl mt-1">{lastWin.label}</p>
              <p className="text-xs text-meow-gray">Reward akan otomatis tersedia di akun.</p>
            </div>
          )}

          <div className="mt-6">
            <p className="text-xs font-bold uppercase tracking-wider text-meow-gray mb-2">Daftar Reward</p>
            <ul className="text-sm space-y-1">
              {rewards.map((r) => (
                <li key={r.id} className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: r.color }} />
                  {r.label}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {history.length > 0 && (
        <div className="mt-8 bg-white rounded-3xl p-6" data-testid="roulette-history">
          <p className="font-heading font-extrabold text-xl mb-3">Riwayat Spin</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            {history.slice(0, 8).map((h) => (
              <div key={h.id} className="bg-meow-bg rounded-2xl p-3">
                <p className="font-bold">{h.reward_label}</p>
                <p className="text-xs text-meow-gray">{new Date(h.created_at).toLocaleString("id-ID")}</p>
                {h.used && <p className="text-xs text-meow-mint mt-1">✓ Digunakan</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RoulettePage;
