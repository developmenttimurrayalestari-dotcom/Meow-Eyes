"""Regression: TRL master IDs cannot identify Everpro shipment locations."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException

from integrations.common import ProviderError
from integrations.config import EverproSettings
from integrations.everpro import EverproClient
from integrations.everpro_reference import SharedToken
from integrations.everpro_v3 import origin_location, shipment_location_id
from integrations.locations import canonical_shipping_location
from mysql.integration_services import everpro_context, shipping_fingerprint, _digest, validated_shipping_quote
from mysql import models as m
from database import read_session, session_scope
from tests_mysql.test_integrations import env, adapters, prepared  # noqa: F401
from tests_mysql.sql_helpers import isolated_database

LOCAL = dict(province_name='DKI Jakarta', city_name='Jakarta Timur', district_name='Matraman',
             sub_district_name='Utan Kayu Selatan', postal_code='13120', sub_district_id=26618)
PROVIDER = {**LOCAL, 'sub_district_id':9149}


class Reference:
    async def locations(self, postal):
        return {'data':[deepcopy(LOCAL)]}

    async def token(self):
        return SharedToken('test-stored-token')


def test_origin_and_destination_translate_ids_and_cache_lookup_without_direct_auth(env):
    calls=[]
    def handler(request):
        calls.append(request.url.path)
        assert request.url.path=='/location/v1/postalcode'
        assert request.headers['Authorization']=='Bearer test-stored-token'
        return httpx.Response(200,json={'data':[PROVIDER]})
    async def run():
        settings=replace(EverproSettings.from_env(),data_source='database',api_version=3,
                         origin_postal_code='13120',origin_subdistrict='Utan Kayu Selatan')
        client=EverproClient(settings,reference_store=Reference(),transport=httpx.MockTransport(handler))
        address=SimpleNamespace(province='DKI Jakarta',city='Jakarta Timur',district='Matraman',
                                subdistrict='Utan Kayu Selatan',postal_code='13120',everpro_destination_id='26618')
        assert (await canonical_shipping_location(address,client,require_id=True))['sub_district_id']==9149
        assert await origin_location(client,settings)=={'id':9149}
        assert (await client.locations('13120'))['data'][0]['sub_district_id']==26618
        data=await client.shipment_locations('13120'); data['data'][0]['sub_district_id']=1
        assert await shipment_location_id(client,LOCAL)==9149
    asyncio.run(run())
    assert calls==['/location/v1/postalcode']


@pytest.mark.parametrize('body',[
    {'data':[]},
    {'data':[{**PROVIDER,'province_name':'Other province'}]},
    {'data':[{**PROVIDER,'city_name':'Other city'}]},
    {'data':[{**PROVIDER,'district_name':'Other district'}]},
    {'data':[{**PROVIDER,'sub_district_name':'Utan Kayu Utara'}]},
    {'data':[{**PROVIDER,'postal_code':'13121'}]},
    {'data':[PROVIDER,{**PROVIDER,'sub_district_id':8489}]},
    {'data':[{**PROVIDER,'sub_district_id':None}]},
    {'data':None},
])
def test_missing_ambiguous_or_mismatched_provider_region_never_uses_local_id(env,body):
    async def run():
        settings=replace(EverproSettings.from_env(),data_source='database',api_version=3)
        client=EverproClient(settings,reference_store=Reference(),transport=httpx.MockTransport(lambda _:httpx.Response(200,json=body)))
        with pytest.raises((HTTPException,ProviderError)):
            await shipment_location_id(client,LOCAL)
    asyncio.run(run())


def test_failed_provider_lookup_never_falls_back_to_shared_master_id(env):
    async def run():
        settings=replace(EverproSettings.from_env(),data_source='database',api_version=3)
        client=EverproClient(settings,reference_store=Reference(),transport=httpx.MockTransport(lambda _:httpx.Response(503,json={})))
        with pytest.raises(ProviderError): await shipment_location_id(client,LOCAL)
    asyncio.run(run())


def test_old_shared_id_quotes_are_rejected_before_checkout(adapters):
    async def run():
        async with isolated_database():
            d=await prepared(adapters)
            settings=replace(adapters[1].settings,data_source='database',api_version=3)
            async with session_scope() as s:
                quote=await s.get(m.ShippingQuote,d['req'].shipping_quote_id)
                address=await s.get(m.Address,d['address'])
                from mysql.commerce import priced_cart
                items,_=await priced_cart(s,d['alice'],[d['cart']])
                _,snapshot=shipping_fingerprint(items,address,settings)
                assert snapshot['provider']['location_mapping']=='everpro-postal-v1'
                del snapshot['provider']['location_mapping']
                quote.cart_fingerprint=_digest(snapshot)
            async with read_session() as s:
                with patch('mysql.integration_services.effective_shipping_settings',AsyncMock(return_value=settings)):
                    with pytest.raises(HTTPException) as error:
                        await validated_shipping_quote(s,await s.get(m.User,d['alice']),d['req'],address,items)
                    assert error.value.status_code==409
    asyncio.run(run())


def test_legacy_api_and_database_v1_keep_existing_context(env):
    settings=EverproSettings.from_env()
    assert 'location_mapping' not in everpro_context(settings)
    assert 'location_mapping' not in everpro_context(replace(settings,data_source='database'))
