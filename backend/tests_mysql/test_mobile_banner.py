import asyncio
from tests_mysql.test_catalog_sql import sql_client


def test_hero_mobile_upload_url_survives_create_edit_and_public_reads():
    async def run():
        async with sql_client() as (client,factory,auth):
            created=await client.post('/api/admin/banners-v2',json={'title':'Mobile Promo','position':'hero','image_desktop':'/api/uploads-files/desktop.webp','image_mobile':'/api/uploads-files/mobile.webp','link_url':'/flash-sale','target_device':'all'})
            assert created.status_code==200,created.text
            banner=created.json()['banner']
            updated=await client.put('/api/admin/banners-v2/'+banner['id'],json={'image_mobile':'/api/uploads-files/mobile-new.webp'})
            assert updated.status_code==200
            admin=auth['user'];auth['user']=None
            for device in ['mobile','desktop']:
                public=(await client.get('/api/banners',params={'position':'hero','device':device})).json()['banners']
                assert public[0]['image_desktop']=='/api/uploads-files/desktop.webp'
                assert public[0]['image_mobile']=='/api/uploads-files/mobile-new.webp'
            auth['user']=admin
            assert (await client.put('/api/admin/banners-v2/'+banner['id'],json={'image_mobile':None})).status_code==200
            assert (await client.get('/api/banners',params={'position':'hero'})).json()['banners'][0]['image_mobile'] is None
    asyncio.run(run())
