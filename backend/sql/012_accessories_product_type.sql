SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

-- Running upgrade 20261112_0011 -> 20261112_0012

-- Back up first; pause writers while replacing the four MySQL 5.7 guards.

DELIMITER $$

DROP TRIGGER `bi_products_mysql57_guard`$$

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
  IF (NEW.`product_type` IN ('frame','lens','package','accessories')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_type failed';
  END IF;
END$$

DROP TRIGGER `bu_products_mysql57_guard`$$

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
  IF (NEW.`product_type` IN ('frame','lens','package','accessories')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_type failed';
  END IF;
END$$

DROP TRIGGER `bi_categories_mysql57_guard`$$

CREATE TRIGGER `bi_categories_mysql57_guard` BEFORE INSERT ON categories FOR EACH ROW BEGIN
  IF (NEW.group_type IN ('product_type','lens_type','gender','frame_shape','material','collection')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_categories_group_type failed'; END IF;
  IF (NEW.group_type <> 'product_type' OR NEW.code IN ('frame','lens','package','accessories')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_categories_product_kind failed'; END IF;
END$$

DROP TRIGGER `bu_categories_mysql57_guard`$$

CREATE TRIGGER `bu_categories_mysql57_guard` BEFORE UPDATE ON categories FOR EACH ROW BEGIN
  IF (NEW.group_type IN ('product_type','lens_type','gender','frame_shape','material','collection')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_categories_group_type failed'; END IF;
  IF (NEW.group_type <> 'product_type' OR NEW.code IN ('frame','lens','package','accessories')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_categories_product_kind failed'; END IF;
  IF NOT (NEW.group_type <=> OLD.group_type) OR NOT (NEW.code <=> OLD.code) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Master group and code are immutable'; END IF;
END$$

DELIMITER ;

UPDATE alembic_version SET version_num='20261112_0012' WHERE alembic_version.version_num = '20261112_0011';

SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;

