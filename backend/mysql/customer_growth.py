"""Customer benefits. Wallet changes use user locks and immutable award keys."""
from copy import deepcopy
from datetime import timedelta
import hashlib
import secrets
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, func, update
from starlette.concurrency import run_in_threadpool
from database import read_session, session_scope
from . import models as m
from .base import utcnow
from .commerce import lock_user
from . import points
import verification_mail


class RewardRule(BaseModel):
    kind: str = Field(default='none', pattern='^(none|points|voucher)$')
    points: int = Field(default=0, ge=0, le=1000000)
    voucher_id: str | None = Field(default=None, max_length=64)
    expiry_days: int = Field(default=30, ge=0, le=3650)  # 0: no expiration

    @model_validator(mode='after')
    def voucher_required(self):
        if self.kind == 'voucher' and not self.voucher_id:
            raise ValueError('Pilih voucher untuk reward referral')
        return self


class GrowthConfig(BaseModel):
    referral_enabled: bool = False
    referral_trigger: str = Field(default='first_order', pattern='^(registration|first_order)$')
    referrer: RewardRule = Field(default_factory=RewardRule)
    referee: RewardRule = Field(default_factory=RewardRule)
    checkin_enabled: bool = False
    daily_points: int = Field(default=1, ge=1, le=1000000)
    streak_points: list[int] = Field(default_factory=lambda: [1, 1, 1, 1, 1, 1, 5], min_length=7, max_length=7)
    use_streak: bool = False
    checkin_expiry_days: int = Field(default=30, ge=0, le=3650)  # 0: no expiration
    cod_enabled: bool = True

    @model_validator(mode='after')
    def valid_streak(self):
        if any(isinstance(n, bool) or n < 0 or n > 1000000 for n in self.streak_points):
            raise ValueError('Reward streak harus 0 sampai 1.000.000 poin')
        return self


async def config(s):
    row = await s.get(m.Setting, 'customer_growth')
    return GrowthConfig.model_validate(row.value if row else {}).model_dump()


def ensure_code(user):
    if not user.referral_code:
        user.referral_code = 'ME' + hashlib.sha256(user.user_id.encode()).hexdigest()[:24].upper()
    return user.referral_code


async def attach_referral(s, user, code):
    ensure_code(user)
    if not code: return
    cfg = await config(s)
    if not cfg['referral_enabled']:
        raise HTTPException(422, 'Program referral belum aktif')
    referrer = await s.scalar(select(m.User).where(m.User.referral_code == code.strip().upper(),
        m.User.role == 'customer', m.User.is_active.is_(True)))
    if not referrer or referrer.user_id == user.user_id:
        raise HTTPException(422, 'Kode referral tidak berlaku')
    s.add(m.Referral(referee_id=user.user_id, referrer_id=referrer.user_id, rule_snapshot=deepcopy(cfg)))
    await s.flush()
    await queue_referral(s, user, 'registration')


async def queue_referral(s, user, trigger, order=None):
    row = await s.get(m.Referral, user.user_id)
    if not row or row.rewarded_at or row.rule_snapshot['referral_trigger'] != trigger: return
    if trigger == 'first_order':
        if not order or order.status != 'completed' or order.payment_status != 'paid': return
        first = await s.scalar(select(m.Order.id).where(m.Order.user_id == user.user_id,
            m.Order.payment_status == 'paid').order_by(m.Order.created_at, m.Order.id).limit(1))
        if first != order.id: return
    for recipient, uid in (('referrer', row.referrer_id), ('referee', user.user_id)):
        rule = deepcopy(row.rule_snapshot[recipient])
        if rule['kind'] == 'none': continue
        rate = await points.settings(s)
        rule.update(rate=str(rate.rate), rate_version=rate.version)
        # Queue recipients separately; never acquire two customer wallet locks.
        s.add(m.GrowthReward(event_key=f'referral:{row.referee_id}:{recipient}', user_id=uid,
            snapshot={**rule, 'source': 'referral', 'order_id': order.id if order else None}))
    row.rewarded_at = utcnow()
    await s.flush()


async def deliver_rewards(user_id=None):
    async with read_session() as s:
        query = select(m.GrowthReward.id).join(m.User, m.User.user_id == m.GrowthReward.user_id).where(
            m.GrowthReward.status == 'pending', m.User.is_active.is_(True)).order_by(m.GrowthReward.created_at).limit(100)
        if user_id: query = query.where(m.GrowthReward.user_id == user_id)
        ids = (await s.scalars(query)).all()
    for rid in ids:
        async with session_scope() as s:
            reward = await s.get(m.GrowthReward, rid)
            user = await lock_user(s, reward.user_id, active=False)
            reward = await s.scalar(select(m.GrowthReward).where(m.GrowthReward.id == rid).with_for_update())
            if reward.status != 'pending' or not user.is_active: continue
            rule = reward.snapshot
            if rule['kind'] == 'points':
                await points.credit(s, user, rule['points'], source='referral', key=reward.event_key,
                    expiry_days=rule['expiry_days'], rate=rule['rate'], version=rule['rate_version'],
                    order_id=rule.get('order_id'), note='Reward referral member')
            elif rule['kind'] == 'voucher':
                exists = await s.scalar(select(m.VoucherGrant.id).where(m.VoucherGrant.user_id == user.user_id,
                    m.VoucherGrant.voucher_id == rule['voucher_id']))
                if not exists:
                    s.add(m.VoucherGrant(user_id=user.user_id, voucher_id=rule['voucher_id'], source='referral'))
            reward.status, reward.granted_at = 'granted', utcnow()


async def voucher_eligible(s, user, voucher, *, claim=False):
    if voucher.audience == 'new_member':
        if not user.email or not user.email_verified_at:
            raise HTTPException(403, 'Verifikasi email dahulu untuk voucher member baru')
        previous = await s.scalar(select(m.Order.id).where(m.Order.user_id == user.user_id,
            m.Order.status.notin_(('cancelled', 'expired'))).limit(1))
        if previous: raise HTTPException(409, 'Voucher member baru hanya untuk transaksi pertama')
    grant = await s.scalar(select(m.VoucherGrant).where(m.VoucherGrant.user_id == user.user_id,
        m.VoucherGrant.voucher_id == voucher.id))
    if voucher.audience == 'referral' and not grant:
        raise HTTPException(403, 'Voucher ini hanya untuk penerima reward referral')
    if claim and not grant:
        grant = m.VoucherGrant(user_id=user.user_id, voucher_id=voucher.id, source=voucher.audience)
        s.add(grant)
    if voucher.audience in ('new_member', 'referral'):
        used = await s.scalar(select(m.VoucherRedemption.id).where(m.VoucherRedemption.user_id == user.user_id,
            m.VoucherRedemption.voucher_id == voucher.id, m.VoucherRedemption.status.in_(('reserved', 'redeemed'))).limit(1))
        if used: raise HTTPException(409, 'Voucher ini sudah digunakan akun Anda')


async def request_verification(user_id, *, optional=False):
    if not verification_mail.ready():
        if optional: return False
        raise HTTPException(503, 'Email verifikasi belum dikonfigurasi. Hubungi toko.')
    async with session_scope() as s:
        user = await lock_user(s, user_id)
        if user.email_verified_at: return True
        if not user.email: raise HTTPException(422, 'Tambahkan alamat email terlebih dahulu')
        last = await s.scalar(select(m.EmailVerification).where(m.EmailVerification.user_id == user_id)
            .order_by(m.EmailVerification.created_at.desc()).limit(1))
        if last and last.created_at > utcnow() - timedelta(seconds=60):
            if optional: return False
            raise HTTPException(429, 'Tunggu 60 detik sebelum mengirim ulang verifikasi', headers={'Retry-After': '60'})
        token = secrets.token_urlsafe(32)
        email = user.email
        verification = m.EmailVerification(user_id=user_id, email=email,
            token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=utcnow() + timedelta(minutes=30))
        s.add(verification)
        await s.flush()
        verification_id = verification.id
    try:
        await run_in_threadpool(verification_mail.send_verification, email, token)
    except HTTPException:
        async with session_scope() as s:
            row = await s.get(m.EmailVerification, verification_id)
            row.used_at = utcnow()
        if optional: return False
        raise
    return True


async def verify_email(token):
    digest = hashlib.sha256(token.encode()).hexdigest()
    async with read_session() as s:
        uid = await s.scalar(select(m.EmailVerification.user_id).where(m.EmailVerification.token_hash == digest))
    if not uid: raise HTTPException(400, 'Tautan verifikasi tidak berlaku')
    async with session_scope() as s:
        user = await lock_user(s, uid)
        row = await s.scalar(select(m.EmailVerification).where(m.EmailVerification.token_hash == digest).with_for_update())
        if row.used_at or row.expires_at <= utcnow() or row.email != user.email:
            raise HTTPException(400, 'Tautan verifikasi sudah dipakai, kedaluwarsa, atau email telah berubah')
        row.used_at = utcnow()
        user.email_verified_at = user.email_verified_at or utcnow()
        await s.execute(update(m.EmailVerification).where(m.EmailVerification.user_id == uid,
            m.EmailVerification.used_at.is_(None)).values(used_at=utcnow()).execution_options(synchronize_session=False))
    return {'ok': True}


def local_day():
    return utcnow().astimezone(ZoneInfo('Asia/Jakarta')).date()


async def checkin(s, user):
    cfg = await config(s)
    if not cfg['checkin_enabled']: raise HTTPException(403, 'Daily check-in belum aktif')
    today = local_day()
    if await s.get(m.DailyCheckin, (user.user_id, today.isoformat())):
        raise HTTPException(409, 'Anda sudah check-in hari ini')
    previous = await s.get(m.DailyCheckin, (user.user_id, (today - timedelta(days=1)).isoformat()))
    streak = previous.streak + 1 if previous else 1
    count = cfg['streak_points'][(streak - 1) % 7] if cfg['use_streak'] else cfg['daily_points']
    row = m.DailyCheckin(user_id=user.user_id, day=today.isoformat(), streak=streak, points=count)
    s.add(row)
    await points.credit(s, user, count, source='daily_checkin', key=f'checkin:{user.user_id}:{today}',
        expiry_days=cfg['checkin_expiry_days'], note=f'Check-in hari ke-{streak}')
    await s.flush()
    return row
