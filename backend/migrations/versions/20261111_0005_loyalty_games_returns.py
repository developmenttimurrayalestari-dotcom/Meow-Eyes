"""Versioned point wallet, verified games, cashback and private replacement RMA.
Frozen MySQL 5.7 DDL. Back up and pause writers before upgrade; DDL commits.
"""
import re
from alembic import context, op
import sqlalchemy as sa
revision = '20261111_0005'
down_revision = '20261110_0004'
branch_labels = depends_on = None
EXPECTED_SQL_MODES = frozenset({'STRICT_TRANS_TABLES','ERROR_FOR_DIVISION_BY_ZERO','NO_ENGINE_SUBSTITUTION','ONLY_FULL_GROUP_BY','NO_ZERO_DATE','NO_ZERO_IN_DATE'})
TABLE_DDL = {'cashback_events': 'CREATE TABLE cashback_events (\n'
                    '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                    '\tname VARCHAR(160) NOT NULL, \n'
                    '\tstart_at DATETIME(6) NOT NULL, \n'
                    '\tend_at DATETIME(6) NOT NULL, \n'
                    '\tpercent NUMERIC(7, 4) NOT NULL, \n'
                    '\texpiry_days INTEGER NOT NULL, \n'
                    '\tis_active BOOL NOT NULL, \n'
                    '\tCONSTRAINT pk_cashback_events PRIMARY KEY (id)\n'
                    ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                    'utf8mb4_unicode_ci',
 'point_settings': 'CREATE TABLE point_settings (\n'
                   '\tid VARCHAR(16) NOT NULL, \n'
                   '\trate NUMERIC(18, 4) NOT NULL, \n'
                   '\tversion INTEGER NOT NULL, \n'
                   '\tcashback_valuation VARCHAR(16) NOT NULL, \n'
                   '\tupdated_at DATETIME(6) NOT NULL, \n'
                   '\tCONSTRAINT pk_point_settings PRIMARY KEY (id)\n'
                   ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                   'utf8mb4_unicode_ci',
 'puzzle_levels': 'CREATE TABLE puzzle_levels (\n'
                  '\tlevel INTEGER NOT NULL, \n'
                  '\t`rows` INTEGER NOT NULL, \n'
                  '\tcolumns INTEGER NOT NULL, \n'
                  '\timage_url TEXT NOT NULL, \n'
                  '\tis_active BOOL NOT NULL, \n'
                  '\tCONSTRAINT pk_puzzle_levels PRIMARY KEY (level)\n'
                  ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                  'utf8mb4_unicode_ci',
 'game_rules': 'CREATE TABLE game_rules (\n'
               '\tgame_key VARCHAR(32) NOT NULL, \n'
               '\tengine VARCHAR(32) NOT NULL, \n'
               '\tcooldown_seconds INTEGER NOT NULL, \n'
               '\texpiry_days INTEGER NOT NULL, \n'
               '\tmax_duration_seconds INTEGER NOT NULL, \n'
               '\tmax_points INTEGER NOT NULL, \n'
               '\tpoints_per_unit INTEGER NOT NULL, \n'
               '\tCONSTRAINT pk_game_rules PRIMARY KEY (game_key), \n'
               '\tCONSTRAINT fk_game_rules_game_key_games_key FOREIGN '
               'KEY(game_key) REFERENCES games (`key`) ON DELETE RESTRICT\n'
               ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
               'utf8mb4_unicode_ci',
 'game_sessions': 'CREATE TABLE game_sessions (\n'
                  '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                  '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                  '\tgame_key VARCHAR(32) NOT NULL, \n'
                  '\tactive_slot VARCHAR(191) COLLATE utf8mb4_bin, \n'
                  '\tseed BIGINT NOT NULL, \n'
                  '\tsnapshot JSON NOT NULL, \n'
                  '\ttranscript JSON, \n'
                  '\tstatus VARCHAR(16) NOT NULL, \n'
                  '\tscore INTEGER NOT NULL, \n'
                  '\tpoints_awarded INTEGER NOT NULL, \n'
                  '\tstarted_at DATETIME(6) NOT NULL, \n'
                  '\tcompleted_at DATETIME(6), \n'
                  '\texpires_at DATETIME(6) NOT NULL, \n'
                  '\tCONSTRAINT pk_game_sessions PRIMARY KEY (id), \n'
                  '\tCONSTRAINT fk_game_sessions_user_id_users_user_id FOREIGN '
                  'KEY(user_id) REFERENCES users (user_id) ON DELETE '
                  'RESTRICT, \n'
                  '\tCONSTRAINT fk_game_sessions_game_key_games_key FOREIGN '
                  'KEY(game_key) REFERENCES games (`key`) ON DELETE '
                  'RESTRICT, \n'
                  '\tCONSTRAINT uq_game_sessions_active_slot UNIQUE '
                  '(active_slot)\n'
                  ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                  'utf8mb4_unicode_ci',
 'point_lots': 'CREATE TABLE point_lots (\n'
               '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
               '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
               '\taward_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL, \n'
               '\tsource VARCHAR(32) NOT NULL, \n'
               '\tearned BIGINT NOT NULL, \n'
               '\tremaining BIGINT NOT NULL, \n'
               '\trate_snapshot NUMERIC(18, 4) NOT NULL, \n'
               '\trate_version INTEGER NOT NULL, \n'
               '\tvaluation VARCHAR(16) NOT NULL, \n'
               '\texpires_at DATETIME(6), \n'
               '\tcreated_at DATETIME(6) NOT NULL, \n'
               '\tCONSTRAINT pk_point_lots PRIMARY KEY (id), \n'
               '\tCONSTRAINT fk_point_lots_user_id_users_user_id FOREIGN '
               'KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, \n'
               '\tCONSTRAINT uq_point_lots_award_key UNIQUE (award_key)\n'
               ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
               'utf8mb4_unicode_ci',
 'point_rate_versions': 'CREATE TABLE point_rate_versions (\n'
                        '\tversion INTEGER NOT NULL, \n'
                        '\trate NUMERIC(18, 4) NOT NULL, \n'
                        '\tcashback_valuation VARCHAR(16) NOT NULL, \n'
                        '\tactor_id VARCHAR(64) COLLATE utf8mb4_bin, \n'
                        '\tcreated_at DATETIME(6) NOT NULL, \n'
                        '\tCONSTRAINT pk_point_rate_versions PRIMARY KEY '
                        '(version), \n'
                        '\tCONSTRAINT '
                        'fk_point_rate_versions_actor_id_users_user_id FOREIGN '
                        'KEY(actor_id) REFERENCES users (user_id) ON DELETE '
                        'RESTRICT\n'
                        ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC '
                        'COLLATE utf8mb4_unicode_ci',
 'cashback_awards': 'CREATE TABLE cashback_awards (\n'
                    '\torder_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                    '\tevent_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                    '\tsnapshot JSON NOT NULL, \n'
                    '\tamount NUMERIC(18, 2) NOT NULL, \n'
                    '\trate_snapshot NUMERIC(18, 4) NOT NULL, \n'
                    '\tpoints BIGINT NOT NULL, \n'
                    '\tcredited_at DATETIME(6), \n'
                    '\tCONSTRAINT pk_cashback_awards PRIMARY KEY (order_id), \n'
                    '\tCONSTRAINT fk_cashback_awards_order_id_orders_id '
                    'FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE '
                    'RESTRICT, \n'
                    '\tCONSTRAINT '
                    'fk_cashback_awards_event_id_cashback_events_id FOREIGN '
                    'KEY(event_id) REFERENCES cashback_events (id) ON DELETE '
                    'RESTRICT\n'
                    ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                    'utf8mb4_unicode_ci',
 'point_history': 'CREATE TABLE point_history (\n'
                  '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                  '\tevent_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL, \n'
                  '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                  '\tlot_id VARCHAR(64) COLLATE utf8mb4_bin, \n'
                  '\torder_id VARCHAR(64) COLLATE utf8mb4_bin, \n'
                  '\tsource VARCHAR(64) NOT NULL, \n'
                  '\tdelta BIGINT NOT NULL, \n'
                  '\tbalance_after BIGINT NOT NULL, \n'
                  '\trate_snapshot NUMERIC(18, 4) NOT NULL, \n'
                  '\trate_version INTEGER NOT NULL, \n'
                  '\tvalue_snapshot NUMERIC(18, 2) NOT NULL, \n'
                  '\texpires_at DATETIME(6), \n'
                  '\tnote TEXT NOT NULL, \n'
                  '\tcreated_at DATETIME(6) NOT NULL, \n'
                  '\tCONSTRAINT pk_point_history PRIMARY KEY (id), \n'
                  '\tCONSTRAINT uq_point_history_event_key UNIQUE '
                  '(event_key), \n'
                  '\tCONSTRAINT fk_point_history_user_id_users_user_id FOREIGN '
                  'KEY(user_id) REFERENCES users (user_id) ON DELETE '
                  'RESTRICT, \n'
                  '\tCONSTRAINT fk_point_history_lot_id_point_lots_id FOREIGN '
                  'KEY(lot_id) REFERENCES point_lots (id) ON DELETE '
                  'RESTRICT, \n'
                  '\tCONSTRAINT fk_point_history_order_id_orders_id FOREIGN '
                  'KEY(order_id) REFERENCES orders (id) ON DELETE RESTRICT\n'
                  ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                  'utf8mb4_unicode_ci',
 'point_redemptions': 'CREATE TABLE point_redemptions (\n'
                      '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                      '\torder_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                      '\tlot_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                      '\tpoints BIGINT NOT NULL, \n'
                      '\trate_snapshot NUMERIC(18, 4) NOT NULL, \n'
                      '\trate_version INTEGER NOT NULL, \n'
                      '\tvalue_snapshot NUMERIC(18, 2) NOT NULL, \n'
                      '\tstatus VARCHAR(16) NOT NULL, \n'
                      '\tCONSTRAINT pk_point_redemptions PRIMARY KEY (id), \n'
                      '\tCONSTRAINT uq_point_redemptions_order_id_lot_id '
                      'UNIQUE (order_id, lot_id), \n'
                      '\tCONSTRAINT fk_point_redemptions_order_id_orders_id '
                      'FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE '
                      'RESTRICT, \n'
                      '\tCONSTRAINT fk_point_redemptions_lot_id_point_lots_id '
                      'FOREIGN KEY(lot_id) REFERENCES point_lots (id) ON '
                      'DELETE RESTRICT\n'
                      ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC '
                      'COLLATE utf8mb4_unicode_ci',
 'return_cases': 'CREATE TABLE return_cases (\n'
                 '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                 '\treference VARCHAR(64) NOT NULL, \n'
                 '\torder_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                 '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                 '\tstatus VARCHAR(32) NOT NULL, \n'
                 '\treason TEXT NOT NULL, \n'
                 '\tinstructions JSON, \n'
                 '\treturn_courier VARCHAR(128), \n'
                 '\treturn_tracking VARCHAR(128), \n'
                 '\treplacement_courier VARCHAR(128), \n'
                 '\treplacement_tracking VARCHAR(128), \n'
                 '\tcreated_at DATETIME(6) NOT NULL, \n'
                 '\tupdated_at DATETIME(6) NOT NULL, \n'
                 '\tCONSTRAINT pk_return_cases PRIMARY KEY (id), \n'
                 '\tCONSTRAINT '
                 'fk_return_cases_order_id_user_id_orders_id_orders_user_id '
                 'FOREIGN KEY(order_id, user_id) REFERENCES orders (id, '
                 'user_id) ON DELETE RESTRICT, \n'
                 '\tCONSTRAINT uq_return_cases_reference UNIQUE (reference)\n'
                 ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                 'utf8mb4_unicode_ci',
 'return_case_items': 'CREATE TABLE return_case_items (\n'
                      '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                      '\tcase_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                      '\torder_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                      '\torder_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT '
                      'NULL, \n'
                      '\tquantity INTEGER NOT NULL, \n'
                      '\tCONSTRAINT pk_return_case_items PRIMARY KEY (id), \n'
                      '\tCONSTRAINT '
                      'fk_return_case_items_order_item_id_order_id_or_e6f8a9f1bb63 '
                      'FOREIGN KEY(order_item_id, order_id) REFERENCES '
                      'order_items (id, order_id) ON DELETE RESTRICT, \n'
                      '\tCONSTRAINT uq_return_case_items_case_id_order_item_id '
                      'UNIQUE (case_id, order_item_id), \n'
                      '\tCONSTRAINT '
                      'fk_return_case_items_case_id_return_cases_id FOREIGN '
                      'KEY(case_id) REFERENCES return_cases (id) ON DELETE '
                      'RESTRICT\n'
                      ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC '
                      'COLLATE utf8mb4_unicode_ci',
 'return_evidence': 'CREATE TABLE return_evidence (\n'
                    '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                    '\tcase_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                    '\tstorage_path TEXT NOT NULL, \n'
                    '\tsha256 VARCHAR(64) NOT NULL, \n'
                    '\tmime_type VARCHAR(32) NOT NULL, \n'
                    '\tbyte_size BIGINT NOT NULL, \n'
                    '\tcreated_at DATETIME(6) NOT NULL, \n'
                    '\tCONSTRAINT pk_return_evidence PRIMARY KEY (id), \n'
                    '\tCONSTRAINT fk_return_evidence_case_id_return_cases_id '
                    'FOREIGN KEY(case_id) REFERENCES return_cases (id) ON '
                    'DELETE RESTRICT\n'
                    ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                    'utf8mb4_unicode_ci',
 'return_timeline': 'CREATE TABLE return_timeline (\n'
                    '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                    '\tcase_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                    '\tactor_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                    '\tstatus VARCHAR(32) NOT NULL, \n'
                    '\tnote TEXT NOT NULL, \n'
                    '\tcreated_at DATETIME(6) NOT NULL, \n'
                    '\tCONSTRAINT pk_return_timeline PRIMARY KEY (id), \n'
                    '\tCONSTRAINT fk_return_timeline_case_id_return_cases_id '
                    'FOREIGN KEY(case_id) REFERENCES return_cases (id) ON '
                    'DELETE RESTRICT, \n'
                    '\tCONSTRAINT fk_return_timeline_actor_id_users_user_id '
                    'FOREIGN KEY(actor_id) REFERENCES users (user_id) ON '
                    'DELETE RESTRICT\n'
                    ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE '
                    'utf8mb4_unicode_ci'}
INDEX_DDL = ['CREATE INDEX ix_game_session_cooldown ON game_sessions (user_id, game_key, '
 'started_at)',
 'CREATE INDEX ix_point_lots_wallet ON point_lots (user_id, expires_at, '
 'created_at)',
 'CREATE INDEX ix_point_history_customer ON point_history (user_id, '
 'created_at, id)',
 'CREATE INDEX ix_return_cases_order ON return_cases (order_id, created_at)']
ALL_TABLES = tuple(TABLE_DDL)
RULES = {'cashback_awards': (('ck_cashback_awards_amounts',
                      'points >= 0 AND amount >= 0 AND rate_snapshot > 0',
                      'NEW.points >= 0 AND NEW.amount >= 0 AND '
                      'NEW.rate_snapshot > 0'),),
 'cashback_events': (('ck_cashback_events_bounds',
                      'percent > 0 AND percent <= 100 AND expiry_days > 0 AND '
                      'end_at > start_at',
                      'NEW.percent > 0 AND NEW.percent <= 100 AND '
                      'NEW.expiry_days > 0 AND NEW.end_at > NEW.start_at'),),
 'game_rules': (('ck_game_rules_bounds',
                 'cooldown_seconds >= 0 AND expiry_days > 0 AND '
                 'max_duration_seconds >= 10 AND max_duration_seconds <= 600 '
                 'AND max_points >= 0 AND points_per_unit > 0',
                 'NEW.cooldown_seconds >= 0 AND NEW.expiry_days > 0 AND '
                 'NEW.max_duration_seconds >= 10 AND NEW.max_duration_seconds '
                 '<= 600 AND NEW.max_points >= 0 AND NEW.points_per_unit > 0'),
                ('ck_game_rules_engine',
                 "engine IN ('matching','slide_puzzle','space_war','roulette')",
                 'NEW.engine IN '
                 "('matching','slide_puzzle','space_war','roulette')")),
 'game_sessions': (('ck_game_sessions_state',
                    "status IN ('active','completed','expired') AND seed >= 0 "
                    'AND points_awarded >= 0 AND score >= 0',
                    "NEW.status IN ('active','completed','expired') AND "
                    'NEW.seed >= 0 AND NEW.points_awarded >= 0 AND NEW.score '
                    '>= 0'),),
 'point_history': (('ck_point_history_amounts',
                    'balance_after >= 0 AND rate_snapshot > 0',
                    'NEW.balance_after >= 0 AND NEW.rate_snapshot > 0'),),
 'point_lots': (('ck_point_lots_amounts',
                 'earned > 0 AND remaining >= 0 AND remaining <= earned AND '
                 'rate_snapshot > 0',
                 'NEW.earned > 0 AND NEW.remaining >= 0 AND NEW.remaining <= '
                 'NEW.earned AND NEW.rate_snapshot > 0'),
                ('ck_point_lots_valuation',
                 "valuation = 'locked'",
                 "NEW.valuation = 'locked'")),
 'point_rate_versions': (('ck_point_rate_versions_positive',
                          'rate > 0 AND version > 0 AND cashback_valuation = '
                          "'locked'",
                          'NEW.rate > 0 AND NEW.version > 0 AND '
                          "NEW.cashback_valuation = 'locked'"),),
 'point_redemptions': (('ck_point_redemptions_valid',
                        'points > 0 AND rate_snapshot > 0 AND status IN '
                        "('reserved','consumed','released')",
                        'NEW.points > 0 AND NEW.rate_snapshot > 0 AND '
                        "NEW.status IN ('reserved','consumed','released')"),),
 'point_settings': (('ck_point_settings_positive',
                     "id = 'global' AND rate > 0 AND version > 0",
                     "NEW.id = 'global' AND NEW.rate > 0 AND NEW.version > 0"),
                    ('ck_point_settings_valuation',
                     "cashback_valuation = 'locked'",
                     "NEW.cashback_valuation = 'locked'")),
 'puzzle_levels': (('ck_puzzle_levels_bounds',
                    'level >= 1 AND level <= 20 AND rows >= 2 AND rows <= 6 '
                    'AND columns >= 2 AND columns <= 6',
                    'NEW.level >= 1 AND NEW.level <= 20 AND NEW.rows >= 2 AND '
                    'NEW.rows <= 6 AND NEW.columns >= 2 AND NEW.columns <= '
                    '6'),),
 'return_case_items': (('ck_return_case_items_quantity',
                        'quantity > 0',
                        'NEW.quantity > 0'),),
 'return_cases': (('ck_return_cases_status',
                   'status IN '
                   "('draft','submitted','approved','return_sent','received','replacement_shipped','completed','rejected','cancelled')",
                   'NEW.status IN '
                   "('draft','submitted','approved','return_sent','received','replacement_shipped','completed','rejected','cancelled')"),),
 'return_evidence': (('ck_return_evidence_file',
                      'byte_size > 0 AND byte_size <= 104857600 AND mime_type '
                      "IN ('video/mp4','video/webm')",
                      'NEW.byte_size > 0 AND NEW.byte_size <= 104857600 AND '
                      "NEW.mime_type IN ('video/mp4','video/webm')"),),
 'return_timeline': ()}

IMMUTABLE = frozenset({'point_history','point_rate_versions','return_timeline','return_evidence'})
SNAPSHOTS = {
 'point_lots': ['id','user_id','award_key','source','earned','rate_snapshot','rate_version','valuation','expires_at','created_at'],
 'point_redemptions': ['id','order_id','lot_id','points','rate_snapshot','rate_version','value_snapshot'],
 'game_sessions': ['id','user_id','game_key','seed','snapshot','started_at','expires_at'],
 'cashback_awards': ['order_id','event_id','snapshot','amount','rate_snapshot','points'],
 'return_cases': ['id','reference','order_id','user_id','reason','created_at'],
 'return_case_items': ['id','case_id','order_id','order_item_id','quantity']}
def quoted(name): return chr(96)+name+chr(96)
def reject(message): return "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '"+message+"';"
def custom_checks(table,event):
    checks=[]
    if event=='UPDATE' and table in SNAPSHOTS:
        fields=SNAPSHOTS[table]
        checks.append('IF '+' OR '.join('NOT (NEW.'+quoted(f)+' <=> OLD.'+quoted(f)+')' for f in fields)+' THEN '+reject('Acquisition and order snapshots are immutable')+' END IF;')
    if event in {'UPDATE','DELETE'} and table in IMMUTABLE:
        checks.append(reject('History is append-only'))
    if event=='DELETE' and table in SNAPSHOTS: checks.append(reject('Audited acquisitions cannot be deleted'))
    if table=='return_case_items' and event=='INSERT':
        checks.append('IF NOT EXISTS (SELECT 1 FROM return_cases c WHERE c.id=NEW.case_id AND c.order_id=NEW.order_id) THEN '+reject('Return item must belong to case order')+' END IF;')
    return checks
def trigger_definitions():
    definitions={}
    for table in ALL_TABLES:
        for event,suffix in (('INSERT','bi'),('UPDATE','bu'),('DELETE','bd')):
            lines=[]
            if event in {'INSERT','UPDATE'}:
                for name,_,predicate in RULES.get(table,()): lines.append('IF ('+predicate+') IS FALSE THEN '+reject('Rule '+name+' failed')+' END IF;')
            lines.extend(custom_checks(table,event))
            if not lines: continue
            name='trg_meow5_'+table+'_'+suffix
            body='BEGIN\n  '+'\n  '.join(lines)+'\nEND'
            definitions[name]={'table':table,'event':event,'timing':'BEFORE','body':body,'sql':'CREATE TRIGGER '+quoted(name)+' BEFORE '+event+' ON '+quoted(table)+' FOR EACH ROW '+body}
    return definitions
def canonical_body(body):
    tokens=re.findall(r"'(?:''|[^'])*'|`(?:``|[^`])*`|[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|[^\s]",body)
    return tuple(t if t.startswith("'") else t.strip(chr(96)).lower() for t in tokens)
def table_issues(connection):
    rows=connection.execute(sa.text('SELECT TABLE_NAME AS name, ENGINE AS engine, ROW_FORMAT AS row_format FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()')).mappings()
    actual={row['name']:row for row in rows};issues=[]
    for table in ALL_TABLES:
        if table not in actual: issues.append('missing_table:'+table)
        elif actual[table]['engine'].lower()!='innodb' or actual[table]['row_format'].lower()!='dynamic': issues.append('table_storage_mismatch:'+table)
    return issues
def row_issues(connection):
    issues=[]
    for table,rules in RULES.items():
        if rules and connection.exec_driver_sql('SELECT 1 FROM '+quoted(table)+' WHERE '+' OR '.join('('+p+') IS FALSE' for _,p,_ in rules)+' LIMIT 1').first(): issues.append('row_rule_violation:'+table)
    return issues
def trigger_issues(connection):
    actual={r['name']:r for r in connection.execute(sa.text('SELECT TRIGGER_NAME AS name,EVENT_OBJECT_TABLE AS table_name,EVENT_MANIPULATION AS event,ACTION_TIMING AS timing,ACTION_STATEMENT AS body,SQL_MODE AS sql_mode,ACTION_ORDER AS action_order FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()')).mappings()}
    issues=[]
    for name,expected in trigger_definitions().items():
        row=actual.get(name)
        if not row: issues.append('missing_trigger:'+name);continue
        if row['table_name']!=expected['table'] or row['event']!=expected['event'] or row['timing']!='BEFORE' or canonical_body(row['body'])!=canonical_body(expected['body']): issues.append('trigger_definition_mismatch:'+name)
        if set(row['sql_mode'].split(','))!=EXPECTED_SQL_MODES: issues.append('trigger_sql_mode_mismatch:'+name)
        if int(row['action_order'])!=max(int(r['action_order']) for r in actual.values() if r['table_name']==row['table_name'] and r['event']==row['event'] and r['timing']=='BEFORE'): issues.append('trigger_not_last:'+name)
    return issues
SEED_SQL = [
 "INSERT INTO point_settings(id,rate,version,cashback_valuation,updated_at) VALUES('global',100,1,'locked',UTC_TIMESTAMP(6))",
 "INSERT INTO point_rate_versions(version,rate,cashback_valuation,created_at) VALUES(1,100,'locked',UTC_TIMESTAMP(6))",
 "UPDATE games SET is_active=0 WHERE `key` IN ('puzzle','tetris','memory')",
 "INSERT INTO point_lots(id,user_id,award_key,source,earned,remaining,rate_snapshot,rate_version,valuation,created_at) SELECT SHA2(CONCAT('legacy-lot:',user_id),256),user_id,CONCAT('legacy:',user_id),'legacy',points_balance,points_balance,100,1,'locked',UTC_TIMESTAMP(6) FROM users WHERE points_balance>0",
 "INSERT INTO point_history(id,event_key,user_id,order_id,source,delta,balance_after,rate_snapshot,rate_version,value_snapshot,note,created_at) SELECT SHA2(CONCAT('legacy-log:',id),256),CONCAT('legacy-log:',id),user_id,order_id,type,delta,balance_after,100,1,delta*100,note,created_at FROM point_logs",
 "INSERT INTO point_history(id,event_key,user_id,lot_id,source,delta,balance_after,rate_snapshot,rate_version,value_snapshot,note,created_at) SELECT SHA2(CONCAT('legacy-ledger:',l.user_id),256),CONCAT('legacy:',l.user_id),l.user_id,l.id,'legacy',l.earned-COALESCE(h.total,0),l.remaining,100,1,(l.earned-COALESCE(h.total,0))*100,'Rekonsiliasi saldo awal; riwayat lama dipertahankan',l.created_at FROM point_lots l LEFT JOIN (SELECT user_id,SUM(delta) AS total FROM point_logs GROUP BY user_id) h ON h.user_id=l.user_id WHERE l.source='legacy'"
]
for key,name,engine,unit in [('matching','Match Meow Pairs','matching',5),('slide-puzzle','Meow Puzzle Geser','slide_puzzle',3),('space-war','Meow Space War','space_war',1),('roulette','Roulette','roulette',1)]:
    SEED_SQL.append("INSERT INTO games(id,`key`,name,description,is_active,max_points,created_at) VALUES(REPLACE(UUID(),'-',''),'"+key+"','"+name+"','',1,50,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE name=VALUES(name),is_active=1")
    SEED_SQL.append("INSERT INTO game_rules(game_key,engine,cooldown_seconds,expiry_days,max_duration_seconds,max_points,points_per_unit) VALUES('"+key+"','"+engine+"',86400,30,180,50,"+str(unit)+")")
SEED_SQL.append("UPDATE game_rules SET max_points=GREATEST(50,COALESCE((SELECT FLOOR(MAX(value)) FROM roulette_rewards WHERE type='points' AND is_active=1),0)) WHERE game_key='roulette'")
for level in range(1,21):
    size=2+(level-1)//4
    SEED_SQL.append("INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES("+str(level)+","+str(size)+","+str(size)+",'/logo-meow.jpg',1)")
TABLE_SHAPE = {'cashback_events': {'columns': {'id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                        False),
                                 'name': ('VARCHAR(160)', False),
                                 'start_at': ('DATETIME(6)', False),
                                 'end_at': ('DATETIME(6)', False),
                                 'percent': ('NUMERIC(7, 4)', False),
                                 'expiry_days': ('INTEGER', False),
                                 'is_active': ('BOOL', False)},
                     'foreign_keys': [],
                     'unique_keys': [],
                     'indexes': []},
 'point_settings': {'columns': {'id': ('VARCHAR(16)', False),
                                'rate': ('NUMERIC(18, 4)', False),
                                'version': ('INTEGER', False),
                                'cashback_valuation': ('VARCHAR(16)', False),
                                'updated_at': ('DATETIME(6)', False)},
                    'foreign_keys': [],
                    'unique_keys': [],
                    'indexes': []},
 'puzzle_levels': {'columns': {'level': ('INTEGER', False),
                               'rows': ('INTEGER', False),
                               'columns': ('INTEGER', False),
                               'image_url': ('TEXT', False),
                               'is_active': ('BOOL', False)},
                   'foreign_keys': [],
                   'unique_keys': [],
                   'indexes': []},
 'game_rules': {'columns': {'game_key': ('VARCHAR(32)', False),
                            'engine': ('VARCHAR(32)', False),
                            'cooldown_seconds': ('INTEGER', False),
                            'expiry_days': ('INTEGER', False),
                            'max_duration_seconds': ('INTEGER', False),
                            'max_points': ('INTEGER', False),
                            'points_per_unit': ('INTEGER', False)},
                'foreign_keys': ['fk_game_rules_game_key_games_key'],
                'unique_keys': [],
                'indexes': []},
 'game_sessions': {'columns': {'id': ('VARCHAR(64) COLLATE utf8mb4_bin', False),
                               'user_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                           False),
                               'game_key': ('VARCHAR(32)', False),
                               'active_slot': ('VARCHAR(191) COLLATE '
                                               'utf8mb4_bin',
                                               True),
                               'seed': ('BIGINT', False),
                               'snapshot': ('JSON', False),
                               'transcript': ('JSON', True),
                               'status': ('VARCHAR(16)', False),
                               'score': ('INTEGER', False),
                               'points_awarded': ('INTEGER', False),
                               'started_at': ('DATETIME(6)', False),
                               'completed_at': ('DATETIME(6)', True),
                               'expires_at': ('DATETIME(6)', False)},
                   'foreign_keys': ['fk_game_sessions_game_key_games_key',
                                    'fk_game_sessions_user_id_users_user_id'],
                   'unique_keys': ['uq_game_sessions_active_slot'],
                   'indexes': ['ix_game_session_cooldown']},
 'point_lots': {'columns': {'id': ('VARCHAR(64) COLLATE utf8mb4_bin', False),
                            'user_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                        False),
                            'award_key': ('VARCHAR(191) COLLATE utf8mb4_bin',
                                          False),
                            'source': ('VARCHAR(32)', False),
                            'earned': ('BIGINT', False),
                            'remaining': ('BIGINT', False),
                            'rate_snapshot': ('NUMERIC(18, 4)', False),
                            'rate_version': ('INTEGER', False),
                            'valuation': ('VARCHAR(16)', False),
                            'expires_at': ('DATETIME(6)', True),
                            'created_at': ('DATETIME(6)', False)},
                'foreign_keys': ['fk_point_lots_user_id_users_user_id'],
                'unique_keys': ['uq_point_lots_award_key'],
                'indexes': ['ix_point_lots_wallet']},
 'point_rate_versions': {'columns': {'version': ('INTEGER', False),
                                     'rate': ('NUMERIC(18, 4)', False),
                                     'cashback_valuation': ('VARCHAR(16)',
                                                            False),
                                     'actor_id': ('VARCHAR(64) COLLATE '
                                                  'utf8mb4_bin',
                                                  True),
                                     'created_at': ('DATETIME(6)', False)},
                         'foreign_keys': ['fk_point_rate_versions_actor_id_users_user_id'],
                         'unique_keys': [],
                         'indexes': []},
 'cashback_awards': {'columns': {'order_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                              False),
                                 'event_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                              False),
                                 'snapshot': ('JSON', False),
                                 'amount': ('NUMERIC(18, 2)', False),
                                 'rate_snapshot': ('NUMERIC(18, 4)', False),
                                 'points': ('BIGINT', False),
                                 'credited_at': ('DATETIME(6)', True)},
                     'foreign_keys': ['fk_cashback_awards_event_id_cashback_events_id',
                                      'fk_cashback_awards_order_id_orders_id'],
                     'unique_keys': [],
                     'indexes': []},
 'point_history': {'columns': {'id': ('VARCHAR(64) COLLATE utf8mb4_bin', False),
                               'event_key': ('VARCHAR(191) COLLATE utf8mb4_bin',
                                             False),
                               'user_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                           False),
                               'lot_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                          True),
                               'order_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                            True),
                               'source': ('VARCHAR(64)', False),
                               'delta': ('BIGINT', False),
                               'balance_after': ('BIGINT', False),
                               'rate_snapshot': ('NUMERIC(18, 4)', False),
                               'rate_version': ('INTEGER', False),
                               'value_snapshot': ('NUMERIC(18, 2)', False),
                               'expires_at': ('DATETIME(6)', True),
                               'note': ('TEXT', False),
                               'created_at': ('DATETIME(6)', False)},
                   'foreign_keys': ['fk_point_history_lot_id_point_lots_id',
                                    'fk_point_history_order_id_orders_id',
                                    'fk_point_history_user_id_users_user_id'],
                   'unique_keys': ['uq_point_history_event_key'],
                   'indexes': ['ix_point_history_customer']},
 'point_redemptions': {'columns': {'id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                          False),
                                   'order_id': ('VARCHAR(64) COLLATE '
                                                'utf8mb4_bin',
                                                False),
                                   'lot_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                              False),
                                   'points': ('BIGINT', False),
                                   'rate_snapshot': ('NUMERIC(18, 4)', False),
                                   'rate_version': ('INTEGER', False),
                                   'value_snapshot': ('NUMERIC(18, 2)', False),
                                   'status': ('VARCHAR(16)', False)},
                       'foreign_keys': ['fk_point_redemptions_lot_id_point_lots_id',
                                        'fk_point_redemptions_order_id_orders_id'],
                       'unique_keys': ['uq_point_redemptions_order_id_lot_id'],
                       'indexes': []},
 'return_cases': {'columns': {'id': ('VARCHAR(64) COLLATE utf8mb4_bin', False),
                              'reference': ('VARCHAR(64)', False),
                              'order_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                           False),
                              'user_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                          False),
                              'status': ('VARCHAR(32)', False),
                              'reason': ('TEXT', False),
                              'instructions': ('JSON', True),
                              'return_courier': ('VARCHAR(128)', True),
                              'return_tracking': ('VARCHAR(128)', True),
                              'replacement_courier': ('VARCHAR(128)', True),
                              'replacement_tracking': ('VARCHAR(128)', True),
                              'created_at': ('DATETIME(6)', False),
                              'updated_at': ('DATETIME(6)', False)},
                  'foreign_keys': ['fk_return_cases_order_id_user_id_orders_id_orders_user_id'],
                  'unique_keys': ['uq_return_cases_reference'],
                  'indexes': ['ix_return_cases_order']},
 'return_case_items': {'columns': {'id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                          False),
                                   'case_id': ('VARCHAR(64) COLLATE '
                                               'utf8mb4_bin',
                                               False),
                                   'order_id': ('VARCHAR(64) COLLATE '
                                                'utf8mb4_bin',
                                                False),
                                   'order_item_id': ('VARCHAR(64) COLLATE '
                                                     'utf8mb4_bin',
                                                     False),
                                   'quantity': ('INTEGER', False)},
                       'foreign_keys': ['fk_return_case_items_case_id_return_cases_id',
                                        'fk_return_case_items_order_item_id_order_id_or_e6f8a9f1bb63'],
                       'unique_keys': ['uq_return_case_items_case_id_order_item_id'],
                       'indexes': []},
 'return_evidence': {'columns': {'id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                        False),
                                 'case_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                             False),
                                 'storage_path': ('TEXT', False),
                                 'sha256': ('VARCHAR(64)', False),
                                 'mime_type': ('VARCHAR(32)', False),
                                 'byte_size': ('BIGINT', False),
                                 'created_at': ('DATETIME(6)', False)},
                     'foreign_keys': ['fk_return_evidence_case_id_return_cases_id'],
                     'unique_keys': [],
                     'indexes': []},
 'return_timeline': {'columns': {'id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                        False),
                                 'case_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                             False),
                                 'actor_id': ('VARCHAR(64) COLLATE utf8mb4_bin',
                                              False),
                                 'status': ('VARCHAR(32)', False),
                                 'note': ('TEXT', False),
                                 'created_at': ('DATETIME(6)', False)},
                     'foreign_keys': ['fk_return_timeline_actor_id_users_user_id',
                                      'fk_return_timeline_case_id_return_cases_id'],
                     'unique_keys': [],
                     'indexes': []}}

def normalized_type(value):
    value=str(value).lower().replace('boolean','tinyint').replace('bool','tinyint').replace('integer','int').replace('numeric','decimal')
    value=value.replace(' character set utf8mb4','').replace(' collate utf8mb4_unicode_ci','')
    return re.sub(r'\b(bigint|int|smallint|tinyint)\([0-9]+\)',r'\1',value)
def empty_recovery_issues(connection):
    from sqlalchemy.dialects.mysql import dialect
    inspector=sa.inspect(connection);issues=table_issues(connection)
    for table,expected in TABLE_SHAPE.items():
        collation=connection.execute(sa.text('SELECT TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:name'),{'name':table}).scalar_one()
        if collation!='utf8mb4_unicode_ci': issues.append('recovery_collation_mismatch:'+table)
        actual={c['name']:(normalized_type(c['type'].compile(dialect=dialect())),c['nullable']) for c in inspector.get_columns(table)}
        columns={name:(normalized_type(kind),nullable) for name,(kind,nullable) in expected['columns'].items()}
        if actual!=columns: issues.append('recovery_columns_mismatch:'+table)
        if sorted(fk['name'] for fk in inspector.get_foreign_keys(table))!=expected['foreign_keys']: issues.append('recovery_foreign_keys_mismatch:'+table)
        if sorted(key['name'] for key in inspector.get_unique_constraints(table))!=expected['unique_keys']: issues.append('recovery_unique_keys_mismatch:'+table)
        if not set(expected['indexes'])<=set(index['name'] for index in inspector.get_indexes(table)): issues.append('recovery_indexes_mismatch:'+table)
        if connection.exec_driver_sql('SELECT 1 FROM '+quoted(table)+' LIMIT 1').first(): issues.append('recovery_table_not_empty:'+table)
    return issues

def upgrade():
    statements=[*TABLE_DDL.values(),*INDEX_DDL,*SEED_SQL]
    if context.is_offline_mode():
        output=op.get_context().impl.static_output
        for sql in statements: output(sql+';')
        output('DELIMITER $$')
        for definition in trigger_definitions().values(): output(definition['sql']+'$$')
        output('DELIMITER ;');return
    connection=op.get_bind()
    overlap=set(sa.inspect(connection).get_table_names()).intersection(ALL_TABLES)
    if overlap:
        if overlap!=set(ALL_TABLES) or context.get_x_argument(as_dictionary=True).get('resume_empty_loyalty')!='true': raise RuntimeError('Partial installation detected; review before retry')
        issues=empty_recovery_issues(connection)
        if issues: raise RuntimeError('Empty schema recovery refused: '+', '.join(issues))
        statements=SEED_SQL
    for sql in statements: connection.exec_driver_sql(sql)
    for definition in trigger_definitions().values(): connection.exec_driver_sql(definition['sql'])
    issues=table_issues(connection)+row_issues(connection)+trigger_issues(connection)
    if issues: raise RuntimeError('Loyalty migration audit failed: '+', '.join(issues))
def downgrade():
    raise RuntimeError('Loyalty and RMA history must be preserved. Restore a reviewed backup.')
