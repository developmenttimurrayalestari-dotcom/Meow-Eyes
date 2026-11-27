"""Tinting catalog, cart ownership, authoritative prices and frozen orders."""
import asyncio
from copy import deepcopy
from decimal import Decimal

from fastapi import FastAPI, HTTPException
import httpx
import pytest
from sqlalchemy import select

from auth import current_user
from database import read_session, session_scope
from models import User
from mysql import models as m, integration_services as service
from mysql.commerce import checkout_quote, create_checkout, priced_cart
from mysql.tinting import DEFAULTS, KEY
from routes_tinting import router
from routes_shopping import router as shopping
from tests_mysql.test_integrations import env, adapters, prepared  # noqa: F401
from tests_mysql.commerce_scenarios import seed_commerce_fixture
from tests_mysql.sql_helpers import isolated_database

BODY={key:value for key,value in DEFAULTS[0].items() if key!='id'} | {'version':0,'code':'CUSTOM','name':'Custom color'}


def app_for(user):
    app=FastAPI();app.include_router(router,prefix='/api');app.include_router(shopping,prefix='/api')
    app.dependency_overrides[current_user]=lambda:user
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test')


def test_seed_and_permissioned_crud_with_price_hex_validation_and_stale_versions():
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False)
            user=User(user_id=d['admin'],name='Admin',role='super_admin')
            async with app_for(user) as client:
                initial=(await client.get('/api/admin/tinting')).json()
                assert len(initial['items'])==66 and initial['version']==0
                public=(await client.get('/api/tinting')).json()['items']
                assert len(public)==61 and not any('source_note' in item for item in public)
                assert {item['additional_price'] for item in public if item['group']=='therapeutic'}=={120000}
                assert {item['additional_price'] for item in public if item['group']!='therapeutic'}=={60000}
                for change in ({'hex_color':'red'},{'hex_color':'url(javascript:bad)'},{'additional_price':-1},
                               {'additional_price':True},{'additional_price':1.5},{'name':' '},
                               {'bottom_hex_color':None},{'requires_sample':True}):
                    response=await client.post('/api/admin/tinting',json={**BODY,**change})
                    assert response.status_code==422,(change,response.text)
                assert (await client.post('/api/admin/tinting',json={**BODY,'code':'01g'})).status_code==422
                created=await client.post('/api/admin/tinting',json=BODY)
                assert created.status_code==200,created.text
                color=next(item for item in created.json()['items'] if item['code']=='CUSTOM')
                updated=await client.put('/api/admin/tinting/'+color['id'],json={**BODY,'version':1,'hex_color':'#123abc','additional_price':75000})
                assert updated.status_code==200
                assert next(item for item in updated.json()['items'] if item['id']==color['id'])['hex_color']=='#123ABC'
                assert (await client.put('/api/admin/tinting/'+color['id'],json={**BODY,'version':1})).status_code==409
                assert (await client.delete('/api/admin/tinting/'+color['id'],params={'version':2})).status_code==200
                user.role='customer'
                assert (await client.get('/api/admin/tinting')).status_code==403
                assert (await client.post('/api/admin/tinting',json={**BODY,'version':3})).status_code==403
                user.role='staff';user.permissions=['product.view']
                assert (await client.get('/api/admin/tinting')).status_code==200
                assert (await client.put('/api/admin/tinting/tinting-01g',json={**BODY,'version':3})).status_code==403
    asyncio.run(run())


def test_cart_choice_is_owned_optional_priced_per_quantity_and_never_merges_with_plain_frame(adapters):
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False,quantity=2,stock=10)
            async with app_for(d['user']) as client:
                assert (await client.patch('/api/cart/'+d['cart']+'/tinting',json={'tinting_id':'tinting-04s','additional_price':1})).status_code==422
                response=await client.patch('/api/cart/'+d['cart']+'/tinting',json={'tinting_id':'tinting-04s'})
                assert response.status_code==200,response.text
                item=response.json()['cart_item']
                assert item['tinting_price']==60000 and item['quantity']==2
                assert item['subtotal']==float((Decimal('1000.10')+60000)*2)
                await client.post('/api/cart',json={'product_id':d['frame'],'variant_id':d['vf'],'quantity':1})
                async with read_session() as s:
                    assert len((await s.scalars(select(m.CartItem).where(m.CartItem.user_id==d['alice']))).all())==2
                assert (await client.patch('/api/cart/'+d['cart']+'/tinting',json={'tinting_id':'tinting-42s'})).status_code==409
                removed=await client.patch('/api/cart/'+d['cart']+'/tinting',json={'tinting_id':None})
                assert removed.json()['cart_item']['tinting'] is None
                assert removed.json()['cart_item']['subtotal']==2000.2
            bob=User(user_id=d['bob'],name='Bob')
            async with app_for(bob) as client:
                assert (await client.patch('/api/cart/'+d['cart']+'/tinting',json={'tinting_id':'tinting-04s'})).status_code==404
    asyncio.run(run())


def test_tinting_changes_invalidate_quotes_and_order_retains_color_price_after_master_edits(adapters):
    async def run():
        async with isolated_database():
            d=await prepared(adapters)
            async with app_for(d['user']) as client:
                selected=await client.patch('/api/cart/'+d['cart']+'/tinting',json={'tinting_id':'tinting-04g'})
                assert selected.status_code==200,selected.text
                with pytest.raises(HTTPException) as error:
                    await create_checkout(d['alice'],d['req'])
                assert error.value.status_code==409
                option=(await service.shipping_options(d['alice'],d['address'],[d['cart']]))['options'][0]
                req=d['req'].model_copy(update={'shipping_quote_id':option['quote_id']})
                async with read_session() as s:
                    preview=await checkout_quote(s,await s.get(m.User,d['alice']),req)
                    assert preview.payload()['tinting_subtotal']==60000
                order=(await create_checkout(d['alice'],req))['order']
                assert order['items'][0]['tinting']['code']=='04G'
                assert order['items'][0]['tinting']['additional_price']==60000
                frozen_total=order['total']
                async with session_scope() as s:
                    values=deepcopy(DEFAULTS)
                    color=next(item for item in values if item['id']=='tinting-04g')
                    color.update(name='Renamed',hex_color='#FF0000',additional_price=99999,is_active=False)
                    s.add(m.Setting(key=KEY,value={'version':1,'items':values},is_public=False))
                async with read_session() as s:
                    from mysql.api import order_dict
                    saved=await order_dict(s,await s.get(m.Order,order['id']))
                    assert saved['items'][0]['tinting']['code']=='04G'
                    assert saved['items'][0]['tinting']['name']=='Black Gradient'
                    assert saved['items'][0]['tinting']['additional_price']==60000 and saved['total']==frozen_total
                    assert await s.get(m.CartTinting,d['cart']) is None
    asyncio.run(run())


def test_disabled_cart_tinting_stays_visible_and_can_be_removed_without_hiding_product(adapters):
    async def run():
        async with isolated_database():
            d=await prepared(adapters)
            async with app_for(d['user']) as client:
                assert (await client.patch('/api/cart/'+d['cart']+'/tinting',json={'tinting_id':'tinting-04s'})).status_code==200
                async with session_scope() as s:
                    values=deepcopy(DEFAULTS)
                    next(item for item in values if item['id']=='tinting-04s')['is_active']=False
                    s.add(m.Setting(key=KEY,value={'version':1,'items':values},is_public=False))
                result=await client.get('/api/cart')
                assert result.status_code==200 and len(result.json()['items'])==1
                assert result.json()['items'][0]['tinting']['is_available'] is False
                with pytest.raises(HTTPException): await service.shipping_options(d['alice'],d['address'],[d['cart']])
                assert (await client.patch('/api/cart/'+d['cart']+'/tinting',json={'tinting_id':None})).status_code==200
    asyncio.run(run())


def test_different_cart_lines_and_package_tinting_are_charged_independently(adapters):
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False,quantity=2,stock=10)
            async with session_scope() as s:
                (await s.get(m.Product,d['frame'])).product_type='package'
                s.add(m.CartItem(id='second',user_id=d['alice'],product_id=d['frame'],variant_id=d['vf'],quantity=1))
            async with app_for(d['user']) as client:
                assert (await client.patch('/api/cart/'+d['cart']+'/tinting',json={'tinting_id':'tinting-04s'})).status_code==200
                assert (await client.patch('/api/cart/second/tinting',json={'tinting_id':'tinting-39s'})).status_code==200
                items=(await client.get('/api/cart')).json()['items']
                assert {item['id']:item['tinting_price'] for item in items}=={d['cart']:60000,'second':120000}
                assert sum(item['subtotal'] for item in items)==243000.3
                async with read_session() as s:
                    priced,weight=await priced_cart(s,d['alice'],[d['cart'],'second'])
                    assert sum(item.tinting_price*item.cart.quantity for item in priced)==240000
                    assert weight==300
    asyncio.run(run())


def test_admin_price_change_reprices_cart_and_invalidates_the_previous_shipping_quote(adapters):
    async def run():
        async with isolated_database():
            d=await prepared(adapters)
            async with app_for(d['user']) as client:
                await client.patch('/api/cart/'+d['cart']+'/tinting',json={'tinting_id':'tinting-04s'})
                option=(await service.shipping_options(d['alice'],d['address'],[d['cart']]))['options'][0]
                async with session_scope() as s:
                    values=deepcopy(DEFAULTS)
                    next(item for item in values if item['id']=='tinting-04s')['additional_price']=75000
                    s.add(m.Setting(key=KEY,value={'version':1,'items':values},is_public=False))
                req=d['req'].model_copy(update={'shipping_quote_id':option['quote_id']})
                with pytest.raises(HTTPException) as error: await create_checkout(d['alice'],req)
                assert error.value.status_code==409
                assert (await client.get('/api/cart')).json()['items'][0]['tinting_price']==75000
    asyncio.run(run())
