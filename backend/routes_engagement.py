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


router = APIRouter(tags=["engagement"])
DAILY_GAME_PLAY_LIMIT = 5
DAILY_POINT_LIMIT = 200
DAILY_ROULETTE_LIMIT = 3
ROULETTE_REWARD_TTL_DAYS = 14


def _today():
    return utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/games")
async def list_games():
    async with read_session() as s:
        games = (await s.scalars(select(m.Game).where(m.Game.is_active.is_(True)).order_by(m.Game.key).limit(20))).all()
        return {"games": [row_dict(game) for game in games]}


@router.post("/games/{game}/submit")
async def submit_game(game: str, payload: dict[str, Any], user: User = Depends(current_user)):
    if game not in ("puzzle", "tetris", "matching", "memory"):
        raise HTTPException(400, "Game tidak dikenal")
    score = max(0, min(integer(payload.get("score", 0), "Skor", -2147483647, 2147483647), 9999))
    async with session_scope() as s:
        fresh = await lock_user(s, user.user_id)
        definition = await s.scalar(select(m.Game).where(m.Game.key == game, m.Game.is_active.is_(True)))
        if definition is None:
            raise HTTPException(400, "Game tidak tersedia")
        today = _today()
        plays = await s.scalar(select(func.count()).select_from(m.GameScore).where(
            m.GameScore.user_id == user.user_id, m.GameScore.game == game, m.GameScore.played_at >= today
        ))
        if plays >= DAILY_GAME_PLAY_LIMIT:
            raise HTTPException(429, "Batas permainan harian tercapai untuk game ini")
        earned = await s.scalar(select(func.coalesce(func.sum(m.PointLog.delta), 0)).where(
            m.PointLog.user_id == user.user_id, m.PointLog.type == "earn_game", m.PointLog.created_at >= today
        ))
        awarded = int(min(score // 10, 50, definition.max_points, max(0, DAILY_POINT_LIMIT - earned)))
        entry = m.GameScore(id=gen_id("gms"), user_id=user.user_id, game=game, score=score, points_awarded=awarded)
        s.add(entry)
        if awarded:
            fresh.points_balance += awarded
            s.add(m.PointLog(id=gen_id("pts"), user_id=user.user_id, delta=awarded,
                            balance_after=fresh.points_balance, type="earn_game", note=f"Game {game} score={score}"))
        await s.flush()
        return {"ok": True, "score": score, "points_awarded": awarded}


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
        count = await s.scalar(select(func.count()).select_from(m.RouletteSpin).where(
            m.RouletteSpin.user_id == user.user_id, m.RouletteSpin.created_at >= _today()
        ))
        if count >= DAILY_ROULETTE_LIMIT:
            raise HTTPException(429, "Batas spin harian tercapai")
        rewards = (await s.scalars(select(m.RouletteReward).where(
            m.RouletteReward.is_active.is_(True), m.RouletteReward.probability > 0
        ).order_by(m.RouletteReward.id).limit(20))).all()
        if not rewards:
            raise HTTPException(503, "Roulette belum dikonfigurasi")
        chosen = random.SystemRandom().choices(rewards, weights=[float(r.probability) for r in rewards], k=1)[0]
        awarded = int(chosen.value) if chosen.type == "points" else 0
        spin = m.RouletteSpin(
            id=gen_id("spn"), user_id=user.user_id, reward_id=chosen.id,
            reward_label=chosen.label, reward_type=chosen.type, reward_value=chosen.value,
            used=awarded > 0, expires_at=utcnow() + timedelta(days=ROULETTE_REWARD_TTL_DAYS),
        )
        s.add(spin)
        if awarded:
            fresh.points_balance += awarded
            s.add(m.PointLog(id=gen_id("pts"), user_id=user.user_id, delta=awarded,
                            balance_after=fresh.points_balance, type="earn_roulette",
                            note=f"Spin reward {chosen.label}"))
        await s.flush()
        return {"ok": True, "spin": row_dict(spin), "reward": row_dict(chosen)}


@router.get("/roulette/my-rewards")
async def my_rewards(user: User = Depends(current_user)):
    async with read_session() as s:
        spins = (await s.scalars(select(m.RouletteSpin).where(m.RouletteSpin.user_id == user.user_id)
                                .order_by(m.RouletteSpin.created_at.desc(), m.RouletteSpin.id).limit(50))).all()
        return {"spins": [row_dict(spin) for spin in spins]}


@router.get("/points/logs")
async def points_logs(user: User = Depends(current_user)):
    async with read_session() as s:
        fresh = await s.get(m.User, user.user_id)
        logs = (await s.scalars(select(m.PointLog).where(m.PointLog.user_id == user.user_id)
                               .order_by(m.PointLog.created_at.desc(), m.PointLog.id).limit(100))).all()
        return {"logs": [row_dict(log) for log in logs], "balance": fresh.points_balance}


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
