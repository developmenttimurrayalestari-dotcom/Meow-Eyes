import asyncio
from sqlalchemy import select
from mysql import models as m
from mysql.navigation import STORE, DEFAULTS
from tests_mysql.test_catalog_sql import sql_client

BODY = dict(version=0,label='Panduan',url='/pages/panduan-belanja',location='header',icon='article',sort_order=0,is_active=True,new_tab=False)


def test_menu_defaults_crud_visibility_order_and_concurrent_versions():
    async def run():
        async with sql_client() as (client,factory,auth):
            initial=(await client.get('/api/admin/menus')).json()
            assert initial['version']==0 and len(initial['items'])==len(DEFAULTS)
            assert any(item['url']=='/meowsurement/' for item in initial['items'])
            async with factory() as s: assert await s.get(m.Setting,STORE.key) is None
            created=await client.post('/api/admin/menus',json=BODY)
            assert created.status_code==200,created.text
            value=created.json(); new=next(item for item in value['items'] if item['label']=='Panduan')
            assert value['version']==1 and len(value['items'])==len(DEFAULTS)+1
            changed=await client.put('/api/admin/menus/'+new['id'],json={**BODY,'version':1,'location':'footer','url':'https://example.com/help','new_tab':True,'sort_order':99})
            assert changed.status_code==200
            assert (await client.put('/api/admin/menus/'+new['id'],json=BODY)).status_code==409
            assert (await client.delete('/api/admin/menus/'+new['id'],params={'version':0})).status_code==409
            admin=auth['user'];auth['user']=None
            public=(await client.get('/api/menus')).json()
            assert set(public)=={'items'} and public['items'][-1]['id']==new['id']
            assert public['items'][-1]['location']=='footer' and public['items'][-1]['new_tab'] is True
            auth['user']=admin
            assert (await client.put('/api/admin/menus/'+new['id'],json={**BODY,'version':2,'is_active':False})).status_code==200
            assert new['id'] not in [item['id'] for item in (await client.get('/api/menus')).json()['items']]
            assert (await client.delete('/api/admin/menus/'+new['id'],params={'version':3})).status_code==200
            async with factory() as s:
                row=await s.get(m.Setting,STORE.key)
                assert row.is_public is False and row.updated_by=='admin'
    asyncio.run(run())


def test_menu_empty_configuration_is_persisted_without_restoring_defaults():
    async def run():
        async with sql_client() as (client,factory,auth):
            for version,item in enumerate(DEFAULTS):
                result=await client.delete('/api/admin/menus/'+item['id'],params={'version':version})
                assert result.status_code==200,result.text
            assert (await client.get('/api/menus')).json()=={'items':[]}
            assert (await client.get('/api/admin/menus')).json()['items']==[]
            assert (await client.put('/api/admin/menus/missing',json={**BODY,'version':len(DEFAULTS)})).status_code==404
    asyncio.run(run())


def test_menu_validation_and_staff_permissions():
    async def run():
        async with sql_client() as (client,factory,auth):
            for change in [dict(url='javascript:alert(1)'),dict(url='//evil.example'),dict(url='/\\evil.example'),dict(label=' '),dict(label='a'*81),dict(location='admin'),dict(icon='<script>'),dict(sort_order=-1),dict(version=-1),dict(id='injected')]:
                response=await client.post('/api/admin/menus',json={**BODY,**change})
                assert response.status_code==422,(change,response.text)
            auth['user'].role='customer'
            assert (await client.get('/api/admin/menus')).status_code==403
            assert (await client.post('/api/admin/menus',json=BODY)).status_code==403
            auth['user'].role='staff';auth['user'].permissions=['setting.view']
            assert (await client.get('/api/admin/menus')).status_code==200
            assert (await client.post('/api/admin/menus',json=BODY)).status_code==403
            assert (await client.delete('/api/admin/menus/nav-home',params={'version':0})).status_code==403
            auth['user'].permissions.append('setting.update')
            assert (await client.post('/api/admin/menus',json=BODY)).status_code==200
            async with factory.begin() as s:
                row=await s.get(m.Setting,STORE.key)
                row.value={'version':1,'items':[{**DEFAULTS[0],'id':str(i)} for i in range(100)]}
            assert (await client.post('/api/admin/menus',json={**BODY,'version':1})).status_code==422
    asyncio.run(run())
