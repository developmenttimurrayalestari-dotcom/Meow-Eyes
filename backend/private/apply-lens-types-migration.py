"""Back up the store and add only the Lens Index classification bridge."""
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
            tables = ('products', 'product_variants', 'lens_indexes', 'categories', 'product_categories')
            values = {table: [dict(row) for row in (await connection.execute(text('SELECT * FROM ' + table))).mappings()] for table in tables}
            canonical = {table: sorted((json.dumps(row, default=str, sort_keys=True) for row in rows)) for table, rows in values.items()}
            return {'revision': revision, 'counts': {table: len(rows) for table, rows in values.items()},
                    'catalog_hash': hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()}
    finally: await db.dispose()


def main():
    before = asyncio.run(snapshot())
    if before['revision'] == '20261112_0010':
        result = {'ok': True, 'already_applied': True, 'integrity': asyncio.run(audit())}
        print(json.dumps(result)); return
    if before['revision'] != '20261112_0009': raise RuntimeError('Unexpected installed revision; no migration applied')
    if not asyncio.run(audit(preflight_only=True))['ok']: raise RuntimeError('Preflight failed; no migration applied')
    print(json.dumps({'stage': 'reviewed_plan', 'from': before['revision'], 'to': '20261112_0010',
                      'change': 'new lens_index_types bridge; existing catalog and stock are preserved; admin assigns lens types',
                      'counts': before['counts']}), flush=True)
    if '--apply' not in sys.argv: return
    directory = ROOT / 'private/backups'; directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_path = directory / ('lens-index-types-before-0010-' + stamp + '.sql')
    settings = MySQLSettings.from_env(); environment = os.environ.copy(); environment['MYSQL_PWD'] = settings.password
    backup = subprocess.run([r'C:\xampp\mysql\bin\mysqldump.exe', '--host=' + settings.host, '--port=' + str(settings.port),
        '--user=' + settings.username, '--single-transaction', '--quick', '--routines', '--events', '--triggers',
        '--hex-blob', '--default-character-set=utf8mb4', '--result-file=' + str(backup_path), settings.database],
        env=environment, capture_output=True, text=True)
    if backup.returncode or not backup_path.exists() or b'Dump completed on' not in backup_path.read_bytes():
        (ROOT / 'private/lens-types-backup-error.log').write_text(backup.stderr, encoding='utf-8')
        raise RuntimeError('Backup incomplete; migration not run')
    print(json.dumps({'stage': 'backup_complete', 'path': str(backup_path.relative_to(ROOT)), 'bytes': backup_path.stat().st_size}), flush=True)
    migration = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', '20261112_0010'], cwd=ROOT, capture_output=True, text=True)
    (ROOT / 'private/lens-types-migration.log').write_text(migration.stdout + '\n' + migration.stderr, encoding='utf-8')
    if migration.returncode: raise RuntimeError('Migration failed; inspect private migration log before retrying')
    after = asyncio.run(snapshot()); integrity = asyncio.run(audit())
    report = {'ok': integrity['ok'] and before['catalog_hash'] == after['catalog_hash'],
              'revision': after['revision'], 'backup': str(backup_path.relative_to(ROOT)),
              'backup_sha256': hashlib.sha256(backup_path.read_bytes()).hexdigest(),
              'catalog_prices_product_tags_and_stock_unchanged': before['catalog_hash'] == after['catalog_hash'],
              'counts': after['counts'], 'lens_type_mapping': 'admin configures existing indexes',
              'integrity': integrity, 'backend_started': False}
    (ROOT / 'private/lens-types-migration-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
    if not report['ok']: raise RuntimeError('Post-migration checks need review')


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print(json.dumps({'ok': False, 'error_type': type(error).__name__, 'details': 'check private migration logs'})); raise SystemExit(1)
