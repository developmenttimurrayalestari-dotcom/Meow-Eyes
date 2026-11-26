"""Customer payment reads, operational shipping actions and verified webhooks."""
from __future__ import annotations

import hashlib
import hmac
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from auth import current_admin, current_user, current_super_admin, require_permission
from database import read_session, session_scope
from mysql.shipping_origin import KEY as ORIGIN_KEY, OriginInput, origin_data, effective_shipping_settings
from integrations.config import EverproSettings
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
from integrations.locations import region_options


router = APIRouter(tags=["integrations"])


class MapSearchInput(BaseModel):
    query: str = Field(min_length=3, max_length=200)


@router.post('/shipping/map-search')
async def map_search(body: MapSearchInput, user: User = Depends(current_user)):
    from integrations.map_search import search_address
    return await search_address(body.query)


async def configured_status(*, admin=False):
    result = integration_status(admin=admin)
    if result['shipping']['provider'] == 'everpro':
        try:
            async with read_session() as s:
                settings = await effective_shipping_settings(s, EverproSettings.from_env(require_origin=False))
            item = result['shipping']
            item.update(ready=True)
            item.pop('configuration_error', None)
            if admin:
                item.update(missing=[], environment=settings.environment, shipment_type=settings.shipment_type)
        except HTTPException as exc:
            result['shipping']['ready'] = False
            if admin: result['shipping']['configuration_error'] = str(exc.detail)
    return result


@router.get('/admin/shipping-origin')
async def get_shipping_origin(admin: User = Depends(current_super_admin)):
    async with read_session() as s:
        return await origin_data(s)


@router.put('/admin/shipping-origin')
async def save_shipping_origin(body: OriginInput, admin: User = Depends(current_super_admin)):
    from integrations.locations import selected_location
    canonical = await selected_location(body)
    from sqlalchemy.exc import IntegrityError
    try:
        async with session_scope() as s:
            row = await s.get(m.Setting, ORIGIN_KEY, with_for_update=True)
            if body.version != (row.value.get('version', 0) if row else 0):
                raise HTTPException(409, 'Alamat asal sudah diubah. Muat ulang sebelum menyimpan.')
            value = {**body.model_dump(), **canonical, 'version':body.version + 1}
            if row is None:
                row = m.Setting(key=ORIGIN_KEY, is_public=False); s.add(row)
            row.value, row.updated_by, row.is_public = value, admin.user_id, False
            await s.flush()
        return {'origin':value, 'source':'admin'}
    except IntegrityError:
        raise HTTPException(409, 'Alamat asal sudah diubah. Muat ulang sebelum menyimpan.') from None


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
    result = await configured_status()
    from mysql.customer_growth import config
    async with read_session() as s:
        cfg = await config(s)
    result['cod'] = {'ready': bool(cfg['cod_enabled'] and result.get('shipping', {}).get('ready'))}
    return result


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


@router.get('/shipping/locations/provinces')
async def shipping_provinces(user: User = Depends(current_user)):
    return {'locations': await region_options('provinces')}


@router.get('/shipping/locations/cities')
async def shipping_cities(province_id: str = Query(min_length=1, max_length=128), user: User = Depends(current_user)):
    return {'locations': await region_options('cities', province_id)}


@router.get('/shipping/locations/districts')
async def shipping_districts(city_id: str = Query(min_length=1, max_length=128), user: User = Depends(current_user)):
    return {'locations': await region_options('districts', city_id)}


@router.get('/shipping/locations/subdistricts')
async def shipping_subdistricts(district_id: str = Query(min_length=1, max_length=128), user: User = Depends(current_user)):
    return {'locations': await region_options('subdistricts', district_id)}


@router.get("/admin/integrations")
async def admin_status(admin: User = Depends(current_admin)):
    result = await configured_status(admin=True)
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
