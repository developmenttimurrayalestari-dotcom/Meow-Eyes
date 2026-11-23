import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiError } from "../lib/api";
import { toast } from "sonner";
import { referralCode, rememberReferral } from '../lib/referral';
import FacebookAuthButton from "../components/FacebookAuthButton";
import GoogleAuthButton from "../components/GoogleAuthButton";
import { authDestination, navigateAfterAuthentication, requestedAuthReturn, usesCustomerMeasurementFlow } from "../lib/authReturn";

const RegisterPage = () => {
  const { register, phoneEnabled } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const returnTo = requestedAuthReturn(location);
  const [method, setMethod] = useState("email");
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [referral, setReferral] = useState(() => rememberReferral(new URLSearchParams(location.search).get('ref') || referralCode()));

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password.length < 8) {
      toast.error("Password minimal 8 karakter");
      return;
    }
    setLoading(true);
    try {
      const user = await register({ name: form.name, password: form.password, [phoneEnabled ? method : "email"]: form[phoneEnabled ? method : "email"], ...(referral ? { referral_code: referral } : {}) });
      toast.success(usesCustomerMeasurementFlow(returnTo) ? "Akun berhasil dibuat. Lengkapi profil dan resep untuk Meowsurement." : "Pendaftaran berhasil! Yuk atur PIN keamanan.");
      navigateAfterAuthentication(authDestination(returnTo, user?.has_pin), navigate);
    } catch (err) {
      toast.error(apiError(err, "Pendaftaran gagal"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-meow-bg flex items-center justify-center p-6" data-testid="register-page">
      <div className="max-w-md w-full bg-white rounded-[32px] shadow-meow-soft p-8 md:p-10">
        <div className="flex justify-center mb-6">
          <img src="/logo-meow.jpg" alt="Meow Eyes" className="h-20 w-20 rounded-full ring-4 ring-meow-salmon/30 object-cover" />
        </div>
        <h1 className="font-heading text-3xl font-black text-center">Daftar Meow Eyes</h1>
        <p className="text-center text-meow-gray mt-2 text-sm">Gabung gratis untuk menikmati manfaat member.</p>

        {phoneEnabled && <div className="mt-6 flex gap-2" role="group" aria-label="Metode registrasi">
          {[['email', 'Email'], ['phone', 'Nomor telepon']].map(([value, label]) => <button type="button" key={value} aria-pressed={method === value} disabled={loading} onClick={() => setMethod(value)} className={`flex-1 rounded-xl border px-3 py-2 text-sm font-bold ${method === value ? 'bg-meow-midnight text-white' : ''}`}>{label}</button>)}
        </div>}
        <form onSubmit={handleSubmit} className="mt-8 space-y-4" data-testid="register-form">
          {[
            { name: "name", label: "Nama Lengkap", type: "text", placeholder: "Nama kamu" },
            { name: phoneEnabled ? method : "email", label: phoneEnabled && method === "phone" ? "Nomor telepon" : "Email", type: phoneEnabled && method === "phone" ? "tel" : "email", placeholder: phoneEnabled && method === "phone" ? "08xxxxxxxxxx" : "email@kamu.com" },
            { name: "password", label: "Password (min. 8)", type: "password", placeholder: "••••••••" },
          ].map((f) => (
            <div key={f.name}>
              <label className="text-xs font-bold uppercase tracking-wider text-meow-gray">{f.label}</label>
              <input
                data-testid={`register-${f.name}`}
                name={f.name} type={f.type} required maxLength={f.name === "phone" ? 40 : undefined}
                value={form[f.name]} onChange={onChange}
                className="w-full mt-1 px-4 py-3 rounded-2xl border-2 border-transparent bg-meow-bg focus:bg-white focus:border-meow-salmon outline-none transition"
                placeholder={f.placeholder}
              />
            </div>
          ))}
          <label className="block text-sm">Kode referral (opsional)<input value={referral} maxLength={32} onChange={e => setReferral(rememberReferral(e.target.value))} className="mt-1 w-full px-4 py-3 rounded-2xl bg-meow-bg border" autoComplete="off" /></label>
          <button type="submit" disabled={loading} className="w-full btn-primary disabled:opacity-60" data-testid="register-submit-btn">
            {loading ? "Membuat akun..." : "Daftar"}
          </button>
        </form>

        <div className="my-6 flex items-center gap-2 text-xs text-meow-gray">
          <div className="h-px bg-meow-gray/30 flex-1" /><span>atau</span><div className="h-px bg-meow-gray/30 flex-1" />
        </div>
        <GoogleAuthButton signup returnTo={returnTo} disabled={loading} />
        <FacebookAuthButton returnTo={returnTo} disabled={loading} />

        <p className="text-center text-sm text-meow-gray mt-6">
          Sudah punya akun?{" "}
          <Link to={returnTo ? "/login?returnTo=" + encodeURIComponent(returnTo) : "/login"} className="text-meow-salmon font-bold" data-testid="login-link">Masuk</Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
