"""Lens type/index prices and atomic product-page configuration."""
import asyncio
from decimal import Decimal
from fastapi import FastAPI
import httpx
import pytest
from sqlalchemy import select,func
from auth import current_user
from models import User
from database import read_session,session_scope
from mysql import models as m
from mysql.commerce import priced_cart
from routes_lens_products import router as lenses
from routes_tinting import router as tinting
from routes_shopping import router as shopping
from tests_mysql.sql_helpers import isolated_database
from tests_mysql.commerce_scenarios import seed_commerce_fixture
from tests_mysql.test_integrations import env, adapters, prepared  # noqa: F401


def client_for(user):
    app=FastAPI();app.dependency_overrides[current_user]=lambda:user
    for router in (lenses,tinting,shopping):app.include_router(router,prefix='/api')
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test')


async def make_offer(client,version=0,kind='clear',index='1.61',price=60000):
    result=await client.post('/api/admin/lens-products',json={'version':version,'lens_type':kind,'index_value':index,'additional_price':price})
    assert result.status_code==200,result.text
    return next(item for item in result.json()['items'] if item['name'].startswith({'clear':'Clear','uv420':'UV420'}[kind]) and item['index_value']==index)


def test_price_matrix_crud_permissions_versions_and_different_prices_for_same_index():
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False)
            admin=User(user_id=d['admin'],name='Admin',role='super_admin')
            async with client_for(admin) as client:
                assert {'clear','uv420','photochromic','uv420-photochromic'} <= {item['code'] for item in (await client.get('/api/admin/lens-products')).json()['types']}
                clear=await make_offer(client)
                uv=await make_offer(client,1,'uv420',price=100000)
                assert clear['id']!=uv['id'] and clear['additional_price']==60000 and uv['additional_price']==100000
                duplicate=await client.post('/api/admin/lens-products',json={'version':2,'lens_type':'clear','index_value':'1.61','additional_price':80000})
                assert duplicate.status_code==409
                assert (await client.put('/api/admin/lens-products/'+clear['id'],json={'version':0,'lens_type':'clear','index_value':'1.61','additional_price':90000})).status_code==409
                for invalid in ({'additional_price':-1},{'index_value':'bad'},{'lens_type':'unknown'}):
                    assert (await client.post('/api/admin/lens-products',json={'version':2,'lens_type':'clear','index_value':'1.67','additional_price':80000,**invalid})).status_code==422
                assert (await client.delete('/api/admin/lens-products/'+clear['id'],params={'version':2})).status_code==200
                assert not next(item for item in (await client.get('/api/admin/lens-products')).json()['items'] if item['id']==clear['id'])['is_active']
                custom=await client.post('/api/admin/lens-products',json={'version':3,'lens_type':'single-vision','index_value':'1.67','additional_price':80000})
                assert custom.status_code==200,custom.text
                admin.role='customer'
                assert (await client.get('/api/admin/lens-products')).status_code==403
    asyncio.run(run())


def test_product_creation_saves_lens_rx_and_tinting_together_and_bad_color_rolls_back():
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False,stock=10)
            async with client_for(User(user_id=d['admin'],name='Admin',role='super_admin')) as client: offer=await make_offer(client)
            async with client_for(d['user']) as client:
                body={'product_id':d['frame'],'variant_id':d['vf'],'quantity':2,'lens_index_id':offer['id'],
                      'prescription':{'notes':'Foto menyusul'},'tinting_id':'tinting-04s'}
                bad=await client.post('/api/cart',json={**body,'tinting_id':'missing'})
                assert bad.status_code==409
                async with read_session() as s:assert await s.scalar(select(func.count()).select_from(m.CartItem))==1
                saved=await client.post('/api/cart',json=body)
                assert saved.status_code==200,saved.text
                row=next(item for item in (await client.get('/api/cart')).json()['items'] if item['id']==saved.json()['id'])
                assert row['lens_price']==60000 and row['tinting_price']==60000
                assert row['prescription']['notes']=='Foto menyusul' and row['subtotal']==242000.2
                assert row['lens_index']['lens_types'][0]['code']=='clear'
    asyncio.run(run())


def test_edit_same_cart_row_preserves_addons_and_blocks_other_customers():
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=True,stock=10)
            async with client_for(User(user_id=d['admin'],name='Admin',role='super_admin')) as client: offer=await make_offer(client)
            body={'quantity':2,'variant_id':d['vf'],'lens_index_id':offer['id'],'prescription':{'notes':'Baru'},'tinting_id':'tinting-04g','replace_lens_product':True}
            async with client_for(User(user_id=d['bob'],name='Bob')) as client:
                assert (await client.patch('/api/cart/'+d['cart']+'/configuration',json=body)).status_code==404
            async with client_for(d['user']) as client:
                response=await client.patch('/api/cart/'+d['cart']+'/configuration',json=body)
                assert response.status_code==200,response.text
                row=response.json()['cart_item']
                assert row['id']==d['cart'] and row['lens_product'] is None and row['lens_price']==60000
                bad=await client.patch('/api/cart/'+d['cart']+'/configuration',json={**body,'tinting_id':'missing','prescription':{'notes':'Should rollback'}})
                assert bad.status_code==409
                row=(await client.get('/api/cart')).json()['items'][0]
                assert row['prescription']['notes']=='Baru'
                assert (await client.patch('/api/cart/'+d['cart']+'/configuration',json={**body,'tinting_id':None,'lens_index_id':None})).status_code==200
                async with read_session() as s:
                    assert await s.scalar(select(func.count()).select_from(m.CartItem))==1
                    assert await s.get(m.CartTinting,d['cart']) is None
    asyncio.run(run())


def test_package_filters_types_and_does_not_charge_combination_price():
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False)
            async with client_for(User(user_id=d['admin'],name='Admin',role='super_admin')) as client:
                clear=await make_offer(client);uv=await make_offer(client,1,'uv420',price=100000)
            async with session_scope() as s:
                (await s.get(m.Product,d['frame'])).product_type='package'
                s.add(m.ProductCategory(product_id=d['frame'],category_id=clear['lens_type_ids'][0]))
            async with client_for(d['user']) as client:
                options=(await client.get('/api/products/'+d['frame']+'/optical-options')).json()['items']
                assert [option['id'] for option in options]==[clear['id']]
                body={'quantity':2,'lens_index_id':uv['id']}
                assert (await client.patch('/api/cart/'+d['cart']+'/configuration',json=body)).status_code==422
                saved=await client.patch('/api/cart/'+d['cart']+'/configuration',json={**body,'lens_index_id':clear['id']})
                assert saved.json()['cart_item']['lens_price']==0
    asyncio.run(run())


def test_same_price_does_not_keep_a_quote_valid_when_lens_identity_changes(adapters):
    from fastapi import HTTPException
    from mysql import integration_services as service
    from mysql.commerce import create_checkout
    async def run():
        async with isolated_database():
            d=await prepared(adapters)
            async with client_for(User(user_id=d['admin'],name='Admin',role='super_admin')) as client:offer=await make_offer(client)
            async with client_for(d['user']) as client:
                assert (await client.patch('/api/cart/'+d['cart']+'/configuration',json={'quantity':1,'lens_index_id':offer['id']})).status_code==200
            option=(await service.shipping_options(d['alice'],d['address'],[d['cart']]))['options'][0]
            async with session_scope() as s:(await s.get(m.LensIndex,offer['id'])).name='Changed lens identity at the same price'
            with pytest.raises(HTTPException) as error:await create_checkout(d['alice'],d['req'].model_copy(update={'shipping_quote_id':option['quote_id']}))
            assert error.value.status_code==409
    asyncio.run(run())
