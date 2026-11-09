SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

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

