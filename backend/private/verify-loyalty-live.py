"""Read-only HTTP smoke and rolled-back immutable-ledger guard probes."""
import asyncio,json
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from mysql.config import MySQLSettings
from mysql.database import Database

def get(path):
    try:
        with urlopen('http://127.0.0.1:8001/api'+path,timeout=10) as response:return response.status,json.loads(response.read())
    except HTTPError as error:return error.code,None

async def main():
    report={}
    status,health=get('/health/ready');assert status==200 and health['ok'];report['backend_ready']=True
    status,data=get('/games');assert status==200 and {g['key'] for g in data['games']}=={'matching','roulette','slide-puzzle','space-war'};report['public_games']=len(data['games'])
    status,data=get('/games/puzzle-levels');assert status==200 and len(data['levels'])==20;report['puzzle_levels']=20
    status,data=get('/try-on/catalog');assert status==200;report['vto_catalog_available']=True;report['vto_products']=len(data['products'])
    for path in ('/points/logs','/admin/points/settings','/admin/points/customers','/admin/games','/admin/returns','/returns/evidence/unauthorized'):
        assert get(path)[0]==401,path
    report['unauthenticated_private_routes_rejected']=True
    d=Database(MySQLSettings.from_env())
    try:
        async with d.engine.connect() as c:
            guards={}
            for table,statement in {
                'point_history':'UPDATE point_history SET delta=delta WHERE id=:id',
                'point_rate_versions':'UPDATE point_rate_versions SET rate=rate WHERE version=:id',
                'point_lots':'UPDATE point_lots SET rate_snapshot=rate_snapshot+1 WHERE id=:id'}.items():
                key='version' if table=='point_rate_versions' else 'id'
                identity=(await c.execute(text('SELECT '+key+' FROM '+table+' LIMIT 1'))).scalar_one()
                await c.rollback()
                try:
                    await c.execute(text(statement),{'id':identity})
                    guards[table]=False
                except DBAPIError as error:guards[table]=(getattr(error.orig,'args',(None,))[0]==1644)
                finally:await c.rollback()
            assert all(guards.values()),'Immutable point guard probe failed'
            report['live_immutable_guards']=guards
    finally:await d.dispose()
    report['ok']=True
    Path('private/loyalty-live-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
asyncio.run(main())
