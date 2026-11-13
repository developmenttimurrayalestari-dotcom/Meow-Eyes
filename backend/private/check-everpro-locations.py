"""Read-only provider diagnostics; never print tokens or merchant credentials."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integrations.everpro import get_everpro_client
from integrations.common import ProviderError
from mysql.config import load_runtime_environment
from fastapi import HTTPException

async def main():
    load_runtime_environment()
    try:
        client = get_everpro_client()
        result = await client.request('GET', '/location/v1/provinces')
        rows = result.get('data')
        print(json.dumps({'ok': True, 'environment': client.settings.environment, 'province_count': len(rows) if isinstance(rows, list) else None,
                          'row_fields': sorted(rows[0]) if isinstance(rows, list) and rows else []}))
        province = rows[0]
        cities = (await client.request('GET', '/location/v1/cities', params={'province_id': province['province_id']}))['data']
        districts = (await client.request('GET', '/location/v1/districts', params={'city_id': cities[0]['city_id']}))['data']
        villages = (await client.request('GET', '/location/v1/sub-districts', params={'district_id': districts[0]['district_id']}))['data']
        village = next(row for row in villages if str(row.get('postal_code', '')).isdigit())
        postal_rows = (await client.locations(str(village['postal_code'])))['data']
        print(json.dumps({'hierarchy_ok': True, 'city_fields': sorted(cities[0]), 'district_fields': sorted(districts[0]),
                          'village_fields': sorted(village), 'postal_fields': sorted(postal_rows[0]),
                          'village_id_type': type(village['sub_district_id']).__name__, 'postal_id_type': type(postal_rows[0]['sub_district_id']).__name__}))
        request = {'origin_postal_code': client.settings.origin_postal_code, 'origin_sub_district_name': client.settings.origin_subdistrict,
                   'destination_postal_code': str(village['postal_code']), 'destination_sub_district_name': village['sub_district_name'],
                   'weight': .2, 'item_price': 100000, 'package_type_id': client.settings.package_type_id,
                   'shipment_type': client.settings.shipment_type, 'length': client.settings.length_cm, 'width': client.settings.width_cm,
                   'height': client.settings.height_cm, 'is_cod': False, 'is_use_insurance': False, 'include_flat_rate': False}
        rate = await client.rates(request)
        print(json.dumps({'rates_ok': True, 'rate_categories': sorted(rate.get('data', {})) if isinstance(rate.get('data'), dict) else [], 'no_shipment_created': True}))
        print(json.dumps({'rate_shapes': {key: {'type': type(value).__name__, 'count': len(value) if isinstance(value, list) else None,
             'missing_courier_code': sum(not row.get('logistic_code') for row in value if isinstance(row, dict)) if isinstance(value, list) else None}
             for key, value in rate.get('data', {}).items()}}))
        from models import EverproLocationSelection
        from integrations.locations import selected_location, canonical_shipping_location
        from mysql.integration_services import _rate_options
        from types import SimpleNamespace
        canonical = await selected_location(EverproLocationSelection(province_id=str(province['province_id']), city_id=str(cities[0]['city_id']),
                  district_id=str(districts[0]['district_id']), subdistrict_id=str(village['sub_district_id'])))
        await canonical_shipping_location(SimpleNamespace(**canonical), client)
        print(json.dumps({'canonical_hierarchy_and_postal_match': True, 'eligible_rate_options': len(_rate_options(rate)), 'no_database_writes': True}))
    except ProviderError as error:
        print(json.dumps({'ok': False, 'provider': error.provider, 'code': error.code, 'status': error.status}))
    except HTTPException as error:
        print(json.dumps({'ok': False, 'configuration_error': error.detail, 'status': error.status_code}))

asyncio.run(main())
