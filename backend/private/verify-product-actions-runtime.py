"""Read-only API checks against actual MySQL; no listening server or mutations."""
import asyncio,json
from pathlib import Path
from fastapi import FastAPI
import httpx
import database
from auth import current_user,current_user_optional
from models import User
from mysql.config import MySQLSettings
from mysql.database import Database
import routes_admin,routes_catalog

async def main():
    db=Database(MySQLSettings.from_env());database.configure_session_factory(db.session_factory)
    app=FastAPI();app.include_router(routes_admin.router,prefix='/api');app.include_router(routes_catalog.router,prefix='/api')
    app.dependency_overrides[current_user]=lambda:User(user_id='read-only-qa',email='qa@example.com',name='QA',role='super_admin')
    app.dependency_overrides[current_user_optional]=lambda:None
    try:
        ready=await db.check_readiness();assert ready.ready
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            admin=await client.get('/api/admin/products?limit=200');assert admin.status_code==200
            public=await client.get('/api/products?limit=100');assert public.status_code==200
            masters=await client.get('/api/admin/categories');assert masters.status_code==200
            inventory=await client.get('/api/admin/inventory');assert inventory.status_code==200
            assert {row['product_id'] for row in inventory.json()['items']}=={row['id'] for row in admin.json()['products']}
            assert all(not row['can_adjust'] and row['deleted_at'] for row in inventory.json()['deleted_items'])
            assert len(masters.json()['groups'])==5
            assert all(row['group_type']!='collection' for row in masters.json()['categories'])
            assert all(item['deleted_at'] is None for item in admin.json()['products'])
            if admin.json()['products']:
                pid=admin.json()['products'][0]['id']
                assert (await client.get('/api/admin/products/'+pid)).status_code==200
            report={'ok':True,'real_mysql_asgi':True,'schema_ready':True,'admin_products':admin.json()['total'],
                    'master_groups':len(masters.json()['groups']),'visible_masters':len(masters.json()['categories']),
                    'inventory_items':len(inventory.json()['items']),'deleted_inventory_items':len(inventory.json()['deleted_items']),
                    'public_products':public.json()['total'],'backend_server_started':False,'product_mutations':0}
            Path('private/product-actions-runtime-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(json.dumps(report))
    finally: database.configure_session_factory(None);await db.dispose()

if __name__=='__main__':
    try:asyncio.run(main())
    except Exception as exc:print(json.dumps({'ok':False,'error_type':type(exc).__name__}));raise SystemExit(1)
