"""Public CMS and lens endpoints using normalized MySQL tables."""
from __future__ import annotations
from decimal import Decimal
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import false, func, or_, select
from database import read_session, session_scope
from auth import current_user_optional
from models import User, ContactMessage as ContactMessageDTO
from mysql import models as m
from mysql.api import product_dict, products_dict, row_dict
from mysql.base import utcnow
from mysql.catalog import (article_dict, articles_dict, banner_dict, contact_dict,
                           knowledge_dict, knowledges_dict, safe_values, slugify, validate_payload)
from mysql.commerce import base_price
from mysql.features import active_flash_conditions

router = APIRouter(tags=["content"])


@router.get("/articles")
async def list_articles(q: Optional[str] = None, category_slug: Optional[str] = None,
                       page: int = Query(1, ge=1), limit: int = Query(12, ge=1, le=100)):
    async with read_session() as s:
        conditions = [m.Article.status == "published"]
        if q:
            conditions.append(m.Article.title.icontains(q, autoescape=True))
        if category_slug:
            cid = await s.scalar(select(m.ArticleCategory.id).where(m.ArticleCategory.slug == category_slug))
            conditions.append(m.Article.category_id == cid if cid else false())
        rows = (await s.scalars(select(m.Article).where(*conditions)
            .order_by(m.Article.published_at.desc(), m.Article.id)
            .offset((page - 1) * limit).limit(limit))).all()
        total = await s.scalar(select(func.count()).select_from(m.Article).where(*conditions))
        return {"articles": await articles_dict(s, rows, include_content=False),
                "total": total, "page": page, "limit": limit}


@router.get("/articles/categories")
async def list_article_categories():
    async with read_session() as s:
        rows = (await s.scalars(select(m.ArticleCategory).where(m.ArticleCategory.is_active.is_(True))
            .order_by(m.ArticleCategory.sort_order, m.ArticleCategory.id).limit(200))).all()
        return {"categories": [row_dict(c) for c in rows]}


@router.get("/articles/{slug}")
async def get_article(slug: str):
    async with session_scope() as s:
        article = await s.scalar(select(m.Article).where(m.Article.slug == slug,
            m.Article.status == "published").with_for_update())
        if article is None:
            raise HTTPException(404, "Artikel tidak ditemukan")
        article.view_count += 1
        await s.flush()
        related = (await s.scalars(select(m.Article).where(m.Article.status == "published",
            m.Article.category_id == article.category_id, m.Article.id != article.id)
            .order_by(m.Article.published_at.desc(), m.Article.id).limit(4))).all()
        return {"article": await article_dict(s, article),
                "related": await articles_dict(s, related, include_content=False)}


@router.get("/knowledge")
async def list_knowledge(type: Optional[str] = None):
    async with read_session() as s:
        stmt = select(m.ProductKnowledge).where(m.ProductKnowledge.status == "published")
        if type:
            stmt = stmt.where(m.ProductKnowledge.knowledge_type == type)
        rows = (await s.scalars(stmt.order_by(m.ProductKnowledge.sort_order, m.ProductKnowledge.id).limit(200))).all()
        return {"items": await knowledges_dict(s, rows)}


@router.get("/knowledge/{slug}")
async def get_knowledge(slug: str):
    async with read_session() as s:
        knowledge = await s.scalar(select(m.ProductKnowledge).where(
            m.ProductKnowledge.slug == slug, m.ProductKnowledge.status == "published"))
        if knowledge is None:
            raise HTTPException(404, "Knowledge tidak ditemukan")
        data = await knowledge_dict(s, knowledge)
        products = (await s.scalars(select(m.Product).join(m.ProductKnowledgeProduct,
            m.ProductKnowledgeProduct.product_id == m.Product.id).where(
            m.ProductKnowledgeProduct.knowledge_id == knowledge.id, m.Product.is_active.is_(True))
            .order_by(m.ProductKnowledgeProduct.sort_order, m.Product.id).limit(8))).all()
        fields = ("id", "name", "slug", "main_image", "price", "discount_price")
        return {"knowledge": data,
                "related_products": [{k: row_dict(p)[k] for k in fields} for p in products]}


@router.get("/lens/indexes")
async def list_lens_indexes():
    async with read_session() as s:
        rows = (await s.scalars(select(m.LensIndex).where(m.LensIndex.is_active.is_(True))
            .order_by(m.LensIndex.sort_order, m.LensIndex.id).limit(20))).all()
        return {"items": [row_dict(row) for row in rows]}


@router.get("/lens/options-for-frame/{frame_product_id}")
async def lens_options_for_frame(frame_product_id: str):
    async with read_session() as s:
        frame = await s.scalar(select(m.Product.id).where(m.Product.id == frame_product_id,
            m.Product.product_type == "frame", m.Product.is_active.is_(True)))
        if frame is None:
            raise HTTPException(404, "Frame tidak ditemukan")
        lenses = (await s.scalars(select(m.Product).where(m.Product.product_type == "lens",
            m.Product.is_active.is_(True)).order_by(m.Product.price, m.Product.id).limit(20))).all()
        indexes = (await s.scalars(select(m.LensIndex).where(m.LensIndex.is_active.is_(True))
            .order_by(m.LensIndex.sort_order, m.LensIndex.id).limit(20))).all()
        return {"lens_products": await products_dict(s, lenses), "lens_indexes": [row_dict(i) for i in indexes]}


@router.get("/lens/recommended-bundle/{frame_product_id}")
async def recommended_bundle(frame_product_id: str, variant_id: Optional[str] = None):
    async with read_session() as s:
        frame = await s.scalar(select(m.Product).where(m.Product.id == frame_product_id,
            m.Product.product_type == "frame", m.Product.is_active.is_(True)))
        if frame is None:
            raise HTTPException(404, "Frame tidak ditemukan")
        variants = (await s.scalars(select(m.ProductVariant).where(
            m.ProductVariant.product_id == frame.id, m.ProductVariant.is_active.is_(True)
        ).order_by(m.ProductVariant.sort_order, m.ProductVariant.id))).all()
        frame_variant = next((v for v in variants if v.id == variant_id), None) if variant_id else (variants[0] if variants else None)
        if variant_id and frame_variant is None:
            raise HTTPException(404, "Varian frame tidak tersedia")
        if frame_variant is None:
            return {"frame": {"id": frame.id, "name": frame.name,
                              "price": float(frame.discount_price if frame.discount_price is not None else frame.price),
                              "variant_id": None, "available_stock": 0}, "picks": []}
        flash_item = await s.scalar(select(m.FlashSaleItem).join(m.FlashSale).where(
            m.FlashSaleItem.product_id == frame.id, *active_flash_conditions()
        ).order_by(m.FlashSaleItem.flash_price, m.FlashSaleItem.id).limit(1))
        # A curated bundle adds exactly one frame. Flash pricing is product-wide
        # and requires one available quota, exactly as priced_cart() does.
        frame_price = flash_item.flash_price if flash_item is not None else base_price(frame, frame_variant)
        frame_stock = max(0, frame_variant.stock - frame_variant.reserved)
        frame_data = {"id": frame.id, "name": frame.name, "price": float(frame_price),
                      "variant_id": frame_variant.id, "available_stock": frame_stock}
        lenses = (await s.scalars(select(m.Product).where(m.Product.product_type == "lens",
            m.Product.is_active.is_(True)).order_by(m.Product.price, m.Product.id).limit(20))).all()
        lens_variants = {}
        if lenses:
            for variant in (await s.scalars(select(m.ProductVariant).where(
                m.ProductVariant.product_id.in_([lens.id for lens in lenses]), m.ProductVariant.is_active.is_(True)
            ).order_by(m.ProductVariant.product_id, m.ProductVariant.sort_order, m.ProductVariant.id))).all():
                # The same deterministic default used by resolve_variant(...,
                # lens=True). The exact SKU is returned and posted by the UI.
                lens_variants.setdefault(variant.product_id, variant)
        lenses = [lens for lens in lenses if lens.id in lens_variants]
        indexes = (await s.scalars(select(m.LensIndex).where(m.LensIndex.is_active.is_(True))
            .order_by(m.LensIndex.additional_price, m.LensIndex.id).limit(20))).all()
        if not lenses or not indexes:
            return {"frame": frame_data, "picks": []}
        lenses.sort(key=lambda lens: (base_price(lens, lens_variants[lens.id]), lens.id))
        def pick(tier, label, tagline, lens, index):
            lens_variant = lens_variants[lens.id]
            # Commerce applies lens-component pricing plus the selected index;
            # a standalone lens flash sale is not applied to a bundle component.
            lens_price = base_price(lens, lens_variant)
            total = frame_price + lens_price + index.additional_price
            original = (frame_variant.price_override if frame_variant.price_override is not None else frame.price)
            original += (lens_variant.price_override if lens_variant.price_override is not None else lens.price)
            original += index.additional_price
            available_stock = min(frame_stock, max(0, lens_variant.stock - lens_variant.reserved))
            return {"tier": tier, "label": label, "tagline": tagline,
                "frame_variant_id": frame_variant.id, "lens_variant_id": lens_variant.id,
                "lens_product_id": lens.id, "lens_product_name": lens.name,
                "lens_product_image": lens.main_image, "lens_index_id": index.id,
                "lens_index_name": index.name, "lens_index_description": index.description,
                "frame_price": float(frame_price), "lens_price": float(lens_price),
                "lens_index_price": float(index.additional_price), "bundle_total": float(total),
                "available_stock": available_stock, "available": available_stock >= 1,
                "original_total": float(original), "savings": float(max(Decimal("0"), original - total))}
        picks = [
            pick("basic", "Paket Hemat", "Lensa dasar untuk pemakaian harian", lenses[0], indexes[0]),
            pick("popular", "Paket Populer", "Pilihan paling laris — perlindungan blue cut untuk mata layar",
                 lenses[len(lenses) // 2], indexes[min(1, len(indexes) - 1)]),
            pick("premium", "Paket Premium", "Lensa premium + index tipis untuk tampilan estetis", lenses[-1], indexes[-1]),
        ]
        return {"frame": frame_data, "picks": picks}


@router.get("/faqs")
async def list_faqs():
    async with read_session() as s:
        categories = (await s.scalars(select(m.FAQCategory).where(m.FAQCategory.is_active.is_(True))
            .order_by(m.FAQCategory.sort_order, m.FAQCategory.id).limit(50))).all()
        items = (await s.scalars(select(m.FAQ).where(m.FAQ.is_active.is_(True))
            .order_by(m.FAQ.sort_order, m.FAQ.id).limit(200))).all()
        return {"categories": [row_dict(c) for c in categories], "items": [row_dict(i) for i in items]}


@router.get("/pages/{slug}")
async def get_page(slug: str):
    async with read_session() as s:
        page = await s.scalar(select(m.CMSPage).where(m.CMSPage.slug == slug, m.CMSPage.status == "published"))
        if page is None:
            raise HTTPException(404, "Halaman tidak ditemukan")
        return {"page": row_dict(page)}


@router.get("/contact/info")
async def contact_info():
    async with read_session() as s:
        contact = await s.scalar(select(m.ContactSetting).where(m.ContactSetting.singleton_key == 1))
        return {"contact": await contact_dict(s, contact)}


@router.post("/contact/send")
async def contact_send(payload: Dict[str, Any], user: User = Depends(current_user_optional)):
    if any(not payload.get(field) for field in ("name", "email", "message")):
        raise HTTPException(400, "Nama, email, dan pesan wajib diisi")
    # Public callers cannot choose status, timestamps or another message's ID.
    data = validate_payload(ContactMessageDTO, {k: payload[k] for k in
        ("name", "email", "phone", "subject", "message") if k in payload})
    async with session_scope() as s:
        s.add(m.ContactMessage(**safe_values(m.ContactMessage, data)))
    return {"ok": True}


@router.get("/banners")
async def list_banners(position: Optional[str] = None, device: Optional[str] = "all"):
    if device not in (None, "all", "desktop", "mobile"):
        raise HTTPException(422, "Device tidak valid")
    async with read_session() as s:
        now = utcnow()
        stmt = select(m.Banner).where(m.Banner.is_active.is_(True),
            or_(m.Banner.start_at.is_(None), m.Banner.start_at <= now),
            or_(m.Banner.end_at.is_(None), m.Banner.end_at > now))
        if position:
            stmt = stmt.where(m.Banner.position == position)
        if device and device != "all":
            stmt = stmt.where(m.Banner.target_device.in_(("all", device)))
        banners = (await s.scalars(stmt.order_by(m.Banner.sort_order, m.Banner.id).limit(30))).all()
        return {"banners": [banner_dict(b) for b in banners]}
