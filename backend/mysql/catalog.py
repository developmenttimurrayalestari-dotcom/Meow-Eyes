"""Relational catalog/content operations shared by the existing API routes.

Queries use SQLAlchemy columns and joins. These helpers serialize normalized
child tables into the existing HTTP response shapes; they do not emulate a
document database or persist opaque copies of products or content.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Any, Iterable
from urllib.parse import urlsplit

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models as m
from .api import row_dict, values_for
from .base import utcnow


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "item"


def validate_payload(dto: type, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return dto.model_validate(payload).model_dump()
    except ValidationError as exc:
        raise HTTPException(422, detail=[
            {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
            for e in exc.errors(include_input=False, include_url=False)
        ]) from None


def safe_values(model: type, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        values = values_for(model, payload)
    except (ValueError, TypeError, InvalidOperation):
        raise HTTPException(422, "Nilai kolom, angka, atau tanggal tidak valid") from None
    for name, value in values.items():
        column = model.__table__.c[name]
        if value is None and not column.nullable:
            raise HTTPException(422, f"{name} tidak boleh kosong")
        if isinstance(value, Decimal) and not value.is_finite():
            raise HTTPException(422, f"{name} harus berupa angka terbatas")
        length = getattr(column.type, "length", None)
        if length and isinstance(value, str) and len(value) > length:
            raise HTTPException(422, f"{name} melebihi {length} karakter")
    return values


def apply_fields(obj: Any, payload: dict[str, Any], allowed: Iterable[str]) -> None:
    values = safe_values(type(obj), {k: v for k, v in payload.items() if k in allowed})
    for name, value in values.items():
        setattr(obj, name, value)
    if hasattr(type(obj), "updated_at"):
        obj.updated_at = utcnow()


async def get_or_404(session: AsyncSession, model: type, key: str,
                     message: str = "Data tidak ditemukan", *, lock: bool = False):
    pk = list(model.__table__.primary_key.columns)[0]
    stmt = select(model).where(pk == key)
    if lock:
        stmt = stmt.with_for_update()
    row = (await session.scalars(stmt)).one_or_none()
    if row is None:
        raise HTTPException(404, message)
    return row


async def unique_slug(session: AsyncSession, model: type, value: str) -> str:
    value = value[:180]
    if await session.scalar(select(model.id).where(model.slug == value)) is not None:
        return value + "-" + m.new_id()[:8]
    return value


def strings(values: Any, *, limit: int = 500, max_length: int | None = None,
            unique: bool = False) -> list[str]:
    if not isinstance(values, list) or len(values) > limit:
        raise HTTPException(422, "Daftar tidak valid atau terlalu panjang")
    if any(not isinstance(x, str) or not x.strip() or
           (max_length is not None and len(x) > max_length) for x in values):
        raise HTTPException(422, "Daftar harus berisi teks yang tidak kosong")
    # Tags, badges and segments use the database's case-insensitive collation.
    if unique:
        seen: set[str] = set()
        out = []
        for item in values:
            if item.casefold() not in seen:
                out.append(item)
                seen.add(item.casefold())
        return out
    return values


PRODUCT_FIELDS = frozenset({
    "name", "slug", "sku", "description", "spec", "product_type", "primary_category_id",
    "brand_id", "price", "discount_price", "flash_sale_price", "weight_gram", "dimension",
    "main_image", "min_stock_alert", "is_active", "seo_title", "seo_description",
    "is_new_arrival", "new_arrival_until",
})
VARIANT_FIELDS = frozenset({"color", "color_hex", "size", "lens_type", "sku", "price_override", "is_active"})


async def write_product(session: AsyncSession, payload: dict[str, Any], *,
                        product: m.Product | None = None,
                        admin_id: str | None = None) -> m.Product:
    """Write product and children in the caller's transaction.

    Existing variant identities and reservation counters survive CMS edits and
    spreadsheet imports. Omitted variants are deactivated, never recreated or
    hard-deleted out from underneath historical order items.
    """
    creating = product is None
    if product is None:
        product = m.Product(id=m.new_id(), **safe_values(
            m.Product, {k: v for k, v in payload.items() if k in PRODUCT_FIELDS}))
        session.add(product)
    else:
        product = await get_or_404(session, m.Product, product.id, lock=True)
        apply_fields(product, payload, PRODUCT_FIELDS)
    for field in ("price", "discount_price", "flash_sale_price"):
        value = getattr(product, field)
        if value is not None and value < 0:
            raise HTTPException(422, f"{field} tidak boleh negatif")
    for field in ("weight_gram", "min_stock_alert"):
        value = getattr(product, field)
        if value is not None and value < 0:
            raise HTTPException(422, f"{field} tidak boleh negatif")
    await session.flush()

    if "category_ids" in payload or "primary_category_id" in payload:
        if "category_ids" in payload:
            category_ids = list(dict.fromkeys(strings(payload["category_ids"], max_length=64)))
        else:
            category_ids = list((await session.scalars(select(m.ProductCategory.category_id)
                .where(m.ProductCategory.product_id == product.id))).all())
        if product.primary_category_id and product.primary_category_id not in category_ids:
            category_ids.append(product.primary_category_id)
        found = set((await session.scalars(select(m.Category.id)
            .where(m.Category.id.in_(category_ids)))).all()) if category_ids else set()
        if found != set(category_ids):
            raise HTTPException(422, "Kategori produk tidak ditemukan")
        await session.execute(delete(m.ProductCategory).where(m.ProductCategory.product_id == product.id))
        session.add_all([m.ProductCategory(product_id=product.id, category_id=cid) for cid in category_ids])

    for field, model, column in (
        ("segments", m.ProductSegment, "segment"),
        ("badges", m.ProductBadge, "badge"),
    ):
        if field in payload:
            entries = strings(payload[field], max_length=64, unique=True)
            await session.execute(delete(model).where(model.product_id == product.id))
            session.add_all([model(product_id=product.id, **{column: item}) for item in entries])
    if "gallery" in payload:
        gallery = strings(payload["gallery"], limit=100)
        await session.execute(delete(m.ProductImage).where(m.ProductImage.product_id == product.id))
        session.add_all([m.ProductImage(product_id=product.id, sort_order=i, image_url=url)
                         for i, url in enumerate(gallery)])

    if "variants" in payload:
        variants = payload["variants"]
        if not isinstance(variants, list) or len(variants) > 500:
            raise HTTPException(422, "Daftar varian tidak valid")
        existing = list((await session.scalars(select(m.ProductVariant)
            .where(m.ProductVariant.product_id == product.id)
            .order_by(m.ProductVariant.id).with_for_update())).all())
        by_id = {v.id: v for v in existing}
        by_sku = {v.sku.casefold(): v for v in existing}
        seen_ids: set[str] = set()
        seen_skus: set[str] = set()
        for i, raw in enumerate(variants):
            if not isinstance(raw, dict) or not isinstance(raw.get("sku"), str) or not raw["sku"].strip():
                raise HTTPException(422, "SKU varian wajib diisi")
            sku_key = raw["sku"].casefold()
            if sku_key in seen_skus:
                raise HTTPException(422, "SKU varian duplikat dalam produk")
            seen_skus.add(sku_key)
            if raw.get("id") and raw["id"] not in by_id:
                other = await session.get(m.ProductVariant, raw["id"])
                if other is not None and other.product_id != product.id:
                    raise HTTPException(422, "Varian berasal dari produk lain")
            variant = by_id.get(raw.get("id")) or by_sku.get(sku_key)
            if variant is None:
                if raw.get("id") and await session.get(m.ProductVariant, raw["id"]) is not None:
                    raise HTTPException(422, "Varian berasal dari produk lain")
                variant = m.ProductVariant(id=raw.get("id") or m.new_id(), product_id=product.id,
                                           stock=0, reserved=0, sort_order=i, is_active=True)
                session.add(variant)
            if variant.id in seen_ids:
                raise HTTPException(422, "Varian duplikat dalam produk")
            seen_ids.add(variant.id)
            if raw.get("reserved", 0) not in (0, variant.reserved):
                raise HTTPException(422, "Stok reserved dikelola oleh transaksi checkout")
            before_stock = variant.stock or 0
            apply_fields(variant, raw, VARIANT_FIELDS)
            if "stock" in raw:
                try:
                    stock = int(raw["stock"])
                except (ValueError, TypeError):
                    raise HTTPException(422, "Stok harus berupa bilangan bulat") from None
                if isinstance(raw["stock"], bool) or Decimal(str(raw["stock"])) != stock:
                    raise HTTPException(422, "Stok harus berupa bilangan bulat")
                if stock < (variant.reserved or 0):
                    raise HTTPException(409, "Stok tidak boleh kurang dari stok reserved")
                variant.stock = stock
            if variant.price_override is not None and variant.price_override < 0:
                raise HTTPException(422, "Harga varian tidak boleh negatif")
            variant.sort_order = i
            await session.flush()
            delta = variant.stock - before_stock
            if delta and admin_id:
                session.add(m.StockMovement(
                    id=m.new_id(), product_id=product.id, variant_id=variant.id,
                    type="stock_in" if delta > 0 else "stock_out", quantity=abs(delta), delta=delta,
                    reserved_delta=0, stock_after=variant.stock, reserved_after=variant.reserved,
                    note="CMS product creation" if creating else "CMS product update/import",
                    admin_id=admin_id,
                ))
        for variant in existing:
            if variant.id not in seen_ids:
                variant.is_active = False
    await session.flush()
    return product


async def category_breadcrumb(session: AsyncSession, category_id: str | None) -> list[dict]:
    chain: list[dict] = []
    seen: set[str] = set()
    while category_id and category_id not in seen:
        seen.add(category_id)
        category = await session.get(m.Category, category_id)
        if category is None:
            break
        chain.insert(0, row_dict(category))
        category_id = category.parent_id
    return chain


async def category_descendants(session: AsyncSession, category_id: str) -> set[str]:
    rows = (await session.execute(select(m.Category.id, m.Category.parent_id))).all()
    children: dict[str, list[str]] = {}
    for cid, parent in rows:
        children.setdefault(parent, []).append(cid)
    found: set[str] = set()
    pending = [category_id]
    while pending:
        current = pending.pop()
        if current in found:
            continue
        found.add(current)
        pending.extend(children.get(current, []))
    return found


async def articles_dict(session: AsyncSession, articles: Iterable[m.Article], *,
                        include_content: bool = True) -> list[dict]:
    articles = list(articles)
    tags: dict[str, list[str]] = {a.id: [] for a in articles}
    if tags:
        rows = await session.execute(select(m.ArticleTag.article_id, m.ArticleTag.tag)
            .where(m.ArticleTag.article_id.in_(tags)).order_by(m.ArticleTag.sort_order, m.ArticleTag.tag))
        for aid, tag in rows:
            tags[aid].append(tag)
    out = []
    for article in articles:
        item = row_dict(article)
        item["tags"] = tags[article.id]
        if not include_content:
            item.pop("content", None)
        out.append(item)
    return out


async def article_dict(session: AsyncSession, article: m.Article) -> dict:
    return (await articles_dict(session, [article]))[0]


async def replace_article_tags(session: AsyncSession, article_id: str, tags: list[str]) -> None:
    tags = strings(tags, max_length=128, unique=True)
    await session.execute(delete(m.ArticleTag).where(m.ArticleTag.article_id == article_id))
    session.add_all([m.ArticleTag(article_id=article_id, tag=tag, sort_order=i)
                     for i, tag in enumerate(tags)])
    await session.flush()


async def knowledges_dict(session: AsyncSession, knowledge_rows: Iterable[m.ProductKnowledge]) -> list[dict]:
    knowledge_rows = list(knowledge_rows)
    if not knowledge_rows:
        return []
    by_id = {knowledge.id: {**row_dict(knowledge), "is_published": knowledge.status == "published",
              "pros": [], "cons": [], "related_product_ids": []} for knowledge in knowledge_rows}
    bullets = await session.scalars(select(m.ProductKnowledgeBullet)
        .where(m.ProductKnowledgeBullet.knowledge_id.in_(by_id))
        .order_by(m.ProductKnowledgeBullet.knowledge_id, m.ProductKnowledgeBullet.kind,
                  m.ProductKnowledgeBullet.sort_order))
    for bullet in bullets:
        by_id[bullet.knowledge_id]["pros" if bullet.kind == "pro" else "cons"].append(bullet.body)
    links = await session.execute(select(m.ProductKnowledgeProduct.knowledge_id, m.ProductKnowledgeProduct.product_id)
        .where(m.ProductKnowledgeProduct.knowledge_id.in_(by_id))
        .order_by(m.ProductKnowledgeProduct.knowledge_id, m.ProductKnowledgeProduct.sort_order,
                  m.ProductKnowledgeProduct.product_id))
    for knowledge_id, product_id in links:
        by_id[knowledge_id]["related_product_ids"].append(product_id)
    return [by_id[knowledge.id] for knowledge in knowledge_rows]


async def knowledge_dict(session: AsyncSession, knowledge: m.ProductKnowledge) -> dict:
    return (await knowledges_dict(session, [knowledge]))[0]


async def replace_knowledge_children(session: AsyncSession, kid: str, payload: dict) -> None:
    for field, kind in (("pros", "pro"), ("cons", "con")):
        if field in payload:
            entries = strings(payload[field])
            await session.execute(delete(m.ProductKnowledgeBullet).where(
                m.ProductKnowledgeBullet.knowledge_id == kid, m.ProductKnowledgeBullet.kind == kind))
            session.add_all([m.ProductKnowledgeBullet(knowledge_id=kid, kind=kind, sort_order=i, body=body)
                             for i, body in enumerate(entries)])
    if "related_product_ids" in payload:
        pids = list(dict.fromkeys(strings(payload["related_product_ids"], max_length=64)))
        found = set((await session.scalars(select(m.Product.id).where(m.Product.id.in_(pids)))).all()) if pids else set()
        if found != set(pids):
            raise HTTPException(422, "Produk terkait tidak ditemukan")
        await session.execute(delete(m.ProductKnowledgeProduct).where(m.ProductKnowledgeProduct.knowledge_id == kid))
        session.add_all([m.ProductKnowledgeProduct(knowledge_id=kid, product_id=pid, sort_order=i)
                         for i, pid in enumerate(pids)])
    await session.flush()


async def reviews_dict(session: AsyncSession, reviews: Iterable[m.ProductReview]) -> list[dict]:
    reviews = list(reviews)
    images: dict[str, list[str]] = {r.id: [] for r in reviews}
    if images:
        rows = await session.execute(select(m.ProductReviewImage.review_id, m.ProductReviewImage.image_url)
            .where(m.ProductReviewImage.review_id.in_(images)).order_by(m.ProductReviewImage.sort_order))
        for rid, url in rows:
            images[rid].append(url)
    return [{**row_dict(r), "is_approved": r.status == "approved", "images": images[r.id]} for r in reviews]


async def flash_dict(session: AsyncSession, flash: m.FlashSale, *, include_inactive: bool = False) -> dict:
    stmt = select(m.FlashSaleItem).where(m.FlashSaleItem.flash_sale_id == flash.id)
    if not include_inactive:
        stmt = stmt.where(m.FlashSaleItem.is_active.is_(True))
    items = (await session.scalars(stmt.order_by(m.FlashSaleItem.id))).all()
    rules = (await session.execute(select(m.FlashSaleCategory, m.Category.name).join(m.Category)
        .where(m.FlashSaleCategory.flash_sale_id == flash.id).order_by(m.FlashSaleCategory.category_id))).all()
    return {**row_dict(flash), "items": [{**row_dict(item), "available_quota": item.quota - item.sold - item.reserved}
            for item in items], "category_rules": [{**row_dict(rule), "category_name": name} for rule, name in rules]}


_BANNER_LINK_COLUMNS = {
    "product": "link_product_id", "category": "link_category_id",
    "article": "link_article_id", "flash_sale": "link_flash_sale_id",
}


def banner_dict(banner: m.Banner) -> dict:
    item = row_dict(banner)
    item["reference_id"] = item.get(_BANNER_LINK_COLUMNS.get(banner.link_type, ""))
    item["image"] = banner.image_desktop
    item["link"] = banner.link_url
    return item


def banner_values(payload: dict) -> dict:
    """Map the existing V1/V2 contract to one typed banner table."""
    values = dict(payload)
    if "image" in values and "image_desktop" not in values:
        values["image_desktop"] = values["image"]
    if "link" in values and "link_url" not in values:
        values["link_url"] = values["link"]
    if "link_url" in values:
        url = values["link_url"] or "/"
        if not isinstance(url, str) or len(url) > 2048:
            raise HTTPException(422, "URL banner tidak valid")
        try:
            parsed = urlsplit(url)
        except ValueError:
            raise HTTPException(422, "URL banner tidak valid") from None
        if not url.startswith("/") and (parsed.scheme not in {"http", "https"} or not parsed.hostname
                                       or parsed.username is not None or parsed.password is not None):
            raise HTTPException(422, "URL banner harus path internal atau URL HTTP/HTTPS")
        if url.startswith("//") or "\\" in url or url != url.strip() or any(ord(c) < 32 for c in url):
            raise HTTPException(422, "URL banner tidak valid")
        values["link_url"] = url
    if "reference_id" in values or "link_type" in values:
        for col in _BANNER_LINK_COLUMNS.values():
            values[col] = None
        col = _BANNER_LINK_COLUMNS.get(values.get("link_type"))
        if col:
            values[col] = values.get("reference_id") or None
    return safe_values(m.Banner, values)


async def contact_dict(session: AsyncSession, setting: m.ContactSetting | None) -> dict:
    if setting is None:
        return {}
    item = row_dict(setting)
    whatsapp = await session.get(m.WhatsAppSetting, 1)
    item["whatsapp"] = whatsapp.phone if whatsapp else ""
    return item
