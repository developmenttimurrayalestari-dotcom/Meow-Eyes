import asyncio
import json
from sqlalchemy import select, text
from mysql import models as m
from mysql.config import MySQLSettings
from mysql.database import Database
from mysql.commerce import priced_cart

async def main():
    db = Database(MySQLSettings.from_env())
    try:
        async with db.session_factory() as session:
            revision = (await session.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()
            rows = (await session.execute(select(m.CartItem, m.Product).join(m.Product, m.Product.id == m.CartItem.product_id)
                .where(m.Product.deleted_at.is_(None)).order_by(m.CartItem.updated_at.desc()).limit(8))).all()
            result = []
            for cart, product in rows:
                entry = {'product': product.name, 'product_type': product.product_type, 'quantity': cart.quantity,
                    'lens_index_saved': bool(cart.lens_index_id), 'prescription_saved': bool(cart.prescription_id)}
                try:
                    priced, _ = await priced_cart(session, cart.user_id, [cart.id], require_stock=False)
                    item = priced[0]
                    entry.update(frame_price=float(item.frame_price), lens_price=float(item.lens_price),
                        product_price=float(product.price), discount_price=float(product.discount_price) if product.discount_price is not None else None,
                        variant_price=float(item.variant.price_override) if item.variant.price_override is not None else None,
                        flash_sale_active=item.flash_item is not None,
                        lens_index_name=item.lens_index.name if item.lens_index else None,
                        unit_price=float(item.unit_price), subtotal=float(item.subtotal))
                except Exception as error: entry['pricing_error'] = type(error).__name__
                result.append(entry)
            print(json.dumps({'revision': revision, 'cart': result, 'read_only': True}))
    finally: await db.dispose()

if __name__ == '__main__':
    try: asyncio.run(main())
    except Exception as error:
        print(json.dumps({'ok': False, 'error_type': type(error).__name__})); raise SystemExit(1)
