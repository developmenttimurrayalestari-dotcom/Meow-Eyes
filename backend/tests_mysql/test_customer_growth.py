"""Customer benefits and compound purchase invariants, with no outbound calls."""
import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from database import session_scope, read_session
from models import CartItemCreate, AddressCreate
from mysql import models as m, customer_growth as growth, points
from mysql.base import utcnow
from mysql.commerce import create_checkout, checkout_quote, lock_user, expire_order, confirm_mock_payment
from mysql.integration_services import _booking_payload, _rate_options, _tracking_update
from integrations.config import DokuSettings
from integrations.doku_payload import enrich_request
from routes_shopping import add_to_cart, create_review
from tests_mysql.commerce_scenarios import seed_commerce_fixture
from tests_mysql.sql_helpers import isolated_database


@pytest.fixture(autouse=True)
def env(monkeypatch):
    for name, value in {'APP_ENV':'test','ENABLE_MOCK_PAYMENTS':'1','PAYMENT_PROVIDER':'mock','SHIPPING_PROVIDER':'mock'}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv('DOKU_PAYMENT_METHOD_TYPES', raising=False)
    monkeypatch.setattr(growth.verification_mail, 'ready', lambda: False)


async def settings(s, **overrides):
    cfg = growth.GrowthConfig.model_validate(overrides).model_dump()
    s.add(m.Setting(key='customer_growth', value=cfg))
    await s.flush()
    return cfg


def test_verification_is_hashed_expiring_single_use_and_throttled(monkeypatch):
    sent = []
    monkeypatch.setattr(growth.verification_mail, 'ready', lambda: True)
    monkeypatch.setattr(growth.verification_mail, 'send_verification', lambda email, token: sent.append((email, token)))
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            assert await growth.request_verification(d['alice'])
            email, token = sent[0]
            async with read_session() as s:
                row = await s.scalar(select(m.EmailVerification))
                assert row.token_hash != token and row.token_hash == hashlib.sha256(token.encode()).hexdigest()
                assert row.email == email and row.used_at is None
                assert 29 * 60 < (row.expires_at - utcnow()).total_seconds() <= 30 * 60
            with pytest.raises(HTTPException) as exc: await growth.request_verification(d['alice'])
            assert exc.value.status_code == 429 and len(sent) == 1
            await growth.verify_email(token)
            with pytest.raises(HTTPException): await growth.verify_email(token)
            async with read_session() as s: assert (await s.get(m.User, d['alice'])).email_verified_at
    asyncio.run(run())


def test_verification_rejects_expired_or_changed_email(monkeypatch):
    sent = []
    monkeypatch.setattr(growth.verification_mail, 'ready', lambda: True)
    monkeypatch.setattr(growth.verification_mail, 'send_verification', lambda email, token: sent.append(token))
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            await growth.request_verification(d['alice'])
            async with session_scope() as s:
                (await s.get(m.User, d['alice'])).email = 'changed@example.com'
            with pytest.raises(HTTPException): await growth.verify_email(sent[0])
            async with session_scope() as s:
                row = await s.scalar(select(m.EmailVerification))
                row.email = 'changed@example.com'; row.expires_at = utcnow() - timedelta(seconds=1)
            with pytest.raises(HTTPException): await growth.verify_email(sent[0])
            async with read_session() as s: assert (await s.get(m.User, d['alice'])).email_verified_at is None
    asyncio.run(run())


def test_member_voucher_requires_verified_first_transaction_once():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False, quantity=1)
            req = d['req'].model_copy(update={'voucher_code': d['voucher'].upper()})
            async with session_scope() as s: (await s.get(m.Voucher, d['voucher'])).audience = 'new_member'
            with pytest.raises(HTTPException) as exc: await create_checkout(d['alice'], req)
            assert exc.value.status_code == 403
            async with session_scope() as s: (await s.get(m.User, d['alice'])).email_verified_at = utcnow()
            result = await create_checkout(d['alice'], req)
            assert result['order']['voucher_discount'] > 0
            async with session_scope() as s:
                fresh = await lock_user(s, d['alice'])
                voucher = await s.get(m.Voucher, d['voucher'])
                with pytest.raises(HTTPException): await growth.voucher_eligible(s, fresh, voucher, claim=True)
            # Parallel intents cannot reuse a member voucher while the first
            # order is awaiting payment. Cancellation releases its reservation.
            await expire_order(result['order']['id'], 'cancelled')
            async with session_scope() as s:
                fresh = await lock_user(s, d['alice'])
                await growth.voucher_eligible(s, fresh, await s.get(m.Voucher, d['voucher']), claim=True)
    asyncio.run(run())


@pytest.mark.parametrize('expiry_days', [0, 30])
def test_referral_rewards_once_to_both_wallets_with_original_rate(expiry_days):
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            async with session_scope() as s:
                await settings(s, referral_enabled=True, referral_trigger='registration',
                    referrer={'kind':'points','points':7,'expiry_days':expiry_days},
                    referee={'kind':'points','points':3,'expiry_days':expiry_days})
                referrer = await s.get(m.User, d['bob']); code = growth.ensure_code(referrer)
                await s.flush()
                user = await s.get(m.User, d['alice'])
                await growth.attach_referral(s, user, code)
                await growth.queue_referral(s, user, 'registration')
                cfg = await points.settings(s); cfg.rate = 999; cfg.version = 2
            await growth.deliver_rewards(); await growth.deliver_rewards()
            async with read_session() as s:
                assert (await s.get(m.User,d['bob'])).points_balance == 107
                assert (await s.get(m.User,d['alice'])).points_balance == 103
                lots = (await s.scalars(select(m.PointLot).where(m.PointLot.source=='referral'))).all()
                assert len(lots) == 2 and all(lot.rate_snapshot == 100 and lot.rate_version == 1 for lot in lots)
                assert all((lot.expires_at is None) == (expiry_days == 0) for lot in lots)
                history = (await s.scalars(select(m.PointHistory).where(m.PointHistory.source == 'referral'))).all()
                assert len(history) == 2
                assert all((row.expires_at is None) == (expiry_days == 0) for row in history)
    asyncio.run(run())


@pytest.mark.parametrize('expiry_days', [0, 30])
def test_daily_checkin_timezone_streak_and_one_per_day(monkeypatch, expiry_days):
    current = [datetime(2026,11,20,16,59,59,tzinfo=timezone.utc)]
    monkeypatch.setattr(growth, 'utcnow', lambda: current[0])
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            async with session_scope() as s:
                await settings(s, checkin_enabled=True, checkin_expiry_days=expiry_days,
                    use_streak=True, streak_points=[2,3,4,5,6,7,20])
                row = await growth.checkin(s, await lock_user(s,d['alice']))
                assert row.day == '2026-11-20' and row.points == 2 and row.streak == 1
            async with session_scope() as s:
                with pytest.raises(HTTPException) as exc: await growth.checkin(s, await lock_user(s,d['alice']))
                assert exc.value.status_code == 409
            current[0] += timedelta(seconds=1)
            async with session_scope() as s:
                row = await growth.checkin(s, await lock_user(s,d['alice']))
                assert row.day == '2026-11-21' and row.points == 3 and row.streak == 2
            current[0] += timedelta(days=2)
            async with session_scope() as s:
                row = await growth.checkin(s, await lock_user(s,d['alice']))
                assert row.streak == 1
            async with read_session() as s:
                assert (await s.get(m.User,d['alice'])).points_balance == 107
                assert await s.scalar(select(func.count()).select_from(m.PointHistory).where(m.PointHistory.source=='daily_checkin')) == 3
                lots = (await s.scalars(select(m.PointLot).where(m.PointLot.source == 'daily_checkin'))).all()
                assert len(lots) == 3
                assert all((lot.expires_at is None) == (expiry_days == 0) for lot in lots)
            if expiry_days == 0:
                monkeypatch.setattr(points, 'utcnow', lambda: current[0] + timedelta(days=4000))
                async with session_scope() as s:
                    user = await lock_user(s, d['alice'])
                    await points.expire(s, user)
                    assert user.points_balance == 107
    asyncio.run(run())


@pytest.mark.parametrize('days', [-1, 3651])
def test_growth_expiry_rejects_invalid_limits(days):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        growth.GrowthConfig(checkin_expiry_days=days)
    with pytest.raises(ValidationError):
        growth.RewardRule(expiry_days=days)


def test_addon_bundle_sums_prices_stock_weight_and_cancellation():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False, quantity=2)
            async with session_scope() as s: (await s.get(m.Product,d['lens'])).sale_role = 'add_on'
            added = await add_to_cart(CartItemCreate(product_id=d['frame'],variant_id=d['vf'],quantity=2,
                addons=[{'product_id':d['lens'],'variant_id':d['vl']}]), d['user'])
            req = d['req'].model_copy(update={'selected_item_ids':[added['id']]})
            async with session_scope() as s:
                quote = await checkout_quote(s, await lock_user(s,d['alice']), req)
                assert quote.subtotal == Decimal('2400.60') and quote.weight == 300
            result = await create_checkout(d['alice'],req)
            assert len(result['order']['items']) == 1
            components = result['order']['items'][0]['components']
            assert [c['component_type'] for c in components] == ['primary','add_on']
            assert components[1]['quantity'] == 2 and components[1]['subtotal'] == 400.4
            async with read_session() as s:
                assert await s.get(m.CartItem, added['id']) is None
                assert await s.get(m.CartAddon,(added['id'],d['lens'])) is None
                assert (await s.get(m.ProductVariant,d['vl'])).reserved == 2
            await expire_order(result['order']['id'],'cancelled')
            async with read_session() as s:
                assert (await s.get(m.ProductVariant,d['vf'])).reserved == 0
                assert (await s.get(m.ProductVariant,d['vl'])).reserved == 0
    asyncio.run(run())


def test_reject_main_product_or_duplicate_addon_selection():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            with pytest.raises(HTTPException):
                await add_to_cart(CartItemCreate(product_id=d['frame'],addons=[{'product_id':d['lens']}]),d['user'])
            with pytest.raises(HTTPException):
                await add_to_cart(CartItemCreate(product_id=d['frame'],addons=[{'product_id':d['lens']},{'product_id':d['lens']}]),d['user'])
            async with read_session() as s: assert await s.scalar(select(func.count()).select_from(m.CartItem)) == 1
    asyncio.run(run())


def test_addon_flash_sale_owns_quota_and_excludes_other_discounts():
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False,quantity=2)
            async with session_scope() as s:
                (await s.get(m.Product,d['lens'])).sale_role='add_on'
                sale=m.FlashSale(id='sale-addon',name='Add On Sale',start_at=utcnow()-timedelta(hours=1),end_at=utcnow()+timedelta(hours=1),is_active=True)
                s.add(sale); await s.flush()
                s.add(m.FlashSaleItem(id='sale-addon-item',flash_sale_id=sale.id,product_id=d['lens'],flash_price=100,quota=3,sold=0,reserved=0,is_active=True))
            added=await add_to_cart(CartItemCreate(product_id=d['frame'],variant_id=d['vf'],quantity=2,
                addons=[{'product_id':d['lens'],'variant_id':d['vl']}]),d['user'])
            req=d['req'].model_copy(update={'selected_item_ids':[added['id']],'voucher_code':d['voucher'].upper(),'use_points':10})
            result=await create_checkout(d['alice'],req)
            assert result['order']['subtotal']==2200.2 and result['order']['voucher_discount']==0 and result['order']['points_used']==0
            async with read_session() as s:
                assert (await s.get(m.FlashSaleItem,'sale-addon-item')).reserved==2
                assert await s.scalar(select(func.count()).select_from(m.AddonFlashReservation))==1
            await confirm_mock_payment(result['order']['order_number'],d['alice'])
            async with read_session() as s:
                sale=await s.get(m.FlashSaleItem,'sale-addon-item')
                assert sale.sold==2 and sale.reserved==0
                assert (await s.get(m.ProductVariant,d['vl'])).stock==3
    asyncio.run(run())


def test_cod_bypasses_doku_and_retries_same_order_without_timeout(monkeypatch):
    monkeypatch.setenv('PAYMENT_PROVIDER','disabled')
    import mysql.integration_services as service
    monkeypatch.setattr(service,'get_doku_client',lambda: pytest.fail('COD must never initialize DOKU'))
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False,quantity=1)
            req = d['req'].model_copy(update={'payment_mode':'cod'})
            result = await create_checkout(d['alice'],req,'cod-repeat')
            again = await create_checkout(d['alice'],req,'cod-repeat')
            order = result['order']
            assert again['order']['id'] == order['id']
            assert order['payment_status']=='cod_pending' and order['status']=='processing'
            assert result['payment']['provider']=='cod' and result['payment']['payment_url'] is None
            assert order['reservation_expires_at'] is None
            assert not await expire_order(order['id'],due_only=True)
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.Order)) == 1
                assert await s.scalar(select(func.count()).select_from(m.Payment).where(m.Payment.provider=='doku')) == 0
            await expire_order(order['id'],'cancelled',owner_id=d['alice'])
            async with read_session() as s: assert (await s.get(m.ProductVariant,d['vf'])).reserved==0
    asyncio.run(run())


def test_cod_booking_payload_preserves_collection_and_coordinates():
    order = m.Order(order_number='MEOW20261120',payment_mode='cod',total=Decimal('112000'))
    address = m.OrderAddress(recipient='Customer',phone='081234567890',street='Alamat tujuan',postal_code='10110',latitude=Decimal('-6.1'),longitude=Decimal('106.8'))
    origin = {'package_type_id':3,'length':20,'width':12,'height':8,'shipment_type':'DROP','name':'Meow Eyes',
        'phone':'081234567890','address':'Alamat toko','postal_code':'40115','subdistrict':'Citarum','latitude':-6.9,'longitude':107.6}
    quote = m.ShippingQuote(weight_gram=200,cost=Decimal('12000'),insurance_cost=Decimal('0'),service_code='REG',
        request_payload={'origin':origin,'rate_request':{'item_price':100000}})
    payload = _booking_payload(order,address,quote,None)
    assert payload['is_cod'] and payload['cod_price']==112000 and payload['package_price']==100000
    assert payload['receiver_latitude']==-6.1 and payload['shipper_longitude']==107.6
    assert payload['cod_price']==payload['package_price']+payload['shipment_price']+payload['insurance_price']


def test_instant_rates_only_available_with_complete_coordinates():
    response = {'data':{'instant':[{'logistic_code':'GOSEND','rate_code':'INSTANT','price':15000}]}}
    assert not _rate_options(response)
    assert _rate_options(response,coordinates=True)[0]['courier_code']=='GOSEND'


@pytest.mark.parametrize('latitude,longitude',[(91,0),(0,181),(float('nan'),0),(0,None)])
def test_address_coordinate_validation(latitude,longitude):
    with pytest.raises(ValueError): AddressCreate(label='Home',recipient='Test',phone='081234567890',street='Alamat',
        city='Jakarta',province='Jakarta',postal_code='10110',latitude=latitude,longitude=longitude)


def test_reviews_require_delivered_after_payment():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False,quantity=1)
            result = await create_checkout(d['alice'],d['req']); order=result['order']
            await confirm_mock_payment(order['order_number'],d['alice'])
            with pytest.raises(HTTPException): await create_review(d['frame'],{'order_id':order['id'],'rating':5},d['user'])
            async with session_scope() as s: (await s.get(m.Order,order['id'])).shipment_status='delivered'
            review = await create_review(d['frame'],{'order_id':order['id'],'rating':5},d['user'])
            assert review['review']['verified_purchase']
    asyncio.run(run())


def test_doku_line_items_addresses_and_whole_rupiah_totals():
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False,quantity=3)
            result=await create_checkout(d['alice'],d['req'])
            async with session_scope() as s:
                order=await s.get(m.Order,result['order']['id']); order.total=Decimal('15001'); order.shipping_cost=Decimal('14000')
                req={'order':{},'payment':{},'customer':{'id':d['alice']}}
                request=await enrich_request(s,req,order,await s.get(m.User,d['alice']),await s.get(m.OrderAddress,order.id),
                    DokuSettings('test','test',frontend_url='https://shop.example.test',public_api_url='https://api.example.test'))
                lines=request['order']['line_items']
                assert sum(row['price']*row['quantity'] for row in lines)==15001
                assert sum(row['quantity'] for row in lines if row['id']!='SHIPPING')==3
                assert request['customer']['state']=='DKI Jakarta' and request['customer']['phone']=='6281234567890'
                assert request['shipping_address']['country_code']=='IDN' and request['billing_address']['last_name']=='alice'
                assert all(row.get('id') and row.get('sku') and row.get('category') and row.get('type') and row.get('url') and row.get('image_url') for row in lines)
    asyncio.run(run())
