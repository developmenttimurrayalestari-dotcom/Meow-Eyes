SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

-- Running upgrade 20261106_0002 -> 20261109_0003

-- Adds customer-owned Meowsurement. Back up and pause writers; DDL commits implicitly.

-- Stop on first error. Never use mysql --force or stamp an incomplete migration.

CREATE TABLE product_frame_specifications (
	product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	a NUMERIC(7, 2), 
	b NUMERIC(7, 2), 
	dbl NUMERIC(7, 2), 
	ed NUMERIC(7, 2), 
	temple_length NUMERIC(7, 2), 
	symmetric BOOL NOT NULL DEFAULT '0', 
	enabled BOOL NOT NULL DEFAULT '0', 
	source_note TEXT, 
	version INTEGER NOT NULL DEFAULT '1', 
	updated_by VARCHAR(64) COLLATE utf8mb4_bin, 
	updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
	created_at DATETIME(6) NOT NULL DEFAULT now(6), 
	CONSTRAINT pk_product_frame_specifications PRIMARY KEY (product_id), 
	CONSTRAINT fk_product_frame_specifications_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
	CONSTRAINT fk_product_frame_specifications_updated_by_users_user_id FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE customer_profiles (
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	phone VARCHAR(32), 
	birth_date DATE, 
	gender VARCHAR(20), 
	address TEXT, 
	active_prescription_id VARCHAR(64) COLLATE utf8mb4_bin, 
	prescription_date DATE, 
	version INTEGER NOT NULL DEFAULT '1', 
	updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
	created_at DATETIME(6) NOT NULL DEFAULT now(6), 
	CONSTRAINT pk_customer_profiles PRIMARY KEY (user_id), 
	CONSTRAINT fk_customer_profiles_active_prescription_id_us_fb9a7da0b44d FOREIGN KEY(active_prescription_id, user_id) REFERENCES prescriptions (id, user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_customer_profiles_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE meowsurement_sessions (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	variant_id VARCHAR(64) COLLATE utf8mb4_bin, 
	prescription_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	profile_version INTEGER NOT NULL, 
	spec_version INTEGER NOT NULL, 
	spec_scope VARCHAR(16) NOT NULL DEFAULT 'product', 
	examination_date DATE NOT NULL, 
	status VARCHAR(24) NOT NULL DEFAULT 'draft', 
	current_revision_id VARCHAR(64) COLLATE utf8mb4_bin, 
	revision_number INTEGER NOT NULL DEFAULT '0', 
	algorithm_version VARCHAR(100) NOT NULL, 
	profile_snapshot JSON NOT NULL, 
	frame_snapshot JSON NOT NULL, 
	device JSON, 
	updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
	created_at DATETIME(6) NOT NULL DEFAULT now(6), 
	CONSTRAINT pk_meowsurement_sessions PRIMARY KEY (id), 
	CONSTRAINT uq_meowsurement_sessions_id_user_id UNIQUE (id, user_id), 
	CONSTRAINT fk_meowsurement_sessions_product_id_variant_id_d94cf60cfd94 FOREIGN KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_sessions_prescription_id_user__80515a965ad8 FOREIGN KEY(prescription_id, user_id) REFERENCES prescriptions (id, user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_sessions_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_sessions_product_id_products_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE product_variant_frame_specifications (
	variant_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	a NUMERIC(7, 2), 
	b NUMERIC(7, 2), 
	dbl NUMERIC(7, 2), 
	ed NUMERIC(7, 2), 
	temple_length NUMERIC(7, 2), 
	symmetric BOOL NOT NULL DEFAULT '0', 
	enabled BOOL NOT NULL DEFAULT '0', 
	source_note TEXT, 
	version INTEGER NOT NULL DEFAULT '1', 
	updated_by VARCHAR(64) COLLATE utf8mb4_bin, 
	updated_at DATETIME(6) NOT NULL DEFAULT now(6), 
	created_at DATETIME(6) NOT NULL DEFAULT now(6), 
	CONSTRAINT pk_product_variant_frame_specifications PRIMARY KEY (variant_id), 
	CONSTRAINT fk_product_variant_frame_specifications_produc_c29aa19f0cb2 FOREIGN KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON DELETE CASCADE, 
	CONSTRAINT fk_product_variant_frame_specifications_update_133a0245692d FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE meowsurement_photos (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	session_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	storage_path VARCHAR(500) NOT NULL, 
	sha256 VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	source_sha256 VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	mime_type VARCHAR(32) NOT NULL, 
	width INTEGER NOT NULL, 
	height INTEGER NOT NULL, 
	byte_size INTEGER NOT NULL, 
	consent BOOL NOT NULL, 
	expires_at DATETIME(6) NOT NULL, 
	deleted_at DATETIME(6), 
	created_at DATETIME(6) NOT NULL DEFAULT now(6), 
	CONSTRAINT pk_meowsurement_photos PRIMARY KEY (id), 
	CONSTRAINT uq_meowsurement_photos_session_id_user_id_id UNIQUE (session_id, user_id, id), 
	CONSTRAINT fk_meowsurement_photos_session_id_user_id_meow_ff3248b1d22e FOREIGN KEY(session_id, user_id) REFERENCES meowsurement_sessions (id, user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE meowsurement_revisions (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	session_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	revision_number INTEGER NOT NULL, 
	parent_revision_id VARCHAR(64) COLLATE utf8mb4_bin, 
	data JSON NOT NULL, 
	reason TEXT NOT NULL, 
	actor_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	algorithm_version VARCHAR(100), 
	created_at DATETIME(6) NOT NULL DEFAULT now(6), 
	CONSTRAINT pk_meowsurement_revisions PRIMARY KEY (id), 
	CONSTRAINT uq_meowsurement_revisions_session_id_user_id_id UNIQUE (session_id, user_id, id), 
	CONSTRAINT uq_meowsurement_revisions_session_id_revision_number UNIQUE (session_id, revision_number), 
	CONSTRAINT uq_meowsurement_revisions_id_session_id_user_id UNIQUE (id, session_id, user_id), 
	CONSTRAINT fk_meowsurement_revisions_session_id_user_id_m_38fd2ad9d211 FOREIGN KEY(session_id, user_id) REFERENCES meowsurement_sessions (id, user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_revisions_session_id_user_id_p_7c6c199459bd FOREIGN KEY(session_id, user_id, parent_revision_id) REFERENCES meowsurement_revisions (session_id, user_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_revisions_actor_id_users_user_id FOREIGN KEY(actor_id) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE meowsurement_audit_events (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	session_id VARCHAR(64) COLLATE utf8mb4_bin, 
	revision_id VARCHAR(64) COLLATE utf8mb4_bin, 
	actor_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	action VARCHAR(64) NOT NULL, 
	details JSON, 
	created_at DATETIME(6) NOT NULL DEFAULT now(6), 
	CONSTRAINT pk_meowsurement_audit_events PRIMARY KEY (id), 
	CONSTRAINT fk_meowsurement_audit_events_session_id_user_i_19b9300e0f0e FOREIGN KEY(session_id, user_id) REFERENCES meowsurement_sessions (id, user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_audit_events_revision_id_sessi_09038f20c82f FOREIGN KEY(revision_id, session_id, user_id) REFERENCES meowsurement_revisions (id, session_id, user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_audit_events_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_audit_events_actor_id_users_user_id FOREIGN KEY(actor_id) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE meowsurement_captures (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	revision_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	session_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	capture_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	view VARCHAR(32) NOT NULL, 
	photo_id VARCHAR(64) COLLATE utf8mb4_bin, 
	photo_hash VARCHAR(64) COLLATE utf8mb4_bin, 
	width INTEGER NOT NULL, 
	height INTEGER NOT NULL, 
	captured_at DATETIME(6), 
	calibration JSON, 
	landmarks JSON, 
	quality JSON, 
	data JSON NOT NULL, 
	created_at DATETIME(6) NOT NULL DEFAULT now(6), 
	CONSTRAINT pk_meowsurement_captures PRIMARY KEY (id), 
	CONSTRAINT uq_meowsurement_captures_revision_id_capture_id UNIQUE (revision_id, capture_id), 
	CONSTRAINT uq_meowsurement_captures_revision_id_id UNIQUE (revision_id, id), 
	CONSTRAINT fk_meowsurement_captures_revision_id_session_i_57d34702e9be FOREIGN KEY(revision_id, session_id, user_id) REFERENCES meowsurement_revisions (id, session_id, user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_captures_session_id_user_id_ph_3ff910ad9b57 FOREIGN KEY(session_id, user_id, photo_id) REFERENCES meowsurement_photos (session_id, user_id, id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE meowsurement_measurements (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	revision_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	session_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	parameter VARCHAR(32) NOT NULL, 
	side VARCHAR(8), 
	unit VARCHAR(8) NOT NULL, 
	method VARCHAR(100) NOT NULL, 
	algorithm_version VARCHAR(100) NOT NULL, 
	valid BOOL NOT NULL, 
	`values` JSON NOT NULL, 
	quality JSON, 
	data JSON NOT NULL, 
	created_at DATETIME(6) NOT NULL DEFAULT now(6), 
	CONSTRAINT pk_meowsurement_measurements PRIMARY KEY (id), 
	CONSTRAINT uq_meowsurement_measurements_revision_id_parameter UNIQUE (revision_id, parameter), 
	CONSTRAINT uq_meowsurement_measurements_revision_id_id UNIQUE (revision_id, id), 
	CONSTRAINT fk_meowsurement_measurements_revision_id_sessi_fc78e521e3a2 FOREIGN KEY(revision_id, session_id, user_id) REFERENCES meowsurement_revisions (id, session_id, user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE meowsurement_reviews (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	session_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	revision_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	reviewer_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	decision VARCHAR(24) NOT NULL, 
	note TEXT NOT NULL, 
	evidence JSON NOT NULL, 
	created_at DATETIME(6) NOT NULL DEFAULT now(6), 
	CONSTRAINT pk_meowsurement_reviews PRIMARY KEY (id), 
	CONSTRAINT fk_meowsurement_reviews_revision_id_session_id_3821c201c3bb FOREIGN KEY(revision_id, session_id, user_id) REFERENCES meowsurement_revisions (id, session_id, user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_reviews_reviewer_id_users_user_id FOREIGN KEY(reviewer_id) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE meowsurement_measurement_sources (
	measurement_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	capture_row_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	revision_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	CONSTRAINT pk_meowsurement_measurement_sources PRIMARY KEY (measurement_id, capture_row_id), 
	CONSTRAINT fk_meowsurement_measurement_sources_revision_i_22aced642967 FOREIGN KEY(revision_id, measurement_id) REFERENCES meowsurement_measurements (revision_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_meowsurement_measurement_sources_revision_i_8050f78eb3c8 FOREIGN KEY(revision_id, capture_row_id) REFERENCES meowsurement_captures (revision_id, id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_meowsurement_review_queue ON meowsurement_sessions (status, updated_at, id);

CREATE INDEX ix_meowsurement_user_history ON meowsurement_sessions (user_id, created_at, id);

CREATE INDEX ix_variant_frame_specs_product ON product_variant_frame_specifications (product_id);

CREATE INDEX ix_meowsurement_photo_retention ON meowsurement_photos (deleted_at, expires_at);

CREATE INDEX ix_meowsurement_revision_actor ON meowsurement_revisions (actor_id, created_at);

CREATE INDEX ix_meowsurement_audit_owner ON meowsurement_audit_events (user_id, created_at, id);

CREATE INDEX ix_meowsurement_reviews_session ON meowsurement_reviews (session_id, created_at);

ALTER TABLE meowsurement_sessions ADD CONSTRAINT fk_meowsurement_current_revision FOREIGN KEY(id, user_id, current_revision_id) REFERENCES meowsurement_revisions (session_id, user_id, id) ON DELETE RESTRICT;

DELIMITER $$

CREATE TRIGGER `trg_meow3_product_frame_specifications_bi` BEFORE INSERT ON `product_frame_specifications`
FOR EACH ROW
BEGIN
  IF ((NEW.`a` IS NULL OR NEW.`a` > 0) AND (NEW.`b` IS NULL OR NEW.`b` > 0) AND (NEW.`dbl` IS NULL OR NEW.`dbl` > 0) AND (NEW.`ed` IS NULL OR NEW.`ed` > 0) AND (NEW.`temple_length` IS NULL OR NEW.`temple_length` > 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_dimensions failed'; END IF;
  IF (NEW.`symmetric` IN (0,1) AND NEW.`enabled` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_flags failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_version failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM products WHERE id = NEW.product_id AND product_type = 'frame') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Frame specification requires a frame product'; END IF;
END$$

CREATE TRIGGER `trg_meow3_product_frame_specifications_bu` BEFORE UPDATE ON `product_frame_specifications`
FOR EACH ROW
BEGIN
  IF ((NEW.`a` IS NULL OR NEW.`a` > 0) AND (NEW.`b` IS NULL OR NEW.`b` > 0) AND (NEW.`dbl` IS NULL OR NEW.`dbl` > 0) AND (NEW.`ed` IS NULL OR NEW.`ed` > 0) AND (NEW.`temple_length` IS NULL OR NEW.`temple_length` > 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_dimensions failed'; END IF;
  IF (NEW.`symmetric` IN (0,1) AND NEW.`enabled` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_flags failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_version failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM products WHERE id = NEW.product_id AND product_type = 'frame') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Frame specification requires a frame product'; END IF;
END$$

CREATE TRIGGER `trg_meow3_customer_profiles_bi` BEFORE INSERT ON `customer_profiles`
FOR EACH ROW
BEGIN
  IF (NEW.`gender` IS NULL OR NEW.`gender` IN ('male','female','unspecified')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_customer_profiles_gender failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_customer_profiles_version failed'; END IF;
END$$

CREATE TRIGGER `trg_meow3_customer_profiles_bu` BEFORE UPDATE ON `customer_profiles`
FOR EACH ROW
BEGIN
  IF (NEW.`gender` IS NULL OR NEW.`gender` IN ('male','female','unspecified')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_customer_profiles_gender failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_customer_profiles_version failed'; END IF;
END$$

CREATE TRIGGER `trg_meow3_meowsurement_sessions_bi` BEFORE INSERT ON `meowsurement_sessions`
FOR EACH ROW
BEGIN
  IF (NEW.`spec_scope` IN ('product','variant')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_spec_scope failed'; END IF;
  IF (NEW.`status` IN ('draft','pending_review','needs_verification','needs_remeasure','approved')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_status failed'; END IF;
  IF (NEW.`profile_version` > 0 AND NEW.`spec_version` > 0 AND NEW.`revision_number` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_versions failed'; END IF;
  IF NEW.status <> 'draft' AND NEW.current_revision_id IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A submitted measurement requires a revision'; END IF;
  IF (NEW.current_revision_id IS NULL AND NEW.revision_number <> 0) OR (NEW.current_revision_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM meowsurement_revisions WHERE id = NEW.current_revision_id AND session_id = NEW.id AND user_id = NEW.user_id AND revision_number = NEW.revision_number)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Current revision pointer and number must agree'; END IF;
  IF NEW.status = 'approved' AND NOT EXISTS (SELECT 1 FROM meowsurement_reviews WHERE session_id = NEW.id AND user_id = NEW.user_id AND revision_id = NEW.current_revision_id AND decision = 'approved' AND reviewer_id <> NEW.user_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Approval requires an independent stored review'; END IF;
END$$

CREATE TRIGGER `trg_meow3_meowsurement_sessions_bu` BEFORE UPDATE ON `meowsurement_sessions`
FOR EACH ROW
BEGIN
  IF (NEW.`spec_scope` IN ('product','variant')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_spec_scope failed'; END IF;
  IF (NEW.`status` IN ('draft','pending_review','needs_verification','needs_remeasure','approved')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_status failed'; END IF;
  IF (NEW.`profile_version` > 0 AND NEW.`spec_version` > 0 AND NEW.`revision_number` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_versions failed'; END IF;
  IF NOT (NEW.`id` <=> OLD.`id`) OR NOT (NEW.`user_id` <=> OLD.`user_id`) OR NOT (NEW.`product_id` <=> OLD.`product_id`) OR NOT (NEW.`variant_id` <=> OLD.`variant_id`) OR NOT (NEW.`prescription_id` <=> OLD.`prescription_id`) OR NOT (NEW.`profile_version` <=> OLD.`profile_version`) OR NOT (NEW.`spec_version` <=> OLD.`spec_version`) OR NOT (NEW.`spec_scope` <=> OLD.`spec_scope`) OR NOT (NEW.`examination_date` <=> OLD.`examination_date`) OR NOT (NEW.`profile_snapshot` <=> OLD.`profile_snapshot`) OR NOT (NEW.`frame_snapshot` <=> OLD.`frame_snapshot`) OR NOT (NEW.`algorithm_version` <=> OLD.`algorithm_version`) OR NOT (NEW.`created_at` <=> OLD.`created_at`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement source snapshots are immutable'; END IF;
  IF NEW.status <> 'draft' AND NEW.current_revision_id IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A submitted measurement requires a revision'; END IF;
  IF (NEW.current_revision_id IS NULL AND NEW.revision_number <> 0) OR (NEW.current_revision_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM meowsurement_revisions WHERE id = NEW.current_revision_id AND session_id = NEW.id AND user_id = NEW.user_id AND revision_number = NEW.revision_number)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Current revision pointer and number must agree'; END IF;
  IF NEW.status = 'approved' AND NOT EXISTS (SELECT 1 FROM meowsurement_reviews WHERE session_id = NEW.id AND user_id = NEW.user_id AND revision_id = NEW.current_revision_id AND decision = 'approved' AND reviewer_id <> NEW.user_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Approval requires an independent stored review'; END IF;
END$$

CREATE TRIGGER `trg_meow3_product_variant_frame_specifications_bi` BEFORE INSERT ON `product_variant_frame_specifications`
FOR EACH ROW
BEGIN
  IF ((NEW.`a` IS NULL OR NEW.`a` > 0) AND (NEW.`b` IS NULL OR NEW.`b` > 0) AND (NEW.`dbl` IS NULL OR NEW.`dbl` > 0) AND (NEW.`ed` IS NULL OR NEW.`ed` > 0) AND (NEW.`temple_length` IS NULL OR NEW.`temple_length` > 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_dimensions failed'; END IF;
  IF (NEW.`symmetric` IN (0,1) AND NEW.`enabled` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_flags failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_version failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM products WHERE id = NEW.product_id AND product_type = 'frame') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Frame specification requires a frame product'; END IF;
END$$

CREATE TRIGGER `trg_meow3_product_variant_frame_specifications_bu` BEFORE UPDATE ON `product_variant_frame_specifications`
FOR EACH ROW
BEGIN
  IF ((NEW.`a` IS NULL OR NEW.`a` > 0) AND (NEW.`b` IS NULL OR NEW.`b` > 0) AND (NEW.`dbl` IS NULL OR NEW.`dbl` > 0) AND (NEW.`ed` IS NULL OR NEW.`ed` > 0) AND (NEW.`temple_length` IS NULL OR NEW.`temple_length` > 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_dimensions failed'; END IF;
  IF (NEW.`symmetric` IN (0,1) AND NEW.`enabled` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_flags failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_version failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM products WHERE id = NEW.product_id AND product_type = 'frame') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Frame specification requires a frame product'; END IF;
END$$

CREATE TRIGGER `trg_meow3_meowsurement_photos_bi` BEFORE INSERT ON `meowsurement_photos`
FOR EACH ROW
BEGIN
  IF (NEW.`consent` = 1) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_consent failed'; END IF;
  IF (NEW.`width` > 0 AND NEW.`height` > 0 AND NEW.`width` * NEW.`height` <= 20000000) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_dimensions failed'; END IF;
  IF (NEW.`mime_type` IN ('image/jpeg','image/png','image/webp')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_mime failed'; END IF;
  IF (NEW.`byte_size` > 0 AND NEW.`byte_size` <= 8388608) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_size failed'; END IF;
END$$

CREATE TRIGGER `trg_meow3_meowsurement_photos_bu` BEFORE UPDATE ON `meowsurement_photos`
FOR EACH ROW
BEGIN
  IF (NEW.`consent` = 1) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_consent failed'; END IF;
  IF (NEW.`width` > 0 AND NEW.`height` > 0 AND NEW.`width` * NEW.`height` <= 20000000) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_dimensions failed'; END IF;
  IF (NEW.`mime_type` IN ('image/jpeg','image/png','image/webp')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_mime failed'; END IF;
  IF (NEW.`byte_size` > 0 AND NEW.`byte_size` <= 8388608) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_size failed'; END IF;
  IF NOT (NEW.`id` <=> OLD.`id`) OR NOT (NEW.`user_id` <=> OLD.`user_id`) OR NOT (NEW.`session_id` <=> OLD.`session_id`) OR NOT (NEW.`storage_path` <=> OLD.`storage_path`) OR NOT (NEW.`sha256` <=> OLD.`sha256`) OR NOT (NEW.`source_sha256` <=> OLD.`source_sha256`) OR NOT (NEW.`mime_type` <=> OLD.`mime_type`) OR NOT (NEW.`width` <=> OLD.`width`) OR NOT (NEW.`height` <=> OLD.`height`) OR NOT (NEW.`byte_size` <=> OLD.`byte_size`) OR NOT (NEW.`consent` <=> OLD.`consent`) OR NOT (NEW.`created_at` <=> OLD.`created_at`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Private photo provenance is immutable'; END IF;
  IF OLD.deleted_at IS NOT NULL AND NEW.deleted_at IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A deleted private photo cannot be reactivated'; END IF;
END$$

CREATE TRIGGER `trg_meow3_meowsurement_revisions_bi` BEFORE INSERT ON `meowsurement_revisions`
FOR EACH ROW
BEGIN
  IF (NEW.`revision_number` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_revisions_number failed'; END IF;
  IF (NEW.`parent_revision_id` IS NULL OR NEW.`parent_revision_id` <> NEW.`id`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_revisions_parent failed'; END IF;
  IF (NEW.revision_number = 1 AND NEW.parent_revision_id IS NOT NULL) OR (NEW.revision_number > 1 AND NOT EXISTS (SELECT 1 FROM meowsurement_revisions WHERE id = NEW.parent_revision_id AND session_id = NEW.session_id AND user_id = NEW.user_id AND revision_number = NEW.revision_number - 1)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Revision parent sequence is invalid'; END IF;
END$$

CREATE TRIGGER `trg_meow3_meowsurement_revisions_bu` BEFORE UPDATE ON `meowsurement_revisions`
FOR EACH ROW
BEGIN
  IF (NEW.`revision_number` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_revisions_number failed'; END IF;
  IF (NEW.`parent_revision_id` IS NULL OR NEW.`parent_revision_id` <> NEW.`id`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_revisions_parent failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_revisions_bd` BEFORE DELETE ON `meowsurement_revisions`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_audit_events_bi` BEFORE INSERT ON `meowsurement_audit_events`
FOR EACH ROW
BEGIN
  IF (NEW.`revision_id` IS NULL OR NEW.`session_id` IS NOT NULL) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_audit_events_revision_owner failed'; END IF;
END$$

CREATE TRIGGER `trg_meow3_meowsurement_audit_events_bu` BEFORE UPDATE ON `meowsurement_audit_events`
FOR EACH ROW
BEGIN
  IF (NEW.`revision_id` IS NULL OR NEW.`session_id` IS NOT NULL) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_audit_events_revision_owner failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_audit_events_bd` BEFORE DELETE ON `meowsurement_audit_events`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_captures_bi` BEFORE INSERT ON `meowsurement_captures`
FOR EACH ROW
BEGIN
  IF (NEW.`width` > 0 AND NEW.`height` > 0 AND NEW.`width` * NEW.`height` <= 20000000) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_captures_dimensions failed'; END IF;
  IF (NEW.`view` IN ('frontal','frontal_near','three_quarter_left','three_quarter_right','lateral_left','lateral_right')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_captures_view failed'; END IF;
END$$

CREATE TRIGGER `trg_meow3_meowsurement_captures_bu` BEFORE UPDATE ON `meowsurement_captures`
FOR EACH ROW
BEGIN
  IF (NEW.`width` > 0 AND NEW.`height` > 0 AND NEW.`width` * NEW.`height` <= 20000000) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_captures_dimensions failed'; END IF;
  IF (NEW.`view` IN ('frontal','frontal_near','three_quarter_left','three_quarter_right','lateral_left','lateral_right')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_captures_view failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_captures_bd` BEFORE DELETE ON `meowsurement_captures`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_measurements_bi` BEFORE INSERT ON `meowsurement_measurements`
FOR EACH ROW
BEGIN
  IF (NEW.`parameter` IN ('distance_pd','near_pd','vertex_right','vertex_left','pantoscopic_right','pantoscopic_left','wrap_right','wrap_left')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_parameter failed'; END IF;
  IF (NEW.`side` IS NULL OR NEW.`side` IN ('right','left','both')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_side failed'; END IF;
  IF (NEW.`unit` IN ('mm','deg') AND NEW.`valid` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_unit_valid failed'; END IF;
END$$

CREATE TRIGGER `trg_meow3_meowsurement_measurements_bu` BEFORE UPDATE ON `meowsurement_measurements`
FOR EACH ROW
BEGIN
  IF (NEW.`parameter` IN ('distance_pd','near_pd','vertex_right','vertex_left','pantoscopic_right','pantoscopic_left','wrap_right','wrap_left')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_parameter failed'; END IF;
  IF (NEW.`side` IS NULL OR NEW.`side` IN ('right','left','both')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_side failed'; END IF;
  IF (NEW.`unit` IN ('mm','deg') AND NEW.`valid` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_unit_valid failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_measurements_bd` BEFORE DELETE ON `meowsurement_measurements`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_reviews_bi` BEFORE INSERT ON `meowsurement_reviews`
FOR EACH ROW
BEGIN
  IF (NEW.`decision` IN ('approved','needs_verification','needs_remeasure')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_reviews_decision failed'; END IF;
  IF (NEW.`reviewer_id` <> NEW.`user_id`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_reviews_independent failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM users u WHERE u.user_id = NEW.reviewer_id AND u.is_active = 1 AND (u.role IN ('admin','super_admin') OR (u.role = 'staff' AND EXISTS (SELECT 1 FROM user_permissions p WHERE p.user_id = u.user_id AND p.permission = 'meowsurement.review')))) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'An active authorized web reviewer is required'; END IF;
  IF NOT EXISTS (SELECT 1 FROM meowsurement_sessions s JOIN meowsurement_revisions r ON r.id = s.current_revision_id AND r.session_id = s.id AND r.user_id = s.user_id WHERE s.id = NEW.session_id AND s.user_id = NEW.user_id AND r.id = NEW.revision_id AND s.status IN ('pending_review','needs_verification') AND r.actor_id <> NEW.reviewer_id AND s.user_id <> NEW.reviewer_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Review requires the current independent revision'; END IF;
END$$

CREATE TRIGGER `trg_meow3_meowsurement_reviews_bu` BEFORE UPDATE ON `meowsurement_reviews`
FOR EACH ROW
BEGIN
  IF (NEW.`decision` IN ('approved','needs_verification','needs_remeasure')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_reviews_decision failed'; END IF;
  IF (NEW.`reviewer_id` <> NEW.`user_id`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_reviews_independent failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_reviews_bd` BEFORE DELETE ON `meowsurement_reviews`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_measurement_sources_bu` BEFORE UPDATE ON `meowsurement_measurement_sources`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

CREATE TRIGGER `trg_meow3_meowsurement_measurement_sources_bd` BEFORE DELETE ON `meowsurement_measurement_sources`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END$$

DELIMITER ;

UPDATE alembic_version SET version_num='20261109_0003' WHERE alembic_version.version_num = '20261106_0002';

SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;

