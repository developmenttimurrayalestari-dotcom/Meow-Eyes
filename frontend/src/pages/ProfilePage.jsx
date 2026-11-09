import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Cat, MapPin, Coins, Ticket, BellRing, ShoppingBag, Shield, Mail } from "lucide-react";

const ProfilePage = () => {
  const { user } = useAuth();
  if (!user) return null;
  const links = [
    { to: "/orders", icon: ShoppingBag, label: "Pesanan", testid: "p-orders" },
    { to: "/addresses", icon: MapPin, label: "Alamat", testid: "p-addresses" },
    { to: "/points", icon: Coins, label: `Poin (${user.points_balance})`, testid: "p-points" },
    { to: "/vouchers", icon: Ticket, label: "Voucher", testid: "p-vouchers" },
    { to: "/wishlist", icon: BellRing, label: "Wishlist", testid: "p-wishlist" },
    { to: "/setup-pin", icon: Shield, label: user.has_pin ? "Ubah PIN" : "Setup PIN", testid: "p-pin" },
    { to: "/newsletter", icon: Mail, label: "Newsletter", testid: "p-newsletter" },
  ];
  return (
    <div className="max-w-3xl mx-auto px-4 md:px-6 py-8" data-testid="profile-page">
      <div className="bg-meow-midnight text-white rounded-[32px] p-8" data-testid="profile-card">
        <div className="flex items-center gap-4">
          {user.picture ? (
            <img src={user.picture} alt="" className="h-16 w-16 rounded-full" />
          ) : (
            <div className="h-16 w-16 rounded-full bg-meow-amber text-meow-midnight grid place-items-center font-heading text-2xl font-black">
              {user.name?.[0]?.toUpperCase()}
            </div>
          )}
          <div>
            <p className="font-heading text-2xl font-black">{user.name}</p>
            <p className="text-white/70 text-sm">{user.email}</p>
            <p className="text-meow-amber text-xs uppercase tracking-wider font-bold mt-1">{user.role}</p>
          </div>
        </div>
        <div className="mt-6 grid grid-cols-3 gap-3 text-center">
          <Stat label="Poin" value={user.points_balance} />
          <Stat label="PIN" value={user.has_pin ? "Aktif" : "Belum"} />
          <Stat label="Status" value={user.is_active === false ? "Off" : "Aktif"} />
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-3" data-testid="profile-links">
        {links.map((l) => (
          <Link key={l.to} to={l.to} className="bg-white rounded-3xl p-5 hover:shadow-meow-soft flex flex-col items-center text-center" data-testid={l.testid}>
            <l.icon className="h-6 w-6 text-meow-salmon" />
            <span className="mt-2 font-bold text-sm">{l.label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
};

const Stat = ({ label, value }) => (
  <div className="bg-white/5 rounded-2xl p-3">
    <p className="font-heading font-black text-2xl">{value}</p>
    <p className="text-xs text-white/60 uppercase tracking-wider">{label}</p>
  </div>
);

export default ProfilePage;
