SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

-- Running upgrade 20261109_0003 -> 20261110_0004

ALTER TABLE meowsurement_sessions MODIFY product_id VARCHAR(64) COLLATE utf8mb4_bin NULL;

DELIMITER $$

DROP TRIGGER IF EXISTS `trg_meow3_meowsurement_sessions_bi`$$

CREATE TRIGGER `trg_meow3_meowsurement_sessions_bi` BEFORE INSERT ON `meowsurement_sessions`
FOR EACH ROW
BEGIN
  IF (NEW.`spec_scope` IN ('product','variant','manual')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_spec_scope failed'; END IF;
  IF (NEW.`status` IN ('draft','pending_review','needs_verification','needs_remeasure','approved')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_status failed'; END IF;
  IF (NEW.`profile_version` > 0 AND NEW.`spec_version` > 0 AND NEW.`revision_number` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_versions failed'; END IF;
  IF ((NEW.spec_scope = 'manual' AND NEW.product_id IS NULL AND NEW.variant_id IS NULL) OR (NEW.spec_scope IN ('product','variant') AND NEW.product_id IS NOT NULL AND NEW.variant_id IS NOT NULL)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_frame_source failed'; END IF;
  IF NEW.status <> 'draft' AND NEW.current_revision_id IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A submitted measurement requires a revision'; END IF;
  IF (NEW.current_revision_id IS NULL AND NEW.revision_number <> 0) OR (NEW.current_revision_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM meowsurement_revisions WHERE id = NEW.current_revision_id AND session_id = NEW.id AND user_id = NEW.user_id AND revision_number = NEW.revision_number)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Current revision pointer and number must agree'; END IF;
  IF NEW.status = 'approved' AND NOT EXISTS (SELECT 1 FROM meowsurement_reviews WHERE session_id = NEW.id AND user_id = NEW.user_id AND revision_id = NEW.current_revision_id AND decision = 'approved' AND reviewer_id <> NEW.user_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Approval requires an independent stored review'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_meow3_meowsurement_sessions_bu`$$

CREATE TRIGGER `trg_meow3_meowsurement_sessions_bu` BEFORE UPDATE ON `meowsurement_sessions`
FOR EACH ROW
BEGIN
  IF (NEW.`spec_scope` IN ('product','variant','manual')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_spec_scope failed'; END IF;
  IF (NEW.`status` IN ('draft','pending_review','needs_verification','needs_remeasure','approved')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_status failed'; END IF;
  IF (NEW.`profile_version` > 0 AND NEW.`spec_version` > 0 AND NEW.`revision_number` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_versions failed'; END IF;
  IF ((NEW.spec_scope = 'manual' AND NEW.product_id IS NULL AND NEW.variant_id IS NULL) OR (NEW.spec_scope IN ('product','variant') AND NEW.product_id IS NOT NULL AND NEW.variant_id IS NOT NULL)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_frame_source failed'; END IF;
  IF NOT (NEW.`id` <=> OLD.`id`) OR NOT (NEW.`user_id` <=> OLD.`user_id`) OR NOT (NEW.`product_id` <=> OLD.`product_id`) OR NOT (NEW.`variant_id` <=> OLD.`variant_id`) OR NOT (NEW.`prescription_id` <=> OLD.`prescription_id`) OR NOT (NEW.`profile_version` <=> OLD.`profile_version`) OR NOT (NEW.`spec_version` <=> OLD.`spec_version`) OR NOT (NEW.`spec_scope` <=> OLD.`spec_scope`) OR NOT (NEW.`examination_date` <=> OLD.`examination_date`) OR NOT (NEW.`profile_snapshot` <=> OLD.`profile_snapshot`) OR NOT (NEW.`frame_snapshot` <=> OLD.`frame_snapshot`) OR NOT (NEW.`algorithm_version` <=> OLD.`algorithm_version`) OR NOT (NEW.`created_at` <=> OLD.`created_at`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement source snapshots are immutable'; END IF;
  IF NEW.status <> 'draft' AND NEW.current_revision_id IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A submitted measurement requires a revision'; END IF;
  IF (NEW.current_revision_id IS NULL AND NEW.revision_number <> 0) OR (NEW.current_revision_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM meowsurement_revisions WHERE id = NEW.current_revision_id AND session_id = NEW.id AND user_id = NEW.user_id AND revision_number = NEW.revision_number)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Current revision pointer and number must agree'; END IF;
  IF NEW.status = 'approved' AND NOT EXISTS (SELECT 1 FROM meowsurement_reviews WHERE session_id = NEW.id AND user_id = NEW.user_id AND revision_id = NEW.current_revision_id AND decision = 'approved' AND reviewer_id <> NEW.user_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Approval requires an independent stored review'; END IF;
END$$

DELIMITER ;

UPDATE alembic_version SET version_num='20261110_0004' WHERE alembic_version.version_num = '20261109_0003';

SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;

