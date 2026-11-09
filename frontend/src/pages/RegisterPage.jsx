import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Cat } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { toast } from "sonner";

const RegisterPage = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password.length < 8) {
      toast.error("Password minimal 8 karakter");
      return;
    }
    setLoading(true);
    try {
      await register(form);
      toast.success("Pendaftaran berhasil! Yuk atur PIN keamanan.");
      navigate("/setup-pin", { replace: true });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Pendaftaran gagal");
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
        <p className="text-center text-meow-gray mt-2 text-sm">Gabung gratis, dapat 500 poin sambutan.</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4" data-testid="register-form">
          {[
            { name: "name", label: "Nama Lengkap", type: "text", placeholder: "Nama kamu" },
            { name: "email", label: "Email", type: "email", placeholder: "email@kamu.com" },
            { name: "password", label: "Password (min. 8)", type: "password", placeholder: "••••••••" },
          ].map((f) => (
            <div key={f.name}>
              <label className="text-xs font-bold uppercase tracking-wider text-meow-gray">{f.label}</label>
              <input
                data-testid={`register-${f.name}`}
                name={f.name} type={f.type} required
                value={form[f.name]} onChange={onChange}
                className="w-full mt-1 px-4 py-3 rounded-2xl border-2 border-transparent bg-meow-bg focus:bg-white focus:border-meow-salmon outline-none transition"
                placeholder={f.placeholder}
              />
            </div>
          ))}
          <button type="submit" disabled={loading} className="w-full btn-primary disabled:opacity-60" data-testid="register-submit-btn">
            {loading ? "Membuat akun..." : "Daftar"}
          </button>
        </form>

        <p className="text-center text-sm text-meow-gray mt-6">
          Sudah punya akun?{" "}
          <Link to="/login" className="text-meow-salmon font-bold" data-testid="login-link">Masuk</Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
