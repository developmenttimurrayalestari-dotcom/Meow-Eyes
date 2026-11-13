"""Idempotent initial master data. Run after alembic upgrade head."""
import asyncio
import json
from .config import MySQLSettings
from .database import Database
from .taxonomy import seed_masters

async def main():
    database = Database(MySQLSettings.from_env())
    try:
        async with database.session() as session:
            async with session.begin():
                await seed_masters(session)
        print(json.dumps({'ok':True,'initial_master_definitions':23}))
    finally:
        await database.dispose()

if __name__ == '__main__':
    asyncio.run(main())
