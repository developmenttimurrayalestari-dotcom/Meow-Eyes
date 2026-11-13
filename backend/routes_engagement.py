"""Games, rewards, balances and subscriptions backed by relational queries."""
from __future__ import annotations

from datetime import timedelta
import random
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from auth import current_user
from database import read_session, session_scope
from models import User, gen_id
from mysql import models as m
from mysql.api import row_dict
from mysql.base import utcnow
from mysql.commerce import integer, lock_user
from mysql import games as verified_games, points as wallet


router = APIRouter(tags=["engagement"])
ROULETTE_REWARD_TTL_DAYS = 14


def _today():
    return utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/games")
async def list_games():
    async with read_session() as s:
        return {"games": await verified_games.catalog(s)}


@router.post("/games/{game}/submit")
async def submit_game(game: str, payload: dict[str, Any], user: User = Depends(current_user)):
    raise HTTPException(410, 'Pengiriman skor langsung dinonaktifkan. Mulai ronde baru dari halaman Games.')


@router.get("/games/leaderboard")
async def game_leaderboard(game: str, limit: int = Query(default=10, ge=1, le=100)):
    async with read_session() as s:
        # Explicit grouped columns work with ONLY_FULL_GROUP_BY on MySQL 5.7.
        rows = (await s.execute(select(m.User.name, func.max(m.GameScore.score).label("best"))
            .join(m.GameScore, m.GameScore.user_id == m.User.user_id)
            .where(m.GameScore.game == game)
            .group_by(m.User.user_id, m.User.name)
            .order_by(func.max(m.GameScore.score).desc(), m.User.user_id).limit(limit))).all()
        return {"leaderboard": [{"user_name": name, "score": best} for name, best in rows]}


@router.get("/roulette/rewards")
async def list_rewards():
    async with read_session() as s:
        rewards = (await s.scalars(select(m.RouletteReward).where(m.RouletteReward.is_active.is_(True))
                                  .order_by(m.RouletteReward.id).limit(20))).all()
        return {"rewards": [row_dict(reward) for reward in rewards]}


@router.post("/roulette/spin")
async def spin_roulette(user: User = Depends(current_user)):
    async with session_scope() as s:
        fresh = await lock_user(s, user.user_id)
        _, rule = await verified_games.definition(s, 'roulette')
        previous = await s.scalar(select(m.RouletteSpin).where(m.RouletteSpin.user_id == user.user_id).order_by(m.RouletteSpin.created_at.desc()).limit(1))
        remaining = max(0, int((previous.created_at + timedelta(seconds=rule.cooldown_seconds) - utcnow()).total_seconds())) if previous else 0
        if remaining: raise HTTPException(429, f'Bisa diputar kembali dalam {remaining} detik', headers={'Retry-After': str(remaining)})
        rewards = (await s.scalars(select(m.RouletteReward).where(
            m.RouletteReward.is_active.is_(True), m.RouletteReward.probability > 0
        ).order_by(m.RouletteReward.id).limit(20))).all()
        if not rewards:
            raise HTTPException(503, "Roulette belum dikonfigurasi")
        chosen = random.SystemRandom().choices(rewards, weights=[float(r.probability) for r in rewards], k=1)[0]
        awarded = min(rule.max_points, int(chosen.value)) if chosen.type == "points" else 0
        spin = m.RouletteSpin(
            id=gen_id("spn"), user_id=user.user_id, reward_id=chosen.id,
            reward_label=chosen.label, reward_type=chosen.type, reward_value=awarded if chosen.type == 'points' else chosen.value,
            used=chosen.type == 'points', expires_at=utcnow() + timedelta(days=rule.expiry_days if chosen.type == 'points' else ROULETTE_REWARD_TTL_DAYS),
        )
        s.add(spin)
        await wallet.credit(s, fresh, awarded, source='earn_roulette', key='roulette:' + spin.id, expiry_days=rule.expiry_days, note=chosen.label)
        await s.flush()
        return {"ok": True, "spin": row_dict(spin), "reward": {**row_dict(chosen), 'value': awarded if chosen.type == 'points' else float(chosen.value)}}


@router.get("/roulette/my-rewards")
async def my_rewards(user: User = Depends(current_user)):
    async with read_session() as s:
        spins = (await s.scalars(select(m.RouletteSpin).where(m.RouletteSpin.user_id == user.user_id)
                                .order_by(m.RouletteSpin.created_at.desc(), m.RouletteSpin.id).limit(50))).all()
        return {"spins": [row_dict(spin) for spin in spins]}


@router.get("/points/logs")
async def points_logs(user: User = Depends(current_user)):
    async with session_scope() as s:
        return await wallet.wallet_payload(s, await lock_user(s, user.user_id))

@router.get('/games/puzzle-levels')
async def puzzle_levels():
    async with read_session() as s:
        return {'levels': [row_dict(row) for row in (await s.scalars(select(m.PuzzleLevel).where(m.PuzzleLevel.is_active.is_(True)).order_by(m.PuzzleLevel.level))).all()]}

@router.post('/games/{key}/start')
async def start_game(key: str, payload: dict[str, Any], user: User = Depends(current_user)):
    async with session_scope() as s:
        return await verified_games.start(s, await lock_user(s, user.user_id), key, integer(payload.get('level', 1), 'Level', 1, 20))

@router.post('/game-sessions/{session_id}/finish')
async def finish_game(session_id: str, payload: dict[str, Any], user: User = Depends(current_user)):
    async with session_scope() as s:
        return await verified_games.finish(s, await lock_user(s, user.user_id), session_id, payload)


def _email(payload: dict[str, Any]) -> str:
    value = payload.get("email")
    if not isinstance(value, str):
        raise HTTPException(400, "Email tidak valid")
    try:
        return str(TypeAdapter(EmailStr).validate_python(value.strip().lower()))
    except ValidationError:
        raise HTTPException(400, "Email tidak valid") from None


@router.post("/newsletter/subscribe")
async def subscribe_newsletter(payload: dict[str, Any]):
    email = _email(payload)
    async with session_scope() as s:
        values = {"id": gen_id("nws"), "email": email, "is_active": True}
        if s.get_bind().dialect.name == "mysql":
            statement = mysql_insert(m.NewsletterSubscriber).values(**values).on_duplicate_key_update(is_active=True)
        elif s.get_bind().dialect.name == "sqlite":
            # Portable contract tests only; production uses the MySQL branch.
            statement = sqlite_insert(m.NewsletterSubscriber).values(**values).on_conflict_do_update(
                index_elements=["email"], set_={"is_active": True},
            )
        else:
            raise RuntimeError("Unsupported newsletter database dialect")
        # A single statement avoids competing locks on a missing unique key
        # under MySQL 5.7 REPEATABLE READ. Existing subscriber identity stays.
        await s.execute(statement)
    return {"ok": True}


@router.post("/newsletter/unsubscribe")
async def unsubscribe_newsletter(payload: dict[str, Any]):
    email = _email(payload)
    async with session_scope() as s:
        await s.execute(update(m.NewsletterSubscriber).where(m.NewsletterSubscriber.email == email).values(is_active=False))
    return {"ok": True}


@router.post("/products/{product_id}/subscribe")
async def subscribe_product(product_id: str, user: User = Depends(current_user)):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        if await s.scalar(select(m.Product.id).where(m.Product.id == product_id, m.Product.is_active.is_(True))) is None:
            raise HTTPException(404, "Produk tidak ditemukan")
        existing = await s.scalar(select(m.ProductSubscription.id).where(
            m.ProductSubscription.user_id == user.user_id, m.ProductSubscription.product_id == product_id
        ))
        if existing is None:
            s.add(m.ProductSubscription(id=gen_id("psb"), user_id=user.user_id, product_id=product_id))
            await s.flush()
    return {"ok": True}


@router.delete("/products/{product_id}/subscribe")
async def unsubscribe_product(product_id: str, user: User = Depends(current_user)):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        await s.execute(delete(m.ProductSubscription).where(
            m.ProductSubscription.user_id == user.user_id, m.ProductSubscription.product_id == product_id
        ))
    return {"ok": True}


@router.get("/product-subscriptions")
async def my_product_subs(user: User = Depends(current_user)):
    async with read_session() as s:
        rows = (await s.execute(select(m.ProductSubscription, m.Product).join(m.Product).where(
            m.ProductSubscription.user_id == user.user_id
        ).order_by(m.ProductSubscription.created_at.desc(), m.ProductSubscription.id).limit(100))).all()
        return {"items": [{**row_dict(subscription), "product": {key: row_dict(product)[key]
            for key in ("id", "name", "slug", "main_image", "price")}}
            for subscription, product in rows]}
