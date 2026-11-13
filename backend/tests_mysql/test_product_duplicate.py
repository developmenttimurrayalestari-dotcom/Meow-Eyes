"""Duplicating a product copies configuration without copying inventory/history."""
import asyncio
from decimal import Decimal
import pytest
from sqlalchemy import delete, func, select
from mysql import models as m
from tests_mysql.test_catalog_sql import sql_client


async def enrich_source(factory):
    async with factory.begin() as s:
        product = await s.get(m.Product, 'product')
        product.description = '<h2>Deskripsi</h2><p>Frame titanium</p>'
        product.spec = {'material': 'Titanium'}
        product.discount_price = Decimal('90')
        product.flash_sale_price = Decimal('80')
        product.sold_count, product.rating_count, product.rating_avg = 12, 4, Decimal('4.50')
        product.seo_title = 'SEO frame'
        kind_id = await s.scalar(select(m.Category.id).where(m.Category.group_type == 'product_type', m.Category.code == 'frame'))
        await s.execute(delete(m.ProductCategory).where(m.ProductCategory.product_id == 'product', m.ProductCategory.category_id == 'cat'))
        product.primary_category_id = kind_id
        s.add(m.ProductCategory(product_id='product', category_id=kind_id))
        s.add(m.ProductImage(product_id='product', image_url='/gallery.png', alt_text='Tampak depan', sort_order=1))
        s.add(m.ProductBadge(product_id='product', badge='limited'))
        s.add(m.ProductBadge(product_id='product', badge='flashsale'))
        s.add(m.ProductVariant(id='inactive-variant', product_id='product', sku='INACTIVE', color='Blue', stock=3, reserved=0, sort_order=4, is_active=False))
        s.add(m.ProductFrameSpecification(product_id='product', a=52, b=38, dbl=18, ed=None, enabled=True, symmetric=True, version=7))
        s.add(m.ProductVariantFrameSpecification(product_id='product', variant_id='variant', a=53, b=38, dbl=18, enabled=True, symmetric=True, version=7))
        s.add(m.VirtualTryOnAsset(id='source-asset', product_id='product', variant_id='variant', asset_type='image',
            source_url='/try-on.png', status='published', scale=Decimal('1.2'), calibration={'eye': [10, 20]}))


def test_duplicate_copies_catalog_and_remaps_variants_specs_and_try_on():
    async def run():
        async with sql_client() as (client, factory, _):
            await enrich_source(factory)
            original = (await client.get('/api/admin/products/product')).json()['product']
            response = await client.post('/api/admin/products/product/duplicate')
            assert response.status_code == 200, response.text
            copy = response.json()['product']
            assert copy['id'] != original['id'] and copy['slug'] != original['slug'] and copy['sku'] != original['sku']
            assert copy['name'] == original['name'] + ' (Salinan)' and not copy['is_active']
            for field in ('description', 'spec', 'price', 'discount_price', 'brand_id', 'category_ids', 'segments', 'gallery', 'main_image', 'seo_title'):
                assert copy[field] == original[field], field
            assert copy['sold_count'] == copy['rating_count'] == copy['rating_avg'] == 0
            assert copy['flash_sale_price'] is None and copy['badges'] == ['limited', 'new']
            assert len(copy['variants']) == len(original['variants']) == 2
            for before, after in zip(original['variants'], copy['variants']):
                assert after['id'] != before['id'] and after['sku'] != before['sku']
                assert after['product_id'] == copy['id'] and after['stock'] == after['reserved'] == 0
                for field in ('color', 'color_hex', 'size', 'lens_type', 'price_override', 'is_active', 'sort_order'):
                    assert after[field] == before[field], field
            async with factory() as s:
                root = await s.get(m.ProductFrameSpecification, copy['id'])
                override = await s.get(m.ProductVariantFrameSpecification, copy['variants'][0]['id'])
                assert root.a == 52 and root.ed is None and root.version == 1
                assert override.a == 53 and override.product_id == copy['id'] and override.version == 1
                asset = await s.scalar(select(m.VirtualTryOnAsset).where(m.VirtualTryOnAsset.product_id == copy['id']))
                assert asset.id != 'source-asset' and asset.variant_id == copy['variants'][0]['id']
                assert asset.status == 'draft' and asset.source_url == '/try-on.png' and asset.scale == Decimal('1.2')
                assert asset.calibration == {'eye': [10, 20]} and asset.updated_by == 'admin'
                source_variant = await s.get(m.ProductVariant, 'variant')
                assert (source_variant.stock, source_variant.reserved) == (10, 2)
                assert (await s.get(m.ProductFrameSpecification, 'product')).version == 7
                assert (await s.get(m.VirtualTryOnAsset, 'source-asset')).status == 'published'
                assert not await s.scalar(select(func.count()).select_from(m.StockMovement).where(m.StockMovement.product_id == copy['id']))
            assert (await client.get('/api/products/' + copy['slug'])).status_code == 404
            assert (await client.put('/api/admin/products/' + copy['id'], json={'name': 'Edited copy'})).status_code == 200
            assert (await client.get('/api/admin/products/product')).json()['product'] == original
    asyncio.run(run())


def test_repeated_duplicates_have_unique_identifiers_even_with_maximum_length_skus():
    async def run():
        async with sql_client() as (client, factory, _):
            async with factory.begin() as s:
                (await s.get(m.Product, 'product')).sku = 'P' * 128
                (await s.get(m.Product, 'product')).name = 'N' * 255
                (await s.get(m.ProductVariant, 'variant')).sku = 'V' * 128
            copies = []
            for _ in range(2):
                response = await client.post('/api/admin/products/product/duplicate')
                assert response.status_code == 200, response.text
                copies.append(response.json()['product'])
            for key in ('id', 'slug', 'sku'):
                assert len({copy[key] for copy in copies}) == 2
            assert len({copy['variants'][0]['sku'] for copy in copies}) == 2
            assert all(len(copy['sku']) <= 128 and len(copy['name']) <= 255 and len(copy['slug']) <= 191
                and len(copy['variants'][0]['sku']) <= 128 for copy in copies)
    asyncio.run(run())


@pytest.mark.parametrize('kind', ['lens', 'package'])
def test_other_product_kinds_and_lens_type_classification_are_preserved(kind):
    async def run():
        async with sql_client() as (client, factory, _):
            async with factory.begin() as s:
                product = await s.get(m.Product, 'product')
                product.product_type = kind
                product.is_active = False
                kind_id = await s.scalar(select(m.Category.id).where(m.Category.group_type == 'product_type', m.Category.code == kind))
                lens_type_id = await s.scalar(select(m.Category.id).where(m.Category.group_type == 'lens_type', m.Category.code == 'single-vision'))
                product.primary_category_id = kind_id
                await s.execute(delete(m.ProductCategory).where(m.ProductCategory.product_id == 'product'))
                s.add_all([m.ProductCategory(product_id='product', category_id=cid) for cid in (kind_id, lens_type_id)])
            response = await client.post('/api/admin/products/product/duplicate')
            assert response.status_code == 200, response.text
            copy = response.json()['product']
            assert copy['product_type'] == kind and not copy['is_active']
            assert set(copy['category_ids']) == {kind_id, lens_type_id}
    asyncio.run(run())


@pytest.mark.parametrize('role', ['customer', 'staff'])
def test_duplicate_requires_admin(role):
    async def run():
        async with sql_client() as (client, factory, auth):
            auth['user'] = auth['user'].model_copy(update={'role': role, 'permissions': ['product.view', 'product.create', 'product.update']})
            assert (await client.post('/api/admin/products/product/duplicate')).status_code == 403
            async with factory() as s:
                assert await s.scalar(select(func.count()).select_from(m.Product)) == 1
    asyncio.run(run())


def test_deleted_and_missing_products_cannot_be_duplicated_and_failures_roll_back(monkeypatch):
    async def run():
        async with sql_client() as (client, factory, _):
            from mysql import product_management
            with monkeypatch.context() as patch:
                patch.setattr(product_management, '_duplicate_sku', lambda sku: sku)
                assert (await client.post('/api/admin/products/product/duplicate')).status_code == 409
            async with factory() as s:
                assert await s.scalar(select(func.count()).select_from(m.Product)) == 1
                assert await s.scalar(select(func.count()).select_from(m.ProductVariant)) == 1
            assert (await client.post('/api/admin/products/missing/duplicate')).status_code == 404
            assert (await client.delete('/api/admin/products/product')).status_code == 200
            assert (await client.post('/api/admin/products/product/duplicate')).status_code == 404
    asyncio.run(run())
