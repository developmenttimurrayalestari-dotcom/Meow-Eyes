import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'flash-validation-tools'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from mysql.config import MySQLSettings
from mysql.database import Database
from mysql.models import CMSPage

async def main():
    database = Database(MySQLSettings.from_env())
    try:
        async with database.session_factory() as session:
            result = await session.execute(select(CMSPage.slug, CMSPage.title, CMSPage.status, CMSPage.page_type).order_by(CMSPage.slug))
            print(json.dumps([dict(row._mapping) for row in result], ensure_ascii=False, indent=2))
    finally:
        await database.dispose()

try:
    asyncio.run(main())
except Exception as exc:
    print(json.dumps({'ok': False, 'error_type': type(exc).__name__}))
    sys.exit(2)
