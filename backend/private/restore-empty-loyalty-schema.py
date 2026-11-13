"""Remove only this run's verified empty 0005 tables after DML rollback."""
import asyncio,json
from pathlib import Path
from sqlalchemy import text
from mysql.check_integrity import load_loyalty_revision
from mysql.config import MySQLSettings
from mysql.database import Database
async def main():
    revision=load_loyalty_revision()
    backup=json.loads(sorted(Path('private/backups').glob('loyalty-before-0005-*.json'))[-1].read_text(encoding='utf-8'))
    d=Database(MySQLSettings.from_env())
    try:
        async with d.engine.connect() as c:
            assert (await c.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()=='20261110_0004'
            names=set((await c.execute(text("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE'"))).scalars().all())
            assert names==set(backup['before_row_counts'])|set(revision.ALL_TABLES)
            for table in revision.ALL_TABLES:
                assert (await c.exec_driver_sql('SELECT COUNT(*) FROM `'+table+'`')).scalar_one()==0,'Refusing to remove a nonempty table'
            for table,count in backup['before_row_counts'].items():
                assert (await c.exec_driver_sql('SELECT COUNT(*) FROM `'+table+'`')).scalar_one()==count,'Historical rows changed'
            for table in reversed(revision.ALL_TABLES): await c.exec_driver_sql('DROP TABLE `'+table+'`')
            await c.commit()
            print(json.dumps({'removed_only_verified_empty_new_tables':len(revision.ALL_TABLES),'historical_tables_unchanged':True,'revision':'20261110_0004'}))
    finally:await d.dispose()
asyncio.run(main())
