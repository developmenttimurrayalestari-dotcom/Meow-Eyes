import asyncio
import json
from datetime import timedelta
from mysql.base import utcnow
from sqlalchemy import select
from mysql import models as m
from mysql.check_integrity import load_retired_collections_revision
from tests_mysql.test_catalog_sql import sql_client

def test_retirement_archives_references_and_removes_collection_assignments():
    async def run():
        async with sql_client() as (client,factory,_):
            async with factory.begin() as s:
                product=await s.get(m.Product,'product');product.primary_category_id='cat'
                s.add(m.FlashSale(id='sale',name='Existing sale',start_at=utcnow(),end_at=utcnow()+timedelta(days=1)))
                await s.flush()
                s.add(m.FlashSaleCategory(flash_sale_id='sale',category_id='cat',discount_type='percent',discount_value=60,quota_per_product=10))
                await s.flush()
                s.add(m.FlashSaleItem(id='flash-item',flash_sale_id='sale',product_id='product',source_category_id='cat',flash_price=40,quota=10,sold=1,reserved=1))
            async with factory.begin() as s:
                connection=await s.connection()
                await connection.run_sync(load_retired_collections_revision().retire_collections)
                assert await connection.run_sync(load_retired_collections_revision().row_issues)==[]
            async with factory() as s:
                assert not (await s.get(m.Category,'cat')).is_active
                assert (await s.get(m.Product,'product')).primary_category_id != 'cat'
                assert 'cat' not in (await s.scalars(select(m.ProductCategory.category_id).where(m.ProductCategory.product_id=='product'))).all()
                archive=(await s.get(m.Setting,'taxonomy-0008-retired-collections')).value
                if isinstance(archive,str):archive=json.loads(archive)
                assert archive['product_tags'] and archive['primaries']
                assert archive['flash_item_sources'][0]['source_category_id']=='cat'
                item=await s.get(m.FlashSaleItem,'flash-item')
                assert item.source_category_id is None and (item.flash_price,item.quota,item.sold,item.reserved)==(40,10,1,1)
                assert (await s.get(m.ProductVariant,'variant')).reserved==2
            categories=(await client.get('/api/admin/categories')).json()
            assert len(categories['groups'])==5
            assert all(item['group_type']!='collection' for item in categories['categories'])
            assert (await client.get('/api/categories/frames')).status_code==404
            assert (await client.put('/api/admin/products/product',json={'category_ids':['cat']})).status_code==422
    asyncio.run(run())
