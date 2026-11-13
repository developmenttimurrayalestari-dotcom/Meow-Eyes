"""Read-only frame selector diagnosis against actual MySQL and source routes."""
import asyncio,json
from pathlib import Path
from fastapi import FastAPI
import httpx
from sqlalchemy import text
import database
from auth import current_user
from models import User
from mysql.config import MySQLSettings
from mysql.database import Database
import routes_admin
async def main():
    db=Database(MySQLSettings.from_env());database.configure_session_factory(db.session_factory)
    try:
        async with db.engine.connect() as c:
            groups=[dict(row) for row in (await c.execute(text("SELECT product_type,deleted_at IS NOT NULL AS deleted,is_active,COUNT(*) AS count FROM products GROUP BY product_type,deleted_at IS NOT NULL,is_active"))).mappings()]
        app=FastAPI();app.include_router(routes_admin.router,prefix='/api')
        app.dependency_overrides[current_user]=lambda:User(user_id='readonly',email='qa@example.com',name='QA',role='admin')
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            response=await client.get('/api/admin/products',params={'try_on_eligible':True,'q':'','limit':100})
            report={'groups':groups,'status':response.status_code,'available_products':response.json().get('total'),
                    'available_types':[p['product_type'] for p in response.json().get('products',[])],'read_only':True}
            Path('private/tryon-product-options-report.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8');print(json.dumps(report,default=str))
    finally:database.configure_session_factory(None);await db.dispose()
if __name__=='__main__':
    try:asyncio.run(main())
    except Exception as e:print(json.dumps({'ok':False,'error_type':type(e).__name__}));raise SystemExit(1)
