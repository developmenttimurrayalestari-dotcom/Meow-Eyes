"""Everpro Swagger v3 contracts and durable shipping flows; no live bookings."""
import asyncio
from dataclasses import replace
from decimal import Decimal

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import select

from database import read_session, session_scope
from integrations.common import ProviderError
from integrations.config import EverproSettings
from integrations.everpro import EverproClient
from integrations.everpro_v3 import location_id, rate_request, surcharge, origin_location
from integrations.check_everpro import check_auth
from mysql import models as m, integration_services as service
from mysql.commerce import create_checkout, admin_transition_order
from tests_mysql.test_integrations import env, adapters, prepared, payment_event  # noqa: F401
from tests_mysql.sql_helpers import isolated_database


def test_v3_auth_is_v2_and_other_endpoints_have_independent_versions(env, monkeypatch):
    monkeypatch.setenv('EVERPRO_API_VERSION', '3')
    settings = EverproSettings.from_env()
    assert settings.auth_path == '/auth/v2/token'
    calls = []
    def handler(request):
        calls.append((request.method, request.url.path))
        if request.url.path == '/auth/v2/token':
            return httpx.Response(200, json={'data': {'token': 'fixture-token', 'expires': 3600}})
        assert request.headers['Authorization'] == 'Bearer fixture-token'
        return httpx.Response(200, json={'data': []})
    async def run():
        client = EverproClient(settings, transport=httpx.MockTransport(handler))
        await client.rates({})
        await client.create_shipment({})
        await client.locations('40115')
        await client.order_detail('INV-1')
        assert (await check_auth(settings, transport=httpx.MockTransport(handler)))['ok']
    asyncio.run(run())
    assert calls == [('POST','/auth/v2/token'), ('POST','/shipment/v3/rates'),
                     ('POST','/shipment/v3/orders'), ('POST','/location/v1/postalcode'),
                     ('GET','/shipment/v1/orders/INV-1'), ('POST','/auth/v2/token')]
    monkeypatch.setenv('EVERPRO_AUTH_VERSION', '1')
    assert EverproSettings.from_env().auth_path == '/auth/v1/token'
    monkeypatch.setenv('EVERPRO_AUTH_VERSION', '3')
    with pytest.raises(HTTPException): EverproSettings.from_env()


def test_v3_timeout_is_uncertain_and_no_order_is_retried_inside_http_client(env):
    settings = replace(EverproSettings.from_env(), api_version=3, auth_version=2)
    calls = []
    def handler(request):
        calls.append(request.url.path)
        if request.url.path == '/auth/v2/token':
            return httpx.Response(200, json={'data': {'token': 'fixture-token'}})
        raise httpx.ReadTimeout('fixture timeout', request=request)
    async def run():
        with pytest.raises(ProviderError) as error:
            await EverproClient(settings, transport=httpx.MockTransport(handler)).create_shipment({})
        assert error.value.uncertain is True
    asyncio.run(run())
    assert calls == ['/auth/v2/token','/shipment/v3/orders']


@pytest.mark.parametrize('value', [True, None, 'opaque-id', 0, -1, 12.5])
def test_v3_rejects_opaque_or_invalid_postal_location_ids(value):
    with pytest.raises(HTTPException): location_id(value)


def test_v3_pinpoints_and_cod_use_nested_documented_fields(env):
    settings = replace(EverproSettings.from_env(), api_version=3)
    request = rate_request(settings, {'id':3300}, {'sub_district_id':8839}, weight=500,
        price=100000, cod=True, coordinates=(-6.9,107.6,-6.1,106.8))
    assert request['origin'] == {'id':3300,'latitude':-6.9,'longitude':107.6}
    assert request['destination'] == {'id':8839,'latitude':-6.1,'longitude':106.8}
    assert request['payment_type'] == 'COD' and request['package']['weight'] == .5


@pytest.mark.parametrize('rate', [{'surcharge':-1}, {'surcharge':.5}, {'surcharge':True},
    {'surcharge':100, 'surcharge_details':{'commodity_surcharge':50}}])
def test_v3_invalid_fee_breakdowns_are_rejected(rate):
    with pytest.raises(ProviderError): surcharge(rate)


def test_v3_origin_lookup_rejects_ambiguous_matches(env):
    settings = EverproSettings.from_env()
    class Client:
        async def locations(self, postal):
            return {'data':[{'postal_code':postal, 'sub_district_name':settings.origin_subdistrict,
                             'sub_district_id':identity} for identity in (1,2)]}
    with pytest.raises(HTTPException) as error:
        asyncio.run(origin_location(Client(), settings))
    assert error.value.status_code == 422


@pytest.mark.parametrize('mode', ['online','cod'])
@pytest.mark.parametrize('timeout', [False, True])
def test_v3_shipping_snapshot_signed_key_fees_and_booking_retry(adapters, monkeypatch, mode, timeout):
    doku, client = adapters
    monkeypatch.setenv('EVERPRO_API_VERSION', '3')
    monkeypatch.setenv('EVERPRO_USE_INSURANCE', '1')
    client.settings = EverproSettings.from_env()
    old_locations = client.locations
    async def locations(postal):
        if postal == client.settings.origin_postal_code:
            return {'data': [{'postal_code': postal, 'sub_district_name': client.settings.origin_subdistrict, 'sub_district_id': 3300}]}
        return await old_locations(postal)
    client.locations = locations
    async def rates(payload):
        client.rate_requests.append(payload)
        return {'data': {'regular': [
            {'logistic_code':'JNE','rate_code':'REG23','price':12000,'insurance_price':500,
             'signed_key':'opaque-signed-rate-key','surcharge':1000, 'surcharge_details':{'commodity_surcharge':1000}},
            {'logistic_code':'OTHER','rate_code':'UNBOOKABLE','price':1},
        ]}}
    client.rates = rates
    async def run():
        async with isolated_database():
            # prepared() exercises the online request shape before the COD
            # variant recomputes the discounted goods value and signed quote.
            d = await prepared(adapters)
            if mode == 'cod':
                option = (await service.shipping_options(d['alice'], d['address'], [d['cart']], payment_mode='cod'))['options'][0]
                d['req'] = d['req'].model_copy(update={'payment_mode':'cod','shipping_quote_id':option['quote_id']})
            rate = client.rate_requests[-1]
            assert rate['origin'] == {'id':3300} and rate['destination'] == {'id':8839}
            assert rate['package']['type'] == 'GLASSWARE' and rate['package']['dimension'] == {'length':20,'width':12,'height':8}
            assert 'origin_postal_code' not in rate
            assert ('payment_type' in rate) == (mode == 'cod')
            client.fail_after_booking = timeout
            result = await create_checkout(d['alice'], d['req'], 'v3-checkout')
            order = result['order']
            if mode == 'online':
                event = payment_event(order)
                await service.apply_doku_event(event, 'v3-paid', 'fixture-v3-event')
                try:
                    await service.book_shipment(order['id'])
                except HTTPException:
                    assert timeout
            client.fail_after_booking = False
            if timeout:
                # Only the retry delay is advanced; request contents stay frozen.
                from datetime import timedelta
                async with session_scope() as s:
                    log = await s.scalar(select(m.ShipmentLog).where(m.ShipmentLog.order_id == order['id'], m.ShipmentLog.action == 'everpro_booking_attempt'))
                    log.created_at -= timedelta(seconds=31)
            await service.book_shipment(order['id'])
            assert len(client.bookings) == 1
            booking = client.bookings[0]
            assert booking['signed_key'] == 'opaque-signed-rate-key'
            assert booking['shipper']['id'] == 3300 and booking['receiver']['id'] == 8839
            assert booking['package']['price'] == rate['package']['price']
            assert booking['shipment_price'] == 12000 and booking['surcharge'] == 1000 and booking['insurance_price'] == 500
            assert ('payment_type' in booking) == (mode == 'cod')
            if mode == 'cod':
                assert booking['cod_price'] == booking['package']['price'] + 12000 + 500
                assert not doku.calls
            async with read_session() as s:
                quote = await s.get(m.ShippingQuote, order['shipping_quote_id'])
                assert quote.cost == 12000 and quote.insurance_cost == 500
                assert quote.response_payload['signed_key'] == 'opaque-signed-rate-key'
            monkeypatch.setenv('EVERPRO_API_VERSION','1')
            client.settings = EverproSettings.from_env()
            with pytest.raises(HTTPException) as error: await service.book_shipment(order['id'])
            assert error.value.status_code == 409
    asyncio.run(run())
