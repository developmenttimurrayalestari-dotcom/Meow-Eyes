"""Apply the reviewed 0005 migration after a verified private full backup."""
import asyncio
import json
from pathlib import Path
import socket
import subprocess
import sys
from sqlalchemy import text
from mysql.check_integrity import audit
from mysql.config import MySQLSettings
from mysql.database import Database

ROOT = Path(__file__).resolve().parents[1]

async def inspect_database(expected):
    database=Database(MySQLSettings.from_env())
    try:
        async with database.engine.connect() as c:
            revision=(await c.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()
            if revision!=expected: raise RuntimeError('Unexpected installed revision; migration was not started')
            active=(await c.execute(text("SELECT COUNT(*) FROM information_schema.PROCESSLIST WHERE DB=DATABASE() AND ID<>CONNECTION_ID() AND COMMAND<>'Sleep'"))).scalar_one()
            if active: raise RuntimeError('Other database writers are active; migration was not started')
            tables=(await c.execute(text("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME"))).scalars().all()
            counts={name:(await c.exec_driver_sql('SELECT COUNT(*) FROM `'+name.replace('`','``')+'`')).scalar_one() for name in tables}
            balances=(await c.execute(text('SELECT user_id,points_balance FROM users ORDER BY user_id'))).all()
            return counts,[(user,int(balance)) for user,balance in balances]
    finally: await database.dispose()

async def main():
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(('127.0.0.1',8001))==0: raise RuntimeError('Stop the existing backend on port 8001 before migration')
    reports=sorted((ROOT/'private/backups').glob('loyalty-before-0005-*.json'))
    if not reports: raise RuntimeError('Verified full backup is required')
    backup=json.loads(reports[-1].read_text(encoding='utf-8'))
    counts,balances=await inspect_database('20261110_0004')
    resume=sys.argv[1:]==['--resume-empty']
    if resume:
        from mysql.check_integrity import load_loyalty_revision
        new=set(load_loyalty_revision().ALL_TABLES)
        if set(counts)!=set(backup['before_row_counts'])|new or any(counts[name] for name in new): raise RuntimeError('Recovery requires exactly the verified empty new tables')
        counts={name:count for name,count in counts.items() if name not in new}
    if counts!=backup['before_row_counts']: raise RuntimeError('Database changed since backup; create a new backup before retrying')
    preflight=await audit(preflight_only=True)
    if not preflight['ok']: raise RuntimeError('Integrity preflight failed; migration was not started')
    arguments=['-m','alembic']+(['-x','resume_empty_loyalty=true'] if resume else [])+['upgrade','head']
    process=await asyncio.create_subprocess_exec(sys.executable,*arguments,cwd=ROOT,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
    output=await process.communicate()
    (ROOT/'private/loyalty-migration.log').write_bytes(output[0])
    if process.returncode: raise RuntimeError('Migration failed; inspect private/loyalty-migration.log before any retry')
    after,after_balances=await inspect_database('20261111_0005')
    changed=[table for table,count in counts.items() if table not in ('games',) and after[table]!=count]
    if changed or balances!=after_balances: raise RuntimeError('Historical data verification failed; inspect private migration report')
    result=await audit()
    database=Database(MySQLSettings.from_env())
    try:
        async with database.engine.connect() as c:
            mismatches=(await c.execute(text('SELECT COUNT(*) FROM users u LEFT JOIN (SELECT user_id,SUM(remaining) AS balance FROM point_lots GROUP BY user_id) l ON l.user_id=u.user_id WHERE u.points_balance<>COALESCE(l.balance,0)'))).scalar_one()
            games=(await c.execute(text('SELECT game_key FROM game_rules ORDER BY game_key'))).scalars().all()
            level_count=(await c.execute(text('SELECT COUNT(*) FROM puzzle_levels'))).scalar_one()
    finally: await database.dispose()
    report={**result,'revision':'20261111_0005','backup':backup['backup'],'application_tables':len(after)-1,'historical_counts_preserved':not changed,'customer_balances_preserved':balances==after_balances,'wallet_mismatches':mismatches,'games':games,'puzzle_levels':level_count,'before_counts':counts,'after_counts':after}
    report['ok']=report['ok'] and mismatches==0 and level_count==20
    (ROOT/'private/loyalty-migration-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items() if key not in ('before_counts','after_counts')},indent=2))
    if not report['ok']: raise RuntimeError('Post-migration audit requires review')

if __name__=='__main__':
    try: asyncio.run(main())
    except Exception as error:
        # Only our explicit messages are safe for terminal output.
        print(str(error) if type(error) is RuntimeError else 'Database operation failed; inspect connection/privileges and private migration log',file=sys.stderr)
        raise SystemExit(1)
