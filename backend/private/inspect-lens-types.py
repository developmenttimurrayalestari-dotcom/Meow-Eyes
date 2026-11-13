import asyncio
import json
from sqlalchemy import text
from mysql.database import Database
from mysql.config import MySQLSettings

async def main():
    db = Database(MySQLSettings.from_env())
    try:
        async with db.engine.connect() as connection:
            queries = {
                'revision': 'SELECT version_num FROM alembic_version',
                'indexes': 'SELECT id,name,index_value,additional_price,is_active FROM lens_indexes ORDER BY sort_order,id',
                'lens_types': "SELECT id,name,code,is_active FROM categories WHERE group_type='lens_type' ORDER BY sort_order,id",
                'package_types': "SELECT p.id,p.name,c.id AS category_id,c.name AS lens_type FROM products p LEFT JOIN product_categories pc ON pc.product_id=p.id LEFT JOIN categories c ON c.id=pc.category_id AND c.group_type='lens_type' WHERE p.product_type='package' AND p.deleted_at IS NULL AND p.is_active=1 AND (c.id IS NOT NULL OR NOT EXISTS(SELECT 1 FROM product_categories x JOIN categories y ON x.category_id=y.id WHERE x.product_id=p.id AND y.group_type='lens_type')) ORDER BY p.id,c.id",
            }
            result = {name: [dict(row) for row in (await connection.execute(text(sql))).mappings()] for name, sql in queries.items()}
            print(json.dumps(result, default=str, ensure_ascii=True))
    finally:
        await db.dispose()

if __name__ == '__main__':
    try: asyncio.run(main())
    except Exception as error:
        print(json.dumps({'ok': False, 'error_type': type(error).__name__})); raise SystemExit(1)
