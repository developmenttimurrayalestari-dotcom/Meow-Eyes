"""Native Google authentication: real signed tokens and isolated SQL accounts."""
import asyncio
from datetime import datetime, timedelta, timezone
import json
import time

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi import FastAPI, HTTPException
from google.auth import crypt, jwt
from google.auth.exceptions import TransportError
import httpx
import pytest
from sqlalchemy import func, select

from auth import hash_secret, token_digest
from database import read_session, session_scope
import google_identity as identity
from mysql import models as m
from routes_auth import router
from tests_mysql.sql_helpers import isolated_database

CLIENT = 'test-client.apps.googleusercontent.com'
NONCE = 'random-browser-nonce-' + 'a' * 32
ORIGIN = 'http://localhost:3000'


@pytest.fixture(scope='module')
def google_keys():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Google test issuer')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=1))
            .sign(key, hashes.SHA256()))
    signer = crypt.RSASigner.from_string(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()), key_id='test-key')
    return signer, cert.public_bytes(serialization.Encoding.PEM).decode()


@pytest.fixture
def google_token(monkeypatch, google_keys):
    signer, certificate = google_keys
    monkeypatch.setenv('GOOGLE_CLIENT_ID', CLIENT)
    monkeypatch.setenv('CORS_ORIGINS', ORIGIN)

    def transport(url, **kwargs):
        assert url == 'https://www.googleapis.com/oauth2/v1/certs'
        assert kwargs['timeout'] == 10
        return type('Reply', (), {'status': 200, 'data': json.dumps({'test-key': certificate}).encode()})()

    monkeypatch.setattr(identity, 'GoogleRequest', lambda session: transport)

    def token(**overrides):
        now = int(time.time())
        claims = dict(iss='https://accounts.google.com', aud=CLIENT, sub='google-subject-1',
                      iat=now, exp=now + 3600, email='customer@gmail.com', email_verified=True,
                      nonce=NONCE, name='Google Customer', picture='https://example.com/avatar.png')
        claims.update(overrides)
        return jwt.encode(signer, claims).decode()
    return token


def test_official_verifier_accepts_signed_google_token(google_token):
    result = identity.verify_google_credential(google_token(), NONCE)
    assert result['subject'] == 'google-subject-1' and result['authoritative_email'] is True
    assert result['email'] == 'customer@gmail.com'


@pytest.mark.parametrize('claims', [
    {'aud': 'other-client'}, {'iss': 'https://attacker.test'}, {'exp': 1},
    {'nonce': 'wrong'}, {'nonce': None}, {'nonce': '\u2603'}, {'email_verified': False},
    {'email_verified': 'true'}, {'email': 'invalid'}, {'sub': ''}, {'sub': 123},
    {'azp': 'other-client'},
])
def test_invalid_signed_claims_are_rejected(google_token, claims):
    with pytest.raises(HTTPException) as error:
        identity.verify_google_credential(google_token(**claims), NONCE)
    assert error.value.status_code == 401


def test_modified_signature_missing_config_and_network_failure(monkeypatch, google_token):
    credential = google_token()
    parts = credential.split('.')
    parts[2] = ('A' if parts[2][0] != 'A' else 'B') + parts[2][1:]
    with pytest.raises(HTTPException) as error:
        identity.verify_google_credential('.'.join(parts), NONCE)
    assert error.value.status_code == 401
    monkeypatch.delenv('GOOGLE_CLIENT_ID')
    with pytest.raises(HTTPException) as error:
        identity.verify_google_credential(credential, NONCE)
    assert error.value.status_code == 503
    monkeypatch.setenv('GOOGLE_CLIENT_ID', CLIENT)
    def offline(*args, **kwargs): raise TransportError('private transport details')
    monkeypatch.setattr(identity.id_token, 'verify_oauth2_token', offline)
    with pytest.raises(HTTPException) as error:
        identity.verify_google_credential(credential, NONCE)
    assert error.value.status_code == 503 and 'private' not in error.value.detail


def test_google_registration_stable_subject_and_hashed_local_session(google_token):
    async def scenario():
        async with isolated_database():
            app = FastAPI(); app.include_router(router, prefix='/api')
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                assert (await client.get('/api/auth/google/config')).json() == {'enabled': True, 'client_id': CLIENT}
                async def login(**claims):
                    return await client.post('/api/auth/google', headers={'Origin': ORIGIN},
                        json={'credential': google_token(**claims), 'nonce': NONCE})
                first = await login()
                assert first.status_code == 200, first.text
                body = first.json(); uid = body['user']['user_id']
                assert body['user']['provider'] == 'google' and body['user']['has_pin'] is False
                assert body['user']['role'] == 'customer' and 'google_subject' not in body['user']
                async with read_session() as session:
                    row = await session.get(m.User, uid)
                    assert row.google_subject == 'google-subject-1' and row.password_hash is None
                    stored = await session.scalar(select(m.UserSession))
                    assert stored.token_hash == token_digest(body['token'])
                # The same Google subject remains the same local account after an email change.
                second = await login(email='changed@gmail.com')
                assert second.json()['user']['user_id'] == uid
                assert (await client.get('/api/auth/me', headers={'Authorization': 'Bearer ' + body['token']})).status_code == 200
                async with read_session() as session:
                    assert await session.scalar(select(func.count()).select_from(m.User)) == 1
                assert (await client.post('/api/auth/google-session', json={'session_id': 'old-broker'})).status_code == 404
    asyncio.run(scenario())


def test_link_old_gmail_account_without_changing_pin_points_password_or_role(google_token):
    async def scenario():
        async with isolated_database():
            password, pin = hash_secret('OldPassword1!'), hash_secret('123456')
            async with session_scope() as session:
                session.add(m.User(user_id='old-user', email='customer@gmail.com', name='Original Name',
                    password_hash=password, pin_hash=pin, role='staff', points_balance=650))
            app = FastAPI(); app.include_router(router, prefix='/api')
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                result = await client.post('/api/auth/google', headers={'Origin': ORIGIN},
                    json={'credential': google_token(), 'nonce': NONCE})
                assert result.status_code == 200, result.text
                assert result.json()['user']['user_id'] == 'old-user'
                assert result.json()['user']['has_pin'] is True
                async with read_session() as session:
                    row = await session.get(m.User, 'old-user')
                    assert (row.name, row.role, row.points_balance, row.password_hash, row.pin_hash) == (
                        'Original Name', 'staff', 650, password, pin)
                    assert row.provider == 'password' and row.google_subject == 'google-subject-1'
                assert (await client.post('/api/auth/login', json={'email': 'customer@gmail.com', 'password': 'OldPassword1!'})).status_code == 200
    asyncio.run(scenario())


@pytest.mark.parametrize('case,status', [('inactive', 403), ('subject-conflict', 409), ('third-party-email', 409)])
def test_inactive_and_conflicting_accounts_never_create_sessions(google_token, case, status):
    async def scenario():
        async with isolated_database():
            email = 'thirdparty@example.com' if case == 'third-party-email' else 'customer@gmail.com'
            async with session_scope() as session:
                session.add(m.User(user_id='old', name='Existing', email=email, is_active=case != 'inactive',
                    google_subject='other-google-sub' if case == 'subject-conflict' else None))
            app = FastAPI(); app.include_router(router, prefix='/api')
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                result = await client.post('/api/auth/google', headers={'Origin': ORIGIN},
                    json={'credential': google_token(email=email), 'nonce': NONCE})
                assert result.status_code == status, result.text
                async with read_session() as session:
                    assert await session.scalar(select(func.count()).select_from(m.UserSession)) == 0
                    if case == 'inactive': assert (await session.get(m.User, 'old')).google_subject is None
    asyncio.run(scenario())


@pytest.mark.parametrize('origin', [None, 'null', 'https://evil.test', ORIGIN + '.evil.test'])
def test_google_login_rejects_cross_site_requests_before_token_exchange(google_token, monkeypatch, origin):
    def forbidden(*args): raise AssertionError('Untrusted origin reached verifier')
    monkeypatch.setattr('routes_auth.verify_google_credential', forbidden)
    async def scenario():
        app = FastAPI(); app.include_router(router, prefix='/api')
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            result = await client.post('/api/auth/google', headers={'Origin': origin} if origin else {},
                json={'credential': google_token(), 'nonce': NONCE})
            assert result.status_code == 403
    asyncio.run(scenario())
