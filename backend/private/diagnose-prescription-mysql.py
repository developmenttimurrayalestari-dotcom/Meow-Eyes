"""Reproduce saves with temporary cart rows inside an always-rolled-back transaction."""
import asyncio
import hashlib
import json
from pathlib import Path
import traceback
import httpx
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from auth import current_user
from database import configure_session_factory
from models import User
from mysql import models as m
from mysql.config import MySQLSettings
from mysql.database import Database
from mysql.lenses import available_indexes
import routes_features


async def fingerprint(db):
    async with db.session_factory() as session:
        rows = (await session.execute(select(m.CartItem.id, m.CartItem.prescription_id, m.CartItem.lens_index_id).order_by(m.CartItem.id))).all()
        count = await session.scalar(select(func.count()).select_from(m.Prescription))
        return hashlib.sha256(json.dumps([list(row) for row in rows]).encode()).hexdigest(), count


async def main():
    db = Database(MySQLSettings.from_env()); results = []
    try:
        before = await fingerprint(db)
        async with db.session_factory() as session:
            carts = list((await session.scalars(select(m.CartItem).join(m.Product, m.Product.id == m.CartItem.product_id)
                .where(m.Product.deleted_at.is_(None), m.Product.is_active.is_(True))
                .order_by(m.CartItem.updated_at.desc()).limit(8))).all())
        for source in carts:
            async with db.engine.connect() as connection:
                outer = await connection.begin()
                factory = async_sessionmaker(bind=connection, expire_on_commit=False, autoflush=False, join_transaction_mode='create_savepoint')
                configure_session_factory(factory)
                try:
                    cart_id = 'qa_rx_' + m.new_id()
                    async with factory() as session, session.begin():
                        product = await session.get(m.Product, source.product_id)
                        indexes = await available_indexes(session, product)
                        upload = await session.scalar(select(m.Upload.id).where(m.Upload.uploaded_by == source.user_id,
                            m.Upload.visibility == 'private', m.Upload.mime == 'image/jpeg').limit(1))
                        session.add(m.CartItem(id=cart_id, user_id=source.user_id, product_id=source.product_id,
                            variant_id=source.variant_id, quantity=source.quantity,
                            lens_product_id=source.lens_product_id, lens_variant_id=source.lens_variant_id))
                    app = FastAPI(); app.include_router(routes_features.router, prefix='/api')
                    app.dependency_overrides[current_user] = lambda: User(user_id=source.user_id, email='qa@example.com', name='QA', role='customer')
                    payload = {key: None for key in ('od_sph','od_cyl','od_axis','od_add','os_sph','os_cyl','os_axis','os_add','pd_total','pd_right','pd_left')}
                    payload.update(notes='Temporary rollback diagnostic', attachment_upload_id=upload,
                        lens_index_id=indexes[0].id if indexes else None)
                    entry = {'product_type': product.product_type, 'has_photo': bool(upload), 'has_lens_index': bool(indexes)}
                    try:
                        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                            response = await client.patch(f'/api/cart/{cart_id}/prescription', json=payload)
                            entry['status'] = response.status_code
                            if response.status_code != 200: entry['detail'] = response.json().get('detail')
                    except Exception as error:
                        entry['error_type'] = type(error).__name__
                        entry['frames'] = [{'file': Path(frame.filename).name, 'line': frame.lineno, 'function': frame.name}
                            for frame in traceback.extract_tb(error.__traceback__)[-10:]]
                        (Path(__file__).parent/'prescription-mysql-exception.log').write_text(traceback.format_exc(), encoding='utf-8')
                    results.append(entry)
                finally:
                    await outer.rollback()
                    configure_session_factory(None)
        after = await fingerprint(db)
        assert after == before, 'Diagnostic rows were not fully rolled back'
        print(json.dumps({'cases': results, 'rolled_back': True, 'original_cart_and_prescription_counts_unchanged': True}))
    finally:
        configure_session_factory(None)
        await db.dispose()


if __name__ == '__main__':
    try: asyncio.run(main())
    except Exception as error:
        print(json.dumps({'ok': False, 'error_type': type(error).__name__})); raise SystemExit(1)
