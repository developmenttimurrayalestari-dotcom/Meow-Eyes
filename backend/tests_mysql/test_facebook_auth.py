import asyncio
import copy
import time
from types import SimpleNamespace
import httpx
import pytest
from fastapi import FastAPI, HTTPException
from sqlalchemy import select, func
from auth import token_digest
from database import read_session, session_scope
import facebook_identity as fb
from mysql import models as m
from routes_auth import router
from tests_mysql.sql_helpers import isolated_database


@pytest.fixture
def facebook(monkeypatch):
    monkeypatch.setenv('FACEBOOK_APP_ID', '12345')
    monkeypatch.setenv('FACEBOOK_APP_SECRET', 'server-secret-fixture')
    monkeypatch.setenv('FACEBOOK_GRAPH_VERSION', 'v27.0')
    monkeypatch.setenv('CORS_ORIGINS', 'https://shop.example.test')
    state = {'claims': {'is_valid': True, 'app_id': '12345', 'user_id': '999', 'type': 'USER',
                       'expires_at': int(time.time()) + 3600, 'data_access_expires_at': int(time.time()) + 3600},
             'profile': {'id': '999', 'name': 'Facebook Customer', 'email': 'facebook@example.com'}, 'calls': []}
    class Session:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, url, **kwargs):
            state['calls'].append((url, kwargs))
            assert kwargs['timeout'] == 10 and kwargs['allow_redirects'] is False
            if state.get('offline'): raise fb.requests.ConnectionError('not for public logs')
            data = {'data': state['claims']} if url.endswith('/debug_token') else state['profile']
            return SimpleNamespace(status_code=state.get('status', 200), json=lambda: copy.deepcopy(data))
    monkeypatch.setattr(fb.requests, 'Session', Session)
    return state


@pytest.mark.parametrize('change', [
    {'app_id': 'attacker-app'}, {'is_valid': False}, {'is_valid': 'true'}, {'expires_at': 1},
    {'data_access_expires_at': 1}, {'user_id': None}, {'user_id': 'invalid'}, {'type': 'PAGE'},
])
def test_facebook_token_metadata_rejected_before_profile_fetch(facebook, change):
    facebook['claims'].update(change)
    with pytest.raises(HTTPException) as error: fb.verify_facebook_token('test-user-token')
    assert error.value.status_code == 401 and len(facebook['calls']) == 1


def test_facebook_verifies_identity_and_uses_backend_app_proof(facebook):
    result = fb.verify_facebook_token('test-user-token')
    assert result['subject'] == '999' and result['email'] == 'facebook@example.com'
    assert facebook['calls'][0][1]['headers']['Authorization'] == 'Bearer 12345|server-secret-fixture'
    assert len(facebook['calls'][1][1]['params']['appsecret_proof']) == 64
    facebook['profile']['id'] = '1000'
    with pytest.raises(HTTPException) as error: fb.verify_facebook_token('test-user-token')
    assert error.value.status_code == 401


def test_facebook_unconfigured_transport_failure_and_private_fields(facebook, monkeypatch):
    facebook['offline'] = True
    with pytest.raises(HTTPException) as error: fb.verify_facebook_token('test-user-token')
    assert error.value.status_code == 503 and 'not for public' not in error.value.detail
    monkeypatch.delenv('FACEBOOK_APP_SECRET')
    assert fb.facebook_config() == {'enabled': False, 'app_id': None, 'version': None}
    with pytest.raises(HTTPException) as error: fb.verify_facebook_token('test-user-token')
    assert error.value.status_code == 503


def test_facebook_registers_and_reuses_subject_without_exposing_meta_token(facebook):
    async def run():
        async with isolated_database():
            app = FastAPI(); app.include_router(router, prefix='/api')
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://api.test') as client:
                config = (await client.get('/api/auth/facebook/config')).json()
                assert config == {'enabled': True, 'app_id': '12345', 'version': 'v27.0'}
                async def login(origin='https://shop.example.test'):
                    return await client.post('/api/auth/facebook', headers={'Origin': origin}, json={'access_token': 'test-user-token'})
                assert (await login('https://evil.test')).status_code == 403
                assert not facebook['calls']
                first = await login(); assert first.status_code == 200, first.text
                body = first.json(); uid = body['user']['user_id']
                assert body['user']['provider'] == 'facebook' and body['user']['role'] == 'customer'
                assert 'facebook_subject' not in body['user'] and 'password_hash' not in body['user']
                assert (await client.get('/api/auth/me', headers={'Authorization': 'Bearer ' + body['token']})).status_code == 200
                facebook['profile']['email'] = None
                second = await login(); assert second.status_code == 200, second.text
                assert second.json()['user']['user_id'] == uid
                async with read_session() as session:
                    assert await session.scalar(select(func.count()).select_from(m.User)) == 1
                    row = await session.get(m.User, uid)
                    assert row.facebook_subject == '999' and row.email == 'facebook@example.com'
                    tokens = (await session.scalars(select(m.UserSession.token_hash))).all()
                    assert token_digest(body['token']) in tokens and 'test-user-token' not in tokens
                async with session_scope() as session: (await session.get(m.User, uid)).is_active = False
                assert (await login()).status_code == 403
    asyncio.run(run())


@pytest.mark.parametrize('existing', [True, False])
def test_facebook_missing_email_and_email_collision_do_not_merge_accounts(facebook, existing):
    async def run():
        async with isolated_database():
            if existing:
                async with session_scope() as session:
                    session.add(m.User(user_id='existing', email='facebook@example.com', name='Owner', points_balance=100))
            else: facebook['profile'].pop('email')
            app = FastAPI(); app.include_router(router, prefix='/api')
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://api.test') as client:
                result = await client.post('/api/auth/facebook', headers={'Origin': 'https://shop.example.test'}, json={'access_token': 'test-user-token'})
                assert result.status_code == (409 if existing else 422), result.text
                async with read_session() as session:
                    assert await session.scalar(select(func.count()).select_from(m.UserSession)) == 0
                    if existing:
                        row = await session.get(m.User, 'existing')
                        assert row.facebook_subject is None and row.points_balance == 100
    asyncio.run(run())
