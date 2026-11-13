import asyncio
from tests_mysql.test_optical_features import feature_client

def test_frame_and_package_asset_lifecycle_and_customer_visibility():
    async def run():
        async with feature_client(bundle=False) as (client,auth,d,_):
            auth['user']=d['admin_user']
            response=await client.post('/api/admin/products',json={'name':'Paket VTO','product_type':'package','description':'Frame dan lensa','price':400000,'main_image':'/package.png',
                'variants':[{'sku':'PACKAGE-VTO','stock':0}]})
            assert response.status_code==200,response.text
            product=response.json()['product'];pid=product['id'];vid=product['variants'][0]['id']
            options=(await client.get('/api/admin/products',params={'try_on_eligible':True})).json()['products']
            assert {p['id'] for p in options}=={d['frame'],pid}
            assert {p['product_type'] for p in options}=={'frame','package'}
            payload={'product_id':pid,'variant_id':vid,'asset_type':'image','source_url':'https://cdn.example.com/package.png','status':'draft'}
            created=await client.post('/api/admin/try-on-assets',json=payload)
            assert created.status_code==200,created.text
            aid=created.json()['asset']['id']
            assert (await client.get(f'/api/products/{pid}/try-on')).json()['assets']==[]
            assert (await client.get('/api/try-on/catalog')).json()['products']==[]
            assert (await client.patch('/api/admin/try-on-assets/'+aid,json={'status':'published'})).status_code==200
            frame_asset=await client.post('/api/admin/try-on-assets',json={**payload,'product_id':d['frame'],'variant_id':d['vf'],'status':'published'})
            assert frame_asset.status_code==200,frame_asset.text
            assert len((await client.get(f'/api/products/{pid}/try-on',params={'variant_id':vid})).json()['assets'])==1
            detail=(await client.get('/api/products/'+product['slug'])).json()['product']
            assert detail['product_type']=='package' and detail['supports_try_on']
            catalog=(await client.get('/api/try-on/catalog')).json()['products']
            assert {p['id'] for p in catalog}=={pid,d['frame']}
            assert all(p['try_on_assets'] for p in catalog)
            assert (await client.post('/api/admin/try-on-assets',json={**payload,'product_id':d['lens'],'variant_id':d['vl']})).status_code==422
            assert (await client.post('/api/admin/try-on-assets',json={**payload,'variant_id':d['vf']})).status_code==422
            assert (await client.put('/api/admin/products/'+pid,json={'is_active':False})).status_code==200
            assert pid not in {p['id'] for p in (await client.get('/api/try-on/catalog')).json()['products']}
            assert pid in {p['id'] for p in (await client.get('/api/admin/products?try_on_eligible=true')).json()['products']}
            await client.delete('/api/admin/products/'+pid)
            assert (await client.get(f'/api/products/{pid}/try-on')).status_code==404
            assert (await client.post('/api/admin/try-on-assets',json=payload)).status_code==422
            assert pid not in {p['id'] for p in (await client.get('/api/admin/products?try_on_eligible=true')).json()['products']}
    asyncio.run(run())
