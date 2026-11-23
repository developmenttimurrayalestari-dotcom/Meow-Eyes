SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

-- Running upgrade 20261120_0015 -> 20261123_0016

ALTER TABLE roulette_spins MODIFY expires_at DATETIME(6) NULL;

DELIMITER $$

DROP TRIGGER IF EXISTS `trg_meow5_cashback_events_bi`$$

CREATE TRIGGER `trg_meow5_cashback_events_bi` BEFORE INSERT ON `cashback_events` FOR EACH ROW BEGIN
  IF (NEW.percent > 0 AND NEW.percent <= 100 AND NEW.expiry_days >= 0 AND NEW.end_at > NEW.start_at) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_cashback_events_bounds failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_meow5_cashback_events_bu`$$

CREATE TRIGGER `trg_meow5_cashback_events_bu` BEFORE UPDATE ON `cashback_events` FOR EACH ROW BEGIN
  IF (NEW.percent > 0 AND NEW.percent <= 100 AND NEW.expiry_days >= 0 AND NEW.end_at > NEW.start_at) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_cashback_events_bounds failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_meow5_game_rules_bi`$$

CREATE TRIGGER `trg_meow5_game_rules_bi` BEFORE INSERT ON `game_rules` FOR EACH ROW BEGIN
  IF (NEW.cooldown_seconds >= 0 AND NEW.expiry_days >= 0 AND NEW.max_duration_seconds >= 10 AND NEW.max_duration_seconds <= 600 AND NEW.max_points >= 0 AND NEW.points_per_unit > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_game_rules_bounds failed'; END IF;
  IF (NEW.engine IN ('matching','slide_puzzle','space_war','roulette')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_game_rules_engine failed'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_meow5_game_rules_bu`$$

CREATE TRIGGER `trg_meow5_game_rules_bu` BEFORE UPDATE ON `game_rules` FOR EACH ROW BEGIN
  IF (NEW.cooldown_seconds >= 0 AND NEW.expiry_days >= 0 AND NEW.max_duration_seconds >= 10 AND NEW.max_duration_seconds <= 600 AND NEW.max_points >= 0 AND NEW.points_per_unit > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_game_rules_bounds failed'; END IF;
  IF (NEW.engine IN ('matching','slide_puzzle','space_war','roulette')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule ck_game_rules_engine failed'; END IF;
END$$

DELIMITER ;

UPDATE alembic_version SET version_num='20261123_0016' WHERE alembic_version.version_num = '20261120_0015';

SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;

