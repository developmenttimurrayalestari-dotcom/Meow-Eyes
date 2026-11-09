"""CMS, moderation, staff and product import routes on normalized MySQL tables."""
from __future__ import annotations
import json
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from sqlalchemy import delete, func, select
from database import read_session, session_scope
from auth import current_admin, require_permission
from models import (User, Article as ArticleDTO, ArticleCategory as ArticleCategoryDTO,
                    ProductKnowledge as KnowledgeDTO, FAQItem, FAQCategory as FAQCategoryDTO,
                    CMSPage as PageDTO, ContactSetting as ContactDTO, BannerV2, LensIndex as LensDTO)
from mysql import models as m
from mysql.api import row_dict, user_dict
from mysql.base import utcnow
from mysql.catalog import (apply_fields, article_dict, articles_dict, banner_dict, banner_values,
    contact_dict, get_or_404, knowledge_dict, knowledges_dict, replace_article_tags, replace_knowledge_children,
    reviews_dict, safe_values, slugify, strings, unique_slug, validate_payload, write_product)
from mysql.features import normalize_whatsapp_phone

router = APIRouter(prefix="/admin", tags=["admin-content"])

ARTICLE_FIELDS = frozenset({"category_id", "title", "slug", "excerpt", "content", "thumbnail", "status", "tags", "seo_title", "seo_description"})
KNOWLEDGE_FIELDS = frozenset(set(KnowledgeDTO.model_fields) - {"id", "created_at", "published_at"})
PAGE_FIELDS = frozenset(set(PageDTO.model_fields) - {"id", "created_at", "updated_at", "version", "published_at"})
LENS_FIELDS = frozenset(set(LensDTO.model_fields) - {"id"})
FAQ_FIELDS = frozenset(set(FAQItem.model_fields) - {"id", "created_at"})
BANNER_FIELDS = frozenset(set(BannerV2.model_fields) - {"id", "created_at"})
CONTACT_FIELDS = frozenset(set(ContactDTO.model_fields) - {"id", "updated_at"})


async def _simple_list(model, ordering, limit=500):
    async with read_session() as s:
        return [row_dict(row) for row in (await s.scalars(select(model).order_by(*ordering).limit(limit))).all()]


async def _delete_record(model, key):
    async with session_scope() as s:
        await s.delete(await get_or_404(s, model, key, lock=True))
    return {"ok": True}


def _subset(payload, allowed):
    return {key: value for key, value in payload.items() if key in allowed}


@router.get("/article-categories")
async def acat_list(admin: User = Depends(require_permission("article.view"))):
    return {"categories": await _simple_list(m.ArticleCategory, (m.ArticleCategory.sort_order, m.ArticleCategory.id), 200)}


@router.post("/article-categories")
async def acat_create(payload: Dict[str, Any], admin: User = Depends(require_permission("article.create"))):
    async with session_scope() as s:
        data = _subset(payload, {"name", "slug", "description", "sort_order", "is_active"})
        data["slug"] = await unique_slug(s, m.ArticleCategory, data.get("slug") or slugify(str(data.get("name", ""))))
        category = m.ArticleCategory(**safe_values(m.ArticleCategory, validate_payload(ArticleCategoryDTO, data)))
        s.add(category)
        await s.flush()
        return {"ok": True, "category": row_dict(category)}


@router.delete("/article-categories/{cid}")
async def acat_delete(cid: str, admin: User = Depends(require_permission("article.delete"))):
    return await _delete_record(m.ArticleCategory, cid)


@router.get("/articles")
async def art_list(status: Optional[str] = None, admin: User = Depends(require_permission("article.view"))):
    async with read_session() as s:
        stmt = select(m.Article)
        if status:
            stmt = stmt.where(m.Article.status == status)
        rows = (await s.scalars(stmt.order_by(m.Article.created_at.desc(), m.Article.id).limit(200))).all()
        return {"articles": await articles_dict(s, rows, include_content=False)}


@router.get("/articles/{aid}")
async def art_get(aid: str, admin: User = Depends(require_permission("article.view"))):
    async with read_session() as s:
        article = await get_or_404(s, m.Article, aid, "Artikel tidak ditemukan")
        return {"article": await article_dict(s, article)}


@router.post("/articles")
async def art_create(payload: Dict[str, Any], admin: User = Depends(require_permission("article.create"))):
    async with session_scope() as s:
        data = _subset(payload, ARTICLE_FIELDS)
        data["slug"] = await unique_slug(s, m.Article, data.get("slug") or slugify(str(data.get("title", ""))))
        data.setdefault("content", "")
        data.update(author_id=admin.user_id, author_name=admin.name)
        data = validate_payload(ArticleDTO, data)
        if data["status"] == "published":
            data["published_at"] = utcnow()
        article = m.Article(**safe_values(m.Article, data))
        s.add(article)
        await s.flush()
        await replace_article_tags(s, article.id, data["tags"])
        return {"ok": True, "article": await article_dict(s, article)}


@router.put("/articles/{aid}")
async def art_update(aid: str, payload: Dict[str, Any], admin: User = Depends(require_permission("article.update"))):
    async with session_scope() as s:
        article = await get_or_404(s, m.Article, aid, "Artikel tidak ditemukan", lock=True)
        data = validate_payload(ArticleDTO, {**await article_dict(s, article), **_subset(payload, ARTICLE_FIELDS)})
        apply_fields(article, data, ARTICLE_FIELDS)
        if article.status == "published" and article.published_at is None:
            article.published_at = utcnow()
        if "tags" in payload:
            await replace_article_tags(s, article.id, data["tags"])
    return {"ok": True}


@router.delete("/articles/{aid}")
async def art_delete(aid: str, admin: User = Depends(require_permission("article.delete"))):
    return await _delete_record(m.Article, aid)


@router.get("/knowledge")
async def kn_list(admin: User = Depends(require_permission("article.view"))):
    async with read_session() as s:
        rows = (await s.scalars(select(m.ProductKnowledge).order_by(m.ProductKnowledge.sort_order, m.ProductKnowledge.id).limit(200))).all()
        return {"items": await knowledges_dict(s, rows)}


def _knowledge_status(payload, data):
    status = payload.get("status")
    if status is not None:
        if status not in {"draft", "published", "unpublished", "archived"}:
            raise HTTPException(422, "Status konten tidak valid")
        if "is_published" in payload and bool(payload["is_published"]) != (status == "published"):
            raise HTTPException(422, "Status dan is_published tidak konsisten")
        data["is_published"] = status == "published"
        return status
    return "published" if data["is_published"] else "draft"


@router.post("/knowledge")
async def kn_create(payload: Dict[str, Any], admin: User = Depends(require_permission("article.create"))):
    async with session_scope() as s:
        data = _subset(payload, KNOWLEDGE_FIELDS)
        data["slug"] = await unique_slug(s, m.ProductKnowledge, data.get("slug") or slugify(str(data.get("title", ""))))
        data.setdefault("content", "")
        data = validate_payload(KnowledgeDTO, data)
        status = _knowledge_status(payload, data)
        data["status"] = status
        if status == "published":
            data["published_at"] = utcnow()
        knowledge = m.ProductKnowledge(**safe_values(m.ProductKnowledge, data))
        s.add(knowledge)
        await s.flush()
        await replace_knowledge_children(s, knowledge.id, data)
        return {"ok": True, "knowledge": await knowledge_dict(s, knowledge)}


@router.put("/knowledge/{kid}")
async def kn_update(kid: str, payload: Dict[str, Any], admin: User = Depends(require_permission("article.update"))):
    async with session_scope() as s:
        knowledge = await get_or_404(s, m.ProductKnowledge, kid, "Knowledge tidak ditemukan", lock=True)
        data = validate_payload(KnowledgeDTO, {**await knowledge_dict(s, knowledge), **_subset(payload, KNOWLEDGE_FIELDS)})
        status = _knowledge_status(payload, data) if "is_published" in payload or "status" in payload else knowledge.status
        apply_fields(knowledge, data, KNOWLEDGE_FIELDS)
        knowledge.status = status
        if status == "published" and knowledge.published_at is None:
            knowledge.published_at = utcnow()
        await replace_knowledge_children(s, knowledge.id, _subset(data, payload.keys()))
    return {"ok": True}


@router.delete("/knowledge/{kid}")
async def kn_delete(kid: str, admin: User = Depends(require_permission("article.delete"))):
    return await _delete_record(m.ProductKnowledge, kid)


@router.get("/lens/indexes")
async def li_list(admin: User = Depends(require_permission("product.view"))):
    return {"items": await _simple_list(m.LensIndex, (m.LensIndex.sort_order, m.LensIndex.id), 50)}


@router.post("/lens/indexes")
async def li_create(payload: Dict[str, Any], admin: User = Depends(require_permission("product.create"))):
    data = validate_payload(LensDTO, _subset(payload, LENS_FIELDS))
    async with session_scope() as s:
        item = m.LensIndex(**safe_values(m.LensIndex, data))
        s.add(item)
        await s.flush()
        return {"ok": True, "item": row_dict(item)}


@router.put("/lens/indexes/{lid}")
async def li_update(lid: str, payload: Dict[str, Any], admin: User = Depends(require_permission("product.update"))):
    async with session_scope() as s:
        item = await get_or_404(s, m.LensIndex, lid, lock=True)
        data = validate_payload(LensDTO, {**row_dict(item), **_subset(payload, LENS_FIELDS)})
        apply_fields(item, data, LENS_FIELDS)
    return {"ok": True}


@router.delete("/lens/indexes/{lid}")
async def li_delete(lid: str, admin: User = Depends(require_permission("product.delete"))):
    async with session_scope() as s:
        item = await get_or_404(s, m.LensIndex, lid, lock=True)
        item.is_active = False
    return {"ok": True}


@router.get("/faqs")
async def faq_list(admin: User = Depends(require_permission("setting.view"))):
    return {"categories": await _simple_list(m.FAQCategory, (m.FAQCategory.sort_order, m.FAQCategory.id), 50),
            "items": await _simple_list(m.FAQ, (m.FAQ.sort_order, m.FAQ.id))}


@router.post("/faqs")
async def faq_create(payload: Dict[str, Any], admin: User = Depends(require_permission("setting.update"))):
    async with session_scope() as s:
        item = m.FAQ(**safe_values(m.FAQ, validate_payload(FAQItem, _subset(payload, FAQ_FIELDS))))
        s.add(item)
        await s.flush()
        return {"ok": True, "item": row_dict(item)}


@router.put("/faqs/{fid}")
async def faq_update(fid: str, payload: Dict[str, Any], admin: User = Depends(require_permission("setting.update"))):
    async with session_scope() as s:
        item = await get_or_404(s, m.FAQ, fid, lock=True)
        apply_fields(item, validate_payload(FAQItem, {**row_dict(item), **_subset(payload, FAQ_FIELDS)}), FAQ_FIELDS)
    return {"ok": True}


@router.delete("/faqs/{fid}")
async def faq_delete(fid: str, admin: User = Depends(require_permission("setting.update"))):
    return await _delete_record(m.FAQ, fid)


@router.post("/faq-categories")
async def faq_cat_create(payload: Dict[str, Any], admin: User = Depends(require_permission("setting.update"))):
    async with session_scope() as s:
        data = _subset(payload, {"name", "slug", "description", "sort_order", "is_active"})
        data["slug"] = await unique_slug(s, m.FAQCategory, data.get("slug") or slugify(str(data.get("name", ""))))
        s.add(m.FAQCategory(**safe_values(m.FAQCategory, validate_payload(FAQCategoryDTO, data))))
    return {"ok": True}


@router.get("/pages")
async def pages_list(admin: User = Depends(require_permission("setting.view"))):
    return {"pages": await _simple_list(m.CMSPage, (m.CMSPage.created_at.desc(), m.CMSPage.id), 100)}


@router.post("/pages")
async def page_create(payload: Dict[str, Any], admin: User = Depends(require_permission("setting.update"))):
    async with session_scope() as s:
        data = _subset(payload, PAGE_FIELDS)
        data["slug"] = await unique_slug(s, m.CMSPage, data.get("slug") or slugify(str(data.get("title", ""))))
        data.setdefault("content", "")
        data = validate_payload(PageDTO, data)
        if data["status"] == "published":
            data["published_at"] = utcnow()
        page = m.CMSPage(**safe_values(m.CMSPage, data))
        s.add(page)
        await s.flush()
        return {"ok": True, "page": row_dict(page)}


@router.put("/pages/{pid}")
async def page_update(pid: str, payload: Dict[str, Any], admin: User = Depends(require_permission("setting.update"))):
    async with session_scope() as s:
        page = await get_or_404(s, m.CMSPage, pid, lock=True)
        data = validate_payload(PageDTO, {**row_dict(page), **_subset(payload, PAGE_FIELDS)})
        apply_fields(page, data, PAGE_FIELDS)
        page.version += 1
        if page.status == "published" and page.published_at is None:
            page.published_at = utcnow()
    return {"ok": True}


@router.delete("/pages/{pid}")
async def page_delete(pid: str, admin: User = Depends(require_permission("setting.update"))):
    return await _delete_record(m.CMSPage, pid)


@router.get("/contact-setting")
async def contact_get(admin: User = Depends(require_permission("setting.view"))):
    async with read_session() as s:
        contact = await s.scalar(select(m.ContactSetting).where(m.ContactSetting.singleton_key == 1))
        return {"contact": await contact_dict(s, contact)}


@router.put("/contact-setting")
async def contact_update(payload: Dict[str, Any], admin: User = Depends(require_permission("setting.update"))):
    async with session_scope() as s:
        contact = await s.scalar(select(m.ContactSetting).where(m.ContactSetting.singleton_key == 1).with_for_update())
        current = await contact_dict(s, contact) if contact else {}
        data = validate_payload(ContactDTO, {**current, **_subset(payload, CONTACT_FIELDS)})
        if contact is None:
            contact = m.ContactSetting(**safe_values(m.ContactSetting, data))
            s.add(contact)
        else:
            apply_fields(contact, data, CONTACT_FIELDS)
        if "whatsapp" in payload:
            phone = normalize_whatsapp_phone(data["whatsapp"])
            whatsapp = await s.get(m.WhatsAppSetting, 1, with_for_update=True)
            if whatsapp is None:
                whatsapp = m.WhatsAppSetting(id=1, phone=phone, default_text="", is_enabled=False, updated_by=admin.user_id)
                s.add(whatsapp)
            else:
                apply_fields(whatsapp, {"phone": phone, "updated_by": admin.user_id}, {"phone", "updated_by"})
                if not phone:
                    whatsapp.is_enabled = False
    return {"ok": True}


@router.get("/contact-messages")
async def contact_msgs(admin: User = Depends(require_permission("setting.view"))):
    return {"messages": await _simple_list(m.ContactMessage, (m.ContactMessage.created_at.desc(), m.ContactMessage.id))}


@router.get("/banners-v2")
async def bn_list(admin: User = Depends(require_permission("banner.view"))):
    async with read_session() as s:
        rows = (await s.scalars(select(m.Banner).order_by(m.Banner.sort_order, m.Banner.id).limit(200))).all()
        return {"banners": [banner_dict(row) for row in rows]}


def _check_banner_window(data):
    if data.get("start_at") and data.get("end_at") and data["end_at"] <= data["start_at"]:
        raise HTTPException(422, "Waktu akhir harus setelah waktu mulai")


@router.post("/banners-v2")
async def bn_create(payload: Dict[str, Any], admin: User = Depends(require_permission("banner.create"))):
    data = banner_values(validate_payload(BannerV2, _subset(payload, BANNER_FIELDS)))
    _check_banner_window(data)
    async with session_scope() as s:
        banner = m.Banner(**data)
        s.add(banner)
        await s.flush()
        return {"ok": True, "banner": banner_dict(banner)}


@router.put("/banners-v2/{bid}")
async def bn_update(bid: str, payload: Dict[str, Any], admin: User = Depends(require_permission("banner.update"))):
    async with session_scope() as s:
        banner = await get_or_404(s, m.Banner, bid, lock=True)
        data = banner_values(validate_payload(BannerV2, {**banner_dict(banner), **_subset(payload, BANNER_FIELDS)}))
        _check_banner_window(data)
        apply_fields(banner, data, set(data) - {"id", "created_at"})
    return {"ok": True}


@router.delete("/banners-v2/{bid}")
async def bn_delete(bid: str, admin: User = Depends(require_permission("banner.delete"))):
    return await _delete_record(m.Banner, bid)


@router.get("/reviews")
async def rev_list(status: Optional[str] = None, admin: User = Depends(require_permission("review.view"))):
    async with read_session() as s:
        stmt = select(m.ProductReview)
        if status:
            stmt = stmt.where(m.ProductReview.status == status)
        rows = (await s.scalars(stmt.order_by(m.ProductReview.created_at.desc(), m.ProductReview.id).limit(500))).all()
        pids = {r.product_id for r in rows}
        products = {p.id: p for p in (await s.scalars(select(m.Product).where(m.Product.id.in_(pids)))).all()} if pids else {}
        data = await reviews_dict(s, rows)
        for item in data:
            product = products.get(item["product_id"])
            item.update(product_name=product.name if product else "-", product_sku=product.sku if product else "-")
        return {"reviews": data}


@router.post("/reviews/{rid}/moderate")
async def rev_moderate(rid: str, payload: Dict[str, Any], admin: User = Depends(require_permission("review.moderate"))):
    statuses = {"approve": "approved", "reject": "rejected", "hide": "hidden"}
    if payload.get("action") not in statuses:
        raise HTTPException(400, "action harus approve/reject/hide")
    async with read_session() as s:
        product_id = await s.scalar(select(m.ProductReview.product_id).where(m.ProductReview.id == rid))
        if product_id is None:
            raise HTTPException(404, "Review tidak ditemukan")
    async with session_scope() as s:
        # Match review creation's product-first lock order. No consistent read
        # happens in this transaction until after the product lock is held;
        # REPEATABLE READ therefore sees the previous writer's committed cache.
        product = await get_or_404(s, m.Product, product_id, lock=True)
        review = await get_or_404(s, m.ProductReview, rid, lock=True)
        if review.product_id != product.id:
            raise HTTPException(409, "Review berubah; silakan ulangi")
        review.status = statuses[payload["action"]]
        review.moderated_by, review.moderated_at = admin.user_id, utcnow()
        if "admin_reply" in payload:
            apply_fields(review, payload, {"admin_reply"})
        await s.flush()
        count, average = (await s.execute(select(func.count(), func.avg(m.ProductReview.rating))
            .where(m.ProductReview.product_id == product.id, m.ProductReview.status == "approved"))).one()
        product.rating_count = count
        product.rating_avg = Decimal(str(average or 0)).quantize(Decimal("0.01"))
    return {"ok": True}


@router.get("/reviews/analytics")
async def rev_analytics(admin: User = Depends(require_permission("review.view"))):
    async with read_session() as s:
        counts = dict((await s.execute(select(m.ProductReview.status, func.count()).group_by(m.ProductReview.status))).all())
        dist = {i: 0 for i in range(1, 6)}
        rows = await s.execute(select(m.ProductReview.rating, func.count()).where(m.ProductReview.status == "approved").group_by(m.ProductReview.rating))
        for rating, count in rows:
            dist[rating] = count
        top = (await s.scalars(select(m.Product).where(m.Product.rating_count > 0)
            .order_by(m.Product.rating_avg.desc(), m.Product.rating_count.desc(), m.Product.id).limit(10))).all()
        return {"total": sum(counts.values()), "pending": counts.get("pending", 0), "approved": counts.get("approved", 0),
            "rejected": counts.get("rejected", 0), "distribution": dist,
            "top_rated": [{k: row_dict(p)[k] for k in ("id", "name", "rating_avg", "rating_count")} for p in top]}


PERMISSION_CATALOG = [
    ("product.view", "Lihat Produk", "product"), ("product.create", "Buat Produk", "product"),
    ("product.update", "Update Produk", "product"), ("product.delete", "Hapus Produk", "product"),
    ("product.import", "Import Produk", "product"), ("order.view", "Lihat Order", "order"),
    ("order.update", "Update Order", "order"), ("article.view", "Lihat Artikel", "article"),
    ("article.create", "Buat Artikel", "article"), ("article.update", "Update Artikel", "article"),
    ("article.delete", "Hapus Artikel", "article"), ("review.view", "Lihat Review", "review"),
    ("review.moderate", "Moderasi Review", "review"), ("banner.view", "Lihat Banner", "banner"),
    ("banner.create", "Buat Banner", "banner"), ("banner.update", "Update Banner", "banner"),
    ("banner.delete", "Hapus Banner", "banner"), ("report.view", "Lihat Laporan", "report"),
    ("report.export", "Export Laporan", "report"), ("setting.view", "Lihat Setting", "setting"),
    ("setting.update", "Update Setting", "setting"),
]


def _permissions(value):
    permissions = strings(value, limit=100, max_length=100, unique=True)
    allowed = {p[0] for p in PERMISSION_CATALOG}
    if any(permission not in allowed for permission in permissions):
        raise HTTPException(422, "Permission tidak dikenal")
    return permissions


@router.get("/staff")
async def staff_list(admin: User = Depends(current_admin)):
    async with read_session() as s:
        rows = (await s.scalars(select(m.User).where(m.User.role.in_(("staff", "admin", "super_admin")))
            .order_by(m.User.created_at.desc(), m.User.user_id).limit(200))).all()
        users = [await user_dict(s, user) for user in rows]
        for data in users:
            data.pop("password_hash", None)
            data.pop("pin_hash", None)
        return {"staff": users}


@router.post("/staff")
async def staff_create(payload: Dict[str, Any], admin: User = Depends(current_admin)):
    from auth import hash_secret
    role = payload.get("role", "staff")
    if role not in {"staff", "admin"}:
        raise HTTPException(400, "Role harus staff atau admin")
    if role == "admin" and admin.role != "super_admin":
        raise HTTPException(403, "Hanya super_admin yang dapat membuat admin")
    password = payload.get("password")
    if not isinstance(password, str) or len(password) < 8 or len(password.encode()) > 72:
        raise HTTPException(422, "Password harus minimal 8 karakter dan maksimal 72 byte")
    pin = payload.get("pin")
    if pin is not None and (not isinstance(pin, str) or len(pin) != 6 or not pin.isascii() or not pin.isdigit()):
        raise HTTPException(422, "PIN harus 6 digit")
    data = validate_payload(User, {
        "email": payload.get("email"), "name": payload.get("name"), "role": role,
        "password_hash": hash_secret(password), "pin_hash": hash_secret(pin) if pin else None,
        "permissions": _permissions(payload.get("permissions", [])),
    })
    async with session_scope() as s:
        if await s.scalar(select(m.User.user_id).where(m.User.email == data["email"])):
            raise HTTPException(400, "Email sudah terdaftar")
        user = m.User(**safe_values(m.User, data))
        s.add(user)
        await s.flush()
        s.add_all([m.UserPermission(user_id=user.user_id, permission=p) for p in data["permissions"]])
        return {"ok": True, "user_id": user.user_id}


@router.put("/staff/{uid}/permissions")
async def staff_perms(uid: str, payload: Dict[str, Any], admin: User = Depends(current_admin)):
    permissions = _permissions(payload.get("permissions", []))
    async with session_scope() as s:
        user = await get_or_404(s, m.User, uid, lock=True)
        if user.role not in {"staff", "admin"}:
            raise HTTPException(400, "Akun bukan staff/admin yang dapat diubah")
        if user.role == "admin" and admin.role != "super_admin":
            raise HTTPException(403, "Hanya super_admin yang dapat mengubah admin")
        await s.execute(delete(m.UserPermission).where(m.UserPermission.user_id == uid))
        s.add_all([m.UserPermission(user_id=uid, permission=p) for p in permissions])
        user.updated_at = utcnow()
    return {"ok": True}


@router.get("/permissions")
async def perm_list(admin: User = Depends(current_admin)):
    return {"permissions": [{"name": n, "display_name": d, "module": module} for n, d, module in PERMISSION_CATALOG]}


IMPORT_TEMPLATE_HEADERS = [
    "product_name", "product_type", "product_slug", "brand", "main_category",
    "description", "specification", "gender_segment", "frame_shape", "material",
    "variant_sku", "variant_color", "variant_color_hex", "variant_size",
    "variant_price", "variant_discount_price", "variant_stock", "variant_weight",
    "variant_image_url", "lens_type", "lens_index", "is_active", "seo_title", "seo_description",
]
MAX_IMPORT_BYTES = 8 * 1024 * 1024
MAX_IMPORT_ROWS = 5000


@router.get("/products/import/template")
async def import_template(admin: User = Depends(require_permission("product.import"))):
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"
    ws.append(IMPORT_TEMPLATE_HEADERS)
    ws.append([
        "Frame Leinz Premium", "frame", "frame-leinz-premium", "Leinz", "Leinz",
        "Frame premium acetate ringan", '{"garansi":"12 bulan"}', "Pria", "Round", "Acetate",
        "LEINZ-BLK-M", "Black", "#000000", "M", 250000, 220000, 10, 120,
        "https://images.unsplash.com/photo-1772009288423-96090d2998c7?w=900", "", "", 1,
        "Leinz Premium Frame", "Frame Leinz Premium acetate",
    ])
    ws.append([
        "Frame Leinz Premium", "frame", "frame-leinz-premium", "Leinz", "Leinz",
        "", "", "Pria", "Round", "Acetate", "LEINZ-GLD-M", "Gold", "#FCA311", "M",
        275000, "", 7, 120, "https://images.unsplash.com/photo-1618677366787-9727aacca7ea?w=900",
        "", "", 1, "", "",
    ])
    from openpyxl.utils import get_column_letter
    for i in range(1, len(IMPORT_TEMPLATE_HEADERS) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 22
    output = BytesIO()
    wb.save(output)
    wb.close()
    return StreamingResponse(BytesIO(output.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=meoweyes_product_import_template.xlsx"})


def _number(value, *, integer=False, default=None):
    if value is None or value == "":
        if default is None:
            raise ValueError
        value = default
    if isinstance(value, bool):
        raise ValueError
    number = Decimal(str(value))
    if not number.is_finite() or number < 0:
        raise ValueError
    if integer and (number != int(number) or number > 2147483647):
        raise ValueError
    if not integer and number >= Decimal("10000000000000000"):
        raise ValueError
    return int(number) if integer else number


def _active(value):
    if value in (None, ""):
        return True
    if value in (True, 1, "1", "true", "TRUE"):
        return True
    if value in (False, 0, "0", "false", "FALSE"):
        return False
    raise ValueError


def _workbook_rows(data: bytes) -> list[dict]:
    if len(data) > MAX_IMPORT_BYTES:
        raise HTTPException(413, "Maksimum 8 MB per file import")
    try:
        # Bound decompressed content before openpyxl reads XML from an XLSX ZIP.
        from zipfile import ZipFile, BadZipFile
        with ZipFile(BytesIO(data)) as archive:
            if sum(info.file_size for info in archive.infolist()) > 64 * 1024 * 1024:
                raise HTTPException(413, "Isi file import terlalu besar")
        wb = load_workbook(BytesIO(data), read_only=True, data_only=False)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "File Excel tidak valid") from None
    try:
        rows = wb.active.iter_rows(values_only=True)
        first = next(rows, None)
        if first is None:
            raise HTTPException(400, "File kosong")
        header = [str(c).strip() if c is not None else "" for c in first]
        required = {"product_name", "product_type", "variant_sku", "variant_price", "variant_stock"}
        missing = sorted(required - set(header))
        if missing:
            raise HTTPException(400, f"Header wajib hilang: {missing}")
        nonempty = [h for h in header if h]
        if len(nonempty) != len(set(nonempty)):
            raise HTTPException(400, "Header duplikat")
        result, seen_skus = [], set()
        for number, values in enumerate(rows, 2):
            if number > MAX_IMPORT_ROWS + 1:
                raise HTTPException(413, f"Maksimum {MAX_IMPORT_ROWS} baris per import")
            if all(value in (None, "") for value in values):
                continue
            record = dict(zip(header, values))
            errors = []
            if not str(record.get("product_name") or "").strip():
                errors.append("product_name kosong")
            if record.get("product_type") not in ("frame", "lens", "package"):
                errors.append("product_type harus frame/lens/package")
            sku = str(record.get("variant_sku") or "").strip()
            if not sku:
                errors.append("variant_sku kosong")
            elif len(sku) > 128 or sku.casefold() in seen_skus:
                errors.append("variant_sku duplikat atau terlalu panjang")
            seen_skus.add(sku.casefold())
            for field, integer, default in (("variant_price", False, None), ("variant_stock", True, None),
                                            ("variant_weight", True, 100)):
                try:
                    _number(record.get(field), integer=integer, default=default)
                except (ValueError, InvalidOperation, TypeError, OverflowError):
                    errors.append(f"{field} harus angka tidak negatif" + (" dan bulat" if integer else ""))
            if record.get("variant_discount_price") not in (None, ""):
                try:
                    _number(record["variant_discount_price"])
                except (ValueError, InvalidOperation, TypeError, OverflowError):
                    errors.append("variant_discount_price tidak valid")
            try:
                _active(record.get("is_active"))
            except ValueError:
                errors.append("is_active harus 0 atau 1")
            spec = record.get("specification")
            if isinstance(spec, str) and spec.strip().startswith("{"):
                try:
                    decoded = json.loads(spec)
                    if not isinstance(decoded, dict):
                        raise ValueError
                except (ValueError, TypeError):
                    errors.append("specification JSON tidak valid")
            result.append({"row": number, "data": record, "errors": errors})
        if not result:
            raise HTTPException(400, "File tidak berisi data produk")
        return result
    finally:
        wb.close()


@router.post("/products/import/preview")
async def import_preview(file: UploadFile = File(...), admin: User = Depends(require_permission("product.import"))):
    rows = _workbook_rows(await file.read(MAX_IMPORT_BYTES + 1))
    return {"rows": rows, "total": len(rows), "valid": sum(not row["errors"] for row in rows)}


@router.post("/products/import/commit")
async def import_commit(file: UploadFile = File(...), admin: User = Depends(require_permission("product.import"))):
    rows = _workbook_rows(await file.read(MAX_IMPORT_BYTES + 1))
    invalid = [{"row": row["row"], "errors": row["errors"]} for row in rows if row["errors"]]
    if invalid:
        raise HTTPException(422, {"message": "Import dibatalkan; perbaiki seluruh baris tidak valid", "rows": invalid})
    groups: dict[str, list[dict]] = {}
    for row in rows:
        record = row["data"]
        slug = str(record.get("product_slug") or slugify(str(record["product_name"])))
        groups.setdefault(slug, []).append(record)
    created, updated = 0, 0
    # Every row is validated before writes. A failed product rolls back the
    # entire workbook, including new brands and child rows.
    async with session_scope() as s:
        for slug, records in sorted(groups.items()):
            first = records[0]
            product = await s.scalar(select(m.Product).where(m.Product.slug == slug).with_for_update())
            bname = str(first.get("brand") or "").strip()
            brand_id = None
            if bname:
                brand = await s.scalar(select(m.Brand).where(m.Brand.name == bname).order_by(m.Brand.id).limit(1))
                if brand is None:
                    brand = m.Brand(id=m.new_id(), name=bname, slug=await unique_slug(s, m.Brand, slugify(bname)))
                    s.add(brand)
                    await s.flush()
                brand_id = brand.id
            cname = str(first.get("main_category") or "").strip()
            category_ids = []
            if cname:
                matches = (await s.scalars(select(m.Category).where(m.Category.name == cname))).all()
                if len(matches) != 1:
                    raise HTTPException(422, "main_category harus cocok dengan satu kategori yang sudah ada")
                category_ids = [matches[0].id]
            variants = [{"sku": str(rec["variant_sku"]).strip(),
                "color": str(rec.get("variant_color") or "").strip() or None,
                "color_hex": str(rec.get("variant_color_hex") or "").strip() or None,
                "size": str(rec.get("variant_size") or "").strip() or None,
                "lens_type": str(rec.get("lens_type") or "").strip() or None,
                "stock": _number(rec["variant_stock"], integer=True),
                "price_override": _number(rec["variant_price"])} for rec in records]
            raw_spec = first.get("specification")
            if isinstance(raw_spec, str) and raw_spec.strip().startswith("{"):
                spec = json.loads(raw_spec)
            else:
                spec = {"Info": str(raw_spec)} if raw_spec not in (None, "") else {}
            if first.get("frame_shape"):
                spec["Bentuk Frame"] = str(first["frame_shape"])
            if first.get("material"):
                spec["Material"] = str(first["material"])
            payload = {
                "name": str(first["product_name"]), "slug": slug,
                "sku": product.sku if product else "ME-" + m.new_id()[:12].upper(),
                "description": str(first.get("description") or ""), "spec": spec,
                "product_type": first["product_type"], "brand_id": brand_id,
                "primary_category_id": category_ids[0] if category_ids else None, "category_ids": category_ids,
                "segments": [str(first["gender_segment"])] if first.get("gender_segment") else [],
                "price": min(variant["price_override"] for variant in variants),
                "discount_price": _number(first["variant_discount_price"]) if first.get("variant_discount_price") not in (None, "") else None,
                "weight_gram": _number(first.get("variant_weight"), integer=True, default=100),
                "main_image": str(first.get("variant_image_url") or (product.main_image if product else "")),
                "gallery": [str(rec["variant_image_url"]) for rec in records if rec.get("variant_image_url")],
                "variants": variants, "is_active": _active(first.get("is_active")),
                "seo_title": first.get("seo_title"), "seo_description": first.get("seo_description"),
            }
            await write_product(s, payload, product=product, admin_id=admin.user_id)
            if product is None:
                created += 1
            else:
                updated += 1
    return {"ok": True, "created": created, "updated": updated, "errors": []}
