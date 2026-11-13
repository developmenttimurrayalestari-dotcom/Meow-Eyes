"""Private, credential-safe snapshot before applying optional-frame migration."""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from sqlalchemy import text
from mysql.config import MySQLSettings
from mysql.database import Database, check_server_compatibility


async def counts(expected_revision='20261109_0003'):
    settings = MySQLSettings.from_env()
    database = Database(settings)
    try:
        async with database.engine.connect() as connection:
            compatibility = await check_server_compatibility(connection)
            if not compatibility.ready:
                raise RuntimeError('Database compatibility preflight failed')
            revision = (await connection.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()
            if revision != expected_revision:
                raise RuntimeError('Unexpected installed schema revision')
            active = (await connection.execute(text("SELECT COUNT(*) FROM information_schema.PROCESSLIST WHERE DB = DATABASE() AND ID <> CONNECTION_ID() AND COMMAND <> 'Sleep'"))).scalar_one()
            if active:
                raise RuntimeError('Other database queries are active; retry after writers are paused')
            tables = (await connection.execute(text("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"))).scalars().all()
            result = {}
            for table in tables:
                result[table] = (await connection.exec_driver_sql('SELECT COUNT(*) FROM `' + table.replace('`', '``') + '`')).scalar_one()
            return settings, result
    finally:
        await database.dispose()


def main():
    settings, before = asyncio.run(counts())
    directory = BACKEND / 'private' / 'backups'
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = directory / ('meowsurement-before-0004-' + stamp + '.sql')
    environment = os.environ.copy()
    environment['MYSQL_PWD'] = settings.password
    args = [r'C:\xampp\mysql\bin\mysqldump.exe', '--host=' + settings.host, '--port=' + str(settings.port), '--user=' + settings.username,
            '--single-transaction', '--quick', '--routines', '--events', '--triggers', '--hex-blob', '--default-character-set=utf8mb4',
            '--result-file=' + str(output), settings.database]
    result = subprocess.run(args, env=environment, capture_output=True, text=True)
    if result.returncode or not output.is_file() or output.stat().st_size == 0:
        # MySQL error text can include connection details; keep it in private QA.
        output.with_suffix('.error.txt').write_text(result.stderr, encoding='utf-8')
        raise RuntimeError('Database backup failed; private error report saved. Migration must not continue.')
    raw = output.read_bytes()
    if b'Dump completed on' not in raw:
        raise RuntimeError('Backup completion marker missing. Migration must not continue.')
    report = {'before_revision': '20261109_0003', 'backup': str(output.relative_to(BACKEND)), 'backup_bytes': len(raw),
              'sha256': hashlib.sha256(raw).hexdigest(), 'before_row_counts': before, 'application_table_count': len(before) - 1}
    report_path = directory / ('meowsurement-before-0004-' + stamp + '.json')
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'before_row_counts'}))
    print('report=' + str(report_path.relative_to(BACKEND)))


if __name__ == '__main__':
    main()
