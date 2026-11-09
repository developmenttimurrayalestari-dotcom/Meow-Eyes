import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { api, setToken } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { Cat } from "lucide-react";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser } = useAuth();
  const [error, setError] = useState(null);
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;
    const hash = location.hash || window.location.hash;
    const params = new URLSearchParams(hash.replace(/^#/, ""));
    const sessionId = params.get("session_id");
    if (!sessionId) {
      navigate("/login", { replace: true });
      return;
    }
    (async () => {
      try {
        const { data } = await api.post("/auth/google-session", { session_id: sessionId });
        if (data.token) setToken(data.token);
        setUser(data.user);
        navigate(data.user?.has_pin ? "/" : "/setup-pin", { replace: true });
      } catch (e) {
        setError("Sesi Google gagal divalidasi. Silakan coba lagi.");
        setTimeout(() => navigate("/login", { replace: true }), 1800);
      }
    })();
  }, [location, navigate, setUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-meow-bg p-6" data-testid="auth-callback-screen">
      <div className="text-center">
        <img src="/logo-meow.jpg" alt="Meow Eyes" className="mx-auto h-16 w-16 rounded-full object-cover animate-pulse" />
        <p className="mt-4 font-heading text-2xl font-bold text-meow-midnight">Sedang masuk...</p>
        {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      </div>
    </div>
  );
};

export default AuthCallback;
