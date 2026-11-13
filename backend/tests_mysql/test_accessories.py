"""Accessories can be managed, filtered and purchased using the real routes."""
import asyncio
from sqlalchemy import select
from models import Product, User
from mysql import models as m
from mysql.commerce import priced_cart
from mysql.lenses import available_indexes
from tests_mysql.test_catalog_sql import sql_client, _workbook
import routes_shopping


def test_accessory_category_crud_product_inventory_filters_and_cart():
    async def scenario():
        async with sql_client() as (client, factory, auth):
            supported = (await client.get('/api/admin/categories')).json()['product_types']
            assert {'code': 'accessories', 'name': 'Aksesoris'} in supported
            created = await client.post('/api/admin/categories', json={
                'name': 'Aksesoris', 'group_type': 'product_type', 'code': 'accessories', 'is_active': True})
            assert created.status_code == 200, created.text
            category = created.json()['category']; cid = category['id']
            assert (await client.post('/api/admin/categories', json={
                'name': 'Aksesoris lain', 'group_type': 'product_type', 'code': 'accessories'})).status_code == 409
            assert (await client.put('/api/admin/categories/' + cid, json={
                'name': 'Aksesoris Kacamata', 'group_type': 'product_type'})).status_code == 200
            created = await client.post('/api/admin/products', json={
                'name': 'Kotak Kacamata', 'sku': 'CASE-001', 'description': '<p>Kotak pelindung</p>',
                'price': 15000, 'main_image': '/case.jpg', 'product_type': 'accessories', 'category_ids': [cid],
                'variants': [{'sku': 'CASE-001-BLACK', 'stock': 5}]})
            assert created.status_code == 200, created.text
            product = created.json()['product']; pid = product['id']
            assert Product(**product).product_type == 'accessories'
            assert product['primary_category_id'] == cid and product['category_ids'] == [cid]
            assert product['variants'][0]['stock'] == 5
            updated = await client.put('/api/admin/products/' + pid, json={'name': 'Kotak Kacamata Hitam', 'product_type': 'accessories'})
            assert updated.status_code == 200, updated.text
            for params in ({'product_type': 'accessories'}, {'category_ids': cid}):
                result = await client.get('/api/products', params=params)
                assert result.status_code == 200, result.text
                assert [item['id'] for item in result.json()['products']] == [pid]
            assert (await client.delete('/api/admin/categories/' + cid)).status_code == 409
            assert (await client.post('/api/admin/products/' + pid + '/duplicate')).status_code == 200
            async with factory() as s:
                row = await s.get(m.Product, pid)
                assert await available_indexes(s, row) == []
            # Accessories use the normal cart price without lens additions.
            client._transport.app.include_router(routes_shopping.router, prefix='/api')
            auth['user'] = User(user_id='customer', email='customer@example.com', name='Customer')
            result = await client.post('/api/cart', json={'product_id': pid, 'variant_id': product['variants'][0]['id'], 'quantity': 2})
            assert result.status_code == 200, result.text
            cart = (await client.get('/api/cart')).json()['items']
            assert len(cart) == 1 and cart[0]['product']['product_type'] == 'accessories'
            assert cart[0]['unit_price'] == 15000 and cart[0]['subtotal'] == 30000 and cart[0]['lens_price'] == 0
            async with factory() as s:
                items, _ = await priced_cart(s, 'customer', require_stock=True)
                assert sum(item.subtotal for item in items) == 30000
                assert (await s.scalar(select(m.ProductVariant).where(m.ProductVariant.product_id == pid))).stock == 5
    asyncio.run(scenario())


def test_accessories_spreadsheet_import_uses_the_same_supported_kinds():
    async def scenario():
        async with sql_client() as (client, factory, _):
            result = await client.post('/api/admin/categories', json={
                'name': 'Aksesoris', 'group_type': 'product_type', 'code': 'accessories'})
            assert result.status_code == 200, result.text
            category = result.json()['category']
            record = {'product_name': 'Kotak Impor', 'product_type': 'accessories', 'product_slug': 'kotak-impor',
                      'main_category': category['slug'], 'variant_sku': 'IMPORT-CASE', 'variant_price': 12500,
                      'variant_stock': 3, 'is_active': 1}
            data = _workbook([record])
            result = await client.post('/api/admin/products/import/preview', files={'file': ('accessories.xlsx', data)})
            assert result.status_code == 200 and result.json()['valid'] == 1, result.text
            result = await client.post('/api/admin/products/import/commit', files={'file': ('accessories.xlsx', data)})
            assert result.status_code == 200 and result.json()['created'] == 1, result.text
            async with factory() as s:
                product = await s.scalar(select(m.Product).where(m.Product.slug == 'kotak-impor'))
                assert product.product_type == 'accessories' and product.primary_category_id == category['id']
                assert (await s.scalar(select(m.ProductVariant).where(m.ProductVariant.product_id == product.id))).stock == 3
    asyncio.run(scenario())
