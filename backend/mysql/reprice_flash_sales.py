"""Repair category Flash Sale prices from the normal product price. Default: read only."""
import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from . import models as m
from .base import utcnow
from .config import MySQLSettings
from .database import Database
from .features import _category_price


async def repair(apply=False):
    settings = MySQLSettings.from_env()
    database = Database(settings)
    try:
        readiness = await database.check_readiness()
        if not readiness.ready:
            return {"ok": False, "reason": readiness.reason}
        changes = []
        async with database.session_factory() as session, session.begin():
            # Follow checkout's lock order: products before campaign/item rows.
            product_ids = select(m.FlashSaleItem.product_id).join(m.FlashSale).where(
                m.FlashSale.end_at > utcnow(), m.FlashSaleItem.source_category_id.is_not(None))
            stmt = select(m.Product).where(m.Product.id.in_(product_ids)).order_by(m.Product.id)
            if apply:
                stmt = stmt.with_for_update()
            products = {p.id: p for p in (await session.scalars(stmt)).all()}
            stmt = (select(m.FlashSaleItem, m.FlashSaleCategory).select_from(m.FlashSaleItem)
                .join(m.FlashSale, m.FlashSale.id == m.FlashSaleItem.flash_sale_id)
                .join(m.FlashSaleCategory, (m.FlashSaleCategory.flash_sale_id == m.FlashSaleItem.flash_sale_id)
                    & (m.FlashSaleCategory.category_id == m.FlashSaleItem.source_category_id))
                .where(m.FlashSale.end_at > utcnow(), m.FlashSaleItem.product_id.in_(products))
                .order_by(m.FlashSaleItem.id))
            if apply:
                stmt = stmt.with_for_update()
            for item, rule in (await session.execute(stmt)).all():
                price = _category_price(products[item.product_id], {
                    "discount_type": rule.discount_type, "discount_value": rule.discount_value})
                if price == item.flash_price:
                    continue
                changes.append({"item_id": item.id, "product_id": item.product_id,
                    "flash_sale_id": item.flash_sale_id, "old_price": str(item.flash_price),
                    "new_price": str(price), "sold": item.sold, "reserved": item.reserved})
                if apply:
                    item.flash_price = price
        return {"ok": True, "mode": "apply" if apply else "dry_run", "database": settings.database,
                "changed_items": len(changes), "changes": changes,
                "note": "Manual product overrides and existing order snapshots are preserved."}
    finally:
        await database.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = asyncio.run(repair(args.apply))
    except Exception as exc:
        result = {"ok": False, "error_type": type(exc).__name__}
    encoded = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
