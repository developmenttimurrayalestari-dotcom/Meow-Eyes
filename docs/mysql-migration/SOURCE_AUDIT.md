# Source audit: MongoDB to MySQL

This audit describes the **original** supplied `app-main.zip`, inspected on 2026-11-06, before migration. References to MongoDB files and defects below are historical source findings, not descriptions of the current runtime. The approved Step 2 package now uses MySQL; see [STEP_2.md](STEP_2.md). No live source database was inspected or imported.

### Target-version revision

The first Step 1 delivery targeted MySQL 8.4. The user subsequently specified
**MySQL 5.7.24-log**, so the revised foundation targets that server family
without changing the original MongoDB source findings below. Alembic revision
`20261106_0001` remains the initial schema history and `20261106_0002` adds the
MySQL 5.7 compatibility enforcement. This is a source/schema adaptation, not a
claim that a live server or its data directory has been downgraded.

MySQL 5.7 parses but ignores native CHECK expressions. The revised foundation
therefore uses database validation triggers for the corresponding row rules;
foreign keys, unique keys, and the normalized entity design remain in place.
Trigger installation and execution privileges are part of the deployment
review. These changes do not supply the later transaction services, data import,
or application-query conversion described in this audit.

Reference: [Oracle's MySQL 5.7 CREATE TABLE manual](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/create-table.html).

## 1. Application and evidence boundaries

- Backend: Python/FastAPI. `backend/database.py:3–12` creates a Motor client from `MONGO_URL` and `DB_NAME` during import. Authentication, routes, scheduler, exports, and seed scripts use this shared MongoDB client.
- Frontend: React. `frontend/src/pages/ShopNowPage.jsx:1–5` aliases the existing `ProductsPage` component.
- The original ZIP contains **37 concrete MongoDB collection names** in top-level backend Python files. No `db[...]` or `getattr(db, ...)` access introduces additional dynamic collection names. The generic helper in `seed_content.py` does not establish a separate collection.
- The original ZIP contains **no `.env`, BSON/database dump, SQL dump, or `.git/` directory**. A sample uploaded image exists, but the archive is not evidence of a complete production media backup.
- Existing seed and test files contain demo accounts and mocked integrations. They must not be treated as production records, credentials, or proof that production integrations work.

Production counts, unknown fields, orphan references, actual duplicate records, and migration duration remain unverified until an authorized database export or read-only source connection is available.

## 2. Original collection inventory

| Domain | MongoDB collections |
| --- | --- |
| Identity | `users`, `user_sessions`, `addresses` |
| Catalog | `products`, `categories`, `brands`, `lens_indexes` |
| Shopping | `cart_items`, `wishlists`, `product_reviews`, `product_subscriptions` |
| Orders and inventory | `orders`, `order_status_logs`, `stock_reservations`, `stock_movements` |
| Payment and shipping | `payment_logs`, `shipment_logs` |
| Promotions | `vouchers`, `flash_sales` |
| Games, roulette, and points | `games`, `game_scores`, `roulette_rewards`, `roulette_spins`, `point_logs` |
| Newsletter | `newsletter_subscribers`, `newsletter_campaigns` |
| Content | `articles`, `article_categories`, `product_knowledges`, `cms_pages`, `faq_categories`, `faqs` |
| Banners | `cms_banners`, `banners_v2` |
| Contact and media | `contact_settings`, `contact_messages`, `uploads` |

The collection inventory was derived from all original `backend/*.py` files, including route, scheduler, authentication, and seed code. Pydantic models alone do not cover the full stored data model.

## 3. Relational mapping and preservation requirements

| Source structure | Required migration treatment |
| --- | --- |
| `users.user_id`; other entity `id`; sessions `session_id` | Preserve public string identifiers. MongoDB `_id` is separate provenance, not the application's canonical ID. |
| `users.permissions[]` | Normalize into user-permission associations; retain current role and effective permissions. |
| `products.variants[]` | Separate variants and inventory rows/columns; preserve variant IDs, SKU, color, size, lens type, price override, stock, and reserved count. Enforce product/variant ownership. |
| `products.category_ids[]`, `segments[]`, `badges[]`, `gallery[]` | Normalize associations/ordered rows. Preserve primary category and image order. Keep flexible specification data where a typed column is not appropriate. |
| `categories.parent_id` | Self-reference with preflight checks for missing parents and cycles. |
| `cart_items` lens fields and `prescription` | Preserve bundle configuration; normalize measurements and optional media without merging distinct prescriptions. |
| `orders.items[]`, `address` | Normalize immutable order item and delivery-address snapshots. Do not reprice historical orders from current catalog records. |
| `orders.roulette_reward_id` | This actually contains a **roulette spin ID**. Map to the spin association, not the reward definition. See `routes_orders.py:261`. |
| `flash_sales.items[]` | Normalize campaign/product associations and prices/quotas. Future category campaigns need an explicit category association and resolved product eligibility. |
| `product_reviews.images[]` | Ordered review media; link reviews to a verified purchase. Reconcile legacy moderation fields. |
| `articles.tags[]`; knowledge `pros[]`, `cons[]`, `related_product_ids[]` | Normalize lists/associations while retaining order. Preserve content HTML and SEO fields. |
| `cms_banners` and `banners_v2` | Consolidate using provenance and an explicit collision policy. Map legacy `image`/`link` to desktop image/destination URL. Preserve V2 scheduling, device targeting, and sorting. |
| `contact_settings` | Preserve store/contact/social fields; a future WhatsApp default message is additional data, not derivable from existing records. |
| Provider payloads/logs | Structured relational payment/shipment records plus JSON for provider payload snapshots; redact secrets in future logging. |
| ISO date strings and floating-point prices | Parse dates into explicit UTC values; migrate money into decimal values using a documented rounding rule. Reject ambiguous/malformed values for review. |
| User password and PIN hashes | Copy existing bcrypt hashes unchanged. Never reset passwords or copy demo seed accounts over real users. |
| Session tokens | Existing plaintext session tokens can be hashed during import while preserving client sessions, provided the new lookup hashes incoming tokens identically. Preserve expiry; do not extend sessions. |

### Stored fields absent from the Pydantic model declarations

| Collection | Additional fields present in writes |
| --- | --- |
| `user_sessions` | `session_id`, `session_token`, `user_id`, `expires_at`, `created_at` |
| `flash_sales` | `activated_at`, `ended_at` |
| `orders` | `carrier_status`, `shipment_checked_at`, `completed_at` |
| `roulette_spins` | `used_order_id` |
| `product_reviews` | `order_id`, `status`, `moderated_by`, `moderated_at`, `admin_reply` |
| `stock_movements` | `id`, `product_id`, `variant_id`, `type`, `quantity`, optional `order_id`, `note`, `admin`, `created_at` |
| `order_status_logs` | `id`, `order_id`, `status`, `note`, optional `admin`, `created_at` |
| `uploads` | `id`, `url`, `filename`, `mime`, `size`, `subdir`, `disk_name`, `uploaded_by`, `uploaded_by_name`, `created_at` |
| `games` | `id`, `key`, `name`, `description`, `is_active`, `image`, `max_points`, `created_at` |
| `newsletter_campaigns` | `id`, `subject`, `body`, `segment`, `status`, `sent_count`, `failed_count`, `created_at` |

Evidence: `backend/auth.py:33–43`; `backend/scheduler.py:65–69,97–113`; `backend/routes_orders.py:294–306`; `backend/routes_admin_content.py:331–338`; `backend/routes_uploads.py:73–84`; `backend/routes_admin.py:215–219,323–326,456–465`; `backend/seed.py:333–345`. Raw dictionary update endpoints can also accept unforeseen fields; a live export must be inventoried rather than truncated to these known fields.

### Existing state values

- Order: `pending_payment`, `paid`, `processing`, `shipped`, `completed`, `cancelled`, `expired`, `refunded`.
- Payment: `pending`, `paid`, `failed`, `expired`, `cancelled`, `refunded`.
- Shipment: `pending`, `created`, `picked_up`, `in_transit`, `delivered`, `failed`, `returned`, `cancelled`.
- Reservation: `active`, `confirmed`, `expired`, `cancelled`.
- Article/CMS publication: `draft`, `published`, `archived`; knowledge currently uses `is_published` instead.
- Review: runtime writes `approved`, `rejected`, `hidden`; admin analytics also expects `pending`. `is_approved` is a separate legacy boolean.

Evidence: `backend/models.py:307–328,496,522,566`; `backend/routes_admin_content.py:329–347`.

## 4. Verified source-data conflicts

### Duplicate product SKUs in the supplied seed

`backend/seed.py:259` generates product SKUs as `"ME-" + slug.upper()[:10]`. A deterministic AST inspection of the literal `products_data` list (20 products) produces these duplicate pairs:

| SKU | Product names |
| --- | --- |
| `ME-MEOWOPTIK-` | MeowOptik Sweetie Cat Eye; MeowOptik Vintage Round |
| `ME-KITTYCRAFT` | Kittycraft Lola Round; Kittycraft Cubby Anak |
| `ME-ESSENSEEYE` | EssenseEye Quad Unisex; EssenseEye Air Rimless |

This evidence comes from source literals, not from a live database. Product SKU uniqueness is not enforced by `backend/database.py`; variant SKUs are a separate field. Before importing into a unique product-SKU column, report conflicts and obtain or apply an explicitly approved mapping. Do not silently rename, drop, or merge products.

### Historical lens/prescription detail is already missing

Cart pricing reads lens configuration and prescription data (`backend/routes_orders.py:60–86`), but checkout builds `OrderItem` with only product identity, label, quantity, and combined price (`:249–254`; `backend/models.py:277–285`). Past orders cannot reliably recover lens selections or measurements from current products. Preserve unknown values as unknown and record the limitation.

### Seeded rating/sales counters are not purchase evidence

`backend/seed.py:270–271` assigns synthetic `sold_count`, `rating_avg`, and `rating_count`; it does not create corresponding reviews or orders. Preserve and reconcile legacy aggregate values separately. Never generate fake purchase or review rows to satisfy the cached counters.

### Other constraints need preflight validation

- Existing category updates do not prevent ancestry cycles (`backend/routes_admin.py:247–255`).
- `game_scores.game` accepts `memory`, while the games seed contains only `matching`, `puzzle`, and `tetris` (`routes_engagement.py:31`; `seed.py:333–345`). Historical memory scores may need a reviewed game-definition mapping before a strict foreign key is enforced.
- The explicit review `order_id` branch checks ownership and completion but does not verify that the order contains the requested product (`routes_shopping.py:254–267`). Review purchase links therefore require validation.
- Collation-dependent duplicate emails/slugs/SKUs, missing foreign references, malformed timestamps, negative quantities, and inconsistent stock/reserved counters cannot be assessed without source data. Preflight must report them before writing relational rows.

## 5. Flash Sale defects traced through the code

### Campaign membership is not the storefront filter

1. The navigation opens `/shop-now?badge=flashsale` (`frontend/src/components/Layout/MainLayout.jsx:182`).
2. The generic product endpoint filters `products.badges` (`backend/routes_catalog.py:126–127`).
3. Admin campaign creation writes only `flash_sales.items` (`backend/routes_admin.py:381–385`).

Adding a product to a Flash Sale therefore does not necessarily add it to the visible listing. The later implementation should query authoritative campaign membership and active dates rather than depend on a manually maintained product badge.

### Price field names differ

The active-campaign endpoint sends `flash_price` (`backend/routes_catalog.py:227`), while `ProductCard` reads `flash_sale_price` (`frontend/src/components/ProductCard.jsx:11–15`). Seeded products already have a static Flash Sale price, which can mask the mismatch.

### Further lifecycle and quota issues

- Checkout selects the campaign price and then overrides it with a variant price, contrary to its documented priority (`backend/routes_orders.py:43–58`).
- Campaign `sold` is read but never incremented by the order/payment implementation. No promotional quota reservation exists, and the read check ignores requested quantity.
- The scheduler activates all inactive campaigns within their date window; this conflates manual disablement with scheduling (`backend/scheduler.py:60–69`).
- Admin date inputs display UTC strings as local values and then convert them again (`frontend/src/pages/admin/AdminPromos.jsx:141–142`).
- The sample campaign's dates are created once, unlike voucher dates, and are not refreshed on repeated seed runs (`backend/seed.py:305–314`).

These are source findings for the next approved feature stages; Step 1 does not modify the storefront or campaign routes.

## 6. Requested-feature baseline and later implementation

| Requested feature | Existing implementation | Later work |
| --- | --- | --- |
| Product breadcrumbs | Backend builds ancestry; product detail renders it. `routes_catalog.py:161–169`; `ProductDetailPage.jsx:122–132`. | Preserve behavior, verify accessible markup and edge cases. |
| Ratings | Completed-order backend endpoint, review display, and moderation exist. `routes_shopping.py:243–296`. | Add customer entry/transaction rating UI, verified-purchase constraints, duplicate protection, and consistent moderation. |
| Prescription form | Product detail has right/left SPH and CYL, PD, notes. `ProductDetailPage.jsx:22,277–285`. | Add AXIS, structured ADD, optional protected prescription upload, checkout validation, immutable order snapshot. |
| Flash Sale | Campaign CRUD and active endpoint exist but disagree with listing/price rendering. | Repair canonical campaign query and price calculation; add category campaigns and quota transactions. |
| Pagination | API supports `page/limit` with default 24; product list has no page controls. `routes_catalog.py:92–143`; `ProductsPage.jsx:208–228`. | Enforce 15 items, validated bounds, deterministic sorting, navigable UI preserving filters. |
| Banner order/URL | Already in BannerV2, CMS fields, and homepage sort. `AdminContent.jsx:303–310`; `HomePage.jsx:194–205`. | Consolidate legacy collections and verify complete click/scheduling/device behavior. |
| Publish/unpublish | Articles use status; knowledge uses a checkbox. `AdminContent.jsx:81–85,170`. | Standardize the state/API and expose the requested quick toggles. |
| WhatsApp | Contact settings and contact-page number link exist. `models.py:581`; `ContactPage.jsx:55–57`. | Add default message settings and global floating button. |
| New Arrival | `new` badges and homepage newest-product section exist. | Add navigation and a frame-specific category/filter. |
| Social sharing | No share/copy implementation found in article/knowledge detail source. | Add safe share URLs and clipboard/native-share fallback. |
| Knowledge content | English Round/Square already seeded. `seed_content.py:115–185`. | Idempotently add requested labels/content and avoid duplicate Round/Square concepts. |
| Virtual Try-On | No supported-frame asset management or frontend interface found. | Add asset/calibration management, supported-product UI, camera consent, and fallback. |
| DOKU/Everpro | Both are simulated in `services_mock.py`. | Implement actual provider adapters, verified events, retries, reconciliation, and sandbox validation using the merchant's provider configuration. |

Moderation currently changes `product_reviews.status`, but public detail filters `is_approved=True`; hidden/rejected reviews may remain visible (`routes_admin_content.py:331–338`; `routes_catalog.py:185–187`). One canonical publication/moderation state is required.

## 7. Transaction and integration work required after Step 1

Checkout writes order, reservations, stock movements, voucher usage, roulette usage, points, cart deletion, and status logs independently (`backend/routes_orders.py:273–328`). Payment/expiry routines also read and write state separately. The later MySQL service implementation needs atomic reservation and state transitions, not only equivalent SQL syntax.

Required acceptance cases:

- Concurrent checkout cannot oversell frame or lens inventory, exceed voucher/Flash Sale quotas, or spend points twice.
- A retried checkout creates one order; repeated provider notifications apply financial/inventory changes once.
- Payment and expiry/cancellation competing for the same reservation produce a single consistent outcome.
- One-hour reservation expiry returns reserved stock and provisional benefits exactly once.
- Historical order/address/price/prescription snapshots do not change when catalog or account records change.
- Provider failures can be retried without duplicate payments or shipments; failures remain visible for reconciliation.

The existing `/payment/confirm/{order_number}` endpoint is an unauthenticated **mock** that marks orders paid (`backend/routes_orders.py:414–460`). It does not call the mock signature checker and must not be presented as an operational DOKU integration.

Shipment polling expects `everpro_track()` to return a dictionary and calls `.get("status")` (`backend/scheduler.py:85–86`), but the mock returns a list (`backend/services_mock.py:95–103`). The adapter contract must be corrected and tested during the shipping stage.

The recommended approval boundary remains: review and validate the Step 1 schema/configuration first; proceed to repository/query conversion, import/reconciliation, and then feature/integration work only after confirmation.
