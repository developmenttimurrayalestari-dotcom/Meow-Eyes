import asyncio,json
from sqlalchemy import inspect
from sqlalchemy.dialects.mysql import dialect
from mysql.config import MySQLSettings
from mysql.database import Database
from mysql.check_integrity import load_loyalty_revision
async def main():
 d=Database(MySQLSettings.from_env());r=load_loyalty_revision()
 try:
  async with d.engine.connect() as c:
   def read(sync):
    output={}
    for table,shape in r.TABLE_SHAPE.items():
     actual={col['name']:(r.normalized_type(col['type'].compile(dialect=dialect())),col['nullable']) for col in inspect(sync).get_columns(table)}
     expected={name:(r.normalized_type(kind),nullable) for name,(kind,nullable) in shape['columns'].items()}
     output[table]=[{'column':name,'expected':value,'actual':actual.get(name)} for name,value in expected.items() if actual.get(name)!=value]
    return output
   print(json.dumps(await c.run_sync(read),indent=2))
 finally:await d.dispose()
asyncio.run(main())
