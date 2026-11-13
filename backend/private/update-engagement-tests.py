from pathlib import Path
p=Path('tests_mysql/test_commerce_sql.py');t=p.read_text(encoding='utf-8')
a=t.index('def test_game_daily_limits_and_wallet_ledger_use_fresh_balance():');b=t.index('\ndef ',a+4)
t=t[:a]+'''def test_direct_game_score_submission_is_rejected():
    from routes_engagement import submit_game
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            with pytest.raises(HTTPException) as exc:
                await submit_game("matching", {"score": 999999}, d["user"])
            assert exc.value.status_code == 410
            async with read_session() as s:
                assert (await s.get(m.User, d["alice"])).points_balance == 100
    asyncio.run(run())

'''+t[b:]
a=t.index('def test_roulette_points_are_immediately_used_and_daily_limited():');b=t.find('\ndef ',a+4)
if b<0:b=len(t)
t=t[:a]+'''def test_roulette_points_are_used_with_configured_cooldown_and_expiry():
    from routes_engagement import spin_roulette
    from tests_mysql.test_loyalty_games_returns import game_fixture
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            async with session_scope() as s:
                await game_fixture(s, 'roulette', 'roulette', cooldown=0)
                (await s.get(m.RouletteReward, d["reward"])).is_active = False
                s.add(m.RouletteReward(id=d["prefix"] + "_points", label="Ten points", type="points", value=10, probability=1, is_active=True))
                await s.flush()
            assert (await spin_roulette(d["user"]))["spin"]["used"] is True
            async with session_scope() as s:
                (await s.get(m.GameRule, 'roulette')).cooldown_seconds = 10800
            with pytest.raises(HTTPException) as exc:
                await spin_roulette(d["user"])
            assert exc.value.status_code == 429
            async with read_session() as s:
                assert (await s.get(m.User, d["alice"])).points_balance == 110
                lot = await s.scalar(select(m.PointLot).where(m.PointLot.source == 'earn_roulette'))
                assert lot.rate_snapshot == 100 and lot.expires_at is not None
    asyncio.run(run())

'''+t[b:]
p.write_text(t,encoding='utf-8')
p=Path('sql/005_loyalty_games_returns.sql');p.write_text(p.read_text(encoding='utf-16'),encoding='utf-8')
