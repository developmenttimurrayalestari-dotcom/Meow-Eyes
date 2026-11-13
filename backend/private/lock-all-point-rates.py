from pathlib import Path
p=Path('mysql/engagement_models.py')
t=p.read_text(encoding='utf-8').replace("default='current'", "default='locked'").replace("cashback_valuation IN ('locked','current')", "cashback_valuation = 'locked'").replace("valuation IN ('locked','current')", "valuation = 'locked'")
p.write_text(t,encoding='utf-8')
p=Path('mysql/points.py');t=p.read_text(encoding='utf-8').replace("cashback_valuation='current'", "cashback_valuation='locked'").replace("config.rate if lot.valuation == 'current' else lot.rate_snapshot", "lot.rate_snapshot").replace("config.version if lot.valuation == 'current' else lot.rate_version", "lot.rate_version");p.write_text(t,encoding='utf-8')
p=Path('routes_loyalty.py');t=p.read_text(encoding='utf-8').replace("Literal['locked', 'current'] = 'current'", "Literal['locked'] = 'locked'");p.write_text(t,encoding='utf-8')
p=Path('private/freeze-engagement-migration.py');t=p.read_text(encoding='utf-8').replace("'current'", "'locked'");p.write_text(t,encoding='utf-8')
p=Path('routes_engagement.py');t=p.read_text(encoding='utf-8');a=t.index('    # Retained below');b=t.index('@router.get("/games/leaderboard")',a);t=t[:a]+ '\n\n'+t[b:];p.write_text(t,encoding='utf-8')
