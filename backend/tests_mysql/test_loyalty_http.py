import asyncio
from pathlib import Path
import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from auth import current_user, current_admin
from models import User
from database import session_scope
from mysql import models as m
from mysql.commerce import create_checkout, confirm_mock_payment, admin_transition_order
from routes_loyalty import router as loyalty_router
from routes_returns import router as returns_router
from tests_mysql.sql_helpers import isolated_database
from tests_mysql.commerce_scenarios import seed_commerce_fixture

def test_private_evidence_ownership_format_size_submission_and_rate_version(monkeypatch,tmp_path):
    monkeypatch.setenv('APP_ENV','test');monkeypatch.setenv('ENABLE_MOCK_PAYMENTS','1')
    monkeypatch.setenv('PAYMENT_PROVIDER','mock');monkeypatch.setenv('SHIPPING_PROVIDER','mock')
    monkeypatch.setattr('routes_returns.ROOT',tmp_path)
    monkeypatch.setattr('routes_returns.MAX_BYTES',128)
    async def run():
        async with isolated_database():
            d=await seed_commerce_fixture(bundle=False)
            result=await create_checkout(d['alice'],d['req'])
            await confirm_mock_payment(result['order']['order_number'],d['alice'])
            await admin_transition_order(result['order']['id'],'completed','',d['admin'])
            app=FastAPI();app.include_router(loyalty_router);app.include_router(returns_router)
            app.dependency_overrides[current_user]=lambda:d['user']
            admin=User(user_id=d['admin'],name='Admin',email='admin@example.com',role='admin')
            app.dependency_overrides[current_admin]=lambda:admin
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
                async with session_scope() as s: item=await s.scalar(select(m.OrderItem).where(m.OrderItem.order_id==result['order']['id']))
                response=await client.post(f"/orders/{result['order']['id']}/returns",json={'items':[{'order_item_id':item.id,'quantity':1}],'reason':'Frame patah saat dibuka'})
                assert response.status_code==200
                case=response.json();url=f"/returns/{case['id']}"
                assert (await client.post(url+'/status',json={'status':'submitted'})).status_code==422
                assert (await client.post(url+'/evidence',files={'file':('bad.mp4',b'not-a-video','video/mp4')})).status_code==422
                assert not list(tmp_path.iterdir())
                assert (await client.post(url+'/evidence',files={'file':('large.mp4',b'0'*256,'video/mp4')})).status_code==413
                header=b'\x00\x00\x00\x18ftypisom'+b'\x00'*40
                uploaded=await client.post(url+'/evidence',files={'file':('unboxing.mp4',header,'video/mp4')})
                assert uploaded.status_code==200
                evidence_url='/returns/evidence/'+uploaded.json()['id']
                served=await client.get(evidence_url);assert served.status_code==200 and served.content==header
                assert served.headers['cache-control']=='private, no-store'
                assert (await client.post(url+'/status',json={'status':'submitted'})).status_code==200
                app.dependency_overrides[current_user]=lambda:User(user_id=d['bob'],name='Bob',email='bob@example.com')
                assert (await client.get(evidence_url)).status_code==404
                assert (await client.post(url+'/status',json={'status':'cancelled'})).status_code==404
                settings=(await client.get('/admin/points/settings')).json()
                updated=await client.put('/admin/points/settings',json={'version':settings['version'],'rate':250,'cashback_valuation':'locked'})
                assert updated.status_code==200 and updated.json()['version']==settings['version']+1
                assert (await client.put('/admin/points/settings',json={'version':settings['version'],'rate':300})).status_code==409
                assert (await client.put('/admin/points/settings',json={'version':2,'rate':400,'cashback_valuation':'current'})).status_code==422
    asyncio.run(run())
