"""Existing admin endpoints using SQLAlchemy transactions and relational tables."""
from __future__ import annotations
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from database import read_session, session_scope
from auth import current_admin, require_permission
from models import (User, ProductCreate, ProductUpdate, CategoryCreate, BrandCreate,
                    Voucher as VoucherDTO, FlashSale as FlashSaleDTO,
                    RouletteReward as RouletteRewardDTO, BannerV2)
from mysql import models as m
from mysql.api import order_dict, product_dict, products_dict, row_dict, user_dict
from mysql.base import utcnow
from mysql.catalog import (apply_fields, banner_dict, banner_values, flash_dict,
                           get_or_404, safe_values, slugify, unique_slug,
                           validate_payload, write_product)

router = APIRouter(prefix="/admin", tags=["admin"])


async def _count(s, model, *conditions):
    return await s.scalar(select(func.count()).select_from(model).where(*conditions)) or 0


async def _status_counts(s, column, statuses):
    counts = dict((await s.execute(select(column, func.count()).group_by(column))).all())
    return {"items": [{"status": status, "count": counts.get(status, 0)} for status in statuses]}


@router.get("/dashboard/summary")
async def dashboard_summary(admin: User = Depends(current_admin)):
    now = utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month = today.replace(day=1)
    async with read_session() as s:
        async def sales_since(start):
            return (await s.execute(select(func.coalesce(func.sum(m.Order.total), 0), func.count())
                .where(m.Order.payment_status == "paid", m.Order.created_at >= start))).one()
        sales_today, orders_today = await sales_since(today)
        sales_month, orders_month = await sales_since(month)
        low_stock = await _count(s, m.Product, m.Product.is_active.is_(True),
            select(m.ProductVariant.id).where(m.ProductVariant.product_id == m.Product.id,
                m.ProductVariant.is_active.is_(True),
                m.ProductVariant.stock - m.ProductVariant.reserved <= m.Product.min_stock_alert).exists())
        return {
            "sales_today": float(sales_today), "orders_today": orders_today,
            "sales_month": float(sales_month), "orders_month": orders_month,
            "total_users": await _count(s, m.User),
            "total_products": await _count(s, m.Product, m.Product.is_active.is_(True)),
            "low_stock": low_stock,
            "pending_payment": await _count(s, m.Order, m.Order.status == "pending_payment"),
            "paid_orders": await _count(s, m.Order, m.Order.payment_status == "paid"),
            "cancelled_orders": await _count(s, m.Order, m.Order.status.in_(("cancelled", "expired"))),
            "subscribers": await _count(s, m.NewsletterSubscriber, m.NewsletterSubscriber.is_active.is_(True)),
            "spins": await _count(s, m.RouletteSpin),
        }


@router.get("/dashboard/sales-chart")
async def sales_chart(days: int = Query(14, ge=1, le=366), admin: User = Depends(current_admin)):
    start = (utcnow() - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_expr = func.date(m.Order.created_at)
    async with read_session() as s:
        rows = await s.execute(select(day_expr, func.sum(m.Order.total), func.count())
            .where(m.Order.payment_status == "paid", m.Order.created_at >= start)
            .group_by(day_expr).order_by(day_expr))
        daily = {str(day): (float(revenue), count) for day, revenue, count in rows}
        labels, revenue, orders = [], [], []
        for i in range(days):
            day = start + timedelta(days=i)
            total, count = daily.get(day.date().isoformat(), (0, 0))
            labels.append(day.strftime("%d %b"))
            revenue.append(total)
            orders.append(count)
        return {"labels": labels, "datasets": [
            {"label": "Revenue", "data": revenue}, {"label": "Orders", "data": orders}]}


@router.get("/dashboard/order-status-chart")
async def order_status_chart(admin: User = Depends(current_admin)):
    async with read_session() as s:
        return await _status_counts(s, m.Order.status,
            ("pending_payment", "paid", "processing", "shipped", "completed", "cancelled", "expired", "refunded"))


@router.get("/dashboard/top-products")
async def top_products(limit: int = Query(10, ge=1, le=100), admin: User = Depends(current_admin)):
    async with read_session() as s:
        rows = (await s.scalars(select(m.Product).where(m.Product.is_active.is_(True))
            .order_by(m.Product.sold_count.desc(), m.Product.id).limit(limit))).all()
        return {"items": [{key: row_dict(p)[key] for key in ("id", "name", "sold_count", "main_image")} for p in rows]}


@router.get("/dashboard/payment-chart")
async def payment_chart(admin: User = Depends(current_admin)):
    async with read_session() as s:
        return await _status_counts(s, m.Order.payment_status, ("pending", "paid", "failed", "expired", "cancelled", "refunded"))


@router.get("/dashboard/shipment-chart")
async def shipment_chart(admin: User = Depends(current_admin)):
    async with read_session() as s:
        return await _status_counts(s, m.Order.shipment_status,
            ("pending", "created", "picked_up", "in_transit", "delivered", "failed", "returned"))


@router.get("/dashboard/game-chart")
async def game_chart(admin: User = Depends(current_admin)):
    async with read_session() as s:
        rows = await s.execute(select(m.GameScore.game, func.count(), func.sum(m.GameScore.points_awarded))
            .group_by(m.GameScore.game).order_by(m.GameScore.game))
        return {"items": [{"_id": game, "plays": plays, "points": int(points)} for game, plays, points in rows]}


@router.get("/dashboard/roulette-chart")
async def roulette_chart(admin: User = Depends(current_admin)):
    async with read_session() as s:
        count = func.count()
        rows = await s.execute(select(m.RouletteSpin.reward_label, count)
            .group_by(m.RouletteSpin.reward_label).order_by(count.desc(), m.RouletteSpin.reward_label).limit(20))
        return {"items": [{"_id": label, "count": n} for label, n in rows]}


@router.get("/products")
async def admin_list_products(q: Optional[str] = None, page: int = Query(1, ge=1),
                             limit: int = Query(50, ge=1, le=200), product_type: Optional[str] = None,
                             admin: User = Depends(require_permission("product.view"))):
    async with read_session() as s:
        conditions = [m.Product.name.icontains(q, autoescape=True)] if q else []
        if product_type:
            conditions.append(m.Product.product_type == product_type)
        rows = (await s.scalars(select(m.Product).where(*conditions)
            .order_by(m.Product.created_at.desc(), m.Product.id).offset((page - 1) * limit).limit(limit))).all()
        return {"products": await products_dict(s, rows, include_inactive_variants=True),
                "total": await _count(s, m.Product, *conditions)}


@router.post("/products")
async def create_product(req: ProductCreate, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        data = req.model_dump()
        data["slug"] = await unique_slug(s, m.Product, req.slug or slugify(req.name))
        data["sku"] = req.sku or "ME-" + m.new_id()[:12].upper()
        product = await write_product(s, data, admin_id=admin.user_id)
        return {"ok": True, "product": await product_dict(s, product, include_inactive_variants=True)}


@router.get("/products/{pid}")
async def admin_get_product(pid: str, admin: User = Depends(require_permission("product.view"))):
    async with read_session() as s:
        product = await get_or_404(s, m.Product, pid, "Produk tidak ditemukan")
        return {"product": await product_dict(s, product, include_inactive_variants=True)}


@router.put("/products/{pid}")
async def update_product(pid: str, req: ProductUpdate, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        product = await get_or_404(s, m.Product, pid, "Produk tidak ditemukan", lock=True)
        # Explicit nulls clear optional prices/category/brand; omitted fields stay unchanged.
        await write_product(s, req.model_dump(exclude_unset=True), product=product, admin_id=admin.user_id)
    return {"ok": True}


@router.delete("/products/{pid}")
async def delete_product(pid: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        product = await get_or_404(s, m.Product, pid, "Produk tidak ditemukan", lock=True)
        product.is_active = False
        product.updated_at = utcnow()
    return {"ok": True}


@router.post("/products/{pid}/stock")
async def adjust_stock(pid: str, payload: Dict[str, Any], admin: User = Depends(current_admin)):
    variant_id = payload.get("variant_id")
    if not variant_id:
        raise HTTPException(422, "variant_id wajib diisi")
    try:
        raw = payload.get("delta", 0)
        delta = int(raw)
        if isinstance(raw, bool) or Decimal(str(raw)) != delta or delta == 0:
            raise ValueError
    except (ValueError, TypeError, InvalidOperation, OverflowError):
        raise HTTPException(422, "delta harus bilangan bulat bukan nol") from None
    async with session_scope() as s:
        await get_or_404(s, m.Product, pid, "Produk tidak ditemukan", lock=True)
        variant = await s.scalar(select(m.ProductVariant).where(
            m.ProductVariant.product_id == pid, m.ProductVariant.id == variant_id).with_for_update())
        if variant is None:
            raise HTTPException(404, "Varian produk tidak ditemukan")
        if variant.stock + delta < variant.reserved:
            raise HTTPException(409, "Stok tidak boleh kurang dari stok reserved")
        variant.stock += delta
        s.add(m.StockMovement(id=m.new_id(), product_id=pid, variant_id=variant_id,
            type="stock_in" if delta > 0 else "stock_out", quantity=abs(delta), delta=delta,
            reserved_delta=0, stock_after=variant.stock, reserved_after=variant.reserved,
            note=str(payload.get("note") or ""), admin_id=admin.user_id))
    return {"ok": True}


@router.get("/categories")
async def admin_list_categories(admin: User = Depends(current_admin)):
    async with read_session() as s:
        rows = (await s.scalars(select(m.Category).order_by(m.Category.sort_order, m.Category.id))).all()
        return {"categories": [row_dict(c) for c in rows]}


async def _category_rows_locked(s):
    return list((await s.scalars(select(m.Category).order_by(m.Category.id).with_for_update())).all())


def _validate_category_parent(rows, category_id, parent_id):
    by_id = {c.id: c for c in rows}
    if parent_id and parent_id not in by_id:
        raise HTTPException(422, "Kategori induk tidak ditemukan")
    seen = {category_id}
    current = parent_id
    while current:
        if current in seen:
            raise HTTPException(422, "Kategori induk membentuk siklus")
        seen.add(current)
        current = by_id[current].parent_id
    return by_id


def _refresh_levels(rows):
    by_id = {c.id: c for c in rows}
    for category in rows:
        parent, depth, seen = category.parent_id, 0, {category.id}
        while parent:
            if parent in seen or parent not in by_id:
                raise HTTPException(409, "Hierarki kategori tidak valid")
            seen.add(parent)
            depth += 1
            parent = by_id[parent].parent_id
        category.level = depth


@router.post("/categories")
async def create_category(req: CategoryCreate, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        rows = await _category_rows_locked(s)
        cid = m.new_id()
        _validate_category_parent(rows, cid, req.parent_id)
        data = req.model_dump()
        data["slug"] = await unique_slug(s, m.Category, req.slug or slugify(req.name))
        category = m.Category(id=cid, **safe_values(m.Category, data))
        s.add(category)
        _refresh_levels([*rows, category])
        await s.flush()
        return {"ok": True, "category": row_dict(category)}


@router.put("/categories/{cid}")
async def update_category(cid: str, req: CategoryCreate, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        rows = await _category_rows_locked(s)
        category = next((c for c in rows if c.id == cid), None)
        if category is None:
            raise HTTPException(404, "Kategori tidak ditemukan")
        _validate_category_parent(rows, cid, req.parent_id)
        data = req.model_dump()
        data["slug"] = req.slug or category.slug
        apply_fields(category, data, set(CategoryCreate.model_fields))
        _refresh_levels(rows)
    return {"ok": True}


@router.delete("/categories/{cid}")
async def delete_category(cid: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        category = await get_or_404(s, m.Category, cid, lock=True)
        if await _count(s, m.ProductCategory, m.ProductCategory.category_id == cid) or await _count(
                s, m.Product, m.Product.primary_category_id == cid):
            raise HTTPException(409, "Kategori masih digunakan produk")
        if await _count(s, m.Category, m.Category.parent_id == cid):
            raise HTTPException(409, "Kategori masih memiliki sub-kategori")
        await s.delete(category)
    return {"ok": True}


@router.get("/brands")
async def admin_list_brands(admin: User = Depends(current_admin)):
    async with read_session() as s:
        return {"brands": [row_dict(b) for b in (await s.scalars(select(m.Brand).order_by(m.Brand.name, m.Brand.id))).all()]}


@router.post("/brands")
async def create_brand(req: BrandCreate, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        data = req.model_dump()
        data["slug"] = await unique_slug(s, m.Brand, req.slug or slugify(req.name))
        brand = m.Brand(id=m.new_id(), **safe_values(m.Brand, data))
        s.add(brand)
        await s.flush()
        return {"ok": True, "brand": row_dict(brand)}


@router.put("/brands/{bid}")
async def update_brand(bid: str, req: BrandCreate, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        brand = await get_or_404(s, m.Brand, bid, "Brand tidak ditemukan", lock=True)
        data = req.model_dump()
        data["slug"] = req.slug or brand.slug
        apply_fields(brand, data, set(BrandCreate.model_fields))
    return {"ok": True}


@router.delete("/brands/{bid}")
async def delete_brand(bid: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        brand = await get_or_404(s, m.Brand, bid, lock=True)
        if await _count(s, m.Product, m.Product.brand_id == bid):
            raise HTTPException(409, "Brand masih digunakan produk")
        await s.delete(brand)
    return {"ok": True}


@router.get("/orders")
async def admin_list_orders(status: Optional[str] = None, page: int = Query(1, ge=1),
                           limit: int = Query(50, ge=1, le=200), admin: User = Depends(require_permission("order.view"))):
    async with read_session() as s:
        conditions = [m.Order.status == status] if status else []
        rows = (await s.scalars(select(m.Order).where(*conditions).order_by(m.Order.created_at.desc(), m.Order.id)
            .offset((page - 1) * limit).limit(limit))).all()
        return {"orders": [await order_dict(s, row) for row in rows], "total": await _count(s, m.Order, *conditions)}


@router.post("/orders/{oid}/status")
async def admin_set_order_status(oid: str, payload: Dict[str, Any], admin: User = Depends(require_permission("order.update"))):
    from mysql.commerce import admin_transition_order
    status = payload.get("status")
    if status not in ("processing", "shipped", "completed", "cancelled"):
        raise HTTPException(400, "Status tidak valid")
    await admin_transition_order(oid, status, str(payload.get("note") or ""), admin.user_id)
    return {"ok": True}


@router.get("/inventory")
async def admin_inventory(admin: User = Depends(current_admin)):
    async with read_session() as s:
        products = (await s.scalars(select(m.Product).order_by(m.Product.name, m.Product.id))).all()
        rows = []
        for product in await products_dict(s, products, include_inactive_variants=True):
            variants = product["variants"] or [None]
            for v in variants:
                rows.append({"product_id": product["id"], "variant_id": v["id"] if v else None,
                    "sku": v["sku"] if v else product["sku"], "name": product["name"],
                    "variant_label": " / ".join(x for x in (v.get("color"), v.get("size"), v.get("lens_type")) if x) or "-" if v else "-",
                    "stock": v["stock"] if v else 0, "reserved": v["reserved"] if v else 0,
                    "min_alert": product["min_stock_alert"]})
        return {"items": rows}


@router.get("/vouchers")
async def admin_list_vouchers(admin: User = Depends(current_admin)):
    async with read_session() as s:
        return {"vouchers": [row_dict(v) for v in (await s.scalars(select(m.Voucher).order_by(m.Voucher.created_at.desc(), m.Voucher.id))).all()]}


@router.post("/vouchers")
async def create_voucher(payload: Dict[str, Any], admin: User = Depends(current_admin)):
    data = {k: v for k, v in payload.items() if k in VoucherDTO.model_fields and k not in {"id", "created_at", "used_count"}}
    data["code"] = str(data.get("code") or "VCH" + m.new_id()[:8]).upper()
    data = safe_values(m.Voucher, validate_payload(VoucherDTO, data))
    if data["end_at"] <= data["start_at"]:
        raise HTTPException(422, "Waktu akhir harus setelah waktu mulai")
    async with session_scope() as s:
        voucher = m.Voucher(**data)
        s.add(voucher)
        await s.flush()
        return {"ok": True, "voucher": row_dict(voucher)}


@router.delete("/vouchers/{vid}")
async def delete_voucher(vid: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        voucher = await get_or_404(s, m.Voucher, vid, lock=True)
        voucher.is_active = False
    return {"ok": True}


@router.get("/flash-sales")
async def admin_list_flash_sales(admin: User = Depends(current_admin)):
    async with read_session() as s:
        rows = (await s.scalars(select(m.FlashSale).order_by(m.FlashSale.start_at.desc(), m.FlashSale.id))).all()
        return {"flash_sales": [await flash_dict(s, row, include_inactive=True) for row in rows]}


@router.post("/flash-sales")
async def create_flash_sale(payload: Dict[str, Any], admin: User = Depends(current_admin)):
    from mysql.features import create_category_flash_sale
    async with session_scope() as s:
        flash, report = await create_category_flash_sale(s, payload)
        return {"ok": True, "flash_sale": await flash_dict(s, flash, include_inactive=True), **report}


@router.delete("/flash-sales/{fid}")
async def delete_flash_sale(fid: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        flash = await get_or_404(s, m.FlashSale, fid, lock=True)
        flash.is_active = False
    return {"ok": True}


@router.get("/roulette/rewards")
async def admin_list_rewards(admin: User = Depends(current_admin)):
    async with read_session() as s:
        return {"rewards": [row_dict(r) for r in (await s.scalars(select(m.RouletteReward).order_by(m.RouletteReward.id))).all()]}


@router.post("/roulette/rewards")
async def create_reward(payload: Dict[str, Any], admin: User = Depends(current_admin)):
    data = validate_payload(RouletteRewardDTO, {k: v for k, v in payload.items() if k in RouletteRewardDTO.model_fields and k != "id"})
    async with session_scope() as s:
        reward = m.RouletteReward(**safe_values(m.RouletteReward, data))
        s.add(reward)
        await s.flush()
        return {"ok": True, "reward": row_dict(reward)}


@router.delete("/roulette/rewards/{rid}")
async def delete_reward(rid: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        reward = await get_or_404(s, m.RouletteReward, rid, lock=True)
        reward.is_active = False
    return {"ok": True}


@router.get("/users")
async def admin_list_users(q: Optional[str] = None, admin: User = Depends(current_admin)):
    async with read_session() as s:
        stmt = select(m.User)
        if q:
            stmt = stmt.where(or_(m.User.name.icontains(q, autoescape=True), m.User.email.icontains(q, autoescape=True)))
        rows = (await s.scalars(stmt.order_by(m.User.created_at.desc(), m.User.user_id).limit(200))).all()
        users = [await user_dict(s, user) for user in rows]
        for data in users:
            data.pop("password_hash", None)
            data.pop("pin_hash", None)
        return {"users": users}


def _can_manage_user(admin, target):
    if target.role in ("admin", "super_admin") and admin.role != "super_admin":
        raise HTTPException(403, "Hanya super_admin yang dapat mengubah akun admin")


@router.post("/users/{uid}/toggle-active")
async def toggle_user_active(uid: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        user = await get_or_404(s, m.User, uid, "User tidak ditemukan", lock=True)
        _can_manage_user(admin, user)
        if user.user_id == admin.user_id:
            raise HTTPException(409, "Tidak dapat menonaktifkan akun sendiri")
        user.is_active = not user.is_active
    return {"ok": True}


@router.post("/users/{uid}/reset-pin")
async def reset_pin(uid: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        user = await get_or_404(s, m.User, uid, "User tidak ditemukan", lock=True)
        _can_manage_user(admin, user)
        user.pin_hash, user.pin_failed_attempts, user.pin_locked_until = None, 0, None
    return {"ok": True}


@router.get("/newsletter/subscribers")
async def admin_subscribers(admin: User = Depends(current_admin)):
    async with read_session() as s:
        rows = (await s.scalars(select(m.NewsletterSubscriber)
            .order_by(m.NewsletterSubscriber.created_at.desc(), m.NewsletterSubscriber.id))).all()
        return {"subscribers": [row_dict(row) for row in rows]}


@router.post("/newsletter/campaigns")
async def create_campaign(payload: Dict[str, Any], admin: User = Depends(current_admin)):
    async with session_scope() as s:
        # Retain the existing simulated campaign behavior; this endpoint sends no email.
        count = await _count(s, m.NewsletterSubscriber, m.NewsletterSubscriber.is_active.is_(True))
        campaign = m.NewsletterCampaign(id=m.new_id(), **safe_values(m.NewsletterCampaign, {
            "subject": payload.get("subject", ""), "body": payload.get("body", ""),
            "segment": payload.get("segment", "all"), "status": "sent",
            "sent_count": count, "failed_count": 0}))
        s.add(campaign)
        await s.flush()
        return {"ok": True, "campaign": row_dict(campaign), "mocked": True}


@router.get("/newsletter/campaigns")
async def list_campaigns(admin: User = Depends(current_admin)):
    async with read_session() as s:
        rows = (await s.scalars(select(m.NewsletterCampaign)
            .order_by(m.NewsletterCampaign.created_at.desc(), m.NewsletterCampaign.id).limit(200))).all()
        return {"campaigns": [row_dict(row) for row in rows]}


@router.get("/banners")
async def admin_banners(admin: User = Depends(current_admin)):
    async with read_session() as s:
        rows = (await s.scalars(select(m.Banner).order_by(m.Banner.sort_order, m.Banner.id))).all()
        return {"banners": [banner_dict(row) for row in rows]}


@router.post("/banners")
async def create_banner(payload: Dict[str, Any], admin: User = Depends(current_admin)):
    data = validate_payload(BannerV2, {
        "title": payload.get("title", ""), "image_desktop": payload.get("image", ""),
        "link_url": payload.get("link") or "/", "position": payload.get("position", "hero"),
        "sort_order": payload.get("sort_order", 0), "is_active": payload.get("is_active", True),
    })
    async with session_scope() as s:
        banner = m.Banner(**banner_values(data))
        s.add(banner)
        await s.flush()
        return {"ok": True, "banner": banner_dict(banner)}


@router.delete("/banners/{bid}")
async def delete_banner(bid: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        await s.delete(await get_or_404(s, m.Banner, bid, lock=True))
    return {"ok": True}
