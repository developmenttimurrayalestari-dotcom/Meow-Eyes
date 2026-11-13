"""Product lifecycle actions without removing immutable purchase references."""
from fastapi import HTTPException
from sqlalchemy import select
from . import models as m
from .base import utcnow
from copy import deepcopy


async def apply_product_action(session, product_ids, action):
    if action not in ('delete', 'deactivate'):
        raise HTTPException(422, 'Aksi produk tidak dikenal')
    if not 1 <= len(product_ids) <= 200 or any(not isinstance(pid, str) or not pid.strip() or pid != pid.strip() or len(pid) > 64 for pid in product_ids):
        raise HTTPException(422, 'Pilih 1 sampai 200 ID produk yang valid')
    ids = sorted(set(product_ids))
    # One transaction and stable lock order: a missing ID never leaves a
    # partially applied bulk action. Repeated requests remain idempotent.
    products = (await session.scalars(select(m.Product).where(m.Product.id.in_(ids))
        .order_by(m.Product.id).with_for_update())).all()
    if len(products) != len(ids):
        raise HTTPException(404, 'Sebagian produk tidak ditemukan. Muat ulang daftar produk.')
    changed = []
    now = utcnow()
    for product in products:
        if product.deleted_at is not None:
            continue
        if action == 'delete':
            product.deleted_at = now
        elif not product.is_active:
            continue
        product.is_active = False
        product.updated_at = now
        changed.append(product.id)
    await session.flush()
    return {'ok': True, 'action': action, 'processed_ids': ids,
            'changed_ids': changed, 'changed_count': len(changed)}


def _duplicate_sku(sku):
    suffix = '-COPY-' + m.new_id()[:16].upper()
    return sku[:128 - len(suffix)] + suffix


async def duplicate_product(session, source, admin_id):
    """Copy catalog configuration in one transaction, with independent identities."""
    from .catalog import PRODUCT_FIELDS, VARIANT_FIELDS
    copied = PRODUCT_FIELDS - {'name', 'slug', 'sku', 'is_active', 'flash_sale_price'}
    product = m.Product(id=m.new_id(), **{field: deepcopy(getattr(source, field)) for field in copied},
        name=source.name[:245] + ' (Salinan)', sku=_duplicate_sku(source.sku),
        slug=source.slug[:160] + '-salinan-' + m.new_id()[:16], is_active=False, flash_sale_price=None)
    session.add(product)
    await session.flush()
    variants = (await session.scalars(select(m.ProductVariant).where(m.ProductVariant.product_id == source.id)
        .order_by(m.ProductVariant.sort_order, m.ProductVariant.id).with_for_update())).all()
    variant_ids = {}
    for variant in variants:
        values = {field: deepcopy(getattr(variant, field)) for field in VARIANT_FIELDS - {'sku'}}
        new_id = m.new_id(); variant_ids[variant.id] = new_id
        session.add(m.ProductVariant(id=new_id, product_id=product.id, sku=_duplicate_sku(variant.sku),
            stock=0, reserved=0, sort_order=variant.sort_order, **values))
    await session.flush()
    for model, fields in (
        (m.ProductImage, ('image_url', 'alt_text', 'sort_order')),
        (m.ProductCategory, ('category_id',)),
        (m.ProductSegment, ('segment',)),
        (m.ProductBadge, ('badge',)),
    ):
        query = select(model).where(model.product_id == source.id)
        if model is m.ProductCategory:
            query = query.join(m.Category, m.Category.id == m.ProductCategory.category_id).where(m.Category.group_type != 'collection')
        if model is m.ProductBadge:
            query = query.where(m.ProductBadge.badge != 'flashsale')
        for row in (await session.scalars(query)).all():
            session.add(model(product_id=product.id, **{field: deepcopy(getattr(row, field)) for field in fields}))
    # Measurements are configuration; customer sessions and their audit history
    # continue to reference the source product and are never duplicated.
    spec_fields = ('a', 'b', 'dbl', 'ed', 'temple_length', 'symmetric', 'enabled', 'source_note')
    root = await session.get(m.ProductFrameSpecification, source.id)
    if root:
        session.add(m.ProductFrameSpecification(product_id=product.id, version=1, updated_by=admin_id,
            **{field: getattr(root, field) for field in spec_fields}))
    overrides = (await session.scalars(select(m.ProductVariantFrameSpecification)
        .where(m.ProductVariantFrameSpecification.product_id == source.id))).all()
    for row in overrides:
        session.add(m.ProductVariantFrameSpecification(product_id=product.id, variant_id=variant_ids[row.variant_id],
            version=1, updated_by=admin_id, **{field: getattr(row, field) for field in spec_fields}))
    # The files may be reused; each asset gets a new record and new variant link.
    asset_fields = ('asset_type', 'upload_id', 'source_url', 'preview_url', 'scale', 'offset_x', 'offset_y', 'offset_z',
                    'rotation_x', 'rotation_y', 'rotation_z', 'calibration', 'sort_order')
    assets = (await session.scalars(select(m.VirtualTryOnAsset).where(m.VirtualTryOnAsset.product_id == source.id,
        m.VirtualTryOnAsset.status != 'archived'))).all()
    for asset in assets:
        session.add(m.VirtualTryOnAsset(id=m.new_id(), product_id=product.id,
            variant_id=variant_ids[asset.variant_id] if asset.variant_id else None, status='draft', updated_by=admin_id,
            **{field: deepcopy(getattr(asset, field)) for field in asset_fields}))
    await session.flush()
    return product
