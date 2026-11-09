SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
) ROW_FORMAT=DYNAMIC;

-- Running upgrade  -> 20261106_0001

CREATE TABLE article_categories (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    slug VARCHAR(191) NOT NULL, 
    description TEXT, 
    is_active BOOL NOT NULL DEFAULT '1', 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_article_categories PRIMARY KEY (id), 
    CONSTRAINT uq_article_categories_slug UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE brands (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    slug VARCHAR(191) NOT NULL, 
    logo TEXT, 
    description TEXT, 
    is_active BOOL NOT NULL DEFAULT '1', 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_brands PRIMARY KEY (id), 
    CONSTRAINT uq_brands_slug UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE categories (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    parent_id VARCHAR(64) COLLATE utf8mb4_bin, 
    name VARCHAR(255) NOT NULL, 
    slug VARCHAR(191) NOT NULL, 
    description TEXT, 
    category_type VARCHAR(32) NOT NULL DEFAULT 'product', 
    icon TEXT, 
    banner_image TEXT, 
    level INTEGER NOT NULL DEFAULT '0', 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    is_featured BOOL NOT NULL DEFAULT '0', 
    is_active BOOL NOT NULL DEFAULT '1', 
    seo_title VARCHAR(255), 
    seo_description TEXT, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_categories PRIMARY KEY (id), 
    CONSTRAINT fk_categories_parent_id_categories_id FOREIGN KEY(parent_id) REFERENCES categories (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_categories_slug UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_categories_parent_sort ON categories (parent_id, sort_order, id);

CREATE TABLE cms_pages (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    page_type VARCHAR(32) NOT NULL DEFAULT 'custom', 
    title VARCHAR(255) NOT NULL, 
    slug VARCHAR(191) NOT NULL, 
    content MEDIUMTEXT NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'draft', 
    version INTEGER NOT NULL DEFAULT '1', 
    seo_title VARCHAR(255), 
    seo_description TEXT, 
    published_at DATETIME(6), 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_cms_pages PRIMARY KEY (id), 
    CONSTRAINT uq_cms_pages_slug UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE contact_messages (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    phone VARCHAR(32), 
    subject VARCHAR(255), 
    message TEXT NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'new', 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_contact_messages PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_contact_messages_inbox ON contact_messages (status, created_at);

CREATE TABLE contact_settings (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    singleton_key SMALLINT NOT NULL DEFAULT '1', 
    store_name VARCHAR(255) NOT NULL DEFAULT 'Meow Eyes', 
    address TEXT NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    phone VARCHAR(32) NOT NULL, 
    operational_hours VARCHAR(255) NOT NULL, 
    instagram TEXT, 
    facebook TEXT, 
    tiktok TEXT, 
    tokopedia TEXT, 
    shopee TEXT, 
    google_maps_embed TEXT, 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_contact_settings PRIMARY KEY (id), 
    CONSTRAINT uq_contact_settings_singleton_key UNIQUE (singleton_key)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE faq_categories (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    slug VARCHAR(191) NOT NULL, 
    description TEXT, 
    is_active BOOL NOT NULL DEFAULT '1', 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    CONSTRAINT pk_faq_categories PRIMARY KEY (id), 
    CONSTRAINT uq_faq_categories_slug UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE flash_sales (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    start_at DATETIME(6) NOT NULL, 
    end_at DATETIME(6) NOT NULL, 
    is_active BOOL NOT NULL DEFAULT '1', 
    activated_at DATETIME(6), 
    ended_at DATETIME(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_flash_sales PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_flash_sales_window ON flash_sales (is_active, start_at, end_at);

CREATE TABLE games (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    `key` VARCHAR(32) NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    description TEXT, 
    is_active BOOL NOT NULL DEFAULT '1', 
    image TEXT, 
    max_points INTEGER NOT NULL DEFAULT '50', 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_games PRIMARY KEY (id), 
    CONSTRAINT uq_games_key UNIQUE (`key`)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE lens_indexes (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    index_value VARCHAR(32) NOT NULL, 
    description TEXT, 
    thickness_level VARCHAR(32) NOT NULL DEFAULT 'medium', 
    recommended_power_range VARCHAR(255) NOT NULL DEFAULT '', 
    additional_price NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    is_active BOOL NOT NULL DEFAULT '1', 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    CONSTRAINT pk_lens_indexes PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_lens_indexes_index_value ON lens_indexes (index_value);

CREATE TABLE migration_runs (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    source_label VARCHAR(255) NOT NULL, 
    export_checksum VARCHAR(64) COLLATE utf8mb4_bin, 
    schema_revision VARCHAR(64) NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'planned', 
    source_count BIGINT NOT NULL DEFAULT '0', 
    migrated_count BIGINT NOT NULL DEFAULT '0', 
    rejected_count BIGINT NOT NULL DEFAULT '0', 
    started_at DATETIME(6), 
    completed_at DATETIME(6), 
    CONSTRAINT pk_migration_runs PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE newsletter_campaigns (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    subject VARCHAR(255) NOT NULL, 
    body TEXT NOT NULL, 
    segment VARCHAR(64) NOT NULL DEFAULT 'all', 
    status VARCHAR(32) NOT NULL, 
    sent_count INTEGER NOT NULL DEFAULT '0', 
    failed_count INTEGER NOT NULL DEFAULT '0', 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_newsletter_campaigns PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE product_knowledges (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    knowledge_type VARCHAR(32) NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    slug VARCHAR(191) NOT NULL, 
    description TEXT, 
    content MEDIUMTEXT NOT NULL, 
    image TEXT, 
    icon TEXT, 
    face_shape_recommendation TEXT, 
    style_recommendation TEXT, 
    filter_param JSON, 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    status VARCHAR(16) NOT NULL DEFAULT 'draft', 
    seo_title VARCHAR(255), 
    seo_description TEXT, 
    published_at DATETIME(6), 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_product_knowledges PRIMARY KEY (id), 
    CONSTRAINT uq_product_knowledges_slug UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_knowledge_public ON product_knowledges (knowledge_type, status, sort_order, id);

CREATE TABLE roulette_rewards (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    label VARCHAR(255) NOT NULL, 
    type VARCHAR(32) NOT NULL, 
    value NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    color VARCHAR(16) NOT NULL DEFAULT '#FF6B6B', 
    probability NUMERIC(18, 8) NOT NULL DEFAULT '0.1', 
    is_active BOOL NOT NULL DEFAULT '1', 
    CONSTRAINT pk_roulette_rewards PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE users (
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    picture TEXT, 
    password_hash VARCHAR(255), 
    pin_hash VARCHAR(255), 
    pin_failed_attempts INTEGER NOT NULL DEFAULT '0', 
    pin_locked_until DATETIME(6), 
    `role` VARCHAR(32) NOT NULL DEFAULT 'customer', 
    provider VARCHAR(32) NOT NULL DEFAULT 'password', 
    is_active BOOL NOT NULL DEFAULT '1', 
    points_balance BIGINT NOT NULL DEFAULT '0', 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_users PRIMARY KEY (user_id), 
    CONSTRAINT uq_users_email UNIQUE (email)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE vouchers (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    code VARCHAR(128) NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    discount_type VARCHAR(32) NOT NULL, 
    discount_value NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    min_purchase NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    max_discount NUMERIC(18, 2), 
    quota INTEGER NOT NULL DEFAULT '100', 
    used_count INTEGER NOT NULL DEFAULT '0', 
    quota_per_user INTEGER NOT NULL DEFAULT '1', 
    start_at DATETIME(6) NOT NULL, 
    end_at DATETIME(6) NOT NULL, 
    is_active BOOL NOT NULL DEFAULT '1', 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_vouchers PRIMARY KEY (id), 
    CONSTRAINT uq_vouchers_code UNIQUE (code)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_vouchers_window ON vouchers (is_active, start_at, end_at);

CREATE TABLE addresses (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    label VARCHAR(100) NOT NULL, 
    recipient VARCHAR(255) NOT NULL, 
    phone VARCHAR(32) NOT NULL, 
    street TEXT NOT NULL, 
    subdistrict VARCHAR(128), 
    district VARCHAR(128), 
    city VARCHAR(128) NOT NULL, 
    province VARCHAR(128) NOT NULL, 
    postal_code VARCHAR(16) NOT NULL, 
    country_code VARCHAR(2) NOT NULL DEFAULT 'ID', 
    everpro_destination_id VARCHAR(128), 
    is_default BOOL NOT NULL DEFAULT '0', 
    default_for_user VARCHAR(64) COLLATE utf8mb4_bin GENERATED ALWAYS AS (CASE WHEN is_default = 1 THEN user_id ELSE NULL END) STORED, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_addresses PRIMARY KEY (id), 
    CONSTRAINT fk_addresses_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_addresses_default_for_user UNIQUE (default_for_user), 
    CONSTRAINT uq_addresses_id_user_id UNIQUE (id, user_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_addresses_user_id ON addresses (user_id);

CREATE TABLE articles (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    category_id VARCHAR(64) COLLATE utf8mb4_bin, 
    author_id VARCHAR(64) COLLATE utf8mb4_bin, 
    author_name VARCHAR(255) NOT NULL DEFAULT 'Admin Meow', 
    title VARCHAR(255) NOT NULL, 
    slug VARCHAR(191) NOT NULL, 
    excerpt TEXT, 
    content MEDIUMTEXT NOT NULL, 
    thumbnail TEXT, 
    status VARCHAR(16) NOT NULL DEFAULT 'draft', 
    view_count BIGINT NOT NULL DEFAULT '0', 
    seo_title VARCHAR(255), 
    seo_description TEXT, 
    published_at DATETIME(6), 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_articles PRIMARY KEY (id), 
    CONSTRAINT fk_articles_author_id_users_user_id FOREIGN KEY(author_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_articles_category_id_article_categories_id FOREIGN KEY(category_id) REFERENCES article_categories (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_articles_slug UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_articles_category ON articles (category_id, status, published_at, id);

CREATE INDEX ix_articles_public ON articles (status, published_at, id);

CREATE TABLE faqs (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    category_id VARCHAR(64) COLLATE utf8mb4_bin, 
    question TEXT NOT NULL, 
    answer TEXT NOT NULL, 
    is_active BOOL NOT NULL DEFAULT '1', 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_faqs PRIMARY KEY (id), 
    CONSTRAINT fk_faqs_category_id_faq_categories_id FOREIGN KEY(category_id) REFERENCES faq_categories (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_faqs_public ON faqs (category_id, is_active, sort_order);

CREATE TABLE flash_sale_categories (
    flash_sale_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    category_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    include_descendants BOOL NOT NULL DEFAULT '1', 
    discount_type VARCHAR(16) NOT NULL, 
    discount_value NUMERIC(18, 2) NOT NULL, 
    quota_per_product INTEGER NOT NULL, 
    CONSTRAINT pk_flash_sale_categories PRIMARY KEY (flash_sale_id, category_id), 
    CONSTRAINT fk_flash_sale_categories_category_id_categories_id FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_flash_sale_categories_flash_sale_id_flash_sales_id FOREIGN KEY(flash_sale_id) REFERENCES flash_sales (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE game_scores (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    game VARCHAR(32) NOT NULL, 
    score INTEGER NOT NULL, 
    points_awarded INTEGER NOT NULL DEFAULT '0', 
    played_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_game_scores PRIMARY KEY (id), 
    CONSTRAINT fk_game_scores_game_games_key FOREIGN KEY(game) REFERENCES games (`key`) ON DELETE RESTRICT, 
    CONSTRAINT fk_game_scores_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_game_scores_daily ON game_scores (user_id, game, played_at);

CREATE INDEX ix_game_scores_leaderboard ON game_scores (game, score, user_id);

CREATE TABLE migration_records (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    run_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    source_collection VARCHAR(64) NOT NULL, 
    source_id VARCHAR(191) COLLATE utf8mb4_bin NOT NULL, 
    source_checksum VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    target_table VARCHAR(64) NOT NULL, 
    target_id VARCHAR(255) NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'planned', 
    verified_at DATETIME(6), 
    CONSTRAINT pk_migration_records PRIMARY KEY (id), 
    CONSTRAINT fk_migration_records_run_id_migration_runs_id FOREIGN KEY(run_id) REFERENCES migration_runs (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_migration_records_run_id_source_collection__93422a0acfa6 UNIQUE (run_id, source_collection, source_id, target_table, target_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_migration_records_run_id ON migration_records (run_id);

CREATE INDEX ix_migration_records_source ON migration_records (source_collection, source_id);

CREATE TABLE newsletter_subscribers (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin, 
    is_active BOOL NOT NULL DEFAULT '1', 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_newsletter_subscribers PRIMARY KEY (id), 
    CONSTRAINT fk_newsletter_subscribers_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE SET NULL, 
    CONSTRAINT uq_newsletter_subscribers_email UNIQUE (email)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE product_knowledge_bullets (
    knowledge_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    kind VARCHAR(3) NOT NULL, 
    sort_order INTEGER NOT NULL, 
    body TEXT NOT NULL, 
    CONSTRAINT pk_product_knowledge_bullets PRIMARY KEY (knowledge_id, kind, sort_order), 
    CONSTRAINT fk_product_knowledge_bullets_knowledge_id_prod_841a09e24921 FOREIGN KEY(knowledge_id) REFERENCES product_knowledges (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE products (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    slug VARCHAR(191) NOT NULL, 
    sku VARCHAR(128) NOT NULL, 
    description TEXT NOT NULL, 
    spec JSON, 
    product_type VARCHAR(16) NOT NULL DEFAULT 'frame', 
    primary_category_id VARCHAR(64) COLLATE utf8mb4_bin, 
    brand_id VARCHAR(64) COLLATE utf8mb4_bin, 
    price NUMERIC(18, 2) NOT NULL, 
    discount_price NUMERIC(18, 2), 
    flash_sale_price NUMERIC(18, 2), 
    weight_gram INTEGER NOT NULL DEFAULT '100', 
    dimension VARCHAR(255), 
    main_image TEXT NOT NULL, 
    min_stock_alert INTEGER NOT NULL DEFAULT '5', 
    rating_avg NUMERIC(3, 2) NOT NULL DEFAULT '0', 
    rating_count INTEGER NOT NULL DEFAULT '0', 
    sold_count BIGINT NOT NULL DEFAULT '0', 
    is_active BOOL NOT NULL DEFAULT '1', 
    is_new_arrival BOOL NOT NULL DEFAULT '0', 
    new_arrival_until DATETIME(6), 
    seo_title VARCHAR(255), 
    seo_description TEXT, 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_products PRIMARY KEY (id), 
    CONSTRAINT fk_products_brand_id_brands_id FOREIGN KEY(brand_id) REFERENCES brands (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_products_primary_category_id_categories_id FOREIGN KEY(primary_category_id) REFERENCES categories (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_products_sku UNIQUE (sku), 
    CONSTRAINT uq_products_slug UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE FULLTEXT INDEX ft_products_name_description ON products (name, description);

CREATE INDEX ix_products_arrivals ON products (is_active, product_type, is_new_arrival, created_at, id);

CREATE INDEX ix_products_brand_id ON products (brand_id);

CREATE INDEX ix_products_price ON products (is_active, price, id);

CREATE INDEX ix_products_primary_category_id ON products (primary_category_id);

CREATE INDEX ix_products_shop ON products (is_active, product_type, created_at, id);

CREATE TABLE roulette_spins (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    reward_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    reward_label VARCHAR(255) NOT NULL, 
    reward_type VARCHAR(32) NOT NULL, 
    reward_value NUMERIC(18, 2) NOT NULL, 
    used BOOL NOT NULL DEFAULT '0', 
    expires_at DATETIME(6) NOT NULL, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_roulette_spins PRIMARY KEY (id), 
    CONSTRAINT fk_roulette_spins_reward_id_roulette_rewards_id FOREIGN KEY(reward_id) REFERENCES roulette_rewards (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_roulette_spins_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_roulette_spins_id_user_id UNIQUE (id, user_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_roulette_spins_eligibility ON roulette_spins (user_id, used, expires_at);

CREATE INDEX ix_roulette_spins_user_date ON roulette_spins (user_id, created_at);

CREATE TABLE settings (
    `key` VARCHAR(128) NOT NULL, 
    value JSON NOT NULL, 
    description TEXT, 
    is_public BOOL NOT NULL DEFAULT '0', 
    updated_by VARCHAR(64) COLLATE utf8mb4_bin, 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_settings PRIMARY KEY (`key`), 
    CONSTRAINT fk_settings_updated_by_users_user_id FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE shipping_quotes (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    provider VARCHAR(32) NOT NULL DEFAULT 'everpro', 
    provider_quote_id VARCHAR(191), 
    origin_id VARCHAR(128) NOT NULL, 
    destination_id VARCHAR(128) NOT NULL, 
    courier_code VARCHAR(64) NOT NULL, 
    service_code VARCHAR(64) NOT NULL, 
    service_label VARCHAR(255), 
    weight_gram INTEGER NOT NULL, 
    cost NUMERIC(18, 2) NOT NULL, 
    insurance_cost NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    currency VARCHAR(3) NOT NULL DEFAULT 'IDR', 
    estimated_delivery VARCHAR(128), 
    cart_fingerprint VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    expires_at DATETIME(6) NOT NULL, 
    request_payload JSON, 
    response_payload JSON, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_shipping_quotes PRIMARY KEY (id), 
    CONSTRAINT fk_shipping_quotes_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_shipping_quotes_id_user_id UNIQUE (id, user_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_shipping_quotes_user_expiry ON shipping_quotes (user_id, expires_at);

CREATE TABLE uploads (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    url TEXT, 
    filename VARCHAR(255) NOT NULL, 
    mime VARCHAR(128) NOT NULL, 
    size BIGINT NOT NULL, 
    subdir VARCHAR(128), 
    disk_name VARCHAR(255), 
    storage_provider VARCHAR(32) NOT NULL DEFAULT 'local', 
    storage_key TEXT, 
    visibility VARCHAR(16) NOT NULL DEFAULT 'public', 
    sha256 VARCHAR(64) COLLATE utf8mb4_bin, 
    uploaded_by VARCHAR(64) COLLATE utf8mb4_bin, 
    uploaded_by_name VARCHAR(255), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_uploads PRIMARY KEY (id), 
    CONSTRAINT fk_uploads_uploaded_by_users_user_id FOREIGN KEY(uploaded_by) REFERENCES users (user_id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_uploads_uploaded_by ON uploads (uploaded_by);

CREATE TABLE user_permissions (
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    permission VARCHAR(100) NOT NULL, 
    CONSTRAINT pk_user_permissions PRIMARY KEY (user_id, permission), 
    CONSTRAINT fk_user_permissions_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE user_sessions (
    session_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    token_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    expires_at DATETIME(6) NOT NULL, 
    revoked_at DATETIME(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_user_sessions PRIMARY KEY (session_id), 
    CONSTRAINT fk_user_sessions_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
    CONSTRAINT uq_user_sessions_token_hash UNIQUE (token_hash)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_user_sessions_expiry ON user_sessions (expires_at);

CREATE INDEX ix_user_sessions_user_id ON user_sessions (user_id);

CREATE TABLE whatsapp_settings (
    id SMALLINT NOT NULL, 
    phone VARCHAR(32) NOT NULL, 
    default_text TEXT NOT NULL, 
    is_enabled BOOL NOT NULL DEFAULT '0', 
    updated_by VARCHAR(64) COLLATE utf8mb4_bin, 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_whatsapp_settings PRIMARY KEY (id), 
    CONSTRAINT fk_whatsapp_settings_updated_by_users_user_id FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE article_tags (
    article_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    tag VARCHAR(128) NOT NULL, 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    CONSTRAINT pk_article_tags PRIMARY KEY (article_id, tag), 
    CONSTRAINT fk_article_tags_article_id_articles_id FOREIGN KEY(article_id) REFERENCES articles (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE banners (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    image_desktop TEXT NOT NULL, 
    image_mobile TEXT, 
    link_type VARCHAR(16) NOT NULL DEFAULT 'internal', 
    link_url TEXT NOT NULL, 
    link_product_id VARCHAR(64) COLLATE utf8mb4_bin, 
    link_category_id VARCHAR(64) COLLATE utf8mb4_bin, 
    link_article_id VARCHAR(64) COLLATE utf8mb4_bin, 
    link_flash_sale_id VARCHAR(64) COLLATE utf8mb4_bin, 
    position VARCHAR(64) NOT NULL DEFAULT 'hero', 
    target_device VARCHAR(16) NOT NULL DEFAULT 'all', 
    alt_text VARCHAR(255), 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    start_at DATETIME(6), 
    end_at DATETIME(6), 
    is_active BOOL NOT NULL DEFAULT '1', 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_banners PRIMARY KEY (id), 
    CONSTRAINT fk_banners_link_article_id_articles_id FOREIGN KEY(link_article_id) REFERENCES articles (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_banners_link_category_id_categories_id FOREIGN KEY(link_category_id) REFERENCES categories (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_banners_link_flash_sale_id_flash_sales_id FOREIGN KEY(link_flash_sale_id) REFERENCES flash_sales (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_banners_link_product_id_products_id FOREIGN KEY(link_product_id) REFERENCES products (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_banners_display ON banners (position, is_active, sort_order, id);

CREATE TABLE flash_sale_items (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    flash_sale_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    source_category_id VARCHAR(64) COLLATE utf8mb4_bin, 
    flash_price NUMERIC(18, 2) NOT NULL, 
    quota INTEGER NOT NULL, 
    sold INTEGER NOT NULL DEFAULT '0', 
    reserved INTEGER NOT NULL DEFAULT '0', 
    is_active BOOL NOT NULL DEFAULT '1', 
    CONSTRAINT pk_flash_sale_items PRIMARY KEY (id), 
    CONSTRAINT fk_flash_sale_items_flash_sale_id_source_categ_0c2c06d567df FOREIGN KEY(flash_sale_id, source_category_id) REFERENCES flash_sale_categories (flash_sale_id, category_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_flash_sale_items_flash_sale_id_flash_sales_id FOREIGN KEY(flash_sale_id) REFERENCES flash_sales (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_flash_sale_items_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_flash_sale_items_flash_sale_id_product_id UNIQUE (flash_sale_id, product_id), 
    CONSTRAINT uq_flash_sale_items_id_product_id UNIQUE (id, product_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_flash_sale_items_product ON flash_sale_items (product_id, flash_sale_id);

CREATE TABLE migration_issues (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    run_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    record_id VARCHAR(64) COLLATE utf8mb4_bin, 
    source_collection VARCHAR(64) NOT NULL, 
    source_id VARCHAR(191) COLLATE utf8mb4_bin NOT NULL, 
    field_name VARCHAR(128), 
    issue_code VARCHAR(128) NOT NULL, 
    severity VARCHAR(16) NOT NULL DEFAULT 'error', 
    explanation TEXT NOT NULL, 
    resolved_at DATETIME(6), 
    resolved_by VARCHAR(64) COLLATE utf8mb4_bin, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_migration_issues PRIMARY KEY (id), 
    CONSTRAINT fk_migration_issues_record_id_migration_records_id FOREIGN KEY(record_id) REFERENCES migration_records (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_migration_issues_resolved_by_users_user_id FOREIGN KEY(resolved_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_migration_issues_run_id_migration_runs_id FOREIGN KEY(run_id) REFERENCES migration_runs (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_migration_issues_resolution ON migration_issues (run_id, severity, resolved_at);

CREATE TABLE orders (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_number VARCHAR(64) NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    subtotal NUMERIC(18, 2) NOT NULL, 
    discount NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    flash_sale_discount NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    voucher_code VARCHAR(128), 
    voucher_discount NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    points_used BIGINT NOT NULL DEFAULT '0', 
    points_discount NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    roulette_discount NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    shipping_quote_id VARCHAR(64) COLLATE utf8mb4_bin, 
    shipping_courier VARCHAR(64) NOT NULL, 
    shipping_service VARCHAR(64) NOT NULL, 
    shipping_cost NUMERIC(18, 2) NOT NULL, 
    total NUMERIC(18, 2) NOT NULL, 
    currency VARCHAR(3) NOT NULL DEFAULT 'IDR', 
    status VARCHAR(32) NOT NULL DEFAULT 'pending_payment', 
    payment_status VARCHAR(32) NOT NULL DEFAULT 'pending', 
    shipment_status VARCHAR(32) NOT NULL DEFAULT 'pending', 
    reservation_expires_at DATETIME(6), 
    completed_at DATETIME(6), 
    checkout_idempotency_key VARCHAR(191) COLLATE utf8mb4_bin, 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_orders PRIMARY KEY (id), 
    CONSTRAINT fk_orders_shipping_quote_id_user_id_shipping_q_5bb98f5fe9ef FOREIGN KEY(shipping_quote_id, user_id) REFERENCES shipping_quotes (id, user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_orders_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_orders_checkout_idempotency_key UNIQUE (checkout_idempotency_key), 
    CONSTRAINT uq_orders_id_user_id UNIQUE (id, user_id), 
    CONSTRAINT uq_orders_order_number UNIQUE (order_number)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_orders_customer_date ON orders (user_id, created_at, id);

CREATE INDEX ix_orders_expiry ON orders (status, reservation_expires_at, id);

CREATE INDEX ix_orders_payment_date ON orders (payment_status, created_at);

CREATE INDEX ix_orders_shipment_status ON orders (shipment_status, updated_at);

CREATE TABLE prescriptions (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    pd_total NUMERIC(5, 2), 
    pd_right NUMERIC(5, 2), 
    pd_left NUMERIC(5, 2), 
    attachment_upload_id VARCHAR(64) COLLATE utf8mb4_bin, 
    notes TEXT, 
    is_order_snapshot BOOL NOT NULL DEFAULT '0', 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_prescriptions PRIMARY KEY (id), 
    CONSTRAINT fk_prescriptions_attachment_upload_id_uploads_id FOREIGN KEY(attachment_upload_id) REFERENCES uploads (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_prescriptions_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_prescriptions_id_user_id UNIQUE (id, user_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_prescriptions_user_id ON prescriptions (user_id);

CREATE TABLE product_badges (
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    badge VARCHAR(64) NOT NULL, 
    CONSTRAINT pk_product_badges PRIMARY KEY (product_id, badge), 
    CONSTRAINT fk_product_badges_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_product_badges_badge ON product_badges (badge, product_id);

CREATE TABLE product_categories (
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    category_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    CONSTRAINT pk_product_categories PRIMARY KEY (product_id, category_id), 
    CONSTRAINT fk_product_categories_category_id_categories_id FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_product_categories_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_product_categories_category ON product_categories (category_id, product_id);

CREATE TABLE product_images (
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    sort_order INTEGER NOT NULL, 
    image_url TEXT NOT NULL, 
    alt_text VARCHAR(255), 
    CONSTRAINT pk_product_images PRIMARY KEY (product_id, sort_order), 
    CONSTRAINT fk_product_images_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE product_knowledge_products (
    knowledge_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    CONSTRAINT pk_product_knowledge_products PRIMARY KEY (knowledge_id, product_id), 
    CONSTRAINT fk_product_knowledge_products_knowledge_id_pro_7120bf35fe3c FOREIGN KEY(knowledge_id) REFERENCES product_knowledges (id) ON DELETE CASCADE, 
    CONSTRAINT fk_product_knowledge_products_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE product_segments (
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    segment VARCHAR(64) NOT NULL, 
    CONSTRAINT pk_product_segments PRIMARY KEY (product_id, segment), 
    CONSTRAINT fk_product_segments_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_product_segments_segment ON product_segments (segment, product_id);

CREATE TABLE product_subscriptions (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    notify_stock BOOL NOT NULL DEFAULT '1', 
    notify_price_drop BOOL NOT NULL DEFAULT '1', 
    notify_flash_sale BOOL NOT NULL DEFAULT '1', 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_product_subscriptions PRIMARY KEY (id), 
    CONSTRAINT fk_product_subscriptions_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
    CONSTRAINT fk_product_subscriptions_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
    CONSTRAINT uq_product_subscriptions_user_id_product_id UNIQUE (user_id, product_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE product_variants (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    color VARCHAR(128), 
    color_hex VARCHAR(16), 
    size VARCHAR(100), 
    lens_type VARCHAR(128), 
    sku VARCHAR(128) NOT NULL, 
    stock INTEGER NOT NULL DEFAULT '0', 
    reserved INTEGER NOT NULL DEFAULT '0', 
    price_override NUMERIC(18, 2), 
    is_active BOOL NOT NULL DEFAULT '1', 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_product_variants PRIMARY KEY (id), 
    CONSTRAINT fk_product_variants_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_product_variants_product_id_id UNIQUE (product_id, id), 
    CONSTRAINT uq_product_variants_sku UNIQUE (sku)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE wishlists (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_wishlists PRIMARY KEY (id), 
    CONSTRAINT fk_wishlists_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
    CONSTRAINT fk_wishlists_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
    CONSTRAINT uq_wishlists_user_id_product_id UNIQUE (user_id, product_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE cart_items (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    variant_id VARCHAR(64) COLLATE utf8mb4_bin, 
    quantity INTEGER NOT NULL DEFAULT '1', 
    lens_product_id VARCHAR(64) COLLATE utf8mb4_bin, 
    lens_variant_id VARCHAR(64) COLLATE utf8mb4_bin, 
    lens_index_id VARCHAR(64) COLLATE utf8mb4_bin, 
    prescription_id VARCHAR(64) COLLATE utf8mb4_bin, 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_cart_items PRIMARY KEY (id), 
    CONSTRAINT fk_cart_items_lens_index_id_lens_indexes_id FOREIGN KEY(lens_index_id) REFERENCES lens_indexes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_cart_items_lens_product_id_lens_variant_id__c4ad8059d234 FOREIGN KEY(lens_product_id, lens_variant_id) REFERENCES product_variants (product_id, id) ON DELETE RESTRICT, 
    CONSTRAINT fk_cart_items_lens_product_id_products_id FOREIGN KEY(lens_product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_cart_items_prescription_id_user_id_prescrip_2529d3d7b52d FOREIGN KEY(prescription_id, user_id) REFERENCES prescriptions (id, user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_cart_items_product_id_variant_id_product_va_65f2cb01a646 FOREIGN KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON DELETE RESTRICT, 
    CONSTRAINT fk_cart_items_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_cart_items_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_cart_items_user_created ON cart_items (user_id, created_at, id);

CREATE TABLE integration_webhook_events (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    provider VARCHAR(32) NOT NULL, 
    event_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL, 
    payload_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin, 
    event_type VARCHAR(128), 
    signature_verified BOOL NOT NULL DEFAULT '0', 
    payload JSON NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'received', 
    attempts INTEGER NOT NULL DEFAULT '0', 
    error_code VARCHAR(128), 
    received_at DATETIME(6) NOT NULL DEFAULT now(6), 
    processed_at DATETIME(6), 
    CONSTRAINT pk_integration_webhook_events PRIMARY KEY (id), 
    CONSTRAINT fk_integration_webhook_events_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_integration_webhook_events_provider_event_key UNIQUE (provider, event_key)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_webhook_events_retry ON integration_webhook_events (status, received_at);

CREATE TABLE order_addresses (
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    source_address_id VARCHAR(64) COLLATE utf8mb4_bin, 
    source_created_at DATETIME(6), 
    source_is_default BOOL, 
    label VARCHAR(100), 
    recipient VARCHAR(255) NOT NULL, 
    phone VARCHAR(32) NOT NULL, 
    street TEXT NOT NULL, 
    subdistrict VARCHAR(128), 
    district VARCHAR(128), 
    city VARCHAR(128) NOT NULL, 
    province VARCHAR(128) NOT NULL, 
    postal_code VARCHAR(16) NOT NULL, 
    country_code VARCHAR(2) NOT NULL DEFAULT 'ID', 
    everpro_destination_id VARCHAR(128), 
    CONSTRAINT pk_order_addresses PRIMARY KEY (order_id), 
    CONSTRAINT fk_order_addresses_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE order_items (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    variant_id VARCHAR(64) COLLATE utf8mb4_bin, 
    product_name VARCHAR(255) NOT NULL, 
    sku VARCHAR(128), 
    variant_label VARCHAR(255), 
    main_image TEXT, 
    quantity INTEGER NOT NULL, 
    unit_price NUMERIC(18, 2) NOT NULL, 
    subtotal NUMERIC(18, 2) NOT NULL, 
    sort_order INTEGER NOT NULL, 
    CONSTRAINT pk_order_items PRIMARY KEY (id), 
    CONSTRAINT fk_order_items_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_order_items_product_id_variant_id_product_v_7663bb3c8106 FOREIGN KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON DELETE RESTRICT, 
    CONSTRAINT fk_order_items_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_order_items_id_order_id_product_id UNIQUE (id, order_id, product_id), 
    CONSTRAINT uq_order_items_id_order_id UNIQUE (id, order_id), 
    CONSTRAINT uq_order_items_id_product_id UNIQUE (id, product_id), 
    CONSTRAINT uq_order_items_order_id_sort_order UNIQUE (order_id, sort_order)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_order_items_product_id ON order_items (product_id);

CREATE TABLE order_reviews (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    rating SMALLINT NOT NULL, 
    body TEXT, 
    status VARCHAR(16) NOT NULL DEFAULT 'pending', 
    admin_reply TEXT, 
    moderated_by VARCHAR(64) COLLATE utf8mb4_bin, 
    moderated_at DATETIME(6), 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_order_reviews PRIMARY KEY (id), 
    CONSTRAINT fk_order_reviews_moderated_by_users_user_id FOREIGN KEY(moderated_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_order_reviews_order_id_user_id_orders_id_orders_user_id FOREIGN KEY(order_id, user_id) REFERENCES orders (id, user_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_order_reviews_order_id UNIQUE (order_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE order_status_logs (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    status VARCHAR(32) NOT NULL, 
    note TEXT, 
    admin_id VARCHAR(64) COLLATE utf8mb4_bin, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_order_status_logs PRIMARY KEY (id), 
    CONSTRAINT fk_order_status_logs_admin_id_users_user_id FOREIGN KEY(admin_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_order_status_logs_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_order_status_logs_timeline ON order_status_logs (order_id, created_at, id);

CREATE TABLE payments (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    provider VARCHAR(32) NOT NULL DEFAULT 'doku', 
    request_id VARCHAR(191) COLLATE utf8mb4_bin NOT NULL, 
    merchant_reference VARCHAR(191) COLLATE utf8mb4_bin NOT NULL, 
    external_id VARCHAR(191) COLLATE utf8mb4_bin, 
    amount NUMERIC(18, 2) NOT NULL, 
    currency VARCHAR(3) NOT NULL DEFAULT 'IDR', 
    method VARCHAR(64), 
    channel VARCHAR(64), 
    status VARCHAR(16) NOT NULL DEFAULT 'pending', 
    payment_url TEXT, 
    virtual_account_number VARCHAR(64), 
    expires_at DATETIME(6), 
    paid_at DATETIME(6), 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_payments PRIMARY KEY (id), 
    CONSTRAINT fk_payments_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_payments_id_order_id UNIQUE (id, order_id), 
    CONSTRAINT uq_payments_provider_external_id UNIQUE (provider, external_id), 
    CONSTRAINT uq_payments_provider_merchant_reference UNIQUE (provider, merchant_reference), 
    CONSTRAINT uq_payments_provider_request_id UNIQUE (provider, request_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_payments_order_status ON payments (order_id, status, created_at);

CREATE TABLE point_logs (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    delta BIGINT NOT NULL, 
    balance_after BIGINT NOT NULL, 
    type VARCHAR(64) NOT NULL, 
    note TEXT NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_point_logs PRIMARY KEY (id), 
    CONSTRAINT fk_point_logs_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_point_logs_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_point_logs_user_type_date ON point_logs (user_id, type, created_at, id);

CREATE TABLE prescription_eyes (
    prescription_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    eye VARCHAR(5) NOT NULL, 
    sph NUMERIC(5, 2), 
    cyl NUMERIC(5, 2), 
    axis SMALLINT, 
    `add` NUMERIC(5, 2), 
    CONSTRAINT pk_prescription_eyes PRIMARY KEY (prescription_id, eye), 
    CONSTRAINT fk_prescription_eyes_prescription_id_prescriptions_id FOREIGN KEY(prescription_id) REFERENCES prescriptions (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE roulette_redemptions (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    spin_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'reserved', 
    discount_amount NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    resolved_at DATETIME(6), 
    active_spin_id VARCHAR(64) COLLATE utf8mb4_bin GENERATED ALWAYS AS (CASE WHEN status IN ('reserved','redeemed') THEN spin_id ELSE NULL END) STORED, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_roulette_redemptions PRIMARY KEY (id), 
    CONSTRAINT fk_roulette_redemptions_order_id_user_id_order_a1ca5f3fa8b0 FOREIGN KEY(order_id, user_id) REFERENCES orders (id, user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_roulette_redemptions_spin_id_user_id_roulet_332771d0a44a FOREIGN KEY(spin_id, user_id) REFERENCES roulette_spins (id, user_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_roulette_redemptions_active_spin_id UNIQUE (active_spin_id), 
    CONSTRAINT uq_roulette_redemptions_order_id UNIQUE (order_id), 
    CONSTRAINT uq_roulette_redemptions_spin_id_order_id UNIQUE (spin_id, order_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE shipments (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    provider VARCHAR(32) NOT NULL DEFAULT 'everpro', 
    request_id VARCHAR(191) COLLATE utf8mb4_bin NOT NULL, 
    external_id VARCHAR(191) COLLATE utf8mb4_bin, 
    courier_code VARCHAR(64) NOT NULL, 
    service_code VARCHAR(64) NOT NULL, 
    tracking_number VARCHAR(191) COLLATE utf8mb4_bin, 
    label_url TEXT, 
    status VARCHAR(32) NOT NULL DEFAULT 'pending', 
    carrier_status VARCHAR(255), 
    cost NUMERIC(18, 2) NOT NULL, 
    currency VARCHAR(3) NOT NULL DEFAULT 'IDR', 
    last_checked_at DATETIME(6), 
    shipped_at DATETIME(6), 
    delivered_at DATETIME(6), 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_shipments PRIMARY KEY (id), 
    CONSTRAINT fk_shipments_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_shipments_id_order_id UNIQUE (id, order_id), 
    CONSTRAINT uq_shipments_provider_external_id UNIQUE (provider, external_id), 
    CONSTRAINT uq_shipments_provider_request_id UNIQUE (provider, request_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_shipments_order ON shipments (order_id, created_at);

CREATE INDEX ix_shipments_poll ON shipments (status, last_checked_at);

CREATE INDEX ix_shipments_tracking ON shipments (provider, tracking_number);

CREATE TABLE virtual_try_on_assets (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    variant_id VARCHAR(64) COLLATE utf8mb4_bin, 
    asset_type VARCHAR(8) NOT NULL, 
    upload_id VARCHAR(64) COLLATE utf8mb4_bin, 
    source_url TEXT, 
    preview_url TEXT, 
    scale NUMERIC(10, 5) NOT NULL DEFAULT '1', 
    offset_x NUMERIC(10, 5) NOT NULL DEFAULT '0', 
    offset_y NUMERIC(10, 5) NOT NULL DEFAULT '0', 
    offset_z NUMERIC(10, 5) NOT NULL DEFAULT '0', 
    rotation_x NUMERIC(10, 5) NOT NULL DEFAULT '0', 
    rotation_y NUMERIC(10, 5) NOT NULL DEFAULT '0', 
    rotation_z NUMERIC(10, 5) NOT NULL DEFAULT '0', 
    calibration JSON, 
    status VARCHAR(16) NOT NULL DEFAULT 'draft', 
    sort_order INTEGER NOT NULL DEFAULT '0', 
    updated_by VARCHAR(64) COLLATE utf8mb4_bin, 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_virtual_try_on_assets PRIMARY KEY (id), 
    CONSTRAINT fk_virtual_try_on_assets_product_id_variant_id_eacdeed585b2 FOREIGN KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON DELETE RESTRICT, 
    CONSTRAINT fk_virtual_try_on_assets_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_virtual_try_on_assets_updated_by_users_user_id FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_virtual_try_on_assets_upload_id_uploads_id FOREIGN KEY(upload_id) REFERENCES uploads (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_vto_product_status ON virtual_try_on_assets (product_id, status, sort_order);

CREATE TABLE voucher_redemptions (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    voucher_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    discount_amount NUMERIC(18, 2) NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'reserved', 
    resolved_at DATETIME(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_voucher_redemptions PRIMARY KEY (id), 
    CONSTRAINT fk_voucher_redemptions_order_id_user_id_orders_958e8f3a8056 FOREIGN KEY(order_id, user_id) REFERENCES orders (id, user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_voucher_redemptions_voucher_id_vouchers_id FOREIGN KEY(voucher_id) REFERENCES vouchers (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_voucher_redemptions_order_id UNIQUE (order_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_voucher_redemptions_quota ON voucher_redemptions (voucher_id, user_id, status);

CREATE TABLE flash_sale_reservations (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    flash_sale_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    quantity INTEGER NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'active', 
    expires_at DATETIME(6) NOT NULL, 
    resolved_at DATETIME(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_flash_sale_reservations PRIMARY KEY (id), 
    CONSTRAINT fk_flash_sale_reservations_flash_sale_item_id__6bebf7ad5666 FOREIGN KEY(flash_sale_item_id, product_id) REFERENCES flash_sale_items (id, product_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_flash_sale_reservations_order_item_id_produ_7cde6df012c5 FOREIGN KEY(order_item_id, product_id) REFERENCES order_items (id, product_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_flash_sale_reservations_order_item_id_flash_sale_item_id UNIQUE (order_item_id, flash_sale_item_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_flash_sale_reservations_expiry ON flash_sale_reservations (status, expires_at);

CREATE TABLE order_item_components (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    component_type VARCHAR(16) NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    variant_id VARCHAR(64) COLLATE utf8mb4_bin, 
    lens_index_id VARCHAR(64) COLLATE utf8mb4_bin, 
    product_name VARCHAR(255) NOT NULL, 
    sku VARCHAR(128), 
    variant_label VARCHAR(255), 
    lens_index_name VARCHAR(255), 
    quantity INTEGER NOT NULL, 
    unit_price NUMERIC(18, 2) NOT NULL, 
    index_surcharge NUMERIC(18, 2) NOT NULL DEFAULT '0', 
    subtotal NUMERIC(18, 2) NOT NULL, 
    sort_order INTEGER NOT NULL, 
    CONSTRAINT pk_order_item_components PRIMARY KEY (id), 
    CONSTRAINT fk_order_item_components_lens_index_id_lens_indexes_id FOREIGN KEY(lens_index_id) REFERENCES lens_indexes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_order_item_components_order_item_id_order_i_380ae62a849f FOREIGN KEY(order_item_id, order_id) REFERENCES order_items (id, order_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_order_item_components_product_id_variant_id_30553bf82c9a FOREIGN KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON DELETE RESTRICT, 
    CONSTRAINT fk_order_item_components_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_order_item_components_id_order_id_product_id UNIQUE (id, order_id, product_id), 
    CONSTRAINT uq_order_item_components_order_item_id_sort_order UNIQUE (order_item_id, sort_order)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_order_item_components_product_id ON order_item_components (product_id);

CREATE TABLE order_item_prescriptions (
    order_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    prescription_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    CONSTRAINT pk_order_item_prescriptions PRIMARY KEY (order_item_id), 
    CONSTRAINT fk_order_item_prescriptions_order_id_user_id_o_97780d5632ac FOREIGN KEY(order_id, user_id) REFERENCES orders (id, user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_order_item_prescriptions_order_item_id_orde_a665d0c8a4a5 FOREIGN KEY(order_item_id, order_id) REFERENCES order_items (id, order_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_order_item_prescriptions_prescription_id_us_3ffb11391bc0 FOREIGN KEY(prescription_id, user_id) REFERENCES prescriptions (id, user_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_order_item_prescriptions_prescription_id UNIQUE (prescription_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE payment_logs (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    payment_id VARCHAR(64) COLLATE utf8mb4_bin, 
    provider VARCHAR(32) NOT NULL, 
    action VARCHAR(64) NOT NULL, 
    payload JSON, 
    response JSON, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_payment_logs PRIMARY KEY (id), 
    CONSTRAINT fk_payment_logs_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_payment_logs_payment_id_order_id_payments_i_50865612f320 FOREIGN KEY(payment_id, order_id) REFERENCES payments (id, order_id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_payment_logs_order_date ON payment_logs (order_id, created_at, id);

CREATE TABLE shipment_logs (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    shipment_id VARCHAR(64) COLLATE utf8mb4_bin, 
    provider VARCHAR(32) NOT NULL, 
    action VARCHAR(64) NOT NULL, 
    payload JSON, 
    response JSON, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_shipment_logs PRIMARY KEY (id), 
    CONSTRAINT fk_shipment_logs_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_shipment_logs_shipment_id_order_id_shipment_d1998a94a236 FOREIGN KEY(shipment_id, order_id) REFERENCES shipments (id, order_id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_shipment_logs_order_date ON shipment_logs (order_id, created_at, id);

CREATE TABLE stock_reservations (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_item_id VARCHAR(64) COLLATE utf8mb4_bin, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    variant_id VARCHAR(64) COLLATE utf8mb4_bin, 
    quantity INTEGER NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'active', 
    expires_at DATETIME(6) NOT NULL, 
    resolved_at DATETIME(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_stock_reservations PRIMARY KEY (id), 
    CONSTRAINT fk_stock_reservations_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_stock_reservations_order_item_id_order_id_o_b9f7577dedc3 FOREIGN KEY(order_item_id, order_id) REFERENCES order_items (id, order_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_stock_reservations_product_id_variant_id_pr_ea500bef0394 FOREIGN KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON DELETE RESTRICT, 
    CONSTRAINT fk_stock_reservations_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_stock_reservations_expiry ON stock_reservations (status, expires_at, id);

CREATE INDEX ix_stock_reservations_order ON stock_reservations (order_id, status);

CREATE TABLE product_reviews (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin, 
    order_item_id VARCHAR(64) COLLATE utf8mb4_bin, 
    order_component_id VARCHAR(64) COLLATE utf8mb4_bin, 
    verified_purchase BOOL NOT NULL DEFAULT '0', 
    user_name VARCHAR(255) NOT NULL, 
    rating SMALLINT NOT NULL, 
    title VARCHAR(255), 
    body TEXT NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'pending', 
    admin_reply TEXT, 
    moderated_by VARCHAR(64) COLLATE utf8mb4_bin, 
    moderated_at DATETIME(6), 
    updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_product_reviews PRIMARY KEY (id), 
    CONSTRAINT fk_product_reviews_moderated_by_users_user_id FOREIGN KEY(moderated_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_product_reviews_order_component_id_order_id_00f2a90bf233 FOREIGN KEY(order_component_id, order_id, product_id) REFERENCES order_item_components (id, order_id, product_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_product_reviews_order_id_user_id_orders_id__9f09bd04e015 FOREIGN KEY(order_id, user_id) REFERENCES orders (id, user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_product_reviews_order_item_id_order_id_prod_375484e0a914 FOREIGN KEY(order_item_id, order_id, product_id) REFERENCES order_items (id, order_id, product_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_product_reviews_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_product_reviews_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_product_reviews_order_id_product_id_user_id UNIQUE (order_id, product_id, user_id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_product_reviews_public ON product_reviews (product_id, status, created_at, id);

CREATE TABLE stock_movements (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    variant_id VARCHAR(64) COLLATE utf8mb4_bin, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin, 
    reservation_id VARCHAR(64) COLLATE utf8mb4_bin, 
    type VARCHAR(64) NOT NULL, 
    quantity INTEGER NOT NULL, 
    delta INTEGER, 
    reserved_delta INTEGER, 
    stock_after INTEGER, 
    reserved_after INTEGER, 
    note TEXT, 
    admin_id VARCHAR(64) COLLATE utf8mb4_bin, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_stock_movements PRIMARY KEY (id), 
    CONSTRAINT fk_stock_movements_admin_id_users_user_id FOREIGN KEY(admin_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_stock_movements_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_stock_movements_product_id_variant_id_produ_3a401ac45048 FOREIGN KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON DELETE RESTRICT, 
    CONSTRAINT fk_stock_movements_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_stock_movements_reservation_id_stock_reservations_id FOREIGN KEY(reservation_id) REFERENCES stock_reservations (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE INDEX ix_stock_movements_order_id ON stock_movements (order_id);

CREATE INDEX ix_stock_movements_product_date ON stock_movements (product_id, created_at, id);

CREATE TABLE product_review_images (
    review_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    sort_order INTEGER NOT NULL, 
    image_url TEXT NOT NULL, 
    CONSTRAINT pk_product_review_images PRIMARY KEY (review_id, sort_order), 
    CONSTRAINT fk_product_review_images_review_id_product_reviews_id FOREIGN KEY(review_id) REFERENCES product_reviews (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

INSERT INTO alembic_version (version_num) VALUES ('20261106_0001');

-- Running upgrade 20261106_0001 -> 20261106_0002

-- MySQL 5.7 validation guards. For populated targets, pause writers and run

-- python -m mysql.check_integrity --preflight-only BEFORE applying this SQL.

-- Stop on the first error. Do not use mysql --force. Requires TRIGGER privileges.

DELIMITER $$

CREATE TRIGGER `bi_articles_mysql57_guard` BEFORE INSERT ON `articles`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_articles_status failed';
  END IF;
  IF (NEW.`view_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_articles_views failed';
  END IF;
END$$

CREATE TRIGGER `bu_articles_mysql57_guard` BEFORE UPDATE ON `articles`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_articles_status failed';
  END IF;
  IF (NEW.`view_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_articles_views failed';
  END IF;
END$$

CREATE TRIGGER `bi_banners_mysql57_guard` BEFORE INSERT ON `banners`
FOR EACH ROW
BEGIN
  IF (NEW.`link_type` IN ('internal','product','category','shop_now','flash_sale','article','external','none')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_link_type failed';
  END IF;
  IF (NEW.`target_device` IN ('desktop','mobile','all')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_target_device failed';
  END IF;
  IF (NEW.`start_at` IS NULL OR NEW.`end_at` IS NULL OR NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_window failed';
  END IF;
END$$

CREATE TRIGGER `bu_banners_mysql57_guard` BEFORE UPDATE ON `banners`
FOR EACH ROW
BEGIN
  IF (NEW.`link_type` IN ('internal','product','category','shop_now','flash_sale','article','external','none')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_link_type failed';
  END IF;
  IF (NEW.`target_device` IN ('desktop','mobile','all')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_target_device failed';
  END IF;
  IF (NEW.`start_at` IS NULL OR NEW.`end_at` IS NULL OR NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_window failed';
  END IF;
END$$

CREATE TRIGGER `bi_cart_items_mysql57_guard` BEFORE INSERT ON `cart_items`
FOR EACH ROW
BEGIN
  IF (NEW.`lens_variant_id` IS NULL OR NEW.`lens_product_id` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cart_items_lens_variant_owner failed';
  END IF;
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cart_items_quantity failed';
  END IF;
END$$

CREATE TRIGGER `bu_cart_items_mysql57_guard` BEFORE UPDATE ON `cart_items`
FOR EACH ROW
BEGIN
  IF (NEW.`lens_variant_id` IS NULL OR NEW.`lens_product_id` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cart_items_lens_variant_owner failed';
  END IF;
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cart_items_quantity failed';
  END IF;
END$$

CREATE TRIGGER `bi_categories_mysql57_guard` BEFORE INSERT ON `categories`
FOR EACH ROW
BEGIN
  IF (NEW.`level` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_categories_level_nonnegative failed';
  END IF;
  IF (NEW.`parent_id` IS NULL OR NEW.`parent_id` <> NEW.`id`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_categories_not_own_parent failed';
  END IF;
END$$

CREATE TRIGGER `bu_categories_mysql57_guard` BEFORE UPDATE ON `categories`
FOR EACH ROW
BEGIN
  IF (NEW.`level` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_categories_level_nonnegative failed';
  END IF;
  IF (NEW.`parent_id` IS NULL OR NEW.`parent_id` <> NEW.`id`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_categories_not_own_parent failed';
  END IF;
END$$

CREATE TRIGGER `bi_cms_pages_mysql57_guard` BEFORE INSERT ON `cms_pages`
FOR EACH ROW
BEGIN
  IF (NEW.`page_type` IN ('about','privacy_policy','terms_conditions','refund_policy','shipping_policy','custom')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_page_type failed';
  END IF;
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_status failed';
  END IF;
  IF (NEW.`version` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_version failed';
  END IF;
END$$

CREATE TRIGGER `bu_cms_pages_mysql57_guard` BEFORE UPDATE ON `cms_pages`
FOR EACH ROW
BEGIN
  IF (NEW.`page_type` IN ('about','privacy_policy','terms_conditions','refund_policy','shipping_policy','custom')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_page_type failed';
  END IF;
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_status failed';
  END IF;
  IF (NEW.`version` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_version failed';
  END IF;
END$$

CREATE TRIGGER `bi_contact_messages_mysql57_guard` BEFORE INSERT ON `contact_messages`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('new','read','replied')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_contact_messages_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_contact_messages_mysql57_guard` BEFORE UPDATE ON `contact_messages`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('new','read','replied')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_contact_messages_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_contact_settings_mysql57_guard` BEFORE INSERT ON `contact_settings`
FOR EACH ROW
BEGIN
  IF (NEW.`singleton_key` = 1) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_contact_settings_singleton failed';
  END IF;
END$$

CREATE TRIGGER `bu_contact_settings_mysql57_guard` BEFORE UPDATE ON `contact_settings`
FOR EACH ROW
BEGIN
  IF (NEW.`singleton_key` = 1) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_contact_settings_singleton failed';
  END IF;
END$$

CREATE TRIGGER `bi_flash_sale_categories_mysql57_guard` BEFORE INSERT ON `flash_sale_categories`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_value` >= 0 AND NEW.`quota_per_product` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_amounts failed';
  END IF;
  IF (NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_percentage failed';
  END IF;
  IF (NEW.`discount_type` IN ('percent','nominal','fixed_price')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_type failed';
  END IF;
END$$

CREATE TRIGGER `bu_flash_sale_categories_mysql57_guard` BEFORE UPDATE ON `flash_sale_categories`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_value` >= 0 AND NEW.`quota_per_product` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_amounts failed';
  END IF;
  IF (NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_percentage failed';
  END IF;
  IF (NEW.`discount_type` IN ('percent','nominal','fixed_price')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_type failed';
  END IF;
END$$

CREATE TRIGGER `bi_flash_sale_items_mysql57_guard` BEFORE INSERT ON `flash_sale_items`
FOR EACH ROW
BEGIN
  IF (NEW.`flash_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_items_price failed';
  END IF;
  IF (NEW.`quota` >= 0 AND NEW.`sold` >= 0 AND NEW.`reserved` >= 0 AND NEW.`sold` + NEW.`reserved` <= NEW.`quota`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_items_quota failed';
  END IF;
END$$

CREATE TRIGGER `bu_flash_sale_items_mysql57_guard` BEFORE UPDATE ON `flash_sale_items`
FOR EACH ROW
BEGIN
  IF (NEW.`flash_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_items_price failed';
  END IF;
  IF (NEW.`quota` >= 0 AND NEW.`sold` >= 0 AND NEW.`reserved` >= 0 AND NEW.`sold` + NEW.`reserved` <= NEW.`quota`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_items_quota failed';
  END IF;
END$$

CREATE TRIGGER `bi_flash_sale_reservations_mysql57_guard` BEFORE INSERT ON `flash_sale_reservations`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_reservations_quantity failed';
  END IF;
  IF (NEW.`status` IN ('active','confirmed','expired','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_reservations_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_flash_sale_reservations_mysql57_guard` BEFORE UPDATE ON `flash_sale_reservations`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_reservations_quantity failed';
  END IF;
  IF (NEW.`status` IN ('active','confirmed','expired','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_reservations_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_flash_sales_mysql57_guard` BEFORE INSERT ON `flash_sales`
FOR EACH ROW
BEGIN
  IF (NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sales_window failed';
  END IF;
END$$

CREATE TRIGGER `bu_flash_sales_mysql57_guard` BEFORE UPDATE ON `flash_sales`
FOR EACH ROW
BEGIN
  IF (NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sales_window failed';
  END IF;
END$$

CREATE TRIGGER `bi_game_scores_mysql57_guard` BEFORE INSERT ON `game_scores`
FOR EACH ROW
BEGIN
  IF (NEW.`score` >= 0 AND NEW.`points_awarded` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_game_scores_scores failed';
  END IF;
END$$

CREATE TRIGGER `bu_game_scores_mysql57_guard` BEFORE UPDATE ON `game_scores`
FOR EACH ROW
BEGIN
  IF (NEW.`score` >= 0 AND NEW.`points_awarded` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_game_scores_scores failed';
  END IF;
END$$

CREATE TRIGGER `bi_games_mysql57_guard` BEFORE INSERT ON `games`
FOR EACH ROW
BEGIN
  IF (NEW.`max_points` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_games_max_points failed';
  END IF;
END$$

CREATE TRIGGER `bu_games_mysql57_guard` BEFORE UPDATE ON `games`
FOR EACH ROW
BEGIN
  IF (NEW.`max_points` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_games_max_points failed';
  END IF;
END$$

CREATE TRIGGER `bi_integration_webhook_events_mysql57_guard` BEFORE INSERT ON `integration_webhook_events`
FOR EACH ROW
BEGIN
  IF (NEW.`attempts` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_integration_webhook_events_attempts failed';
  END IF;
  IF (NEW.`status` IN ('received','processed','failed','ignored')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_integration_webhook_events_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_integration_webhook_events_mysql57_guard` BEFORE UPDATE ON `integration_webhook_events`
FOR EACH ROW
BEGIN
  IF (NEW.`attempts` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_integration_webhook_events_attempts failed';
  END IF;
  IF (NEW.`status` IN ('received','processed','failed','ignored')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_integration_webhook_events_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_lens_indexes_mysql57_guard` BEFORE INSERT ON `lens_indexes`
FOR EACH ROW
BEGIN
  IF (NEW.`additional_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_lens_indexes_price failed';
  END IF;
END$$

CREATE TRIGGER `bu_lens_indexes_mysql57_guard` BEFORE UPDATE ON `lens_indexes`
FOR EACH ROW
BEGIN
  IF (NEW.`additional_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_lens_indexes_price failed';
  END IF;
END$$

CREATE TRIGGER `bi_migration_issues_mysql57_guard` BEFORE INSERT ON `migration_issues`
FOR EACH ROW
BEGIN
  IF (NEW.`severity` IN ('info','warning','error')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_issues_severity failed';
  END IF;
END$$

CREATE TRIGGER `bu_migration_issues_mysql57_guard` BEFORE UPDATE ON `migration_issues`
FOR EACH ROW
BEGIN
  IF (NEW.`severity` IN ('info','warning','error')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_issues_severity failed';
  END IF;
END$$

CREATE TRIGGER `bi_migration_records_mysql57_guard` BEFORE INSERT ON `migration_records`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('planned','imported','verified','rejected')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_records_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_migration_records_mysql57_guard` BEFORE UPDATE ON `migration_records`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('planned','imported','verified','rejected')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_records_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_migration_runs_mysql57_guard` BEFORE INSERT ON `migration_runs`
FOR EACH ROW
BEGIN
  IF (NEW.`source_count` >= 0 AND NEW.`migrated_count` >= 0 AND NEW.`rejected_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_runs_counts failed';
  END IF;
  IF (NEW.`status` IN ('planned','running','validated','failed','completed')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_runs_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_migration_runs_mysql57_guard` BEFORE UPDATE ON `migration_runs`
FOR EACH ROW
BEGIN
  IF (NEW.`source_count` >= 0 AND NEW.`migrated_count` >= 0 AND NEW.`rejected_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_runs_counts failed';
  END IF;
  IF (NEW.`status` IN ('planned','running','validated','failed','completed')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_runs_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_newsletter_campaigns_mysql57_guard` BEFORE INSERT ON `newsletter_campaigns`
FOR EACH ROW
BEGIN
  IF (NEW.`sent_count` >= 0 AND NEW.`failed_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_newsletter_campaigns_counts failed';
  END IF;
END$$

CREATE TRIGGER `bu_newsletter_campaigns_mysql57_guard` BEFORE UPDATE ON `newsletter_campaigns`
FOR EACH ROW
BEGIN
  IF (NEW.`sent_count` >= 0 AND NEW.`failed_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_newsletter_campaigns_counts failed';
  END IF;
END$$

CREATE TRIGGER `bi_order_item_components_mysql57_guard` BEFORE INSERT ON `order_item_components`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0 AND NEW.`index_surcharge` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_item_components_amounts failed';
  END IF;
  IF (NEW.`component_type` IN ('primary','lens')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_item_components_type failed';
  END IF;
END$$

CREATE TRIGGER `bu_order_item_components_mysql57_guard` BEFORE UPDATE ON `order_item_components`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0 AND NEW.`index_surcharge` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_item_components_amounts failed';
  END IF;
  IF (NEW.`component_type` IN ('primary','lens')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_item_components_type failed';
  END IF;
END$$

CREATE TRIGGER `bi_order_items_mysql57_guard` BEFORE INSERT ON `order_items`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_items_amounts failed';
  END IF;
END$$

CREATE TRIGGER `bu_order_items_mysql57_guard` BEFORE UPDATE ON `order_items`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_items_amounts failed';
  END IF;
END$$

CREATE TRIGGER `bi_order_reviews_mysql57_guard` BEFORE INSERT ON `order_reviews`
FOR EACH ROW
BEGIN
  IF (NEW.`rating` BETWEEN 1 AND 5) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_reviews_rating failed';
  END IF;
  IF (NEW.`status` IN ('pending','approved','rejected','hidden')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_reviews_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_order_reviews_mysql57_guard` BEFORE UPDATE ON `order_reviews`
FOR EACH ROW
BEGIN
  IF (NEW.`rating` BETWEEN 1 AND 5) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_reviews_rating failed';
  END IF;
  IF (NEW.`status` IN ('pending','approved','rejected','hidden')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_reviews_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_orders_mysql57_guard` BEFORE INSERT ON `orders`
FOR EACH ROW
BEGIN
  IF (NEW.`points_used` >= 0 AND NEW.`points_discount` >= 0 AND NEW.`roulette_discount` >= 0 AND NEW.`shipping_cost` >= 0 AND NEW.`total` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_amounts failed';
  END IF;
  IF (NEW.`subtotal` >= 0 AND NEW.`discount` >= 0 AND NEW.`flash_sale_discount` >= 0 AND NEW.`voucher_discount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_discount_amounts failed';
  END IF;
  IF (NEW.`payment_status` IN ('pending','paid','failed','expired','cancelled','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_payment_status failed';
  END IF;
  IF (NEW.`shipment_status` IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_shipment_status failed';
  END IF;
  IF (NEW.`status` IN ('pending_payment','paid','processing','shipped','completed','cancelled','expired','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_orders_mysql57_guard` BEFORE UPDATE ON `orders`
FOR EACH ROW
BEGIN
  IF (NEW.`points_used` >= 0 AND NEW.`points_discount` >= 0 AND NEW.`roulette_discount` >= 0 AND NEW.`shipping_cost` >= 0 AND NEW.`total` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_amounts failed';
  END IF;
  IF (NEW.`subtotal` >= 0 AND NEW.`discount` >= 0 AND NEW.`flash_sale_discount` >= 0 AND NEW.`voucher_discount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_discount_amounts failed';
  END IF;
  IF (NEW.`payment_status` IN ('pending','paid','failed','expired','cancelled','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_payment_status failed';
  END IF;
  IF (NEW.`shipment_status` IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_shipment_status failed';
  END IF;
  IF (NEW.`status` IN ('pending_payment','paid','processing','shipped','completed','cancelled','expired','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_payments_mysql57_guard` BEFORE INSERT ON `payments`
FOR EACH ROW
BEGIN
  IF (NEW.`amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_payments_amount failed';
  END IF;
  IF (NEW.`status` IN ('pending','paid','failed','expired','cancelled','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_payments_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_payments_mysql57_guard` BEFORE UPDATE ON `payments`
FOR EACH ROW
BEGIN
  IF (NEW.`amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_payments_amount failed';
  END IF;
  IF (NEW.`status` IN ('pending','paid','failed','expired','cancelled','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_payments_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_point_logs_mysql57_guard` BEFORE INSERT ON `point_logs`
FOR EACH ROW
BEGIN
  IF (NEW.`balance_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_point_logs_balance failed';
  END IF;
END$$

CREATE TRIGGER `bu_point_logs_mysql57_guard` BEFORE UPDATE ON `point_logs`
FOR EACH ROW
BEGIN
  IF (NEW.`balance_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_point_logs_balance failed';
  END IF;
END$$

CREATE TRIGGER `bi_prescription_eyes_mysql57_guard` BEFORE INSERT ON `prescription_eyes`
FOR EACH ROW
BEGIN
  IF (NEW.`axis` IS NULL OR NEW.`axis` BETWEEN 0 AND 180) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescription_eyes_axis failed';
  END IF;
  IF (NEW.`eye` IN ('right','left')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescription_eyes_eye failed';
  END IF;
END$$

CREATE TRIGGER `bu_prescription_eyes_mysql57_guard` BEFORE UPDATE ON `prescription_eyes`
FOR EACH ROW
BEGIN
  IF (NEW.`axis` IS NULL OR NEW.`axis` BETWEEN 0 AND 180) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescription_eyes_axis failed';
  END IF;
  IF (NEW.`eye` IN ('right','left')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescription_eyes_eye failed';
  END IF;
END$$

CREATE TRIGGER `bi_prescriptions_mysql57_guard` BEFORE INSERT ON `prescriptions`
FOR EACH ROW
BEGIN
  IF (NEW.`pd_left` IS NULL OR NEW.`pd_left` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_left failed';
  END IF;
  IF (NEW.`pd_total` IS NULL OR (NEW.`pd_right` IS NULL AND NEW.`pd_left` IS NULL)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_mode failed';
  END IF;
  IF ((NEW.`pd_right` IS NULL AND NEW.`pd_left` IS NULL) OR (NEW.`pd_right` IS NOT NULL AND NEW.`pd_left` IS NOT NULL)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_pair failed';
  END IF;
  IF (NEW.`pd_right` IS NULL OR NEW.`pd_right` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_right failed';
  END IF;
  IF (NEW.`pd_total` IS NULL OR NEW.`pd_total` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_total failed';
  END IF;
END$$

CREATE TRIGGER `bu_prescriptions_mysql57_guard` BEFORE UPDATE ON `prescriptions`
FOR EACH ROW
BEGIN
  IF (NEW.`pd_left` IS NULL OR NEW.`pd_left` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_left failed';
  END IF;
  IF (NEW.`pd_total` IS NULL OR (NEW.`pd_right` IS NULL AND NEW.`pd_left` IS NULL)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_mode failed';
  END IF;
  IF ((NEW.`pd_right` IS NULL AND NEW.`pd_left` IS NULL) OR (NEW.`pd_right` IS NOT NULL AND NEW.`pd_left` IS NOT NULL)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_pair failed';
  END IF;
  IF (NEW.`pd_right` IS NULL OR NEW.`pd_right` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_right failed';
  END IF;
  IF (NEW.`pd_total` IS NULL OR NEW.`pd_total` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_total failed';
  END IF;
END$$

CREATE TRIGGER `bi_product_knowledge_bullets_mysql57_guard` BEFORE INSERT ON `product_knowledge_bullets`
FOR EACH ROW
BEGIN
  IF (NEW.`kind` IN ('pro','con')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledge_bullets_kind failed';
  END IF;
END$$

CREATE TRIGGER `bu_product_knowledge_bullets_mysql57_guard` BEFORE UPDATE ON `product_knowledge_bullets`
FOR EACH ROW
BEGIN
  IF (NEW.`kind` IN ('pro','con')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledge_bullets_kind failed';
  END IF;
END$$

CREATE TRIGGER `bi_product_knowledges_mysql57_guard` BEFORE INSERT ON `product_knowledges`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledges_status failed';
  END IF;
  IF (NEW.`knowledge_type` IN ('frame_shape','material','lens_type','lens_index','buying_guide')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledges_type failed';
  END IF;
END$$

CREATE TRIGGER `bu_product_knowledges_mysql57_guard` BEFORE UPDATE ON `product_knowledges`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledges_status failed';
  END IF;
  IF (NEW.`knowledge_type` IN ('frame_shape','material','lens_type','lens_index','buying_guide')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledges_type failed';
  END IF;
END$$

CREATE TRIGGER `bi_product_reviews_mysql57_guard` BEFORE INSERT ON `product_reviews`
FOR EACH ROW
BEGIN
  IF ((NEW.`order_item_id` IS NULL AND NEW.`order_component_id` IS NULL) OR NEW.`order_id` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_line_requires_order failed';
  END IF;
  IF (NEW.`order_item_id` IS NULL OR NEW.`order_component_id` IS NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_one_purchase_line failed';
  END IF;
  IF (NEW.`rating` BETWEEN 1 AND 5) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_rating failed';
  END IF;
  IF (NEW.`status` IN ('pending','approved','rejected','hidden')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_status failed';
  END IF;
  IF (NEW.`verified_purchase` = 0 OR (NEW.`order_id` IS NOT NULL AND (NEW.`order_item_id` IS NOT NULL OR NEW.`order_component_id` IS NOT NULL))) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_verified_purchase failed';
  END IF;
END$$

CREATE TRIGGER `bu_product_reviews_mysql57_guard` BEFORE UPDATE ON `product_reviews`
FOR EACH ROW
BEGIN
  IF ((NEW.`order_item_id` IS NULL AND NEW.`order_component_id` IS NULL) OR NEW.`order_id` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_line_requires_order failed';
  END IF;
  IF (NEW.`order_item_id` IS NULL OR NEW.`order_component_id` IS NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_one_purchase_line failed';
  END IF;
  IF (NEW.`rating` BETWEEN 1 AND 5) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_rating failed';
  END IF;
  IF (NEW.`status` IN ('pending','approved','rejected','hidden')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_status failed';
  END IF;
  IF (NEW.`verified_purchase` = 0 OR (NEW.`order_id` IS NOT NULL AND (NEW.`order_item_id` IS NOT NULL OR NEW.`order_component_id` IS NOT NULL))) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_verified_purchase failed';
  END IF;
END$$

CREATE TRIGGER `bi_product_variants_mysql57_guard` BEFORE INSERT ON `product_variants`
FOR EACH ROW
BEGIN
  IF (NEW.`stock` >= 0 AND NEW.`reserved` >= 0 AND NEW.`reserved` <= NEW.`stock`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_variants_inventory failed';
  END IF;
  IF (NEW.`price_override` IS NULL OR NEW.`price_override` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_variants_price failed';
  END IF;
END$$

CREATE TRIGGER `bu_product_variants_mysql57_guard` BEFORE UPDATE ON `product_variants`
FOR EACH ROW
BEGIN
  IF (NEW.`stock` >= 0 AND NEW.`reserved` >= 0 AND NEW.`reserved` <= NEW.`stock`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_variants_inventory failed';
  END IF;
  IF (NEW.`price_override` IS NULL OR NEW.`price_override` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_variants_price failed';
  END IF;
END$$

CREATE TRIGGER `bi_products_mysql57_guard` BEFORE INSERT ON `products`
FOR EACH ROW
BEGIN
  IF (NEW.`rating_avg` BETWEEN 0 AND 5 AND NEW.`rating_count` >= 0 AND NEW.`sold_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_counters failed';
  END IF;
  IF (NEW.`weight_gram` >= 0 AND NEW.`min_stock_alert` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_inventory_values failed';
  END IF;
  IF (NEW.`flash_sale_price` IS NULL OR NEW.`flash_sale_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_legacy_flash_nonnegative failed';
  END IF;
  IF (NEW.`price` >= 0 AND (NEW.`discount_price` IS NULL OR NEW.`discount_price` >= 0)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_prices_nonnegative failed';
  END IF;
  IF (NEW.`product_type` IN ('frame','lens','package')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_type failed';
  END IF;
END$$

CREATE TRIGGER `bu_products_mysql57_guard` BEFORE UPDATE ON `products`
FOR EACH ROW
BEGIN
  IF (NEW.`rating_avg` BETWEEN 0 AND 5 AND NEW.`rating_count` >= 0 AND NEW.`sold_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_counters failed';
  END IF;
  IF (NEW.`weight_gram` >= 0 AND NEW.`min_stock_alert` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_inventory_values failed';
  END IF;
  IF (NEW.`flash_sale_price` IS NULL OR NEW.`flash_sale_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_legacy_flash_nonnegative failed';
  END IF;
  IF (NEW.`price` >= 0 AND (NEW.`discount_price` IS NULL OR NEW.`discount_price` >= 0)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_prices_nonnegative failed';
  END IF;
  IF (NEW.`product_type` IN ('frame','lens','package')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_type failed';
  END IF;
END$$

CREATE TRIGGER `bi_roulette_redemptions_mysql57_guard` BEFORE INSERT ON `roulette_redemptions`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_redemptions_discount failed';
  END IF;
  IF (NEW.`status` IN ('reserved','redeemed','released')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_redemptions_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_roulette_redemptions_mysql57_guard` BEFORE UPDATE ON `roulette_redemptions`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_redemptions_discount failed';
  END IF;
  IF (NEW.`status` IN ('reserved','redeemed','released')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_redemptions_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_roulette_rewards_mysql57_guard` BEFORE INSERT ON `roulette_rewards`
FOR EACH ROW
BEGIN
  IF (NEW.`value` >= 0 AND NEW.`probability` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_rewards_amounts failed';
  END IF;
  IF (NEW.`type` IN ('points','voucher','free_shipping','discount','nothing')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_rewards_type failed';
  END IF;
END$$

CREATE TRIGGER `bu_roulette_rewards_mysql57_guard` BEFORE UPDATE ON `roulette_rewards`
FOR EACH ROW
BEGIN
  IF (NEW.`value` >= 0 AND NEW.`probability` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_rewards_amounts failed';
  END IF;
  IF (NEW.`type` IN ('points','voucher','free_shipping','discount','nothing')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_rewards_type failed';
  END IF;
END$$

CREATE TRIGGER `bi_roulette_spins_mysql57_guard` BEFORE INSERT ON `roulette_spins`
FOR EACH ROW
BEGIN
  IF (NEW.`reward_value` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_spins_value failed';
  END IF;
END$$

CREATE TRIGGER `bu_roulette_spins_mysql57_guard` BEFORE UPDATE ON `roulette_spins`
FOR EACH ROW
BEGIN
  IF (NEW.`reward_value` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_spins_value failed';
  END IF;
END$$

CREATE TRIGGER `bi_shipments_mysql57_guard` BEFORE INSERT ON `shipments`
FOR EACH ROW
BEGIN
  IF (NEW.`cost` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipments_cost failed';
  END IF;
  IF (NEW.`status` IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipments_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_shipments_mysql57_guard` BEFORE UPDATE ON `shipments`
FOR EACH ROW
BEGIN
  IF (NEW.`cost` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipments_cost failed';
  END IF;
  IF (NEW.`status` IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipments_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_shipping_quotes_mysql57_guard` BEFORE INSERT ON `shipping_quotes`
FOR EACH ROW
BEGIN
  IF (NEW.`weight_gram` > 0 AND NEW.`cost` >= 0 AND NEW.`insurance_cost` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipping_quotes_amounts failed';
  END IF;
END$$

CREATE TRIGGER `bu_shipping_quotes_mysql57_guard` BEFORE UPDATE ON `shipping_quotes`
FOR EACH ROW
BEGIN
  IF (NEW.`weight_gram` > 0 AND NEW.`cost` >= 0 AND NEW.`insurance_cost` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipping_quotes_amounts failed';
  END IF;
END$$

CREATE TRIGGER `bi_stock_movements_mysql57_guard` BEFORE INSERT ON `stock_movements`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_quantity failed';
  END IF;
  IF (NEW.`reserved_after` IS NULL OR NEW.`reserved_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_reserved_after failed';
  END IF;
  IF (NEW.`stock_after` IS NULL OR NEW.`stock_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_stock_after failed';
  END IF;
END$$

CREATE TRIGGER `bu_stock_movements_mysql57_guard` BEFORE UPDATE ON `stock_movements`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_quantity failed';
  END IF;
  IF (NEW.`reserved_after` IS NULL OR NEW.`reserved_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_reserved_after failed';
  END IF;
  IF (NEW.`stock_after` IS NULL OR NEW.`stock_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_stock_after failed';
  END IF;
END$$

CREATE TRIGGER `bi_stock_reservations_mysql57_guard` BEFORE INSERT ON `stock_reservations`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_reservations_quantity failed';
  END IF;
  IF (NEW.`status` IN ('active','confirmed','expired','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_reservations_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_stock_reservations_mysql57_guard` BEFORE UPDATE ON `stock_reservations`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_reservations_quantity failed';
  END IF;
  IF (NEW.`status` IN ('active','confirmed','expired','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_reservations_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_uploads_mysql57_guard` BEFORE INSERT ON `uploads`
FOR EACH ROW
BEGIN
  IF (NEW.`size` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_uploads_size failed';
  END IF;
  IF (NEW.`visibility` IN ('public','private')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_uploads_visibility failed';
  END IF;
END$$

CREATE TRIGGER `bu_uploads_mysql57_guard` BEFORE UPDATE ON `uploads`
FOR EACH ROW
BEGIN
  IF (NEW.`size` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_uploads_size failed';
  END IF;
  IF (NEW.`visibility` IN ('public','private')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_uploads_visibility failed';
  END IF;
END$$

CREATE TRIGGER `bi_users_mysql57_guard` BEFORE INSERT ON `users`
FOR EACH ROW
BEGIN
  IF (NEW.`pin_failed_attempts` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_pin_attempts_nonnegative failed';
  END IF;
  IF (NEW.`points_balance` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_points_nonnegative failed';
  END IF;
  IF (NEW.`role` IN ('customer','staff','admin','super_admin')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_role failed';
  END IF;
END$$

CREATE TRIGGER `bu_users_mysql57_guard` BEFORE UPDATE ON `users`
FOR EACH ROW
BEGIN
  IF (NEW.`pin_failed_attempts` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_pin_attempts_nonnegative failed';
  END IF;
  IF (NEW.`points_balance` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_points_nonnegative failed';
  END IF;
  IF (NEW.`role` IN ('customer','staff','admin','super_admin')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_role failed';
  END IF;
END$$

CREATE TRIGGER `bi_virtual_try_on_assets_mysql57_guard` BEFORE INSERT ON `virtual_try_on_assets`
FOR EACH ROW
BEGIN
  IF (NEW.`asset_type` IN ('image','glb','gltf')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_asset_type failed';
  END IF;
  IF (NEW.`scale` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_scale failed';
  END IF;
  IF (NEW.`upload_id` IS NOT NULL OR NEW.`source_url` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_source failed';
  END IF;
  IF (NEW.`status` IN ('draft','published','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_virtual_try_on_assets_mysql57_guard` BEFORE UPDATE ON `virtual_try_on_assets`
FOR EACH ROW
BEGIN
  IF (NEW.`asset_type` IN ('image','glb','gltf')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_asset_type failed';
  END IF;
  IF (NEW.`scale` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_scale failed';
  END IF;
  IF (NEW.`upload_id` IS NOT NULL OR NEW.`source_url` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_source failed';
  END IF;
  IF (NEW.`status` IN ('draft','published','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_voucher_redemptions_mysql57_guard` BEFORE INSERT ON `voucher_redemptions`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_voucher_redemptions_amount failed';
  END IF;
  IF (NEW.`status` IN ('reserved','redeemed','released')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_voucher_redemptions_status failed';
  END IF;
END$$

CREATE TRIGGER `bu_voucher_redemptions_mysql57_guard` BEFORE UPDATE ON `voucher_redemptions`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_voucher_redemptions_amount failed';
  END IF;
  IF (NEW.`status` IN ('reserved','redeemed','released')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_voucher_redemptions_status failed';
  END IF;
END$$

CREATE TRIGGER `bi_vouchers_mysql57_guard` BEFORE INSERT ON `vouchers`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_value` >= 0 AND NEW.`min_purchase` >= 0 AND (NEW.`max_discount` IS NULL OR NEW.`max_discount` >= 0)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_amounts failed';
  END IF;
  IF (NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_percentage failed';
  END IF;
  IF (NEW.`quota` >= 0 AND NEW.`used_count` >= 0 AND NEW.`used_count` <= NEW.`quota` AND NEW.`quota_per_user` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_quotas failed';
  END IF;
  IF (NEW.`discount_type` IN ('percent','nominal','free_shipping')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_type failed';
  END IF;
  IF (NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_window failed';
  END IF;
END$$

CREATE TRIGGER `bu_vouchers_mysql57_guard` BEFORE UPDATE ON `vouchers`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_value` >= 0 AND NEW.`min_purchase` >= 0 AND (NEW.`max_discount` IS NULL OR NEW.`max_discount` >= 0)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_amounts failed';
  END IF;
  IF (NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_percentage failed';
  END IF;
  IF (NEW.`quota` >= 0 AND NEW.`used_count` >= 0 AND NEW.`used_count` <= NEW.`quota` AND NEW.`quota_per_user` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_quotas failed';
  END IF;
  IF (NEW.`discount_type` IN ('percent','nominal','free_shipping')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_type failed';
  END IF;
  IF (NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_window failed';
  END IF;
END$$

CREATE TRIGGER `bi_whatsapp_settings_mysql57_guard` BEFORE INSERT ON `whatsapp_settings`
FOR EACH ROW
BEGIN
  IF (NEW.`id` = 1) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_whatsapp_settings_singleton failed';
  END IF;
END$$

CREATE TRIGGER `bu_whatsapp_settings_mysql57_guard` BEFORE UPDATE ON `whatsapp_settings`
FOR EACH ROW
BEGIN
  IF (NEW.`id` = 1) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_whatsapp_settings_singleton failed';
  END IF;
END$$

DELIMITER ;

UPDATE alembic_version SET version_num='20261106_0002' WHERE alembic_version.version_num = '20261106_0001';

SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;

