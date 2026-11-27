SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

-- Running upgrade 20261123_0016 -> 20261127_0017

CREATE TABLE cart_tintings (
        cart_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
        tinting_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
        details JSON NOT NULL,
        CONSTRAINT pk_cart_tintings PRIMARY KEY (cart_item_id),
        CONSTRAINT fk_cart_tintings_cart_item_id_cart_items_id FOREIGN KEY(cart_item_id) REFERENCES cart_items (id) ON DELETE CASCADE
    ) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE order_item_tintings (
        order_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
        details JSON NOT NULL,
        CONSTRAINT pk_order_item_tintings PRIMARY KEY (order_item_id),
        CONSTRAINT fk_order_item_tintings_order_item_id_order_items_id FOREIGN KEY(order_item_id) REFERENCES order_items (id) ON DELETE RESTRICT
    ) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

UPDATE alembic_version SET version_num='20261127_0017' WHERE alembic_version.version_num = '20261123_0016';

SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;

