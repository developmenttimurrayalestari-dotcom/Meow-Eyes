"""Social account completion, with isolated SQL sessions and no OAuth network."""
import asyncio
import httpx
import pytest
from fastapi import Depends, FastAPI
from auth import create_session, current_user, hash_secret, verify_secret
from database import read_session, session_scope
from mysql import models as m
from routes_auth import router
from tests_mysql.sql_helpers import isolated_database


@pytest.mark.parametrize('provider', ['google', 'facebook'])
@pytest.mark.parametrize('existing_pin', [False, True])
def test_password_and_pin_are_required_and_existing_credentials_are_preserved(provider, existing_pin):
    async def run():
        async with isolated_database():
            original_pin = hash_secret('123456') if existing_pin else None
            async with session_scope() as s:
                s.add(m.User(user_id='social', name='Customer', email='social@example.com',
                             provider=provider, pin_hash=original_pin))
                await s.flush()
                token, _ = await create_session('social', s)
            app = FastAPI(); app.include_router(router, prefix='/api')
            @app.get('/private')
            async def private(user=Depends(current_user)):
                return {'user_id': user.user_id}
            headers = {'Authorization': 'Bearer ' + token}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                assert (await client.post('/api/auth/password/setup', json={'password':'NewPassword123', 'confirm_password':'NewPassword123'})).status_code == 401
                before = (await client.get('/api/auth/me', headers=headers)).json()['user']
                assert before['has_password'] is False and before['has_pin'] == existing_pin
                assert 'password_hash' not in before
                assert (await client.get('/private', headers=headers)).status_code == 403
                assert (await client.post('/api/auth/pin/setup', headers=headers, json={'pin':'123456'})).status_code == 403
                for password, confirmation in [('short','short'), ('NewPassword123','DifferentPassword'), ('🐱'*20,'🐱'*20)]:
                    assert (await client.post('/api/auth/password/setup', headers=headers,
                        json={'password':password, 'confirm_password':confirmation})).status_code == 422
                result = await client.post('/api/auth/password/setup', headers=headers,
                    json={'password':'NewPassword123', 'confirm_password':'NewPassword123'})
                assert result.status_code == 200, result.text
                assert (await client.get('/api/auth/me', headers=headers)).json()['user']['has_password'] is True
                assert (await client.get('/private', headers=headers)).status_code == (200 if existing_pin else 403)
                if not existing_pin:
                    assert (await client.post('/api/auth/pin/setup', headers=headers, json={'pin':'123456'})).status_code == 200
                assert (await client.get('/private', headers=headers)).status_code == 200
                assert (await client.post('/api/auth/password/setup', headers=headers,
                    json={'password':'OverwritePassword', 'confirm_password':'OverwritePassword'})).status_code == 409
                login = await client.post('/api/auth/login', json={'email':'social@example.com','password':'NewPassword123'})
                assert login.status_code == 200, login.text
                async with read_session() as s:
                    row = await s.get(m.User, 'social')
                    assert row.password_hash != 'NewPassword123' and verify_secret('NewPassword123', row.password_hash)
                    assert verify_secret('123456', row.pin_hash)
                    if existing_pin: assert row.pin_hash == original_pin
                    assert row.provider == provider
    asyncio.run(run())
