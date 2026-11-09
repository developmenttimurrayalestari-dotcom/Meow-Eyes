"""Catalog API backed by explicit MySQL-compatible relational queries."""
from __future__ import annotations
from decimal import Decimal
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import false, func, or_, select
from database import read_session
from mysql import models as m
from mysql.api import product_dict, products_dict, row_dict
from mysql.base import utcnow
from mysql.catalog import (banner_dict, category_breadcrumb, category_descendants,
                           flash_dict, reviews_dict, slugify)
from mysql.features import (NEW_ARRIVAL_CATEGORY_SLUG, active_flash_conditions,
                            active_flash_product_ids, effective_catalog_price, new_arrival_conditions, public_products)

router = APIRouter(tags=["catalog"])


@router.get("/categories")
async def list_categories(is_active: Optional[bool] = True):
    async with read_session() as s:
        stmt = select(m.Category)
        if is_active is not None:
            stmt = stmt.where(m.Category.is_active == is_active)
        rows = (await s.scalars(stmt.order_by(m.Category.sort_order, m.Category.id))).all()
        return {"categories": [row_dict(row) for row in rows]}


@router.get("/categories/tree")
async def category_tree():
    async with read_session() as s:
        rows = (await s.scalars(select(m.Category).where(m.Category.is_active.is_(True))
            .order_by(m.Category.sort_order, m.Category.id))).all()
        by_id = {c.id: {**row_dict(c), "children": []} for c in rows}
        roots = []
        for c in rows:
            if c.parent_id and c.parent_id in by_id:
                by_id[c.parent_id]["children"].append(by_id[c.id])
            else:
                roots.append(by_id[c.id])
        return {"tree": roots}


@router.get("/categories/{slug}")
async def get_category(slug: str):
    async with read_session() as s:
        category = await s.scalar(select(m.Category).where(m.Category.slug == slug))
        if category is None:
            raise HTTPException(404, "Kategori tidak ditemukan")
        return {"category": row_dict(category), "breadcrumb": await category_breadcrumb(s, category.id)}


@router.get("/brands")
async def list_brands():
    async with read_session() as s:
        rows = (await s.scalars(select(m.Brand).where(m.Brand.is_active.is_(True))
            .order_by(m.Brand.name, m.Brand.id))).all()
        return {"brands": [row_dict(row) for row in rows]}


def _to_card(p: Dict[str, Any]) -> Dict[str, Any]:
    fields = ("id", "name", "slug", "sku", "main_image", "price", "discount_price",
              "flash_sale_price", "badges", "rating_avg", "rating_count", "sold_count",
              "brand_id", "segments", "product_type", "category_ids", "is_new_arrival",
              "new_arrival_until", "supports_try_on", "flash_sale_id", "flash_sale_item_id",
              "flash_sale_available", "flash_sale_ends_at")
    return {field: p.get(field) for field in fields}


@router.get("/products")
async def list_products(
    q: Optional[str] = None, category_id: Optional[str] = None,
    category_slug: Optional[str] = None, brand_id: Optional[str] = None,
    product_type: Optional[str] = None, segment: Optional[str] = None,
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    badge: Optional[str] = None, sort: str = "newest", new_arrival: Optional[bool] = None,
    page: int = Query(1, ge=1), limit: int = Query(15, ge=1, le=100),
):
    async with read_session() as s:
        conditions = [m.Product.is_active.is_(True)]
        if q:
            conditions.append(m.Product.name.icontains(q, autoescape=True))
        if category_id:
            category = await s.scalar(select(m.Category).where(m.Category.id == category_id,
                m.Category.is_active.is_(True)))
            if category and category.slug == NEW_ARRIVAL_CATEGORY_SLUG:
                conditions.extend([m.Product.product_type == "frame", *new_arrival_conditions()])
            else:
                conditions.append(m.Product.id.in_(select(m.ProductCategory.product_id)
                    .where(m.ProductCategory.category_id == category_id)) if category else false())
        if category_slug:
            category = await s.scalar(select(m.Category).where(m.Category.slug == category_slug,
                m.Category.is_active.is_(True)))
            if category_slug == NEW_ARRIVAL_CATEGORY_SLUG:
                conditions.extend([m.Product.product_type == "frame", *new_arrival_conditions()])
            elif category is None:
                conditions.append(false())
            else:
                ids = await category_descendants(s, category.id)
                conditions.append(m.Product.id.in_(select(m.ProductCategory.product_id)
                    .where(m.ProductCategory.category_id.in_(ids))))
        if brand_id:
            conditions.append(m.Product.brand_id == brand_id)
        if product_type:
            conditions.append(m.Product.product_type == product_type)
        if segment:
            conditions.append(m.Product.id.in_(select(m.ProductSegment.product_id)
                .where(m.ProductSegment.segment == segment)))
        if new_arrival is True:
            conditions.extend(new_arrival_conditions())
        if badge in {"flashsale", "flash-sale", "flash_sale"}:
            conditions.append(m.Product.id.in_(active_flash_product_ids()))
        elif badge:
            conditions.append(m.Product.id.in_(select(m.ProductBadge.product_id)
                .where(m.ProductBadge.badge == badge)))
        public_price = effective_catalog_price()
        if min_price is not None:
            conditions.append(public_price >= min_price)
        if max_price is not None:
            conditions.append(public_price <= max_price)
        sort_columns = {
            "newest": m.Product.created_at.desc(), "bestseller": m.Product.sold_count.desc(),
            "price_asc": public_price.asc(), "price_desc": public_price.desc(),
            "rating": m.Product.rating_avg.desc(), "discount": m.Product.discount_price.asc(),
        }
        stmt = select(m.Product).where(*conditions).order_by(
            sort_columns.get(sort, sort_columns["newest"]), m.Product.id)
        rows = (await s.scalars(stmt.offset((page - 1) * limit).limit(limit))).all()
        total = await s.scalar(select(func.count()).select_from(m.Product).where(*conditions))
        cards = [_to_card(item) for item in await public_products(s, rows)]
        return {"products": cards, "total": total, "page": page, "limit": limit}


@router.get("/products/search-suggest")
async def search_suggest(q: str = Query(min_length=1, max_length=64)):
    async with read_session() as s:
        rows = (await s.scalars(select(m.Product).where(m.Product.is_active.is_(True),
            m.Product.name.icontains(q, autoescape=True)).order_by(m.Product.name, m.Product.id).limit(8))).all()
        fields = ("id", "name", "slug", "main_image", "price")
        return {"items": [{key: row_dict(row)[key] for key in fields} for row in rows]}


@router.get("/products/{slug}")
async def product_detail(slug: str):
    async with read_session() as s:
        product = await s.scalar(select(m.Product).where(m.Product.slug == slug, m.Product.is_active.is_(True)))
        if product is None:
            raise HTTPException(404, "Produk tidak ditemukan")
        related = []
        if product.primary_category_id:
            rows = (await s.scalars(select(m.Product).where(
                m.Product.primary_category_id == product.primary_category_id,
                m.Product.id != product.id, m.Product.is_active.is_(True))
                .order_by(m.Product.created_at.desc(), m.Product.id).limit(8))).all()
            related = [_to_card(item) for item in await public_products(s, rows)]
        brand = await s.get(m.Brand, product.brand_id) if product.brand_id else None
        reviews = (await s.scalars(select(m.ProductReview).where(
            m.ProductReview.product_id == product.id, m.ProductReview.status == "approved")
            .order_by(m.ProductReview.created_at.desc(), m.ProductReview.id).limit(10))).all()
        now = utcnow()
        flash = await s.scalar(select(m.FlashSale).join(m.FlashSaleItem,
            m.FlashSaleItem.flash_sale_id == m.FlashSale.id).where(
            *active_flash_conditions(now), m.FlashSaleItem.product_id == product.id)
            .order_by(m.FlashSaleItem.flash_price, m.FlashSaleItem.id).limit(1))
        flash_data = await flash_dict(s, flash) if flash else None
        flash_item = next((it for it in flash_data["items"] if it["product_id"] == product.id), None) if flash_data else None
        return {"product": (await public_products(s, [product]))[0],
                "breadcrumb": await category_breadcrumb(s, product.primary_category_id),
                "brand": row_dict(brand) if brand else None, "related": related,
                "reviews": await reviews_dict(s, reviews), "flash_sale": flash_data, "flash_item": flash_item}


@router.get("/flash-sales/active")
async def active_flash_sales():
    async with read_session() as s:
        now = utcnow()
        flashes = (await s.scalars(select(m.FlashSale).where(m.FlashSale.is_active.is_(True),
            m.FlashSale.start_at <= now, m.FlashSale.end_at > now)
            .order_by(m.FlashSale.start_at, m.FlashSale.id).limit(20))).all()
        out = []
        for flash in flashes:
            data = await flash_dict(s, flash)
            data["items"] = [item for item in data["items"] if item["available_quota"] > 0]
            pids = [item["product_id"] for item in data["items"]]
            products = (await s.scalars(select(m.Product).where(m.Product.id.in_(pids),
                m.Product.is_active.is_(True)))).all() if pids else []
            cards = {p["id"]: _to_card(p) for p in await public_products(s, products)}
            data["items"] = [{**cards[item["product_id"]], "flash_price": item["flash_price"],
                "flash_sale_price": item["flash_price"], "flash_sale_id": flash.id,
                "flash_sale_item_id": item["id"], "flash_sale_available": item["available_quota"],
                "flash_sale_ends_at": flash.end_at.isoformat(), "quota": item["quota"], "sold": item["sold"],
                "reserved": item["reserved"], "available_quota": item["available_quota"]}
                for item in data["items"] if item["product_id"] in cards
                and cards[item["product_id"]]["flash_sale_item_id"] == item["id"]]
            if data["items"]:
                out.append(data)
        return {"flash_sales": out}


@router.get("/homepage")
async def homepage():
    async with read_session() as s:
        base = select(m.Product).where(m.Product.is_active.is_(True))
        best = (await s.scalars(base.order_by(m.Product.sold_count.desc(), m.Product.id).limit(8))).all()
        newest = (await s.scalars(base.order_by(m.Product.created_at.desc(), m.Product.id).limit(8))).all()
        discounted = (await s.scalars(base.where(m.Product.discount_price.is_not(None))
            .order_by(m.Product.id).limit(8))).all()
        categories = (await s.scalars(select(m.Category).where(m.Category.is_active.is_(True),
            m.Category.is_featured.is_(True)).order_by(m.Category.sort_order, m.Category.id).limit(8))).all()
        brands = (await s.scalars(select(m.Brand).where(m.Brand.is_active.is_(True))
            .order_by(m.Brand.name, m.Brand.id).limit(8))).all()
        now = utcnow()
        banners = (await s.scalars(select(m.Banner).where(m.Banner.is_active.is_(True),
            or_(m.Banner.start_at.is_(None), m.Banner.start_at <= now),
            or_(m.Banner.end_at.is_(None), m.Banner.end_at > now))
            .order_by(m.Banner.sort_order, m.Banner.id).limit(10))).all()
        return {
            "bestsellers": [_to_card(p) for p in await public_products(s, best)],
            "newest": [_to_card(p) for p in await public_products(s, newest)],
            "discounted": [_to_card(p) for p in await public_products(s, discounted)],
            "categories": [row_dict(c) for c in categories],
            "brands": [row_dict(b) for b in brands], "banners": [banner_dict(b) for b in banners],
        }
