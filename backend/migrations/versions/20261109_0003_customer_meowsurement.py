"""Integrated customer profile, frame specification and Meowsurement schema.

Revision ID: 20261109_0003
Revises: 20261106_0002

Frozen MySQL 5.7.24-log DDL: no imports of live application metadata.
Adds 11 tables without rewriting users, prescriptions, products or old orders.
MySQL DDL commits implicitly. Back up and pause writers; stop on the first error.
"""
from __future__ import annotations
import re
from alembic import context, op
import sqlalchemy as sa

revision = "20261109_0003"
down_revision = "20261106_0002"
branch_labels = None
depends_on = None
EXPECTED_SQL_MODES = frozenset({"STRICT_TRANS_TABLES", "ERROR_FOR_DIVISION_BY_ZERO",
    "NO_ENGINE_SUBSTITUTION", "ONLY_FULL_GROUP_BY", "NO_ZERO_DATE", "NO_ZERO_IN_DATE"})

TABLE_DDL = {'product_frame_specifications': 'CREATE TABLE product_frame_specifications (\n'
                                 '\tproduct_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                                 '\ta NUMERIC(7, 2), \n'
                                 '\tb NUMERIC(7, 2), \n'
                                 '\tdbl NUMERIC(7, 2), \n'
                                 '\ted NUMERIC(7, 2), \n'
                                 '\ttemple_length NUMERIC(7, 2), \n'
                                 "\tsymmetric BOOL NOT NULL DEFAULT '0', \n"
                                 "\tenabled BOOL NOT NULL DEFAULT '0', \n"
                                 '\tsource_note TEXT, \n'
                                 "\tversion INTEGER NOT NULL DEFAULT '1', \n"
                                 '\tupdated_by VARCHAR(64) COLLATE utf8mb4_bin, \n'
                                 '\tupdated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                                 '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                                 '\tCONSTRAINT pk_product_frame_specifications PRIMARY KEY (product_id), \n'
                                 '\tCONSTRAINT fk_product_frame_specifications_product_id_products_id '
                                 'FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, \n'
                                 '\tCONSTRAINT fk_product_frame_specifications_updated_by_users_user_id '
                                 'FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT\n'
                                 ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                                 'utf8mb4_unicode_ci',
 'customer_profiles': 'CREATE TABLE customer_profiles (\n'
                      '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                      '\tphone VARCHAR(32), \n'
                      '\tbirth_date DATE, \n'
                      '\tgender VARCHAR(20), \n'
                      '\taddress TEXT, \n'
                      '\tactive_prescription_id VARCHAR(64) COLLATE utf8mb4_bin, \n'
                      '\tprescription_date DATE, \n'
                      "\tversion INTEGER NOT NULL DEFAULT '1', \n"
                      '\tupdated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                      '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                      '\tCONSTRAINT pk_customer_profiles PRIMARY KEY (user_id), \n'
                      '\tCONSTRAINT fk_customer_profiles_active_prescription_id_us_fb9a7da0b44d FOREIGN '
                      'KEY(active_prescription_id, user_id) REFERENCES prescriptions (id, user_id) ON DELETE '
                      'RESTRICT, \n'
                      '\tCONSTRAINT fk_customer_profiles_user_id_users_user_id FOREIGN KEY(user_id) '
                      'REFERENCES users (user_id) ON DELETE RESTRICT\n'
                      ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'meowsurement_sessions': 'CREATE TABLE meowsurement_sessions (\n'
                          '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                          '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                          '\tproduct_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                          '\tvariant_id VARCHAR(64) COLLATE utf8mb4_bin, \n'
                          '\tprescription_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                          '\tprofile_version INTEGER NOT NULL, \n'
                          '\tspec_version INTEGER NOT NULL, \n'
                          "\tspec_scope VARCHAR(16) NOT NULL DEFAULT 'product', \n"
                          '\texamination_date DATE NOT NULL, \n'
                          "\tstatus VARCHAR(24) NOT NULL DEFAULT 'draft', \n"
                          '\tcurrent_revision_id VARCHAR(64) COLLATE utf8mb4_bin, \n'
                          "\trevision_number INTEGER NOT NULL DEFAULT '0', \n"
                          '\talgorithm_version VARCHAR(100) NOT NULL, \n'
                          '\tprofile_snapshot JSON NOT NULL, \n'
                          '\tframe_snapshot JSON NOT NULL, \n'
                          '\tdevice JSON, \n'
                          '\tupdated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                          '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                          '\tCONSTRAINT pk_meowsurement_sessions PRIMARY KEY (id), \n'
                          '\tCONSTRAINT uq_meowsurement_sessions_id_user_id UNIQUE (id, user_id), \n'
                          '\tCONSTRAINT fk_meowsurement_sessions_product_id_variant_id_d94cf60cfd94 FOREIGN '
                          'KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON '
                          'DELETE RESTRICT, \n'
                          '\tCONSTRAINT fk_meowsurement_sessions_prescription_id_user__80515a965ad8 FOREIGN '
                          'KEY(prescription_id, user_id) REFERENCES prescriptions (id, user_id) ON DELETE '
                          'RESTRICT, \n'
                          '\tCONSTRAINT fk_meowsurement_sessions_user_id_users_user_id FOREIGN KEY(user_id) '
                          'REFERENCES users (user_id) ON DELETE RESTRICT, \n'
                          '\tCONSTRAINT fk_meowsurement_sessions_product_id_products_id FOREIGN '
                          'KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT\n'
                          ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'product_variant_frame_specifications': 'CREATE TABLE product_variant_frame_specifications (\n'
                                         '\tvariant_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                                         '\tproduct_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                                         '\ta NUMERIC(7, 2), \n'
                                         '\tb NUMERIC(7, 2), \n'
                                         '\tdbl NUMERIC(7, 2), \n'
                                         '\ted NUMERIC(7, 2), \n'
                                         '\ttemple_length NUMERIC(7, 2), \n'
                                         "\tsymmetric BOOL NOT NULL DEFAULT '0', \n"
                                         "\tenabled BOOL NOT NULL DEFAULT '0', \n"
                                         '\tsource_note TEXT, \n'
                                         "\tversion INTEGER NOT NULL DEFAULT '1', \n"
                                         '\tupdated_by VARCHAR(64) COLLATE utf8mb4_bin, \n'
                                         '\tupdated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                                         '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                                         '\tCONSTRAINT pk_product_variant_frame_specifications PRIMARY KEY '
                                         '(variant_id), \n'
                                         '\tCONSTRAINT '
                                         'fk_product_variant_frame_specifications_produc_c29aa19f0cb2 '
                                         'FOREIGN KEY(product_id, variant_id) REFERENCES product_variants '
                                         '(product_id, id) ON DELETE CASCADE, \n'
                                         '\tCONSTRAINT '
                                         'fk_product_variant_frame_specifications_update_133a0245692d '
                                         'FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE '
                                         'RESTRICT\n'
                                         ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                                         'utf8mb4_unicode_ci',
 'meowsurement_photos': 'CREATE TABLE meowsurement_photos (\n'
                        '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                        '\tsession_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                        '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                        '\tstorage_path VARCHAR(500) NOT NULL, \n'
                        '\tsha256 VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                        '\tsource_sha256 VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                        '\tmime_type VARCHAR(32) NOT NULL, \n'
                        '\twidth INTEGER NOT NULL, \n'
                        '\theight INTEGER NOT NULL, \n'
                        '\tbyte_size INTEGER NOT NULL, \n'
                        '\tconsent BOOL NOT NULL, \n'
                        '\texpires_at DATETIME(6) NOT NULL, \n'
                        '\tdeleted_at DATETIME(6), \n'
                        '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                        '\tCONSTRAINT pk_meowsurement_photos PRIMARY KEY (id), \n'
                        '\tCONSTRAINT uq_meowsurement_photos_session_id_user_id_id UNIQUE (session_id, '
                        'user_id, id), \n'
                        '\tCONSTRAINT fk_meowsurement_photos_session_id_user_id_meow_ff3248b1d22e FOREIGN '
                        'KEY(session_id, user_id) REFERENCES meowsurement_sessions (id, user_id) ON DELETE '
                        'RESTRICT\n'
                        ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'meowsurement_revisions': 'CREATE TABLE meowsurement_revisions (\n'
                           '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                           '\tsession_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                           '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                           '\trevision_number INTEGER NOT NULL, \n'
                           '\tparent_revision_id VARCHAR(64) COLLATE utf8mb4_bin, \n'
                           '\tdata JSON NOT NULL, \n'
                           '\treason TEXT NOT NULL, \n'
                           '\tactor_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                           '\talgorithm_version VARCHAR(100), \n'
                           '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                           '\tCONSTRAINT pk_meowsurement_revisions PRIMARY KEY (id), \n'
                           '\tCONSTRAINT uq_meowsurement_revisions_session_id_user_id_id UNIQUE (session_id, '
                           'user_id, id), \n'
                           '\tCONSTRAINT uq_meowsurement_revisions_session_id_revision_number UNIQUE '
                           '(session_id, revision_number), \n'
                           '\tCONSTRAINT uq_meowsurement_revisions_id_session_id_user_id UNIQUE (id, '
                           'session_id, user_id), \n'
                           '\tCONSTRAINT fk_meowsurement_revisions_session_id_user_id_m_38fd2ad9d211 FOREIGN '
                           'KEY(session_id, user_id) REFERENCES meowsurement_sessions (id, user_id) ON '
                           'DELETE RESTRICT, \n'
                           '\tCONSTRAINT fk_meowsurement_revisions_session_id_user_id_p_7c6c199459bd FOREIGN '
                           'KEY(session_id, user_id, parent_revision_id) REFERENCES meowsurement_revisions '
                           '(session_id, user_id, id) ON DELETE RESTRICT, \n'
                           '\tCONSTRAINT fk_meowsurement_revisions_actor_id_users_user_id FOREIGN '
                           'KEY(actor_id) REFERENCES users (user_id) ON DELETE RESTRICT\n'
                           ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'meowsurement_audit_events': 'CREATE TABLE meowsurement_audit_events (\n'
                              '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                              '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                              '\tsession_id VARCHAR(64) COLLATE utf8mb4_bin, \n'
                              '\trevision_id VARCHAR(64) COLLATE utf8mb4_bin, \n'
                              '\tactor_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                              '\taction VARCHAR(64) NOT NULL, \n'
                              '\tdetails JSON, \n'
                              '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                              '\tCONSTRAINT pk_meowsurement_audit_events PRIMARY KEY (id), \n'
                              '\tCONSTRAINT fk_meowsurement_audit_events_session_id_user_i_19b9300e0f0e '
                              'FOREIGN KEY(session_id, user_id) REFERENCES meowsurement_sessions (id, '
                              'user_id) ON DELETE RESTRICT, \n'
                              '\tCONSTRAINT fk_meowsurement_audit_events_revision_id_sessi_09038f20c82f '
                              'FOREIGN KEY(revision_id, session_id, user_id) REFERENCES '
                              'meowsurement_revisions (id, session_id, user_id) ON DELETE RESTRICT, \n'
                              '\tCONSTRAINT fk_meowsurement_audit_events_user_id_users_user_id FOREIGN '
                              'KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, \n'
                              '\tCONSTRAINT fk_meowsurement_audit_events_actor_id_users_user_id FOREIGN '
                              'KEY(actor_id) REFERENCES users (user_id) ON DELETE RESTRICT\n'
                              ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'meowsurement_captures': 'CREATE TABLE meowsurement_captures (\n'
                          '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                          '\trevision_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                          '\tsession_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                          '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                          '\tcapture_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                          '\tview VARCHAR(32) NOT NULL, \n'
                          '\tphoto_id VARCHAR(64) COLLATE utf8mb4_bin, \n'
                          '\tphoto_hash VARCHAR(64) COLLATE utf8mb4_bin, \n'
                          '\twidth INTEGER NOT NULL, \n'
                          '\theight INTEGER NOT NULL, \n'
                          '\tcaptured_at DATETIME(6), \n'
                          '\tcalibration JSON, \n'
                          '\tlandmarks JSON, \n'
                          '\tquality JSON, \n'
                          '\tdata JSON NOT NULL, \n'
                          '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                          '\tCONSTRAINT pk_meowsurement_captures PRIMARY KEY (id), \n'
                          '\tCONSTRAINT uq_meowsurement_captures_revision_id_capture_id UNIQUE (revision_id, '
                          'capture_id), \n'
                          '\tCONSTRAINT uq_meowsurement_captures_revision_id_id UNIQUE (revision_id, id), \n'
                          '\tCONSTRAINT fk_meowsurement_captures_revision_id_session_i_57d34702e9be FOREIGN '
                          'KEY(revision_id, session_id, user_id) REFERENCES meowsurement_revisions (id, '
                          'session_id, user_id) ON DELETE RESTRICT, \n'
                          '\tCONSTRAINT fk_meowsurement_captures_session_id_user_id_ph_3ff910ad9b57 FOREIGN '
                          'KEY(session_id, user_id, photo_id) REFERENCES meowsurement_photos (session_id, '
                          'user_id, id) ON DELETE RESTRICT\n'
                          ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'meowsurement_measurements': 'CREATE TABLE meowsurement_measurements (\n'
                              '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                              '\trevision_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                              '\tsession_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                              '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                              '\tparameter VARCHAR(32) NOT NULL, \n'
                              '\tside VARCHAR(8), \n'
                              '\tunit VARCHAR(8) NOT NULL, \n'
                              '\tmethod VARCHAR(100) NOT NULL, \n'
                              '\talgorithm_version VARCHAR(100) NOT NULL, \n'
                              '\tvalid BOOL NOT NULL, \n'
                              '\t`values` JSON NOT NULL, \n'
                              '\tquality JSON, \n'
                              '\tdata JSON NOT NULL, \n'
                              '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                              '\tCONSTRAINT pk_meowsurement_measurements PRIMARY KEY (id), \n'
                              '\tCONSTRAINT uq_meowsurement_measurements_revision_id_parameter UNIQUE '
                              '(revision_id, parameter), \n'
                              '\tCONSTRAINT uq_meowsurement_measurements_revision_id_id UNIQUE (revision_id, '
                              'id), \n'
                              '\tCONSTRAINT fk_meowsurement_measurements_revision_id_sessi_fc78e521e3a2 '
                              'FOREIGN KEY(revision_id, session_id, user_id) REFERENCES '
                              'meowsurement_revisions (id, session_id, user_id) ON DELETE RESTRICT\n'
                              ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'meowsurement_reviews': 'CREATE TABLE meowsurement_reviews (\n'
                         '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                         '\tsession_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                         '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                         '\trevision_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                         '\treviewer_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                         '\tdecision VARCHAR(24) NOT NULL, \n'
                         '\tnote TEXT NOT NULL, \n'
                         '\tevidence JSON NOT NULL, \n'
                         '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                         '\tCONSTRAINT pk_meowsurement_reviews PRIMARY KEY (id), \n'
                         '\tCONSTRAINT fk_meowsurement_reviews_revision_id_session_id_3821c201c3bb FOREIGN '
                         'KEY(revision_id, session_id, user_id) REFERENCES meowsurement_revisions (id, '
                         'session_id, user_id) ON DELETE RESTRICT, \n'
                         '\tCONSTRAINT fk_meowsurement_reviews_reviewer_id_users_user_id FOREIGN '
                         'KEY(reviewer_id) REFERENCES users (user_id) ON DELETE RESTRICT\n'
                         ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'meowsurement_measurement_sources': 'CREATE TABLE meowsurement_measurement_sources (\n'
                                     '\tmeasurement_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                                     '\tcapture_row_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                                     '\trevision_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                                     '\tCONSTRAINT pk_meowsurement_measurement_sources PRIMARY KEY '
                                     '(measurement_id, capture_row_id), \n'
                                     '\tCONSTRAINT '
                                     'fk_meowsurement_measurement_sources_revision_i_22aced642967 FOREIGN '
                                     'KEY(revision_id, measurement_id) REFERENCES meowsurement_measurements '
                                     '(revision_id, id) ON DELETE RESTRICT, \n'
                                     '\tCONSTRAINT '
                                     'fk_meowsurement_measurement_sources_revision_i_8050f78eb3c8 FOREIGN '
                                     'KEY(revision_id, capture_row_id) REFERENCES meowsurement_captures '
                                     '(revision_id, id) ON DELETE RESTRICT\n'
                                     ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                                     'utf8mb4_unicode_ci'}
INDEX_DDL = ['CREATE INDEX ix_meowsurement_review_queue ON meowsurement_sessions (status, updated_at, id)',
 'CREATE INDEX ix_meowsurement_user_history ON meowsurement_sessions (user_id, created_at, id)',
 'CREATE INDEX ix_variant_frame_specs_product ON product_variant_frame_specifications (product_id)',
 'CREATE INDEX ix_meowsurement_photo_retention ON meowsurement_photos (deleted_at, expires_at)',
 'CREATE INDEX ix_meowsurement_revision_actor ON meowsurement_revisions (actor_id, created_at)',
 'CREATE INDEX ix_meowsurement_audit_owner ON meowsurement_audit_events (user_id, created_at, id)',
 'CREATE INDEX ix_meowsurement_reviews_session ON meowsurement_reviews (session_id, created_at)']
DEFERRED_DDL = ['ALTER TABLE meowsurement_sessions ADD CONSTRAINT fk_meowsurement_current_revision FOREIGN KEY(id, user_id, '
 'current_revision_id) REFERENCES meowsurement_revisions (session_id, user_id, id) ON DELETE RESTRICT']
ALL_TABLES = tuple(TABLE_DDL)
RULES = {'product_frame_specifications': (('ck_product_frame_specifications_dimensions',
                                   '(`a` IS NULL OR `a` > 0) AND (`b` IS NULL OR `b` > 0) AND (`dbl` IS NULL '
                                   'OR `dbl` > 0) AND (`ed` IS NULL OR `ed` > 0) AND (`temple_length` IS '
                                   'NULL OR `temple_length` > 0)',
                                   '(NEW.`a` IS NULL OR NEW.`a` > 0) AND (NEW.`b` IS NULL OR NEW.`b` > 0) '
                                   'AND (NEW.`dbl` IS NULL OR NEW.`dbl` > 0) AND (NEW.`ed` IS NULL OR '
                                   'NEW.`ed` > 0) AND (NEW.`temple_length` IS NULL OR NEW.`temple_length` > '
                                   '0)'),
                                  ('ck_product_frame_specifications_flags',
                                   '`symmetric` IN (0,1) AND `enabled` IN (0,1)',
                                   'NEW.`symmetric` IN (0,1) AND NEW.`enabled` IN (0,1)'),
                                  ('ck_product_frame_specifications_version',
                                   '`version` > 0',
                                   'NEW.`version` > 0')),
 'customer_profiles': (('ck_customer_profiles_gender',
                        "`gender` IS NULL OR `gender` IN ('male','female','unspecified')",
                        "NEW.`gender` IS NULL OR NEW.`gender` IN ('male','female','unspecified')"),
                       ('ck_customer_profiles_version', '`version` > 0', 'NEW.`version` > 0')),
 'meowsurement_sessions': (('ck_meowsurement_sessions_spec_scope',
                            "`spec_scope` IN ('product','variant')",
                            "NEW.`spec_scope` IN ('product','variant')"),
                           ('ck_meowsurement_sessions_status',
                            '`status` IN '
                            "('draft','pending_review','needs_verification','needs_remeasure','approved')",
                            'NEW.`status` IN '
                            "('draft','pending_review','needs_verification','needs_remeasure','approved')"),
                           ('ck_meowsurement_sessions_versions',
                            '`profile_version` > 0 AND `spec_version` > 0 AND `revision_number` >= 0',
                            'NEW.`profile_version` > 0 AND NEW.`spec_version` > 0 AND NEW.`revision_number` '
                            '>= 0')),
 'product_variant_frame_specifications': (('ck_product_variant_frame_specifications_dimensions',
                                           '(`a` IS NULL OR `a` > 0) AND (`b` IS NULL OR `b` > 0) AND (`dbl` '
                                           'IS NULL OR `dbl` > 0) AND (`ed` IS NULL OR `ed` > 0) AND '
                                           '(`temple_length` IS NULL OR `temple_length` > 0)',
                                           '(NEW.`a` IS NULL OR NEW.`a` > 0) AND (NEW.`b` IS NULL OR NEW.`b` '
                                           '> 0) AND (NEW.`dbl` IS NULL OR NEW.`dbl` > 0) AND (NEW.`ed` IS '
                                           'NULL OR NEW.`ed` > 0) AND (NEW.`temple_length` IS NULL OR '
                                           'NEW.`temple_length` > 0)'),
                                          ('ck_product_variant_frame_specifications_flags',
                                           '`symmetric` IN (0,1) AND `enabled` IN (0,1)',
                                           'NEW.`symmetric` IN (0,1) AND NEW.`enabled` IN (0,1)'),
                                          ('ck_product_variant_frame_specifications_version',
                                           '`version` > 0',
                                           'NEW.`version` > 0')),
 'meowsurement_photos': (('ck_meowsurement_photos_consent', '`consent` = 1', 'NEW.`consent` = 1'),
                         ('ck_meowsurement_photos_dimensions',
                          '`width` > 0 AND `height` > 0 AND `width` * `height` <= 20000000',
                          'NEW.`width` > 0 AND NEW.`height` > 0 AND NEW.`width` * NEW.`height` <= 20000000'),
                         ('ck_meowsurement_photos_mime',
                          "`mime_type` IN ('image/jpeg','image/png','image/webp')",
                          "NEW.`mime_type` IN ('image/jpeg','image/png','image/webp')"),
                         ('ck_meowsurement_photos_size',
                          '`byte_size` > 0 AND `byte_size` <= 8388608',
                          'NEW.`byte_size` > 0 AND NEW.`byte_size` <= 8388608')),
 'meowsurement_revisions': (('ck_meowsurement_revisions_number',
                             '`revision_number` > 0',
                             'NEW.`revision_number` > 0'),
                            ('ck_meowsurement_revisions_parent',
                             '`parent_revision_id` IS NULL OR `parent_revision_id` <> `id`',
                             'NEW.`parent_revision_id` IS NULL OR NEW.`parent_revision_id` <> NEW.`id`')),
 'meowsurement_audit_events': (('ck_meowsurement_audit_events_revision_owner',
                                '`revision_id` IS NULL OR `session_id` IS NOT NULL',
                                'NEW.`revision_id` IS NULL OR NEW.`session_id` IS NOT NULL'),),
 'meowsurement_captures': (('ck_meowsurement_captures_dimensions',
                            '`width` > 0 AND `height` > 0 AND `width` * `height` <= 20000000',
                            'NEW.`width` > 0 AND NEW.`height` > 0 AND NEW.`width` * NEW.`height` <= '
                            '20000000'),
                           ('ck_meowsurement_captures_view',
                            '`view` IN '
                            "('frontal','frontal_near','three_quarter_left','three_quarter_right','lateral_left','lateral_right')",
                            'NEW.`view` IN '
                            "('frontal','frontal_near','three_quarter_left','three_quarter_right','lateral_left','lateral_right')")),
 'meowsurement_measurements': (('ck_meowsurement_measurements_parameter',
                                '`parameter` IN '
                                "('distance_pd','near_pd','vertex_right','vertex_left','pantoscopic_right','pantoscopic_left','wrap_right','wrap_left')",
                                'NEW.`parameter` IN '
                                "('distance_pd','near_pd','vertex_right','vertex_left','pantoscopic_right','pantoscopic_left','wrap_right','wrap_left')"),
                               ('ck_meowsurement_measurements_side',
                                "`side` IS NULL OR `side` IN ('right','left','both')",
                                "NEW.`side` IS NULL OR NEW.`side` IN ('right','left','both')"),
                               ('ck_meowsurement_measurements_unit_valid',
                                "`unit` IN ('mm','deg') AND `valid` IN (0,1)",
                                "NEW.`unit` IN ('mm','deg') AND NEW.`valid` IN (0,1)")),
 'meowsurement_reviews': (('ck_meowsurement_reviews_decision',
                           "`decision` IN ('approved','needs_verification','needs_remeasure')",
                           "NEW.`decision` IN ('approved','needs_verification','needs_remeasure')"),
                          ('ck_meowsurement_reviews_independent',
                           '`reviewer_id` <> `user_id`',
                           'NEW.`reviewer_id` <> NEW.`user_id`'))}

IMMUTABLE = frozenset({"meowsurement_revisions", "meowsurement_captures",
    "meowsurement_measurements", "meowsurement_measurement_sources",
    "meowsurement_reviews", "meowsurement_audit_events"})

def quoted(name: str) -> str:
    return chr(96) + name + chr(96)

def reject(message: str) -> str:
    return "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '" + message + "';"

def custom_checks(table: str, event: str) -> list[str]:
    checks = []
    if table in {"product_frame_specifications", "product_variant_frame_specifications"}:
        checks.append("IF NOT EXISTS (SELECT 1 FROM products WHERE id = NEW.product_id AND product_type = 'frame') THEN "
                      + reject("Frame specification requires a frame product") + " END IF;")
    if table == "meowsurement_sessions":
        if event == "UPDATE":
            fields = ["id", "user_id", "product_id", "variant_id", "prescription_id", "profile_version",
                      "spec_version", "spec_scope", "examination_date", "profile_snapshot", "frame_snapshot",
                      "algorithm_version", "created_at"]
            checks.append("IF " + " OR ".join("NOT (NEW." + quoted(f) + " <=> OLD." + quoted(f) + ")" for f in fields)
                          + " THEN " + reject("Measurement source snapshots are immutable") + " END IF;")
        checks.append("IF NEW.status <> 'draft' AND NEW.current_revision_id IS NULL THEN "
                      + reject("A submitted measurement requires a revision") + " END IF;")
        checks.append("IF (NEW.current_revision_id IS NULL AND NEW.revision_number <> 0) OR "
                      "(NEW.current_revision_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM meowsurement_revisions "
                      "WHERE id = NEW.current_revision_id AND session_id = NEW.id AND user_id = NEW.user_id "
                      "AND revision_number = NEW.revision_number)) THEN "
                      + reject("Current revision pointer and number must agree") + " END IF;")
        checks.append("IF NEW.status = 'approved' AND NOT EXISTS (SELECT 1 FROM meowsurement_reviews "
                      "WHERE session_id = NEW.id AND user_id = NEW.user_id AND revision_id = NEW.current_revision_id "
                      "AND decision = 'approved' AND reviewer_id <> NEW.user_id) THEN "
                      + reject("Approval requires an independent stored review") + " END IF;")
    if table == "meowsurement_revisions" and event == "INSERT":
        checks.append("IF (NEW.revision_number = 1 AND NEW.parent_revision_id IS NOT NULL) OR "
                      "(NEW.revision_number > 1 AND NOT EXISTS (SELECT 1 FROM meowsurement_revisions "
                      "WHERE id = NEW.parent_revision_id AND session_id = NEW.session_id AND user_id = NEW.user_id "
                      "AND revision_number = NEW.revision_number - 1)) THEN "
                      + reject("Revision parent sequence is invalid") + " END IF;")
    if table == "meowsurement_reviews" and event == "INSERT":
        checks.append("IF NOT EXISTS (SELECT 1 FROM users u WHERE u.user_id = NEW.reviewer_id AND u.is_active = 1 "
                      "AND (u.role IN ('admin','super_admin') OR (u.role = 'staff' AND EXISTS "
                      "(SELECT 1 FROM user_permissions p WHERE p.user_id = u.user_id "
                      "AND p.permission = 'meowsurement.review')))) THEN "
                      + reject("An active authorized web reviewer is required") + " END IF;")
        checks.append("IF NOT EXISTS (SELECT 1 FROM meowsurement_sessions s JOIN meowsurement_revisions r "
                      "ON r.id = s.current_revision_id AND r.session_id = s.id AND r.user_id = s.user_id "
                      "WHERE s.id = NEW.session_id AND s.user_id = NEW.user_id AND r.id = NEW.revision_id "
                      "AND s.status IN ('pending_review','needs_verification') "
                      "AND r.actor_id <> NEW.reviewer_id AND s.user_id <> NEW.reviewer_id) THEN "
                      + reject("Review requires the current independent revision") + " END IF;")
    if table == "meowsurement_photos" and event == "UPDATE":
        fields = ["id", "user_id", "session_id", "storage_path", "sha256", "source_sha256",
                  "mime_type", "width", "height", "byte_size", "consent", "created_at"]
        checks.append("IF " + " OR ".join("NOT (NEW." + quoted(f) + " <=> OLD." + quoted(f) + ")" for f in fields)
                      + " THEN " + reject("Private photo provenance is immutable") + " END IF;")
        checks.append("IF OLD.deleted_at IS NOT NULL AND NEW.deleted_at IS NULL THEN "
                      + reject("A deleted private photo cannot be reactivated") + " END IF;")
    return checks

def trigger_definitions() -> dict[str, dict]:
    definitions = {}
    for table in ALL_TABLES:
        for event, suffix in (("INSERT","bi"), ("UPDATE","bu"), ("DELETE","bd")):
            lines = []
            if event in {"INSERT", "UPDATE"}:
                for rule_name, _, predicate in RULES.get(table, ()):
                    lines.append("IF (" + predicate + ") IS FALSE THEN " + reject("Rule " + rule_name + " failed") + " END IF;")
                lines.extend(custom_checks(table, event))
            if table in IMMUTABLE and event in {"UPDATE", "DELETE"}:
                lines.append(reject("Measurement history is append-only"))
            if not lines:
                continue
            name = "trg_meow3_" + table + "_" + suffix
            body = "BEGIN\n  " + "\n  ".join(lines) + "\nEND"
            definitions[name] = {"table": table, "event": event, "timing": "BEFORE", "body": body,
                "sql": "CREATE TRIGGER " + quoted(name) + " BEFORE " + event + " ON " + quoted(table) + "\nFOR EACH ROW\n" + body}
    return definitions

def canonical_body(body: str) -> tuple[str, ...]:
    tokens = re.findall(r"'(?:''|[^'])*'|\x60(?:\x60\x60|[^\x60])*\x60|[A-Za-z_][A-Za-z_0-9]*|\d+(?:\.\d+)?|[^\s]", body)
    return tuple(token if token.startswith("'") else token.strip(chr(96)).lower() for token in tokens)

def table_issues(connection) -> list[str]:
    rows = connection.execute(sa.text(
        "SELECT TABLE_NAME AS table_name, ENGINE AS engine, ROW_FORMAT AS row_format "
        "FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()")).mappings()
    actual = {row["table_name"]: row for row in rows}
    issues = []
    for table in ALL_TABLES:
        row = actual.get(table)
        if row is None:
            issues.append("missing_table:" + table)
        elif str(row["engine"]).lower() != "innodb" or str(row["row_format"]).lower() != "dynamic":
            issues.append("table_storage_mismatch:" + table)
    return issues

def row_issues(connection) -> list[str]:
    issues = []
    for table, rules in RULES.items():
        where = " OR ".join("(" + predicate + ") IS FALSE" for _, predicate, _ in rules)
        if connection.exec_driver_sql("SELECT 1 FROM " + quoted(table) + " WHERE " + where + " LIMIT 1").first():
            issues.append("row_rule_violation:" + table)
    return issues

def trigger_issues(connection) -> list[str]:
    rows = connection.execute(sa.text(
        "SELECT TRIGGER_NAME AS name, EVENT_MANIPULATION AS event, EVENT_OBJECT_TABLE AS table_name, "
        "ACTION_TIMING AS timing, ACTION_STATEMENT AS body, SQL_MODE AS sql_mode, ACTION_ORDER AS action_order "
        "FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE()")).mappings()
    actual = {row["name"]: dict(row) for row in rows}
    issues = []
    for name, expected in trigger_definitions().items():
        row = actual.get(name)
        if row is None:
            issues.append("missing_trigger:" + name)
        elif (row["table_name"] != expected["table"] or row["event"] != expected["event"]
              or row["timing"] != "BEFORE" or canonical_body(row["body"]) != canonical_body(expected["body"])):
            issues.append("trigger_definition_mismatch:" + name)
        else:
            modes = {value.strip().upper() for value in row["sql_mode"].split(",") if value.strip()}
            if modes != EXPECTED_SQL_MODES:
                issues.append("trigger_sql_mode_mismatch:" + name)
            last = max(int(other["action_order"]) for other in actual.values()
                       if other["table_name"] == row["table_name"] and other["event"] == row["event"]
                       and other["timing"] == "BEFORE")
            if int(row["action_order"]) != last:
                issues.append("trigger_not_last:" + name)
    return issues

def upgrade() -> None:
    if context.is_offline_mode():
        output = op.get_context().impl.static_output
        output("-- Adds customer-owned Meowsurement. Back up and pause writers; DDL commits implicitly.")
        output("-- Stop on first error. Never use mysql --force or stamp an incomplete migration.")
        for sql in [*TABLE_DDL.values(), *INDEX_DDL, *DEFERRED_DDL]:
            output(sql + ";")
        output("DELIMITER $$")
        for definition in trigger_definitions().values():
            output(definition["sql"] + "$$")
        output("DELIMITER ;")
        return
    connection = op.get_bind()
    # New tables are deliberately not silently overwritten/replaced on a retry.
    existing = set(sa.inspect(connection).get_table_names())
    overlap = existing.intersection(ALL_TABLES)
    if overlap:
        raise RuntimeError("Meowsurement tables already exist; review partial migration before retry: " + ", ".join(sorted(overlap)))
    for sql in [*TABLE_DDL.values(), *INDEX_DDL, *DEFERRED_DDL]:
        connection.exec_driver_sql(sql)
    for definition in trigger_definitions().values():
        connection.exec_driver_sql(definition["sql"])
    issues = table_issues(connection) + row_issues(connection) + trigger_issues(connection)
    if issues:
        raise RuntimeError("Meowsurement migration verification failed: " + ", ".join(issues))

def downgrade() -> None:
    if not context.is_offline_mode() and context.get_x_argument(as_dictionary=True).get("allow_schema_drop") != "true":
        raise RuntimeError("Dropping measurement records requires -x allow_schema_drop=true on a disposable/restored target only.")
    for name in reversed(trigger_definitions()):
        op.execute(sa.text("DROP TRIGGER IF EXISTS " + quoted(name)))
    op.execute(sa.text("ALTER TABLE meowsurement_sessions DROP FOREIGN KEY fk_meowsurement_current_revision"))
    for table in reversed(ALL_TABLES):
        op.execute(sa.text("DROP TABLE " + quoted(table)))
