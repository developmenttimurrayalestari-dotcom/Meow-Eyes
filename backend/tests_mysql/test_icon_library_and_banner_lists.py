import asyncio
from mysql.icon_library import LUCIDE_NAMES
from tests_mysql.test_catalog_sql import sql_client


def test_new_lucide_icons_are_persisted_and_returned_for_menus_and_home_cards():
    assert len(LUCIDE_NAMES)>1000 and 'camera' in LUCIDE_NAMES
    async def run():
        async with sql_client() as (client,factory,auth):
            menu=dict(version=0,label='Foto',url='/shop-now',icon='lucide:camera',location='header')
            card=dict(version=0,title='Foto',link_url='/shop-now',icon='lucide:heart')
            assert (await client.post('/api/admin/menus',json=menu)).status_code==200
            assert (await client.post('/api/admin/home-categories',json=card)).status_code==200
            assert any(item['icon']=='lucide:camera' for item in (await client.get('/api/menus')).json()['items'])
            assert any(item['icon']=='lucide:heart' for item in (await client.get('/api/homepage')).json()['home_categories'])
            for value in ['lucide:not-real-xyz','<svg onload=alert(1)>','lucide:__proto__']:
                assert (await client.post('/api/admin/menus',json={**menu,'version':1,'icon':value})).status_code==422
                assert (await client.post('/api/admin/home-categories',json={**card,'version':1,'icon':value})).status_code==422
    asyncio.run(run())


def test_banner_admin_filter_separates_popup_and_normal_content():
    async def run():
        async with sql_client() as (client,factory,auth):
            for position in ['hero','promo','popup']:
                response=await client.post('/api/admin/banners-v2',json={'title':position,'position':position,'image_desktop':'/image.png'})
                assert response.status_code==200
            normal=(await client.get('/api/admin/banners-v2',params={'exclude_position':'popup'})).json()['banners']
            popups=(await client.get('/api/admin/banners-v2',params={'position':'popup'})).json()['banners']
            assert {row['position'] for row in normal}=={'hero','promo'}
            assert [row['position'] for row in popups]==['popup']
    asyncio.run(run())
