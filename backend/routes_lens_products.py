"""Priced lens type/index combinations reuse the existing relational lens tables."""
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from auth import require_permission
from database import read_session, session_scope
from models import User
from mysql import models as m
from mysql.commerce import lock_user
from mysql.lenses import available_indexes, indexes_payload, replace_index_types

router = APIRouter(tags=['lens-products'])
TYPES = {'clear':'Clear', 'uv420':'UV420', 'photochromic':'Photochromic', 'uv420-photochromic':'UV420 + Photochromic'}
KEY = 'catalog.lens_products.version'


class LensProductInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    version: int = Field(ge=0)
    lens_type: str = Field(min_length=1,max_length=64)
    index_value: str = Field(pattern=r'^1\.[0-9]{2}$')
    name: str = Field(default='', max_length=120)
    additional_price: Decimal = Field(ge=0, le=1000000000, decimal_places=2, allow_inf_nan=False)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0, le=9999)


async def payload(s):
    rows = (await s.scalars(select(m.LensIndex).order_by(m.LensIndex.sort_order,m.LensIndex.id))).all()
    gate = await s.get(m.Setting,KEY)
    categories=(await s.scalars(select(m.Category).where(m.Category.group_type=='lens_type',m.Category.is_active.is_(True)).order_by(m.Category.sort_order,m.Category.id))).all()
    types={**TYPES,**{category.code:TYPES.get(category.code,category.name) for category in categories}}
    inactive=set((await s.scalars(select(m.Category.code).where(m.Category.group_type=='lens_type',m.Category.is_active.is_(False)))).all())
    return {'version':gate.value['version'] if gate else 0,
            'types':[{'code':code,'name':name} for code,name in types.items() if code not in inactive],
            'items':await indexes_payload(s,rows)}


@router.get('/products/{product_id}/optical-options')
async def optical_options(product_id: str):
    async with read_session() as s:
        product = await s.get(m.Product,product_id)
        if not product or not product.is_active or product.deleted_at:
            raise HTTPException(404,'Produk tidak tersedia')
        items=await indexes_payload(s,await available_indexes(s,product))
        # Each new choice must identify exactly one treatment. Historical
        # surcharge rows with no/multiple types remain editable in admin.
        items=[item for item in items if len(item['lens_types'])==1 and item['lens_types'][0]['is_active']]
        return {'items':items,
                'included_in_package':product.product_type=='package'}


@router.get('/admin/lens-products')
async def list_products(admin: User = Depends(require_permission('product.view'))):
    async with read_session() as s: return await payload(s)


async def write(admin,version,body=None,identity=None,remove=False):
    try:
        async with session_scope() as s:
            await lock_user(s,admin.user_id)
            gate = await s.get(m.Setting,KEY,with_for_update=True)
            current = gate.value['version'] if gate else 0
            if current != version: raise HTTPException(409,'Daftar lensa sudah diubah. Muat ulang sebelum menyimpan.')
            row = await s.get(m.LensIndex,identity,with_for_update=True) if identity else None
            if identity and not row: raise HTTPException(404,'Produk lensa tidak ditemukan')
            if remove:
                # Preserve IDs referenced by carts and immutable order components.
                row.is_active=False
            else:
                category = await s.scalar(select(m.Category).where(m.Category.group_type=='lens_type',m.Category.code==body.lens_type).with_for_update())
                if category is None:
                    if body.lens_type not in TYPES: raise HTTPException(422,'Jenis lensa belum tersedia. Tambahkan melalui Master Kategori > Jenis Lensa.')
                    category=m.Category(id=m.new_id(),group_type='lens_type',code=body.lens_type,
                        slug='lens-type-'+body.lens_type,name=TYPES[body.lens_type],is_active=True)
                    s.add(category); await s.flush()
                if not category.is_active: raise HTTPException(422,'Jenis lensa nonaktif. Aktifkan pada Master Kategori dahulu.')
                duplicate=await s.scalar(select(m.LensIndex.id).join(m.LensIndexType).where(
                    m.LensIndexType.category_id==category.id,m.LensIndex.index_value==body.index_value,
                    m.LensIndex.id != (identity or '')).limit(1))
                if duplicate: raise HTTPException(409,'Kombinasi jenis dan indeks ini sudah tersedia. Edit harga pada entri tersebut.')
                if row is None:
                    row=m.LensIndex(id=m.new_id());s.add(row)
                row.name=f'{TYPES.get(body.lens_type,category.name)} · Indeks {body.index_value}' + (f' — {body.name}' if body.name else '')
                row.index_value,row.additional_price=body.index_value,body.additional_price
                row.is_active,row.sort_order=body.is_active,body.sort_order
                await s.flush()
                await replace_index_types(s,row.id,[category.id])
            if gate is None: gate=m.Setting(key=KEY,is_public=False);s.add(gate)
            gate.value,gate.updated_by={'version':current+1},admin.user_id
            await s.flush()
            return await payload(s)
    except IntegrityError:
        raise HTTPException(409,'Data lensa berubah atau kombinasi sudah digunakan. Muat ulang daftar.') from None


@router.post('/admin/lens-products')
async def create(body: LensProductInput,admin: User=Depends(require_permission('product.create'))):
    return await write(admin,body.version,body=body)


@router.put('/admin/lens-products/{identity}')
async def update(identity: str,body: LensProductInput,admin: User=Depends(require_permission('product.update'))):
    return await write(admin,body.version,body=body,identity=identity)


@router.delete('/admin/lens-products/{identity}')
async def remove(identity: str,version: int=Query(ge=0),admin: User=Depends(require_permission('product.delete'))):
    return await write(admin,version,identity=identity,remove=True)
