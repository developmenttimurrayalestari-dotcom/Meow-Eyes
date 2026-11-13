"""SQL-backed maintenance jobs, safe to retry across application workers.

The scheduler reconciles persisted intents with authenticated provider APIs.
It never fabricates payment or delivery success and never books a shipment
before an operator confirms that the optical order is ready.
"""
from __future__ import annotations

from datetime import timedelta
import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import HTTPException
from sqlalchemy import or_, select, update

from database import read_session, session_scope
from models import gen_id
from mysql import models as m
from mysql.base import utcnow
from mysql.commerce import admin_transition_order, expire_order, lock_user, mock_payments_enabled
from services_mock import everpro_track


log = logging.getLogger("meow.scheduler")
scheduler = AsyncIOScheduler(timezone="UTC")
ORDER_EXPIRE_INTERVAL_MIN = int(os.environ.get("ORDER_EXPIRE_INTERVAL_MIN", "5"))
FLASH_SALE_INTERVAL_MIN = int(os.environ.get("FLASH_SALE_INTERVAL_MIN", "1"))
SHIPMENT_POLL_INTERVAL_MIN = int(os.environ.get("SHIPMENT_POLL_INTERVAL_MIN", "10"))
ORDER_AUTO_COMPLETE_INTERVAL_MIN = int(os.environ.get("ORDER_AUTO_COMPLETE_INTERVAL_MIN", "60"))
AUTO_COMPLETE_DAYS = int(os.environ.get("ORDER_AUTO_COMPLETE_DAYS", "7"))


def _now_iso() -> str:
    return utcnow().isoformat()


async def job_expire_pending_orders() -> None:
    async with read_session() as s:
        ids = list((await s.scalars(select(m.Order.id).where(
            m.Order.status == "pending_payment", m.Order.reservation_expires_at <= utcnow()
        ).order_by(m.Order.reservation_expires_at, m.Order.id).limit(500))).all())
    for order_id in ids:
        try:
            await expire_order(order_id, due_only=True)
        except Exception:
            # No SQL parameters, payment payloads or prescription data in logs.
            log.error("Scheduled reservation release failed for order %s", order_id)


async def job_activate_flash_sales() -> None:
    now = utcnow()
    async with session_scope() as s:
        # is_active is the operator's switch. Disabled campaigns must not be
        # silently re-enabled by an interval job when their window begins.
        await s.execute(update(m.FlashSale).where(
            m.FlashSale.is_active.is_(True), m.FlashSale.start_at <= now,
            m.FlashSale.end_at > now, m.FlashSale.activated_at.is_(None),
        ).values(activated_at=now))
        await s.execute(update(m.FlashSale).where(
            m.FlashSale.end_at <= now, m.FlashSale.ended_at.is_(None),
        ).values(is_active=False, ended_at=now))


async def job_poll_shipments() -> None:
    from mysql.integration_services import refresh_shipment
    async with read_session() as s:
        attempted = select(m.ShipmentLog.shipment_id).where(m.ShipmentLog.action == "everpro_request")
        live_ids = list((await s.scalars(select(m.Shipment.order_id).join(m.Order).where(
            m.Shipment.provider == "everpro", m.Shipment.status.in_(("pending", "created", "picked_up", "in_transit", "failed")),
            or_(m.Shipment.external_id.is_not(None), m.Shipment.tracking_number.is_not(None), m.Shipment.id.in_(attempted)),
            m.Order.payment_status == "paid", m.Order.status.in_(("paid", "processing", "shipped")),
        ).order_by(m.Shipment.last_checked_at, m.Shipment.id).limit(200))).all())
    for order_id in live_ids:
        try:
            await refresh_shipment(order_id)
        except Exception:
            log.error("Scheduled Everpro reconciliation failed for order %s", order_id)
    if not mock_payments_enabled():
        return
    # Pull candidates before calling the adapter; no inventory lock is held.
    async with read_session() as s:
        candidates = (await s.execute(select(m.Shipment.id, m.Shipment.order_id,
            m.Shipment.tracking_number, m.Order.user_id).join(m.Order).where(
                m.Shipment.provider == "everpro-mock", m.Shipment.tracking_number.is_not(None),
                m.Shipment.status.in_(("created", "picked_up", "in_transit")),
                m.Order.status.in_(("paid", "processing", "shipped")), m.Order.payment_status == "paid",
            ).order_by(m.Shipment.last_checked_at, m.Shipment.id).limit(500))).all()
    for shipment_id, order_id, tracking, owner_id in candidates:
        try:
            response = everpro_track(tracking)
            # The current mock returns a timeline list, not a dict with a
            # machine status. Preserve it as events and do not invent delivery.
            state = response.get("status") if isinstance(response, dict) else None
            carrier = state
            if isinstance(response, list) and response:
                carrier = response[-1].get("status") if isinstance(response[-1], dict) else None
            status_map = {"picked_up": "picked_up", "in_transit": "in_transit",
                          "on_delivery": "in_transit", "delivered": "delivered"}
            async with session_scope() as s:
                await lock_user(s, owner_id, active=False)
                order = await s.scalar(select(m.Order).where(m.Order.id == order_id).with_for_update())
                shipment = await s.scalar(select(m.Shipment).where(m.Shipment.id == shipment_id).with_for_update())
                if order.status not in {"paid", "processing", "shipped"} or order.payment_status != "paid":
                    continue
                shipment.last_checked_at = utcnow()
                if carrier is not None:
                    shipment.carrier_status = str(carrier)[:255]
                mapped = status_map.get(state)
                if mapped:
                    shipment.status, order.shipment_status = mapped, mapped
                    if shipment.shipped_at is None:
                        shipment.shipped_at = utcnow()
                    if mapped == "delivered" and shipment.delivered_at is None:
                        shipment.delivered_at = utcnow()
                    if order.status != "shipped":
                        order.status = "shipped"
                        s.add(m.OrderStatusLog(id=gen_id("ols"), order_id=order.id, status="shipped",
                                              note="Status pengiriman diperbarui"))
                s.add(m.ShipmentLog(id=gen_id("slg"), order_id=order.id, shipment_id=shipment.id,
                                    provider="everpro-mock", action="tracking_poll",
                                    response=response if isinstance(response, dict) else {"events": response}))
                await s.flush()
        except Exception:
            log.error("Scheduled shipment poll failed for shipment %s", shipment_id)


async def job_auto_complete_orders() -> None:
    cutoff = utcnow() - timedelta(days=max(AUTO_COMPLETE_DAYS, 1))
    async with read_session() as s:
        shipped_by = select(m.Shipment.order_id).where(m.Shipment.shipped_at <= cutoff)
        shipped_log = select(m.OrderStatusLog.order_id).where(
            m.OrderStatusLog.status == "shipped", m.OrderStatusLog.created_at <= cutoff
        )
        live_orders = select(m.Shipment.order_id).where(m.Shipment.provider == "everpro")
        delivered_live = select(m.Shipment.order_id).where(m.Shipment.provider == "everpro",
            m.Shipment.status == "delivered", m.Shipment.delivered_at <= cutoff)
        ids = list((await s.scalars(select(m.Order.id).where(
            m.Order.status == "shipped", m.Order.payment_status == "paid",
            or_(m.Order.id.in_(delivered_live),
                (~m.Order.id.in_(live_orders)) & or_(m.Order.id.in_(shipped_by), m.Order.id.in_(shipped_log))),
        ).order_by(m.Order.id).limit(500))).all())
    for order_id in ids:
        try:
            # Uses the same order/user locks and state machine as admin actions.
            # Tracking polls never reset the immutable shipped-at clock.
            await admin_transition_order(order_id, "completed", "Pesanan selesai otomatis", None)
        except HTTPException as exc:
            if exc.status_code not in {404, 409}:
                log.error("Scheduled completion rejected for order %s", order_id)
        except Exception:
            log.error("Scheduled completion failed for order %s", order_id)


async def job_reconcile_payments() -> None:
    from mysql.integration_services import refresh_doku_payment
    async with read_session() as s:
        ids = list((await s.scalars(select(m.Order.id).join(m.Payment).where(
            m.Payment.provider == "doku", m.Payment.status == "pending", m.Order.payment_status == "pending",
            m.Order.status == "pending_payment", m.Payment.created_at <= utcnow() - timedelta(seconds=60),
        ).order_by(m.Payment.created_at, m.Payment.id).limit(100))).all())
    for order_id in ids:
        try:
            await refresh_doku_payment(order_id)
        except HTTPException as exc:
            if exc.status_code != 429:
                log.error("Scheduled DOKU reconciliation failed for order %s", order_id)
        except Exception:
            log.error("Scheduled DOKU reconciliation failed for order %s", order_id)


async def job_expire_meowsurement_photos() -> None:
    from routes_meowsurement import expire_private_photos
    try:
        await expire_private_photos()
    except Exception:
        # Never log file paths, face photos, prescriptions, or raw DB errors.
        log.error("Scheduled Meowsurement photo retention cleanup failed")
        raise


async def job_expire_points() -> None:
    from mysql.commerce import lock_user
    from mysql.points import expire
    async with read_session() as s:
        ids = list((await s.scalars(select(m.PointLot.user_id).where(m.PointLot.remaining > 0, m.PointLot.expires_at <= utcnow()).distinct().order_by(m.PointLot.user_id).limit(500))).all())
    for user_id in ids:
        async with session_scope() as s:
            await expire(s, await lock_user(s, user_id, active=False))

def start_scheduler() -> None:
    defaults = {"max_instances": 1, "coalesce": True, "misfire_grace_time": 60}
    for job_id, handler, minutes in (
        ("expire-pending-orders", job_expire_pending_orders, ORDER_EXPIRE_INTERVAL_MIN),
        ("activate-flash-sales", job_activate_flash_sales, FLASH_SALE_INTERVAL_MIN),
        ("poll-shipments", job_poll_shipments, SHIPMENT_POLL_INTERVAL_MIN),
        ("auto-complete-orders", job_auto_complete_orders, ORDER_AUTO_COMPLETE_INTERVAL_MIN),
        ("reconcile-payments", job_reconcile_payments, ORDER_EXPIRE_INTERVAL_MIN),
        ("expire-meowsurement-photos", job_expire_meowsurement_photos, 60),
        ("expire-points", job_expire_points, 5),
    ):
        scheduler.add_job(handler, id=job_id, replace_existing=True,
                          trigger=IntervalTrigger(minutes=max(minutes, 1)), **defaults)
    if not scheduler.running:
        scheduler.start()
        log.info("Maintenance scheduler started")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        log.info("Maintenance scheduler stopped")
