import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Gamepad2, Trophy } from "lucide-react";

const GamesPage = () => {
  const [games, setGames] = useState([]);
  useEffect(() => {
    api.get("/games").then(({ data }) => setGames(data.games));
  }, []);
  return (
    <div className="max-w-6xl mx-auto px-4 md:px-6 py-8" data-testid="games-page">
      <div className="text-center mb-8">
        <Gamepad2 className="h-10 w-10 mx-auto text-meow-salmon" />
        <h1 className="font-heading text-4xl md:text-5xl font-black mt-2">Mini Games Meow</h1>
        <p className="text-meow-gray mt-2">Main game, kumpulkan poin, tukar voucher belanja.</p>
        <p className="text-xs uppercase tracking-wider text-meow-salmon font-bold mt-3">Max 50 poin / game, 5 sesi / hari</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {games.map((g) => (
          <div key={g.id} className="meow-card overflow-hidden flex flex-col" data-testid={`game-card-${g.key}`}>
            <div className="aspect-video overflow-hidden bg-meow-bg">
              <img src={g.image} alt="" className="w-full h-full object-cover" />
            </div>
            <div className="p-5 flex-1 flex flex-col">
              <p className="font-heading font-extrabold text-xl">{g.name}</p>
              <p className="text-sm text-meow-gray mt-1">{g.description}</p>
              <Link to={`/games/${g.key}`} className="btn-gamified mt-4 text-center" data-testid={`play-game-${g.key}`}>
                ▶ Main Sekarang
              </Link>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12 bg-meow-amber/15 rounded-3xl p-8 text-center">
        <Trophy className="h-8 w-8 mx-auto text-meow-amber" />
        <p className="font-heading font-black text-2xl mt-2">Tukar Poin = Diskon Belanja</p>
        <p className="text-meow-gray text-sm mt-2">1 poin = Rp 100. Gunakan poin saat checkout untuk potongan harga.</p>
      </div>
    </div>
  );
};

export default GamesPage;
