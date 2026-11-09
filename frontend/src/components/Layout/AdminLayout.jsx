import React, { useState } from "react";
import { Link, NavLink, useNavigate, Outlet } from "react-router-dom";
import {
  LayoutDashboard, Package, FolderTree, Boxes, ShoppingBag,
  Truck, Tag, Zap, Ticket, Gamepad2, Target, Coins, Mail,
  Users, FileBarChart, Image, Cat, LogOut, ChevronLeft, ChevronRight, Menu, X,
  FileText, BookOpen, MessageSquare, Star, ShieldCheck, Upload, Layers, Glasses, Plug,
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";

const NAV = [
  { to: "/admin/dashboard", icon: LayoutDashboard, label: "Dashboard", testid: "admin-nav-dashboard", section: "main", perm: null },
  { to: "/admin/products", icon: Package, label: "Produk", testid: "admin-nav-products", section: "catalog", perm: "product.view" },
  { to: "/admin/import", icon: Upload, label: "Import Produk", testid: "admin-nav-import", section: "catalog", perm: "product.import" },
  { to: "/admin/categories", icon: FolderTree, label: "Kategori", testid: "admin-nav-categories", section: "catalog", perm: "product.view" },
  { to: "/admin/lens-indexes", icon: Layers, label: "Lens Indexes", testid: "admin-nav-lens", section: "catalog", perm: "product.view" },
  { to: "/admin/try-on", icon: Glasses, label: "Virtual Try-On", testid: "admin-nav-tryon", section: "catalog", perm: "product.update" },
  { to: "/admin/inventory", icon: Boxes, label: "Inventory", testid: "admin-nav-inventory", section: "catalog", perm: "product.update" },
  { to: "/admin/orders", icon: ShoppingBag, label: "Pesanan", testid: "admin-nav-orders", section: "sales", perm: "order.view" },
  { to: "/admin/reviews", icon: Star, label: "Review", testid: "admin-nav-reviews", section: "sales", perm: "review.view" },
  { to: "/admin/flash-sales", icon: Zap, label: "Flash Sale", testid: "admin-nav-flashsale", section: "sales", perm: null },
  { to: "/admin/vouchers", icon: Ticket, label: "Voucher", testid: "admin-nav-vouchers", section: "sales", perm: null },
  { to: "/admin/roulette", icon: Target, label: "Roulette", testid: "admin-nav-roulette", section: "engage", perm: null },
  { to: "/admin/newsletter", icon: Mail, label: "Newsletter", testid: "admin-nav-newsletter", section: "engage", perm: null },
  { to: "/admin/articles", icon: FileText, label: "Artikel", testid: "admin-nav-articles", section: "content", perm: "article.view" },
  { to: "/admin/knowledge", icon: BookOpen, label: "Product Knowledge", testid: "admin-nav-knowledge", section: "content", perm: "article.view" },
  { to: "/admin/banners", icon: Image, label: "Banner", testid: "admin-nav-banners", section: "content", perm: "banner.view" },
  { to: "/admin/faqs", icon: MessageSquare, label: "FAQ", testid: "admin-nav-faqs", section: "content", perm: "setting.view" },
  { to: "/admin/pages", icon: FileText, label: "CMS Pages", testid: "admin-nav-pages", section: "content", perm: "setting.view" },
  { to: "/admin/whatsapp", icon: MessageSquare, label: "WhatsApp", testid: "admin-nav-whatsapp", section: "content", perm: "setting.update" },
  { to: "/admin/integrations", icon: Plug, label: "Integrasi", testid: "admin-nav-integrations", section: "account", perm: null },
  { to: "/admin/contact-setting", icon: MessageSquare, label: "Contact", testid: "admin-nav-contact", section: "content", perm: "setting.update" },
  { to: "/admin/users", icon: Users, label: "Pelanggan", testid: "admin-nav-users", section: "account", perm: null },
  { to: "/admin/staff", icon: ShieldCheck, label: "Staff", testid: "admin-nav-staff", section: "account", perm: null },
  { to: "/admin/reports", icon: FileBarChart, label: "Laporan", testid: "admin-nav-reports", section: "account", perm: "report.view" },
];
const SECTIONS = [
  { key: "main", label: "" },
  { key: "catalog", label: "Katalog" },
  { key: "sales", label: "Penjualan" },
  { key: "engage", label: "Engagement" },
  { key: "content", label: "Konten CMS" },
  { key: "account", label: "Akun & Laporan" },
];

const AdminLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  // For staff, only show NAV items whose `perm` is in their permissions list.
  // Items with perm=null are admin/super_admin-only and are hidden from staff.
  const isStaff = user?.role === "staff";
  const visibleNav = NAV.filter((n) => {
    if (!isStaff) return true;
    if (!n.perm) return false;
    return (user?.permissions || []).includes(n.perm);
  });

  return (
    <div className="min-h-screen bg-meow-admin flex" data-testid="admin-layout">
      {/* Sidebar Desktop */}
      <aside className="hidden md:flex w-64 bg-meow-midnight text-white flex-col fixed inset-y-0">
        <div className="p-5 border-b border-white/10">
          <Link to="/admin/dashboard" className="flex items-center gap-2" data-testid="admin-brand">
            <img src="/logo-meow.jpg" alt="Meow Eyes" className="h-11 w-11 rounded-full ring-2 ring-meow-amber/40 object-cover" />
            <div>
              <p className="font-heading font-black text-lg leading-none">Meow Eyes</p>
              <p className="text-[10px] text-meow-amber tracking-widest uppercase">Admin Panel</p>
            </div>
          </Link>
        </div>
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {SECTIONS.map((sec) => (
            <div key={sec.key} className="mb-2">
              {sec.label && <p className="text-[10px] uppercase tracking-widest text-meow-amber/60 px-3 pt-3 pb-1">{sec.label}</p>}
              {visibleNav.filter((n) => n.section === sec.key).map((n) => (
                <NavLink
                  key={n.to} to={n.to} data-testid={n.testid}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-semibold transition-colors ${
                      isActive ? "bg-meow-amber text-meow-midnight" : "text-white/70 hover:bg-white/10 hover:text-white"
                    }`
                  }
                >
                  <n.icon className="h-4 w-4" />
                  {n.label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="p-3 border-t border-white/10">
          <div className="px-3 py-2 text-xs text-white/60">
            <p className="font-bold text-white">{user?.name}</p>
            <p>{user?.email}</p>
          </div>
          <button onClick={async () => { await logout(); navigate("/"); }} data-testid="admin-logout-btn"
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-white/70 hover:bg-white/10">
            <LogOut className="h-4 w-4" /> Keluar
          </button>
          <Link to="/" data-testid="admin-back-shop"
                className="mt-1 w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-meow-amber hover:bg-white/10">
            <ChevronLeft className="h-4 w-4" /> Ke Marketplace
          </Link>
        </div>
      </aside>

      {/* Mobile topbar */}
      <div className="md:hidden flex items-center justify-between p-4 bg-meow-midnight text-white fixed top-0 inset-x-0 z-30">
        <button onClick={() => setMobileOpen(true)} data-testid="admin-mobile-menu">
          <Menu className="h-5 w-5" />
        </button>
        <p className="font-heading font-black">Meow Eyes Admin</p>
        <Link to="/" className="text-meow-amber"><ChevronRight className="h-5 w-5" /></Link>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-black/50" onClick={() => setMobileOpen(false)}>
          <aside className="absolute left-0 top-0 bottom-0 w-72 bg-meow-midnight text-white p-5 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <p className="font-heading font-black text-xl">Admin Menu</p>
              <button onClick={() => setMobileOpen(false)} data-testid="admin-mobile-close"><X className="h-5 w-5" /></button>
            </div>
            <nav className="space-y-1">
              {SECTIONS.map((sec) => (
                <div key={sec.key}>
                  {sec.label && <p className="text-[10px] uppercase tracking-widest text-meow-amber/60 pt-3 pb-1">{sec.label}</p>}
                  {visibleNav.filter((n) => n.section === sec.key).map((n) => (
                    <NavLink
                      key={n.to} to={n.to} onClick={() => setMobileOpen(false)}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-semibold ${
                          isActive ? "bg-meow-amber text-meow-midnight" : "text-white/70 hover:bg-white/10"
                        }`
                      }
                    >
                      <n.icon className="h-4 w-4" /> {n.label}
                    </NavLink>
                  ))}
                </div>
              ))}
            </nav>
          </aside>
        </div>
      )}

      {/* Main content */}
      <main className="md:ml-64 flex-1 p-4 md:p-8 pt-20 md:pt-8" data-testid="admin-main">
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;
