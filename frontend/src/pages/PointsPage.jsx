import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { Coins, ArrowUpRight, ArrowDownRight } from "lucide-react";

const PointsPage = () => {
  const { user } = useAuth();
  const [logs, setLogs] = useState([]);
  useEffect(() => {
    api.get("/points/logs").then(({ data }) => setLogs(data.logs));
  }, []);
  return (
    <div className="max-w-3xl mx-auto px-4 md:px-6 py-8" data-testid="points-page">
      <div className="bg-meow-midnight text-white rounded-[32px] p-8 text-center">
        <Coins className="h-10 w-10 mx-auto text-meow-amber" />
        <p className="text-xs uppercase tracking-wider text-meow-amber mt-2">Saldo Poin</p>
        <p className="font-heading font-black text-5xl mt-1" data-testid="points-balance">{user?.points_balance ?? 0}</p>
        <p className="text-sm text-white/70 mt-2">≈ Rp {((user?.points_balance ?? 0) * 100).toLocaleString("id-ID")}</p>
      </div>
      <h2 className="font-heading text-2xl font-extrabold mt-8 mb-3">Riwayat Poin</h2>
      <div className="bg-white rounded-3xl divide-y divide-meow-midnight/5" data-testid="point-logs">
        {logs.length === 0 ? (
          <p className="p-6 text-center text-meow-gray">Belum ada aktivitas poin.</p>
        ) : (
          logs.map((l) => (
            <div key={l.id} className="p-4 flex items-center gap-3" data-testid={`point-log-${l.id}`}>
              <div className={`h-9 w-9 rounded-full grid place-items-center ${l.delta > 0 ? "bg-meow-mint/20 text-meow-mint" : "bg-red-100 text-red-500"}`}>
                {l.delta > 0 ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-bold text-sm">{l.type.replace(/_/g, " ")}</p>
                <p className="text-xs text-meow-gray line-clamp-1">{l.note || "-"}</p>
              </div>
              <p className={`font-bold ${l.delta > 0 ? "text-meow-mint" : "text-red-500"}`}>{l.delta > 0 ? "+" : ""}{l.delta}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default PointsPage;
