"""Read-only taxonomy mapping audit; no credentials or customer data."""
import asyncio, json
from pathlib import Path
from sqlalchemy import select, text
from mysql import models as m
from mysql.database import Database
from mysql.config import MySQLSettings

async def main():
    database=Database(MySQLSettings.from_env())
    try:
        async with database.session() as s:
            categories=(await s.scalars(select(m.Category).order_by(m.Category.name))).all()
            products=(await s.scalars(select(m.Product).order_by(m.Product.name))).all()
            links=(await s.execute(select(m.ProductCategory.product_id,m.ProductCategory.category_id))).all()
            segments=(await s.execute(select(m.ProductSegment.product_id,m.ProductSegment.segment))).all()
            report={'revision':(await s.execute(text('SELECT version_num FROM alembic_version'))).scalar_one(),
              'categories':[{key:getattr(c,key) for key in ('id','parent_id','name','slug','category_type','level','is_active')} for c in categories],
              'products':[{'id':p.id,'name':p.name,'type':p.product_type,'primary_category_id':p.primary_category_id,
                'category_ids':[cid for pid,cid in links if pid==p.id], 'segments':[seg for pid,seg in segments if pid==p.id],
                'spec':p.spec} for p in products]}
            Path('private/category-flattening-audit.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
            print(json.dumps(report,indent=2,default=str))
    finally:await database.dispose()
if __name__=='__main__':
    try:asyncio.run(main())
    except Exception as error:
        print(json.dumps({'ok':False,'error_type':type(error).__name__}));raise SystemExit(1)
