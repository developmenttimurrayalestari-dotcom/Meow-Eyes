import FormField from "../FormField";
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Search, ShoppingCart, Heart, User, Cat, Menu as MenuIcon,
  Home, Sparkles, Gamepad2, X, LogOut, Coins, Bell, Tag } from
"lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { Button } from "../ui/button";
import {
  DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuLabel } from
"../ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger } from "../ui/sheet";
import FooterPages from "./FooterPages";
import { TranslationButtons } from '../ConveyThisTranslation';
import PromoPopup from '../PromoPopup';
import StorefrontMenus, { useStorefrontMenus } from '../StorefrontMenus';

const MainLayout = ({ children }) => {

  const { user, logout, cartCount } = useAuth();
  const navigate = useNavigate();
  const menus = useStorefrontMenus();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQ, setSearchQ] = useState("");

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQ.trim()) navigate(`/products?q=${encodeURIComponent(searchQ.trim())}`);
  };

  return (
    <div className="min-h-screen bg-meow-bg flex flex-col" data-testid="main-layout">
      <PromoPopup />
      <div className="flex justify-end px-4 md:px-8 py-1 bg-white border-b border-meow-midnight/5"><TranslationButtons /></div>
      {/* Marquee top bar */}
      <div className="bg-meow-midnight text-white text-xs overflow-hidden" data-testid="top-marquee">
        <div className="flex animate-marquee whitespace-nowrap py-2">
          {[...Array(2)].map((_, i) =>
          <div key={i} className="flex gap-12 px-6">
              <span>{"🎉 Gratis Ongkir min Rp 200.000"}</span>
              <span>{"⚡ Lihat Flash Sale yang sedang berlangsung"}</span>
              <span>{"🎁 Spin Roulette dapat poin & voucher"}</span>
              <span>{"🐱 Garansi 12 bulan untuk semua frame"}</span>
              <span>{"📦 Pilih kurir dan cek ongkir saat checkout"}</span>
            </div>
          )}
        </div>
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-white/70 border-b border-meow-midnight/5" data-testid="main-header">
        <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 flex items-center justify-between h-16 md:h-20">
          <Link to="/" className="flex items-center gap-2" data-testid="brand-link">
            <img src="/logo-meow.jpg" alt={"Meow Eyes"} className="h-11 w-11 rounded-full ring-2 ring-meow-amber/40 object-cover" />
            <div>
              <p className="font-heading font-black text-xl text-meow-midnight leading-none">{"Meow Eyes"}</p>
              {/* <p className="text-[10px] text-meow-gray tracking-widest uppercase">Catlux Marketplace</p> */}
            </div>
          </Link>

          {/* Search desktop */}
          <form onSubmit={handleSearch} className="hidden md:flex flex-1 max-w-xl mx-8" data-testid="search-form">
            <div className="flex items-center w-full bg-meow-bg border-2 border-transparent focus-within:border-meow-salmon focus-within:bg-white rounded-full px-5 py-2 transition-all">
              <Search className="h-4 w-4 text-meow-gray mr-2" />
              <FormField label={"Cari produk"} className="flex-1"><input
                  data-testid="search-input"
                  value={searchQ}
                  onChange={(e) => setSearchQ(e.target.value)}
                  placeholder={"Cari frame Leinz, Cat Eye, Lensa Blue Cut..."}
                  className="bg-transparent w-full outline-none text-sm placeholder:text-meow-gray" />
              </FormField>
              {searchQ &&
              <button type="button" onClick={() => setSearchQ("")} data-testid="search-clear">
                  <X className="h-4 w-4 text-meow-gray" />
                </button>
              }
            </div>
          </form>

          {/* Right icons */}
          <div className="flex items-center gap-2 md:gap-4">
            <button
              data-testid="search-mobile-btn"
              onClick={() => setSearchOpen(!searchOpen)}
              className="md:hidden p-2 rounded-full hover:bg-meow-bg">

              <Search className="h-5 w-5 text-meow-midnight" />
            </button>

            <Link to="/wishlist" className="hidden md:flex p-2 rounded-full hover:bg-meow-bg" data-testid="wishlist-link">
              <Heart className="h-5 w-5 text-meow-midnight" />
            </Link>

            <Link to="/cart" className="relative p-2 rounded-full hover:bg-meow-bg" data-testid="cart-link">
              <ShoppingCart className="h-5 w-5 text-meow-midnight" />
              {cartCount > 0 &&
              <span className="absolute -top-1 -right-1 bg-meow-salmon text-white text-[10px] font-bold rounded-full h-5 w-5 grid place-items-center">
                  {cartCount}
                </span>
              }
            </Link>

            {user ?
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button data-testid="profile-menu-btn" className="flex items-center gap-2 px-2 py-1.5 rounded-full hover:bg-meow-bg">
                    {user.picture ?
                  <img src={user.picture} alt="" className="h-8 w-8 rounded-full" /> :

                  <div className="h-8 w-8 rounded-full bg-meow-midnight text-meow-amber grid place-items-center font-bold">
                        {user?.["name"]?.[0]?.toUpperCase()}
                      </div>
                  }
                    <span className="hidden md:block text-sm font-semibold">{user?.["name"]?.split(" ")[0]}</span>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56" data-testid="profile-menu">
                  <DropdownMenuLabel>
                    <p className="font-bold">{user?.["name"]}</p>
                    <p className="text-xs text-meow-gray"><span className="conveythis-no-translate notranslate" translate="no" data-conveythis-private="">{user.email || user.phone}</span></p>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate("/profile")} data-testid="menu-profile">
                    <User className="h-4 w-4 mr-2" />{" Profil"}
                </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/orders")} data-testid="menu-orders">
                    <Tag className="h-4 w-4 mr-2" />{" Pesanan"}
                </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/wishlist")} data-testid="menu-wishlist">
                    <Heart className="h-4 w-4 mr-2" />{" Wishlist"}
                </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/points")} data-testid="menu-points">
                    <Coins className="h-4 w-4 mr-2" />{" Poin ("}{user.points_balance})
                  </DropdownMenuItem>
                  {(user.role === "admin" || user.role === "super_admin") &&
                <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => navigate("/admin/dashboard")} data-testid="menu-admin">
                        <Sparkles className="h-4 w-4 mr-2" />{" Admin Panel"}
                  </DropdownMenuItem>
                    </>
                }
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={async () => {await logout();navigate("/");}} data-testid="menu-logout">
                    <LogOut className="h-4 w-4 mr-2" />{" Keluar"}
                </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu> :

            <Link to="/login" className="btn-primary text-sm hidden sm:inline-block" data-testid="header-login-btn">{"Masuk"}

            </Link>
            }
          </div>
        </div>

        {/* Mobile search */}
        {searchOpen &&
        <form onSubmit={handleSearch} className="md:hidden px-4 pb-3" data-testid="mobile-search-form">
            <div className="flex items-center w-full bg-meow-bg border-2 border-meow-salmon rounded-full px-5 py-2">
              <Search className="h-4 w-4 text-meow-gray mr-2" />
              <FormField label={"Cari produk"} className="flex-1"><input
                data-testid="search-input-mobile"
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
                placeholder={"Cari kacamata..."}
                className="bg-transparent w-full outline-none text-sm"
                autoFocus />
            </FormField>
            </div>
          </form>
        }

        <div className="border-t border-meow-midnight/5 overflow-x-auto no-scrollbar">
          <StorefrontMenus items={menus} location="header" user={user} />
        </div>
      </header>

      <main className="flex-1">{children}</main>

      {/* Footer */}
      <footer className="bg-meow-midnight text-white mt-16 pt-12 pb-24 md:pb-12" data-testid="main-footer">
        <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 grid grid-cols-2 md:grid-cols-4 gap-8 text-sm">
          <div className="col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <img src="/logo-meow.jpg" alt="" className="h-9 w-9 rounded-full object-cover" />
              <p className="font-heading text-2xl font-black">{"Meow Eyes"}</p>
            </div>
            <p className="text-white/70 max-w-sm leading-relaxed">{"Marketplace kacamata online dengan ratusan pilihan frame & lensa. Stylish, premium, dan playful — buat mata kucingmu makin glow."}


            </p>
          </div>
          <div>
            <p className="font-bold mb-3 text-meow-amber">{"Bantuan"}</p>
            <ul className="space-y-2 text-white/70">
              <li><Link to="/faq" data-testid="footer-faq">{"FAQ"}</Link></li>
              <li><Link to="/contact" data-testid="footer-contact">{"Kontak"}</Link></li>
              <FooterPages />
            </ul>
          </div>
          <div>
            <p className="font-bold mb-3 text-meow-amber">{"Eksplorasi"}</p>
            <ul className="space-y-2 text-white/70"><StorefrontMenus items={menus} location="footer" user={user} /></ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-4 mt-12 text-center text-xs text-white/50">{"© 2026 Meow Eyes — Crafted with 🐾 for cat-eyed humans."}

        </div>
      </footer>

      <StorefrontMenus items={menus} location="mobile" user={user} cartCount={cartCount} />
    </div>);

};

export default MainLayout;
