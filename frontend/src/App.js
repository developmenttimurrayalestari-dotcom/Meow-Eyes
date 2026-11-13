import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "./contexts/AuthContext";

import MainLayout from "./components/Layout/MainLayout";
import AdminLayout from "./components/Layout/AdminLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import AuthCallback from "./components/AuthCallback";

import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import SetupPinPage from "./pages/SetupPinPage";
import ProductsPage from "./pages/ProductsPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import CartPage from "./pages/CartPage";
import CheckoutPage from "./pages/CheckoutPage";
import PaymentPage from "./pages/PaymentPage";
import OrdersPage from "./pages/OrdersPage";
import OrderDetailPage from "./pages/OrderDetailPage";
import WishlistPage from "./pages/WishlistPage";
import ProfilePage from "./pages/ProfilePage";
import AddressesPage from "./pages/AddressesPage";
import GamesPage from "./pages/GamesPage";
import GamePlayPage from "./pages/GamesRoundPage";
import VirtualTryOnPage from './pages/VirtualTryOnPage';
import AdminReturns from './pages/admin/AdminReturns';
import { AdminPointConversion, AdminPointMonitoring, AdminManageGames, AdminCashback } from './pages/admin/AdminLoyalty';
import RoulettePage from "./pages/RoulettePage";
import PointsPage from "./pages/WalletPage";
import VouchersPage from "./pages/VouchersPage";
import NewsletterPage from "./pages/NewsletterPage";
import StaticPage from "./pages/StaticPage";

import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminProducts from "./pages/admin/AdminProducts";
import AdminMeowsurement from "./pages/admin/AdminMeowsurement";
import AdminCategories from "./pages/admin/AdminCategories";
import AdminOrders from "./pages/admin/AdminOrders";
import AdminInventory from "./pages/admin/AdminInventory";
import { AdminVouchers, AdminFlashSales } from "./pages/admin/AdminPromos";
import { AdminUsers, AdminNewsletter } from "./pages/admin/AdminCustomers";
import AdminReports from "./pages/admin/AdminReports";
import { AdminWhatsApp, AdminTryOn } from "./pages/admin/AdminFeatures";
import AdminIntegrations from "./pages/admin/AdminIntegrations";
import FlashSalePage from "./pages/FlashSalePage";
import FloatingWhatsApp from "./components/FloatingWhatsApp";
import {
  AdminArticles, AdminKnowledge, AdminReviewsMod, AdminBannersV2,
  AdminFAQs, AdminPages, AdminContactSetting, AdminStaff, AdminImport, AdminLensIndexes,
} from "./pages/admin/AdminContent";
import ShopNowPage from "./pages/ShopNowPage";
import ArticleListPage from "./pages/ArticleListPage";
import ArticleDetailPage from "./pages/ArticleDetailPage";
import { OurProductPage, OurProductDetailPage } from "./pages/OurProductPage";
import ContactPage from "./pages/ContactPage";

const Shell = ({ children }) => <MainLayout>{children}</MainLayout>;

function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/setup-pin" element={<ProtectedRoute><SetupPinPage /></ProtectedRoute>} />

      {/* Admin */}
      <Route element={<ProtectedRoute requireRole="admin"><AdminLayout /></ProtectedRoute>}>
        <Route path="/admin/whatsapp" element={<AdminWhatsApp />} />
        <Route path="/admin/try-on" element={<AdminTryOn />} />
        <Route path="/admin/integrations" element={<AdminIntegrations />} />
        <Route path="/admin/dashboard" element={<AdminDashboard />} />
        <Route path="/admin/products" element={<AdminProducts />} />
        <Route path="/admin/meowsurement" element={<AdminMeowsurement />} />
        <Route path="/admin/categories" element={<AdminCategories />} />
        <Route path="/admin/orders" element={<AdminOrders />} />
        <Route path="/admin/inventory" element={<AdminInventory />} />
        <Route path="/admin/vouchers" element={<AdminVouchers />} />
        <Route path="/admin/flash-sales" element={<AdminFlashSales />} />
        <Route path="/admin/roulette" element={<Navigate to="/admin/games/roulette" replace />} />
        <Route path="/admin/games" element={<AdminManageGames />} />
        <Route path="/admin/games/:key" element={<AdminManageGames />} />
        <Route path="/admin/points/conversion" element={<AdminPointConversion />} />
        <Route path="/admin/points/customers" element={<AdminPointMonitoring />} />
        <Route path="/admin/cashback-events" element={<AdminCashback />} />
        <Route path="/admin/returns" element={<AdminReturns />} />
        <Route path="/admin/users" element={<AdminUsers />} />
        <Route path="/admin/newsletter" element={<AdminNewsletter />} />
        <Route path="/admin/reports" element={<AdminReports />} />
        <Route path="/admin/articles" element={<AdminArticles />} />
        <Route path="/admin/knowledge" element={<AdminKnowledge />} />
        <Route path="/admin/reviews" element={<AdminReviewsMod />} />
        <Route path="/admin/banners" element={<AdminBannersV2 />} />
        <Route path="/admin/faqs" element={<AdminFAQs />} />
        <Route path="/admin/pages" element={<AdminPages />} />
        <Route path="/admin/contact-setting" element={<AdminContactSetting />} />
        <Route path="/admin/staff" element={<AdminStaff />} />
        <Route path="/admin/import" element={<AdminImport />} />
        <Route path="/admin/lens-indexes" element={<AdminLensIndexes />} />
      </Route>

      {/* Customer routes within MainLayout */}
      <Route path="/" element={<Shell><HomePage /></Shell>} />
      <Route path="/flash-sale" element={<Shell><FlashSalePage /></Shell>} />
      <Route path="/new-arrival" element={<Shell><ProductsPage /></Shell>} />
      <Route path="/shop-now" element={<Shell><ShopNowPage /></Shell>} />
      <Route path="/our-product" element={<Shell><OurProductPage /></Shell>} />
      <Route path="/our-product/:slug" element={<Shell><OurProductDetailPage /></Shell>} />
      <Route path="/articles" element={<Shell><ArticleListPage /></Shell>} />
      <Route path="/articles/:slug" element={<Shell><ArticleDetailPage /></Shell>} />
      <Route path="/contact" element={<Shell><ContactPage /></Shell>} />
      <Route path="/products" element={<Shell><ProductsPage /></Shell>} />
      <Route path="/products/:slug" element={<Shell><ProductDetailPage /></Shell>} />
      <Route path="/category/:slug" element={<Shell><ProductsPage /></Shell>} />
      <Route path="/games" element={<Shell><GamesPage /></Shell>} />
      <Route path="/virtual-try-on" element={<Shell><VirtualTryOnPage /></Shell>} />
      <Route path="/games/:key" element={<Shell><GamePlayPage /></Shell>} />
      <Route path="/roulette" element={<Shell><RoulettePage /></Shell>} />
      <Route path="/newsletter" element={<Shell><NewsletterPage /></Shell>} />
      <Route path="/vouchers" element={<Shell><VouchersPage /></Shell>} />
      <Route path="/faq" element={<Shell><ContactPage /></Shell>} />
      <Route path="/terms" element={<Shell><StaticPage slug="syarat-ketentuan" pageType="terms_conditions" /></Shell>} />
      <Route path="/privacy" element={<Shell><StaticPage slug="kebijakan-privasi" pageType="privacy_policy" /></Shell>} />
      <Route path="/pages/:slug" element={<Shell><StaticPage /></Shell>} />

      {/* Protected customer pages */}
      <Route path="/cart" element={<ProtectedRoute><Shell><CartPage /></Shell></ProtectedRoute>} />
      <Route path="/checkout" element={<ProtectedRoute><Shell><CheckoutPage /></Shell></ProtectedRoute>} />
      <Route path="/payment/:orderNumber" element={<ProtectedRoute><Shell><PaymentPage /></Shell></ProtectedRoute>} />
      <Route path="/orders" element={<ProtectedRoute><Shell><OrdersPage /></Shell></ProtectedRoute>} />
      <Route path="/orders/:id" element={<ProtectedRoute><Shell><OrderDetailPage /></Shell></ProtectedRoute>} />
      <Route path="/wishlist" element={<ProtectedRoute><Shell><WishlistPage /></Shell></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Shell><ProfilePage /></Shell></ProtectedRoute>} />
      <Route path="/addresses" element={<ProtectedRoute><Shell><AddressesPage /></Shell></ProtectedRoute>} />
      <Route path="/points" element={<ProtectedRoute><Shell><PointsPage /></Shell></ProtectedRoute>} />

      <Route path="*" element={<Shell><HomePage /></Shell>} />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Toaster position="top-center" richColors closeButton />
          <AppRouter />
          <FloatingWhatsApp />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
