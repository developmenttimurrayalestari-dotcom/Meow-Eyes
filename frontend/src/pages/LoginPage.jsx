import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Cat, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { toast } from "sonner";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await login(email, password);
      toast.success("Selamat datang, " + user.name + "!");
      const dest = user.has_pin ? (location.state?.from || "/") : "/setup-pin";
      navigate(dest, { replace: true });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Gagal masuk");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = () => {
    const redirectUrl = window.location.origin + "/auth/callback";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen bg-meow-bg flex items-center justify-center p-6" data-testid="login-page">
      <div className="max-w-md w-full bg-white rounded-[32px] shadow-meow-soft p-8 md:p-10">
        <div className="flex justify-center mb-6">
          <img src="/logo-meow.jpg" alt="Meow Eyes" className="h-20 w-20 rounded-full ring-4 ring-meow-amber/30 object-cover" />
        </div>
        <h1 className="font-heading text-3xl font-black text-center">Masuk ke Meow Eyes</h1>
        <p className="text-center text-meow-gray mt-2 text-sm">Lanjutkan petualangan belanja kacamatamu.</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4" data-testid="login-form">
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-meow-gray">Email</label>
            <input
              data-testid="login-email"
              type="email" required
              value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full mt-1 px-4 py-3 rounded-2xl border-2 border-transparent bg-meow-bg focus:bg-white focus:border-meow-salmon outline-none transition"
              placeholder="email@kamu.com"
            />
          </div>
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-meow-gray">Password</label>
            <div className="relative">
              <input
                data-testid="login-password"
                type={showPwd ? "text" : "password"} required
                value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full mt-1 px-4 py-3 pr-12 rounded-2xl border-2 border-transparent bg-meow-bg focus:bg-white focus:border-meow-salmon outline-none transition"
                placeholder="••••••••"
              />
              <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-meow-gray" data-testid="toggle-pwd">
                {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          <button type="submit" disabled={loading} className="w-full btn-primary disabled:opacity-60" data-testid="login-submit-btn">
            {loading ? "Sedang masuk..." : "Masuk"}
          </button>
        </form>

        <div className="my-6 flex items-center gap-2 text-xs text-meow-gray">
          <div className="h-px bg-meow-gray/30 flex-1" />
          <span>atau</span>
          <div className="h-px bg-meow-gray/30 flex-1" />
        </div>

        <button onClick={handleGoogle} className="w-full flex items-center justify-center gap-3 py-3 rounded-full border-2 border-meow-midnight font-bold hover:bg-meow-midnight hover:text-white transition" data-testid="google-login-btn">
          <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.5h-1.9V20H24v8h11.3c-1.6 4.6-6 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34 6.5 29.3 4.5 24 4.5 13.2 4.5 4.5 13.2 4.5 24S13.2 43.5 24 43.5 43.5 34.8 43.5 24c0-1.2-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34 6.5 29.3 4.5 24 4.5 16.3 4.5 9.6 8.9 6.3 14.7z"/><path fill="#4CAF50" d="M24 43.5c5.2 0 9.8-2 13.4-5.2l-6.2-5.1c-2 1.4-4.5 2.3-7.2 2.3-5.3 0-9.7-3.4-11.3-8L6.2 32.6C9.5 38.5 16.3 43.5 24 43.5z"/><path fill="#1976D2" d="M43.6 20.5h-1.9V20H24v8h11.3c-.7 2.1-2.1 3.9-3.9 5.2l6.2 5.1c-.4.4 6.6-4.8 6.6-14.3 0-1.2-.1-2.4-.4-3.5z"/></svg>
          Masuk dengan Google
        </button>

        <p className="text-center text-sm text-meow-gray mt-6">
          Belum punya akun?{" "}
          <Link to="/register" className="text-meow-salmon font-bold" data-testid="register-link">Daftar di sini</Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
