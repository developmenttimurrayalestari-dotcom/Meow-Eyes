"""Relational serializers preserving existing API contracts, never Mongo emulation.

Money stays Decimal in services/storage and becomes a JSON number at the HTTP
boundary. Child data comes from normalized tables, batched for product lists.
"""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable
from fastapi import HTTPException
from sqlalchemy import Boolean, Integer, Numeric, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from . import models as m
from .base import UTCDateTime


def json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    return value


def row_dict(instance: Any) -> dict[str, Any]:
    return {c.name: json_value(getattr(instance, c.name))
            for c in instance.__table__.columns if c.computed is None}


def values_for(model: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """Coerce actual scalar columns. Domain services allowlist writable fields.

    Child lists and API aliases are not columns. No document/query interpreter
    is involved. Generated columns cannot be written through this helper.
    """
    out: dict[str, Any] = {}
    for c in model.__table__.columns:
        if c.computed is not None or c.name not in payload:
            continue
        value = payload[c.name]
        if value is None:
            if not c.nullable:
                raise HTTPException(422, f"{c.name} tidak boleh kosong")
            out[c.name] = None
            continue
        try:
            if isinstance(c.type, UTCDateTime):
                if isinstance(value, str):
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if not isinstance(value, datetime) or value.tzinfo is None:
                    raise ValueError("timezone required")
                value = value.astimezone(timezone.utc)
            elif isinstance(c.type, Boolean):
                if value not in (True, False, 0, 1):
                    raise ValueError("boolean required")
                value = bool(value)
            elif isinstance(c.type, Integer):
                if isinstance(value, bool) or Decimal(str(value)) != int(value):
                    raise ValueError("integer required")
                value = int(value)
            elif isinstance(c.type, Numeric):
                if isinstance(value, bool):
                    raise ValueError("number required")
                value = Decimal(str(value))
                if not value.is_finite():
                    raise ValueError("finite number required")
                if c.type.precision and abs(value) >= Decimal(10) ** (c.type.precision - (c.type.scale or 0)):
                    raise ValueError("number out of range")
            elif isinstance(c.type, String):
                if not isinstance(value, str):
                    raise ValueError("string required")
                if c.type.length and len(value) > c.type.length:
                    raise ValueError("string too long")
        except (ValueError, TypeError, InvalidOperation, OverflowError):
            raise HTTPException(422, f"Nilai {c.name} tidak valid") from None
        out[c.name] = value
    return out


async def user_dict(session: AsyncSession, user: m.User) -> dict[str, Any]:
    result = row_dict(user)
    result["permissions"] = list((await session.scalars(
        select(m.UserPermission.permission).where(m.UserPermission.user_id == user.user_id)
        .order_by(m.UserPermission.permission))).all())
    return result


async def products_dict(session: AsyncSession, products: Iterable[m.Product],
                        include_inactive_variants: bool = False) -> list[dict[str, Any]]:
    products = list(products)
    if not products:
        return []
    ids = [p.id for p in products]
    result = {p.id: {**row_dict(p), "category_id": p.primary_category_id,
                     "variants": [], "gallery": [], "category_ids": [],
                     "segments": [], "badges": []} for p in products}
    variants = select(m.ProductVariant).where(m.ProductVariant.product_id.in_(ids))
    if not include_inactive_variants:
        variants = variants.where(m.ProductVariant.is_active.is_(True))
    for variant in (await session.scalars(variants.order_by(
            m.ProductVariant.product_id, m.ProductVariant.sort_order, m.ProductVariant.id))).all():
        result[variant.product_id]["variants"].append(row_dict(variant))
    children = [
        (m.ProductImage, "gallery", "image_url", m.ProductImage.sort_order),
        (m.ProductCategory, "category_ids", "category_id", m.ProductCategory.category_id),
        (m.ProductSegment, "segments", "segment", m.ProductSegment.segment),
        (m.ProductBadge, "badges", "badge", m.ProductBadge.badge),
    ]
    for cls, key, attr, ordering in children:
        for child in (await session.scalars(select(cls).where(cls.product_id.in_(ids))
                                            .order_by(cls.product_id, ordering))).all():
            result[child.product_id][key].append(getattr(child, attr))
    return [result[p.id] for p in products]


async def product_dict(session: AsyncSession, product: m.Product,
                       include_inactive_variants: bool = False) -> dict[str, Any]:
    return (await products_dict(session, [product], include_inactive_variants))[0]


async def order_dict(session: AsyncSession, order: m.Order) -> dict[str, Any]:
    result = row_dict(order)
    result.pop("checkout_idempotency_key", None)
    items = list((await session.scalars(select(m.OrderItem).where(
        m.OrderItem.order_id == order.id).order_by(m.OrderItem.sort_order, m.OrderItem.id))).all())
    components = list((await session.scalars(select(m.OrderItemComponent).where(
        m.OrderItemComponent.order_id == order.id).order_by(
            m.OrderItemComponent.sort_order, m.OrderItemComponent.id))).all())
    result["items"] = [row_dict(it) for it in items]
    by_id = {it["id"]: it for it in result["items"]}
    for it in by_id.values():
        it["components"] = []
    for component in components:
        by_id[component.order_item_id]["components"].append(row_dict(component))
    for link in (await session.scalars(select(m.OrderItemPrescription).where(
            m.OrderItemPrescription.order_id == order.id))).all():
        from .commerce import prescription_payload
        by_id[link.order_item_id]["prescription"] = await prescription_payload(session, link.prescription_id)
    address = await session.get(m.OrderAddress, order.id)
    result["address"] = row_dict(address) if address else {}
    if address:
        result["address"].update(id=address.source_address_id, user_id=order.user_id,
                                 created_at=json_value(address.source_created_at),
                                 is_default=address.source_is_default)
    payment = await session.scalar(select(m.Payment).where(m.Payment.order_id == order.id)
                                   .order_by(m.Payment.created_at.desc(), m.Payment.id.desc()).limit(1))
    shipment = await session.scalar(select(m.Shipment).where(m.Shipment.order_id == order.id)
                                    .order_by(m.Shipment.created_at.desc(), m.Shipment.id.desc()).limit(1))
    result.update(payment_method=payment.method if payment else None,
                  payment_url=payment.payment_url if payment else None,
                  payment_provider=payment.provider if payment else None,
                  payment_mock=bool(payment and payment.provider == "doku-mock"),
                  tracking_number=shipment.tracking_number if shipment else None,
                  shipment_provider=shipment.provider if shipment else None,
                  shipment_id=shipment.id if shipment else None,
                  shipment_label_url=shipment.label_url if shipment else None,
                  label_url=shipment.label_url if shipment else None,
                  carrier_status=shipment.carrier_status if shipment else None,
                  shipment_checked_at=json_value(shipment.last_checked_at) if shipment else None)
    result["payment_reconciliation_required"] = bool(await session.scalar(select(m.IntegrationWebhookEvent.id).where(
        m.IntegrationWebhookEvent.order_id == order.id, m.IntegrationWebhookEvent.provider == "doku",
        m.IntegrationWebhookEvent.status == "failed",
    ).limit(1)))
    result["roulette_reward_id"] = await session.scalar(select(m.RouletteRedemption.spin_id)
                                                       .where(m.RouletteRedemption.order_id == order.id))
    return result
