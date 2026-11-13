"""Independent category assignments; no runtime ancestry or implicit children."""
import hashlib
from collections import defaultdict
from fastapi import HTTPException
from sqlalchemy import select, delete
from . import models as m
from .taxonomy_definitions import GROUPS, INITIAL_MASTERS

def master_id(group, code):
    return 'catm_' + hashlib.sha256((group + ':' + code).encode()).hexdigest()[:32]

async def seed_masters(s):
    """Explicit idempotent seed; existing names/activation choices are preserved."""
    existing = set((await s.execute(select(m.Category.group_type, m.Category.code))).all())
    for index, (group, code, name) in enumerate(INITIAL_MASTERS):
        if (group, code) not in existing:
            slug = group.replace('_', '-') + '-' + code
            s.add(m.Category(id=master_id(group, code), group_type=group, code=code, name=name, slug=slug, sort_order=index, is_active=True))
    await s.flush()

async def replace_product_tags(s, product, payload):
    """The engine's product kind and the master tag must agree atomically."""
    current = set((await s.scalars(select(m.ProductCategory.category_id).where(m.ProductCategory.product_id == product.id))).all())
    ids = set(payload.get('category_ids', current))
    if 'segments' in payload and 'category_ids' not in payload:
        gender_ids = set((await s.scalars(select(m.Category.id).where(m.Category.group_type == 'gender'))).all())
        ids -= gender_ids
    legacy_primary = payload.get('primary_category_id')
    if legacy_primary: ids.add(legacy_primary)
    rows = list((await s.scalars(select(m.Category).where(m.Category.id.in_(ids)).order_by(m.Category.id).with_for_update())).all()) if ids else []
    if {row.id for row in rows} != ids: raise HTTPException(422, 'Master data produk tidak ditemukan')
    for row in rows:
        if row.group_type == 'collection': raise HTTPException(422, 'Kategori Koleksi sudah tidak digunakan. Muat ulang form produk.')
        if not row.is_active and row.id not in current: raise HTTPException(422, 'Master data yang dipilih sudah nonaktif')
        if row.group_type == 'product_type' and row.code != product.product_type:
            if 'category_ids' in payload: raise HTTPException(422, 'Jenis Produk tidak sesuai dengan tag master yang dipilih')
            ids.discard(row.id)
    kind = await s.scalar(select(m.Category).where(m.Category.group_type == 'product_type', m.Category.code == product.product_type).with_for_update())
    if not kind or (not kind.is_active and kind.id not in current): raise HTTPException(422, 'Master Jenis Produk belum tersedia atau nonaktif')
    ids.add(kind.id)
    # Legacy clients can still send segments; translate them into gender tags.
    if 'segments' in payload and not any(row.group_type == 'gender' for row in rows):
        names = {name.casefold() for name in payload['segments']}
        genders = (await s.scalars(select(m.Category).where(m.Category.group_type == 'gender', m.Category.is_active.is_(True)))).all()
        matched = [row for row in genders if row.name.casefold() in names or row.code.casefold() in names]
        if names - {value.casefold() for row in matched for value in (row.name, row.code)}:
            raise HTTPException(422, 'Gender yang dipilih tidak tersedia pada master data')
        ids.update(row.id for row in matched)
    product.primary_category_id = kind.id
    await s.execute(delete(m.ProductCategory).where(m.ProductCategory.product_id == product.id))
    s.add_all(m.ProductCategory(product_id=product.id, category_id=category_id) for category_id in sorted(ids))
    genders = (await s.scalars(select(m.Category).where(m.Category.id.in_(ids), m.Category.group_type == 'gender'))).all()
    await s.execute(delete(m.ProductSegment).where(m.ProductSegment.product_id == product.id))
    s.add_all(m.ProductSegment(product_id=product.id, segment=name) for name in sorted({row.name for row in genders}))
    await s.flush()

async def master_filter_conditions(s, raw):
    if not raw: return []
    values = raw.split(',')
    if len(values) > 100 or any(not value or len(value) > 64 for value in values): raise HTTPException(422, 'Filter master tidak valid')
    ids = set(values)
    rows = (await s.scalars(select(m.Category).where(m.Category.id.in_(ids), m.Category.is_active.is_(True), m.Category.group_type != 'collection'))).all()
    if {row.id for row in rows} != ids: raise HTTPException(422, 'Pilihan filter sudah tidak tersedia. Hapus atau ubah filter.')
    groups = defaultdict(list)
    for row in rows: groups[row.group_type].append(row)
    conditions = []
    for group, choices in groups.items():
        if group == 'product_type': conditions.append(m.Product.product_type.in_([row.code for row in choices]))
        else: conditions.append(m.Product.id.in_(select(m.ProductCategory.product_id).where(m.ProductCategory.category_id.in_([row.id for row in choices]))))
    return conditions
