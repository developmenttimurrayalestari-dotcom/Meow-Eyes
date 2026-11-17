SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

-- Running upgrade 20261112_0012 -> 20261117_0013

ALTER TABLE users ADD COLUMN phone VARCHAR(16);

ALTER TABLE users ADD CONSTRAINT uq_users_phone UNIQUE (phone);

ALTER TABLE users MODIFY email VARCHAR(254) NULL;

UPDATE alembic_version SET version_num='20261117_0013' WHERE alembic_version.version_num = '20261112_0012';

SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;

