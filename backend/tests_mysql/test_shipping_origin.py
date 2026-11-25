import asyncio
import pytest
from fastapi import FastAPI, HTTPException
import httpx
from sqlalchemy import select
from auth import current_user
from models import User
from database import read_session, session_scope
from mysql import models as m
from mysql.shipping_origin import effective_shipping_settings, KEY
from integrations.config import EverproSettings
from tests_mysql.test_integrations import env, adapters, prepared, paid_order
from tests_mysql.sql_helpers import isolated_database
from mysql import integration_services as service
from mysql.commerce import create_checkout
from routes_integrations import router

ORIGIN = dict(version=0,name='Gudang Kedua',phone='081234567890',address='Jalan Gudang Baru 23',email='toko@example.com',
    province_id='p',city_id='c',district_id='d',subdistrict_id='s',province='spoof',city='',district='',subdistrict='',postal_code='00000',latitude=None,longitude=None)

def test_superadmin_origin_permission_canonical_validation_and_versions(env,monkeypatch):
    async def canonical(body):
        return dict(province='Jawa Barat',city='Bandung',district='Bandung Wetan',subdistrict='Citarum',postal_code='40115',everpro_destination_id='s')
    monkeypatch.setattr('integrations.locations.selected_location',canonical)
    async def run():
        async with isolated_database():
            async with session_scope() as s: s.add(m.User(user_id='root',name='Root',role='super_admin'))
            app=FastAPI(); app.include_router(router,prefix='/api')
            user=User(user_id='root',name='Root',role='customer')
            app.dependency_overrides[current_user]=lambda:user
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
                for role in ['customer','staff','admin']:
                    user.role=role
                    assert (await client.get('/api/admin/shipping-origin')).status_code==403
                    assert (await client.put('/api/admin/shipping-origin',json=ORIGIN)).status_code==403
                user.role='super_admin'
                assert (await client.get('/api/admin/shipping-origin')).json()['source']=='env'
                result=await client.put('/api/admin/shipping-origin',json=ORIGIN)
                assert result.status_code==200,result.text
                saved=result.json()['origin']; assert saved['province']=='Jawa Barat' and saved['postal_code']=='40115'
                assert (await client.put('/api/admin/shipping-origin',json=ORIGIN)).status_code==409
                assert (await client.put('/api/admin/shipping-origin',json={**saved,'latitude':12})).status_code==422
                assert (await client.put('/api/admin/shipping-origin',json=saved)).status_code==200
                for name in ['EVERPRO_ORIGIN_POSTAL_CODE','EVERPRO_SHIPPER_NAME','EVERPRO_SHIPPER_PHONE','EVERPRO_SHIPPER_ADDRESS']:
                    monkeypatch.delenv(name)
                async with read_session() as s:
                    settings=await effective_shipping_settings(s,EverproSettings.from_env(require_origin=False))
                    assert settings.shipper_address==ORIGIN['address'] and settings.origin_postal_code=='40115'
                    assert (await s.get(m.Setting,KEY)).is_public is False
                assert (await client.get('/api/integrations/status')).json()['shipping']['ready'] is True
    asyncio.run(run())

def test_changed_origin_invalidates_old_quote_and_rates_use_saved_origin(adapters):
    async def run():
        async with isolated_database():
            fixture=await prepared(adapters)
            async with session_scope() as s:
                s.add(m.Setting(key=KEY,is_public=False,value={**ORIGIN,'postal_code':'40115','subdistrict':'Citarum'}))
            with pytest.raises(HTTPException) as error: await create_checkout(fixture['alice'],fixture['req'])
            assert error.value.status_code==409
            response=await service.shipping_options(fixture['alice'],fixture['address'],[fixture['cart']])
            async with read_session() as s:
                quote=await s.get(m.ShippingQuote,response['options'][0]['quote_id'])
                assert quote.request_payload['origin']['address']==ORIGIN['address']
                assert quote.request_payload['origin']['name']==ORIGIN['name']
    asyncio.run(run())

def test_existing_order_booking_retains_original_dispatch_address(adapters):
    async def run():
        async with isolated_database():
            fixture,order=await paid_order(adapters)
            async with session_scope() as s: s.add(m.Setting(key=KEY,is_public=False,value={**ORIGIN,'postal_code':'40115','subdistrict':'Citarum'}))
            await service.book_shipment(order['id'])
            assert adapters[1].bookings[0]['shipper_address']=='Jl. Fixture 12'
    asyncio.run(run())


def test_origin_changed_during_rate_request_rejects_the_stale_response(adapters,monkeypatch):
    async def run():
        async with isolated_database():
            fixture=await prepared(adapters)
            original=adapters[1].rates
            async def changed(request):
                async with session_scope() as s:
                    s.add(m.Setting(key=KEY,is_public=False,value={**ORIGIN,'postal_code':'40115','subdistrict':'Citarum'}))
                return await original(request)
            monkeypatch.setattr(adapters[1],'rates',changed)
            with pytest.raises(HTTPException) as error:
                await service.shipping_options(fixture['alice'],fixture['address'],[fixture['cart']])
            assert error.value.status_code==409
    asyncio.run(run())
