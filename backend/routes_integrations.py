"""Customer payment reads, operational shipping actions and verified webhooks."""
from __future__ import annotations

import hashlib
import hmac
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from auth import current_admin, current_user, require_permission
from database import read_session
from models import User
from mysql import models as m
from mysql.api import json_value
from mysql.integration_services import (
    apply_doku_event, apply_everpro_event, book_shipment, ensure_payment,
    integration_status, payment_response, refresh_doku_payment, refresh_shipment,
    shipment_pickup_times, doku_context,
)
from integrations.common import ProviderError, strict_json
from integrations.config import DokuSettings
from integrations.doku import verify_notification
from integrations.everpro import get_everpro_client


router = APIRouter(tags=["integrations"])


async def _owned_order(order_id: str, user: User) -> None:
    async with read_session() as s:
        found = await s.scalar(select(m.Order.id).where(m.Order.id == order_id, m.Order.user_id == user.user_id))
        if not found:
            raise HTTPException(404, "Order tidak ditemukan")


async def _body(request: Request) -> tuple[bytes, dict]:
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise HTTPException(415, "Content-Type application/json diperlukan")
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 262144:
            raise HTTPException(413, "Payload terlalu besar")
        chunks.append(chunk)
    raw = b"".join(chunks)
    try:
        payload = strict_json(raw)
    except (ValueError, UnicodeError):
        raise HTTPException(400, "JSON tidak valid") from None
    return raw, payload


@router.get("/integrations/status")
async def public_status():
    return integration_status()


@router.get("/payments/{order_number}")
async def get_payment(order_number: str, user: User = Depends(current_user)):
    async with read_session() as s:
        order_id = await s.scalar(select(m.Order.id).where(m.Order.order_number == order_number, m.Order.user_id == user.user_id))
        if not order_id:
            raise HTTPException(404, "Order tidak ditemukan")
    return await payment_response(order_id)


@router.post("/orders/{order_id}/payment/retry")
async def retry_payment(order_id: str, user: User = Depends(current_user)):
    await _owned_order(order_id, user)
    await ensure_payment(order_id)
    return await payment_response(order_id)


@router.post("/orders/{order_id}/payment/refresh")
async def refresh_payment(order_id: str, user: User = Depends(current_user)):
    await _owned_order(order_id, user)
    return await refresh_doku_payment(order_id)


@router.get("/shipping/locations")
async def shipping_locations(postal_code: str = Query(pattern=r"^\d{5}$"), user: User = Depends(current_user)):
    try:
        result = await get_everpro_client().locations(postal_code)
    except ProviderError:
        raise HTTPException(503, "Lokasi Everpro belum dapat diperiksa") from None
    rows = result.get("data") or []
    if not isinstance(rows, list):
        raise HTTPException(502, "Respons lokasi Everpro tidak valid")
    return {"locations": [{key: row.get(key) for key in ("postal_code", "province_name", "city_name", "district_name", "sub_district_name", "sub_district_id")}
                          for row in rows if isinstance(row, dict)]}


@router.get("/admin/integrations")
async def admin_status(admin: User = Depends(current_admin)):
    result = integration_status(admin=True)
    async with read_session() as s:
        failed = await s.scalar(select(func.count()).select_from(m.IntegrationWebhookEvent).where(
            m.IntegrationWebhookEvent.status == "failed"))
        pending = await s.scalar(select(func.count()).select_from(m.Shipment).where(
            m.Shipment.provider == "everpro", m.Shipment.status == "pending"))
        events = (await s.execute(select(m.IntegrationWebhookEvent.id, m.IntegrationWebhookEvent.order_id,
            m.IntegrationWebhookEvent.provider, m.IntegrationWebhookEvent.error_code, m.IntegrationWebhookEvent.received_at)
            .where(m.IntegrationWebhookEvent.status == "failed").order_by(m.IntegrationWebhookEvent.received_at.desc()).limit(20))).all()
        result["reconciliation"] = {"payment_events_failed": int(failed or 0), "shipments_pending": int(pending or 0),
            "events": [{"id": row.id, "order_id": row.order_id, "provider": row.provider,
                        "reason": row.error_code, "received_at": json_value(row.received_at)} for row in events]}
    return result


class ShipmentBooking(BaseModel):
    pickup_time: int | None = Field(default=None, gt=0)


@router.get("/admin/orders/{order_id}/shipment/pickup-times")
async def pickup_times(order_id: str, admin: User = Depends(require_permission("order.update"))):
    return await shipment_pickup_times(order_id)


@router.post("/admin/orders/{order_id}/shipment")
async def create_shipment(order_id: str, payload: ShipmentBooking, admin: User = Depends(require_permission("order.update"))):
    return await book_shipment(order_id, payload.pickup_time)


@router.post("/admin/orders/{order_id}/shipment/refresh")
async def refresh_admin_shipment(order_id: str, admin: User = Depends(require_permission("order.update"))):
    return await refresh_shipment(order_id)


@router.post("/admin/orders/{order_id}/payment/refresh")
async def refresh_admin_payment(order_id: str, admin: User = Depends(require_permission("order.update"))):
    return await refresh_doku_payment(order_id)


@router.post("/webhooks/doku")
async def doku_notification(request: Request):
    raw, payload = await _body(request)
    settings = DokuSettings.from_env()
    try:
        request_id = verify_notification(settings, request.headers, raw)
    except ProviderError:
        raise HTTPException(401, "Notifikasi DOKU tidak terverifikasi") from None
    return await apply_doku_event(payload, "notification:" + request_id, hashlib.sha256(raw).hexdigest(),
                                  authenticated_context=doku_context(settings))


async def _everpro_notification(request: Request, kind: str) -> dict:
    key = os.environ.get("EVERPRO_WEBHOOK_KEY", "")
    if not key:
        raise HTTPException(503, "Verifikasi webhook Everpro belum dikonfigurasi")
    received = request.headers.get("x-everpro-key", "")
    if not hmac.compare_digest(received.encode("utf-8"), key.encode("utf-8")):
        raise HTTPException(401, "Notifikasi Everpro tidak terverifikasi")
    raw, payload = await _body(request)
    return await apply_everpro_event(payload, hashlib.sha256(raw).hexdigest(), kind=kind)


@router.post("/webhooks/everpro/awb")
async def everpro_awb(request: Request):
    return await _everpro_notification(request, "awb")


@router.post("/webhooks/everpro/tracking")
async def everpro_tracking(request: Request):
    return await _everpro_notification(request, "tracking")
