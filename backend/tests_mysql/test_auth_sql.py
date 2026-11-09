"""SQL authentication, transaction rollback, session/PIN and permission contracts."""
import asyncio
from datetime import timedelta
import httpx
from fastapi import FastAPI, Depends, HTTPException
import pytest
from sqlalchemy import select, func
from auth import token_digest, require_permission
from database import session_scope, read_session
from mysql import models as m
from mysql.base import utcnow
from mysql.api import values_for
from routes_auth import router
from tests_mysql.sql_helpers import isolated_database


def test_register_login_hashed_sessions_revocation_and_permissions():
    async def scenario():
        async with isolated_database():
            app = FastAPI()
            app.include_router(router, prefix="/api")
            @app.get("/staff-probe")
            async def staff_probe(user=Depends(require_permission("product.view"))):
                return {"id": user.user_id}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                result = await client.post("/api/auth/register", json={"email": "Auth@Example.com", "name": "Tester", "password": "Example123!"})
                assert result.status_code == 200, result.text
                body = result.json()
                assert "password_hash" not in body["user"] and body["user"]["email"] == "auth@example.com"
                token, uid = body["token"], body["user"]["user_id"]
                async with read_session() as session:
                    stored = await session.scalar(select(m.UserSession))
                    assert stored.token_hash == token_digest(token) and token not in stored.token_hash
                    assert not hasattr(stored, "session_token")
                headers = {"Authorization": f"Bearer {token}"}
                assert (await client.get("/api/auth/me", headers=headers)).status_code == 200
                assert (await client.get("/staff-probe", headers=headers)).status_code == 403
                async with session_scope() as session:
                    user = await session.get(m.User, uid)
                    user.role = "staff"
                    session.add(m.UserPermission(user_id=uid, permission="product.view"))
                assert (await client.get("/staff-probe", headers=headers)).status_code == 200
                assert (await client.post("/api/auth/register", json={"email": "auth@example.com", "name": "Duplicate", "password": "Example123!"})).status_code == 400
                assert (await client.post("/api/auth/login", json={"email": "auth@example.com", "password": "wrong"})).status_code == 401
                assert (await client.post("/api/auth/login", json={"email": "auth@example.com", "password": "Example123!"})).status_code == 200
                assert (await client.post("/api/auth/logout", headers=headers)).status_code == 200
                assert (await client.get("/api/auth/me", headers=headers)).status_code == 401
                async with read_session() as session:
                    assert await session.scalar(select(func.count()).select_from(m.UserSession)) == 0
    asyncio.run(scenario())


def test_pin_attempts_commit_on_failure_and_reset_after_lock_expiry():
    async def scenario():
        async with isolated_database():
            app = FastAPI()
            app.include_router(router, prefix="/api")
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.post("/api/auth/register", json={"email": "pin@example.com", "name": "PIN", "password": "Example123!"})
                uid = r.json()["user"]["user_id"]
                headers = {"Authorization": "Bearer " + r.json()["token"]}
                assert (await client.post("/api/auth/pin/setup", json={"pin": "123456"}, headers=headers)).status_code == 200
                for attempt in range(5):
                    failure = await client.post("/api/auth/pin/verify", json={"pin": "000000"}, headers=headers)
                    assert failure.status_code == (423 if attempt == 4 else 400), failure.text
                assert (await client.post("/api/auth/pin/verify", json={"pin": "123456"}, headers=headers)).status_code == 423
                async with session_scope() as session:
                    row = await session.get(m.User, uid)
                    assert row.pin_locked_until > utcnow()
                    row.pin_locked_until = utcnow() - timedelta(seconds=1)
                assert (await client.post("/api/auth/pin/verify", json={"pin": "123456"}, headers=headers)).status_code == 200
                async with read_session() as session:
                    row = await session.get(m.User, uid)
                    assert row.pin_locked_until is None and row.pin_failed_attempts == 0
    asyncio.run(scenario())


def test_expired_and_inactive_sessions_are_rejected():
    async def scenario():
        async with isolated_database():
            app = FastAPI()
            app.include_router(router, prefix="/api")
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.post("/api/auth/register", json={"email": "expiry@example.com", "name": "Expiry", "password": "Example123!"})
                headers = {"Authorization": "Bearer " + r.json()["token"]}
                uid = r.json()["user"]["user_id"]
                async with session_scope() as session:
                    row = await session.get(m.User, uid)
                    row.is_active = False
                assert (await client.get("/api/auth/me", headers=headers)).status_code == 403
                assert (await client.post("/api/auth/login", json={"email": "expiry@example.com", "password": "Example123!"})).status_code == 403
                async with session_scope() as session:
                    row = await session.get(m.User, uid)
                    row.is_active = True
                    sess = await session.scalar(select(m.UserSession))
                    sess.expires_at = utcnow() - timedelta(seconds=1)
                assert (await client.get("/api/auth/me", headers=headers)).status_code == 401
    asyncio.run(scenario())


def test_sql_unit_of_work_rolls_back_and_read_session_never_commits():
    async def scenario():
        async with isolated_database():
            with pytest.raises(RuntimeError):
                async with session_scope() as session:
                    session.add(m.User(user_id="rollback", email="rollback@example.com", name="Rollback"))
                    await session.flush()
                    raise RuntimeError("later operation failed")
            async with read_session() as session:
                assert await session.get(m.User, "rollback") is None
                session.add(m.User(user_id="read", email="read@example.com", name="Read"))
                await session.flush()
            async with read_session() as session:
                assert await session.get(m.User, "read") is None
    asyncio.run(scenario())


@pytest.mark.parametrize("payload", [{"price": "NaN"}, {"price": "Infinity"}, {"price": True}, {"price": None}])
def test_nonfinite_or_missing_money_is_rejected(payload):
    with pytest.raises(HTTPException) as exc:
        values_for(m.Product, payload)
    assert exc.value.status_code == 422
