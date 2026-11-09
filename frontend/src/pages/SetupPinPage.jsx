import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, Cat } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { toast } from "sonner";

const SetupPinPage = () => {
  const { user, refreshMe } = useAuth();
  const navigate = useNavigate();
  const [pin, setPin] = useState(["", "", "", "", "", ""]);
  const [confirm, setConfirm] = useState(["", "", "", "", "", ""]);
  const [stage, setStage] = useState("enter");
  const inputs = useRef([]);

  useEffect(() => {
    inputs.current[0]?.focus();
  }, [stage]);

  const setAt = (arr, idx, val) => {
    const next = [...arr];
    next[idx] = val;
    return next;
  };

  const handle = (val, idx, target) => {
    if (!/^\d?$/.test(val)) return;
    const setter = target === "enter" ? setPin : setConfirm;
    const arr = target === "enter" ? pin : confirm;
    const next = setAt(arr, idx, val);
    setter(next);
    if (val && idx < 5) inputs.current[idx + 1]?.focus();
  };

  const handleNext = async () => {
    if (pin.some((p) => p === "")) {
      toast.error("PIN harus 6 digit");
      return;
    }
    setStage("confirm");
    inputs.current = [];
  };

  const handleSave = async () => {
    if (confirm.join("") !== pin.join("")) {
      toast.error("PIN konfirmasi tidak cocok");
      setConfirm(["", "", "", "", "", ""]);
      return;
    }
    try {
      await api.post("/auth/pin/setup", { pin: pin.join("") });
      toast.success("PIN keamanan tersimpan!");
      await refreshMe();
      navigate("/", { replace: true });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Gagal menyimpan PIN");
    }
  };

  const current = stage === "enter" ? pin : confirm;

  return (
    <div className="min-h-screen bg-meow-bg flex items-center justify-center p-6" data-testid="setup-pin-page">
      <div className="max-w-md w-full bg-white rounded-[32px] shadow-meow-soft p-8 md:p-10 text-center">
        <div className="flex justify-center mb-4">
          <div className="h-14 w-14 rounded-2xl bg-meow-amber grid place-items-center">
            <Shield className="h-7 w-7 text-meow-midnight" />
          </div>
        </div>
        <h1 className="font-heading text-3xl font-black">
          {stage === "enter" ? "Atur PIN Keamanan" : "Konfirmasi PIN"}
        </h1>
        <p className="text-sm text-meow-gray mt-2">
          {stage === "enter"
            ? "PIN 6 digit digunakan sebelum checkout. Pilih yang mudah diingat namun rahasia."
            : "Masukkan ulang PIN-mu untuk konfirmasi."}
        </p>

        <div className="flex justify-center gap-2 mt-8" data-testid="pin-input-row">
          {current.map((v, i) => (
            <input
              key={i}
              ref={(el) => (inputs.current[i] = el)}
              type="password" inputMode="numeric" maxLength={1}
              value={v}
              onChange={(e) => handle(e.target.value, i, stage)}
              onKeyDown={(e) => {
                if (e.key === "Backspace" && !current[i] && i > 0) inputs.current[i - 1]?.focus();
              }}
              className="w-12 h-14 text-center text-2xl font-bold rounded-2xl border-2 border-meow-midnight/10 bg-meow-bg focus:bg-white focus:border-meow-salmon outline-none"
              data-testid={`pin-input-${i}`}
            />
          ))}
        </div>

        <div className="mt-8">
          {stage === "enter" ? (
            <button onClick={handleNext} className="w-full btn-primary" data-testid="pin-next-btn">Lanjut</button>
          ) : (
            <div className="flex gap-2">
              <button onClick={() => { setStage("enter"); setConfirm(["", "", "", "", "", ""]); }} className="btn-secondary flex-1" data-testid="pin-back-btn">Ulang</button>
              <button onClick={handleSave} className="btn-primary flex-1" data-testid="pin-save-btn">Simpan PIN</button>
            </div>
          )}
        </div>
        {user?.has_pin && (
          <p className="text-xs text-meow-gray mt-6">
            <button onClick={() => navigate("/")} className="underline" data-testid="pin-skip-btn">Lewati untuk sekarang</button>
          </p>
        )}
      </div>
    </div>
  );
};

export default SetupPinPage;
