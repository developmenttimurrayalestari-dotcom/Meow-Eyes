"""Exercise real-provider orchestration using only local fake provider adapters."""
import asyncio
import hashlib
from sqlalchemy import select, func
from database import read_session, session_scope
from mysql import models as m, integration_services as service
from mysql.commerce import create_checkout, admin_transition_order
from tests_mysql.commerce_scenarios import seed_commerce_fixture
from tests_mysql.sql_helpers import isolated_database
from tests_mysql.test_integrations import env, adapters  # noqa: F401


def test_cod_books_everpro_once_and_settles_stock_only_on_delivered(adapters):
    doku, everpro = adapters
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False, quantity=1)
            async with session_scope() as s:
                address = await s.get(m.Address, d['address'])
                address.district, address.subdistrict = 'Gambir', 'Cideng'
            options = await service.shipping_options(d['alice'], d['address'], [d['cart']], payment_mode='cod')
            quote = options['options'][0]
            req = d['req'].model_copy(update={'payment_mode':'cod', 'shipping_quote_id':quote['quote_id'],
                'courier_code':quote['courier_code'], 'service_code':quote['service_code']})
            first = await create_checkout(d['alice'], req, 'cod-remote')
            again = await create_checkout(d['alice'], req, 'cod-remote')
            order = first['order']
            assert not first.get('payment_error'), first
            assert again['order']['id'] == order['id'] and not doku.calls
            assert len(everpro.bookings) == 1
            booking = everpro.bookings[0]
            assert booking['is_cod'] and booking['cod_price'] == order['total']
            assert booking['cod_price'] == booking['package_price'] + booking['shipment_price'] + booking['insurance_price']
            async with read_session() as s:
                assert (await s.get(m.ProductVariant, d['vf'])).stock == 5
                assert (await s.get(m.ProductVariant, d['vf'])).reserved == 1
            payload={'client_order_no': order['order_number'], 'tracking_code':'DELIVERED', 'awb_number':'AWB-' + order['order_number']}
            digest=hashlib.sha256(str(payload).encode()).hexdigest()
            await service.apply_everpro_event(payload, digest, kind='tracking')
            await service.apply_everpro_event(payload, digest, kind='tracking')
            async with read_session() as s:
                row=await s.get(m.Order, order['id'])
                assert row.payment_status == 'paid' and row.shipment_status == 'delivered'
                variant=await s.get(m.ProductVariant, d['vf'])
                assert variant.stock == 4 and variant.reserved == 0
                assert await s.scalar(select(func.count()).select_from(m.PaymentLog).where(m.PaymentLog.action=='cod_delivered'))==1
            await admin_transition_order(order['id'],'completed',None,d['admin'])
    asyncio.run(run())


def test_uncertain_cod_booking_returns_durable_order_and_retry_identity(adapters):
    doku, everpro=adapters
    everpro.fail_after_booking=True
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False,quantity=1)
            async with session_scope() as s:
                address=await s.get(m.Address,d['address'])
                address.district,address.subdistrict='Gambir','Cideng'
            options=await service.shipping_options(d['alice'],d['address'],[d['cart']],payment_mode='cod')
            quote=options['options'][0]
            req=d['req'].model_copy(update={'payment_mode':'cod','shipping_quote_id':quote['quote_id'],
                'courier_code':quote['courier_code'],'service_code':quote['service_code']})
            result=await create_checkout(d['alice'],req,'cod-timeout')
            # The fake provider accepted the request before timing out. A retry
            # reconciles its existing remote identity rather than booking twice.
            everpro.fail_after_booking=False
            again=await create_checkout(d['alice'],req,'cod-timeout')
            assert result['order']['id']==again['order']['id']
            assert len(everpro.bookings)==1 and not doku.calls
            async with read_session() as s: assert await s.scalar(select(func.count()).select_from(m.Order))==1
    asyncio.run(run())


def test_pinpoints_reach_rate_request_and_invalidate_old_quote(adapters, monkeypatch):
    from integrations.config import EverproSettings
    from fastapi import HTTPException
    import pytest
    _,everpro=adapters
    monkeypatch.setenv('EVERPRO_ORIGIN_LATITUDE','-6.9')
    monkeypatch.setenv('EVERPRO_ORIGIN_LONGITUDE','107.6')
    everpro.settings=EverproSettings.from_env()
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False,quantity=1)
            async with session_scope() as s:
                address=await s.get(m.Address,d['address'])
                address.district,address.subdistrict='Gambir','Cideng'
                address.latitude,address.longitude=-6.1,106.8
            options=await service.shipping_options(d['alice'],d['address'],[d['cart']])
            request=everpro.rate_requests[0]
            assert request['origin_latitude']==-6.9 and request['destination_longitude']==106.8
            quote=options['options'][0]
            req=d['req'].model_copy(update={'shipping_quote_id':quote['quote_id'],'courier_code':quote['courier_code'],'service_code':quote['service_code']})
            async with session_scope() as s: (await s.get(m.Address,d['address'])).latitude=-6.2
            with pytest.raises(HTTPException) as exc: await create_checkout(d['alice'],req)
            assert exc.value.status_code==409
    asyncio.run(run())


def test_returned_cod_releases_inventory_and_acknowledges_duplicate_callback(adapters):
    _, everpro=adapters
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False,quantity=1)
            async with session_scope() as s:
                address=await s.get(m.Address,d['address'])
                address.district,address.subdistrict='Gambir','Cideng'
            options=await service.shipping_options(d['alice'],d['address'],[d['cart']],payment_mode='cod')
            quote=options['options'][0]
            req=d['req'].model_copy(update={'payment_mode':'cod','shipping_quote_id':quote['quote_id'],
                'courier_code':quote['courier_code'],'service_code':quote['service_code']})
            result=await create_checkout(d['alice'],req,'cod-return')
            number=result['order']['order_number']
            payload={'client_order_no':number,'tracking_code':'RETURN','awb_number':'AWB-'+number}
            digest=hashlib.sha256(str(payload).encode()).hexdigest()
            await service.apply_everpro_event(payload,digest,kind='tracking')
            assert (await service.apply_everpro_event(payload,digest,kind='tracking'))['duplicate']
            async with read_session() as s:
                order=await s.get(m.Order,result['order']['id'])
                assert order.status=='cancelled' and order.payment_status=='cancelled'
                variant=await s.get(m.ProductVariant,d['vf'])
                assert variant.stock==5 and variant.reserved==0
    asyncio.run(run())
