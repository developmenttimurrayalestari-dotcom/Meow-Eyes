"""Read-only ASGI and SQL validation; no server, cart edit, or order creation."""
import asyncio
import json
from sqlalchemy import select
from fastapi import FastAPI
import httpx
from auth import current_user
from database import configure_session_factory
from models import User
from mysql.config import MySQLSettings
from mysql.database import Database
from mysql import models as m
from mysql.lenses import available_indexes
import routes_admin_content
import routes_content


async def main():
    db = Database(MySQLSettings.from_env()); configure_session_factory(db.session_factory)
    try:
        app = FastAPI()
        app.dependency_overrides[current_user] = lambda: User(user_id='qa-readonly', email='qa@example.com', name='Read-only QA', role='admin')
        app.include_router(routes_admin_content.router, prefix='/api')
        app.include_router(routes_content.router, prefix='/api')
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            admin = await client.get('/api/admin/lens/indexes')
            public = await client.get('/api/lens/indexes')
            assert admin.status_code == public.status_code == 200
            assert all('lens_type_ids' in index and 'lens_types' in index for index in admin.json()['items'])
            active_count = len(public.json()['items'])
        async with db.session_factory() as s:
            products = list((await s.scalars(select(m.Product).where(m.Product.product_type.in_(('frame', 'package')),
                m.Product.deleted_at.is_(None), m.Product.is_active.is_(True)))).all())
            frame_counts, package_counts = [], []
            for product in products:
                choices = len(await available_indexes(s, product))
                if product.product_type == 'frame':
                    assert choices == active_count
                    frame_counts.append(choices)
                else: package_counts.append(choices)
        report = {'ok': True, 'admin_api': admin.status_code, 'public_api': public.status_code,
                  'active_indexes': active_count, 'frame_product_count': len(frame_counts),
                  'package_product_count': len(package_counts), 'package_choice_counts': package_counts,
                  'existing_type_mapping': 'admin will configure', 'read_only': True, 'backend_started': False}
        print(json.dumps(report))
    finally: await db.dispose()


if __name__ == '__main__':
    try: asyncio.run(main())
    except Exception as error:
        print(json.dumps({'ok': False, 'error_type': type(error).__name__})); raise SystemExit(1)
