from pathlib import Path
import io
from alembic import command
from alembic.config import Config
p=Path('private/freeze-engagement-migration.py');t=p.read_text(encoding='utf-8')
anchor="path.write_text(text,encoding='utf-8')"
correction='''text=text.replace("SELECT REPLACE(UUID(),'-',''),user_id,CONCAT('legacy:',user_id)","SELECT SHA2(CONCAT('legacy-lot:',user_id),256),user_id,CONCAT('legacy:',user_id)")
text=text.replace("SELECT REPLACE(UUID(),'-',''),CONCAT('legacy-log:',id)","SELECT SHA2(CONCAT('legacy-log:',id),256),CONCAT('legacy-log:',id)")
text=text.replace("SELECT REPLACE(UUID(),'-',''),CONCAT('legacy:',l.user_id)","SELECT SHA2(CONCAT('legacy-ledger:',l.user_id),256),CONCAT('legacy:',l.user_id)")
'''
assert anchor in t;t=t.replace(anchor,correction+anchor);p.write_text(t,encoding='utf-8')
exec(compile(t,str(p),'exec'))
out=io.StringIO();command.upgrade(Config('alembic.ini',output_buffer=out),'20261110_0004:20261111_0005',sql=True)
Path('sql/005_loyalty_games_returns.sql').write_text(out.getvalue(),encoding='utf-8')
