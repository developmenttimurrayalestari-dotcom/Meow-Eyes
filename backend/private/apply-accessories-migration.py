"""Back up the store and update only product/category validation guards for Accessories."""
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
from mysql.check_integrity import audit

ROOT = Path(__file__).resolve().parents[1]


async def snapshot():
    db = Database(MySQLSettings.from_env())
    try:
        async with db.engine.connect() as connection:
            revision = (await connection.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()
            tables = ('users', 'user_permissions', 'user_sessions', 'categories', 'products', 'product_categories', 'product_variants', 'orders')
            values = {table: [dict(row) for row in (await connection.execute(text('SELECT * FROM ' + table))).mappings()] for table in tables}
            canonical = {table: sorted((json.dumps(row, default=str, sort_keys=True) for row in rows)) for table, rows in values.items()}
            return {'revision': revision, 'counts': {table: len(rows) for table, rows in values.items()},
                    'account_and_catalog_hash': hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()}
    finally: await db.dispose()


def main():
    before = asyncio.run(snapshot())
    if before['revision'] == '20261112_0012':
        result = {'ok': True, 'already_applied': True, 'integrity': asyncio.run(audit())}
        print(json.dumps(result)); return
    if before['revision'] != '20261112_0011': raise RuntimeError('Unexpected installed revision; no migration applied')
    if not asyncio.run(audit(preflight_only=True))['ok']: raise RuntimeError('Preflight failed; no migration applied')
    print(json.dumps({'stage': 'reviewed_plan', 'from': before['revision'], 'to': '20261112_0012',
                      'change': 'replace four product/category guards to accept accessories; no row or table replacement',
                      'counts': before['counts']}), flush=True)
    if '--apply' not in sys.argv: return
    directory = ROOT / 'private/backups'; directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_path = directory / ('accessories-before-0012-' + stamp + '.sql')
    settings = MySQLSettings.from_env(); environment = os.environ.copy(); environment['MYSQL_PWD'] = settings.password
    backup = subprocess.run([r'C:\xampp\mysql\bin\mysqldump.exe', '--host=' + settings.host, '--port=' + str(settings.port),
        '--user=' + settings.username, '--single-transaction', '--quick', '--routines', '--events', '--triggers',
        '--hex-blob', '--default-character-set=utf8mb4', '--result-file=' + str(backup_path), settings.database],
        env=environment, capture_output=True, text=True)
    if backup.returncode or not backup_path.exists() or b'Dump completed on' not in backup_path.read_bytes():
        (ROOT / 'private/accessories-backup-error.log').write_text(backup.stderr, encoding='utf-8')
        raise RuntimeError('Backup incomplete; migration not run')
    print(json.dumps({'stage': 'backup_complete', 'path': str(backup_path.relative_to(ROOT)), 'bytes': backup_path.stat().st_size}), flush=True)
    migration = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', '20261112_0012'], cwd=ROOT, capture_output=True, text=True)
    (ROOT / 'private/accessories-migration.log').write_text(migration.stdout + '\n' + migration.stderr, encoding='utf-8')
    if migration.returncode: raise RuntimeError('Migration failed; inspect private migration log before retrying')
    after = asyncio.run(snapshot()); integrity = asyncio.run(audit())
    report = {'ok': integrity['ok'] and before['account_and_catalog_hash'] == after['account_and_catalog_hash'],
              'revision': after['revision'], 'backup': str(backup_path.relative_to(ROOT)),
              'backup_sha256': hashlib.sha256(backup_path.read_bytes()).hexdigest(),
              'existing_accounts_permissions_sessions_and_stock_unchanged': before['account_and_catalog_hash'] == after['account_and_catalog_hash'],
              'counts': after['counts'], 'category_creation': 'admin creates the Accessories master; no store rows are seeded by this migration',
              'integrity': integrity, 'backend_started': False}
    (ROOT / 'private/accessories-migration-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
    if not report['ok']: raise RuntimeError('Post-migration checks need review')


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print(json.dumps({'ok': False, 'error_type': type(error).__name__, 'details': 'check private migration logs'})); raise SystemExit(1)
