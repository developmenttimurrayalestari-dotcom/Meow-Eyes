import asyncio
from copy import deepcopy
from sqlalchemy import select
from mysql import models as m
from mysql.home_categories import KEY, DEFAULTS
from tests_mysql.test_catalog_sql import sql_client

BASE = dict(version=0, title='Frame Premium', description='Pilihan terbaru', link_url='/shop-now?product_type=frame', background_image='/api/uploads-files/frame.webp', icon='frame', theme='coral', sort_order=0, is_active=True)


def test_home_card_crud_defaults_public_filter_and_versions():
    async def run():
        async with sql_client() as (client, factory, auth):
            initial = (await client.get('/api/admin/home-categories')).json()
            assert initial == {'version': 0, 'items': DEFAULTS}
            async with factory() as session:
                assert await session.get(m.Setting, KEY) is None
            response = await client.post('/api/admin/home-categories', json=BASE)
            assert response.status_code == 200, response.text
            saved = response.json()
            assert saved['version'] == 1 and len(saved['items']) == 5
            new = next(item for item in saved['items'] if item['title'] == BASE['title'])
            assert new['background_image'] == BASE['background_image']
            # A second admin editing the old snapshot cannot erase the first change.
            stale = await client.put('/api/admin/home-categories/' + new['id'], json={**BASE, 'title': 'Stale'})
            assert stale.status_code == 409
            assert (await client.delete('/api/admin/home-categories/' + new['id'], params={'version': 0})).status_code == 409
            update = await client.put('/api/admin/home-categories/' + new['id'], json={**BASE, 'version': 1, 'title': 'Paket', 'is_active': False, 'sort_order': 99})
            assert update.status_code == 200
            admin = auth['user']; auth['user'] = None
            public = (await client.get('/api/homepage')).json()['home_categories']
            assert new['id'] not in [item['id'] for item in public]
            assert len(public) == 4
            auth['user'] = admin
            active = await client.put('/api/admin/home-categories/' + new['id'], json={**BASE, 'version': 2, 'title': 'Paket', 'sort_order': 99})
            assert active.status_code == 200
            public = (await client.get('/api/homepage')).json()['home_categories']
            assert public[-1]['title'] == 'Paket'
            removed = await client.delete('/api/admin/home-categories/' + new['id'], params={'version': 3})
            assert removed.status_code == 200 and removed.json()['version'] == 4
            assert len(removed.json()['items']) == 4
            async with factory() as session:
                row = await session.get(m.Setting, KEY)
                assert row.is_public is False and row.updated_by == 'admin'
                assert await session.scalar(select(m.Category.id).where(m.Category.id == 'cat')) == 'cat'
    asyncio.run(run())


def test_deleting_all_cards_keeps_homepage_empty_instead_of_restoring_defaults():
    async def run():
        async with sql_client() as (client, factory, auth):
            for version, item in enumerate(DEFAULTS):
                result = await client.delete('/api/admin/home-categories/' + item['id'], params={'version': version})
                assert result.status_code == 200, result.text
            assert (await client.get('/api/admin/home-categories')).json() == {'version': 4, 'items': []}
            assert (await client.get('/api/homepage')).json()['home_categories'] == []
            assert (await client.put('/api/admin/home-categories/missing', json={**BASE, 'version': 4})).status_code == 404
    asyncio.run(run())


def test_card_validation_limits_and_permissions():
    async def run():
        async with sql_client() as (client, factory, auth):
            for change in [dict(title=' '), dict(title='a'*101), dict(description='x'*181), dict(sort_order=-1), dict(sort_order=10000), dict(icon='arbitrary'), dict(version=-1), dict(id='injected'), dict(link_url='javascript:alert(1)'), dict(link_url='//evil.example'), dict(link_url='/\\evil.example'), dict(background_image='data:image/svg+xml,bad'), dict(background_image='javascript:alert(1)')]:
                result = await client.post('/api/admin/home-categories', json={**BASE, **change})
                assert result.status_code == 422, (change, result.text)
            auth['user'].role = 'customer'
            assert (await client.get('/api/admin/home-categories')).status_code == 403
            assert (await client.post('/api/admin/home-categories', json=BASE)).status_code == 403
            auth['user'].role = 'staff'; auth['user'].permissions = ['setting.view']
            assert (await client.get('/api/admin/home-categories')).status_code == 200
            assert (await client.put('/api/admin/home-categories/home-frame', json=BASE)).status_code == 403
            assert (await client.delete('/api/admin/home-categories/home-frame', params={'version':0})).status_code == 403
            auth['user'].permissions.append('setting.update')
            assert (await client.post('/api/admin/home-categories', json=BASE)).status_code == 200
            async with factory.begin() as session:
                row = await session.get(m.Setting, KEY)
                row.value = {'version': 2, 'items': [{**deepcopy(DEFAULTS[0]), 'id': str(i)} for i in range(50)]}
            assert (await client.post('/api/admin/home-categories', json={**BASE, 'version':2})).status_code == 422
    asyncio.run(run())
