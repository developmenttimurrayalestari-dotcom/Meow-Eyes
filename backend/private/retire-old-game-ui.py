from pathlib import Path
Path('../frontend/src/pages/GamePlayPage.jsx').write_text('export { default } from "./GamesRoundPage";\n',encoding='utf-8')
Path('../frontend/src/pages/PointsPage.jsx').write_text('export { default } from "./WalletPage";\n',encoding='utf-8')
p=Path('mysql/commerce.py');t=p.read_text(encoding='utf-8').replace('POINT_VALUE = Decimal("100.00")\n','');p.write_text(t,encoding='utf-8')
p=Path('routes_orders.py');t=p.read_text(encoding='utf-8').replace('    POINT_VALUE, RESERVATION_HOURS,','    RESERVATION_HOURS,');p.write_text(t,encoding='utf-8')
p=Path('routes_engagement.py');t=p.read_text(encoding='utf-8');a=t.index('DAILY_GAME_PLAY_LIMIT =');b=t.index('ROULETTE_REWARD_TTL_DAYS',a);t=t[:a]+t[b:];p.write_text(t,encoding='utf-8')
p=Path('../frontend/src/pages/VirtualTryOnPage.jsx');t=p.read_text(encoding='utf-8').replace('rounded border ml-1 px-2 py-1 max-w-48','rounded border px-2 py-1 w-full max-w-48');p.write_text(t,encoding='utf-8')
