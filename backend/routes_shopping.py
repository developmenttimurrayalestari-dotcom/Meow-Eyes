"""Cart, address book, wishlist, vouchers and existing purchase reviews on SQL."""
from __future__ import annotations

from decimal import Decimal
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select, update

from auth import current_user
from database import read_session, session_scope
from models import AddressCreate, CartItemCreate, CartUpdate, User, gen_id
from mysql import models as m
from mysql.api import row_dict, values_for
from mysql.base import utcnow
from mysql.commerce import (
    MAX_CART_QUANTITY, ZERO, PricedItem, integer, lock_user, money, priced_cart,
    prescription_payload, resolve_variant, save_prescription, voucher_amount,
)
from mysql.features import PAID_ORDER_STATUSES, safe_web_url


router = APIRouter(tags=["shopping"])


async def _cart_payload(s, item: PricedItem) -> dict[str, Any]:
    product, variant = item.product, item.variant
    available = variant.stock - variant.reserved
    if item.lens_variant:
        available = min(available, item.lens_variant.stock - item.lens_variant.reserved)
    return {
        "id": item.cart.id, "product_id": product.id, "variant_id": variant.id,
        "quantity": item.cart.quantity,
        "product": {key: row_dict(product)[key] for key in (
            "id", "name", "slug", "main_image", "weight_gram", "product_type"
        )},
        "variant": row_dict(variant),
        "lens_product": {key: getattr(item.lens_product, key) for key in ("id", "name", "slug")}
            if item.lens_product else None,
        "lens_variant": row_dict(item.lens_variant) if item.lens_variant else None,
        "lens_index": row_dict(item.lens_index) if item.lens_index else None,
        "lens_price": float(item.lens_price), "frame_price": float(item.frame_price),
        "unit_price": float(item.unit_price), "subtotal": float(item.subtotal),
        "available_stock": max(available, 0),
        "prescription": await prescription_payload(s, item.cart.prescription_id),
    }


async def _enrich_cart_item(it: dict[str, Any]):
    async with read_session() as s:
        items, _ = await priced_cart(s, it["user_id"], [it["id"]], require_stock=False, skip_unavailable=True)
        return await _cart_payload(s, items[0]) if items else None


@router.get("/cart")
async def get_cart(user: User = Depends(current_user)):
    async with read_session() as s:
        priced, _ = await priced_cart(s, user.user_id, require_stock=False, skip_unavailable=True)
        items = [await _cart_payload(s, item) for item in priced]
        return {"items": items, "subtotal": float(sum((i.subtotal for i in priced), ZERO)), "count": len(items)}


@router.post("/cart")
async def add_to_cart(req: CartItemCreate, user: User = Depends(current_user)):
    quantity = integer(req.quantity, "Jumlah", 1, MAX_CART_QUANTITY)
    if (req.lens_variant_id or req.lens_index_id or req.prescription) and not req.lens_product_id:
        raise HTTPException(400, "Konfigurasi lensa memerlukan produk lensa")
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        product = await s.scalar(select(m.Product).where(m.Product.id == req.product_id, m.Product.is_active.is_(True)))
        if product is None:
            raise HTTPException(404, "Produk tidak ditemukan")
        variant = await resolve_variant(s, product, req.variant_id)
        lens_variant = None
        if req.lens_product_id:
            lens = await s.scalar(select(m.Product).where(
                m.Product.id == req.lens_product_id, m.Product.product_type == "lens", m.Product.is_active.is_(True)
            ))
            if product.product_type != "frame" or lens is None:
                raise HTTPException(400, "Pasangan frame dan lensa tidak valid")
            lens_variant = await resolve_variant(s, lens, req.lens_variant_id, lens=True)
            if req.lens_index_id and await s.scalar(select(m.LensIndex.id).where(
                m.LensIndex.id == req.lens_index_id, m.LensIndex.is_active.is_(True)
            )) is None:
                raise HTTPException(400, "Indeks lensa tidak tersedia")
        if not req.lens_product_id:
            existing = await s.scalar(select(m.CartItem).where(
                m.CartItem.user_id == user.user_id, m.CartItem.product_id == product.id,
                m.CartItem.variant_id == variant.id, m.CartItem.lens_product_id.is_(None),
                m.CartItem.prescription_id.is_(None),
            ).order_by(m.CartItem.id).with_for_update())
            if existing:
                existing.quantity = integer(existing.quantity + quantity, "Jumlah", 1, MAX_CART_QUANTITY)
                await s.flush()
                return {"ok": True, "id": existing.id}
        count = await s.scalar(select(func.count()).select_from(m.CartItem).where(m.CartItem.user_id == user.user_id))
        if count >= 200:
            raise HTTPException(400, "Keranjang penuh")
        prescription = await save_prescription(s, user.user_id, req.prescription)
        item = m.CartItem(
            id=gen_id("cit"), user_id=user.user_id, product_id=product.id,
            variant_id=variant.id, quantity=quantity, lens_product_id=req.lens_product_id,
            lens_variant_id=lens_variant.id if lens_variant else None,
            lens_index_id=req.lens_index_id, prescription_id=prescription.id if prescription else None,
        )
        s.add(item)
        await s.flush()
        return {"ok": True, "id": item.id}


@router.patch("/cart/{cart_item_id}")
async def update_cart(cart_item_id: str, req: CartUpdate, user: User = Depends(current_user)):
    quantity = integer(req.quantity, "Jumlah", -MAX_CART_QUANTITY, MAX_CART_QUANTITY)
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        item = await s.scalar(select(m.CartItem).where(
            m.CartItem.id == cart_item_id, m.CartItem.user_id == user.user_id
        ).with_for_update())
        if item is None:
            raise HTTPException(404, "Item keranjang tidak ditemukan")
        if quantity <= 0:
            await s.delete(item)
        else:
            item.quantity = quantity
        await s.flush()
    return {"ok": True}


@router.delete("/cart/{cart_item_id}")
async def remove_cart(cart_item_id: str, user: User = Depends(current_user)):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        await s.execute(delete(m.CartItem).where(m.CartItem.id == cart_item_id, m.CartItem.user_id == user.user_id))
    return {"ok": True}


@router.get("/addresses")
async def list_addresses(user: User = Depends(current_user)):
    async with read_session() as s:
        addresses = (await s.scalars(select(m.Address).where(m.Address.user_id == user.user_id)
                                    .order_by(m.Address.is_default.desc(), m.Address.created_at, m.Address.id).limit(50))).all()
        return {"addresses": [row_dict(a) for a in addresses]}


@router.post("/addresses")
async def create_address(req: AddressCreate, user: User = Depends(current_user)):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        if req.is_default:
            await s.execute(update(m.Address).where(m.Address.user_id == user.user_id).values(is_default=False))
        address = m.Address(id=gen_id("adr"), user_id=user.user_id, **values_for(m.Address, req.model_dump()))
        s.add(address)
        await s.flush()
        return {"ok": True, "address": row_dict(address)}


@router.patch("/addresses/{address_id}/default")
async def set_default_address(address_id: str, user: User = Depends(current_user)):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        target = await s.scalar(select(m.Address).where(
            m.Address.id == address_id, m.Address.user_id == user.user_id
        ).with_for_update())
        if target is None:
            raise HTTPException(404, "Alamat tidak ditemukan")
        await s.execute(update(m.Address).where(m.Address.user_id == user.user_id).values(is_default=False))
        target.is_default = True
        await s.flush()
    return {"ok": True}


@router.delete("/addresses/{address_id}")
async def delete_address(address_id: str, user: User = Depends(current_user)):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        await s.execute(delete(m.Address).where(m.Address.id == address_id, m.Address.user_id == user.user_id))
    return {"ok": True}


@router.get("/wishlist")
async def get_wishlist(user: User = Depends(current_user)):
    async with read_session() as s:
        rows = (await s.execute(select(m.Wishlist, m.Product).join(m.Product).where(
            m.Wishlist.user_id == user.user_id, m.Product.is_active.is_(True)
        ).order_by(m.Wishlist.created_at.desc(), m.Wishlist.id).limit(200))).all()
        return {"items": [{"id": entry.id, "product": {key: row_dict(product)[key] for key in (
            "id", "name", "slug", "main_image", "price", "discount_price"
        )}} for entry, product in rows]}


@router.post("/wishlist/{product_id}")
async def add_wishlist(product_id: str, user: User = Depends(current_user)):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        if await s.scalar(select(m.Product.id).where(m.Product.id == product_id, m.Product.is_active.is_(True))) is None:
            raise HTTPException(404, "Produk tidak ditemukan")
        exists = await s.scalar(select(m.Wishlist.id).where(m.Wishlist.user_id == user.user_id, m.Wishlist.product_id == product_id))
        if exists is None:
            s.add(m.Wishlist(id=gen_id("wsh"), user_id=user.user_id, product_id=product_id))
            await s.flush()
    return {"ok": True}


@router.delete("/wishlist/{product_id}")
async def remove_wishlist(product_id: str, user: User = Depends(current_user)):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        await s.execute(delete(m.Wishlist).where(m.Wishlist.user_id == user.user_id, m.Wishlist.product_id == product_id))
    return {"ok": True}


@router.get("/vouchers/active")
async def list_active_vouchers():
    now = utcnow()
    async with read_session() as s:
        vouchers = (await s.scalars(select(m.Voucher).where(
            m.Voucher.is_active.is_(True), m.Voucher.start_at <= now, m.Voucher.end_at > now,
            m.Voucher.used_count < m.Voucher.quota,
        ).order_by(m.Voucher.end_at, m.Voucher.id).limit(50))).all()
        return {"vouchers": [row_dict(v) for v in vouchers]}


@router.post("/vouchers/validate")
async def validate_voucher(payload: dict[str, Any]):
    code = payload.get("code") or ""
    if not isinstance(code, str):
        raise HTTPException(400, "Kode voucher tidak valid")
    subtotal = money(payload.get("subtotal", 0))
    if subtotal < 0:
        raise HTTPException(400, "Subtotal tidak valid")
    async with read_session() as s:
        voucher = await s.scalar(select(m.Voucher).where(m.Voucher.code == code.upper()))
        if voucher is None:
            raise HTTPException(404, "Voucher tidak ditemukan")
        discount, free_shipping = voucher_amount(voucher, subtotal)
        return {"voucher": row_dict(voucher), "discount": float(discount), "free_shipping": free_shipping}


@router.post("/products/{product_id}/reviews")
async def create_review(product_id: str, payload: dict[str, Any], user: User = Depends(current_user)):
    order_id = payload.get("order_id")
    if order_id is not None and (not isinstance(order_id, str) or not order_id.strip() or len(order_id) > 64):
        raise HTTPException(422, "ID pesanan tidak valid")
    rating = integer(payload.get("rating", 5), "Rating", 1, 5)
    body = payload.get("body") or ""
    images = payload.get("images") or []
    if not isinstance(body, str) or len(body) > 10000:
        raise HTTPException(400, "Ulasan maksimum 10000 karakter")
    if not isinstance(images, list) or len(images) > 10 or any(not isinstance(i, str) or len(i) > 2048 for i in images):
        raise HTTPException(400, "Foto ulasan tidak valid")
    images = [safe_web_url(url, "Foto ulasan", allow_http=True) for url in images]
    title = payload.get("title")
    if title is not None and (not isinstance(title, str) or len(title) > 255):
        raise HTTPException(400, "Judul ulasan tidak valid")
    async with session_scope() as s:
        fresh = await lock_user(s, user.user_id)
        product = await s.scalar(select(m.Product).where(m.Product.id == product_id).with_for_update())
        if product is None:
            raise HTTPException(404, "Produk tidak ditemukan")
        # Use an actual order line belonging to this user and product. An
        # explicit unrelated order ID may never fall back to another purchase.
        # The customer row serializes order transitions. The product lock
        # precedes the first consistent read, so REPEATABLE READ counter
        # snapshots include reviews committed by the previous lock holder.
        query = select(m.OrderItem, m.Order).join(m.Order, m.Order.id == m.OrderItem.order_id).where(
            m.OrderItem.product_id == product_id, m.Order.user_id == user.user_id,
            m.Order.status.in_(PAID_ORDER_STATUSES), m.Order.payment_status == "paid",
        )
        if order_id:
            query = query.where(m.Order.id == order_id)
        row = (await s.execute(query.order_by(m.Order.created_at.desc(), m.Order.id, m.OrderItem.id)
                               .limit(1))).first()
        component_purchase = False
        if row is None:
            # Lens products purchased as a bundle component are verified
            # purchases too; retain their exact immutable component identity.
            query = select(m.OrderItemComponent, m.Order).join(m.Order, m.Order.id == m.OrderItemComponent.order_id).where(
                m.OrderItemComponent.product_id == product_id, m.Order.user_id == user.user_id,
                m.Order.status.in_(PAID_ORDER_STATUSES), m.Order.payment_status == "paid",
            )
            if order_id:
                query = query.where(m.Order.id == order_id)
            row = (await s.execute(query.order_by(m.Order.created_at.desc(), m.Order.id,
                m.OrderItemComponent.id).limit(1))).first()
            component_purchase = row is not None
        if row is None:
            raise HTTPException(400, "Ulasan hanya tersedia untuk produk yang dibeli dan pembayarannya berhasil")
        item, order = row
        existing = await s.scalar(select(m.ProductReview.id).where(
            m.ProductReview.user_id == user.user_id, m.ProductReview.product_id == product_id,
            m.ProductReview.order_id == order.id,
        ))
        if existing:
            raise HTTPException(400, "Kamu sudah memberi review untuk pembelian ini")
        review = m.ProductReview(
            id=gen_id("rev"), product_id=product_id, user_id=user.user_id,
            user_name=fresh.name, order_id=order.id,
            order_item_id=None if component_purchase else item.id,
            order_component_id=item.id if component_purchase else None,
            verified_purchase=True, rating=rating, title=title, body=body.strip(), status="approved",
        )
        s.add(review)
        await s.flush()
        s.add_all(m.ProductReviewImage(review_id=review.id, sort_order=i, image_url=url) for i, url in enumerate(images))
        count, average = (await s.execute(select(func.count(m.ProductReview.id), func.avg(m.ProductReview.rating)).where(
            m.ProductReview.product_id == product_id, m.ProductReview.status == "approved"
        ))).one()
        product.rating_count, product.rating_avg = count, money(average or 0)
        await s.flush()
        data = row_dict(review)
        data.update(images=images, is_approved=True)
        return {"ok": True, "review": data}
