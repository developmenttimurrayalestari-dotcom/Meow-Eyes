from pathlib import Path
import io
from alembic.config import Config
from alembic import command
p=Path('private/freeze-engagement-migration.py');t=p.read_text(encoding='utf-8')
old='"INSERT INTO point_history(id,event_key,user_id,lot_id,source,delta,balance_after,rate_snapshot,rate_version,value_snapshot,note,created_at) SELECT REPLACE(UUID(),\'-\',\'\'),CONCAT(\'legacy:\',user_id),user_id,id,\'legacy\',earned,remaining,100,1,earned*100,\'Saldo awal sebelum dompet per perolehan\',created_at FROM point_lots WHERE source=\'legacy\'"'
new='''"INSERT INTO point_history(id,event_key,user_id,order_id,source,delta,balance_after,rate_snapshot,rate_version,value_snapshot,note,created_at) SELECT REPLACE(UUID(),'-',''),CONCAT('legacy-log:',id),user_id,order_id,type,delta,balance_after,100,1,delta*100,note,created_at FROM point_logs",
 "INSERT INTO point_history(id,event_key,user_id,lot_id,source,delta,balance_after,rate_snapshot,rate_version,value_snapshot,note,created_at) SELECT REPLACE(UUID(),'-',''),CONCAT('legacy:',l.user_id),l.user_id,l.id,'legacy',l.earned-COALESCE(h.total,0),l.remaining,100,1,(l.earned-COALESCE(h.total,0))*100,'Rekonsiliasi saldo awal; riwayat lama dipertahankan',l.created_at FROM point_lots l LEFT JOIN (SELECT user_id,SUM(delta) AS total FROM point_logs GROUP BY user_id) h ON h.user_id=l.user_id WHERE l.source='legacy'"'''
assert old in t
t=t.replace(old,new);p.write_text(t,encoding='utf-8')
exec(compile(t,str(p),'exec'))
out=io.StringIO();command.upgrade(Config('alembic.ini',output_buffer=out),'20261110_0004:20261111_0005',sql=True)
Path('sql/005_loyalty_games_returns.sql').write_text(out.getvalue(),encoding='utf-8')
