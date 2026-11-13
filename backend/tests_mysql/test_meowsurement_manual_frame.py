"""Manual source isolation, optional ED, and immutable session geometry."""
import asyncio
from copy import deepcopy

from sqlalchemy import select

from database import read_session
from mysql import models as m
from tests_mysql.test_meowsurement import client_fixture, prepared, revise


def test_manual_frame_session_without_product_and_immutable_geometry():
    async def run():
        async with client_fixture() as (client, auth, d):
            catalog = await prepared(client, auth, d)
            payload = {key: value for key, value in catalog.items() if key not in ('product_id', 'variant_id', 'expected_spec_version')}
            payload['manual_frame'] = {'a': 52, 'b': 40, 'dbl': 18}
            response = await client.post('/api/meowsurement/sessions', json=payload)
            assert response.status_code == 201, response.text
            detail = response.json()
            frame = detail['revision']['data']['frame']
            assert frame['ed'] is None and frame['sourceScope'] == 'manual'
            assert frame['productId'] is None and frame['variantId'] is None
            async with read_session() as s:
                row = await s.scalar(select(m.MeowsurementSession).where(m.MeowsurementSession.id == detail['session']['id']))
                assert row.product_id is None and row.variant_id is None and row.spec_scope == 'manual'
            data = deepcopy(detail['revision']['data'])
            data['notes'] = 'Catatan customer'
            assert (await revise(client, detail, data)).status_code == 200
            latest = (await client.get('/api/meowsurement/sessions/' + detail['session']['id'])).json()
            data['frame']['a'] = 99
            assert (await revise(client, latest, data)).status_code == 422
            for invalid in [
                {**payload, 'manual_frame': {'a': 0, 'b': 40, 'dbl': 18}},
                {**payload, 'manual_frame': {'a': 52, 'dbl': 18}},
                {**payload, 'manual_frame': {'a': 52, 'b': 40, 'dbl': 18, 'ed': -1}},
                {**payload, 'manual_frame': None},
                {**payload, 'variant_id': catalog['variant_id']},
                {**catalog, 'manual_frame': payload['manual_frame']},
            ]:
                assert (await client.post('/api/meowsurement/sessions', json=invalid)).status_code == 422
    asyncio.run(run())


def test_catalog_frame_without_ed_remains_available_and_can_start_session():
    async def run():
        async with client_fixture() as (client, auth, d):
            from tests_mysql.test_meowsurement import SPEC
            spec = deepcopy(SPEC)
            spec['specification']['ed'] = None
            payload = await prepared(client, auth, d, spec=spec)
            frames = (await client.get('/api/meowsurement/frames')).json()['products']
            assert frames[0]['frame_specification']['complete'] is True
            response = await client.post('/api/meowsurement/sessions', json=payload)
            assert response.status_code == 201, response.text
            assert response.json()['revision']['data']['frame']['ed'] is None
    asyncio.run(run())
