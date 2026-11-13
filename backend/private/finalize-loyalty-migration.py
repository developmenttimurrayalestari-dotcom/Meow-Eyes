from pathlib import Path
import io
from alembic import command
from alembic.config import Config

p=Path('private/freeze-engagement-migration.py');t=p.read_text(encoding='utf-8')
t=t.replace("for level in range(1,21):", "SEED_SQL.append(\"UPDATE game_rules SET max_points=GREATEST(50,COALESCE((SELECT FLOOR(MAX(value)) FROM roulette_rewards WHERE type='points' AND is_active=1),0)) WHERE game_key='roulette'\")\nfor level in range(1,21):")
p.write_text(t,encoding='utf-8')
exec(compile(t,str(p),'exec'))
output=io.StringIO();config=Config('alembic.ini',output_buffer=output)
command.upgrade(config,'20261110_0004:20261111_0005',sql=True)
Path('sql/005_loyalty_games_returns.sql').write_text(output.getvalue(),encoding='utf-8')
