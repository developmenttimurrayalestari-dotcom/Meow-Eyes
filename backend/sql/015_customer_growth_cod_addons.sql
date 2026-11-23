SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

-- Running upgrade 20261117_0014 -> 20261120_0015

ALTER TABLE `users` ADD COLUMN email_verified_at DATETIME(6);

ALTER TABLE `users` ADD COLUMN referral_code VARCHAR(32);

ALTER TABLE `products` ADD COLUMN sale_role VARCHAR(16) NOT NULL DEFAULT 'main';

ALTER TABLE `addresses` ADD COLUMN latitude NUMERIC(10, 7);

ALTER TABLE `addresses` ADD COLUMN longitude NUMERIC(10, 7);

ALTER TABLE `order_addresses` ADD COLUMN latitude NUMERIC(10, 7);

ALTER TABLE `order_addresses` ADD COLUMN longitude NUMERIC(10, 7);

ALTER TABLE `orders` ADD COLUMN payment_mode VARCHAR(16) NOT NULL DEFAULT 'online';

ALTER TABLE `vouchers` ADD COLUMN audience VARCHAR(16) NOT NULL DEFAULT 'general';

ALTER TABLE users ADD CONSTRAINT uq_users_referral_code UNIQUE (referral_code);

CREATE TABLE email_verifications (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    token_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    expires_at DATETIME(6) NOT NULL, 
    used_at DATETIME(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_email_verifications PRIMARY KEY (id), 
    CONSTRAINT fk_email_verifications_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
    CONSTRAINT uq_email_verifications_token_hash UNIQUE (token_hash)
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE customer_referrals (
    referee_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    referrer_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    rule_snapshot JSON NOT NULL, 
    rewarded_at DATETIME(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_customer_referrals PRIMARY KEY (referee_id), 
    CONSTRAINT fk_customer_referrals_referee_id_users_user_id FOREIGN KEY(referee_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_customer_referrals_referrer_id_users_user_id FOREIGN KEY(referrer_id) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE customer_growth_rewards (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    event_key VARCHAR(191) NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    snapshot JSON NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'pending', 
    granted_at DATETIME(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_customer_growth_rewards PRIMARY KEY (id), 
    CONSTRAINT uq_customer_growth_rewards_event_key UNIQUE (event_key), 
    CONSTRAINT fk_customer_growth_rewards_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE customer_voucher_grants (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    voucher_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    source VARCHAR(32) NOT NULL, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_customer_voucher_grants PRIMARY KEY (id), 
    CONSTRAINT uq_customer_voucher_grants_user_id_voucher_id UNIQUE (user_id, voucher_id), 
    CONSTRAINT fk_customer_voucher_grants_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_customer_voucher_grants_voucher_id_vouchers_id FOREIGN KEY(voucher_id) REFERENCES vouchers (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE daily_checkins (
    user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    day VARCHAR(10) NOT NULL, 
    streak INTEGER NOT NULL, 
    points INTEGER NOT NULL, 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_daily_checkins PRIMARY KEY (user_id, day), 
    CONSTRAINT fk_daily_checkins_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE cart_item_addons (
    cart_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    variant_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    CONSTRAINT pk_cart_item_addons PRIMARY KEY (cart_item_id, product_id), 
    CONSTRAINT fk_cart_item_addons_product_id_variant_id_prod_79b4ad7e2738 FOREIGN KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON DELETE RESTRICT, 
    CONSTRAINT fk_cart_item_addons_cart_item_id_cart_items_id FOREIGN KEY(cart_item_id) REFERENCES cart_items (id) ON DELETE CASCADE, 
    CONSTRAINT fk_cart_item_addons_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE addon_flash_reservations (
    id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    component_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    flash_sale_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    quantity INTEGER NOT NULL, 
    status VARCHAR(16) NOT NULL DEFAULT 'active', 
    expires_at DATETIME(6) NOT NULL, 
    resolved_at DATETIME(6), 
    created_at DATETIME(6) NOT NULL DEFAULT now(6), 
    CONSTRAINT pk_addon_flash_reservations PRIMARY KEY (id), 
    CONSTRAINT uq_addon_flash_reservations_component_id_flash_sale_item_id UNIQUE (component_id, flash_sale_item_id), 
    CONSTRAINT fk_addon_flash_reservations_component_id_order_54baf21467dd FOREIGN KEY(component_id, order_id, product_id) REFERENCES order_item_components (id, order_id, product_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_addon_flash_reservations_flash_sale_item_id_f9dbd13f63bb FOREIGN KEY(flash_sale_item_id, product_id) REFERENCES flash_sale_items (id, product_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_email_verifications_user_date ON email_verifications (user_id, created_at);

CREATE INDEX ix_referrals_referrer ON customer_referrals (referrer_id, created_at);

CREATE INDEX ix_growth_rewards_pending ON customer_growth_rewards (status, user_id);

UPDATE users SET referral_code=CONCAT('ME', UPPER(LEFT(SHA2(user_id,256),24))) WHERE referral_code IS NULL;

DELIMITER $$

DROP TRIGGER IF EXISTS `bi_products_mysql57_guard`$$

CREATE TRIGGER `bi_products_mysql57_guard` BEFORE INSERT ON `products` FOR EACH ROW BEGIN
  IF (NEW.`rating_avg` BETWEEN 0 AND 5 AND NEW.`rating_count` >= 0 AND NEW.`sold_count` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_counters failed'; END IF;
  IF (NEW.`weight_gram` >= 0 AND NEW.`min_stock_alert` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_inventory_values failed'; END IF;
  IF (NEW.`flash_sale_price` IS NULL OR NEW.`flash_sale_price` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_legacy_flash_nonnegative failed'; END IF;
  IF (NEW.`price` >= 0 AND (NEW.`discount_price` IS NULL OR NEW.`discount_price` >= 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_prices_nonnegative failed'; END IF;
  IF (NEW.`sale_role` IN ('main','add_on')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_sale_role failed'; END IF;
  IF (NEW.`product_type` IN ('frame','lens','package','accessories')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_type failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bu_products_mysql57_guard`$$

CREATE TRIGGER `bu_products_mysql57_guard` BEFORE UPDATE ON `products` FOR EACH ROW BEGIN
  IF (NEW.`rating_avg` BETWEEN 0 AND 5 AND NEW.`rating_count` >= 0 AND NEW.`sold_count` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_counters failed'; END IF;
  IF (NEW.`weight_gram` >= 0 AND NEW.`min_stock_alert` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_inventory_values failed'; END IF;
  IF (NEW.`flash_sale_price` IS NULL OR NEW.`flash_sale_price` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_legacy_flash_nonnegative failed'; END IF;
  IF (NEW.`price` >= 0 AND (NEW.`discount_price` IS NULL OR NEW.`discount_price` >= 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_prices_nonnegative failed'; END IF;
  IF (NEW.`sale_role` IN ('main','add_on')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_sale_role failed'; END IF;
  IF (NEW.`product_type` IN ('frame','lens','package','accessories')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_products_type failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bi_addresses_mysql57_guard`$$

CREATE TRIGGER `bi_addresses_mysql57_guard` BEFORE INSERT ON `addresses` FOR EACH ROW BEGIN
  IF ((NEW.`latitude` IS NULL AND NEW.`longitude` IS NULL) OR (NEW.`latitude` IS NOT NULL AND NEW.`longitude` IS NOT NULL AND NEW.`latitude` BETWEEN -90 AND 90 AND NEW.`longitude` BETWEEN -180 AND 180)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_addresses_coordinates failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bu_addresses_mysql57_guard`$$

CREATE TRIGGER `bu_addresses_mysql57_guard` BEFORE UPDATE ON `addresses` FOR EACH ROW BEGIN
  IF ((NEW.`latitude` IS NULL AND NEW.`longitude` IS NULL) OR (NEW.`latitude` IS NOT NULL AND NEW.`longitude` IS NOT NULL AND NEW.`latitude` BETWEEN -90 AND 90 AND NEW.`longitude` BETWEEN -180 AND 180)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_addresses_coordinates failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bi_order_addresses_mysql57_guard`$$

CREATE TRIGGER `bi_order_addresses_mysql57_guard` BEFORE INSERT ON `order_addresses` FOR EACH ROW BEGIN
  IF ((NEW.`latitude` IS NULL AND NEW.`longitude` IS NULL) OR (NEW.`latitude` IS NOT NULL AND NEW.`longitude` IS NOT NULL AND NEW.`latitude` BETWEEN -90 AND 90 AND NEW.`longitude` BETWEEN -180 AND 180)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_order_addresses_coordinates failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bu_order_addresses_mysql57_guard`$$

CREATE TRIGGER `bu_order_addresses_mysql57_guard` BEFORE UPDATE ON `order_addresses` FOR EACH ROW BEGIN
  IF ((NEW.`latitude` IS NULL AND NEW.`longitude` IS NULL) OR (NEW.`latitude` IS NOT NULL AND NEW.`longitude` IS NOT NULL AND NEW.`latitude` BETWEEN -90 AND 90 AND NEW.`longitude` BETWEEN -180 AND 180)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_order_addresses_coordinates failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bi_orders_mysql57_guard`$$

CREATE TRIGGER `bi_orders_mysql57_guard` BEFORE INSERT ON `orders` FOR EACH ROW BEGIN
  IF (NEW.`points_used` >= 0 AND NEW.`points_discount` >= 0 AND NEW.`roulette_discount` >= 0 AND NEW.`shipping_cost` >= 0 AND NEW.`total` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_amounts failed'; END IF;
  IF (NEW.`subtotal` >= 0 AND NEW.`discount` >= 0 AND NEW.`flash_sale_discount` >= 0 AND NEW.`voucher_discount` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_discount_amounts failed'; END IF;
  IF (NEW.`payment_mode` IN ('online','cod')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_payment_mode failed'; END IF;
  IF (NEW.`payment_status` IN ('pending','cod_pending','paid','failed','expired','cancelled','refunded')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_payment_status failed'; END IF;
  IF (NEW.`shipment_status` IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_shipment_status failed'; END IF;
  IF (NEW.`status` IN ('pending_payment','paid','processing','shipped','completed','cancelled','expired','refunded')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_status failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bu_orders_mysql57_guard`$$

CREATE TRIGGER `bu_orders_mysql57_guard` BEFORE UPDATE ON `orders` FOR EACH ROW BEGIN
  IF (NEW.`points_used` >= 0 AND NEW.`points_discount` >= 0 AND NEW.`roulette_discount` >= 0 AND NEW.`shipping_cost` >= 0 AND NEW.`total` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_amounts failed'; END IF;
  IF (NEW.`subtotal` >= 0 AND NEW.`discount` >= 0 AND NEW.`flash_sale_discount` >= 0 AND NEW.`voucher_discount` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_discount_amounts failed'; END IF;
  IF (NEW.`payment_mode` IN ('online','cod')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_payment_mode failed'; END IF;
  IF (NEW.`payment_status` IN ('pending','cod_pending','paid','failed','expired','cancelled','refunded')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_payment_status failed'; END IF;
  IF (NEW.`shipment_status` IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_shipment_status failed'; END IF;
  IF (NEW.`status` IN ('pending_payment','paid','processing','shipped','completed','cancelled','expired','refunded')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_orders_status failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bi_vouchers_mysql57_guard`$$

CREATE TRIGGER `bi_vouchers_mysql57_guard` BEFORE INSERT ON `vouchers` FOR EACH ROW BEGIN
  IF (NEW.`discount_value` >= 0 AND NEW.`min_purchase` >= 0 AND (NEW.`max_discount` IS NULL OR NEW.`max_discount` >= 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_amounts failed'; END IF;
  IF (NEW.`audience` IN ('general','new_member','referral')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_audience failed'; END IF;
  IF (NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_percentage failed'; END IF;
  IF (NEW.`quota` >= 0 AND NEW.`used_count` >= 0 AND NEW.`used_count` <= NEW.`quota` AND NEW.`quota_per_user` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_quotas failed'; END IF;
  IF (NEW.`discount_type` IN ('percent','nominal','free_shipping')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_type failed'; END IF;
  IF (NEW.`end_at` > NEW.`start_at`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_window failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bu_vouchers_mysql57_guard`$$

CREATE TRIGGER `bu_vouchers_mysql57_guard` BEFORE UPDATE ON `vouchers` FOR EACH ROW BEGIN
  IF (NEW.`discount_value` >= 0 AND NEW.`min_purchase` >= 0 AND (NEW.`max_discount` IS NULL OR NEW.`max_discount` >= 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_amounts failed'; END IF;
  IF (NEW.`audience` IN ('general','new_member','referral')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_audience failed'; END IF;
  IF (NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_percentage failed'; END IF;
  IF (NEW.`quota` >= 0 AND NEW.`used_count` >= 0 AND NEW.`used_count` <= NEW.`quota` AND NEW.`quota_per_user` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_quotas failed'; END IF;
  IF (NEW.`discount_type` IN ('percent','nominal','free_shipping')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_type failed'; END IF;
  IF (NEW.`end_at` > NEW.`start_at`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_vouchers_window failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bi_order_item_components_mysql57_guard`$$

CREATE TRIGGER `bi_order_item_components_mysql57_guard` BEFORE INSERT ON `order_item_components` FOR EACH ROW BEGIN
  IF (NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0 AND NEW.`index_surcharge` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_order_item_components_amounts failed'; END IF;
  IF (NEW.`component_type` IN ('primary','lens','add_on')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_order_item_components_type failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bu_order_item_components_mysql57_guard`$$

CREATE TRIGGER `bu_order_item_components_mysql57_guard` BEFORE UPDATE ON `order_item_components` FOR EACH ROW BEGIN
  IF (NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0 AND NEW.`index_surcharge` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_order_item_components_amounts failed'; END IF;
  IF (NEW.`component_type` IN ('primary','lens','add_on')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_order_item_components_type failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bi_customer_referrals_mysql57_guard`$$

CREATE TRIGGER `bi_customer_referrals_mysql57_guard` BEFORE INSERT ON `customer_referrals` FOR EACH ROW BEGIN
  IF (NEW.`referee_id` <> NEW.`referrer_id`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_customer_referrals_not_self failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bu_customer_referrals_mysql57_guard`$$

CREATE TRIGGER `bu_customer_referrals_mysql57_guard` BEFORE UPDATE ON `customer_referrals` FOR EACH ROW BEGIN
  IF (NEW.`referee_id` <> NEW.`referrer_id`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_customer_referrals_not_self failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bi_customer_growth_rewards_mysql57_guard`$$

CREATE TRIGGER `bi_customer_growth_rewards_mysql57_guard` BEFORE INSERT ON `customer_growth_rewards` FOR EACH ROW BEGIN
  IF (NEW.`status` IN ('pending','granted')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_customer_growth_rewards_status failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bu_customer_growth_rewards_mysql57_guard`$$

CREATE TRIGGER `bu_customer_growth_rewards_mysql57_guard` BEFORE UPDATE ON `customer_growth_rewards` FOR EACH ROW BEGIN
  IF (NEW.`status` IN ('pending','granted')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_customer_growth_rewards_status failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bi_daily_checkins_mysql57_guard`$$

CREATE TRIGGER `bi_daily_checkins_mysql57_guard` BEFORE INSERT ON `daily_checkins` FOR EACH ROW BEGIN
  IF (NEW.`streak` > 0 AND NEW.`points` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_daily_checkins_amounts failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bu_daily_checkins_mysql57_guard`$$

CREATE TRIGGER `bu_daily_checkins_mysql57_guard` BEFORE UPDATE ON `daily_checkins` FOR EACH ROW BEGIN
  IF (NEW.`streak` > 0 AND NEW.`points` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_daily_checkins_amounts failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bi_addon_flash_reservations_mysql57_guard`$$

CREATE TRIGGER `bi_addon_flash_reservations_mysql57_guard` BEFORE INSERT ON `addon_flash_reservations` FOR EACH ROW BEGIN
  IF (NEW.`quantity` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_addon_flash_reservations_quantity failed'; END IF;
  IF (NEW.`status` IN ('active','confirmed','expired','cancelled')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_addon_flash_reservations_status failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `bu_addon_flash_reservations_mysql57_guard`$$

CREATE TRIGGER `bu_addon_flash_reservations_mysql57_guard` BEFORE UPDATE ON `addon_flash_reservations` FOR EACH ROW BEGIN
  IF (NEW.`quantity` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_addon_flash_reservations_quantity failed'; END IF;
  IF (NEW.`status` IN ('active','confirmed','expired','cancelled')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_addon_flash_reservations_status failed'; END IF;
END$$

DELIMITER ;

UPDATE alembic_version SET version_num='20261120_0015' WHERE alembic_version.version_num = '20261117_0014';

SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;

