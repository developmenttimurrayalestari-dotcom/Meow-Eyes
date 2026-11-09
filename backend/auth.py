"""Auth utilities: password & PIN hashing, session, dependencies."""
from __future__ import annotations
import os
import bcrypt
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import Cookie, Header, HTTPException, Depends
from database import session_scope, read_session
from sqlalchemy import select
from mysql.models import User as SQLUser, UserSession
from mysql.api import user_dict
from mysql.base import utcnow
from models import User, UserPublic, gen_id, now_iso


PIN_MAX_ATTEMPTS = 5
PIN_LOCK_MINUTES = 15
SESSION_DAYS = 7


def hash_secret(value: str) -> str:
    if not value or len(value.encode("utf-8")) > 72:
        raise HTTPException(422, "Password maksimal 72 byte UTF-8")
    return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_secret(value: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def gen_session_token() -> str:
    return secrets.token_urlsafe(48)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_session(user_id: str, session=None) -> tuple[str, str]:
    """Hash the random token at rest, optionally in the caller's transaction."""
    token = gen_session_token()
    expires = utcnow() + timedelta(days=SESSION_DAYS)
    row = UserSession(session_id=gen_id("ses"), token_hash=token_digest(token),
                      user_id=user_id, expires_at=expires)
    if session is None:
        async with session_scope() as work:
            work.add(row)
    else:
        session.add(row)
    return token, expires.isoformat()


async def get_session_user(token: str) -> Optional[User]:
    if not token or len(token) > 4096:
        return None
    async with read_session() as session:
        row = await session.scalar(select(SQLUser).join(
            UserSession, UserSession.user_id == SQLUser.user_id).where(
                UserSession.token_hash == token_digest(token),
                UserSession.expires_at > utcnow(), UserSession.revoked_at.is_(None)))
        return User(**await user_dict(session, row)) if row is not None else None


def public_user(u: User) -> UserPublic:
    return UserPublic(
        user_id=u.user_id, email=u.email, name=u.name, picture=u.picture,
        role=u.role, provider=u.provider, has_pin=bool(u.pin_hash),
        points_balance=u.points_balance, permissions=u.permissions,
        created_at=u.created_at,
    )


async def current_user_optional(
    session_token: Optional[str] = Cookie(default=None),
    authorization: Optional[str] = Header(default=None),
) -> Optional[User]:
    token = session_token
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        return None
    return await get_session_user(token)


async def current_user(
    user: Optional[User] = Depends(current_user_optional),
) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Tidak terautentikasi")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Akun dinonaktifkan")
    return user


async def current_admin(user: User = Depends(current_user)) -> User:
    if user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Akses admin diperlukan")
    return user


async def current_admin_or_staff(user: User = Depends(current_user)) -> User:
    """Allow staff, admin, and super_admin (staff routes fall through to permission checks)."""
    if user.role not in ("staff", "admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Akses staff/admin diperlukan")
    return user


def require_permission(perm: str):
    """Factory that returns a FastAPI dependency enforcing a specific permission.

    Admins and super_admins bypass permission checks. Staff must have `perm` in
    their `permissions` list.
    """
    async def _dep(user: User = Depends(current_user)) -> User:
        if user.role in ("admin", "super_admin"):
            return user
        if user.role == "staff" and perm in (user.permissions or []):
            return user
        raise HTTPException(status_code=403, detail=f"Izin '{perm}' diperlukan")
    return _dep


async def current_super_admin(user: User = Depends(current_user)) -> User:
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Akses super admin diperlukan")
    return user


async def verify_pin_or_raise(user: User, pin: str) -> None:
    """Serialize PIN attempts and commit failed counters before raising an error."""
    error = None
    async with session_scope() as session:
        row = await session.scalar(select(SQLUser).where(
            SQLUser.user_id == user.user_id).with_for_update())
        if row is None or not row.is_active:
            raise HTTPException(403, "Akun tidak aktif")
        if not row.pin_hash:
            raise HTTPException(400, "PIN belum diatur")
        if row.pin_locked_until and row.pin_locked_until > utcnow():
            raise HTTPException(423, f"PIN terkunci, coba lagi nanti ({row.pin_locked_until.isoformat()})")
        if verify_secret(pin, row.pin_hash):
            row.pin_failed_attempts = 0
            row.pin_locked_until = None
        else:
            attempts = row.pin_failed_attempts + 1
            if attempts >= PIN_MAX_ATTEMPTS:
                row.pin_locked_until = utcnow() + timedelta(minutes=PIN_LOCK_MINUTES)
                row.pin_failed_attempts = 0
                error = HTTPException(423, "PIN salah berkali-kali, dikunci 15 menit")
            else:
                row.pin_failed_attempts = attempts
                error = HTTPException(400, f"PIN salah ({PIN_MAX_ATTEMPTS - attempts} percobaan tersisa)")
        row.updated_at = utcnow()
    if error is not None:
        raise error
