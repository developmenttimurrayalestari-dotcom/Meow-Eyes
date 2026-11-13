"""Back up and apply the additive product deletion column; never start servers."""
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
from mysql.check_integrity import audit, load_product_deletion_revision

BACKEND = Path(__file__).resolve().parents[1]

async def snapshot():
    database = Database(MySQLSettings.from_env())
    try:
        async with database.engine.connect() as conn:
            revision = (await conn.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()
            products = [dict(row) for row in (await conn.execute(text('SELECT * FROM products ORDER BY id'))).mappings()]
            variants = [dict(row) for row in (await conn.execute(text('SELECT * FROM product_variants ORDER BY id'))).mappings()]
            canonical = [{key:value for key,value in row.items() if key != 'deleted_at'} for row in products]
            digest = hashlib.sha256(json.dumps([canonical,variants],sort_keys=True,default=str).encode()).hexdigest()
            return {'revision':revision,'product_count':len(products),'product_hash':digest,
                    'deleted_count':sum(row.get('deleted_at') is not None for row in products)}
    finally: await database.dispose()

def main():
    before = asyncio.run(snapshot())
    if before['revision'] == '20261112_0009':
        print(json.dumps({'ok':True,'already_applied':True,'integrity':asyncio.run(audit())})); return
    if before['revision'] != '20261112_0008': raise RuntimeError('Unexpected installed revision; nothing changed')
    if not asyncio.run(audit(preflight_only=True))['ok']: raise RuntimeError('Preflight integrity failed; nothing changed')
    print(json.dumps({'stage':'reviewed_plan','from':before['revision'],'to':'20261112_0009',
                      'product_count':before['product_count'],'change':'nullable stock_movements.ttb_number; no stock changes'}),flush=True)
    if '--apply' not in sys.argv: return
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    directory = BACKEND/'private'/'backups';directory.mkdir(parents=True,exist_ok=True)
    output = directory/('stock-ttb-before-0009-'+stamp+'.sql')
    settings = MySQLSettings.from_env(); environment=os.environ.copy();environment['MYSQL_PWD']=settings.password
    args=[r'C:\xampp\mysql\bin\mysqldump.exe','--host='+settings.host,'--port='+str(settings.port),'--user='+settings.username,
          '--single-transaction','--quick','--routines','--events','--triggers','--hex-blob','--default-character-set=utf8mb4','--result-file='+str(output),settings.database]
    backup=subprocess.run(args,env=environment,capture_output=True,text=True)
    if backup.returncode or not output.exists() or b'Dump completed on' not in output.read_bytes():
        output.with_suffix('.error.txt').write_text(backup.stderr,encoding='utf-8')
        raise RuntimeError('Backup incomplete; migration not run')
    print(json.dumps({'stage':'backup_complete','path':str(output.relative_to(BACKEND)),'bytes':output.stat().st_size}),flush=True)
    migration=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=BACKEND,capture_output=True,text=True)
    (BACKEND/'private'/'stock-ttb-migration.log').write_text(migration.stdout+'\n'+migration.stderr,encoding='utf-8')
    if migration.returncode: raise RuntimeError('Migration failed; inspect private/stock-ttb-migration.log before retrying')
    after=asyncio.run(snapshot()); integrity=asyncio.run(audit())
    report={'ok':integrity['ok'] and before['product_hash']==after['product_hash'] and after['deleted_count']==before['deleted_count'],
            'revision':after['revision'],'backup':str(output.relative_to(BACKEND)),
            'backup_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'existing_product_data_unchanged':before['product_hash']==after['product_hash'],
            'before_product_count':before['product_count'],'after_product_count':after['product_count'],
            'deleted_product_count':after['deleted_count'],'integrity':integrity,'backend_started':False}
    (BACKEND/'private'/'stock-ttb-migration-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
    if not report['ok']: raise RuntimeError('Post-migration verification needs review; inspect private report')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(json.dumps({'ok':False,'error_type':type(exc).__name__,'details':'check private migration log'}));raise SystemExit(1)
