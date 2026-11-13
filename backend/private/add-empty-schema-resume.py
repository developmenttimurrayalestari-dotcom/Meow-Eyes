"""Freeze exact recovery shape and support a reviewed non-destructive retry."""
from pathlib import Path
from pprint import pformat
import io
from sqlalchemy.dialects.mysql import dialect
from sqlalchemy import UniqueConstraint
from mysql.base import Base
from mysql import models
from mysql.check_integrity import load_loyalty_revision
from alembic import command
from alembic.config import Config
path=Path('migrations/versions/20261111_0005_loyalty_games_returns.py')
source=path.read_text(encoding='utf-8')
shape={name:{'columns':{c.name:(str(c.type.compile(dialect=dialect())),c.nullable) for c in Base.metadata.tables[name].columns},
    'foreign_keys':sorted(str(fk.name) for fk in Base.metadata.tables[name].foreign_key_constraints),
    'unique_keys':sorted(str(c.name) for c in Base.metadata.tables[name].constraints if isinstance(c,UniqueConstraint)),
    'indexes':sorted(str(i.name) for i in Base.metadata.tables[name].indexes)} for name in load_loyalty_revision().ALL_TABLES}
recovery='''
def normalized_type(value):
    value=str(value).lower().replace('boolean','tinyint').replace('bool','tinyint').replace('integer','int')
    return re.sub(r'\\b(bigint|int|smallint|tinyint)\\([0-9]+\\)',r'\\1',value)
def empty_recovery_issues(connection):
    from sqlalchemy.dialects.mysql import dialect
    inspector=sa.inspect(connection);issues=table_issues(connection)
    for table,expected in TABLE_SHAPE.items():
        actual={c['name']:(normalized_type(c['type'].compile(dialect=dialect())),c['nullable']) for c in inspector.get_columns(table)}
        columns={name:(normalized_type(kind),nullable) for name,(kind,nullable) in expected['columns'].items()}
        if actual!=columns: issues.append('recovery_columns_mismatch:'+table)
        if sorted(fk['name'] for fk in inspector.get_foreign_keys(table))!=expected['foreign_keys']: issues.append('recovery_foreign_keys_mismatch:'+table)
        if sorted(key['name'] for key in inspector.get_unique_constraints(table))!=expected['unique_keys']: issues.append('recovery_unique_keys_mismatch:'+table)
        if not set(expected['indexes'])<=set(index['name'] for index in inspector.get_indexes(table)): issues.append('recovery_indexes_mismatch:'+table)
        if connection.exec_driver_sql('SELECT 1 FROM '+quoted(table)+' LIMIT 1').first(): issues.append('recovery_table_not_empty:'+table)
    return issues
'''
source=source.replace('def upgrade():','TABLE_SHAPE = '+pformat(shape,sort_dicts=False)+'\n'+recovery+'\ndef upgrade():')
old="    if set(sa.inspect(connection).get_table_names()).intersection(ALL_TABLES): raise RuntimeError('Partial installation detected; review before retry')\n    for sql in statements: connection.exec_driver_sql(sql)"
new="""    overlap=set(sa.inspect(connection).get_table_names()).intersection(ALL_TABLES)
    if overlap:
        if overlap!=set(ALL_TABLES) or context.get_x_argument(as_dictionary=True).get('resume_empty_loyalty')!='true': raise RuntimeError('Partial installation detected; review before retry')
        issues=empty_recovery_issues(connection)
        if issues: raise RuntimeError('Empty schema recovery refused: '+', '.join(issues))
        statements=SEED_SQL
    for sql in statements: connection.exec_driver_sql(sql)"""
assert old in source;source=source.replace(old,new);path.write_text(source,encoding='utf-8')
out=io.StringIO();command.upgrade(Config('alembic.ini',output_buffer=out),'20261110_0004:20261111_0005',sql=True)
Path('sql/005_loyalty_games_returns.sql').write_text(out.getvalue(),encoding='utf-8')

p=Path('private/apply-loyalty-migration.py');t=p.read_text(encoding='utf-8')
t=t.replace("    if counts!=backup['before_row_counts']: raise RuntimeError('Database changed since backup; create a new backup before retrying')", """    resume=sys.argv[1:]==['--resume-empty']
    if resume:
        from mysql.check_integrity import load_loyalty_revision
        new=set(load_loyalty_revision().ALL_TABLES)
        if set(counts)!=set(backup['before_row_counts'])|new or any(counts[name] for name in new): raise RuntimeError('Recovery requires exactly the verified empty new tables')
        counts={name:count for name,count in counts.items() if name not in new}
    if counts!=backup['before_row_counts']: raise RuntimeError('Database changed since backup; create a new backup before retrying')""")
t=t.replace("    process=await asyncio.create_subprocess_exec(sys.executable,'-m','alembic','upgrade','head',", "    arguments=['-m','alembic']+(['-x','resume_empty_loyalty=true'] if resume else [])+['upgrade','head']\n    process=await asyncio.create_subprocess_exec(sys.executable,*arguments,")
p.write_text(t,encoding='utf-8')
