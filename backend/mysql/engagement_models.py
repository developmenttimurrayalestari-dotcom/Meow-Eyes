"""Immutable point valuations, verified game sessions, cashback and replacement RMA."""
from datetime import datetime
from decimal import Decimal
import uuid
from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, ID, OPAQUE, UTCDateTime, utcnow

def identity(): return uuid.uuid4().hex

class PointSettings(Base):
    __tablename__ = 'point_settings'
    __table_args__ = (CheckConstraint("id = 'global' AND rate > 0 AND version > 0", name='positive'), CheckConstraint("cashback_valuation = 'locked'", name='valuation'))
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=100)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cashback_valuation: Mapped[str] = mapped_column(String(16), nullable=False, default='locked')
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)

class PointRateVersion(Base):
    __tablename__ = 'point_rate_versions'
    __table_args__ = (CheckConstraint("rate > 0 AND version > 0 AND cashback_valuation = 'locked'", name='positive'),)
    version: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    cashback_valuation: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(ID, ForeignKey('users.user_id', ondelete='RESTRICT'))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False)

class PointLot(Base):
    __tablename__ = 'point_lots'
    __table_args__ = (CheckConstraint('earned > 0 AND remaining >= 0 AND remaining <= earned AND rate_snapshot > 0', name='amounts'), CheckConstraint("valuation = 'locked'", name='valuation'), Index('ix_point_lots_wallet', 'user_id', 'expires_at', 'created_at'))
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=identity)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    award_key: Mapped[str] = mapped_column(OPAQUE, unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    earned: Mapped[int] = mapped_column(BigInteger, nullable=False)
    remaining: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    rate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    valuation: Mapped[str] = mapped_column(String(16), nullable=False, default='locked')
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False)

class PointHistory(Base):
    __tablename__ = 'point_history'
    __table_args__ = (CheckConstraint('balance_after >= 0 AND rate_snapshot > 0', name='amounts'), Index('ix_point_history_customer', 'user_id', 'created_at', 'id'))
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=identity)
    event_key: Mapped[str] = mapped_column(OPAQUE, unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    lot_id: Mapped[str | None] = mapped_column(ID, ForeignKey('point_lots.id', ondelete='RESTRICT'))
    order_id: Mapped[str | None] = mapped_column(ID, ForeignKey('orders.id', ondelete='RESTRICT'))
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    delta: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    rate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    value_snapshot: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    note: Mapped[str] = mapped_column(Text, nullable=False, default='')
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False)

class PointRedemption(Base):
    __tablename__ = 'point_redemptions'
    __table_args__ = (UniqueConstraint('order_id', 'lot_id'), CheckConstraint("points > 0 AND rate_snapshot > 0 AND status IN ('reserved','consumed','released')", name='valid'))
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=identity)
    order_id: Mapped[str] = mapped_column(ID, ForeignKey('orders.id', ondelete='RESTRICT'), nullable=False)
    lot_id: Mapped[str] = mapped_column(ID, ForeignKey('point_lots.id', ondelete='RESTRICT'), nullable=False)
    points: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    rate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    value_snapshot: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default='reserved')

class GameRule(Base):
    __tablename__ = 'game_rules'
    __table_args__ = (CheckConstraint('cooldown_seconds >= 0 AND expiry_days > 0 AND max_duration_seconds >= 10 AND max_duration_seconds <= 600 AND max_points >= 0 AND points_per_unit > 0', name='bounds'), CheckConstraint("engine IN ('matching','slide_puzzle','space_war','roulette')", name='engine'))
    game_key: Mapped[str] = mapped_column(String(32), ForeignKey('games.key', ondelete='RESTRICT'), primary_key=True)
    engine: Mapped[str] = mapped_column(String(32), nullable=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=86400)
    expiry_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    max_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=180)
    max_points: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    points_per_unit: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

class PuzzleLevel(Base):
    __tablename__ = 'puzzle_levels'
    __table_args__ = (CheckConstraint('level >= 1 AND level <= 20 AND rows >= 2 AND rows <= 6 AND columns >= 2 AND columns <= 6', name='bounds'),)
    level: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    rows: Mapped[int] = mapped_column(Integer, nullable=False)
    columns: Mapped[int] = mapped_column(Integer, nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class GameSession(Base):
    __tablename__ = 'game_sessions'
    __table_args__ = (CheckConstraint("status IN ('active','completed','expired') AND seed >= 0 AND points_awarded >= 0 AND score >= 0", name='state'), Index('ix_game_session_cooldown', 'user_id', 'game_key', 'started_at'))
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=identity)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    game_key: Mapped[str] = mapped_column(String(32), ForeignKey('games.key', ondelete='RESTRICT'), nullable=False)
    active_slot: Mapped[str | None] = mapped_column(OPAQUE, unique=True)
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    transcript: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default='active')
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_awarded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

class CashbackEvent(Base):
    __tablename__ = 'cashback_events'
    __table_args__ = (CheckConstraint('percent > 0 AND percent <= 100 AND expiry_days > 0 AND end_at > start_at', name='bounds'),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=identity)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    start_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    end_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    percent: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    expiry_days: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class CashbackAward(Base):
    __tablename__ = 'cashback_awards'
    __table_args__ = (CheckConstraint('points >= 0 AND amount >= 0 AND rate_snapshot > 0', name='amounts'),)
    order_id: Mapped[str] = mapped_column(ID, ForeignKey('orders.id', ondelete='RESTRICT'), primary_key=True)
    event_id: Mapped[str] = mapped_column(ID, ForeignKey('cashback_events.id', ondelete='RESTRICT'), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    points: Mapped[int] = mapped_column(BigInteger, nullable=False)
    credited_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

class ReturnCase(Base):
    __tablename__ = 'return_cases'
    __table_args__ = (ForeignKeyConstraint(['order_id', 'user_id'], ['orders.id', 'orders.user_id'], ondelete='RESTRICT'), CheckConstraint("status IN ('draft','submitted','approved','return_sent','received','replacement_shipped','completed','rejected','cancelled')", name='status'), Index('ix_return_cases_order', 'order_id', 'created_at'))
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=identity)
    reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    order_id: Mapped[str] = mapped_column(ID, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='draft')
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[dict | None] = mapped_column(JSON)
    return_courier: Mapped[str | None] = mapped_column(String(128))
    return_tracking: Mapped[str | None] = mapped_column(String(128))
    replacement_courier: Mapped[str | None] = mapped_column(String(128))
    replacement_tracking: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False)

class ReturnCaseItem(Base):
    __tablename__ = 'return_case_items'
    __table_args__ = (CheckConstraint('quantity > 0', name='quantity'), ForeignKeyConstraint(['order_item_id', 'order_id'], ['order_items.id', 'order_items.order_id'], ondelete='RESTRICT'), UniqueConstraint('case_id', 'order_item_id'))
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=identity)
    case_id: Mapped[str] = mapped_column(ID, ForeignKey('return_cases.id', ondelete='RESTRICT'), nullable=False)
    order_id: Mapped[str] = mapped_column(ID, nullable=False)
    order_item_id: Mapped[str] = mapped_column(ID, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

class ReturnEvidence(Base):
    __tablename__ = 'return_evidence'
    __table_args__ = (CheckConstraint("byte_size > 0 AND byte_size <= 104857600 AND mime_type IN ('video/mp4','video/webm')", name='file'),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=identity)
    case_id: Mapped[str] = mapped_column(ID, ForeignKey('return_cases.id', ondelete='RESTRICT'), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(32), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False)

class ReturnTimeline(Base):
    __tablename__ = 'return_timeline'
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=identity)
    case_id: Mapped[str] = mapped_column(ID, ForeignKey('return_cases.id', ondelete='RESTRICT'), nullable=False)
    actor_id: Mapped[str] = mapped_column(ID, ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default='')
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False)
