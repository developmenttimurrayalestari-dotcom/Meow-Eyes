"""Read-only LEFT JOIN audit of retained stock and deleted product flags."""
import asyncio,json
from pathlib import Path
from sqlalchemy import text
from mysql.config import MySQLSettings
from mysql.database import Database

async def main():
    db=Database(MySQLSettings.from_env())
    try:
        async with db.engine.connect() as c:
            groups=[dict(row) for row in (await c.execute(text("""
SELECT CASE WHEN p.deleted_at IS NOT NULL THEN 'deleted'
            WHEN p.is_active=0 THEN 'inactive' ELSE 'active' END AS product_status,
       COUNT(DISTINCT p.id) AS products, COUNT(v.id) AS stock_variants,
       COALESCE(SUM(v.stock),0) AS stock, COALESCE(SUM(v.reserved),0) AS reserved
FROM products p LEFT JOIN product_variants v ON v.product_id=p.id
GROUP BY product_status ORDER BY product_status
"""))).mappings()]
            orphaned=(await c.execute(text('SELECT COUNT(*) FROM product_variants v LEFT JOIN products p ON p.id=v.product_id WHERE p.id IS NULL'))).scalar_one()
            revision=(await c.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()
            report={'revision':revision,'groups':groups,'orphaned_variants':orphaned,'read_only':True}
            Path('private/inventory-join-report.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
            print(json.dumps(report,default=str))
    finally:await db.dispose()
if __name__=='__main__':
    try:asyncio.run(main())
    except Exception as e:print(json.dumps({'ok':False,'error_type':type(e).__name__}));raise SystemExit(1)
