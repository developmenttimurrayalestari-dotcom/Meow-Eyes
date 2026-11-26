"""Shared TRL tables and token renewal, isolated from real DB/API writes."""
import asyncio
from datetime import datetime, timedelta, timezone
from dataclasses import replace
import json
from zoneinfo import ZoneInfo

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import text

from database import session_scope
from integrations.common import ProviderError
from integrations.config import EverproSettings
from integrations.everpro import EverproClient
from integrations.everpro_reference import EverproReferenceStore, SharedToken, normalize_token
from integrations.check_everpro import check_auth
from integrations.locations import selected_location
from tests_mysql.test_integrations import env, adapters, payment_event  # noqa: F401
from tests_mysql.sql_helpers import isolated_database


async def tables():
    async with session_scope() as s:
        await s.execute(text("ATTACH DATABASE ':memory:' AS db_mobtrl"))
        await s.execute(text('''CREATE TABLE db_mobtrl.apieverpro_master
            (id INTEGER PRIMARY KEY, province TEXT, city TEXT, district TEXT, sub_district TEXT, post_code TEXT)'''))
        await s.execute(text('''CREATE TABLE db_mobtrl.apieverpro_key
            (id_key INTEGER PRIMARY KEY, security_key TEXT, type_key TEXT, expired INTEGER, datetime_updatekey DATETIME)'''))
        for identity, province, city, district, village, postal in [
            (10,'Alpha','Same City','Same District','North','10001'),
            (11,'Alpha','Same City','Same District','South','10002'),
            (12,'Alpha','Other City','Other District','North','10003'),
            (20,'Beta','Same City','Same District','North','20001'),
        ]:
            await s.execute(text('INSERT INTO db_mobtrl.apieverpro_master VALUES (:id,:p,:c,:d,:v,:z)'),
                            {'id':identity,'p':province,'c':city,'d':district,'v':village,'z':postal})


async def insert_token(value='stored-token', *, age=0, ttl=3600, kind='Bearer', identity=1):
    updated = (datetime.now(ZoneInfo('Asia/Jakarta')) - timedelta(seconds=age)).replace(tzinfo=None)
    async with session_scope() as s:
        await s.execute(text('INSERT INTO db_mobtrl.apieverpro_key VALUES (:id,:token,:kind,:ttl,:updated)'),
                        {'id':identity,'token':value,'kind':kind,'ttl':ttl,'updated':updated.isoformat(sep=' ')})


def db_settings():
    return replace(EverproSettings.from_env(), data_source='database', api_version=3)


def test_db_mode_needs_no_client_credentials_and_rejects_unsafe_identifiers(env, monkeypatch):
    monkeypatch.setenv('EVERPRO_DATA_SOURCE','database')
    monkeypatch.delenv('EVERPRO_CLIENT_KEY'); monkeypatch.delenv('EVERPRO_CLIENT_SECRET')
    settings = EverproSettings.from_env()
    assert settings.client_key == settings.client_secret == ''
    assert settings.reference_database == 'db_mobtrl'
    monkeypatch.setenv('EVERPRO_REFERENCE_DATABASE','db_mobtrl;DROP TABLE users')
    with pytest.raises(HTTPException): EverproSettings.from_env()


def test_regions_postal_codes_and_parent_scoping_are_database_only(env, monkeypatch):
    import integrations.locations as locations
    from models import EverproLocationSelection
    def no_http(request): raise AssertionError('Location calls must never use HTTP')
    async def run():
        async with isolated_database():
            await tables()
            client = EverproClient(db_settings(), transport=httpx.MockTransport(no_http))
            monkeypatch.setattr(locations, 'get_everpro_client', lambda:client)
            assert await client.regions('provinces') == [{'id':'10','name':'Alpha'},{'id':'20','name':'Beta'}]
            assert await client.regions('cities','10') == [{'id':'12','name':'Other City'},{'id':'10','name':'Same City'}]
            assert await client.regions('districts','20') == [{'id':'20','name':'Same District'}]
            villages = await client.regions('subdistricts','10')
            assert [v['id'] for v in villages] == ['10','11'] and villages[1]['postal_code'] == '10002'
            postal = (await client.locations('10001'))['data'][0]
            assert postal['sub_district_id'] == 10 and postal['province_name'] == 'Alpha'
            assert await client.locations('10001 OR 1=1') == {'data':[]}
            assert await client.regions('cities','1 OR 1=1') == []
            selection = EverproLocationSelection(province_id='10',city_id='10',district_id='10',subdistrict_id='11')
            assert (await selected_location(selection))['postal_code'] == '10002'
            selection.subdistrict_id = '20'
            with pytest.raises(HTTPException): await selected_location(selection)
    asyncio.run(run())


def test_db_token_timezone_prefix_and_bearer_filter(env):
    async def run():
        async with isolated_database():
            await tables()
            await insert_token('Bearer stored-token')
            await insert_token('callback-secret', kind='CALLBACK', identity=2)
            token = await EverproReferenceStore(db_settings()).token()
            assert token.value == 'stored-token' and 3500 < token.remaining() <= 3600
            assert 'stored-token' not in repr(token)
    asyncio.run(run())


@pytest.mark.parametrize('bad', ['', None, 'Bearer ', 'Bearer Bearer token', 'value\nheader', 'value token'])
def test_invalid_bearer_values_are_not_used(bad):
    assert normalize_token(bad) is None


@pytest.mark.parametrize('state', ['expired','missing','db_unavailable'])
def test_missing_or_expired_token_refreshes_from_given_get_api_only(env, state):
    calls = []
    def handler(request):
        calls.append((request.method,request.url.host,request.url.path))
        assert '/auth/' not in request.url.path
        if request.url.host == '180.250.96.154':
            assert request.method == 'GET' and request.url.path.endswith('/Api_everpro//getToken')
            assert 'authorization' not in request.headers
            return httpx.Response(200,json={'status':True,'token':'Bearer refreshed-token'})
        assert request.headers['Authorization'] == 'Bearer refreshed-token'
        return httpx.Response(200,json={'data':[]})
    async def run():
        async with isolated_database():
            if state != 'db_unavailable':
                await tables()
                if state == 'expired': await insert_token(age=7200)
            client = EverproClient(db_settings(),transport=httpx.MockTransport(handler))
            await client.request('GET','/shipment/v1/logistics')
            assert client.token_source == 'refresh_api'
    asyncio.run(run())
    assert len(calls) == 2


def test_valid_db_token_used_by_all_services_without_direct_auth(env):
    seen = []
    def handler(request):
        seen.append(request.url.path)
        assert request.headers['Authorization'] == 'Bearer stored-token'
        assert '/auth/' not in request.url.path and 'getToken' not in request.url.path
        return httpx.Response(200,json={'data':{}})
    async def run():
        async with isolated_database():
            await tables(); await insert_token()
            client=EverproClient(db_settings(),transport=httpx.MockTransport(handler))
            await client.rates({}); await client.create_shipment({'client_order_no':'same-reference'})
            await client.tracking('awb'); await client.awb('ref'); await client.label('awb')
            await client.pickup_times('rate'); await client.order_detail('ref')
            report=await check_auth(db_settings(),transport=httpx.MockTransport(handler))
            assert report['ok'] and report['reason']=='shared_token_valid' and report['token_source']=='database'
    asyncio.run(run())
    assert len(seen) == 8


@pytest.mark.parametrize('status,body', [(401,{'message':'unauthorized'}),(403,{'message':'token is expired'})])
def test_rejected_token_refreshes_and_retries_exact_booking_once(env, status, body):
    requests=[]
    def handler(request):
        requests.append(request)
        if request.url.host=='180.250.96.154':
            return httpx.Response(200,json={'status':True,'token':'new-token'})
        if request.headers['Authorization']=='Bearer stored-token':
            return httpx.Response(status,json=body)
        return httpx.Response(200,json={'client_order_no':'REF-1'})
    async def run():
        async with isolated_database():
            await tables(); await insert_token()
            client=EverproClient(db_settings(),transport=httpx.MockTransport(handler))
            await client.create_shipment({'client_order_no':'REF-1','signed_key':'signed'})
    asyncio.run(run())
    bookings=[r for r in requests if r.method=='POST']
    assert len(bookings)==2 and bookings[0].content==bookings[1].content
    assert len(requests)==3 and not any('/auth/' in r.url.path for r in requests)


@pytest.mark.parametrize('refresh_body', [{'status':False,'token':'bad'}, {'status':True,'token':'Bearer stored-token'}, {'status':True,'token':None}])
def test_bad_refresh_is_bounded_and_never_leaks_token(env, refresh_body):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json=refresh_body) if request.url.host=='180.250.96.154' else httpx.Response(401,json={})
    async def run():
        async with isolated_database():
            await tables(); await insert_token()
            with pytest.raises(ProviderError) as error:
                await EverproClient(db_settings(),transport=httpx.MockTransport(handler)).rates({})
            assert 'stored-token' not in str(error.value)
    asyncio.run(run())
    assert len(calls)==2


def test_permission_failure_is_not_mistaken_for_token_expiry(env):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(403,json={'message':'courier not permitted'})
    async def run():
        async with isolated_database():
            await tables(); await insert_token()
            with pytest.raises(ProviderError):
                await EverproClient(db_settings(),transport=httpx.MockTransport(handler)).rates({})
    asyncio.run(run())
    assert len(calls)==1


def test_simultaneous_401_requests_share_one_token_refresh(env):
    refreshes=[]
    async def handler(request):
        if request.url.host=='180.250.96.154':
            refreshes.append(request)
            await asyncio.sleep(.03)
            return httpx.Response(200,json={'status':True,'token':'rotated-token'})
        if request.headers['Authorization']=='Bearer stored-token':
            await asyncio.sleep(.01)
            return httpx.Response(401,json={})
        return httpx.Response(200,json={'data':[]})
    async def run():
        async with isolated_database():
            await tables(); await insert_token()
            client=EverproClient(db_settings(),transport=httpx.MockTransport(handler))
            await asyncio.gather(*(client.request('GET','/shipment/v1/logistics') for _ in range(4)))
    asyncio.run(run())
    assert len(refreshes)==1


def test_checkout_quote_and_booking_use_shared_locations_and_token_end_to_end(adapters, monkeypatch):
    from mysql import integration_services as service, models as m
    from mysql.commerce import create_checkout
    from tests_mysql.commerce_scenarios import seed_commerce_fixture
    for key,value in {'EVERPRO_DATA_SOURCE':'database','EVERPRO_API_VERSION':'3',
                      'EVERPRO_ORIGIN_POSTAL_CODE':'10001','EVERPRO_ORIGIN_SUBDISTRICT':'North'}.items():
        monkeypatch.setenv(key,value)
    monkeypatch.delenv('EVERPRO_CLIENT_KEY'); monkeypatch.delenv('EVERPRO_CLIENT_SECRET')
    calls=[]
    def handler(request):
        calls.append(request.url.path)
        assert request.headers['Authorization']=='Bearer stored-token'
        if request.method=='GET':
            assert request.url.path.startswith('/shipment/v1/orders/')
            return httpx.Response(200,json={'data':{'client_order_no':request.url.path.split('/')[-1],
                'shipment_price':12000,'insurance_price':0,'tracking_code':'CREATED'}})
        payload=json.loads(request.content)
        if request.url.path=='/location/v1/postalcode':
            postal=payload['postal_code']
            # Shared primary keys deliberately differ from provider IDs.
            return httpx.Response(200,json={'data':[{
                'province_name':'Alpha','city_name':'Same City','district_name':'Same District',
                'sub_district_name':'North' if postal=='10001' else 'South',
                'postal_code':postal,'sub_district_id':68371 if postal=='10001' else 9149}]})
        if request.url.path=='/shipment/v3/rates':
            assert payload['origin']['id']==68371 and payload['destination']['id']==9149
            return httpx.Response(200,json={'data':{'regular':[{'logistic_code':'JNE','rate_code':'REG',
                'price':12000,'signed_key':'shared-rate-key'}]}})
        assert request.url.path=='/shipment/v3/orders'
        assert payload['shipper']['id']==68371 and payload['receiver']['id']==9149
        assert payload['signed_key']=='shared-rate-key'
        return httpx.Response(200,json={'client_order_no':payload['client_order_no'],'actual_price':12000})
    async def run():
        async with isolated_database():
            await tables(); await insert_token()
            d=await seed_commerce_fixture(bundle=False,quantity=1)
            async with session_scope() as s:
                address=await s.get(m.Address,d['address'])
                address.province,address.city,address.district='Alpha','Same City','Same District'
                address.subdistrict,address.postal_code='South','10002'
            client=EverproClient(EverproSettings.from_env(),transport=httpx.MockTransport(handler))
            monkeypatch.setattr(service,'get_everpro_client',lambda:client)
            option=(await service.shipping_options(d['alice'],d['address'],[d['cart']]))['options'][0]
            req=d['req'].model_copy(update={'shipping_quote_id':option['quote_id'],'courier_code':'JNE','service_code':'REG'})
            order=(await create_checkout(d['alice'],req))['order']
            await service.apply_doku_event(payment_event(order),'shared-paid','shared-test-hash')
            await service.book_shipment(order['id'])
    asyncio.run(run())
    assert calls[:4]==['/location/v1/postalcode','/location/v1/postalcode','/shipment/v3/rates','/shipment/v3/orders']
    assert len(calls)==5 and calls[4].startswith('/shipment/v1/orders/')
