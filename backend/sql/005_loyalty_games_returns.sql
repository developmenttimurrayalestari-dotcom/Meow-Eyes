SET @meow_previous_sql_mode = @@SESSION.sql_mode;

SET @meow_previous_time_zone = @@SESSION.time_zone;

SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE', time_zone = '+00:00', innodb_strict_mode = ON;

-- Running upgrade 20261110_0004 -> 20261111_0005

CREATE TABLE cashback_events (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	start_at DATETIME(6) NOT NULL, 
	end_at DATETIME(6) NOT NULL, 
	percent NUMERIC(7, 4) NOT NULL, 
	expiry_days INTEGER NOT NULL, 
	is_active BOOL NOT NULL, 
	CONSTRAINT pk_cashback_events PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE point_settings (
	id VARCHAR(16) NOT NULL, 
	rate NUMERIC(18, 4) NOT NULL, 
	version INTEGER NOT NULL, 
	cashback_valuation VARCHAR(16) NOT NULL, 
	updated_at DATETIME(6) NOT NULL, 
	CONSTRAINT pk_point_settings PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE puzzle_levels (
	level INTEGER NOT NULL, 
	`rows` INTEGER NOT NULL, 
	columns INTEGER NOT NULL, 
	image_url TEXT NOT NULL, 
	is_active BOOL NOT NULL, 
	CONSTRAINT pk_puzzle_levels PRIMARY KEY (level)
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE game_rules (
	game_key VARCHAR(32) NOT NULL, 
	engine VARCHAR(32) NOT NULL, 
	cooldown_seconds INTEGER NOT NULL, 
	expiry_days INTEGER NOT NULL, 
	max_duration_seconds INTEGER NOT NULL, 
	max_points INTEGER NOT NULL, 
	points_per_unit INTEGER NOT NULL, 
	CONSTRAINT pk_game_rules PRIMARY KEY (game_key), 
	CONSTRAINT fk_game_rules_game_key_games_key FOREIGN KEY(game_key) REFERENCES games (`key`) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE game_sessions (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	game_key VARCHAR(32) NOT NULL, 
	active_slot VARCHAR(191) COLLATE utf8mb4_bin, 
	seed BIGINT NOT NULL, 
	snapshot JSON NOT NULL, 
	transcript JSON, 
	status VARCHAR(16) NOT NULL, 
	score INTEGER NOT NULL, 
	points_awarded INTEGER NOT NULL, 
	started_at DATETIME(6) NOT NULL, 
	completed_at DATETIME(6), 
	expires_at DATETIME(6) NOT NULL, 
	CONSTRAINT pk_game_sessions PRIMARY KEY (id), 
	CONSTRAINT fk_game_sessions_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_game_sessions_game_key_games_key FOREIGN KEY(game_key) REFERENCES games (`key`) ON DELETE RESTRICT, 
	CONSTRAINT uq_game_sessions_active_slot UNIQUE (active_slot)
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE point_lots (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	award_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL, 
	source VARCHAR(32) NOT NULL, 
	earned BIGINT NOT NULL, 
	remaining BIGINT NOT NULL, 
	rate_snapshot NUMERIC(18, 4) NOT NULL, 
	rate_version INTEGER NOT NULL, 
	valuation VARCHAR(16) NOT NULL, 
	expires_at DATETIME(6), 
	created_at DATETIME(6) NOT NULL, 
	CONSTRAINT pk_point_lots PRIMARY KEY (id), 
	CONSTRAINT fk_point_lots_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
	CONSTRAINT uq_point_lots_award_key UNIQUE (award_key)
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE point_rate_versions (
	version INTEGER NOT NULL, 
	rate NUMERIC(18, 4) NOT NULL, 
	cashback_valuation VARCHAR(16) NOT NULL, 
	actor_id VARCHAR(64) COLLATE utf8mb4_bin, 
	created_at DATETIME(6) NOT NULL, 
	CONSTRAINT pk_point_rate_versions PRIMARY KEY (version), 
	CONSTRAINT fk_point_rate_versions_actor_id_users_user_id FOREIGN KEY(actor_id) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE cashback_awards (
	order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	event_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	snapshot JSON NOT NULL, 
	amount NUMERIC(18, 2) NOT NULL, 
	rate_snapshot NUMERIC(18, 4) NOT NULL, 
	points BIGINT NOT NULL, 
	credited_at DATETIME(6), 
	CONSTRAINT pk_cashback_awards PRIMARY KEY (order_id), 
	CONSTRAINT fk_cashback_awards_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_cashback_awards_event_id_cashback_events_id FOREIGN KEY(event_id) REFERENCES cashback_events (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE point_history (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	event_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	lot_id VARCHAR(64) COLLATE utf8mb4_bin, 
	order_id VARCHAR(64) COLLATE utf8mb4_bin, 
	source VARCHAR(64) NOT NULL, 
	delta BIGINT NOT NULL, 
	balance_after BIGINT NOT NULL, 
	rate_snapshot NUMERIC(18, 4) NOT NULL, 
	rate_version INTEGER NOT NULL, 
	value_snapshot NUMERIC(18, 2) NOT NULL, 
	expires_at DATETIME(6), 
	note TEXT NOT NULL, 
	created_at DATETIME(6) NOT NULL, 
	CONSTRAINT pk_point_history PRIMARY KEY (id), 
	CONSTRAINT uq_point_history_event_key UNIQUE (event_key), 
	CONSTRAINT fk_point_history_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_point_history_lot_id_point_lots_id FOREIGN KEY(lot_id) REFERENCES point_lots (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_point_history_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE point_redemptions (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	lot_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	points BIGINT NOT NULL, 
	rate_snapshot NUMERIC(18, 4) NOT NULL, 
	rate_version INTEGER NOT NULL, 
	value_snapshot NUMERIC(18, 2) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	CONSTRAINT pk_point_redemptions PRIMARY KEY (id), 
	CONSTRAINT uq_point_redemptions_order_id_lot_id UNIQUE (order_id, lot_id), 
	CONSTRAINT fk_point_redemptions_order_id_orders_id FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_point_redemptions_lot_id_point_lots_id FOREIGN KEY(lot_id) REFERENCES point_lots (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE return_cases (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	reference VARCHAR(64) NOT NULL, 
	order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	user_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	reason TEXT NOT NULL, 
	instructions JSON, 
	return_courier VARCHAR(128), 
	return_tracking VARCHAR(128), 
	replacement_courier VARCHAR(128), 
	replacement_tracking VARCHAR(128), 
	created_at DATETIME(6) NOT NULL, 
	updated_at DATETIME(6) NOT NULL, 
	CONSTRAINT pk_return_cases PRIMARY KEY (id), 
	CONSTRAINT fk_return_cases_order_id_user_id_orders_id_orders_user_id FOREIGN KEY(order_id, user_id) REFERENCES orders (id, user_id) ON DELETE RESTRICT, 
	CONSTRAINT uq_return_cases_reference UNIQUE (reference)
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE return_case_items (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	case_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	order_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	quantity INTEGER NOT NULL, 
	CONSTRAINT pk_return_case_items PRIMARY KEY (id), 
	CONSTRAINT fk_return_case_items_order_item_id_order_id_or_e6f8a9f1bb63 FOREIGN KEY(order_item_id, order_id) REFERENCES order_items (id, order_id) ON DELETE RESTRICT, 
	CONSTRAINT uq_return_case_items_case_id_order_item_id UNIQUE (case_id, order_item_id), 
	CONSTRAINT fk_return_case_items_case_id_return_cases_id FOREIGN KEY(case_id) REFERENCES return_cases (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE return_evidence (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	case_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	storage_path TEXT NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	mime_type VARCHAR(32) NOT NULL, 
	byte_size BIGINT NOT NULL, 
	created_at DATETIME(6) NOT NULL, 
	CONSTRAINT pk_return_evidence PRIMARY KEY (id), 
	CONSTRAINT fk_return_evidence_case_id_return_cases_id FOREIGN KEY(case_id) REFERENCES return_cases (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE TABLE return_timeline (
	id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	case_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	actor_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	note TEXT NOT NULL, 
	created_at DATETIME(6) NOT NULL, 
	CONSTRAINT pk_return_timeline PRIMARY KEY (id), 
	CONSTRAINT fk_return_timeline_case_id_return_cases_id FOREIGN KEY(case_id) REFERENCES return_cases (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_return_timeline_actor_id_users_user_id FOREIGN KEY(actor_id) REFERENCES users (user_id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_game_session_cooldown ON game_sessions (user_id, game_key, started_at);

CREATE INDEX ix_point_lots_wallet ON point_lots (user_id, expires_at, created_at);

CREATE INDEX ix_point_history_customer ON point_history (user_id, created_at, id);

CREATE INDEX ix_return_cases_order ON return_cases (order_id, created_at);

INSERT INTO point_settings(id,rate,version,cashback_valuation,updated_at) VALUES('global',100,1,'locked',UTC_TIMESTAMP(6));

INSERT INTO point_rate_versions(version,rate,cashback_valuation,created_at) VALUES(1,100,'locked',UTC_TIMESTAMP(6));

UPDATE games SET is_active=0 WHERE `key` IN ('puzzle','tetris','memory');

INSERT INTO point_lots(id,user_id,award_key,source,earned,remaining,rate_snapshot,rate_version,valuation,created_at) SELECT SHA2(CONCAT('legacy-lot:',user_id),256),user_id,CONCAT('legacy:',user_id),'legacy',points_balance,points_balance,100,1,'locked',UTC_TIMESTAMP(6) FROM users WHERE points_balance>0;

INSERT INTO point_history(id,event_key,user_id,order_id,source,delta,balance_after,rate_snapshot,rate_version,value_snapshot,note,created_at) SELECT SHA2(CONCAT('legacy-log:',id),256),CONCAT('legacy-log:',id),user_id,order_id,type,delta,balance_after,100,1,delta*100,note,created_at FROM point_logs;

INSERT INTO point_history(id,event_key,user_id,lot_id,source,delta,balance_after,rate_snapshot,rate_version,value_snapshot,note,created_at) SELECT SHA2(CONCAT('legacy-ledger:',l.user_id),256),CONCAT('legacy:',l.user_id),l.user_id,l.id,'legacy',l.earned-COALESCE(h.total,0),l.remaining,100,1,(l.earned-COALESCE(h.total,0))*100,'Rekonsiliasi saldo awal; riwayat lama dipertahankan',l.created_at FROM point_lots l LEFT JOIN (SELECT user_id,SUM(delta) AS total FROM point_logs GROUP BY user_id) h ON h.user_id=l.user_id WHERE l.source='legacy';

INSERT INTO games(id,`key`,name,description,is_active,max_points,created_at) VALUES(REPLACE(UUID(),'-',''),'matching','Match Meow Pairs','',1,50,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE name=VALUES(name),is_active=1;

INSERT INTO game_rules(game_key,engine,cooldown_seconds,expiry_days,max_duration_seconds,max_points,points_per_unit) VALUES('matching','matching',86400,30,180,50,5);

INSERT INTO games(id,`key`,name,description,is_active,max_points,created_at) VALUES(REPLACE(UUID(),'-',''),'slide-puzzle','Meow Puzzle Geser','',1,50,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE name=VALUES(name),is_active=1;

INSERT INTO game_rules(game_key,engine,cooldown_seconds,expiry_days,max_duration_seconds,max_points,points_per_unit) VALUES('slide-puzzle','slide_puzzle',86400,30,180,50,3);

INSERT INTO games(id,`key`,name,description,is_active,max_points,created_at) VALUES(REPLACE(UUID(),'-',''),'space-war','Meow Space War','',1,50,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE name=VALUES(name),is_active=1;

INSERT INTO game_rules(game_key,engine,cooldown_seconds,expiry_days,max_duration_seconds,max_points,points_per_unit) VALUES('space-war','space_war',86400,30,180,50,1);

INSERT INTO games(id,`key`,name,description,is_active,max_points,created_at) VALUES(REPLACE(UUID(),'-',''),'roulette','Roulette','',1,50,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE name=VALUES(name),is_active=1;

INSERT INTO game_rules(game_key,engine,cooldown_seconds,expiry_days,max_duration_seconds,max_points,points_per_unit) VALUES('roulette','roulette',86400,30,180,50,1);

UPDATE game_rules SET max_points=GREATEST(50,COALESCE((SELECT FLOOR(MAX(value)) FROM roulette_rewards WHERE type='points' AND is_active=1),0)) WHERE game_key='roulette';

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(1,2,2,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(2,2,2,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(3,2,2,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(4,2,2,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(5,3,3,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(6,3,3,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(7,3,3,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(8,3,3,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(9,4,4,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(10,4,4,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(11,4,4,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(12,4,4,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(13,5,5,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(14,5,5,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(15,5,5,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(16,5,5,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(17,6,6,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(18,6,6,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(19,6,6,'/logo-meow.jpg',1);

INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES(20,6,6,'/logo-meow.jpg',1);

DELIMITER $$

CREATE TRIGGER `trg_meow5_cashback_events_bi` BEFORE INSERT ON `cashback_events` FOR EACH ROW BEGIN
  IF (NEW.percent > 0 AND NEW.percent <= 100 AND NEW.expiry_days > 0 AND NEW.end_at > NEW.start_at) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_cashback_events_bounds failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_cashback_events_bu` BEFORE UPDATE ON `cashback_events` FOR EACH ROW BEGIN
  IF (NEW.percent > 0 AND NEW.percent <= 100 AND NEW.expiry_days > 0 AND NEW.end_at > NEW.start_at) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_cashback_events_bounds failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_point_settings_bi` BEFORE INSERT ON `point_settings` FOR EACH ROW BEGIN
  IF (NEW.id = 'global' AND NEW.rate > 0 AND NEW.version > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_settings_positive failed'; END IF;
  IF (NEW.cashback_valuation = 'locked') IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_settings_valuation failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_point_settings_bu` BEFORE UPDATE ON `point_settings` FOR EACH ROW BEGIN
  IF (NEW.id = 'global' AND NEW.rate > 0 AND NEW.version > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_settings_positive failed'; END IF;
  IF (NEW.cashback_valuation = 'locked') IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_settings_valuation failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_puzzle_levels_bi` BEFORE INSERT ON `puzzle_levels` FOR EACH ROW BEGIN
  IF (NEW.level >= 1 AND NEW.level <= 20 AND NEW.rows >= 2 AND NEW.rows <= 6 AND NEW.columns >= 2 AND NEW.columns <= 6) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_puzzle_levels_bounds failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_puzzle_levels_bu` BEFORE UPDATE ON `puzzle_levels` FOR EACH ROW BEGIN
  IF (NEW.level >= 1 AND NEW.level <= 20 AND NEW.rows >= 2 AND NEW.rows <= 6 AND NEW.columns >= 2 AND NEW.columns <= 6) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_puzzle_levels_bounds failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_game_rules_bi` BEFORE INSERT ON `game_rules` FOR EACH ROW BEGIN
  IF (NEW.cooldown_seconds >= 0 AND NEW.expiry_days > 0 AND NEW.max_duration_seconds >= 10 AND NEW.max_duration_seconds <= 600 AND NEW.max_points >= 0 AND NEW.points_per_unit > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_game_rules_bounds failed'; END IF;
  IF (NEW.engine IN ('matching','slide_puzzle','space_war','roulette')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_game_rules_engine failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_game_rules_bu` BEFORE UPDATE ON `game_rules` FOR EACH ROW BEGIN
  IF (NEW.cooldown_seconds >= 0 AND NEW.expiry_days > 0 AND NEW.max_duration_seconds >= 10 AND NEW.max_duration_seconds <= 600 AND NEW.max_points >= 0 AND NEW.points_per_unit > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_game_rules_bounds failed'; END IF;
  IF (NEW.engine IN ('matching','slide_puzzle','space_war','roulette')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_game_rules_engine failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_game_sessions_bi` BEFORE INSERT ON `game_sessions` FOR EACH ROW BEGIN
  IF (NEW.status IN ('active','completed','expired') AND NEW.seed >= 0 AND NEW.points_awarded >= 0 AND NEW.score >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_game_sessions_state failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_game_sessions_bu` BEFORE UPDATE ON `game_sessions` FOR EACH ROW BEGIN
  IF (NEW.status IN ('active','completed','expired') AND NEW.seed >= 0 AND NEW.points_awarded >= 0 AND NEW.score >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_game_sessions_state failed'; END IF;
  IF NOT (NEW.`id` <=> OLD.`id`) OR NOT (NEW.`user_id` <=> OLD.`user_id`) OR NOT (NEW.`game_key` <=> OLD.`game_key`) OR NOT (NEW.`seed` <=> OLD.`seed`) OR NOT (NEW.`snapshot` <=> OLD.`snapshot`) OR NOT (NEW.`started_at` <=> OLD.`started_at`) OR NOT (NEW.`expires_at` <=> OLD.`expires_at`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Acquisition and order snapshots are immutable'; END IF;
END$$

CREATE TRIGGER `trg_meow5_game_sessions_bd` BEFORE DELETE ON `game_sessions` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audited acquisitions cannot be deleted';
END$$

CREATE TRIGGER `trg_meow5_point_lots_bi` BEFORE INSERT ON `point_lots` FOR EACH ROW BEGIN
  IF (NEW.earned > 0 AND NEW.remaining >= 0 AND NEW.remaining <= NEW.earned AND NEW.rate_snapshot > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_lots_amounts failed'; END IF;
  IF (NEW.valuation = 'locked') IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_lots_valuation failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_point_lots_bu` BEFORE UPDATE ON `point_lots` FOR EACH ROW BEGIN
  IF (NEW.earned > 0 AND NEW.remaining >= 0 AND NEW.remaining <= NEW.earned AND NEW.rate_snapshot > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_lots_amounts failed'; END IF;
  IF (NEW.valuation = 'locked') IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_lots_valuation failed'; END IF;
  IF NOT (NEW.`id` <=> OLD.`id`) OR NOT (NEW.`user_id` <=> OLD.`user_id`) OR NOT (NEW.`award_key` <=> OLD.`award_key`) OR NOT (NEW.`source` <=> OLD.`source`) OR NOT (NEW.`earned` <=> OLD.`earned`) OR NOT (NEW.`rate_snapshot` <=> OLD.`rate_snapshot`) OR NOT (NEW.`rate_version` <=> OLD.`rate_version`) OR NOT (NEW.`valuation` <=> OLD.`valuation`) OR NOT (NEW.`expires_at` <=> OLD.`expires_at`) OR NOT (NEW.`created_at` <=> OLD.`created_at`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Acquisition and order snapshots are immutable'; END IF;
END$$

CREATE TRIGGER `trg_meow5_point_lots_bd` BEFORE DELETE ON `point_lots` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audited acquisitions cannot be deleted';
END$$

CREATE TRIGGER `trg_meow5_point_rate_versions_bi` BEFORE INSERT ON `point_rate_versions` FOR EACH ROW BEGIN
  IF (NEW.rate > 0 AND NEW.version > 0 AND NEW.cashback_valuation = 'locked') IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_rate_versions_positive failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_point_rate_versions_bu` BEFORE UPDATE ON `point_rate_versions` FOR EACH ROW BEGIN
  IF (NEW.rate > 0 AND NEW.version > 0 AND NEW.cashback_valuation = 'locked') IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_rate_versions_positive failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'History is append-only';
END$$

CREATE TRIGGER `trg_meow5_point_rate_versions_bd` BEFORE DELETE ON `point_rate_versions` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'History is append-only';
END$$

CREATE TRIGGER `trg_meow5_cashback_awards_bi` BEFORE INSERT ON `cashback_awards` FOR EACH ROW BEGIN
  IF (NEW.points >= 0 AND NEW.amount >= 0 AND NEW.rate_snapshot > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_cashback_awards_amounts failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_cashback_awards_bu` BEFORE UPDATE ON `cashback_awards` FOR EACH ROW BEGIN
  IF (NEW.points >= 0 AND NEW.amount >= 0 AND NEW.rate_snapshot > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_cashback_awards_amounts failed'; END IF;
  IF NOT (NEW.`order_id` <=> OLD.`order_id`) OR NOT (NEW.`event_id` <=> OLD.`event_id`) OR NOT (NEW.`snapshot` <=> OLD.`snapshot`) OR NOT (NEW.`amount` <=> OLD.`amount`) OR NOT (NEW.`rate_snapshot` <=> OLD.`rate_snapshot`) OR NOT (NEW.`points` <=> OLD.`points`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Acquisition and order snapshots are immutable'; END IF;
END$$

CREATE TRIGGER `trg_meow5_cashback_awards_bd` BEFORE DELETE ON `cashback_awards` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audited acquisitions cannot be deleted';
END$$

CREATE TRIGGER `trg_meow5_point_history_bi` BEFORE INSERT ON `point_history` FOR EACH ROW BEGIN
  IF (NEW.balance_after >= 0 AND NEW.rate_snapshot > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_history_amounts failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_point_history_bu` BEFORE UPDATE ON `point_history` FOR EACH ROW BEGIN
  IF (NEW.balance_after >= 0 AND NEW.rate_snapshot > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_history_amounts failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'History is append-only';
END$$

CREATE TRIGGER `trg_meow5_point_history_bd` BEFORE DELETE ON `point_history` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'History is append-only';
END$$

CREATE TRIGGER `trg_meow5_point_redemptions_bi` BEFORE INSERT ON `point_redemptions` FOR EACH ROW BEGIN
  IF (NEW.points > 0 AND NEW.rate_snapshot > 0 AND NEW.status IN ('reserved','consumed','released')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_redemptions_valid failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_point_redemptions_bu` BEFORE UPDATE ON `point_redemptions` FOR EACH ROW BEGIN
  IF (NEW.points > 0 AND NEW.rate_snapshot > 0 AND NEW.status IN ('reserved','consumed','released')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_point_redemptions_valid failed'; END IF;
  IF NOT (NEW.`id` <=> OLD.`id`) OR NOT (NEW.`order_id` <=> OLD.`order_id`) OR NOT (NEW.`lot_id` <=> OLD.`lot_id`) OR NOT (NEW.`points` <=> OLD.`points`) OR NOT (NEW.`rate_snapshot` <=> OLD.`rate_snapshot`) OR NOT (NEW.`rate_version` <=> OLD.`rate_version`) OR NOT (NEW.`value_snapshot` <=> OLD.`value_snapshot`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Acquisition and order snapshots are immutable'; END IF;
END$$

CREATE TRIGGER `trg_meow5_point_redemptions_bd` BEFORE DELETE ON `point_redemptions` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audited acquisitions cannot be deleted';
END$$

CREATE TRIGGER `trg_meow5_return_cases_bi` BEFORE INSERT ON `return_cases` FOR EACH ROW BEGIN
  IF (NEW.status IN ('draft','submitted','approved','return_sent','received','replacement_shipped','completed','rejected','cancelled')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_return_cases_status failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_return_cases_bu` BEFORE UPDATE ON `return_cases` FOR EACH ROW BEGIN
  IF (NEW.status IN ('draft','submitted','approved','return_sent','received','replacement_shipped','completed','rejected','cancelled')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_return_cases_status failed'; END IF;
  IF NOT (NEW.`id` <=> OLD.`id`) OR NOT (NEW.`reference` <=> OLD.`reference`) OR NOT (NEW.`order_id` <=> OLD.`order_id`) OR NOT (NEW.`user_id` <=> OLD.`user_id`) OR NOT (NEW.`reason` <=> OLD.`reason`) OR NOT (NEW.`created_at` <=> OLD.`created_at`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Acquisition and order snapshots are immutable'; END IF;
END$$

CREATE TRIGGER `trg_meow5_return_cases_bd` BEFORE DELETE ON `return_cases` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audited acquisitions cannot be deleted';
END$$

CREATE TRIGGER `trg_meow5_return_case_items_bi` BEFORE INSERT ON `return_case_items` FOR EACH ROW BEGIN
  IF (NEW.quantity > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_return_case_items_quantity failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM return_cases c WHERE c.id=NEW.case_id AND c.order_id=NEW.order_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Return item must belong to case order'; END IF;
END$$

CREATE TRIGGER `trg_meow5_return_case_items_bu` BEFORE UPDATE ON `return_case_items` FOR EACH ROW BEGIN
  IF (NEW.quantity > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_return_case_items_quantity failed'; END IF;
  IF NOT (NEW.`id` <=> OLD.`id`) OR NOT (NEW.`case_id` <=> OLD.`case_id`) OR NOT (NEW.`order_id` <=> OLD.`order_id`) OR NOT (NEW.`order_item_id` <=> OLD.`order_item_id`) OR NOT (NEW.`quantity` <=> OLD.`quantity`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Acquisition and order snapshots are immutable'; END IF;
END$$

CREATE TRIGGER `trg_meow5_return_case_items_bd` BEFORE DELETE ON `return_case_items` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audited acquisitions cannot be deleted';
END$$

CREATE TRIGGER `trg_meow5_return_evidence_bi` BEFORE INSERT ON `return_evidence` FOR EACH ROW BEGIN
  IF (NEW.byte_size > 0 AND NEW.byte_size <= 104857600 AND NEW.mime_type IN ('video/mp4','video/webm')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_return_evidence_file failed'; END IF;
END$$

CREATE TRIGGER `trg_meow5_return_evidence_bu` BEFORE UPDATE ON `return_evidence` FOR EACH ROW BEGIN
  IF (NEW.byte_size > 0 AND NEW.byte_size <= 104857600 AND NEW.mime_type IN ('video/mp4','video/webm')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_return_evidence_file failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'History is append-only';
END$$

CREATE TRIGGER `trg_meow5_return_evidence_bd` BEFORE DELETE ON `return_evidence` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'History is append-only';
END$$

CREATE TRIGGER `trg_meow5_return_timeline_bu` BEFORE UPDATE ON `return_timeline` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'History is append-only';
END$$

CREATE TRIGGER `trg_meow5_return_timeline_bd` BEFORE DELETE ON `return_timeline` FOR EACH ROW BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'History is append-only';
END$$

DELIMITER ;

UPDATE alembic_version SET version_num='20261111_0005' WHERE alembic_version.version_num = '20261110_0004';

SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;

