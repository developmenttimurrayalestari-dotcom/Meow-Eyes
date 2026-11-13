"""Package lens eligibility and Frame surcharges must agree from cart to order."""
import asyncio
from decimal import Decimal
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from database import read_session, session_scope
from mysql import models as m
from mysql.commerce import checkout_quote, create_checkout, priced_cart
from mysql.lenses import replace_index_types
from tests_mysql.test_optical_features import feature_client


@pytest.fixture(autouse=True)
def mock_providers(monkeypatch):
    for key, value in {'APP_ENV': 'test', 'ENABLE_MOCK_PAYMENTS': '1', 'PAYMENT_PROVIDER': 'mock', 'SHIPPING_PROVIDER': 'mock'}.items():
        monkeypatch.setenv(key, value)


async def configured_cart(d):
    async with session_scope() as s:
        types = {c.code: c.id for c in (await s.scalars(select(m.Category).where(m.Category.group_type == 'lens_type'))).all()}
        await replace_index_types(s, d['index'], [types['single-vision']])
        for key, price, active in (('photo', 125, True), ('unassigned', 200, True), ('inactive', 400, False)):
            d[key] = d['prefix'] + '_' + key
            s.add(m.LensIndex(id=d[key], name=key, index_value='1.56', additional_price=price, is_active=active))
        await s.flush()
        await replace_index_types(s, d['photo'], [types['photochromic']])
        d['package'], d['pv'], d['pc'] = (d['prefix'] + suffix for suffix in ('_package', '_pv', '_pc'))
        s.add(m.Product(id=d['package'], name='Paket', slug=d['package'], sku=d['package'].upper(), price=5000,
                        product_type='package', description='Paket', main_image='/fixture.png', weight_gram=150, is_active=True))
        await s.flush()
        s.add(m.ProductCategory(product_id=d['package'], category_id=types['single-vision']))
        s.add(m.ProductVariant(id=d['pv'], product_id=d['package'], sku=d['pv'].upper(), stock=5, reserved=0, is_active=True))
        await s.flush()
        s.add(m.CartItem(id=d['pc'], user_id=d['alice'], product_id=d['package'], variant_id=d['pv'], quantity=2))
        (await s.get(m.CartItem, d['cart'])).quantity = 2
    return types


def test_package_filters_by_master_type_and_frame_gets_all_active_indexes():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            types = await configured_cart(d)
            frame = await client.get(f'/api/cart/{d["cart"]}/lens-options')
            assert frame.status_code == 200, frame.text
            assert {i['id'] for i in frame.json()['items']} == {d['index'], d['photo'], d['unassigned']}
            package = await client.get(f'/api/cart/{d["pc"]}/lens-options')
            assert package.status_code == 200 and package.json()['included_in_package']
            assert [i['id'] for i in package.json()['items']] == [d['index']]
            assert package.json()['lens_types'][0]['id'] == types['single-vision']
            endpoint = f'/api/cart/{d["pc"]}/prescription'
            for invalid in (d['photo'], d['inactive'], 'missing', 123):
                response = await client.patch(endpoint, json={'lens_index_id': invalid, 'notes': 'must rollback'})
                assert response.status_code == 422, response.text
            auth['user'] = d['bob_user']
            assert (await client.get(f'/api/cart/{d["pc"]}/lens-options')).status_code == 404
            assert (await client.patch(endpoint, json={'lens_index_id': d['index']})).status_code == 404
            async with read_session() as s:
                row = await s.get(m.CartItem, d['pc'])
                assert row.lens_index_id is None and row.prescription_id is None
    asyncio.run(run())


def test_frame_charges_per_unit_package_stays_fixed_and_both_snapshot_selected_index():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            await configured_cart(d)
            for cart_id, index_id, expected in ((d['cart'], d['photo'], 1125.10), (d['pc'], d['index'], 5000)):
                response = await client.patch(f'/api/cart/{cart_id}/prescription', json={'lens_index_id': index_id, 'notes': cart_id})
                assert response.status_code == 200, response.text
                row = response.json()['cart_item']
                assert row['unit_price'] == expected and row['subtotal'] == expected * 2
                assert row['lens_price'] == (125 if cart_id == d['cart'] else 0)
            req = d['req'].model_copy(update={'selected_item_ids': [d['cart'], d['pc']]})
            async with read_session() as s:
                preview = (await checkout_quote(s, await s.get(m.User, d['alice']), req)).payload()
                assert preview['product_subtotal'] == 12000.20
                assert preview['lens_subtotal'] == 250
                assert preview['subtotal'] == preview['product_subtotal'] + preview['lens_subtotal']
            order = (await create_checkout(d['alice'], req))['order']
            assert order['subtotal'] == 12250.20
            rows = {row['product_id']: row for row in order['items']}
            for product_id, index_id, surcharge in ((d['frame'], d['photo'], 125), (d['package'], d['index'], 0)):
                item = rows[product_id]
                assert item['prescription']['notes'] == (d['cart'] if product_id == d['frame'] else d['pc'])
                assert len(item['components']) == 1  # Index choices must not create extra stock reservations.
                component = item['components'][0]
                assert component['lens_index_id'] == index_id and component['index_surcharge'] == surcharge
                assert component['subtotal'] == item['subtotal'] and component['unit_price'] == item['unit_price']
            async with session_scope() as s:
                (await s.get(m.LensIndex, d['photo'])).additional_price = Decimal('9999')
            async with read_session() as s:
                component = await s.scalar(select(m.OrderItemComponent).where(m.OrderItemComponent.order_id == order['id'], m.OrderItemComponent.product_id == d['frame']))
                assert component.index_surcharge == Decimal('125.00') and component.unit_price == Decimal('1125.10')
    asyncio.run(run())


def test_admin_assigns_multiple_lens_types_and_invalid_assignments_roll_back():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            types = await configured_cart(d)
            auth['user'] = d['admin_user']
            created = await client.post('/api/admin/lens/indexes', json={'name': 'Universal', 'index_value': '1.60',
                'additional_price': 300, 'lens_type_ids': [types['single-vision'], types['photochromic']]})
            assert created.status_code == 200, created.text
            index_id = created.json()['item']['id']
            assert (await client.post('/api/admin/lens/indexes', json={'name': 'Invalid price', 'index_value': '1.60', 'additional_price': -1})).status_code == 422
            assert set(created.json()['item']['lens_type_ids']) == {types['single-vision'], types['photochromic']}
            assert (await client.put(f'/api/admin/lens/indexes/{index_id}', json={'additional_price': 350})).status_code == 200
            async with read_session() as s:
                gender_id = await s.scalar(select(m.Category.id).where(m.Category.group_type == 'gender').limit(1))
            invalid = await client.put(f'/api/admin/lens/indexes/{index_id}', json={'name': 'Should not persist', 'lens_type_ids': [gender_id]})
            assert invalid.status_code == 422, invalid.text
            listing = (await client.get('/api/admin/lens/indexes')).json()['items']
            saved = next(row for row in listing if row['id'] == index_id)
            assert saved['name'] == 'Universal' and saved['additional_price'] == 350
            assert set(saved['lens_type_ids']) == {types['single-vision'], types['photochromic']}
            auth['user'] = d['user']
            package = (await client.get(f'/api/cart/{d["pc"]}/lens-options')).json()
            assert {row['id'] for row in package['items']} == {d['index'], index_id}
            assert (await client.post('/api/admin/lens/indexes', json={'name': 'Denied', 'index_value': '1.60'})).status_code == 403
    asyncio.run(run())


def test_cart_add_accepts_index_only_and_keeps_it_separate_from_plain_cart():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            await configured_cart(d)
            added = await client.post('/api/cart', json={'product_id': d['frame'], 'variant_id': d['vf'], 'quantity': 1, 'lens_index_id': d['photo']})
            assert added.status_code == 200 and added.json()['id'] != d['cart'], added.text
            invalid = await client.post('/api/cart', json={'product_id': d['package'], 'variant_id': d['pv'], 'quantity': 1, 'lens_index_id': d['photo']})
            assert invalid.status_code == 422, invalid.text
            # Validate again at pricing/confirmation if a previously valid assignment changes.
            async with session_scope() as s:
                (await s.get(m.CartItem, d['pc'])).lens_index_id = d['photo']
            with pytest.raises(HTTPException) as failure:
                async with read_session() as s:
                    await priced_cart(s, d['alice'], [d['pc']])
            assert failure.value.status_code == 422
    asyncio.run(run())


def test_frame_only_checkout_does_not_require_lens_or_prescription():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            order = (await create_checkout(d['alice'], d['req']))['order']
            assert order['subtotal'] == 1000.10
            assert order['items'][0].get('prescription') is None
            assert len(order['items'][0]['components']) == 1
            assert order['items'][0]['components'][0]['lens_index_id'] is None
            assert order['items'][0]['components'][0]['index_surcharge'] == 0
            async with read_session() as s:
                assert not (await s.scalars(select(m.OrderItemPrescription).where(m.OrderItemPrescription.order_id == order['id']))).all()
    asyncio.run(run())


def test_frame_only_choice_removes_existing_bundle_charges_and_allows_empty_prescription():
    async def run():
        async with feature_client(bundle=True) as (client, auth, d, _):
            endpoint = f'/api/cart/{d["cart"]}/prescription'
            invalid = await client.patch(endpoint, json={'frame_only': True, 'lens_index_id': d['index']})
            assert invalid.status_code == 422
            async with read_session() as s:
                assert (await s.get(m.CartItem, d['cart'])).lens_product_id == d['lens']
            payload = {key: None for key in ('od_sph','od_cyl','od_axis','od_add','os_sph','os_cyl','os_axis','os_add','pd_total','pd_right','pd_left')}
            payload.update(frame_only=True, lens_index_id=None, notes='', attachment_upload_id=None)
            response = await client.patch(endpoint, json=payload)
            assert response.status_code == 200, response.text
            row = response.json()['cart_item']
            assert row['lens_product'] is row['lens_variant'] is row['lens_index'] is row['prescription'] is None
            assert row['lens_price'] == 0 and row['unit_price'] == 1000.10
            order = (await create_checkout(d['alice'], d['req']))['order']
            assert order['subtotal'] == 1000.10 and order['items'][0].get('prescription') is None
            async with read_session() as s:
                assert await s.get(m.Prescription, d['rx']) is not None  # Retain source history.
                assert (await s.get(m.ProductVariant, d['vl'])).reserved == 0
    asyncio.run(run())
