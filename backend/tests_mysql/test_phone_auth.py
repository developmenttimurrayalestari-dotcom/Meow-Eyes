import asyncio
import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from database import read_session, session_scope
from mysql.models import User
from routes_auth import router
from tests_mysql.sql_helpers import isolated_database


@pytest.fixture(autouse=True)
def enabled_phone_auth(monkeypatch):
    monkeypatch.setenv('AUTH_PHONE_ENABLED', 'true')


def test_phone_signup_normalized_login_pin_session_and_inactive_account():
    async def run():
        async with isolated_database():
            app = FastAPI(); app.include_router(router, prefix='/api')
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
                payload = {'name':'Phone Customer','phone':'0812-3456-7890','password':'Example123!'}
                r = await client.post('/api/auth/register',json=payload)
                assert r.status_code == 200, r.text
                result=r.json();uid=result['user']['user_id']
                assert result['user']['email'] is None and result['user']['phone']=='+6281234567890'
                headers={'Authorization':'Bearer '+result['token']}
                assert (await client.get('/api/auth/me',headers=headers)).json()['user']['phone']=='+6281234567890'
                assert (await client.post('/api/auth/pin/setup',json={'pin':'123456'},headers=headers)).status_code==200
                for number in ('081234567890','6281234567890','+62 812 3456 7890'):
                    r=await client.post('/api/auth/login',json={'identifier':number,'password':'Example123!'})
                    assert r.status_code==200,r.text
                    assert r.json()['user']['user_id']==uid and r.json()['user']['has_pin'] is True
                    assert (await client.post('/api/auth/register',json={**payload,'phone':number})).status_code==400
                assert (await client.post('/api/auth/login',json={'phone':'081234567890','password':'wrong'})).status_code==401
                # Multiple phone-only users share NULL email, never a fake email.
                assert (await client.post('/api/auth/register',json={**payload,'phone':'081234567891'})).status_code==200
                async with read_session() as s:
                    row=await s.get(User,uid)
                    assert row.email is None and row.password_hash!='Example123!'
                async with session_scope() as s:
                    (await s.get(User,uid)).is_active=False
                assert (await client.post('/api/auth/login',json={'phone':'081234567890','password':'Example123!'})).status_code==403
    asyncio.run(run())


def test_phone_auth_disabled_blocks_registration_and_every_login_field(monkeypatch):
    async def run():
        async with isolated_database():
            app = FastAPI(); app.include_router(router, prefix='/api')
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                original = await client.post('/api/auth/register', json={'name':'Phone','phone':'081234567890','password':'Example123!'})
                assert original.status_code == 200
                monkeypatch.setenv('AUTH_PHONE_ENABLED', 'false')
                assert (await client.get('/api/auth/config')).json() == {'phone_enabled': False}
                assert (await client.post('/api/auth/register', json={'name':'Phone','phone':'081234567891','password':'Example123!'})).status_code == 403
                for key in ('phone', 'email', 'identifier'):
                    assert (await client.post('/api/auth/login', json={key:'081234567890','password':'Example123!'})).status_code == 403
                assert (await client.get('/api/auth/me', headers={'Authorization':'Bearer '+original.json()['token']})).status_code == 200
                assert (await client.post('/api/auth/register', json={'name':'Email','email':'still@example.com','password':'Example123!'})).status_code == 200
                monkeypatch.setenv('AUTH_PHONE_ENABLED','true')
                assert (await client.post('/api/auth/login', json={'phone':'081234567890','password':'Example123!'})).status_code == 200
    asyncio.run(run())


@pytest.mark.parametrize('contact',[{}, {'phone':'abc'}, {'phone':'123'}, {'phone':1234567890},
    {'phone':'081234567890','email':'test@example.com'}, {'email':'not-an-email'}, {'phone':'+'+'1'*16}])
def test_invalid_or_ambiguous_registration_contact_is_rejected(contact):
    async def run():
        app=FastAPI();app.include_router(router,prefix='/api')
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            assert (await client.post('/api/auth/register',json={'name':'Test','password':'Example123!',**contact})).status_code==422
    asyncio.run(run())
