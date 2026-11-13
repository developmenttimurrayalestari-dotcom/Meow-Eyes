"""Lot-based point wallet. Call mutations only while holding the user's lock."""
from datetime import timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
import uuid
from sqlalchemy import select, func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from fastapi import HTTPException
from . import models as m
from .base import utcnow

CENT = Decimal('.01')
LEGACY_RATE = Decimal('100.0000')

def amount(value): return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)

async def settings(s, *, lock=False):
    query = select(m.PointSettings).where(m.PointSettings.id == 'global')
    row = await s.scalar(query.with_for_update() if lock else query)
    if row is None:
        values = dict(id='global', rate=LEGACY_RATE, version=1, cashback_valuation='locked', updated_at=utcnow())
        if s.get_bind().dialect.name == 'mysql':
            statement = mysql_insert(m.PointSettings).values(**values).on_duplicate_key_update(id='global')
        else:
            statement = sqlite_insert(m.PointSettings).values(**values).on_conflict_do_nothing(index_elements=['id'])
        await s.execute(statement)
        row = await s.scalar(query.with_for_update() if lock else query)
    return row

async def record(s, user, *, delta, source, rate, version, event_key, lot=None, order_id=None, note='', old_log=True):
    s.add(m.PointHistory(id=uuid.uuid4().hex, event_key=event_key, user_id=user.user_id, lot_id=lot.id if lot else None,
        order_id=order_id, source=source, delta=delta, balance_after=user.points_balance, rate_snapshot=rate,
        rate_version=version, value_snapshot=amount(Decimal(delta) * rate), expires_at=lot.expires_at if lot else None, note=note))
    if old_log:
        s.add(m.PointLog(id=uuid.uuid4().hex, user_id=user.user_id, delta=delta, balance_after=user.points_balance,
                         type=source, order_id=order_id, note=note))

async def ensure_wallet(s, user):
    if user.points_balance <= 0: return
    exists = await s.scalar(select(m.PointLot.id).where(m.PointLot.user_id == user.user_id).limit(1))
    if exists: return
    # Imported balances were earned when the released app used Rp100/point.
    lot = m.PointLot(id=uuid.uuid4().hex, user_id=user.user_id, award_key='legacy:' + user.user_id,
        source='legacy', earned=user.points_balance, remaining=user.points_balance, rate_snapshot=LEGACY_RATE,
        rate_version=1, valuation='locked', expires_at=None)
    s.add(lot); await s.flush()
    await record(s, user, delta=user.points_balance, source='legacy', rate=LEGACY_RATE, version=1,
        event_key='legacy:' + user.user_id, lot=lot, note='Saldo awal sebelum dompet per perolehan', old_log=False)

async def expire(s, user):
    await ensure_wallet(s, user)
    lots = (await s.scalars(select(m.PointLot).where(m.PointLot.user_id == user.user_id, m.PointLot.remaining > 0,
        m.PointLot.expires_at <= utcnow()).order_by(m.PointLot.id).with_for_update())).all()
    for lot in lots:
        points, lot.remaining = lot.remaining, 0
        user.points_balance -= points
        if user.points_balance < 0: raise HTTPException(409, 'Saldo poin perlu direkonsiliasi')
        await record(s, user, delta=-points, source='expire_points', rate=lot.rate_snapshot, version=lot.rate_version,
            event_key='expire:' + uuid.uuid4().hex, lot=lot, note='Poin melewati tanggal kedaluwarsa')
    await s.flush()

async def credit(s, user, points, *, source, key, expiry_days=None, rate=None, version=None, valuation='locked', order_id=None, note=''):
    if points <= 0: return None
    await expire(s, user)
    existing = await s.scalar(select(m.PointLot).where(m.PointLot.award_key == key))
    if existing: return existing
    config = await settings(s)
    rate = Decimal(rate if rate is not None else config.rate)
    lot = m.PointLot(id=uuid.uuid4().hex, user_id=user.user_id, award_key=key, source=source, earned=points,
        remaining=points, rate_snapshot=rate, rate_version=version or config.version, valuation=valuation,
        expires_at=utcnow() + timedelta(days=expiry_days) if expiry_days else None)
    s.add(lot); await s.flush()
    user.points_balance += points
    await record(s, user, delta=points, source=source, rate=rate, version=lot.rate_version,
        event_key='credit:' + key, lot=lot, order_id=order_id, note=note)
    await s.flush()
    return lot

async def quote(s, user, requested, limit):
    await expire(s, user)
    config = await settings(s)
    lots = (await s.scalars(select(m.PointLot).where(m.PointLot.user_id == user.user_id, m.PointLot.remaining > 0)
        .order_by(m.PointLot.expires_at.is_(None), m.PointLot.expires_at, m.PointLot.created_at, m.PointLot.id).with_for_update())).all()
    plan, remaining, capacity = [], requested, max(Decimal(0), limit)
    for lot in lots:
        if not remaining: break
        rate = lot.rate_snapshot
        count = min(lot.remaining, remaining, int(capacity // rate))
        if count <= 0: continue
        value = amount(Decimal(count) * rate)
        if value > capacity: continue
        plan.append({'lot_id': lot.id, 'points': count, 'rate': str(rate), 'version': lot.rate_version, 'value': str(value)})
        remaining -= count; capacity -= value
    return sum(row['points'] for row in plan), sum((Decimal(row['value']) for row in plan), Decimal('0.00')), plan

async def reserve(s, user, order, plan):
    for row in plan:
        lot = await s.get(m.PointLot, row['lot_id'])
        if lot.user_id != user.user_id or lot.remaining < row['points'] or (lot.expires_at and lot.expires_at <= utcnow()):
            raise HTTPException(409, 'Poin berubah atau kedaluwarsa. Hitung ulang pesanan.')
        lot.remaining -= row['points']; user.points_balance -= row['points']
        s.add(m.PointRedemption(id=uuid.uuid4().hex, order_id=order.id, lot_id=lot.id, points=row['points'],
            rate_snapshot=Decimal(row['rate']), rate_version=row['version'], value_snapshot=Decimal(row['value']), status='reserved'))
        await record(s, user, delta=-row['points'], source='redeem_checkout', rate=Decimal(row['rate']), version=row['version'],
            event_key=f"redeem:{order.id}:{lot.id}", lot=lot, order_id=order.id, note=order.order_number)
    await s.flush()

async def release(s, user, order, status):
    rows = (await s.scalars(select(m.PointRedemption).where(m.PointRedemption.order_id == order.id).with_for_update())).all()
    if not rows:
        if order.points_used:
            rate = (order.points_discount / order.points_used).quantize(Decimal('.0001')) or LEGACY_RATE
            await credit(s, user, order.points_used, source='refund_point', key='legacy-refund:' + order.id,
                         rate=rate, version=1, order_id=order.id, note=order.order_number + ' (' + status + ')')
        return
    for row in rows:
        if row.status != 'reserved': continue
        row.status = 'released'
        lot = await s.get(m.PointLot, row.lot_id)
        lot.remaining += row.points; user.points_balance += row.points
        await record(s, user, delta=row.points, source='refund_point', rate=row.rate_snapshot, version=row.rate_version,
            event_key=f'refund:{order.id}:{lot.id}', lot=lot, order_id=order.id, note=order.order_number + ' (' + status + ')')
    await expire(s, user)

async def snapshot_cashback(s, order):
    if await s.get(m.CashbackAward, order.id): return
    # Highest percentage wins if events overlap; cashback never stacks events.
    event = await s.scalar(select(m.CashbackEvent).where(m.CashbackEvent.is_active.is_(True), m.CashbackEvent.start_at <= order.created_at,
        m.CashbackEvent.end_at > order.created_at).order_by(m.CashbackEvent.percent.desc(), m.CashbackEvent.id).limit(1))
    if not event: return
    config = await settings(s)
    value = amount(order.total * event.percent / 100)
    points = int((value / config.rate).to_integral_value(rounding=ROUND_DOWN))
    s.add(m.CashbackAward(order_id=order.id, event_id=event.id, amount=value, rate_snapshot=config.rate, points=points,
        snapshot={'name': event.name, 'percent': str(event.percent), 'expiry_days': event.expiry_days, 'rate_version': config.version,
                  'valuation': config.cashback_valuation, 'base': str(order.total), 'credit_on': 'completed'}))
    await s.flush()

async def complete_order(s, user, order):
    rows = (await s.scalars(select(m.PointRedemption).where(m.PointRedemption.order_id == order.id, m.PointRedemption.status == 'reserved'))).all()
    for row in rows: row.status = 'consumed'
    award = await s.get(m.CashbackAward, order.id)
    if award and not award.credited_at and order.payment_status == 'paid' and order.status == 'completed':
        await credit(s, user, award.points, source='cashback', key='cashback:' + order.id, expiry_days=award.snapshot['expiry_days'],
            rate=award.rate_snapshot, version=award.snapshot['rate_version'], valuation=award.snapshot['valuation'], order_id=order.id,
            note='Cashback ' + award.snapshot['name'])
        award.credited_at = utcnow()
        await s.flush()

async def wallet_payload(s, user):
    await expire(s, user)
    config = await settings(s)
    lots = (await s.scalars(select(m.PointLot).where(m.PointLot.user_id == user.user_id, m.PointLot.remaining > 0).order_by(m.PointLot.expires_at.is_(None), m.PointLot.expires_at))).all()
    history = (await s.scalars(select(m.PointHistory).where(m.PointHistory.user_id == user.user_id).order_by(m.PointHistory.created_at.desc(), m.PointHistory.id.desc()).limit(100))).all()
    return {'balance': user.points_balance, 'value': float(sum((lot.remaining * (lot.rate_snapshot) for lot in lots), Decimal(0))),
        'current_rate': float(config.rate), 'rate_version': config.version, 'lots': [{'id': lot.id, 'source': lot.source, 'remaining': lot.remaining,
        'rate_snapshot': float(lot.rate_snapshot), 'effective_rate': float(lot.rate_snapshot), 'valuation': lot.valuation,
        'expires_at': lot.expires_at.isoformat() if lot.expires_at else None} for lot in lots],
        'logs': [{'id': row.id, 'delta': row.delta, 'type': row.source, 'note': row.note, 'balance_after': row.balance_after,
                  'rate_snapshot': float(row.rate_snapshot), 'value_snapshot': float(row.value_snapshot), 'expires_at': row.expires_at.isoformat() if row.expires_at else None,
                  'created_at': row.created_at.isoformat(), 'order_id': row.order_id} for row in history]}
