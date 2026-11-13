import asyncio
import pytest
from sqlalchemy import select
from mysql import models as m
from tests_mysql.test_catalog_sql import sql_client

def test_new_product_without_variant_can_initialize_receipt_and_issue():
    async def run():
        async with sql_client() as (client,factory,_):
            created=await client.post('/api/admin/products',json={'name':'New stock','description':'New','price':100,'main_image':'','variants':[]})
            assert created.status_code==200,created.text
            pid=created.json()['product']['id']
            inv=(await client.get('/api/admin/inventory')).json()
            row=next(row for row in inv['items'] if row['product_id']==pid)
            assert row['variant_id'] is None and row['stock']==0 and row['can_adjust']
            response=await client.post(f'/api/admin/products/{pid}/stock',json={'adjustment_type':'receipt_stock','quantity':10,'ttb_number':' TTB-001 '})
            assert response.status_code==200,response.text
            vid=response.json()['variant_id'];assert response.json()['stock']==10
            issued=await client.post(f'/api/admin/products/{pid}/stock',json={'variant_id':vid,'adjustment_type':'issue_stock','quantity':3,'ttb_number':'TTB-002'})
            assert issued.status_code==200 and issued.json()['stock']==7
            async with factory() as s:
                moves=(await s.scalars(select(m.StockMovement).where(m.StockMovement.product_id==pid).order_by(m.StockMovement.created_at))).all()
                assert [(row.type,row.ttb_number,row.delta) for row in moves]==[('receipt_stock','TTB-001',10),('issue_stock','TTB-002',-3)]
                assert len((await s.scalars(select(m.ProductVariant).where(m.ProductVariant.product_id==pid))).all())==1
    asyncio.run(run())

@pytest.mark.parametrize('payload',[
 {'adjustment_type':'receipt_stock','quantity':1},
 {'adjustment_type':'receipt_stock','quantity':-1,'ttb_number':'TTB'},
 {'adjustment_type':'receipt_stock','quantity':1.5,'ttb_number':'TTB'},
 {'adjustment_type':'receipt_stock','quantity':True,'ttb_number':'TTB'},
 {'adjustment_type':'other','quantity':1,'ttb_number':'TTB'},
 {'adjustment_type':'issue_stock','quantity':9,'ttb_number':'TTB'},
])
def test_bad_adjustments_leave_reserved_stock_unchanged(payload):
    async def run():
        async with sql_client() as (client,factory,_):
            result=await client.post('/api/admin/products/product/stock',json={'variant_id':'variant',**payload})
            assert result.status_code in (409,422),result.text
            async with factory() as s:
                variant=await s.get(m.ProductVariant,'variant');assert (variant.stock,variant.reserved)==(10,2)
                assert not (await s.scalars(select(m.StockMovement))).all()
    asyncio.run(run())

def test_deleted_inventory_is_separate_and_cannot_be_adjusted():
    async def run():
        async with sql_client() as (client,factory,_):
            await client.delete('/api/admin/products/product')
            data=(await client.get('/api/admin/inventory')).json()
            assert data['items']==[] and len(data['deleted_items'])==1
            row=data['deleted_items'][0]
            assert row['deleted_at'] and not row['can_adjust'] and row['stock']==10
            result=await client.post('/api/admin/products/product/stock',json={'variant_id':'variant','adjustment_type':'receipt_stock','quantity':10,'ttb_number':'TTB'})
            assert result.status_code==404
    asyncio.run(run())
