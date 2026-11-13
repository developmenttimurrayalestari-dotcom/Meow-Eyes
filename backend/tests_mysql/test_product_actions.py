"""Product deletion and deactivation have different, atomic lifecycle effects."""
import asyncio
from decimal import Decimal
import pytest
from sqlalchemy import select
from mysql import models as m
from tests_mysql.test_catalog_sql import sql_client


async def second_product(factory):
    async with factory.begin() as s:
        s.add(m.Product(id='second',name='Second',slug='second',sku='SECOND',description='',main_image='',price=Decimal('200')))


def test_deactivation_keeps_admin_listing_and_can_be_reactivated():
    async def run():
        async with sql_client() as (client,factory,_):
            await second_product(factory)
            response = await client.post('/api/admin/products/bulk-actions', json={'action':'deactivate','product_ids':['product','second','product']})
            assert response.status_code == 200, response.text
            assert response.json()['changed_count'] == 2
            assert (await client.get('/api/products')).json()['total'] == 0
            admin = (await client.get('/api/admin/products')).json()
            assert admin['total'] == 2 and all(not item['is_active'] for item in admin['products'])
            async with factory() as s:
                assert (await s.get(m.Product,'product')).deleted_at is None
                variant = await s.get(m.ProductVariant,'variant')
                assert (variant.stock,variant.reserved) == (10,2)
            assert (await client.put('/api/admin/products/product',json={'is_active':True})).status_code == 200
            assert (await client.get('/api/products')).json()['total'] == 1
    asyncio.run(run())


def test_delete_removes_admin_and_public_access_preserves_order_and_stock_history():
    async def run():
        async with sql_client() as (client,factory,_):
            async with factory.begin() as s:
                s.add(m.Order(id='order',order_number='ORD-DELETE-QA',user_id='customer',subtotal=100,shipping_courier='jne',shipping_service='REG',shipping_cost=0,total=100))
                await s.flush()
                s.add(m.OrderItem(id='line',order_id='order',product_id='product',variant_id='variant',product_name='Original frame',sku='VARIANT',quantity=1,unit_price=100,subtotal=100,sort_order=0))
                s.add(m.StockMovement(id='movement',product_id='product',variant_id='variant',type='stock_in',quantity=10,delta=10,reserved_delta=0,stock_after=10,reserved_after=2,note='Original stock',admin_id='admin'))
            response = await client.delete('/api/admin/products/product')
            assert response.status_code == 200 and response.json()['changed_count'] == 1
            assert (await client.get('/api/admin/products')).json()['total'] == 0
            assert (await client.get('/api/admin/products/product')).status_code == 404
            assert (await client.get('/api/products')).json()['total'] == 0
            assert (await client.get('/api/products/frame')).status_code == 404
            assert (await client.put('/api/admin/products/product',json={'is_active':True})).status_code == 404
            assert (await client.post('/api/admin/products/product/stock',json={'variant_id':'variant','delta':1})).status_code == 404
            async with factory() as s:
                product = await s.get(m.Product,'product')
                assert product.deleted_at is not None and not product.is_active
                assert (await s.get(m.OrderItem,'line')).product_name == 'Original frame'
                assert (await s.get(m.Order,'order')).total == Decimal('100')
                assert (await s.get(m.StockMovement,'movement')).stock_after == 10
                variant = await s.get(m.ProductVariant,'variant')
                assert (variant.stock,variant.reserved) == (10,2)
            repeated = await client.delete('/api/admin/products/product')
            assert repeated.status_code == 200 and repeated.json()['changed_count'] == 0
            assert (await client.post('/api/admin/products/bulk-actions',json={'action':'deactivate','product_ids':['product']})).json()['changed_count'] == 0
    asyncio.run(run())


def test_bulk_delete_is_all_or_nothing_and_idempotent():
    async def run():
        async with sql_client() as (client,factory,_):
            await second_product(factory)
            missing = await client.post('/api/admin/products/bulk-actions',json={'action':'delete','product_ids':['product','unknown']})
            assert missing.status_code == 404
            async with factory() as s:
                assert (await s.get(m.Product,'product')).deleted_at is None
            for expected_count in (2,0):
                response = await client.post('/api/admin/products/bulk-actions',json={'action':'delete','product_ids':['second','product']})
                assert response.status_code == 200, response.text
                assert response.json()['changed_count'] == expected_count
            assert (await client.get('/api/admin/products')).json()['total'] == 0
            async with factory() as s:
                assert (await s.get(m.Product,'product')).deleted_at == (await s.get(m.Product,'second')).deleted_at
    asyncio.run(run())


def test_pending_bundle_payment_can_complete_after_products_are_deleted(monkeypatch):
    from tests_mysql.test_optical_features import feature_client
    from mysql.commerce import create_checkout, confirm_mock_payment
    from database import read_session
    for key,value in {'APP_ENV':'test','ENABLE_MOCK_PAYMENTS':'1','PAYMENT_PROVIDER':'mock','SHIPPING_PROVIDER':'mock'}.items():
        monkeypatch.setenv(key,value)
    async def run():
        async with feature_client() as (client,auth,d,factory):
            result = await create_checkout(d['alice'],d['req'])
            order = result['order']
            auth['user'] = d['admin_user']
            deleted = await client.post('/api/admin/products/bulk-actions',json={'action':'delete','product_ids':[d['frame'],d['lens']]})
            assert deleted.status_code == 200, deleted.text
            await confirm_mock_payment(order['order_number'],d['alice'])
            async with read_session() as s:
                saved = await s.get(m.Order,order['id'])
                assert saved.payment_status == 'paid' and float(saved.total) == order['total']
                for key in ('vf','vl'):
                    variant = await s.get(m.ProductVariant,d[key])
                    assert variant.stock == 4 and variant.reserved == 0
                assert (await s.get(m.Product,d['frame'])).deleted_at is not None
                assert (await s.get(m.Product,d['lens'])).deleted_at is not None
    asyncio.run(run())


@pytest.mark.parametrize('payload',[
    {'action':'erase','product_ids':['product']},
    {'action':'delete','product_ids':[]},
    {'action':'delete','product_ids':['product']*201},
    {'action':'delete','product_ids':[' ']},
    {'action':'delete','product_ids':['p'*65]},
    {'action':'delete','product_ids':['product'],'is_active':True},
])
def test_bulk_validation_does_not_change_products(payload):
    async def run():
        async with sql_client() as (client,factory,_):
            response = await client.post('/api/admin/products/bulk-actions',json=payload)
            assert response.status_code == 422, response.text
            async with factory() as s:
                item = await s.get(m.Product,'product')
                assert item.is_active and item.deleted_at is None
    asyncio.run(run())


@pytest.mark.parametrize('role',['customer','staff'])
def test_non_admin_cannot_delete_or_bulk_deactivate(role):
    async def run():
        async with sql_client() as (client,factory,auth):
            auth['user'] = auth['user'].model_copy(update={'role':role,'permissions':['product.view','product.update']})
            assert (await client.delete('/api/admin/products/product')).status_code == 403
            assert (await client.post('/api/admin/products/bulk-actions',json={'action':'deactivate','product_ids':['product']})).status_code == 403
            async with factory() as s:
                assert (await s.get(m.Product,'product')).is_active
    asyncio.run(run())
