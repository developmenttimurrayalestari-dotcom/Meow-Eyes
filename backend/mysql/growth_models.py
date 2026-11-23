"""Normalized customer growth records; imported by mysql.models after core models."""
from datetime import datetime
from typing import Any
from sqlalchemy import String, Integer, JSON, ForeignKey, ForeignKeyConstraint, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, ID, TOKEN, UTCDateTime
from .models import CreatedMixin, new_id


class EmailVerification(CreatedMixin, Base):
    __tablename__ = 'email_verifications'
    __table_args__ = (Index('ix_email_verifications_user_date', 'user_id', 'created_at'),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    token_hash: Mapped[str] = mapped_column(TOKEN, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Referral(CreatedMixin, Base):
    __tablename__ = 'customer_referrals'
    __table_args__ = (CheckConstraint('referee_id <> referrer_id', name='not_self'),
                     Index('ix_referrals_referrer', 'referrer_id', 'created_at'))
    referee_id: Mapped[str] = mapped_column(ID, ForeignKey('users.user_id', ondelete='RESTRICT'), primary_key=True)
    referrer_id: Mapped[str] = mapped_column(ID, ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    rule_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    rewarded_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class GrowthReward(CreatedMixin, Base):
    __tablename__ = 'customer_growth_rewards'
    __table_args__ = (CheckConstraint("status IN ('pending','granted')", name='status'),
                     Index('ix_growth_rewards_pending', 'status', 'user_id'))
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    event_key: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default='pending', nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class VoucherGrant(CreatedMixin, Base):
    __tablename__ = 'customer_voucher_grants'
    __table_args__ = (UniqueConstraint('user_id', 'voucher_id'),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    voucher_id: Mapped[str] = mapped_column(ID, ForeignKey('vouchers.id', ondelete='RESTRICT'), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)


class DailyCheckin(CreatedMixin, Base):
    __tablename__ = 'daily_checkins'
    __table_args__ = (CheckConstraint('streak > 0 AND points >= 0', name='amounts'),)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey('users.user_id', ondelete='RESTRICT'), primary_key=True)
    day: Mapped[str] = mapped_column(String(10), primary_key=True)
    streak: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)


class CartAddon(Base):
    __tablename__ = 'cart_item_addons'
    __table_args__ = (ForeignKeyConstraint(['product_id', 'variant_id'],
        ['product_variants.product_id', 'product_variants.id'], ondelete='RESTRICT'),)
    cart_item_id: Mapped[str] = mapped_column(ID, ForeignKey('cart_items.id', ondelete='CASCADE'), primary_key=True)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey('products.id', ondelete='RESTRICT'), primary_key=True)
    variant_id: Mapped[str] = mapped_column(ID, nullable=False)


class AddonFlashReservation(CreatedMixin, Base):
    __tablename__ = 'addon_flash_reservations'
    __table_args__ = (
        UniqueConstraint('component_id', 'flash_sale_item_id'),
        ForeignKeyConstraint(['component_id', 'order_id', 'product_id'],
            ['order_item_components.id', 'order_item_components.order_id', 'order_item_components.product_id'], ondelete='RESTRICT'),
        ForeignKeyConstraint(['flash_sale_item_id', 'product_id'], ['flash_sale_items.id', 'flash_sale_items.product_id'], ondelete='RESTRICT'),
        CheckConstraint("status IN ('active','confirmed','expired','cancelled')", name='status'),
        CheckConstraint('quantity > 0', name='quantity'))
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    component_id: Mapped[str] = mapped_column(ID, nullable=False)
    order_id: Mapped[str] = mapped_column(ID, nullable=False)
    product_id: Mapped[str] = mapped_column(ID, nullable=False)
    flash_sale_item_id: Mapped[str] = mapped_column(ID, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default='active', nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
