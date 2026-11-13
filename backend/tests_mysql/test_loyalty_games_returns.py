"""Transactional wallet, replay and replacement lifecycle regressions."""
import asyncio
from datetime import timedelta
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select, func
import pytest
from database import session_scope, read_session
from mysql import models as m, points, games, returns
from mysql.base import utcnow
from mysql.commerce import lock_user, create_checkout, confirm_mock_payment, admin_transition_order
from mysql.game_engine import shuffled, SpaceWar, replay_space, puzzle_board, replay_puzzle
from tests_mysql.sql_helpers import isolated_database
from tests_mysql.commerce_scenarios import seed_commerce_fixture

@pytest.fixture(autouse=True)
def test_mode(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'test'); monkeypatch.setenv('ENABLE_MOCK_PAYMENTS', '1')
    monkeypatch.setenv('PAYMENT_PROVIDER', 'mock'); monkeypatch.setenv('SHIPPING_PROVIDER', 'mock')

async def game_fixture(s, key='matching', engine='matching', cooldown=86400):
    s.add(m.Game(key=key, name=key, max_points=50, is_active=True)); await s.flush()
    s.add(m.GameRule(game_key=key, engine=engine, cooldown_seconds=cooldown, expiry_days=3, max_duration_seconds=180, max_points=50, points_per_unit=5)); await s.flush()

def test_old_and_new_point_rates_are_frozen_and_fifo_value_is_correct():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            async with session_scope() as s:
                user = await lock_user(s, d['alice'])
                await points.credit(s, user, 10, source='earn_game', key='first', expiry_days=30)
                config = await points.settings(s); config.rate = Decimal('250'); config.version = 2; await s.flush()
                await points.credit(s, user, 4, source='cashback', key='second', expiry_days=60)
                used, value, plan = await points.quote(s, user, 114, Decimal('100000'))
                assert used == 114 and value == Decimal('12000')
                rates = {r['lot_id']: Decimal(r['rate']) for r in plan}
                assert sorted(rates.values()) == [Decimal(100), Decimal(100), Decimal(250)]
                config.rate = Decimal('999'); await s.flush()
                assert (await points.wallet_payload(s, user))['value'] == 12000
                assert (await points.credit(s, user, 999, source='cashback', key='second')).earned == 4
                assert user.points_balance == 114
    asyncio.run(run())

def test_expiry_removes_cached_balance_once_and_redemption_restores_original_lot():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            async with session_scope() as s:
                user = await lock_user(s, d['alice']); lot = await points.credit(s, user, 20, source='earn_game', key='expired', expiry_days=1)
                lot.expires_at = utcnow() - timedelta(seconds=1); await s.flush()
                await points.expire(s, user); await points.expire(s, user)
                assert user.points_balance == 100
                assert await s.scalar(select(func.count()).select_from(m.PointHistory).where(m.PointHistory.source == 'expire_points')) == 1
            result = await create_checkout(d['alice'], d['req'].model_copy(update={'use_points': 2}))
            from mysql.commerce import expire_order
            await expire_order(result['order']['id'], 'cancelled'); await expire_order(result['order']['id'], 'cancelled')
            async with session_scope() as s:
                user = await lock_user(s, d['alice']); assert (await points.wallet_payload(s, user))['balance'] == 100
                rows = (await s.scalars(select(m.PointRedemption))).all(); assert len(rows) == 1 and rows[0].status == 'released' and rows[0].rate_snapshot == 100
    asyncio.run(run())

def test_game_round_idempotency_cooldown_rate_snapshot_and_forged_steps():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            async with session_scope() as s:
                await game_fixture(s)
                user = await lock_user(s, d['alice']); round_ = await games.start(s, user, 'matching')
                assert (await games.start(s, user, 'matching'))['id'] == round_['id']
                stored = await s.get(m.GameSession, round_['id']); stored.started_at -= timedelta(seconds=10)
                config = await points.settings(s); config.rate = Decimal(300); await s.flush()
                deck = shuffled(round_['seed'], list(range(8)) * 2)
                moves = [i for face in range(8) for i, value in enumerate(deck) if value == face]
                with pytest.raises(HTTPException): await games.finish(s, user, round_['id'], {'moves': [0, 0]})
                result = await games.finish(s, user, round_['id'], {'moves': moves})
                assert result['points_awarded'] == 40
                assert await games.finish(s, user, round_['id'], {'moves': []}) == result
                lot = await s.scalar(select(m.PointLot).where(m.PointLot.source == 'earn_game'))
                assert lot.rate_snapshot == 100 and user.points_balance == 140
                with pytest.raises(HTTPException) as error: await games.start(s, user, 'matching')
                assert error.value.status_code == 429
                with pytest.raises(HTTPException) as error: await games.finish(s, await lock_user(s, d['bob']), round_['id'], {'moves': moves})
                assert error.value.status_code == 404
    asyncio.run(run())

def test_space_replay_rejects_client_score_and_enforces_round_end():
    config = {'max_duration_seconds': 180, 'max_points': 50, 'points_per_unit': 2}
    engine = SpaceWar(123456, config)
    for _ in range(5400):
        if engine.done: break
        engine.step(0)
    result = replay_space(123456, config, {'ticks': engine.tick, 'commands': [], 'score': 999999})
    assert result[:2] == (engine.kills, min(50, engine.kills * 2)) and result[1] <= 50
    with pytest.raises(HTTPException): replay_space(123456, config, {'ticks': 1, 'commands': []})
    with pytest.raises(HTTPException): replay_space(1, config, {'ticks': 9000, 'commands': []})
    with pytest.raises(HTTPException): replay_space(1, config, {'ticks': engine.tick, 'commands': [{'t': 0, 'd': 5}]})
    assert engine.lives == 0 or engine.tick == 5400 or engine.kills * 2 >= 50

def test_puzzles_are_reachable_and_illegal_moves_are_rejected():
    for size in range(2, 7):
        board = puzzle_board(458, size, size)
        assert sorted(board) == list(range(size * size)) and board != list(range(1, size * size)) + [0]
        empty = board.index(0)
        with pytest.raises(HTTPException): replay_puzzle(458, {'rows': size, 'columns': size, 'level': 1}, [empty])

def test_cashback_order_snapshot_only_credits_on_completion_once():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            async with session_scope() as s:
                s.add(m.CashbackEvent(id='event', name='Cashback', start_at=utcnow() - timedelta(days=1), end_at=utcnow() + timedelta(days=1), percent=10, expiry_days=14, is_active=True)); await s.flush()
            result = await create_checkout(d['alice'], d['req']); order_id = result['order']['id']
            async with session_scope() as s:
                award = await s.get(m.CashbackAward, order_id); expected = award.points
                assert expected > 0 and award.credited_at is None
                (await s.get(m.CashbackEvent, 'event')).percent = 99
                config = await points.settings(s); config.rate = Decimal(999); await s.flush()
            await confirm_mock_payment(result['order']['order_number'], d['alice'])
            await admin_transition_order(order_id, 'completed', '', d['admin']); await admin_transition_order(order_id, 'completed', '', d['admin'])
            async with read_session() as s:
                lots = (await s.scalars(select(m.PointLot).where(m.PointLot.source == 'cashback'))).all()
                assert len(lots) == 1 and lots[0].earned == expected and lots[0].rate_snapshot == 100 and lots[0].valuation == 'locked'
    asyncio.run(run())

def test_replacement_requires_video_quantity_ownership_and_valid_state_and_debits_components_once():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            result = await create_checkout(d['alice'], d['req']); order_id = result['order']['id']
            await confirm_mock_payment(result['order']['order_number'], d['alice']); await admin_transition_order(order_id, 'completed', '', d['admin'])
            async with session_scope() as s:
                user = await lock_user(s, d['alice']); admin = await s.get(m.User, d['admin'])
                item = await s.scalar(select(m.OrderItem).where(m.OrderItem.order_id == order_id))
                case = await returns.create(s, user, order_id, [{'order_item_id': item.id, 'quantity': 1}], 'Frame rusak saat unboxing')
                row = await s.get(m.ReturnCase, case['id'])
                with pytest.raises(HTTPException): await returns.transition(s, row, user, 'submitted')
                with pytest.raises(HTTPException): await returns.create(s, user, order_id, [{'order_item_id': item.id, 'quantity': 2}], 'Jumlah melebihi pesanan')
                with pytest.raises(HTTPException): await returns.create(s, await lock_user(s, d['bob']), order_id, [{'order_item_id': item.id, 'quantity': 1}], 'Bukan pemilik pesanan')
                s.add(m.ReturnEvidence(case_id=row.id, storage_path='private.mp4', sha256='a'*64, mime_type='video/mp4', byte_size=100)); await s.flush()
                await returns.transition(s, row, user, 'submitted')
                with pytest.raises(HTTPException): await returns.transition(s, row, admin, 'approved', admin=True)
                s.add(m.Setting(key='rma_policy', value={**returns.DEFAULT_POLICY, 'recipient': 'Toko', 'phone': '0812', 'address': 'Alamat retur toko'}, is_public=False)); await s.flush()
                await returns.transition(s, row, admin, 'approved', admin=True)
                assert row.instructions['reference'] == row.reference
                with pytest.raises(HTTPException): await returns.transition(s, row, admin, 'replacement_shipped', admin=True, courier='JNE', tracking='real')
                await returns.transition(s, row, user, 'return_sent', courier='JNE', tracking='RETUR-001')
                await returns.transition(s, row, admin, 'received', admin=True)
                before = (await s.get(m.ProductVariant, d['vf'])).stock
                await returns.transition(s, row, admin, 'replacement_shipped', admin=True, courier='JNE', tracking='REPLACE-001')
                await returns.transition(s, row, admin, 'replacement_shipped', admin=True, courier='JNE', tracking='REPLACE-001')
                assert (await s.get(m.ProductVariant, d['vf'])).stock == before - 1
                assert await s.scalar(select(func.count()).select_from(m.StockMovement).where(m.StockMovement.type == 'rma_replacement')) == 2
                await returns.transition(s, row, admin, 'completed', admin=True)
    asyncio.run(run())
