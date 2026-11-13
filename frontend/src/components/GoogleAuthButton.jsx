import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../contexts/AuthContext";
import { api, apiError } from "../lib/api";
import { authDestination, navigateAfterAuthentication, rememberAuthReturn } from "../lib/authReturn";
import { googleNonce, loadGoogleIdentity } from "../lib/googleIdentity";

export default function GoogleAuthButton({ signup = false, returnTo = "", disabled = false }) {
  const { loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const host = useRef(null);
  const latest = useRef();
  latest.current = { loginWithGoogle, navigate, returnTo, disabled };
  const [phase, setPhase] = useState("loading");
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let disposed = false;
    let exchanging = false;
    const controller = new AbortController();
    const element = host.current;
    setPhase("loading");
    setError("");
    (async () => {
      try {
        const { data } = await api.get("/auth/google/config", { signal: controller.signal });
        if (disposed) return;
        if (!data.enabled || !data.client_id) { setPhase("unconfigured"); return; }
        const google = await loadGoogleIdentity();
        if (disposed) return;
        const nonce = googleNonce();
        google.initialize({
          client_id: data.client_id, nonce, auto_select: false, ux_mode: "popup",
          callback: async ({ credential }) => {
            if (disposed || exchanging || latest.current.disabled) return;
            if (!credential) { setError("Google belum mengirim identitas. Silakan coba lagi."); return; }
            exchanging = true;
            setPhase("busy");
            setError("");
            try {
              const user = await latest.current.loginWithGoogle(credential, nonce);
              if (disposed) return;
              rememberAuthReturn("");
              toast.success("Selamat datang, " + user.name + "!");
              navigateAfterAuthentication(authDestination(latest.current.returnTo, user.has_pin), latest.current.navigate);
            } catch (err) {
              if (!disposed) { setError(apiError(err, "Gagal masuk dengan Google. Silakan coba lagi.")); setPhase("ready"); }
            } finally { exchanging = false; }
          },
        });
        google.renderButton(element, { type: "standard", theme: "outline", size: "large", shape: "pill",
          text: signup ? "signup_with" : "signin_with", locale: "id",
          width: Math.min(400, element.clientWidth || 300) });
        setPhase("ready");
      } catch (err) {
        if (!disposed) { setError(apiError(err, err.message || "Login Google gagal dimuat.")); setPhase("error"); }
      }
    })();
    return () => { disposed = true; controller.abort(); element?.replaceChildren(); };
  }, [signup, attempt]);

  return <div data-testid={signup ? "google-register-btn" : "google-login-btn"}>
    <div ref={host} className={`${phase === "unconfigured" || phase === "error" ? "hidden" : "flex"} justify-center min-h-[44px] ${disabled || phase === "busy" ? "pointer-events-none opacity-60" : ""}`}
      aria-busy={phase === "busy"} />
    {phase === "loading" && <p className="text-center text-sm text-meow-gray" role="status">Memuat tombol Google...</p>}
    {phase === "busy" && <p className="text-center text-sm text-meow-gray" role="status">Memverifikasi akun Google...</p>}
    {phase === "unconfigured" && <p className="text-center text-sm text-meow-gray">Daftar/masuk Google belum tersedia. Silakan gunakan email dan password.</p>}
    {error && <p className="mt-2 text-center text-sm text-red-600" role="alert">{error}</p>}
    {phase === "error" && <button type="button" onClick={() => setAttempt((value) => value + 1)}
      className="mt-2 w-full text-sm font-bold text-meow-salmon">Muat ulang tombol Google</button>}
  </div>;
}
