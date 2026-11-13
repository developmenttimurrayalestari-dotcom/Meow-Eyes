"""Lens index classification, package eligibility and authoritative pricing rules."""
from fastapi import HTTPException
from sqlalchemy import delete, select
from . import models as m
from .api import row_dict


async def replace_index_types(s, index_id, type_ids):
    ids = set(type_ids)
    current = set((await s.scalars(select(m.LensIndexType.category_id).where(m.LensIndexType.lens_index_id == index_id))).all())
    types = (await s.scalars(select(m.Category).where(m.Category.id.in_(ids),
        m.Category.group_type == 'lens_type').with_for_update())).all() if ids else []
    if {row.id for row in types} != ids or any(not row.is_active and row.id not in current for row in types):
        raise HTTPException(422, 'Pilih Jenis Lensa yang aktif dari master kategori')
    await s.execute(delete(m.LensIndexType).where(m.LensIndexType.lens_index_id == index_id))
    s.add_all(m.LensIndexType(lens_index_id=index_id, category_id=cid) for cid in sorted(ids))
    await s.flush()


async def indexes_payload(s, indexes):
    result = {row.id: {**row_dict(row), 'lens_type_ids': [], 'lens_types': []} for row in indexes}
    if result:
        rows = (await s.execute(select(m.LensIndexType.lens_index_id, m.Category).join(m.Category,
            m.Category.id == m.LensIndexType.category_id).where(m.LensIndexType.lens_index_id.in_(result))
            .order_by(m.Category.sort_order, m.Category.id))).all()
        for index_id, category in rows:
            result[index_id]['lens_type_ids'].append(category.id)
            result[index_id]['lens_types'].append({'id': category.id, 'name': category.name, 'is_active': category.is_active})
    return list(result.values())


async def product_lens_types(s, product_id):
    return list((await s.scalars(select(m.Category).join(m.ProductCategory,
        m.ProductCategory.category_id == m.Category.id).where(m.ProductCategory.product_id == product_id,
        m.Category.group_type == 'lens_type', m.Category.is_active.is_(True))
        .order_by(m.Category.sort_order, m.Category.id))).all())


async def available_indexes(s, product):
    query = select(m.LensIndex).where(m.LensIndex.is_active.is_(True))
    if product.product_type == 'package':
        types = await product_lens_types(s, product.id)
        query = query.where(m.LensIndex.id.in_(select(m.LensIndexType.lens_index_id)
            .where(m.LensIndexType.category_id.in_([row.id for row in types]))))
    elif product.product_type != 'frame':
        return []
    return list((await s.scalars(query.order_by(m.LensIndex.sort_order, m.LensIndex.id))).all())


async def validate_index(s, product, index_id, *, lock=False):
    if index_id is None or index_id == '':
        return None
    if not isinstance(index_id, str) or len(index_id) > 64 or product.product_type not in ('frame', 'package'):
        raise HTTPException(422, 'Pilihan Lens Index tidak valid untuk produk ini')
    query = select(m.LensIndex).where(m.LensIndex.id == index_id, m.LensIndex.is_active.is_(True))
    index = await s.scalar(query.with_for_update() if lock else query)
    if index is None:
        raise HTTPException(422, 'Lens Index tidak tersedia; pilih kembali lensa')
    if product.product_type == 'package':
        allowed = await s.scalar(select(m.LensIndexType.lens_index_id).join(m.ProductCategory,
            m.ProductCategory.category_id == m.LensIndexType.category_id).join(m.Category,
            m.Category.id == m.LensIndexType.category_id).where(m.ProductCategory.product_id == product.id,
            m.LensIndexType.lens_index_id == index.id, m.Category.group_type == 'lens_type',
            m.Category.is_active.is_(True)).limit(1))
        if not allowed:
            raise HTTPException(422, 'Lens Index tidak sesuai Jenis Lensa pada paket. Pilih kembali lensa.')
    return index
