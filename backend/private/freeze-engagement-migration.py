from pathlib import Path
from pprint import pformat
import re
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects.mysql import dialect
from sqlalchemy import CheckConstraint
from mysql import models as m
from mysql.base import Base

names = {model.__tablename__ for model in (m.PointSettings,m.PointRateVersion,m.PointLot,m.PointHistory,m.PointRedemption,m.GameRule,m.PuzzleLevel,m.GameSession,m.CashbackEvent,m.CashbackAward,m.ReturnCase,m.ReturnCaseItem,m.ReturnEvidence,m.ReturnTimeline)}
tables = [table for table in Base.metadata.sorted_tables if table.name in names]
ddl = {table.name: str(CreateTable(table).compile(dialect=dialect())).strip() for table in tables}
indexes = [str(CreateIndex(index).compile(dialect=dialect())) for table in tables for index in sorted(table.indexes, key=lambda index:index.name)]
rules = {}
for table in tables:
    rules[table.name] = tuple((constraint.name,str(constraint.sqltext),re.sub(r'\b('+'|'.join(re.escape(c.name) for c in table.columns)+r')\b',r'NEW.\1',str(constraint.sqltext))) for constraint in sorted(table.constraints,key=lambda c:str(c.name)) if isinstance(constraint,CheckConstraint))
path = Path('migrations/versions/20261111_0005_loyalty_games_returns.py')
text = '''"""Versioned point wallet, verified games, cashback and private replacement RMA.
Frozen MySQL 5.7 DDL. Back up and pause writers before upgrade; DDL commits.
"""
import re
from alembic import context, op
import sqlalchemy as sa
revision = '20261111_0005'
down_revision = '20261110_0004'
branch_labels = depends_on = None
EXPECTED_SQL_MODES = frozenset({'STRICT_TRANS_TABLES','ERROR_FOR_DIVISION_BY_ZERO','NO_ENGINE_SUBSTITUTION','ONLY_FULL_GROUP_BY','NO_ZERO_DATE','NO_ZERO_IN_DATE'})
'''
text += 'TABLE_DDL = ' + pformat(ddl,sort_dicts=False) + '\nINDEX_DDL = ' + pformat(indexes) + '\nALL_TABLES = tuple(TABLE_DDL)\nRULES = ' + pformat(rules) + '\n'
text += '''
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
            body='BEGIN\\n  '+'\\n  '.join(lines)+'\\nEND'
            definitions[name]={'table':table,'event':event,'timing':'BEFORE','body':body,'sql':'CREATE TRIGGER '+quoted(name)+' BEFORE '+event+' ON '+quoted(table)+' FOR EACH ROW '+body}
    return definitions
def canonical_body(body):
    tokens=re.findall(r"'(?:''|[^'])*'|`(?:``|[^`])*`|[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\\.[0-9]+)?|[^\\s]",body)
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
 "INSERT INTO point_lots(id,user_id,award_key,source,earned,remaining,rate_snapshot,rate_version,valuation,created_at) SELECT CONCAT('legacy_',user_id),user_id,CONCAT('legacy:',user_id),'legacy',points_balance,points_balance,100,1,'locked',UTC_TIMESTAMP(6) FROM users WHERE points_balance>0",
 "INSERT INTO point_history(id,event_key,user_id,order_id,source,delta,balance_after,rate_snapshot,rate_version,value_snapshot,note,created_at) SELECT REPLACE(UUID(),'-',''),CONCAT('legacy-log:',id),user_id,order_id,type,delta,balance_after,100,1,delta*100,note,created_at FROM point_logs",
 "INSERT INTO point_history(id,event_key,user_id,lot_id,source,delta,balance_after,rate_snapshot,rate_version,value_snapshot,note,created_at) SELECT REPLACE(UUID(),'-',''),CONCAT('legacy:',l.user_id),l.user_id,l.id,'legacy',l.earned-COALESCE(h.total,0),l.remaining,100,1,(l.earned-COALESCE(h.total,0))*100,'Rekonsiliasi saldo awal; riwayat lama dipertahankan',l.created_at FROM point_lots l LEFT JOIN (SELECT user_id,SUM(delta) AS total FROM point_logs GROUP BY user_id) h ON h.user_id=l.user_id WHERE l.source='legacy'"
]
for key,name,engine,unit in [('matching','Match Meow Pairs','matching',5),('slide-puzzle','Meow Puzzle Geser','slide_puzzle',3),('space-war','Meow Space War','space_war',1),('roulette','Roulette','roulette',1)]:
    SEED_SQL.append("INSERT INTO games(id,`key`,name,description,is_active,max_points,created_at) VALUES(REPLACE(UUID(),'-',''),'"+key+"','"+name+"','',1,50,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE name=VALUES(name),is_active=1")
    SEED_SQL.append("INSERT INTO game_rules(game_key,engine,cooldown_seconds,expiry_days,max_duration_seconds,max_points,points_per_unit) VALUES('"+key+"','"+engine+"',86400,30,180,50,"+str(unit)+")")
SEED_SQL.append("UPDATE game_rules SET max_points=GREATEST(50,COALESCE((SELECT FLOOR(MAX(value)) FROM roulette_rewards WHERE type='points' AND is_active=1),0)) WHERE game_key='roulette'")
for level in range(1,21):
    size=2+(level-1)//4
    SEED_SQL.append("INSERT INTO puzzle_levels(level,rows,columns,image_url,is_active) VALUES("+str(level)+","+str(size)+","+str(size)+",'/logo-meow.jpg',1)")
def upgrade():
    statements=[*TABLE_DDL.values(),*INDEX_DDL,*SEED_SQL]
    if context.is_offline_mode():
        output=op.get_context().impl.static_output
        for sql in statements: output(sql+';')
        output('DELIMITER $$')
        for definition in trigger_definitions().values(): output(definition['sql']+'$$')
        output('DELIMITER ;');return
    connection=op.get_bind()
    if set(sa.inspect(connection).get_table_names()).intersection(ALL_TABLES): raise RuntimeError('Partial installation detected; review before retry')
    for sql in statements: connection.exec_driver_sql(sql)
    for definition in trigger_definitions().values(): connection.exec_driver_sql(definition['sql'])
    issues=table_issues(connection)+row_issues(connection)+trigger_issues(connection)
    if issues: raise RuntimeError('Loyalty migration audit failed: '+', '.join(issues))
def downgrade():
    raise RuntimeError('Loyalty and RMA history must be preserved. Restore a reviewed backup.')
'''
# Legacy IDs can already occupy all 64 bytes; deterministic UUID is safer.
text=text.replace("CONCAT('legacy_',user_id),user_id", "REPLACE(UUID(),'-',''),user_id")
text=text.replace("SELECT REPLACE(UUID(),'-',''),user_id,CONCAT('legacy:',user_id)","SELECT SHA2(CONCAT('legacy-lot:',user_id),256),user_id,CONCAT('legacy:',user_id)")
text=text.replace("SELECT REPLACE(UUID(),'-',''),CONCAT('legacy-log:',id)","SELECT SHA2(CONCAT('legacy-log:',id),256),CONCAT('legacy-log:',id)")
text=text.replace("SELECT REPLACE(UUID(),'-',''),CONCAT('legacy:',l.user_id)","SELECT SHA2(CONCAT('legacy-ledger:',l.user_id),256),CONCAT('legacy:',l.user_id)")
path.write_text(text,encoding='utf-8')
print('Frozen',len(ddl),'tables;',sum(len(r) for r in rules.values()),'rules')
