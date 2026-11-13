SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

-- Running upgrade 20261112_0009 -> 20261112_0010

CREATE TABLE lens_index_types (
    lens_index_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    category_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
    CONSTRAINT pk_lens_index_types PRIMARY KEY (lens_index_id, category_id), 
    CONSTRAINT fk_lens_index_types_lens_index_id_lens_indexes_id FOREIGN KEY(lens_index_id) REFERENCES lens_indexes (id) ON DELETE CASCADE, 
    CONSTRAINT fk_lens_index_types_category_id_categories_id FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_lens_index_types_category ON lens_index_types (category_id, lens_index_id);

UPDATE alembic_version SET version_num='20261112_0010' WHERE alembic_version.version_num = '20261112_0009';

SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;

