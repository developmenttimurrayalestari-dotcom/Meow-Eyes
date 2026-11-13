"""Credential-safe backup, online migration, and preservation audit. No server start."""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from sqlalchemy import text
from mysql.config import MySQLSettings
from mysql.database import Database
from mysql.check_integrity import audit, load_flat_master_revision

BACKEND = Path(__file__).resolve().parents[1]

async def snapshot():
    db = Database(MySQLSettings.from_env())
    try:
        async with db.engine.connect() as conn:
            revision = (await conn.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()
            tables = (await conn.execute(text("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME"))).scalars().all()
            counts, hashes = {}, {}
            for table in tables:
                rows = (await conn.exec_driver_sql('SELECT * FROM `'+table.replace('`','``')+'`')).mappings().all()
                counts[table] = len(rows)
                normalized = sorted(json.dumps(dict(row),sort_keys=True,default=str,ensure_ascii=True) for row in rows)
                hashes[table] = hashlib.sha256('\n'.join(normalized).encode()).hexdigest()
            categories = [dict(row) for row in (await conn.execute(text('SELECT * FROM categories ORDER BY id'))).mappings()]
            links = [tuple(row) for row in (await conn.execute(text('SELECT product_id,category_id FROM product_categories'))).all()]
            result = {'revision':revision,'counts':counts,'hashes':hashes,'categories':categories,'links':links}
            if revision == '20261111_0005':
                products = [dict(row) for row in (await conn.execute(text('SELECT id,product_type,primary_category_id,spec FROM products'))).mappings()]
                segments = (await conn.execute(text('SELECT product_id,segment FROM product_segments'))).all()
                variants = (await conn.execute(text('SELECT product_id,lens_type FROM product_variants WHERE lens_type IS NOT NULL'))).all()
                result['plan'] = load_flat_master_revision().plan_rows(categories,products,links,segments,variants)
            return result
    finally: await db.dispose()


def main():
    before = asyncio.run(snapshot())
    if before['revision'] != '20261111_0005': raise RuntimeError('Unexpected installed revision; nothing changed')
    issues = asyncio.run(audit(preflight_only=True))
    if not issues['ok']: raise RuntimeError('Preflight integrity failed; nothing changed')
    plan = before['plan']
    print(json.dumps({'stage':'reviewed_plan','before_categories':len(before['categories']),'after_categories':len(plan['masters']),
        'before_product_tags':len(before['links']),'after_product_tags':len(plan['links']),'required_masters':len(plan['initial_ids'])}),flush=True)
    if '--apply' not in sys.argv: return
    settings = MySQLSettings.from_env(); stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    directory = BACKEND/'private'/'backups'; directory.mkdir(parents=True,exist_ok=True)
    output = directory/('flat-masters-before-0006-'+stamp+'.sql')
    env = os.environ.copy(); env['MYSQL_PWD']=settings.password
    args=[r'C:\xampp\mysql\bin\mysqldump.exe','--host='+settings.host,'--port='+str(settings.port),'--user='+settings.username,
        '--single-transaction','--quick','--routines','--events','--triggers','--hex-blob','--default-character-set=utf8mb4','--result-file='+str(output),settings.database]
    backup=subprocess.run(args,env=env,capture_output=True,text=True)
    if backup.returncode or not output.exists() or b'Dump completed on' not in output.read_bytes():
        output.with_suffix('.error.txt').write_text(backup.stderr,encoding='utf-8')
        raise RuntimeError('Backup incomplete; migration was not run')
    print(json.dumps({'stage':'backup_complete','path':str(output.relative_to(BACKEND)),'bytes':output.stat().st_size}),flush=True)
    migration=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=BACKEND,capture_output=True,text=True)
    (BACKEND/'private'/'flat-master-migration.log').write_text(migration.stdout+'\n'+migration.stderr,encoding='utf-8')
    if migration.returncode: raise RuntimeError('Migration failed; inspect private/flat-master-migration.log before retrying')
    after=asyncio.run(snapshot()); integrity=asyncio.run(audit()); issues=[]
    changed={'alembic_version','categories','product_categories','settings','flash_sale_categories'}
    for table in before['counts']:
        if table not in changed and before['hashes'][table]!=after['hashes'][table]: issues.append('unexpected_change:'+table)
    if not set(before['links'])<=set(after['links']): issues.append('original_product_tags_lost')
    if not {row['id'] for row in before['categories']}<={row['id'] for row in after['categories']}: issues.append('original_category_ids_lost')
    required=set(plan['initial_ids'].values()); active_ids={row['id'] for row in after['categories']}
    if not required<=active_ids: issues.append('initial_master_missing')
    if len(after['links'])!=len(plan['links']): issues.append('product_tag_count_mismatch')
    if any({'parent_id','level','category_type'} & set(row) for row in after['categories']): issues.append('hierarchy_columns_remain')
    report={'ok':not issues and integrity['ok'],'revision':after['revision'],'backup':str(output.relative_to(BACKEND)),
        'backup_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'before_counts':before['counts'],'after_counts':after['counts'],
        'business_tables_unchanged':not any(item.startswith('unexpected_change:') for item in issues),'original_assignments_preserved':not any('lost' in item for item in issues),
        'required_masters':len(required),'category_groups':{group:sum(row['group_type']==group for row in after['categories']) for group in sorted({row['group_type'] for row in after['categories']})},
        'integrity':integrity,'issues':issues}
    (BACKEND/'private'/'flat-master-migration-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items() if key not in ('before_counts','after_counts','backup_sha256')}))
    if not report['ok']: raise RuntimeError('Migration preservation audit failed; keep application stopped')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(json.dumps({'ok':False,'error_type':type(exc).__name__,'stage':'stopped_check_private_report'})); raise SystemExit(1)
