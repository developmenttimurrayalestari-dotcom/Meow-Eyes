import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from auth import current_user
from database import read_session
from integrations.config import EverproSettings
from integrations.common import ProviderError
from integrations.everpro import EverproClient
from integrations.locations import canonical_shipping_location
from mysql import integration_services as service, models as m
from tests_mysql.test_integrations import env  # noqa: F401
from tests_mysql.sql_helpers import isolated_database
from tests_mysql.commerce_scenarios import seed_commerce_fixture
import integrations.locations as locations
import routes_integrations
import routes_shopping

REGIONS = {'provinces': [{'id': 'p+/=', 'name': 'Jawa Barat'}], 'cities': [{'id': 'c=', 'name': 'Kota Bandung'}],
           'districts': [{'id': 'd=', 'name': 'Bandung Wetan'}], 'subdistricts': [{'id': 'v=', 'name': 'Citarum', 'postal_code': '40115'}]}
SELECTION = {'province_id': 'p+/=', 'city_id': 'c=', 'district_id': 'd=', 'subdistrict_id': 'v='}
POSTAL = {'postal_code': '40115', 'province_name': 'Jawa Barat', 'city_name': 'Kota Bandung', 'district_name': 'Bandung Wetan', 'sub_district_name': 'Citarum', 'sub_district_id': 123}

class FakeLocations:
    async def regions(self, level, parent=None):
        expected = {'cities': 'p+/=', 'districts': 'c=', 'subdistricts': 'd='}
        return deepcopy(REGIONS[level]) if level == 'provinces' or parent == expected[level] else []

    async def locations(self, postal):
        return {'data': [deepcopy(POSTAL)] if postal == '40115' else []}


def test_provider_hierarchy_uses_correct_filters_opaque_ids_cache_and_404(env):
    calls = []
    def handler(request):
        calls.append(request)
        if request.url.path == '/auth/v1/token': return httpx.Response(200, json={'data': {'token': 'fixture', 'expires': 300}})
        if request.url.path.endswith('/provinces'): return httpx.Response(200, json={'data': [{'province_id': 'p+/=', 'province_name': 'Jawa Barat'}]})
        if request.url.path.endswith('/cities'):
            assert request.url.params['province_id'] == 'p+/='
            return httpx.Response(200, json={'data': [{'city_id': 'c=', 'city_name': 'Kota Bandung'}]})
        if request.url.path.endswith('/districts'): return httpx.Response(404, json={'data': []})
        if request.url.path.endswith('/sub-districts'):
            assert request.url.params['district_id'] == 'd='
            return httpx.Response(200, json={'data': [{'sub_district_id': 'v=', 'sub_district_name': 'Citarum', 'postal_code': '40115'}]})
        raise AssertionError('Unexpected provider request')
    async def run():
        client = EverproClient(EverproSettings.from_env(), transport=httpx.MockTransport(handler))
        first = await client.regions('provinces'); first[0]['name'] = 'tampered'
        assert (await client.regions('provinces'))[0]['name'] == 'Jawa Barat'
        assert (await client.regions('cities', 'p+/='))[0]['id'] == 'c='
        assert await client.regions('districts', 'c=') == []
        assert (await client.regions('subdistricts', 'd='))[0]['postal_code'] == '40115'
    asyncio.run(run())
    assert sum(request.url.path.endswith('/provinces') for request in calls) == 1


def test_address_selection_is_canonical_owned_editable_and_rejects_mixed_hierarchy(monkeypatch):
    monkeypatch.setattr(locations, 'get_everpro_client', lambda: FakeLocations())
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            app = FastAPI(); app.dependency_overrides[current_user] = lambda: d['user']
            app.include_router(routes_shopping.router, prefix='/api'); app.include_router(routes_integrations.router, prefix='/api')
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                assert (await client.get('/api/shipping/locations/provinces')).json()['locations'] == REGIONS['provinces']
                assert (await client.get('/api/shipping/locations/cities')).status_code == 422
                payload = {'label': 'Rumah', 'recipient': 'Customer', 'phone': '081234567890', 'street': 'Jl. QA No. 1', 'is_default': True,
                           'province': 'Fake', 'city': 'Fake', 'district': 'Fake', 'subdistrict': 'Fake', 'postal_code': '99999', 'everpro_location': SELECTION}
                response = await client.post('/api/addresses', json=payload)
                assert response.status_code == 200, response.text
                saved = response.json()['address']
                assert saved['province'] == 'Jawa Barat' and saved['subdistrict'] == 'Citarum' and saved['postal_code'] == '40115'
                assert saved['everpro_destination_id'] == 'v='
                assert (await client.patch('/api/addresses/' + d['address_bob'], json=payload)).status_code == 404
                bad = {**payload, 'everpro_location': {**SELECTION, 'city_id': 'other-city'}}
                assert (await client.post('/api/addresses', json=bad)).status_code == 422
                assert (await client.patch('/api/addresses/' + saved['id'], json={**payload, 'street': 'Jl. QA Baru'})).status_code == 200
                async with read_session() as s:
                    assert (await s.get(m.Address, saved['id'])).street == 'Jl. QA Baru'
                    assert not (await s.get(m.Address, d['address'])).is_default
    asyncio.run(run())


def test_postal_lookup_validates_full_hierarchy_without_comparing_incompatible_id_encodings():
    async def run():
        address = SimpleNamespace(province='Jawa Barat', city='Kota Bandung', district='Bandung Wetan', subdistrict='Citarum', postal_code='40115', everpro_destination_id='v=')
        assert (await canonical_shipping_location(address, FakeLocations()))['subdistrict'] == 'Citarum'
        address.district = 'Wrong district'
        with pytest.raises(HTTPException) as error: await canonical_shipping_location(address, FakeLocations())
        assert error.value.status_code == 422 and 'Ubah' in error.value.detail
    asyncio.run(run())


def test_rate_errors_do_not_claim_a_shipment_or_transaction_was_created():
    for code in ['authentication_failed', 'provider_rejected', 'network_error']:
        error = service._safe_error(ProviderError('everpro', code), 'menghitung ongkir')
        assert error.status_code == 503 and 'referensi transaksi' not in error.detail


def test_unbookable_cargo_without_courier_code_does_not_hide_valid_regular_services():
    body = {'data': {'regular': [{'logistic_code': 'SCP', 'rate_code': 'REG', 'logistic_name': 'SiCepat', 'price': 9000}],
                     'cargo': [{'logistic_code': '', 'rate_code': 'DARAT-NON ELEKTRONIK', 'logistic_name': 'Sentral Cargo', 'price': 30000}]}}
    options = service._rate_options(body)
    assert len(options) == 1 and options[0]['courier_code'] == 'SCP' and options[0]['cost'] == 9000
