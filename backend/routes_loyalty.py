"""Admin loyalty settings and versioned game/event configuration."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, func
from auth import current_admin
from models import User
from database import read_session, session_scope
from mysql import models as m, points, games
from mysql.api import row_dict
from mysql.base import utcnow
from mysql.commerce import lock_user

router = APIRouter(tags=['loyalty-admin'])

class RateInput(BaseModel):
    rate: Decimal = Field(ge=1, le=1000000, decimal_places=4)
    version: int = Field(ge=1)
    cashback_valuation: Literal['locked'] = 'locked'

@router.get('/admin/points/settings')
async def get_settings(admin: User = Depends(current_admin)):
    async with session_scope() as s:
        return row_dict(await points.settings(s))

@router.put('/admin/points/settings')
async def save_settings(body: RateInput, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        config = await points.settings(s, lock=True)
        if config.version != body.version: raise HTTPException(409, 'Pengaturan sudah berubah. Muat ulang halaman.')
        config.version += 1; config.rate = body.rate; config.cashback_valuation = body.cashback_valuation; config.updated_at = utcnow()
        s.add(m.PointRateVersion(version=config.version, rate=config.rate, cashback_valuation=config.cashback_valuation, actor_id=admin.user_id))
        await s.flush()
        return row_dict(config)

@router.get('/admin/points/customers')
async def customers(q: str = '', offset: int = Query(0, ge=0), admin: User = Depends(current_admin)):
    async with session_scope() as s:
        query = select(m.User).where(m.User.role == 'customer')
        if q: query = query.where(m.User.name.contains(q, autoescape=True) | m.User.email.contains(q, autoescape=True))
        rows = (await s.scalars(query.order_by(m.User.name, m.User.user_id).offset(offset).limit(30).with_for_update())).all()
        result = []
        for user in rows:
            await points.expire(s, user)
            entries = (await s.execute(select(m.PointHistory.delta, m.PointHistory.source).where(m.PointHistory.user_id == user.user_id))).all()
            earned = sum(delta for delta, source in entries if delta > 0 and source != 'refund_point')
            spent = -sum(delta for delta, source in entries if delta < 0 and source == 'redeem_checkout') - sum(delta for delta, source in entries if source == 'refund_point')
            result.append({'user_id': user.user_id, 'name': user.name, 'email': user.email, 'earned': earned, 'spent': max(0, spent),
                'expired': -sum(delta for delta, source in entries if source == 'expire_points'), 'balance': user.points_balance})
        return {'customers': result, 'next_offset': offset + 30 if len(rows) == 30 else None}

@router.get('/admin/points/customers/{user_id}')
async def customer_wallet(user_id: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        return await points.wallet_payload(s, await lock_user(s, user_id))

class GameInput(BaseModel):
    key: str = Field(min_length=2, max_length=32, pattern=r'^[a-z][a-z0-9-]+$')
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(default='', max_length=2000)
    engine: Literal['matching', 'slide_puzzle', 'space_war', 'roulette']
    is_active: bool = True
    cooldown_seconds: int = Field(ge=0, le=31536000)
    expiry_days: int = Field(ge=1, le=3650)
    max_duration_seconds: int = Field(ge=10, le=600)
    max_points: int = Field(ge=0, le=10000)
    points_per_unit: int = Field(ge=1, le=1000)

@router.get('/admin/games')
async def admin_games(admin: User = Depends(current_admin)):
    async with read_session() as s: return {'games': await games.catalog(s, admin=True)}

@router.put('/admin/games/{key}')
async def save_game(key: str, body: GameInput, admin: User = Depends(current_admin)):
    if key != body.key or key in ('puzzle', 'tetris', 'memory'): raise HTTPException(422, 'Kode game tidak dapat digunakan')
    if body.engine == 'roulette' and key != 'roulette': raise HTTPException(422, 'Gunakan kode roulette untuk game ini')
    async with session_scope() as s:
        rule = await s.get(m.GameRule, key, with_for_update=True)
        if body.engine == 'roulette':
            reward_max = await s.scalar(select(func.coalesce(func.max(m.RouletteReward.value), 0)).where(m.RouletteReward.type == 'points', m.RouletteReward.is_active.is_(True)))
            if reward_max > body.max_points: raise HTTPException(422, 'Batas poin lebih rendah dari hadiah Roulette aktif. Sesuaikan hadiahnya terlebih dahulu.')
        game = await s.scalar(select(m.Game).where(m.Game.key == key).with_for_update())
        if not game: game = m.Game(key=key, name=body.name); s.add(game); await s.flush()
        if rule and rule.engine != body.engine: raise HTTPException(409, 'Jenis permainan yang sudah dibuat tidak dapat diubah')
        if not rule: rule = m.GameRule(game_key=key, engine=body.engine); s.add(rule)
        for field in ('name', 'description', 'is_active', 'max_points'): setattr(game, field, getattr(body, field))
        for field in ('cooldown_seconds', 'expiry_days', 'max_duration_seconds', 'max_points', 'points_per_unit'): setattr(rule, field, getattr(body, field))
        await s.flush()
        return {'ok': True}

class LevelInput(BaseModel):
    rows: int = Field(ge=2, le=6)
    columns: int = Field(ge=2, le=6)
    image_url: str = Field(min_length=1, max_length=2000)
    is_active: bool = True

@router.get('/admin/games/puzzle/levels')
async def admin_levels(admin: User = Depends(current_admin)):
    async with read_session() as s:
        return {'levels': [row_dict(row) for row in (await s.scalars(select(m.PuzzleLevel).order_by(m.PuzzleLevel.level))).all()]}

@router.put('/admin/games/puzzle/levels/{level}')
async def save_level(level: int, body: LevelInput, admin: User = Depends(current_admin)):
    if not 1 <= level <= 20: raise HTTPException(422, 'Level harus 1 sampai 20')
    if not (body.image_url.startswith(('/uploads/', '/api/uploads-files/', '/logo-meow', 'https://'))): raise HTTPException(422, 'Gunakan gambar unggahan atau URL HTTPS')
    async with session_scope() as s:
        row = await s.get(m.PuzzleLevel, level)
        if not row: row = m.PuzzleLevel(level=level); s.add(row)
        for field, value in body.model_dump().items(): setattr(row, field, value)
        await s.flush()
        return row_dict(row)

class EventInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    start_at: datetime
    end_at: datetime
    percent: Decimal = Field(gt=0, le=100, decimal_places=4)
    expiry_days: int = Field(ge=1, le=3650)
    is_active: bool = True
    @model_validator(mode='after')
    def dates(self):
        if not self.start_at.tzinfo or not self.end_at.tzinfo or self.end_at <= self.start_at: raise ValueError('Periode event tidak valid atau tanpa zona waktu')
        return self

@router.get('/cashback-events')
async def live_cashback():
    async with read_session() as s:
        events = (await s.scalars(select(m.CashbackEvent).where(m.CashbackEvent.is_active.is_(True), m.CashbackEvent.start_at <= utcnow(), m.CashbackEvent.end_at > utcnow()).order_by(m.CashbackEvent.percent.desc()))).all()
        return {'events': [row_dict(row) for row in events], 'credit_on': 'completed'}

@router.get('/admin/cashback-events')
async def events(admin: User = Depends(current_admin)):
    async with read_session() as s:
        return {'events': [row_dict(row) for row in (await s.scalars(select(m.CashbackEvent).order_by(m.CashbackEvent.start_at.desc()))).all()]}

@router.post('/admin/cashback-events')
async def create_event(body: EventInput, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        row = m.CashbackEvent(**body.model_dump()); s.add(row); await s.flush(); return row_dict(row)

@router.put('/admin/cashback-events/{event_id}')
async def update_event(event_id: str, body: EventInput, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        row = await s.get(m.CashbackEvent, event_id, with_for_update=True)
        if not row: raise HTTPException(404, 'Event tidak ditemukan')
        for field, value in body.model_dump().items(): setattr(row, field, value)
        await s.flush(); return row_dict(row)
