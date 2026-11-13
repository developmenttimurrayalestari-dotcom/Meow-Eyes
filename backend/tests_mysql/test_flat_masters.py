"""Grouped masters: real route transactions, filters, and frozen legacy mapping."""
import asyncio
from sqlalchemy import func, select
from mysql import models as m
from mysql.check_integrity import load_flat_master_revision
from mysql.taxonomy import seed_masters, master_id
from mysql.taxonomy_definitions import INITIAL_MASTERS
from tests_mysql.test_catalog_sql import sql_client


def mid(group, code): return master_id(group, code)


def test_seed_is_idempotent_and_grouped_crud_rejects_hierarchy_and_used_deletes():
    async def run():
        async with sql_client() as (client, factory, _):
            async with factory.begin() as s:
                row = await s.get(m.Category, mid('material', 'titanium'))
                row.name = 'Titanium premium'; row.is_active = False
                await seed_masters(s)
            data = (await client.get('/api/admin/categories')).json()
            assert len(data['groups']) == 5
            assert all('parent_id' not in row and 'children' not in row for row in data['categories'])
            materials = (await client.get('/api/admin/categories?group_type=material')).json()['categories']
            assert len(materials) == 3
            assert next(row for row in materials if row['code'] == 'titanium')['name'] == 'Titanium premium'
            assert len((await client.get('/api/categories?group_type=material')).json()['categories']) == 2
            assert (await client.post('/api/admin/categories', json={'name':'X','parent_id':'cat'})).status_code == 422
            assert (await client.post('/api/admin/categories', json={'name':'X','group_type':'unknown'})).status_code == 422
            assert (await client.post('/api/admin/categories', json={'name':'X','group_type':'product_type','code':'newkind'})).status_code == 422
            assert (await client.post('/api/admin/categories', json={'name':'Acetate','group_type':'material'})).status_code == 409
            assert all(row['group_type'] != 'collection' for row in data['categories'])
            assert (await client.post('/api/admin/categories',json={'name':'Legacy','group_type':'collection'})).status_code == 422
            created = await client.post('/api/admin/categories', json={'name':'Stainless','group_type':'material'})
            assert created.status_code == 200, created.text
            item = created.json()['category']
            bad = await client.put('/api/admin/categories/'+item['id'], json={**{'name':'Stainless','group_type':'gender'}, 'code':item['code']})
            assert bad.status_code == 422
            assert (await client.put('/api/admin/categories/'+item['id'], json={'name':'Stainless steel','group_type':'material'})).status_code == 200
            assert (await client.delete('/api/admin/categories/'+item['id'])).status_code == 200
            assert (await client.delete('/api/admin/categories/'+mid('product_type','frame'))).status_code == 409
            tree = (await client.get('/api/categories/tree')).json()['tree']
            assert all('children' not in row for row in tree)
    asyncio.run(run())


def test_product_multi_group_writes_filters_and_rollback_preserve_stock():
    async def run():
        async with sql_client() as (client, factory, _):
            tags = [mid('gender','pria'),mid('frame_shape','round'),mid('material','titanium')]
            response = await client.put('/api/admin/products/product', json={'category_ids':tags, 'product_type':'frame'})
            assert response.status_code == 200, response.text
            item = (await client.get('/api/admin/products/product')).json()['product']
            assert set(item['category_ids']) == set(tags+[mid('product_type','frame')])
            assert item['segments'] == ['Pria']
            assert item['variants'][0]['reserved'] == 2
            second = await client.post('/api/admin/products', json={'name':'Second','description':'','price':200,'main_image':'','product_type':'frame',
                'category_ids':[mid('gender','wanita'),mid('frame_shape','square'),mid('material','acetate')]})
            assert second.status_code == 200, second.text
            sid = second.json()['product']['id']
            async def matches(ids):
                result = await client.get('/api/products', params={'category_ids':','.join(ids)})
                assert result.status_code == 200, result.text
                return {p['id'] for p in result.json()['products']}
            assert await matches([mid('gender','pria'),mid('gender','wanita')]) == {'product',sid}
            assert await matches([mid('gender','pria'),mid('gender','wanita'),mid('material','titanium')]) == {'product'}
            assert await matches([mid('gender','wanita'),mid('material','titanium')]) == set()
            assert await matches([mid('product_type','lens')]) == set()
            assert (await client.get('/api/products?category_ids=does-not-exist')).status_code == 422
            bad = await client.put('/api/admin/products/product', json={'name':'Must rollback','category_ids':[mid('product_type','lens')]})
            assert bad.status_code == 422
            async with factory() as s:
                assert (await s.get(m.Product,'product')).name == 'Frame 100%'
            async with factory.begin() as s:
                (await s.get(m.Category, mid('material','titanium'))).is_active = False
            # Existing inactive tags survive edits, but cannot be newly assigned.
            assert (await client.put('/api/admin/products/product', json={'category_ids':tags})).status_code == 200
            assert (await client.put('/api/admin/products/'+sid, json={'category_ids':tags})).status_code == 422
            assert (await client.get('/api/products', params={'category_ids':mid('material','titanium')})).status_code == 422
            assert (await client.put('/api/admin/products/product', json={'category_ids':[]})).status_code == 200
            item = (await client.get('/api/admin/products/product')).json()['product']
            assert item['category_ids'] == [mid('product_type','frame')] and item['segments'] == []
            assert (await client.put('/api/admin/products/product', json={'segments':['Wanita']})).status_code == 200
            assert (await client.put('/api/admin/products/product', json={'segments':['Unisex']})).status_code == 200
            item = (await client.get('/api/admin/products/product')).json()['product']
            assert item['segments'] == ['Unisex']
            assert mid('gender','wanita') not in item['category_ids']
            assert (await client.put('/api/admin/products/product', json={'segments':['Unknown']})).status_code == 422
    asyncio.run(run())


def test_legacy_mapping_preserves_ids_scopes_and_adds_independent_tags():
    revision = load_flat_master_revision()
    assert revision.INITIAL_MASTERS == INITIAL_MASTERS
    def cat(cid,name,parent=None,kind='frame'):
        return {'id':cid,'name':name,'slug':cid,'parent_id':parent,'level':0 if not parent else 1,'category_type':kind}
    cats = [cat('frame','Frame'),cat('round','Round','frame'),cat('male-round','Pria','round'),
            cat('square','Square','frame'),cat('male-square','Pria','square'),cat('lens','Lensa',kind='lens'),
            cat('blue','Anti Radiasi (Blue Cut)','lens','lens')]
    products = [{'id':'p','product_type':'frame','primary_category_id':'male-round','spec':{'Material':'Titanium','Wajah':'Oval'}},
                {'id':'l','product_type':'lens','spec':{'Material':'Acetate'}}]
    links = [('p','male-round'),('l','blue')]
    plan = revision.plan_rows(cats,products,links,[])
    assert plan == revision.plan_rows(cats,products,links,[])
    assert set(links) <= set(plan['links'])
    assert {('p','round'),('p','frame'),('p',mid('gender','pria')),('p',mid('material','titanium'))} <= set(plan['links'])
    assert ('p','male-square') not in plan['links']
    assert ('p',mid('frame_shape','oval')) not in plan['links']
    assert ('l',mid('material','acetate')) not in plan['links']
    rows = {row['id']:row for row in plan['masters']}
    assert rows['male-round']['name'] == 'Round · Pria' and rows['male-round']['group_type'] == 'collection'
    assert rows['blue']['code'] == 'blue-cut' and rows['blue']['name'] == 'Anti Radiasi (Blue Cut)'
    assert plan['initial_ids']['lens_type:uv420'] != 'blue'
    assert len(plan['initial_ids']) == 23
    assert not {'parent_id','level','category_type'} & set(m.Category.__table__.columns.keys())
    assert all(fk.target_fullname != 'categories.id' for fk in m.Category.__table__.foreign_keys)


def test_legacy_mapping_rejects_broken_ancestry_before_any_write():
    import pytest
    revision = load_flat_master_revision()
    with pytest.raises(RuntimeError, match='ancestry'):
        revision.plan_rows([{'id':'a','name':'A','slug':'a','parent_id':'a'}],[],[],[])
    with pytest.raises(RuntimeError, match='ancestry'):
        revision.plan_rows([{'id':'a','name':'A','slug':'a','parent_id':'missing'}],[],[],[])
