"""Read-only real MySQL route checks through ASGI, without starting a server."""
import asyncio
import json
from pathlib import Path
from fastapi import FastAPI
import httpx
from sqlalchemy import select, func
import database
from auth import current_user, current_user_optional
from models import User
from mysql import models as m
from mysql.config import MySQLSettings
from mysql.database import Database
import routes_admin
import routes_catalog

async def main():
    db=Database(MySQLSettings.from_env()); database.configure_session_factory(db.session_factory)
    app=FastAPI(); app.include_router(routes_admin.router,prefix='/api');app.include_router(routes_catalog.router,prefix='/api')
    app.dependency_overrides[current_user]=lambda:User(user_id='qa-read-only',email='qa@example.com',name='QA',role='super_admin')
    app.dependency_overrides[current_user_optional]=lambda:None
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            response=await client.get('/api/admin/categories'); assert response.status_code==200
            rows=response.json()['categories']; assert len(rows)==74
            assert all('parent_id' not in row and 'level' not in row and 'children' not in row for row in rows)
            assert len((await client.get('/api/categories?group_type=material')).json()['categories'])==3
            ids={row['code']:row['id'] for row in rows if row['group_type']=='material'}
            male=next(row['id'] for row in rows if row['group_type']=='gender' and row['code']=='pria')
            filtered=await client.get('/api/products',params={'category_ids':ids['acetate']+','+male,'limit':100})
            assert filtered.status_code==200, filtered.status_code
            async with db.session() as s:
                expected=set((await s.scalars(select(m.Product.id).where(m.Product.is_active.is_(True),
                    m.Product.id.in_(select(m.ProductCategory.product_id).where(m.ProductCategory.category_id==ids['acetate'])),
                    m.Product.id.in_(select(m.ProductCategory.product_id).where(m.ProductCategory.category_id==male))))).all())
                tag_count=await s.scalar(select(func.count()).select_from(m.ProductCategory))
            assert {p['id'] for p in filtered.json()['products']}==expected
            listing=await client.get('/api/products?limit=100'); assert listing.status_code==200
            if listing.json()['products']:
                item=listing.json()['products'][0]
                detail=await client.get('/api/products/'+item['slug']); assert detail.status_code==200
                assert 'category_ids' in detail.json()['product']
            report={'ok':True,'real_mysql_asgi':True,'list_master_categories':len(rows),'product_tag_count':tag_count,
                    'catalog_total':listing.json()['total'],'combined_filter_matches':len(expected),'backend_server_started':False}
            Path('private/flat-master-runtime-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(json.dumps(report))
    finally:
        database.configure_session_factory(None); await db.dispose()

if __name__=='__main__':
    try:asyncio.run(main())
    except Exception as exc:
        print(json.dumps({'ok':False,'error_type':type(exc).__name__}));raise SystemExit(1)
