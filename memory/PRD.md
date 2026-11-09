# Meow Eyes Marketplace — PRD

## Original Problem Statement
Aplikasi marketplace kacamata online bertema "Meow Eyes" untuk membeli frame, lensa, dan paket frame + lensa. Pengalaman marketplace lengkap (Shopee/Tokopedia-style) dengan katalog produk, cart, checkout (PIN), payment gateway (DOKU), ekspedisi (EVERPRO), inventory management, CMS admin, promo, flash sale, newsletter, subscription produk, mini games, roulette reward, poin, dashboard chart, export Excel.

**Phase 2 Additions:** Menu Shop Now (gabungan frame+lensa), Our Product (Product Knowledge), Article/Berita, Dynamic Banners, Reviews (hanya untuk order completed), Contact/FAQ/Privacy Policy, Role Staff dengan RBAC, Opsi bundle Frame + Lensa di detail produk, dan Import Produk Lanjutan via Excel dengan multiple pricing (varian warna).

## Stack Adaptation (User Confirmed)
- Backend: FastAPI (was: PHP CodeIgniter 4)
- Frontend: React + Tailwind + Shadcn UI (was: JavaScript+Bootstrap)
- Database: MongoDB (was: MySQL)
- Payment: MOCKED DOKU (`services_mock.doku_create_payment`)
- Shipping: MOCKED EVERPRO (`services_mock.everpro_cost`/`create_shipment`/`track`)
- Auth: Email/password + 6-digit PIN + Google SSO (Emergent Auth)
- Excel: openpyxl
- Charts: Recharts

## User Personas
1. **Customer** — browse, cart, checkout (PIN), pay, track, wishlist, play games, spin roulette, redeem points, subscribe newsletter, review completed orders.
2. **Staff** — content management with fine-grained permissions (article.view/create/update/delete, review.view/moderate, banner.*, product.*, order.*, report.*).
3. **Admin** — all staff permissions + products/categories/brands/orders/inventory/promos/users/newsletter management.
4. **Super Admin** — all admin + staff role/permission management (only super_admin can create admin accounts).

## What's Been Implemented

### 2026-02-11 — MVP (Iteration 1)
- Auth: register/login/google-session/me/logout, PIN setup+verify with 5-strike lockout
- Catalog: products/{slug}, categories (3-level tree), brands, homepage, flash-sales
- Cart, Wishlist, Addresses, Vouchers (validate), Reviews
- Checkout: shipping-options, preview, confirm (PIN required)
- Orders (list/detail/cancel), Payment confirm mock DOKU, cron/expire-orders
- Games (5/day, 50pts/game, 200pts/day cap), Roulette (weighted spin 3/day)
- Points logs, Newsletter subscribe, Product subscription
- Admin: dashboard chart endpoints, CRUD products/categories/orders/inventory/vouchers/flash-sales/roulette/users/newsletter/banners
- Excel exports for sales/inventory/flash-sales/roulette/games/newsletter/users/points
- Frontend: 30+ pages (customer + admin), Recharts, framer-motion roulette wheel

### 2026-08-07 — Phase 2 + RBAC (Iterations 2-4)
**Backend:**
- Content models: Article, ArticleCategory, ProductKnowledge, LensIndex, FAQItem, FAQCategory, CMSPage, ContactSetting, ContactMessage, BannerV2
- Public routes: /articles, /knowledge, /faqs, /pages/{slug}, /contact/info+send, /banners, /lens/indexes, /lens/options-for-frame/{frame_id}, /lens/recommended-bundle/{frame_id} (returns 3 curated Basic/Popular/Premium picks with pre-computed bundle_total + savings)
- Admin content routes: full CRUD for articles, knowledge, banners-v2, faqs, pages, contact-setting, lens/indexes, staff, reviews (list/moderate/analytics)
- Excel product import: /admin/products/import/{template,preview,commit} — multi-row-per-color creates one product with N variants
- Cart & Checkout bundle logic: `lens_product_id` + `lens_variant_id` + `lens_index_id` add-ons; subtotal = frame_price + lens_price + lens_index_additional_price
- Review gate: only status='completed' orders qualify; duplicate rejected per (user, product, order)
- **RBAC (Full Coverage)**: `require_permission(name)` factory + `current_admin_or_staff`; applied to article/banner/review/import + knowledge (article.*) + faq/page/contact (setting.*) + lens-indexes (product.*) routes. Staff role now respects every catalog permission.
- **APScheduler**: 4 background jobs — `expire-pending-orders` (5min), `activate-flash-sales` (1min), `poll-shipments` (10min), `auto-complete-orders` (60min, marks shipped→completed after 7 days). Admin endpoints: `GET /api/admin/scheduler/status`, `POST /api/admin/scheduler/run/{job_id}`. `/api/health` now returns `scheduler_running`.
- Staff seed: staff@meoweyes.id / Staff@123 / PIN 111222 with article.* + review.view/moderate permissions

**Frontend:**
- Pages: ShopNowPage, OurProductPage + detail, ArticleListPage + detail, ContactPage
- Admin pages: AdminContent module (AdminArticles, AdminKnowledge, AdminReviewsMod, AdminBannersV2, AdminFAQs, AdminPages, AdminContactSetting, AdminStaff, AdminImport, AdminLensIndexes)
- AdminLayout: `visibleNav` filters menu by role/permissions for staff
- ProtectedRoute: accepts staff for requireRole="admin"
- **Bundle Picks UI on ProductDetailPage**: 3-card layout (Paket Hemat/Populer/Premium) with pricing, savings badge, one-click "Ambil Paket Ini" → adds bundle to cart and navigates to /cart

### Bug Fixes (2026-08-07)
1. **CRITICAL** — models.py: CheckoutPreview was missing `courier_code`/`service_code`/`voucher_code`/`use_points`/`roulette_spin_id`/`selected_item_ids` (fields were misplaced inside ProductImportRow). Fixed → checkout preview/confirm now work.
2. **CRITICAL** — routes_shopping.py: POST /reviews returned 500 due to `insert_one` mutating doc with ObjectId `_id`. Fixed with `doc.pop("_id", None)` before return.
3. **MEDIUM** — seed.py: Voucher `end_at` extended from 30 to 365 days, refreshed on each boot so /vouchers/active always returns data.
4. **MEDIUM** — routes_shopping.py: Review gate now only accepts `status="completed"` (previously also allowed `shipped`, contradicting spec).
5. **MEDIUM** — seed.py: staff@meoweyes.id is now seeded idempotently.
6. **POLISH** — server.py: Invalid scheduler job_id now returns HTTP 400 (was 200 + ok:false); job exceptions caught and returned as 500.

## Test Results
- Iteration 1: 40/42 pytest (95%)
- Iteration 2 (Phase 2): 83/85 (97.6%) — 2 minor (voucher expiry, endpoint naming); no critical
- Iteration 3 (RBAC + regression): 21/21 (100%)
- **Iteration 4 (RBAC full + Bundle + Scheduler): 30/30 (100%)**

## Seed Data
- 3 users: admin@meoweyes.id / Admin@123 / PIN 123456 (super_admin); customer@meoweyes.id / Customer@123 / PIN 654321 (customer, 500 starter points); staff@meoweyes.id / Staff@123 / PIN 111222 (staff)
- 3 root + 10 frame subs + 40 frame_segment categories + lens/package subs (~60 total)
- 6 brands, 20 products (Frame/Lens/Package), 3 vouchers (365 days), 1 flash sale, 8 roulette rewards, 3 games, 5 lens indexes
- 4 articles, 22 product knowledge entries, 6 FAQs (4 categories), 5 CMS pages, 3 banners V2

## Prioritized Backlog

### P1 — Recommended next
- Real DOKU integration (replace mock) — needs DOKU sandbox credentials from user
- Real EVERPRO integration — needs EVERPRO API key from user
- Image upload to object storage (Cloudinary / Emergent storage) for product gallery, article thumbnails, banners
- Cron scheduler (APScheduler) for order expiry, flash sale activation, shipment polling
- Email sending via Resend (transactional + newsletter campaigns)
- Migrate remaining admin content routes (knowledge/faq/pages/contact-setting/lens-indexes) from `current_admin` to `require_permission` per full RBAC catalog

### P2 — Enhancement
- Search autocomplete UI (backend endpoint exists at /api/products/search-suggest)
- Real-time notifications (websocket / SSE)
- Tetris/Puzzle games proper (currently both stub to a Catch game)
- Product subscription notifications (stock/price drop)
- Customer review submit UI on order detail (backend ready; needs UI)
- 2-factor PIN via OTP for reset

## Architecture
```
/app
├── backend
│   ├── auth.py            (bcrypt, session, current_user, current_admin, require_permission)
│   ├── database.py        (motor async client + indexes)
│   ├── models.py          (Pydantic models, all UUID-based, ISO datetime)
│   ├── server.py          (FastAPI app, /api prefix, lifespan indexes)
│   ├── routes_auth.py     (register/login/google-session/me/pin/logout)
│   ├── routes_catalog.py  (public product catalog)
│   ├── routes_shopping.py (cart w/ lens bundle, wishlist, addresses, reviews)
│   ├── routes_orders.py   (checkout preview/confirm, orders, payment confirm)
│   ├── routes_engagement.py (games, roulette, points, newsletter, vouchers)
│   ├── routes_content.py  (articles, knowledge, faqs, pages, contact, banners, lens)
│   ├── routes_admin.py    (dashboard charts, admin CRUD)
│   ├── routes_admin_content.py (staff-permission-gated content CRUD + excel import)
│   ├── routes_export.py   (excel exports)
│   ├── services_mock.py   (DOKU + EVERPRO mocks)
│   ├── seed.py, seed_content.py
│   └── tests/             (pytest suite)
└── frontend/src
    ├── App.js             (BrowserRouter, hash-based OAuth callback detect)
    ├── contexts/AuthContext.jsx
    ├── components/{Layout/{MainLayout,AdminLayout}, AuthCallback, ProtectedRoute}
    └── pages/             (customer + admin/)
```
