import asyncio
from datetime import timedelta
from mysql.base import utcnow
from tests_mysql.test_catalog_sql import sql_client


def test_popup_banner_crud_visibility_priority_device_and_validation():
    async def run():
        async with sql_client() as (client, factory, auth):
            now = utcnow()
            base = dict(title='Promo Popup', image_desktop='/promo.png', image_mobile='/mobile.png', position='popup', link_type='internal', link_url='/flash-sale')
            saved = []
            for changes in [dict(sort_order=10), dict(sort_order=0, target_device='mobile'), dict(is_active=False), dict(start_at=(now + timedelta(days=1)).isoformat()), dict(end_at=(now - timedelta(days=1)).isoformat())]:
                response = await client.post('/api/admin/banners-v2', json={**base, **changes})
                assert response.status_code == 200, response.text
                saved.append(response.json()['banner'])
            for changes in [dict(image_desktop=''), dict(title=' '), dict(link_url='javascript:alert(1)'), dict(start_at=now.isoformat(), end_at=(now - timedelta(days=1)).isoformat())]:
                assert (await client.post('/api/admin/banners-v2', json={**base, **changes})).status_code == 422
            admin = auth['user']; auth['user'] = None
            desktop = (await client.get('/api/banners?position=popup&device=desktop')).json()['banners']
            assert [row['id'] for row in desktop] == [saved[0]['id']]
            mobile = (await client.get('/api/banners?position=popup&device=mobile')).json()['banners']
            assert [row['id'] for row in mobile] == [saved[1]['id'], saved[0]['id']]
            assert mobile[0]['image_mobile'] == '/mobile.png'
            assert not (await client.get('/api/banners?position=hero')).json()['banners']
            assert not (await client.get('/api/homepage')).json()['banners']
            auth['user'] = admin
            assert (await client.put('/api/admin/banners-v2/' + saved[0]['id'], json={'is_active': False})).status_code == 200
            assert not (await client.get('/api/banners?position=popup&device=desktop')).json()['banners']
            assert (await client.delete('/api/admin/banners-v2/' + saved[1]['id'])).status_code == 200
            assert not (await client.get('/api/banners?position=popup&device=mobile')).json()['banners']
    asyncio.run(run())
