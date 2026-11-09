# MySQL 5.7.24-log schema reference

Generated from `backend/mysql/models.py`; schema only, with no database access.

**68 business/support tables**, excluding Alembic's `alembic_version` table.

All tables use InnoDB, ROW_FORMAT=DYNAMIC and utf8mb4. Imported string IDs are retained. Dates use UTC DATETIME(6); money uses DECIMAL(18,2).

MySQL 5.7 does not enforce CHECK constraints. The 97 row rules shown below are enforced by 90 BEFORE INSERT/UPDATE validation triggers installed by revision `20261106_0002`, across 45 tables. Metadata CHECK objects remain for documentation and portable SQLite tests; they are omitted from MySQL DDL.

`prescriptions` attached to orders are separate snapshots; future services must enforce ownership, private access and immutability. SQL constraints do not check cross-row order status, category cycles or external webhook signatures.

## Table index

| Table | Columns | Foreign keys |
| --- | ---: | ---: |
| `addresses` | 16 | 1 |
| `article_categories` | 7 | 0 |
| `article_tags` | 3 | 1 |
| `articles` | 16 | 2 |
| `banners` | 18 | 4 |
| `brands` | 7 | 0 |
| `cart_items` | 11 | 7 |
| `categories` | 15 | 1 |
| `cms_pages` | 12 | 0 |
| `contact_messages` | 8 | 0 |
| `contact_settings` | 14 | 0 |
| `faq_categories` | 6 | 0 |
| `faqs` | 7 | 1 |
| `flash_sale_categories` | 6 | 2 |
| `flash_sale_items` | 9 | 3 |
| `flash_sale_reservations` | 9 | 2 |
| `flash_sales` | 8 | 0 |
| `game_scores` | 6 | 2 |
| `games` | 8 | 0 |
| `integration_webhook_events` | 13 | 1 |
| `lens_indexes` | 9 | 0 |
| `migration_issues` | 12 | 3 |
| `migration_records` | 9 | 1 |
| `migration_runs` | 10 | 0 |
| `newsletter_campaigns` | 8 | 0 |
| `newsletter_subscribers` | 5 | 1 |
| `order_addresses` | 15 | 1 |
| `order_item_components` | 16 | 4 |
| `order_item_prescriptions` | 4 | 3 |
| `order_items` | 12 | 3 |
| `order_reviews` | 11 | 2 |
| `order_status_logs` | 6 | 2 |
| `orders` | 25 | 2 |
| `payment_logs` | 8 | 2 |
| `payments` | 17 | 1 |
| `point_logs` | 8 | 2 |
| `prescription_eyes` | 6 | 1 |
| `prescriptions` | 10 | 2 |
| `product_badges` | 2 | 1 |
| `product_categories` | 2 | 2 |
| `product_images` | 4 | 1 |
| `product_knowledge_bullets` | 4 | 1 |
| `product_knowledge_products` | 3 | 2 |
| `product_knowledges` | 18 | 0 |
| `product_review_images` | 3 | 1 |
| `product_reviews` | 17 | 6 |
| `product_segments` | 2 | 1 |
| `product_subscriptions` | 7 | 2 |
| `product_variants` | 14 | 1 |
| `products` | 26 | 2 |
| `roulette_redemptions` | 9 | 2 |
| `roulette_rewards` | 7 | 0 |
| `roulette_spins` | 9 | 2 |
| `settings` | 6 | 1 |
| `shipment_logs` | 8 | 2 |
| `shipments` | 18 | 1 |
| `shipping_quotes` | 19 | 1 |
| `stock_movements` | 14 | 5 |
| `stock_reservations` | 10 | 4 |
| `uploads` | 14 | 1 |
| `user_permissions` | 2 | 1 |
| `user_sessions` | 6 | 1 |
| `users` | 14 | 0 |
| `virtual_try_on_assets` | 20 | 4 |
| `voucher_redemptions` | 8 | 2 |
| `vouchers` | 14 | 0 |
| `whatsapp_settings` | 6 | 1 |
| `wishlists` | 4 | 2 |

## addresses

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `label` | `VARCHAR(100)` | no | — |
| `recipient` | `VARCHAR(255)` | no | — |
| `phone` | `VARCHAR(32)` | no | — |
| `street` | `TEXT` | no | — |
| `subdistrict` | `VARCHAR(128)` | yes | — |
| `district` | `VARCHAR(128)` | yes | — |
| `city` | `VARCHAR(128)` | no | — |
| `province` | `VARCHAR(128)` | no | — |
| `postal_code` | `VARCHAR(16)` | no | — |
| `country_code` | `VARCHAR(2)` | no | ID |
| `everpro_destination_id` | `VARCHAR(128)` | yes | — |
| `is_default` | `BOOL` | no | 0 |
| `default_for_user` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | GENERATED: CASE WHEN is_default = 1 THEN user_id ELSE NULL END |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `user_id` → `users.user_id`; delete `RESTRICT`.

Unique keys:

- `default_for_user`.
- `id, user_id`.

Indexes:

- `ix_addresses_user_id`: `user_id`.

## article_categories

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `name` | `VARCHAR(255)` | no | — |
| `slug` | `VARCHAR(191)` | no | — |
| `description` | `TEXT` | yes | — |
| `is_active` | `BOOL` | no | 1 |
| `sort_order` | `INTEGER` | no | 0 |
| `created_at` | `DATETIME(6)` | no | now(6) |

Unique keys:

- `slug`.

## article_tags

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `article_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `tag` (PK) | `VARCHAR(128)` | no | — |
| `sort_order` | `INTEGER` | no | 0 |

Foreign keys:

- `article_id` → `articles.id`; delete `CASCADE`.

## articles

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `category_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `author_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `author_name` | `VARCHAR(255)` | no | Admin Meow |
| `title` | `VARCHAR(255)` | no | — |
| `slug` | `VARCHAR(191)` | no | — |
| `excerpt` | `TEXT` | yes | — |
| `content` | `MEDIUMTEXT` | no | — |
| `thumbnail` | `TEXT` | yes | — |
| `status` | `VARCHAR(16)` | no | draft |
| `view_count` | `BIGINT` | no | 0 |
| `seo_title` | `VARCHAR(255)` | yes | — |
| `seo_description` | `TEXT` | yes | — |
| `published_at` | `DATETIME(6)` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `author_id` → `users.user_id`; delete `RESTRICT`.
- `category_id` → `article_categories.id`; delete `RESTRICT`.

Unique keys:

- `slug`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `status IN ('draft','published','unpublished','archived')`.
- `view_count >= 0`.

Indexes:

- `ix_articles_category`: `category_id, status, published_at, id`.
- `ix_articles_public`: `status, published_at, id`.

## banners

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `title` | `VARCHAR(255)` | no | — |
| `image_desktop` | `TEXT` | no | — |
| `image_mobile` | `TEXT` | yes | — |
| `link_type` | `VARCHAR(16)` | no | internal |
| `link_url` | `TEXT` | no | — |
| `link_product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `link_category_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `link_article_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `link_flash_sale_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `position` | `VARCHAR(64)` | no | hero |
| `target_device` | `VARCHAR(16)` | no | all |
| `alt_text` | `VARCHAR(255)` | yes | — |
| `sort_order` | `INTEGER` | no | 0 |
| `start_at` | `DATETIME(6)` | yes | — |
| `end_at` | `DATETIME(6)` | yes | — |
| `is_active` | `BOOL` | no | 1 |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `link_article_id` → `articles.id`; delete `RESTRICT`.
- `link_category_id` → `categories.id`; delete `RESTRICT`.
- `link_flash_sale_id` → `flash_sales.id`; delete `RESTRICT`.
- `link_product_id` → `products.id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `link_type IN ('internal','product','category','shop_now','flash_sale','article','external','none')`.
- `target_device IN ('desktop','mobile','all')`.
- `start_at IS NULL OR end_at IS NULL OR end_at > start_at`.

Indexes:

- `ix_banners_display`: `position, is_active, sort_order, id`.

## brands

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `name` | `VARCHAR(255)` | no | — |
| `slug` | `VARCHAR(191)` | no | — |
| `logo` | `TEXT` | yes | — |
| `description` | `TEXT` | yes | — |
| `is_active` | `BOOL` | no | 1 |
| `created_at` | `DATETIME(6)` | no | now(6) |

Unique keys:

- `slug`.

## cart_items

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `variant_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `quantity` | `INTEGER` | no | 1 |
| `lens_product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `lens_variant_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `lens_index_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `prescription_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `lens_index_id` → `lens_indexes.id`; delete `RESTRICT`.
- `lens_product_id, lens_variant_id` → `product_variants.product_id, product_variants.id`; delete `RESTRICT`.
- `lens_product_id` → `products.id`; delete `RESTRICT`.
- `prescription_id, user_id` → `prescriptions.id, prescriptions.user_id`; delete `RESTRICT`.
- `product_id` → `products.id`; delete `RESTRICT`.
- `product_id, variant_id` → `product_variants.product_id, product_variants.id`; delete `RESTRICT`.
- `user_id` → `users.user_id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `lens_variant_id IS NULL OR lens_product_id IS NOT NULL`.
- `quantity > 0`.

Indexes:

- `ix_cart_items_user_created`: `user_id, created_at, id`.

## categories

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `parent_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `name` | `VARCHAR(255)` | no | — |
| `slug` | `VARCHAR(191)` | no | — |
| `description` | `TEXT` | yes | — |
| `category_type` | `VARCHAR(32)` | no | product |
| `icon` | `TEXT` | yes | — |
| `banner_image` | `TEXT` | yes | — |
| `level` | `INTEGER` | no | 0 |
| `sort_order` | `INTEGER` | no | 0 |
| `is_featured` | `BOOL` | no | 0 |
| `is_active` | `BOOL` | no | 1 |
| `seo_title` | `VARCHAR(255)` | yes | — |
| `seo_description` | `TEXT` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `parent_id` → `categories.id`; delete `RESTRICT`.

Unique keys:

- `slug`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `level >= 0`.
- `parent_id IS NULL OR parent_id <> id`.

Indexes:

- `ix_categories_parent_sort`: `parent_id, sort_order, id`.

## cms_pages

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `page_type` | `VARCHAR(32)` | no | custom |
| `title` | `VARCHAR(255)` | no | — |
| `slug` | `VARCHAR(191)` | no | — |
| `content` | `MEDIUMTEXT` | no | — |
| `status` | `VARCHAR(16)` | no | draft |
| `version` | `INTEGER` | no | 1 |
| `seo_title` | `VARCHAR(255)` | yes | — |
| `seo_description` | `TEXT` | yes | — |
| `published_at` | `DATETIME(6)` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Unique keys:

- `slug`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `page_type IN ('about','privacy_policy','terms_conditions','refund_policy','shipping_policy','custom')`.
- `status IN ('draft','published','unpublished','archived')`.
- `version > 0`.

## contact_messages

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `name` | `VARCHAR(255)` | no | — |
| `email` | `VARCHAR(254)` | no | — |
| `phone` | `VARCHAR(32)` | yes | — |
| `subject` | `VARCHAR(255)` | yes | — |
| `message` | `TEXT` | no | — |
| `status` | `VARCHAR(16)` | no | new |
| `created_at` | `DATETIME(6)` | no | now(6) |

Row rules (enforced by MySQL 5.7 validation triggers):

- `status IN ('new','read','replied')`.

Indexes:

- `ix_contact_messages_inbox`: `status, created_at`.

## contact_settings

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `singleton_key` | `SMALLINT` | no | 1 |
| `store_name` | `VARCHAR(255)` | no | Meow Eyes |
| `address` | `TEXT` | no | — |
| `email` | `VARCHAR(254)` | no | — |
| `phone` | `VARCHAR(32)` | no | — |
| `operational_hours` | `VARCHAR(255)` | no | — |
| `instagram` | `TEXT` | yes | — |
| `facebook` | `TEXT` | yes | — |
| `tiktok` | `TEXT` | yes | — |
| `tokopedia` | `TEXT` | yes | — |
| `shopee` | `TEXT` | yes | — |
| `google_maps_embed` | `TEXT` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |

Unique keys:

- `singleton_key`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `singleton_key = 1`.

## faq_categories

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `name` | `VARCHAR(255)` | no | — |
| `slug` | `VARCHAR(191)` | no | — |
| `description` | `TEXT` | yes | — |
| `is_active` | `BOOL` | no | 1 |
| `sort_order` | `INTEGER` | no | 0 |

Unique keys:

- `slug`.

## faqs

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `category_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `question` | `TEXT` | no | — |
| `answer` | `TEXT` | no | — |
| `is_active` | `BOOL` | no | 1 |
| `sort_order` | `INTEGER` | no | 0 |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `category_id` → `faq_categories.id`; delete `RESTRICT`.

Indexes:

- `ix_faqs_public`: `category_id, is_active, sort_order`.

## flash_sale_categories

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `flash_sale_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `category_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `include_descendants` | `BOOL` | no | 1 |
| `discount_type` | `VARCHAR(16)` | no | — |
| `discount_value` | `NUMERIC(18, 2)` | no | — |
| `quota_per_product` | `INTEGER` | no | — |

Foreign keys:

- `category_id` → `categories.id`; delete `RESTRICT`.
- `flash_sale_id` → `flash_sales.id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `discount_value >= 0 AND quota_per_product >= 0`.
- `discount_type <> 'percent' OR discount_value <= 100`.
- `discount_type IN ('percent','nominal','fixed_price')`.

## flash_sale_items

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `flash_sale_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `source_category_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `flash_price` | `NUMERIC(18, 2)` | no | — |
| `quota` | `INTEGER` | no | — |
| `sold` | `INTEGER` | no | 0 |
| `reserved` | `INTEGER` | no | 0 |
| `is_active` | `BOOL` | no | 1 |

Foreign keys:

- `flash_sale_id` → `flash_sales.id`; delete `RESTRICT`.
- `flash_sale_id, source_category_id` → `flash_sale_categories.flash_sale_id, flash_sale_categories.category_id`; delete `RESTRICT`.
- `product_id` → `products.id`; delete `RESTRICT`.

Unique keys:

- `flash_sale_id, product_id`.
- `id, product_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `flash_price >= 0`.
- `quota >= 0 AND sold >= 0 AND reserved >= 0 AND sold + reserved <= quota`.

Indexes:

- `ix_flash_sale_items_product`: `product_id, flash_sale_id`.

## flash_sale_reservations

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_item_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `flash_sale_item_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `quantity` | `INTEGER` | no | — |
| `status` | `VARCHAR(16)` | no | active |
| `expires_at` | `DATETIME(6)` | no | — |
| `resolved_at` | `DATETIME(6)` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `flash_sale_item_id, product_id` → `flash_sale_items.id, flash_sale_items.product_id`; delete `RESTRICT`.
- `order_item_id, product_id` → `order_items.id, order_items.product_id`; delete `RESTRICT`.

Unique keys:

- `order_item_id, flash_sale_item_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `quantity > 0`.
- `status IN ('active','confirmed','expired','cancelled')`.

Indexes:

- `ix_flash_sale_reservations_expiry`: `status, expires_at`.

## flash_sales

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `name` | `VARCHAR(255)` | no | — |
| `start_at` | `DATETIME(6)` | no | — |
| `end_at` | `DATETIME(6)` | no | — |
| `is_active` | `BOOL` | no | 1 |
| `activated_at` | `DATETIME(6)` | yes | — |
| `ended_at` | `DATETIME(6)` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Row rules (enforced by MySQL 5.7 validation triggers):

- `end_at > start_at`.

Indexes:

- `ix_flash_sales_window`: `is_active, start_at, end_at`.

## game_scores

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `game` | `VARCHAR(32)` | no | — |
| `score` | `INTEGER` | no | — |
| `points_awarded` | `INTEGER` | no | 0 |
| `played_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `game` → `games.key`; delete `RESTRICT`.
- `user_id` → `users.user_id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `score >= 0 AND points_awarded >= 0`.

Indexes:

- `ix_game_scores_daily`: `user_id, game, played_at`.
- `ix_game_scores_leaderboard`: `game, score, user_id`.

## games

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `key` | `VARCHAR(32)` | no | — |
| `name` | `VARCHAR(255)` | no | — |
| `description` | `TEXT` | yes | — |
| `is_active` | `BOOL` | no | 1 |
| `image` | `TEXT` | yes | — |
| `max_points` | `INTEGER` | no | 50 |
| `created_at` | `DATETIME(6)` | no | now(6) |

Unique keys:

- `key`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `max_points >= 0`.

## integration_webhook_events

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `provider` | `VARCHAR(32)` | no | — |
| `event_key` | `VARCHAR(191) COLLATE utf8mb4_bin` | no | — |
| `payload_hash` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `event_type` | `VARCHAR(128)` | yes | — |
| `signature_verified` | `BOOL` | no | 0 |
| `payload` | `JSON` | no | — |
| `status` | `VARCHAR(16)` | no | received |
| `attempts` | `INTEGER` | no | 0 |
| `error_code` | `VARCHAR(128)` | yes | — |
| `received_at` | `DATETIME(6)` | no | now(6) |
| `processed_at` | `DATETIME(6)` | yes | — |

Foreign keys:

- `order_id` → `orders.id`; delete `RESTRICT`.

Unique keys:

- `provider, event_key`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `attempts >= 0`.
- `status IN ('received','processed','failed','ignored')`.

Indexes:

- `ix_webhook_events_retry`: `status, received_at`.

## lens_indexes

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `name` | `VARCHAR(255)` | no | — |
| `index_value` | `VARCHAR(32)` | no | — |
| `description` | `TEXT` | yes | — |
| `thickness_level` | `VARCHAR(32)` | no | medium |
| `recommended_power_range` | `VARCHAR(255)` | no |  |
| `additional_price` | `NUMERIC(18, 2)` | no | 0 |
| `is_active` | `BOOL` | no | 1 |
| `sort_order` | `INTEGER` | no | 0 |

Row rules (enforced by MySQL 5.7 validation triggers):

- `additional_price >= 0`.

Indexes:

- `ix_lens_indexes_index_value`: `index_value`.

## migration_issues

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `run_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `record_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `source_collection` | `VARCHAR(64)` | no | — |
| `source_id` | `VARCHAR(191) COLLATE utf8mb4_bin` | no | — |
| `field_name` | `VARCHAR(128)` | yes | — |
| `issue_code` | `VARCHAR(128)` | no | — |
| `severity` | `VARCHAR(16)` | no | error |
| `explanation` | `TEXT` | no | — |
| `resolved_at` | `DATETIME(6)` | yes | — |
| `resolved_by` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `record_id` → `migration_records.id`; delete `RESTRICT`.
- `resolved_by` → `users.user_id`; delete `RESTRICT`.
- `run_id` → `migration_runs.id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `severity IN ('info','warning','error')`.

Indexes:

- `ix_migration_issues_resolution`: `run_id, severity, resolved_at`.

## migration_records

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `run_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `source_collection` | `VARCHAR(64)` | no | — |
| `source_id` | `VARCHAR(191) COLLATE utf8mb4_bin` | no | — |
| `source_checksum` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `target_table` | `VARCHAR(64)` | no | — |
| `target_id` | `VARCHAR(255)` | no | — |
| `status` | `VARCHAR(16)` | no | planned |
| `verified_at` | `DATETIME(6)` | yes | — |

Foreign keys:

- `run_id` → `migration_runs.id`; delete `RESTRICT`.

Unique keys:

- `run_id, source_collection, source_id, target_table, target_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `status IN ('planned','imported','verified','rejected')`.

Indexes:

- `ix_migration_records_run_id`: `run_id`.
- `ix_migration_records_source`: `source_collection, source_id`.

## migration_runs

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `source_label` | `VARCHAR(255)` | no | — |
| `export_checksum` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `schema_revision` | `VARCHAR(64)` | no | — |
| `status` | `VARCHAR(16)` | no | planned |
| `source_count` | `BIGINT` | no | 0 |
| `migrated_count` | `BIGINT` | no | 0 |
| `rejected_count` | `BIGINT` | no | 0 |
| `started_at` | `DATETIME(6)` | yes | — |
| `completed_at` | `DATETIME(6)` | yes | — |

Row rules (enforced by MySQL 5.7 validation triggers):

- `source_count >= 0 AND migrated_count >= 0 AND rejected_count >= 0`.
- `status IN ('planned','running','validated','failed','completed')`.

## newsletter_campaigns

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `subject` | `VARCHAR(255)` | no | — |
| `body` | `TEXT` | no | — |
| `segment` | `VARCHAR(64)` | no | all |
| `status` | `VARCHAR(32)` | no | — |
| `sent_count` | `INTEGER` | no | 0 |
| `failed_count` | `INTEGER` | no | 0 |
| `created_at` | `DATETIME(6)` | no | now(6) |

Row rules (enforced by MySQL 5.7 validation triggers):

- `sent_count >= 0 AND failed_count >= 0`.

## newsletter_subscribers

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `email` | `VARCHAR(254)` | no | — |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `is_active` | `BOOL` | no | 1 |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `user_id` → `users.user_id`; delete `SET NULL`.

Unique keys:

- `email`.

## order_addresses

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `order_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `source_address_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `source_created_at` | `DATETIME(6)` | yes | — |
| `source_is_default` | `BOOL` | yes | — |
| `label` | `VARCHAR(100)` | yes | — |
| `recipient` | `VARCHAR(255)` | no | — |
| `phone` | `VARCHAR(32)` | no | — |
| `street` | `TEXT` | no | — |
| `subdistrict` | `VARCHAR(128)` | yes | — |
| `district` | `VARCHAR(128)` | yes | — |
| `city` | `VARCHAR(128)` | no | — |
| `province` | `VARCHAR(128)` | no | — |
| `postal_code` | `VARCHAR(16)` | no | — |
| `country_code` | `VARCHAR(2)` | no | ID |
| `everpro_destination_id` | `VARCHAR(128)` | yes | — |

Foreign keys:

- `order_id` → `orders.id`; delete `RESTRICT`.

## order_item_components

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_item_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `component_type` | `VARCHAR(16)` | no | — |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `variant_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `lens_index_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `product_name` | `VARCHAR(255)` | no | — |
| `sku` | `VARCHAR(128)` | yes | — |
| `variant_label` | `VARCHAR(255)` | yes | — |
| `lens_index_name` | `VARCHAR(255)` | yes | — |
| `quantity` | `INTEGER` | no | — |
| `unit_price` | `NUMERIC(18, 2)` | no | — |
| `index_surcharge` | `NUMERIC(18, 2)` | no | 0 |
| `subtotal` | `NUMERIC(18, 2)` | no | — |
| `sort_order` | `INTEGER` | no | — |

Foreign keys:

- `lens_index_id` → `lens_indexes.id`; delete `RESTRICT`.
- `order_item_id, order_id` → `order_items.id, order_items.order_id`; delete `RESTRICT`.
- `product_id` → `products.id`; delete `RESTRICT`.
- `product_id, variant_id` → `product_variants.product_id, product_variants.id`; delete `RESTRICT`.

Unique keys:

- `id, order_id, product_id`.
- `order_item_id, sort_order`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `quantity > 0 AND unit_price >= 0 AND subtotal >= 0 AND index_surcharge >= 0`.
- `component_type IN ('primary','lens')`.

Indexes:

- `ix_order_item_components_product_id`: `product_id`.

## order_item_prescriptions

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `order_item_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `prescription_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |

Foreign keys:

- `order_id, user_id` → `orders.id, orders.user_id`; delete `RESTRICT`.
- `order_item_id, order_id` → `order_items.id, order_items.order_id`; delete `RESTRICT`.
- `prescription_id, user_id` → `prescriptions.id, prescriptions.user_id`; delete `RESTRICT`.

Unique keys:

- `prescription_id`.

## order_items

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `variant_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `product_name` | `VARCHAR(255)` | no | — |
| `sku` | `VARCHAR(128)` | yes | — |
| `variant_label` | `VARCHAR(255)` | yes | — |
| `main_image` | `TEXT` | yes | — |
| `quantity` | `INTEGER` | no | — |
| `unit_price` | `NUMERIC(18, 2)` | no | — |
| `subtotal` | `NUMERIC(18, 2)` | no | — |
| `sort_order` | `INTEGER` | no | — |

Foreign keys:

- `order_id` → `orders.id`; delete `RESTRICT`.
- `product_id` → `products.id`; delete `RESTRICT`.
- `product_id, variant_id` → `product_variants.product_id, product_variants.id`; delete `RESTRICT`.

Unique keys:

- `id, order_id`.
- `id, order_id, product_id`.
- `id, product_id`.
- `order_id, sort_order`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `quantity > 0 AND unit_price >= 0 AND subtotal >= 0`.

Indexes:

- `ix_order_items_product_id`: `product_id`.

## order_reviews

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `rating` | `SMALLINT` | no | — |
| `body` | `TEXT` | yes | — |
| `status` | `VARCHAR(16)` | no | pending |
| `admin_reply` | `TEXT` | yes | — |
| `moderated_by` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `moderated_at` | `DATETIME(6)` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `moderated_by` → `users.user_id`; delete `RESTRICT`.
- `order_id, user_id` → `orders.id, orders.user_id`; delete `RESTRICT`.

Unique keys:

- `order_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `rating BETWEEN 1 AND 5`.
- `status IN ('pending','approved','rejected','hidden')`.

## order_status_logs

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `status` | `VARCHAR(32)` | no | — |
| `note` | `TEXT` | yes | — |
| `admin_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `admin_id` → `users.user_id`; delete `RESTRICT`.
- `order_id` → `orders.id`; delete `RESTRICT`.

Indexes:

- `ix_order_status_logs_timeline`: `order_id, created_at, id`.

## orders

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_number` | `VARCHAR(64)` | no | — |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `subtotal` | `NUMERIC(18, 2)` | no | — |
| `discount` | `NUMERIC(18, 2)` | no | 0 |
| `flash_sale_discount` | `NUMERIC(18, 2)` | no | 0 |
| `voucher_code` | `VARCHAR(128)` | yes | — |
| `voucher_discount` | `NUMERIC(18, 2)` | no | 0 |
| `points_used` | `BIGINT` | no | 0 |
| `points_discount` | `NUMERIC(18, 2)` | no | 0 |
| `roulette_discount` | `NUMERIC(18, 2)` | no | 0 |
| `shipping_quote_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `shipping_courier` | `VARCHAR(64)` | no | — |
| `shipping_service` | `VARCHAR(64)` | no | — |
| `shipping_cost` | `NUMERIC(18, 2)` | no | — |
| `total` | `NUMERIC(18, 2)` | no | — |
| `currency` | `VARCHAR(3)` | no | IDR |
| `status` | `VARCHAR(32)` | no | pending_payment |
| `payment_status` | `VARCHAR(32)` | no | pending |
| `shipment_status` | `VARCHAR(32)` | no | pending |
| `reservation_expires_at` | `DATETIME(6)` | yes | — |
| `completed_at` | `DATETIME(6)` | yes | — |
| `checkout_idempotency_key` | `VARCHAR(191) COLLATE utf8mb4_bin` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `shipping_quote_id, user_id` → `shipping_quotes.id, shipping_quotes.user_id`; delete `RESTRICT`.
- `user_id` → `users.user_id`; delete `RESTRICT`.

Unique keys:

- `checkout_idempotency_key`.
- `id, user_id`.
- `order_number`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `points_used >= 0 AND points_discount >= 0 AND roulette_discount >= 0 AND shipping_cost >= 0 AND total >= 0`.
- `subtotal >= 0 AND discount >= 0 AND flash_sale_discount >= 0 AND voucher_discount >= 0`.
- `payment_status IN ('pending','paid','failed','expired','cancelled','refunded')`.
- `shipment_status IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')`.
- `status IN ('pending_payment','paid','processing','shipped','completed','cancelled','expired','refunded')`.

Indexes:

- `ix_orders_customer_date`: `user_id, created_at, id`.
- `ix_orders_expiry`: `status, reservation_expires_at, id`.
- `ix_orders_payment_date`: `payment_status, created_at`.
- `ix_orders_shipment_status`: `shipment_status, updated_at`.

## payment_logs

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `payment_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `provider` | `VARCHAR(32)` | no | — |
| `action` | `VARCHAR(64)` | no | — |
| `payload` | `JSON` | yes | — |
| `response` | `JSON` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `order_id` → `orders.id`; delete `RESTRICT`.
- `payment_id, order_id` → `payments.id, payments.order_id`; delete `RESTRICT`.

Indexes:

- `ix_payment_logs_order_date`: `order_id, created_at, id`.

## payments

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `provider` | `VARCHAR(32)` | no | doku |
| `request_id` | `VARCHAR(191) COLLATE utf8mb4_bin` | no | — |
| `merchant_reference` | `VARCHAR(191) COLLATE utf8mb4_bin` | no | — |
| `external_id` | `VARCHAR(191) COLLATE utf8mb4_bin` | yes | — |
| `amount` | `NUMERIC(18, 2)` | no | — |
| `currency` | `VARCHAR(3)` | no | IDR |
| `method` | `VARCHAR(64)` | yes | — |
| `channel` | `VARCHAR(64)` | yes | — |
| `status` | `VARCHAR(16)` | no | pending |
| `payment_url` | `TEXT` | yes | — |
| `virtual_account_number` | `VARCHAR(64)` | yes | — |
| `expires_at` | `DATETIME(6)` | yes | — |
| `paid_at` | `DATETIME(6)` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `order_id` → `orders.id`; delete `RESTRICT`.

Unique keys:

- `id, order_id`.
- `provider, external_id`.
- `provider, merchant_reference`.
- `provider, request_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `amount >= 0`.
- `status IN ('pending','paid','failed','expired','cancelled','refunded')`.

Indexes:

- `ix_payments_order_status`: `order_id, status, created_at`.

## point_logs

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `delta` | `BIGINT` | no | — |
| `balance_after` | `BIGINT` | no | — |
| `type` | `VARCHAR(64)` | no | — |
| `note` | `TEXT` | no | application: '' |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `order_id` → `orders.id`; delete `RESTRICT`.
- `user_id` → `users.user_id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `balance_after >= 0`.

Indexes:

- `ix_point_logs_user_type_date`: `user_id, type, created_at, id`.

## prescription_eyes

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `prescription_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `eye` (PK) | `VARCHAR(5)` | no | — |
| `sph` | `NUMERIC(5, 2)` | yes | — |
| `cyl` | `NUMERIC(5, 2)` | yes | — |
| `axis` | `SMALLINT` | yes | — |
| `add` | `NUMERIC(5, 2)` | yes | — |

Foreign keys:

- `prescription_id` → `prescriptions.id`; delete `CASCADE`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `axis IS NULL OR axis BETWEEN 0 AND 180`.
- `eye IN ('right','left')`.

## prescriptions

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `pd_total` | `NUMERIC(5, 2)` | yes | — |
| `pd_right` | `NUMERIC(5, 2)` | yes | — |
| `pd_left` | `NUMERIC(5, 2)` | yes | — |
| `attachment_upload_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `notes` | `TEXT` | yes | — |
| `is_order_snapshot` | `BOOL` | no | 0 |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `attachment_upload_id` → `uploads.id`; delete `RESTRICT`.
- `user_id` → `users.user_id`; delete `RESTRICT`.

Unique keys:

- `id, user_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `pd_left IS NULL OR pd_left > 0`.
- `pd_total IS NULL OR (pd_right IS NULL AND pd_left IS NULL)`.
- `(pd_right IS NULL AND pd_left IS NULL) OR (pd_right IS NOT NULL AND pd_left IS NOT NULL)`.
- `pd_right IS NULL OR pd_right > 0`.
- `pd_total IS NULL OR pd_total > 0`.

Indexes:

- `ix_prescriptions_user_id`: `user_id`.

## product_badges

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `product_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `badge` (PK) | `VARCHAR(64)` | no | — |

Foreign keys:

- `product_id` → `products.id`; delete `CASCADE`.

Indexes:

- `ix_product_badges_badge`: `badge, product_id`.

## product_categories

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `product_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `category_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |

Foreign keys:

- `category_id` → `categories.id`; delete `RESTRICT`.
- `product_id` → `products.id`; delete `CASCADE`.

Indexes:

- `ix_product_categories_category`: `category_id, product_id`.

## product_images

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `product_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `sort_order` (PK) | `INTEGER` | no | — |
| `image_url` | `TEXT` | no | — |
| `alt_text` | `VARCHAR(255)` | yes | — |

Foreign keys:

- `product_id` → `products.id`; delete `CASCADE`.

## product_knowledge_bullets

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `knowledge_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `kind` (PK) | `VARCHAR(3)` | no | — |
| `sort_order` (PK) | `INTEGER` | no | — |
| `body` | `TEXT` | no | — |

Foreign keys:

- `knowledge_id` → `product_knowledges.id`; delete `CASCADE`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `kind IN ('pro','con')`.

## product_knowledge_products

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `knowledge_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `product_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `sort_order` | `INTEGER` | no | 0 |

Foreign keys:

- `knowledge_id` → `product_knowledges.id`; delete `CASCADE`.
- `product_id` → `products.id`; delete `RESTRICT`.

## product_knowledges

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `knowledge_type` | `VARCHAR(32)` | no | — |
| `title` | `VARCHAR(255)` | no | — |
| `slug` | `VARCHAR(191)` | no | — |
| `description` | `TEXT` | yes | — |
| `content` | `MEDIUMTEXT` | no | — |
| `image` | `TEXT` | yes | — |
| `icon` | `TEXT` | yes | — |
| `face_shape_recommendation` | `TEXT` | yes | — |
| `style_recommendation` | `TEXT` | yes | — |
| `filter_param` | `JSON` | yes | — |
| `sort_order` | `INTEGER` | no | 0 |
| `status` | `VARCHAR(16)` | no | draft |
| `seo_title` | `VARCHAR(255)` | yes | — |
| `seo_description` | `TEXT` | yes | — |
| `published_at` | `DATETIME(6)` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Unique keys:

- `slug`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `status IN ('draft','published','unpublished','archived')`.
- `knowledge_type IN ('frame_shape','material','lens_type','lens_index','buying_guide')`.

Indexes:

- `ix_knowledge_public`: `knowledge_type, status, sort_order, id`.

## product_review_images

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `review_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `sort_order` (PK) | `INTEGER` | no | — |
| `image_url` | `TEXT` | no | — |

Foreign keys:

- `review_id` → `product_reviews.id`; delete `CASCADE`.

## product_reviews

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `order_item_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `order_component_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `verified_purchase` | `BOOL` | no | 0 |
| `user_name` | `VARCHAR(255)` | no | — |
| `rating` | `SMALLINT` | no | — |
| `title` | `VARCHAR(255)` | yes | — |
| `body` | `TEXT` | no | — |
| `status` | `VARCHAR(16)` | no | pending |
| `admin_reply` | `TEXT` | yes | — |
| `moderated_by` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `moderated_at` | `DATETIME(6)` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `moderated_by` → `users.user_id`; delete `RESTRICT`.
- `order_component_id, order_id, product_id` → `order_item_components.id, order_item_components.order_id, order_item_components.product_id`; delete `RESTRICT`.
- `order_id, user_id` → `orders.id, orders.user_id`; delete `RESTRICT`.
- `order_item_id, order_id, product_id` → `order_items.id, order_items.order_id, order_items.product_id`; delete `RESTRICT`.
- `product_id` → `products.id`; delete `RESTRICT`.
- `user_id` → `users.user_id`; delete `RESTRICT`.

Unique keys:

- `order_id, product_id, user_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `(order_item_id IS NULL AND order_component_id IS NULL) OR order_id IS NOT NULL`.
- `order_item_id IS NULL OR order_component_id IS NULL`.
- `rating BETWEEN 1 AND 5`.
- `status IN ('pending','approved','rejected','hidden')`.
- `verified_purchase = 0 OR (order_id IS NOT NULL AND (order_item_id IS NOT NULL OR order_component_id IS NOT NULL))`.

Indexes:

- `ix_product_reviews_public`: `product_id, status, created_at, id`.

## product_segments

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `product_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `segment` (PK) | `VARCHAR(64)` | no | — |

Foreign keys:

- `product_id` → `products.id`; delete `CASCADE`.

Indexes:

- `ix_product_segments_segment`: `segment, product_id`.

## product_subscriptions

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `notify_stock` | `BOOL` | no | 1 |
| `notify_price_drop` | `BOOL` | no | 1 |
| `notify_flash_sale` | `BOOL` | no | 1 |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `product_id` → `products.id`; delete `CASCADE`.
- `user_id` → `users.user_id`; delete `CASCADE`.

Unique keys:

- `user_id, product_id`.

## product_variants

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `color` | `VARCHAR(128)` | yes | — |
| `color_hex` | `VARCHAR(16)` | yes | — |
| `size` | `VARCHAR(100)` | yes | — |
| `lens_type` | `VARCHAR(128)` | yes | — |
| `sku` | `VARCHAR(128)` | no | — |
| `stock` | `INTEGER` | no | 0 |
| `reserved` | `INTEGER` | no | 0 |
| `price_override` | `NUMERIC(18, 2)` | yes | — |
| `is_active` | `BOOL` | no | 1 |
| `sort_order` | `INTEGER` | no | 0 |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `product_id` → `products.id`; delete `RESTRICT`.

Unique keys:

- `product_id, id`.
- `sku`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `stock >= 0 AND reserved >= 0 AND reserved <= stock`.
- `price_override IS NULL OR price_override >= 0`.

## products

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `name` | `VARCHAR(255)` | no | — |
| `slug` | `VARCHAR(191)` | no | — |
| `sku` | `VARCHAR(128)` | no | — |
| `description` | `TEXT` | no | — |
| `spec` | `JSON` | yes | — |
| `product_type` | `VARCHAR(16)` | no | frame |
| `primary_category_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `brand_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `price` | `NUMERIC(18, 2)` | no | — |
| `discount_price` | `NUMERIC(18, 2)` | yes | — |
| `flash_sale_price` | `NUMERIC(18, 2)` | yes | — |
| `weight_gram` | `INTEGER` | no | 100 |
| `dimension` | `VARCHAR(255)` | yes | — |
| `main_image` | `TEXT` | no | — |
| `min_stock_alert` | `INTEGER` | no | 5 |
| `rating_avg` | `NUMERIC(3, 2)` | no | 0 |
| `rating_count` | `INTEGER` | no | 0 |
| `sold_count` | `BIGINT` | no | 0 |
| `is_active` | `BOOL` | no | 1 |
| `is_new_arrival` | `BOOL` | no | 0 |
| `new_arrival_until` | `DATETIME(6)` | yes | — |
| `seo_title` | `VARCHAR(255)` | yes | — |
| `seo_description` | `TEXT` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `brand_id` → `brands.id`; delete `RESTRICT`.
- `primary_category_id` → `categories.id`; delete `RESTRICT`.

Unique keys:

- `sku`.
- `slug`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `rating_avg BETWEEN 0 AND 5 AND rating_count >= 0 AND sold_count >= 0`.
- `weight_gram >= 0 AND min_stock_alert >= 0`.
- `flash_sale_price IS NULL OR flash_sale_price >= 0`.
- `price >= 0 AND (discount_price IS NULL OR discount_price >= 0)`.
- `product_type IN ('frame','lens','package')`.

Indexes:

- `ft_products_name_description`: FULLTEXT `name, description`.
- `ix_products_arrivals`: `is_active, product_type, is_new_arrival, created_at, id`.
- `ix_products_brand_id`: `brand_id`.
- `ix_products_price`: `is_active, price, id`.
- `ix_products_primary_category_id`: `primary_category_id`.
- `ix_products_shop`: `is_active, product_type, created_at, id`.

## roulette_redemptions

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `spin_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `status` | `VARCHAR(16)` | no | reserved |
| `discount_amount` | `NUMERIC(18, 2)` | no | 0 |
| `resolved_at` | `DATETIME(6)` | yes | — |
| `active_spin_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | GENERATED: CASE WHEN status IN ('reserved','redeemed') THEN spin_id ELSE NULL END |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `order_id, user_id` → `orders.id, orders.user_id`; delete `RESTRICT`.
- `spin_id, user_id` → `roulette_spins.id, roulette_spins.user_id`; delete `RESTRICT`.

Unique keys:

- `active_spin_id`.
- `order_id`.
- `spin_id, order_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `discount_amount >= 0`.
- `status IN ('reserved','redeemed','released')`.

## roulette_rewards

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `label` | `VARCHAR(255)` | no | — |
| `type` | `VARCHAR(32)` | no | — |
| `value` | `NUMERIC(18, 2)` | no | 0 |
| `color` | `VARCHAR(16)` | no | #FF6B6B |
| `probability` | `NUMERIC(18, 8)` | no | 0.1 |
| `is_active` | `BOOL` | no | 1 |

Row rules (enforced by MySQL 5.7 validation triggers):

- `value >= 0 AND probability >= 0`.
- `type IN ('points','voucher','free_shipping','discount','nothing')`.

## roulette_spins

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `reward_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `reward_label` | `VARCHAR(255)` | no | — |
| `reward_type` | `VARCHAR(32)` | no | — |
| `reward_value` | `NUMERIC(18, 2)` | no | — |
| `used` | `BOOL` | no | 0 |
| `expires_at` | `DATETIME(6)` | no | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `reward_id` → `roulette_rewards.id`; delete `RESTRICT`.
- `user_id` → `users.user_id`; delete `RESTRICT`.

Unique keys:

- `id, user_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `reward_value >= 0`.

Indexes:

- `ix_roulette_spins_eligibility`: `user_id, used, expires_at`.
- `ix_roulette_spins_user_date`: `user_id, created_at`.

## settings

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `key` (PK) | `VARCHAR(128)` | no | — |
| `value` | `JSON` | no | — |
| `description` | `TEXT` | yes | — |
| `is_public` | `BOOL` | no | 0 |
| `updated_by` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `updated_by` → `users.user_id`; delete `RESTRICT`.

## shipment_logs

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `shipment_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `provider` | `VARCHAR(32)` | no | — |
| `action` | `VARCHAR(64)` | no | — |
| `payload` | `JSON` | yes | — |
| `response` | `JSON` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `order_id` → `orders.id`; delete `RESTRICT`.
- `shipment_id, order_id` → `shipments.id, shipments.order_id`; delete `RESTRICT`.

Indexes:

- `ix_shipment_logs_order_date`: `order_id, created_at, id`.

## shipments

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `provider` | `VARCHAR(32)` | no | everpro |
| `request_id` | `VARCHAR(191) COLLATE utf8mb4_bin` | no | — |
| `external_id` | `VARCHAR(191) COLLATE utf8mb4_bin` | yes | — |
| `courier_code` | `VARCHAR(64)` | no | — |
| `service_code` | `VARCHAR(64)` | no | — |
| `tracking_number` | `VARCHAR(191) COLLATE utf8mb4_bin` | yes | — |
| `label_url` | `TEXT` | yes | — |
| `status` | `VARCHAR(32)` | no | pending |
| `carrier_status` | `VARCHAR(255)` | yes | — |
| `cost` | `NUMERIC(18, 2)` | no | — |
| `currency` | `VARCHAR(3)` | no | IDR |
| `last_checked_at` | `DATETIME(6)` | yes | — |
| `shipped_at` | `DATETIME(6)` | yes | — |
| `delivered_at` | `DATETIME(6)` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `order_id` → `orders.id`; delete `RESTRICT`.

Unique keys:

- `id, order_id`.
- `provider, external_id`.
- `provider, request_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `cost >= 0`.
- `status IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')`.

Indexes:

- `ix_shipments_order`: `order_id, created_at`.
- `ix_shipments_poll`: `status, last_checked_at`.
- `ix_shipments_tracking`: `provider, tracking_number`.

## shipping_quotes

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `provider` | `VARCHAR(32)` | no | everpro |
| `provider_quote_id` | `VARCHAR(191)` | yes | — |
| `origin_id` | `VARCHAR(128)` | no | — |
| `destination_id` | `VARCHAR(128)` | no | — |
| `courier_code` | `VARCHAR(64)` | no | — |
| `service_code` | `VARCHAR(64)` | no | — |
| `service_label` | `VARCHAR(255)` | yes | — |
| `weight_gram` | `INTEGER` | no | — |
| `cost` | `NUMERIC(18, 2)` | no | — |
| `insurance_cost` | `NUMERIC(18, 2)` | no | 0 |
| `currency` | `VARCHAR(3)` | no | IDR |
| `estimated_delivery` | `VARCHAR(128)` | yes | — |
| `cart_fingerprint` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `expires_at` | `DATETIME(6)` | no | — |
| `request_payload` | `JSON` | yes | — |
| `response_payload` | `JSON` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `user_id` → `users.user_id`; delete `RESTRICT`.

Unique keys:

- `id, user_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `weight_gram > 0 AND cost >= 0 AND insurance_cost >= 0`.

Indexes:

- `ix_shipping_quotes_user_expiry`: `user_id, expires_at`.

## stock_movements

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `variant_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `reservation_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `type` | `VARCHAR(64)` | no | — |
| `quantity` | `INTEGER` | no | — |
| `delta` | `INTEGER` | yes | — |
| `reserved_delta` | `INTEGER` | yes | — |
| `stock_after` | `INTEGER` | yes | — |
| `reserved_after` | `INTEGER` | yes | — |
| `note` | `TEXT` | yes | — |
| `admin_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `admin_id` → `users.user_id`; delete `RESTRICT`.
- `order_id` → `orders.id`; delete `RESTRICT`.
- `product_id` → `products.id`; delete `RESTRICT`.
- `product_id, variant_id` → `product_variants.product_id, product_variants.id`; delete `RESTRICT`.
- `reservation_id` → `stock_reservations.id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `quantity >= 0`.
- `reserved_after IS NULL OR reserved_after >= 0`.
- `stock_after IS NULL OR stock_after >= 0`.

Indexes:

- `ix_stock_movements_order_id`: `order_id`.
- `ix_stock_movements_product_date`: `product_id, created_at, id`.

## stock_reservations

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `order_item_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `variant_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `quantity` | `INTEGER` | no | — |
| `status` | `VARCHAR(16)` | no | active |
| `expires_at` | `DATETIME(6)` | no | — |
| `resolved_at` | `DATETIME(6)` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `order_id` → `orders.id`; delete `RESTRICT`.
- `order_item_id, order_id` → `order_items.id, order_items.order_id`; delete `RESTRICT`.
- `product_id` → `products.id`; delete `RESTRICT`.
- `product_id, variant_id` → `product_variants.product_id, product_variants.id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `quantity > 0`.
- `status IN ('active','confirmed','expired','cancelled')`.

Indexes:

- `ix_stock_reservations_expiry`: `status, expires_at, id`.
- `ix_stock_reservations_order`: `order_id, status`.

## uploads

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `url` | `TEXT` | yes | — |
| `filename` | `VARCHAR(255)` | no | — |
| `mime` | `VARCHAR(128)` | no | — |
| `size` | `BIGINT` | no | — |
| `subdir` | `VARCHAR(128)` | yes | — |
| `disk_name` | `VARCHAR(255)` | yes | — |
| `storage_provider` | `VARCHAR(32)` | no | local |
| `storage_key` | `TEXT` | yes | — |
| `visibility` | `VARCHAR(16)` | no | public |
| `sha256` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `uploaded_by` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `uploaded_by_name` | `VARCHAR(255)` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `uploaded_by` → `users.user_id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `size >= 0`.
- `visibility IN ('public','private')`.

Indexes:

- `ix_uploads_uploaded_by`: `uploaded_by`.

## user_permissions

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `user_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `permission` (PK) | `VARCHAR(100)` | no | — |

Foreign keys:

- `user_id` → `users.user_id`; delete `CASCADE`.

## user_sessions

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `session_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `token_hash` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `expires_at` | `DATETIME(6)` | no | — |
| `revoked_at` | `DATETIME(6)` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `user_id` → `users.user_id`; delete `CASCADE`.

Unique keys:

- `token_hash`.

Indexes:

- `ix_user_sessions_expiry`: `expires_at`.
- `ix_user_sessions_user_id`: `user_id`.

## users

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `user_id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `email` | `VARCHAR(254)` | no | — |
| `name` | `VARCHAR(255)` | no | — |
| `picture` | `TEXT` | yes | — |
| `password_hash` | `VARCHAR(255)` | yes | — |
| `pin_hash` | `VARCHAR(255)` | yes | — |
| `pin_failed_attempts` | `INTEGER` | no | 0 |
| `pin_locked_until` | `DATETIME(6)` | yes | — |
| `role` | `VARCHAR(32)` | no | customer |
| `provider` | `VARCHAR(32)` | no | password |
| `is_active` | `BOOL` | no | 1 |
| `points_balance` | `BIGINT` | no | 0 |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Unique keys:

- `email`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `pin_failed_attempts >= 0`.
- `points_balance >= 0`.
- `role IN ('customer','staff','admin','super_admin')`.

## virtual_try_on_assets

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `variant_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `asset_type` | `VARCHAR(8)` | no | — |
| `upload_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `source_url` | `TEXT` | yes | — |
| `preview_url` | `TEXT` | yes | — |
| `scale` | `NUMERIC(10, 5)` | no | 1 |
| `offset_x` | `NUMERIC(10, 5)` | no | 0 |
| `offset_y` | `NUMERIC(10, 5)` | no | 0 |
| `offset_z` | `NUMERIC(10, 5)` | no | 0 |
| `rotation_x` | `NUMERIC(10, 5)` | no | 0 |
| `rotation_y` | `NUMERIC(10, 5)` | no | 0 |
| `rotation_z` | `NUMERIC(10, 5)` | no | 0 |
| `calibration` | `JSON` | yes | — |
| `status` | `VARCHAR(16)` | no | draft |
| `sort_order` | `INTEGER` | no | 0 |
| `updated_by` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `product_id` → `products.id`; delete `RESTRICT`.
- `product_id, variant_id` → `product_variants.product_id, product_variants.id`; delete `RESTRICT`.
- `updated_by` → `users.user_id`; delete `RESTRICT`.
- `upload_id` → `uploads.id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `asset_type IN ('image','glb','gltf')`.
- `scale > 0`.
- `upload_id IS NOT NULL OR source_url IS NOT NULL`.
- `status IN ('draft','published','archived')`.

Indexes:

- `ix_vto_product_status`: `product_id, status, sort_order`.

## voucher_redemptions

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `voucher_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `order_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `discount_amount` | `NUMERIC(18, 2)` | no | — |
| `status` | `VARCHAR(16)` | no | reserved |
| `resolved_at` | `DATETIME(6)` | yes | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `order_id, user_id` → `orders.id, orders.user_id`; delete `RESTRICT`.
- `voucher_id` → `vouchers.id`; delete `RESTRICT`.

Unique keys:

- `order_id`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `discount_amount >= 0`.
- `status IN ('reserved','redeemed','released')`.

Indexes:

- `ix_voucher_redemptions_quota`: `voucher_id, user_id, status`.

## vouchers

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `code` | `VARCHAR(128)` | no | — |
| `name` | `VARCHAR(255)` | no | — |
| `discount_type` | `VARCHAR(32)` | no | — |
| `discount_value` | `NUMERIC(18, 2)` | no | 0 |
| `min_purchase` | `NUMERIC(18, 2)` | no | 0 |
| `max_discount` | `NUMERIC(18, 2)` | yes | — |
| `quota` | `INTEGER` | no | 100 |
| `used_count` | `INTEGER` | no | 0 |
| `quota_per_user` | `INTEGER` | no | 1 |
| `start_at` | `DATETIME(6)` | no | — |
| `end_at` | `DATETIME(6)` | no | — |
| `is_active` | `BOOL` | no | 1 |
| `created_at` | `DATETIME(6)` | no | now(6) |

Unique keys:

- `code`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `discount_value >= 0 AND min_purchase >= 0 AND (max_discount IS NULL OR max_discount >= 0)`.
- `discount_type <> 'percent' OR discount_value <= 100`.
- `quota >= 0 AND used_count >= 0 AND used_count <= quota AND quota_per_user >= 0`.
- `discount_type IN ('percent','nominal','free_shipping')`.
- `end_at > start_at`.

Indexes:

- `ix_vouchers_window`: `is_active, start_at, end_at`.

## whatsapp_settings

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `SMALLINT` | no | application: 1 |
| `phone` | `VARCHAR(32)` | no | — |
| `default_text` | `TEXT` | no | — |
| `is_enabled` | `BOOL` | no | 0 |
| `updated_by` | `VARCHAR(64) COLLATE utf8mb4_bin` | yes | — |
| `updated_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `updated_by` → `users.user_id`; delete `RESTRICT`.

Row rules (enforced by MySQL 5.7 validation triggers):

- `id = 1`.

## wishlists

| Column | MySQL type | Null | Default / generated |
| --- | --- | --- | --- |
| `id` (PK) | `VARCHAR(64) COLLATE utf8mb4_bin` | no | application generated |
| `user_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `product_id` | `VARCHAR(64) COLLATE utf8mb4_bin` | no | — |
| `created_at` | `DATETIME(6)` | no | now(6) |

Foreign keys:

- `product_id` → `products.id`; delete `CASCADE`.
- `user_id` → `users.user_id`; delete `CASCADE`.

Unique keys:

- `user_id, product_id`.
