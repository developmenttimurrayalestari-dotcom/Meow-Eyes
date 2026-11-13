import asyncio,json
from sqlalchemy import text
from mysql.config import MySQLSettings
from mysql.database import Database
from mysql.check_integrity import load_loyalty_revision
async def main():
 d=Database(MySQLSettings.from_env())
 try:
  async with d.engine.connect() as c:
   revision=(await c.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()
   counts={t:(await c.exec_driver_sql('SELECT COUNT(*) FROM `'+t+'`')).scalar_one() for t in load_loyalty_revision().ALL_TABLES}
   print(json.dumps({'revision':revision,'new_counts':counts}))
 finally:await d.dispose()
asyncio.run(main())
