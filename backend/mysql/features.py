"""Commerce-facing catalog rules shared by the new UI/API features.

Scheduled Flash Sale rows are the only source of flash pricing. Historical
product.flash_sale_price and manual badges remain in storage for import audits,
but never activate a sale in a public response.
"""
from __future__ import annotations

from decimal import Decimal
import re
from typing import Any
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy import func, or_, select

from . import models as m
from .api import products_dict, row_dict
from .base import utcnow
from .catalog import safe_values, validate_payload
from .commerce import integer, money


PAID_ORDER_STATUSES = frozenset({"paid", "processing", "shipped", "completed"})
NEW_ARRIVAL_CATEGORY_SLUG = "frame-new-arrival"
TRY_ON_PRODUCT_TYPES = ('frame', 'package')


def normalize_whatsapp_phone(raw: str, *, required: bool = False) -> str:
    raw = raw.strip()
    if raw and not re.fullmatch(r"\+?[0-9 ()-]+", raw):
        raise HTTPException(422, "Nomor WhatsApp harus berupa nomor telepon internasional")
    phone = re.sub(r"[^0-9]", "", raw)
    if phone.startswith("08"):
        phone = "62" + phone[1:]
    if (phone and not re.fullmatch(r"[1-9][0-9]{7,14}", phone)) or (required and not phone):
        raise HTTPException(422, "Isi nomor WhatsApp internasional, misalnya 6281234567890")
    return phone


def order_can_be_reviewed(order: m.Order) -> bool:
    return order.payment_status == "paid" and order.status in PAID_ORDER_STATUSES


def safe_web_url(value: Any, label: str = "URL", *, allow_http: bool = False) -> str:
    """Validate a browser URL, never fetch it from the application server."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise HTTPException(422, f"{label} tidak valid")
    if value != value.strip() or "\\" in value or any(ord(c) < 33 for c in value):
        raise HTTPException(422, f"{label} tidak valid")
    try:
        parsed = urlsplit(value)
    except ValueError:
        raise HTTPException(422, f"{label} tidak valid") from None
    if value.startswith("/") and not value.startswith("//") and not parsed.netloc:
        if parsed.path.startswith("/api/prescriptions/"):
            raise HTTPException(422, "File resep privat tidak boleh menjadi aset publik")
        return value
    if (parsed.scheme not in ({"https", "http"} if allow_http else {"https"})
            or not parsed.hostname or parsed.username is not None or parsed.password is not None):
        raise HTTPException(422, f"{label} harus path internal atau URL HTTPS")
    return value


def active_flash_conditions(now=None):
    now = now or utcnow()
    return (
        m.FlashSale.is_active.is_(True), m.FlashSale.start_at <= now, m.FlashSale.end_at > now,
        m.FlashSaleItem.is_active.is_(True),
        m.FlashSaleItem.quota > m.FlashSaleItem.sold + m.FlashSaleItem.reserved,
    )


def active_flash_product_ids(now=None):
    return select(m.FlashSaleItem.product_id).join(m.FlashSale).where(*active_flash_conditions(now))


def effective_catalog_price(now=None):
    """MySQL 5.7-compatible scalar subquery for current public price filters."""
    active = (select(m.FlashSaleItem.flash_price).join(m.FlashSale).where(
        m.FlashSaleItem.product_id == m.Product.id, *active_flash_conditions(now)
    ).order_by(m.FlashSaleItem.flash_price, m.FlashSaleItem.id).limit(1)
        .correlate(m.Product).scalar_subquery())
    return func.coalesce(active, m.Product.discount_price, m.Product.price)


def new_arrival_conditions(now=None):
    now = now or utcnow()
    return (m.Product.is_new_arrival.is_(True),
            or_(m.Product.new_arrival_until.is_(None), m.Product.new_arrival_until > now))


def published_try_on_conditions():
    return (m.VirtualTryOnAsset.status == "published", or_(m.VirtualTryOnAsset.variant_id.is_(None),
        m.VirtualTryOnAsset.variant_id.in_(select(m.ProductVariant.id).where(m.ProductVariant.is_active.is_(True)))))


async def public_products(session, products) -> list[dict]:
    products = list(products)
    data = await products_dict(session, products)
    if not products:
        return data
    now = utcnow()
    ids = [p.id for p in products]
    rows = (await session.execute(select(m.FlashSaleItem, m.FlashSale).join(m.FlashSale).where(
        m.FlashSaleItem.product_id.in_(ids), *active_flash_conditions(now)
    ).order_by(m.FlashSaleItem.flash_price, m.FlashSaleItem.id))).all()
    chosen = {}
    for item, campaign in rows:
        chosen.setdefault(item.product_id, (item, campaign))
    supported_ids = set((await session.scalars(select(m.VirtualTryOnAsset.product_id).where(
        m.VirtualTryOnAsset.product_id.in_(ids), *published_try_on_conditions()
    ))).all())
    for product, item in zip(products, data):
        item["flash_sale_price"] = None
        item["flash_sale_id"] = None
        item["flash_sale_item_id"] = None
        item["flash_sale_available"] = 0
        item["flash_sale_ends_at"] = None
        # These badges describe current business rules, not legacy CMS labels.
        item["badges"] = [b for b in item["badges"] if b.casefold() not in {
            "flashsale", "flash-sale", "flash_sale", "new", "newarrival", "new-arrival", "new_arrival"}]
        current = chosen.get(product.id)
        if current:
            sale_item, campaign = current
            item["discount_price"] = None
            item.update(flash_sale_price=float(sale_item.flash_price), flash_sale_id=campaign.id,
                        flash_sale_item_id=sale_item.id,
                        flash_sale_available=sale_item.quota - sale_item.sold - sale_item.reserved,
                        flash_sale_ends_at=campaign.end_at.isoformat())
            item["badges"].append("flashsale")
        item["is_new_arrival"] = bool(product.is_new_arrival and (
            product.new_arrival_until is None or product.new_arrival_until > now))
        if item["is_new_arrival"] and "new" not in item["badges"]:
            item["badges"].append("new")
        item["supports_try_on"] = product.product_type in TRY_ON_PRODUCT_TYPES and product.deleted_at is None and product.id in supported_ids
    return data


def _category_rules(payload: Any) -> list[dict]:
    if not isinstance(payload, list) or len(payload) > 100:
        raise HTTPException(422, "Maksimum 100 aturan kategori per Flash Sale")
    rules, seen = [], set()
    for raw in payload:
        if not isinstance(raw, dict):
            raise HTTPException(422, "Aturan kategori tidak valid")
        category_id = raw.get("category_id")
        if not isinstance(category_id, str) or not category_id or category_id in seen:
            raise HTTPException(422, "Kategori Flash Sale kosong atau duplikat")
        seen.add(category_id)
        discount_type = raw.get("discount_type", "percent")
        if discount_type not in {"percent", "nominal", "fixed_price"}:
            raise HTTPException(422, "Jenis diskon kategori tidak valid")
        discount = money(raw.get("discount_value", 0))
        if discount < 0 or (discount_type == "percent" and discount > 100):
            raise HTTPException(422, "Nilai diskon kategori tidak valid")
        descendants = raw.get("include_descendants", False)
        if not isinstance(descendants, bool):
            raise HTTPException(422, "include_descendants harus boolean")
        rules.append(dict(category_id=category_id, include_descendants=False,
                          discount_type=discount_type, discount_value=discount,
                          quota_per_product=integer(raw.get("quota_per_product", 0), "Kuota per produk")))
    return rules


def _category_price(product: m.Product, rule: dict) -> Decimal:
    # Flash Sale is exclusive: category discounts always start at the normal price.
    base = money(product.price)
    amount = money(rule["discount_value"])
    if rule["discount_type"] == "percent":
        result = base * (Decimal("100") - amount) / Decimal("100")
    elif rule["discount_type"] == "nominal":
        result = max(Decimal("0"), base - amount)
    else:
        result = amount
    if result > base:
        raise HTTPException(422, f"Harga Flash Sale kategori melebihi harga produk {product.name}")
    return money(result)


async def _category_candidates(session, rules: list[dict]) -> dict[str, list[dict]]:
    candidates: dict[str, list[dict]] = {}
    for rule in rules:
        category = await session.scalar(select(m.Category).where(
            m.Category.id == rule["category_id"], m.Category.is_active.is_(True)))
        if category is None:
            raise HTTPException(422, "Kategori Flash Sale tidak tersedia")
        if category.slug == NEW_ARRIVAL_CATEGORY_SLUG:
            condition = (m.Product.product_type == "frame", *new_arrival_conditions())
        else:
            ids = {category.id}
            condition = (or_(m.Product.primary_category_id.in_(ids), m.Product.id.in_(
                select(m.ProductCategory.product_id).where(m.ProductCategory.category_id.in_(ids)))),)
        pids = (await session.scalars(select(m.Product.id).where(
            m.Product.is_active.is_(True), *condition))).all()
        for pid in pids:
            candidates.setdefault(pid, []).append(rule)
    if len(candidates) > 5000:
        raise HTTPException(422, "Flash Sale maksimum 5000 produk; pecah kategori menjadi beberapa kampanye")
    return candidates


async def create_category_flash_sale(session, payload: dict) -> tuple[m.FlashSale, dict]:
    """Materialize category rules once, preserving a transparent source FK.

    The lowest category price wins for overlaps; explicit product rows override
    category rules. Refresh can synchronize category prices from the regular
    product price; quotas, counters, manual overrides and order snapshots survive.
    """
    from models import FlashSale as FlashSaleDTO

    data = validate_payload(FlashSaleDTO, {k: v for k, v in payload.items()
        if k in {"name", "start_at", "end_at", "is_active", "items"}})
    values = safe_values(m.FlashSale, data)
    if not data["name"].strip() or values["end_at"] <= values["start_at"]:
        raise HTTPException(422, "Nama dan rentang waktu Flash Sale tidak valid")
    rules = _category_rules(payload.get("category_rules", []))
    candidates = await _category_candidates(session, rules)
    manual = {}
    if len(data["items"]) > 5000:
        raise HTTPException(422, "Flash Sale maksimum 5000 produk")
    for item in data["items"]:
        pid = item.get("product_id")
        if not isinstance(pid, str) or not pid or pid in manual:
            raise HTTPException(422, "Produk Flash Sale kosong atau duplikat")
        price = money(item.get("flash_price"))
        if price < 0:
            raise HTTPException(422, "Harga Flash Sale tidak boleh negatif")
        manual[pid] = {"flash_price": price, "quota": integer(item.get("quota", 0), "Kuota")}
    product_ids = sorted(set(candidates) | set(manual))
    if len(product_ids) > 5000:
        raise HTTPException(422, "Flash Sale maksimum 5000 produk")
    products = (await session.scalars(select(m.Product).where(m.Product.id.in_(product_ids))
        .order_by(m.Product.id).with_for_update().execution_options(populate_existing=True))).all() if product_ids else []
    by_id = {p.id: p for p in products}
    if any(pid not in by_id or not by_id[pid].is_active for pid in manual):
        raise HTTPException(422, "Produk Flash Sale tidak ditemukan atau nonaktif")
    flash = m.FlashSale(**values)
    session.add(flash)
    await session.flush()
    session.add_all(m.FlashSaleCategory(flash_sale_id=flash.id, **rule) for rule in rules)
    await session.flush()
    for product in products:
        if not product.is_active:
            continue
        if product.id in manual:
            amount = manual[product.id]
            source_id = None
        else:
            rule = min(candidates[product.id], key=lambda r: (_category_price(product, r), r["category_id"]))
            source_id = rule["category_id"]
            amount = {"flash_price": _category_price(product, rule), "quota": rule["quota_per_product"]}
        session.add(m.FlashSaleItem(id=m.new_id(), flash_sale_id=flash.id, product_id=product.id,
                                   source_category_id=source_id, sold=0, reserved=0, **amount))
    await session.flush()
    return flash, {"materialized_products": len(products), "category_rule_count": len(rules),
                   "pricing_basis": "regular_product_price"}


async def refresh_category_flash_sale(session, flash_id: str, *, reprice_existing: bool = False) -> int:
    rules = [row_dict(r) for r in (await session.scalars(select(m.FlashSaleCategory).where(
        m.FlashSaleCategory.flash_sale_id == flash_id))).all()]
    candidates = await _category_candidates(session, rules)
    # Match checkout lock ordering: product rows before campaign/item rows.
    products = (await session.scalars(select(m.Product).where(m.Product.id.in_(candidates))
        .order_by(m.Product.id).with_for_update().execution_options(populate_existing=True))).all() if candidates else []
    flash = await session.scalar(select(m.FlashSale).where(m.FlashSale.id == flash_id).with_for_update())
    if flash is None:
        raise HTTPException(404, "Flash Sale tidak ditemukan")
    if flash.end_at <= utcnow():
        raise HTTPException(409, "Flash Sale telah berakhir")
    existing = {item.product_id: item for item in (await session.scalars(select(m.FlashSaleItem).where(
        m.FlashSaleItem.flash_sale_id == flash_id).order_by(m.FlashSaleItem.id).with_for_update())).all()}
    rules_by_id = {rule["category_id"]: rule for rule in rules}
    count = 0
    for product in products:
        if not product.is_active:
            continue
        if product.id in existing:
            item = existing[product.id]
            if reprice_existing and item.source_category_id in rules_by_id:
                price = _category_price(product, rules_by_id[item.source_category_id])
                if price != item.flash_price:
                    item.flash_price = price
            continue
        rule = min(candidates[product.id], key=lambda r: (_category_price(product, r), r["category_id"]))
        session.add(m.FlashSaleItem(id=m.new_id(), flash_sale_id=flash_id, product_id=product.id,
            source_category_id=rule["category_id"], flash_price=_category_price(product, rule),
            quota=rule["quota_per_product"], sold=0, reserved=0))
        count += 1
    await session.flush()
    return count
