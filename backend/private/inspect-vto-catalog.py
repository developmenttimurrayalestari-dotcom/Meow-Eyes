"""Read-only publication audit. Never output credentials or source URLs."""
import asyncio, json
from pathlib import Path
from sqlalchemy import select
from mysql.config import MySQLSettings
from mysql.database import Database
from mysql import models as m

async def main():
    database = Database(MySQLSettings.from_env())
    try:
        async with database.session() as s:
            rows = (await s.execute(select(m.VirtualTryOnAsset, m.Product, m.ProductVariant, m.Upload)
                .join(m.Product, m.Product.id == m.VirtualTryOnAsset.product_id)
                .outerjoin(m.ProductVariant, m.ProductVariant.id == m.VirtualTryOnAsset.variant_id)
                .outerjoin(m.Upload, m.Upload.id == m.VirtualTryOnAsset.upload_id)
                .order_by(m.Product.name, m.VirtualTryOnAsset.id))).all()
            items = []
            for asset, product, variant, upload in rows:
                reasons = []
                if not product.is_active: reasons.append('product_inactive')
                if product.product_type != 'frame': reasons.append('not_frame')
                if asset.status != 'published': reasons.append('asset_' + asset.status)
                if asset.variant_id and (not variant or not variant.is_active): reasons.append('variant_inactive')
                if asset.upload_id and (not upload or upload.visibility != 'public' or not upload.url): reasons.append('upload_unavailable')
                if not asset.upload_id and not asset.source_url: reasons.append('source_missing')
                items.append({'asset_id': asset.id, 'product_id': product.id, 'product_name': product.name,
                    'status': asset.status, 'product_active': product.is_active, 'product_type': product.product_type,
                    'variant_active': variant.is_active if variant else None, 'excluded_by': reasons})
            report = {'assets': len(items), 'distinct_products': len({item['product_id'] for item in items}),
                      'eligible_products': len({item['product_id'] for item in items if not item['excluded_by']}), 'items': items}
            Path('private/vto-catalog-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            print(json.dumps(report, indent=2))
    finally: await database.dispose()

if __name__ == '__main__':
    try: asyncio.run(main())
    except Exception as error:
        print(json.dumps({'ok': False, 'error_type': type(error).__name__}))
        raise SystemExit(1)
