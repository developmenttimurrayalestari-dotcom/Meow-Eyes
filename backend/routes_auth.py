"""Authentication routes backed by relational users, permissions and sessions."""
from __future__ import annotations
import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from database import session_scope, read_session
from mysql.models import User as SQLUser, UserSession
from mysql.api import user_dict
from mysql.base import utcnow
from models import RegisterRequest, LoginRequest, PinSetupRequest, PinVerifyRequest, GoogleSessionRequest, User, gen_id
from auth import hash_secret, verify_secret, create_session, current_user, current_user_optional, public_user, verify_pin_or_raise

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookie(resp: Response, token: str) -> None:
    resp.set_cookie("session_token", token, path="/", httponly=True,
                    secure=True, samesite="none", max_age=60 * 60 * 24 * 7)


@router.post("/register")
async def register(req: RegisterRequest, response: Response):
    email = str(req.email).strip().lower()
    hashed = hash_secret(req.password)
    try:
        async with session_scope() as session:
            if await session.scalar(select(SQLUser.user_id).where(func.lower(SQLUser.email) == email)):
                raise HTTPException(400, "Email sudah terdaftar")
            row = SQLUser(user_id=gen_id("usr"), email=email, name=req.name,
                          password_hash=hashed, provider="password")
            session.add(row)
            await session.flush()
            token, _ = await create_session(row.user_id, session)
            user = User(**await user_dict(session, row))
    except IntegrityError:
        raise HTTPException(400, "Email sudah terdaftar") from None
    _set_cookie(response, token)
    return {"token": token, "user": public_user(user).model_dump()}


@router.post("/login")
async def login(req: LoginRequest, response: Response):
    async with session_scope() as session:
        row = await session.scalar(select(SQLUser).where(
            func.lower(SQLUser.email) == str(req.email).strip().lower()))
        if row is None or not row.password_hash or not verify_secret(req.password, row.password_hash):
            raise HTTPException(401, "Email atau password salah")
        if not row.is_active:
            raise HTTPException(403, "Akun dinonaktifkan")
        token, _ = await create_session(row.user_id, session)
        user = User(**await user_dict(session, row))
    _set_cookie(response, token)
    return {"token": token, "user": public_user(user).model_dump()}


@router.post("/google-session")
async def google_session(req: GoogleSessionRequest, response: Response):
    """Preserve the existing Emergent identity exchange; no DB lock during HTTP."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": req.session_id})
        if r.status_code != 200:
            raise HTTPException(401, "Sesi Google tidak valid")
        data = r.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(503, "Layanan autentikasi sementara tidak tersedia") from None
    if not isinstance(data, dict) or not data.get("email"):
        raise HTTPException(400, "Data Google tidak lengkap")
    from pydantic import ValidationError
    try:
        candidate = User(email=data["email"], name=data.get("name") or data["email"],
                         picture=data.get("picture"), provider="google")
    except ValidationError:
        raise HTTPException(400, "Data Google tidak valid") from None
    email = str(candidate.email).strip().lower()
    async with session_scope() as session:
        row = await session.scalar(select(SQLUser).where(func.lower(SQLUser.email) == email).with_for_update())
        if row is None:
            row = SQLUser(user_id=candidate.user_id, email=email, name=candidate.name,
                          picture=candidate.picture, provider="google")
            session.add(row)
            await session.flush()
        elif not row.is_active:
            raise HTTPException(403, "Akun dinonaktifkan")
        else:
            row.name, row.picture, row.updated_at = candidate.name, candidate.picture, utcnow()
        token, _ = await create_session(row.user_id, session)
        user = User(**await user_dict(session, row))
    _set_cookie(response, token)
    return {"token": token, "user": public_user(user).model_dump()}


@router.get("/me")
async def me(user: User = Depends(current_user)):
    return {"user": public_user(user).model_dump()}


@router.post("/logout")
async def logout(response: Response, user=Depends(current_user_optional)):
    response.delete_cookie("session_token", path="/", secure=True, httponly=True, samesite="none")
    if user:
        async with session_scope() as session:
            await session.execute(delete(UserSession).where(UserSession.user_id == user.user_id))
    return {"ok": True}


@router.post("/pin/setup")
async def setup_pin(req: PinSetupRequest, user: User = Depends(current_user)):
    hashed = hash_secret(req.pin)
    async with session_scope() as session:
        row = await session.scalar(select(SQLUser).where(SQLUser.user_id == user.user_id).with_for_update())
        if row is None or not row.is_active:
            raise HTTPException(403, "Akun dinonaktifkan")
        row.pin_hash, row.pin_failed_attempts, row.pin_locked_until = hashed, 0, None
        row.updated_at = utcnow()
    return {"ok": True}


@router.post("/pin/verify")
async def verify_pin(req: PinVerifyRequest, user: User = Depends(current_user)):
    await verify_pin_or_raise(user, req.pin)
    return {"ok": True}
