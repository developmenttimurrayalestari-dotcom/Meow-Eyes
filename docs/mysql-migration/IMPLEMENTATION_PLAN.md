# Meow Eyes implementation plan

The supplied application is a React storefront and FastAPI backend. The plan
keeps those frameworks and the current API contracts where practical. The
database target is **Oracle MySQL 5.7.24-log**, as requested in the Step 1
revision. The runtime accepts the MySQL 5.7 series from patch 5.7.24 onward;
MySQL 8.x and MariaDB are outside this target. The design uses relational tables
and explicit SQL services.

## Authorization and delivery status

The user authorized completion through the final step. No per-step approval
remains pending. Steps 1–9 are implemented in the delivered source; the local
validation record and activation requirements are in [the release guide](../FEATURES_AND_RELEASE.md)
and [VALIDATION](VALIDATION.md). Actual production data migration, MySQL-engine
acceptance and provider-account sandbox acceptance require the user's target
infrastructure and credentials; offline transport tests do not establish those
external outcomes.

| Step | Scope | Reviewable acceptance result |
| --- | --- | --- |
| 1. MySQL schema and backend foundation | Audit the actual collections; normalize entities; preserve string identifiers; introduce Decimal money, UTC dates, keys and MySQL 5.7 validation triggers; version the schema with Alembic through `20261106_0002`; configure independent async connections and readiness. | Schema targeting MySQL 5.7.24, source mapping, SQL, config template, optional `mysql:5.7.24` Compose service, tests, and explicit limitations. No production data migration or API cutover. |
| 2. MySQL application migration and data conversion | Rewrite auth, catalog, cart, checkout, CMS, games, exports, and scheduled jobs using SQLAlchemy queries and transaction services. Convert every existing collection and embedded array with a dry-run report, deterministic IDs, checkpoints, and reconciliation. Replace legacy seeders. | All existing routes now use SQL services; isolated route and reconciliation tests pass. Motor/PyMongo runtime access is removed. Actual server execution and production-export reconciliation await the target environment. |
| 3. Checkout and verified ratings | Persist frame/lens components and bilateral SPH/CYL/AXIS/ADD and PD per purchased line; private prescription photo upload; paid-order review form; enforce purchaser and item ownership; order/transaction rating; stock and reservation concurrency. | Complete bundle survives checkout and order history; prescription access is restricted; duplicate or unrelated-product reviews are rejected; transaction retries cannot oversell or double-charge points. |
| 4. Flash Sale | Query campaign membership consistently across listing/detail/checkout; fix price response contract; category rules with explicit descendants policy; materialize campaign products/variants; reserve quotas; handle timezone windows and manual enable/disable independently. | A product added in admin appears without a manual badge; displayed price equals charged price; expired campaigns disappear; quota cannot be oversold. |
| 5. Storefront UI | Shop Now pagination fixed at 15 items with stable ordering and filter preservation; verify existing breadcrumbs; global floating WhatsApp; New Arrival menu and dedicated frame category; article/knowledge share and copy-link. | Responsive screens preserve the current design and correct navigation, pagination, and accessible controls. |
| 6. CMS and content | Consolidate banner sources and reuse existing order/destination controls; consistent publish/unpublish state; WhatsApp number/default-message settings; frame try-on asset management; idempotent Product Knowledge content additions. | Public content respects one publication state; banner scheduling/sorting/links agree; requested content exists once; asset validation distinguishes private prescriptions from public frame assets. |
| 7. Virtual Try-On | Camera consent, supported-frame gating, image/3D asset fitting and calibration, mobile support, loading/error/fallback behavior. | A documented, tested preview using the managed asset source and supported devices; no visual accuracy claim without calibration tests. |
| 8. DOKU payments | Select the merchant-enabled DOKU product/channel and documented API; signed sandbox requests; protected notification verification; amount/order matching; idempotent payment transitions and reconciliation; disable the mock confirm route. | Adapter, signature, amount, duplicate-event and payment-state tests pass with an HTTP transport double; client actions cannot mark a real order paid. Merchant sandbox acceptance awaits account configuration. |
| 9. Everpro shipping and release | Confirm the enabled Everpro API/service; origin/destination resolution and postal codes; authenticated rate lookup, shipment creation, tracking, retry and webhook handling; final integration and recovery tests. | Rate, booking, retry, AWB and tracking behavior pass isolated protocol tests. Account sandbox acceptance and production cutover/rollback require the target environment and data reconciliation. |

## Decisions already made from the source

- Keep the current application IDs (`user_id`, `id`, and `session_id`) instead of
  substituting auto-increment IDs throughout the frontend and APIs.
- Preserve bcrypt password and PIN hashes. Session tokens are hashed for storage and their SQL lookup uses the same hash.
- Target MySQL 5.7.24 syntax and behavior in all future query/service work.
  Use supported joins, subqueries and locking reads; do not introduce MySQL 8
  CTEs, window functions or `SKIP LOCKED` into this target.
- Preserve row validation through `BEFORE INSERT` and `BEFORE UPDATE` triggers.
  MySQL 5.7 does not enforce native CHECK predicates. These triggers complement
  foreign/unique keys and application validation; they do not implement checkout
  transactions or provider verification.
- Use transactions for checkout, stock, promo quotas, points, and payment state
  transitions. External payment/shipping calls must not run inside long-lived
  stock-lock transactions; record attempts and use retryable operations/outbox.
- Store order address, product label, charged prices, selected lens components,
  and prescription values as historical snapshots.
- Treat campaign membership as the Flash Sale authority, publication status as
  the content/review visibility authority, and frame-category membership as an
  explicit relationship.
- Reuse the existing breadcrumbs, banner fields, publication controls, and
  review backend where sound. The source audit describes their missing pieces.

## Information needed later

An actual MongoDB export or authorized database connection is needed to move
records; the ZIP includes source and sample seed definitions only. The requested
server version is now established as MySQL 5.7.24-log. Its host, InnoDB settings,
account privileges, deployment platform and backup policy will be checked at
cutover. DOKU and Everpro account-specific products, sandbox credentials,
webhook endpoints, and shipping-origin details are needed for environment activation and external acceptance. Send secrets through environment/secret management rather than source
files or chat messages. These credentials are not needed for the offline tests or code review. Actual
cutover cannot be verified from source code alone.
