"""Existing checkout/order API, backed exclusively by relational services."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select

from auth import current_admin, current_user, verify_pin_or_raise
from database import read_session, session_scope
from models import CheckoutConfirm, CheckoutPreview, User
from mysql import models as m
from mysql.api import order_dict, product_dict, row_dict
from mysql.base import utcnow
from mysql.commerce import (
    RESERVATION_HOURS, checkout_quote, confirm_mock_payment,
    create_checkout, expire_order, priced_cart, prescription_payload,
)
from services_mock import everpro_track
from integrations.config import require_payment_provider
from mysql.integration_services import shipping_options as provider_shipping_options, stored_tracking


router = APIRouter(tags=["orders"])


async def _calc_cart_subtotal(user_id: str, selected_ids: list[str] | None = None):
    """Compatibility helper for callers of the former checkout module."""
    async with read_session() as s:
        items, weight = await priced_cart(s, user_id, selected_ids)
        enriched = [{
            "cart_id": item.cart.id, "product": await product_dict(s, item.product),
            "variant": row_dict(item.variant), "quantity": item.cart.quantity,
            "unit_price": float(item.unit_price), "subtotal": float(item.subtotal),
            "lens_product": await product_dict(s, item.lens_product) if item.lens_product else None,
            "lens_price": float(item.lens_price),
            "prescription": await prescription_payload(s, item.cart.prescription_id),
        } for item in items]
        return float(sum(item.subtotal for item in items)), enriched, weight


@router.post("/checkout/shipping-options")
async def shipping_options(payload: dict[str, Any], user: User = Depends(current_user)):
    selected = payload.get("selected_item_ids") or []
    if not isinstance(selected, list) or len(selected) > 200 or any(not isinstance(x, str) for x in selected):
        raise HTTPException(400, "Item checkout tidak valid")
    return await provider_shipping_options(user.user_id, payload.get("address_id"), selected)


@router.post("/checkout/preview")
async def checkout_preview(req: CheckoutPreview, user: User = Depends(current_user)):
    from mysql.commerce import lock_user
    async with session_scope() as s:
        fresh = await lock_user(s, user.user_id)
        return (await checkout_quote(s, fresh, req)).payload()


@router.post("/checkout/confirm")
async def checkout_confirm(
    req: CheckoutConfirm, user: User = Depends(current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    require_payment_provider()
    # PIN attempt accounting deliberately commits in its own small transaction;
    # a failed checkout must not roll back failed-PIN/lockout counters.
    await verify_pin_or_raise(user, req.pin)
    return await create_checkout(user.user_id, req, idempotency_key)


@router.get("/orders")
async def list_orders(user: User = Depends(current_user), status: str | None = None):
    async with read_session() as s:
        query = select(m.Order).where(m.Order.user_id == user.user_id)
        if status:
            query = query.where(m.Order.status == status)
        orders = (await s.scalars(query.order_by(m.Order.created_at.desc(), m.Order.id).limit(200))).all()
        return {"orders": [await order_dict(s, order) for order in orders]}


@router.get("/orders/{order_id}")
async def order_detail(order_id: str, user: User = Depends(current_user)):
    async with read_session() as s:
        order = await s.scalar(select(m.Order).where(m.Order.id == order_id, m.Order.user_id == user.user_id))
        if order is None:
            raise HTTPException(404, "Order tidak ditemukan")
        data = await order_dict(s, order)
        shipment = await s.scalar(select(m.Shipment).where(m.Shipment.order_id == order.id)
                                  .order_by(m.Shipment.created_at.desc(), m.Shipment.id))
        tracking_number = shipment.tracking_number if shipment and shipment.provider == "everpro-mock" else None
        tracking = await stored_tracking(s, order_id) if shipment and shipment.provider == "everpro" else None
    if tracking_number:
        tracking = everpro_track(tracking_number)
    return {"order": data, "tracking": tracking}


@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str, user: User = Depends(current_user)):
    await expire_order(order_id, "cancelled", owner_id=user.user_id)
    return {"ok": True}


async def _expire_order(order_id: str, status: str = "expired") -> None:
    await expire_order(order_id, status, due_only=status == "expired")


@router.post("/payment/confirm/{order_number}")
async def confirm_payment(order_number: str, user: User = Depends(current_user)):
    """Development/test simulation; never an unauthenticated payment webhook."""
    return await confirm_mock_payment(order_number, user.user_id, admin=user.role in {"admin", "super_admin"})


@router.post("/cron/expire-orders")
async def cron_expire_orders(admin: User = Depends(current_admin)):
    async with read_session() as s:
        ids = list((await s.scalars(select(m.Order.id).where(
            m.Order.status == "pending_payment", m.Order.reservation_expires_at <= utcnow()
        ).order_by(m.Order.reservation_expires_at, m.Order.id).limit(500))).all())
    count = 0
    for order_id in ids:
        count += int(await expire_order(order_id, due_only=True))
    return {"expired_count": count}
