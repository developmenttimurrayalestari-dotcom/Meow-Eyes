"""Persisted integration intents around short relational transactions.

Remote calls never run while cart/inventory/order locks are held. Provider
identifiers survive retries. Authenticated callbacks are the authority for
money; a browser redirect never marks an order paid.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import hmac
import json
import os
import re
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, select, update

from database import read_session, session_scope
from models import gen_id
from mysql import models as m
from mysql.api import json_value, order_dict, row_dict
from mysql.base import utcnow
from mysql.commerce import ZERO, lock_user, money, priced_cart, payment_payload
from integrations.common import ProviderError, json_bytes
from integrations.config import DokuSettings, EverproSettings, payment_provider, shipping_provider, mock_enabled
from integrations.doku import get_doku_client, safe_checkout_url
from integrations.everpro import get_everpro_client
from integrations.locations import canonical_shipping_location


def _digest(value: Any) -> str:
    return hashlib.sha256(json_bytes(value)).hexdigest()


def _amount(value: Any, provider: str, *, positive: bool = False) -> Decimal:
    try:
        if isinstance(value, bool):
            raise ValueError
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or number >= Decimal("1000000000000") or number != number.to_integral_value() or (positive and number <= 0):
            raise ValueError
        return number.quantize(Decimal("0.01"))
    except (TypeError, InvalidOperation, ValueError):
        raise ProviderError(provider, "invalid_amount") from None


def _safe_error(exc: ProviderError, action: str) -> HTTPException:
    if exc.provider == 'everpro' and action == 'menghitung ongkir':
        message = 'Layanan ongkir EVERPRO belum dapat dihubungi. Silakan coba kembali.'
        if exc.code in {'authentication_failed', 'invalid_auth_response'}:
            message = 'Koneksi EVERPRO belum dapat diautentikasi. Hubungi toko untuk memeriksa layanan pengiriman.'
        elif exc.code == 'provider_rejected':
            message = 'EVERPRO menolak permintaan ongkir. Periksa wilayah alamat melalui tombol Ubah; jika sudah sesuai, hubungi toko.'
        elif exc.code in {'invalid_rates_response', 'invalid_response', 'invalid_amount'}:
            message = 'Tarif EVERPRO belum dapat dibaca. Silakan coba kembali atau hubungi toko.'
        return HTTPException(503, message)
    return HTTPException(503, f"Layanan {exc.provider.upper()} belum dapat {action}. Silakan coba kembali; referensi transaksi tetap sama.")


def doku_context(settings: DokuSettings) -> dict[str, str]:
    return {"environment": settings.environment, "account": hashlib.sha256(settings.client_id.encode()).hexdigest()}


async def _saved_doku_context(s, payment_id: str) -> dict | None:
    log = await s.scalar(select(m.PaymentLog).where(m.PaymentLog.payment_id == payment_id,
        m.PaymentLog.action == "doku_configuration").order_by(m.PaymentLog.created_at, m.PaymentLog.id).limit(1))
    return log.payload if log else None


def shipping_fingerprint(items, address: m.Address, settings: EverproSettings) -> tuple[str, dict]:
    address_snapshot = {key: getattr(address, key) for key in (
        "id", "recipient", "phone", "street", "subdistrict", "district", "city", "province", "postal_code", "country_code",
    )}
    origin = {
        "postal_code": settings.origin_postal_code, "subdistrict": settings.origin_subdistrict,
        "name": settings.shipper_name, "phone": settings.shipper_phone, "address": settings.shipper_address,
        "email": settings.shipper_email, "shipment_type": settings.shipment_type,
        "package_type_id": settings.package_type_id, "length": settings.length_cm,
        "width": settings.width_cm, "height": settings.height_cm, "insurance": settings.insurance,
    }
    lines = [{
        "cart_id": item.cart.id, "product_id": item.product.id, "variant_id": item.variant.id,
        "quantity": item.cart.quantity, "unit_price": str(item.unit_price),
        "weight": item.product.weight_gram,
        "lens_id": item.lens_product.id if item.lens_product else None,
        "lens_variant_id": item.lens_variant.id if item.lens_variant else None,
        "lens_weight": item.lens_product.weight_gram if item.lens_product else None,
        "prescription_id": item.cart.prescription_id,
    } for item in sorted(items, key=lambda x: x.cart.id)]
    provider = {"environment": settings.environment, "base_url": settings.base_url,
                "account": hashlib.sha256(settings.client_key.encode()).hexdigest()}
    snapshot = {"address": address_snapshot, "origin": origin, "items": lines, "provider": provider, "version": 1}
    return _digest(snapshot), snapshot


def _shipping_address_valid(address: m.Address) -> None:
    if address.country_code != "ID" or not re.fullmatch(r"\d{5}", address.postal_code or ""):
        raise HTTPException(422, "Everpro memerlukan alamat Indonesia dengan kode pos 5 digit")
    if len(address.recipient.strip()) < 3 or not 3 <= len(address.street.strip()) <= 250:
        raise HTTPException(422, "Nama penerima minimal 3 karakter dan alamat maksimal 250 karakter")
    if not re.fullmatch(r"(?:\+?62|08)\d{8,12}", address.phone or "") or len(address.phone) > 15:
        raise HTTPException(422, "Nomor telepon penerima harus menggunakan nomor Indonesia yang valid")


def _rate_options(body: dict) -> list[dict]:
    data = body.get("data")
    if not isinstance(data, dict):
        raise ProviderError("everpro", "invalid_rates_response")
    options, seen = [], set()
    # Instant/same-day need verified coordinates; these are intentionally not
    # offered from a postcode-only address form. Regular/express/cargo use the
    # postal-address request documented in the provider's OpenAPI.
    for group in ("regular", "express", "cargo"):
        rates = data.get(group) or []
        if not isinstance(rates, list):
            raise ProviderError("everpro", "invalid_rates_response")
        for rate in rates:
            if not isinstance(rate, dict):
                raise ProviderError("everpro", "invalid_rates_response")
            courier, service = rate.get("logistic_code"), rate.get("rate_code")
            if not isinstance(courier, str) or not isinstance(service, str) or not 1 <= len(courier) <= 64 or not 1 <= len(service) <= 64:
                # The live provider can include cargo rows without a courier
                # code. They cannot be booked, but must not hide valid rates
                # from the other couriers. Never guess a code from its name.
                continue
            key = (courier, service)
            if key in seen or rate.get("is_flat_rate") or rate.get("is_use_wood_packing"):
                # Flat-rate/wood-packing rate requests require an extended
                # booking contract; do not present an unbookable rate.
                continue
            cost, insurance = _amount(rate.get("price"), "everpro"), _amount(rate.get("insurance_price", 0), "everpro")
            seen.add(key)
            options.append({"courier_code": courier, "service_code": service,
                            "courier_name": str(rate.get("logistic_name") or courier)[:255],
                            "service_label": str(rate.get("rate_name") or service)[:255],
                            "cost": cost, "insurance_cost": insurance,
                            "etd": f"{rate.get('min_duration', '?')}–{rate.get('max_duration', '?')} {rate.get('duration_type') or 'hari'}"[:128],
                            "raw": rate})
    return options


async def shipping_options(user_id: str, address_id: str, selected_ids: list[str]) -> dict:
    provider = shipping_provider()
    if provider == "disabled":
        raise HTTPException(503, "Pengiriman belum diaktifkan")
    async with read_session() as s:
        address = await s.scalar(select(m.Address).where(m.Address.id == address_id, m.Address.user_id == user_id))
        if address is None:
            raise HTTPException(404, "Alamat tidak ditemukan")
        items, weight = await priced_cart(s, user_id, selected_ids)
        weight = max(weight, 100)
        if not items:
            raise HTTPException(400, "Tidak ada item yang dipilih")
        if provider == "mock":
            from services_mock import everpro_cost
            return {"options": [{**o, "provider": "everpro-mock", "quote_id": None} for o in everpro_cost(address.province, weight)],
                    "weight_gram": weight, "provider": "everpro-mock"}
        client = get_everpro_client()
        settings = client.settings
        _shipping_address_valid(address)
        destination = await canonical_shipping_location(address, client)
        fingerprint, snapshot = shipping_fingerprint(items, address, settings)
        value = sum((item.subtotal for item in items), ZERO).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        if value <= 0:
            raise HTTPException(422, "Nilai barang untuk pengiriman harus lebih besar dari nol")
        request = {
            "origin_postal_code": settings.origin_postal_code, "origin_sub_district_name": settings.origin_subdistrict,
            "destination_postal_code": destination['postal_code'], "destination_sub_district_name": destination['subdistrict'],
            "weight": float(Decimal(weight) / 1000), "item_price": int(value), "package_type_id": settings.package_type_id,
            "shipment_type": settings.shipment_type, "length": settings.length_cm, "width": settings.width_cm,
            "height": settings.height_cm, "is_cod": False, "is_use_insurance": settings.insurance, "include_flat_rate": False,
        }
    try:
        response = await client.rates(request)
        options = _rate_options(response)
    except ProviderError as exc:
        raise _safe_error(exc, "menghitung ongkir") from None
    expires = utcnow() + timedelta(seconds=settings.quote_ttl_seconds)
    result = []
    async with session_scope() as s:
        await lock_user(s, user_id)
        current_address = await s.get(m.Address, address_id)
        if current_address is None or current_address.user_id != user_id:
            raise HTTPException(409, "Alamat berubah; hitung kembali ongkir")
        current_items, _ = await priced_cart(s, user_id, selected_ids)
        if shipping_fingerprint(current_items, current_address, settings)[0] != fingerprint:
            raise HTTPException(409, "Keranjang/alamat berubah; hitung kembali ongkir")
        for option in options:
            row = m.ShippingQuote(
                id=gen_id("sqt"), user_id=user_id, provider="everpro", origin_id=settings.origin_postal_code,
                destination_id=address.postal_code, courier_code=option["courier_code"], service_code=option["service_code"],
                service_label=option["service_label"], weight_gram=weight, cost=option["cost"], insurance_cost=option["insurance_cost"],
                currency="IDR", estimated_delivery=option["etd"], cart_fingerprint=fingerprint, expires_at=expires,
                request_payload={**snapshot, "rate_request": request}, response_payload=option["raw"],
            )
            s.add(row)
            result.append({"quote_id": row.id, "courier_code": row.courier_code, "courier_name": option["courier_name"],
                           "service_code": row.service_code, "service_label": row.service_label,
                           "cost": float(row.cost + row.insurance_cost), "insurance_cost": float(row.insurance_cost),
                           "etd": option["etd"], "expires_at": expires.isoformat(), "provider": "everpro"})
        await s.flush()
    return {"options": result, "weight_gram": weight, "provider": "everpro"}


async def validated_shipping_quote(s, user: m.User, req, address: m.Address, items, *, lock: bool = False) -> dict:
    quote_id = getattr(req, "shipping_quote_id", None)
    if not quote_id:
        raise HTTPException(422, "Pilih ongkir Everpro yang masih berlaku")
    query = select(m.ShippingQuote).where(m.ShippingQuote.id == quote_id, m.ShippingQuote.user_id == user.user_id)
    row = await s.scalar(query.with_for_update() if lock else query)
    if row is None or row.provider != "everpro" or row.currency != "IDR":
        raise HTTPException(422, "Pilihan ongkir tidak valid")
    if row.expires_at <= utcnow():
        raise HTTPException(409, "Penawaran ongkir kedaluwarsa; hitung kembali ongkir")
    settings = EverproSettings.from_env()
    if row.cart_fingerprint != shipping_fingerprint(items, address, settings)[0]:
        raise HTTPException(409, "Keranjang/alamat berubah; hitung kembali ongkir")
    if row.courier_code != req.courier_code or row.service_code != req.service_code:
        raise HTTPException(422, "Layanan pengiriman tidak sesuai penawaran")
    return {"quote_id": row.id, "courier_code": row.courier_code, "service_code": row.service_code,
            "service_label": row.service_label or row.service_code,
            "courier_name": (row.response_payload or {}).get("logistic_name", row.courier_code),
            "cost": row.cost + row.insurance_cost, "provider": "everpro"}


async def _order_and_payment(s, order_id: str, *, lock: bool = False, provider: str | None = None):
    oq = select(m.Order).where(m.Order.id == order_id)
    order = await s.scalar(oq.with_for_update() if lock else oq)
    pq = select(m.Payment).where(m.Payment.order_id == order_id)
    if provider:
        pq = pq.where(m.Payment.provider == provider)
    pq = pq.order_by(m.Payment.created_at.desc(), m.Payment.id.desc()).limit(1)
    payment = await s.scalar(pq.with_for_update() if lock else pq)
    if order is None or payment is None:
        raise HTTPException(404, "Pembayaran tidak ditemukan")
    return order, payment


async def payment_response(order_id: str) -> dict:
    async with read_session() as s:
        order, payment = await _order_and_payment(s, order_id)
        return {"order": await order_dict(s, order), "payment": payment_payload(order, payment)}


async def ensure_doku_payment(order_id: str) -> dict:
    client = get_doku_client()
    settings = client.settings
    async with read_session() as s:
        order, payment = await _order_and_payment(s, order_id, provider="doku")
        owner = order.user_id
    async with session_scope() as s:
        await lock_user(s, owner, active=False)
        order, payment = await _order_and_payment(s, order_id, lock=True, provider="doku")
        if payment.provider != "doku":
            raise HTTPException(409, "Penyedia pembayaran order berbeda")
        if payment.payment_url or payment.status != "pending":
            return payment_payload(order, payment)
        if order.status != "pending_payment" or order.payment_status != "pending":
            raise HTTPException(409, "Order tidak dapat dibayar")
        previous = await s.scalar(select(m.PaymentLog).where(m.PaymentLog.payment_id == payment.id,
                                                           m.PaymentLog.action == "doku_request").order_by(m.PaymentLog.created_at).limit(1))
        if previous:
            request = previous.payload
            if await _saved_doku_context(s, payment.id) != doku_context(settings):
                raise HTTPException(409, "Konfigurasi akun DOKU berbeda dari permintaan awal; lakukan rekonsiliasi")
        else:
            if order.reservation_expires_at and order.reservation_expires_at <= utcnow():
                raise HTTPException(409, "Waktu membuat pembayaran sudah berakhir")
            address = await s.get(m.OrderAddress, order_id)
            user = await s.get(m.User, owner)
            return_url = settings.frontend_url + "/payment/" + order.order_number
            request = {
                "order": {"amount": int(_amount(order.total, "doku", positive=True)), "invoice_number": order.order_number,
                          "currency": "IDR", "callback_url": return_url, "callback_url_cancel": return_url,
                          "auto_redirect": True, "recover_abandoned_cart": False},
                "payment": {"payment_due_date": settings.due_minutes, "type": "SALE"},
                "customer": {"id": owner, "name": user.name, "email": user.email, "phone": address.phone,
                             "address": address.street, "country": "ID", "city": address.city, "postcode": address.postal_code},
            }
            if settings.notification_override_url:
                request["additional_info"] = {"override_notification_url": settings.notification_override_url}
            s.add(m.PaymentLog(id=gen_id("plg"), order_id=order_id, payment_id=payment.id, provider="doku",
                               action="doku_request", payload=request))
            s.add(m.PaymentLog(id=gen_id("plg"), order_id=order_id, payment_id=payment.id, provider="doku", action="doku_configuration",
                               payload=doku_context(settings)))
        last_attempt = await s.scalar(select(m.PaymentLog).where(m.PaymentLog.payment_id == payment.id,
            m.PaymentLog.action == "doku_attempt").order_by(m.PaymentLog.created_at.desc(), m.PaymentLog.id).limit(1))
        if last_attempt and last_attempt.created_at > utcnow() - timedelta(seconds=30):
            raise HTTPException(409, "Permintaan DOKU sedang diproses. Tunggu sebentar lalu periksa kembali.", headers={"Retry-After": "30"})
        s.add(m.PaymentLog(id=gen_id("plg"), order_id=order_id, payment_id=payment.id, provider="doku",
                           action="doku_attempt", payload={"request_id": payment.request_id}))
        request_id, payment_id = payment.request_id, payment.id
        await s.flush()
    try:
        response = await client.create_payment(request_id, request)
        response_data = response.get("response") or {}
        if not isinstance(response_data, dict):
            raise ProviderError("doku", "invalid_response", uncertain=True)
        remote_order, remote_payment = response_data.get("order") or {}, response_data.get("payment") or {}
        if not isinstance(remote_order, dict) or not isinstance(remote_payment, dict):
            raise ProviderError("doku", "invalid_response", uncertain=True)
        if remote_order.get("invoice_number") != request["order"]["invoice_number"] or _amount(remote_order.get("amount"), "doku") != Decimal(request["order"]["amount"]):
            raise ProviderError("doku", "response_order_mismatch", uncertain=True)
        if remote_order.get("currency", "IDR") != "IDR":
            raise ProviderError("doku", "response_currency_mismatch", uncertain=True)
        url = safe_checkout_url(remote_payment.get("url"))
        external = remote_payment.get("token_id")
        if not isinstance(external, str) or not 1 <= len(external) <= 191:
            raise ProviderError("doku", "invalid_payment_reference", uncertain=True)
        try:
            expiry = datetime.strptime(remote_payment["expired_date"], "%Y%m%d%H%M%S").replace(tzinfo=ZoneInfo("Asia/Jakarta")).astimezone(timezone.utc)
        except (KeyError, ValueError, TypeError):
            raise ProviderError("doku", "invalid_expiry", uncertain=True) from None
    except ProviderError as exc:
        async with session_scope() as s:
            await lock_user(s, owner, active=False)
            s.add(m.PaymentLog(id=gen_id("plg"), order_id=order_id, payment_id=payment_id, provider="doku",
                               action="doku_create_error", response={"code": exc.code, "uncertain": exc.uncertain}))
        raise _safe_error(exc, "membuat tautan pembayaran") from None
    async with session_scope() as s:
        await lock_user(s, owner, active=False)
        order, payment = await _order_and_payment(s, order_id, lock=True, provider="doku")
        payment.external_id = external
        payment.payment_url = url
        payment.expires_at = expiry
        if order.status == "pending_payment" and order.payment_status == "pending":
            order.reservation_expires_at = expiry
            await s.execute(update(m.StockReservation).where(m.StockReservation.order_id == order_id,
                m.StockReservation.status == "active").values(expires_at=expiry))
            item_ids = select(m.OrderItem.id).where(m.OrderItem.order_id == order_id)
            await s.execute(update(m.FlashSaleReservation).where(m.FlashSaleReservation.order_item_id.in_(item_ids),
                m.FlashSaleReservation.status == "active").values(expires_at=expiry))
        s.add(m.PaymentLog(id=gen_id("plg"), order_id=order_id, payment_id=payment.id, provider="doku",
                           action="doku_created", response={"token_id": external, "expires_at": expiry.isoformat()}))
        await s.flush()
        return payment_payload(order, payment)


async def ensure_payment(order_id: str) -> dict:
    async with read_session() as s:
        _, payment = await _order_and_payment(s, order_id)
        provider = payment.provider
    if provider == "doku-mock":
        from mysql.commerce import ensure_mock_payment
        return await ensure_mock_payment(order_id)
    if provider != "doku":
        raise HTTPException(409, "Penyedia pembayaran order memerlukan rekonsiliasi")
    return await ensure_doku_payment(order_id)


async def apply_doku_event(payload: dict, event_key: str, payload_hash: str, *, source: str = "notification",
                           authenticated_context: dict | None = None) -> dict:
    """Accept a verified DOKU event once; money/stock resolve in one transaction."""
    from mysql.commerce import _resolve_stock, _resolve_promotions, _release_locked
    remote_order, transaction = payload.get("order"), payload.get("transaction")
    if not isinstance(remote_order, dict) or not isinstance(transaction, dict):
        raise HTTPException(422, "Payload DOKU tidak valid")
    invoice, status = remote_order.get("invoice_number"), transaction.get("status")
    if not isinstance(invoice, str) or not 1 <= len(invoice) <= 64 or not isinstance(status, str) or not 1 <= len(status) <= 128:
        raise HTTPException(422, "Referensi/status DOKU tidak valid")
    context = authenticated_context if authenticated_context is not None else doku_context(DokuSettings.from_env())
    async with read_session() as s:
        payment = await s.scalar(select(m.Payment).where(m.Payment.provider == "doku", m.Payment.merchant_reference == invoice))
        if payment is None:
            raise HTTPException(404, "Referensi pembayaran tidak ditemukan")
        order = await s.get(m.Order, payment.order_id)
        owner, order_id, payment_id = order.user_id, order.id, payment.id
    async with session_scope() as s:
        user = await lock_user(s, owner, active=False)
        order = await s.scalar(select(m.Order).where(m.Order.id == order_id).with_for_update())
        payment = await s.scalar(select(m.Payment).where(m.Payment.id == payment_id, m.Payment.order_id == order_id).with_for_update())
        event = await s.scalar(select(m.IntegrationWebhookEvent).where(
            m.IntegrationWebhookEvent.provider == "doku", m.IntegrationWebhookEvent.event_key == event_key))
        context_matches = await _saved_doku_context(s, payment.id) == context
        if event:
            if event.order_id != order_id or event.payload_hash != payload_hash:
                raise HTTPException(409, "Identitas notifikasi sudah digunakan")
            if not context_matches:
                raise HTTPException(409, "Akun/lingkungan notifikasi tidak cocok dengan payment intent")
            return {"ok": True, "duplicate": True, "reconciliation_required": event.status == "failed"}
        event = m.IntegrationWebhookEvent(
            id=gen_id("evt"), provider="doku", event_key=event_key, payload_hash=payload_hash,
            order_id=order_id, event_type=status, signature_verified=source == "notification", payload=payload,
            status="received", attempts=1,
        )
        s.add(event)
        await s.flush()
        try:
            received_amount = _amount(remote_order.get("amount"), "doku")
        except ProviderError:
            received_amount = None
        if not context_matches:
            event.status, event.error_code = "failed", "payment_account_or_environment_mismatch"
        elif received_amount != payment.amount or payment.amount != order.total or remote_order.get("currency", "IDR") != payment.currency or payment.currency != order.currency:
            event.status, event.error_code = "failed", "payment_amount_or_currency_mismatch"
        elif status == "SUCCESS" and (transaction.get("type") is None or isinstance(transaction.get("type"), str) and transaction.get("type") in {"SALE", "INSTALLMENT", "CAPTURE", "RECURRING"}):
            recovery = payment.status == "paid" and order.payment_status == "paid" and order.status == "pending_payment"
            if payment.status == "paid" and order.payment_status == "paid" and order.status in {"paid", "processing", "shipped", "completed"}:
                event.status = "processed"
            elif not recovery and (order.status != "pending_payment" or order.payment_status != "pending" or payment.status != "pending"):
                # Money can arrive after a provider expiry/cancellation. Keep
                # its fact, never resurrect released inventory or ship it.
                payment.status, payment.paid_at = "paid", payment.paid_at or utcnow()
                order.payment_status = "paid"
                event.status, event.error_code = "failed", "late_payment_requires_reconciliation"
            else:
                payment.status, payment.paid_at = "paid", payment.paid_at or utcnow()
                order.payment_status = "paid"
                # If a migrated/inconsistent inventory ledger prevents sale,
                # retain the authentic money receipt and flag an operator task.
                # A savepoint prevents partial stock/promo resolution.
                try:
                    async with s.begin_nested():
                        await _resolve_stock(s, order, sold=True, status="confirmed")
                        await _resolve_promotions(s, order, sold=True, status="confirmed")
                except HTTPException:
                    await s.refresh(order)
                    await s.refresh(payment)
                    event.status, event.error_code = "failed", "stock_or_promotion_reconciliation"
                else:
                    order.status = "paid"
                    channel_data = payload.get("channel") or {}
                    channel = channel_data.get("id") if isinstance(channel_data, dict) else None
                    payment.channel = str(channel)[:64] if channel else None
                    event.status = "processed"
                    s.add(m.OrderStatusLog(id=gen_id("ols"), order_id=order_id, status="paid", note="Pembayaran terverifikasi DOKU"))
                    if recovery:
                        unresolved = (await s.scalars(select(m.IntegrationWebhookEvent).where(
                            m.IntegrationWebhookEvent.order_id == order_id, m.IntegrationWebhookEvent.provider == "doku",
                            m.IntegrationWebhookEvent.status == "failed",
                            m.IntegrationWebhookEvent.error_code == "stock_or_promotion_reconciliation",
                        ).order_by(m.IntegrationWebhookEvent.received_at, m.IntegrationWebhookEvent.id))).all()
                        for prior in unresolved:
                            # Keep the original payload and error_code as the
                            # history; the new verified event and audit log
                            # explain why its outstanding flag is now closed.
                            prior.status, prior.processed_at = "processed", utcnow()
                            prior.attempts += 1
                        s.add(m.PaymentLog(id=gen_id("plg"), order_id=order_id, payment_id=payment.id, provider="doku",
                            action="doku_reconciliation_resolved", payload={"event_ids": [prior.id for prior in unresolved],
                                "resolution_event_id": event.id, "source": source}))
                    quote = await s.get(m.ShippingQuote, order.shipping_quote_id) if order.shipping_quote_id else None
                    shipping = "everpro" if quote and quote.provider == "everpro" else "everpro-mock" if mock_enabled() else None
                    existing_shipment = await s.scalar(select(m.Shipment.id).where(m.Shipment.order_id == order_id).limit(1))
                    if shipping and not existing_shipment:
                        s.add(m.Shipment(id=gen_id("shp"), order_id=order_id, provider=shipping,
                            request_id="shipment:" + order_id, courier_code=order.shipping_courier,
                            service_code=order.shipping_service, cost=quote.cost + quote.insurance_cost if quote else order.shipping_cost,
                            currency=order.currency, status="pending"))
        elif status == "EXPIRED" and source == "status_query" and order.status == "pending_payment" and order.payment_status == "pending" and payment.expires_at and payment.expires_at + timedelta(seconds=60) <= utcnow():
            await _release_locked(s, order, user, "expired", provider_confirmed=True, note="DOKU mengonfirmasi pembayaran kedaluwarsa")
            event.status = "processed"
        elif status == "REFUNDED":
            event.status, event.error_code = "failed", "refund_requires_reconciliation"
        else:
            # Checkout FAILED is not terminal: the customer may change method.
            # A channel's EXPIRED notification is also not the checkout's
            # authority to release stock before an authenticated status query.
            event.status = "ignored"
        event.processed_at = utcnow()
        s.add(m.PaymentLog(id=gen_id("plg"), order_id=order_id, payment_id=payment.id, provider="doku",
                           action="doku_" + source, payload={"event_id": event.id, "status": status},
                           response={"result": event.status, "error_code": event.error_code}))
        await s.flush()
        return {"ok": True, "reconciliation_required": event.status == "failed"}


async def refresh_doku_payment(order_id: str) -> dict:
    client = get_doku_client()
    async with read_session() as s:
        order, payment = await _order_and_payment(s, order_id, provider="doku")
        owner = order.user_id
    async with session_scope() as s:
        await lock_user(s, owner, active=False)
        order, payment = await _order_and_payment(s, order_id, lock=True, provider="doku")
        if payment.provider != "doku":
            raise HTTPException(409, "Order bukan pembayaran DOKU")
        if await _saved_doku_context(s, payment.id) != doku_context(client.settings):
            raise HTTPException(409, "Akun/lingkungan DOKU tidak cocok dengan payment intent; pulihkan konfigurasi asal sebelum rekonsiliasi")
        last = await s.scalar(select(m.PaymentLog).where(m.PaymentLog.payment_id == payment.id,
            m.PaymentLog.action.in_(("doku_status_attempt", "doku_attempt"))).order_by(m.PaymentLog.created_at.desc(), m.PaymentLog.id).limit(1))
        if last and last.created_at > utcnow() - timedelta(seconds=60):
            raise HTTPException(429, "Periksa status DOKU paling cepat setiap 60 detik", headers={"Retry-After": "60"})
        invoice = payment.merchant_reference
        s.add(m.PaymentLog(id=gen_id("plg"), order_id=order_id, payment_id=payment.id, provider="doku", action="doku_status_attempt"))
        await s.flush()
    try:
        payload = await client.check_status(invoice)
    except ProviderError as exc:
        raise _safe_error(exc, "memeriksa pembayaran") from None
    if (payload.get("order") or {}).get("invoice_number") != invoice:
        raise HTTPException(502, "Respons status pembayaran tidak cocok")
    digest = _digest(payload)
    # Include the query time bucket: EXPIRED observed before the reservation
    # boundary must not suppress a later authoritative expiry after the grace.
    event_key = "status:" + digest + ":" + str(int(utcnow().timestamp() // 60))
    await apply_doku_event(payload, event_key, digest, source="status_query", authenticated_context=doku_context(client.settings))
    return await payment_response(order_id)


async def expire_doku_order(order_id: str, status: str, *, owner_id: str | None = None, due_only: bool = False) -> bool:
    from mysql.commerce import _release_locked
    async with read_session() as s:
        order, payment = await _order_and_payment(s, order_id, provider="doku")
        owner = order.user_id
        if owner_id is not None and owner_id != owner:
            raise HTTPException(404, "Order tidak ditemukan")
        if order.status in {"expired", "cancelled"}:
            return False
        if order.status != "pending_payment" or order.payment_status != "pending":
            if owner_id:
                raise HTTPException(409, "Order yang sudah dibayar tidak dapat dibatalkan di sini")
            return False
        if due_only and (not order.reservation_expires_at or order.reservation_expires_at > utcnow()):
            return False
    async with session_scope() as s:
        user = await lock_user(s, owner, active=False)
        order, payment = await _order_and_payment(s, order_id, lock=True, provider="doku")
        attempt = await s.scalar(select(m.PaymentLog.id).where(m.PaymentLog.payment_id == payment.id,
                                                             m.PaymentLog.action == "doku_attempt").limit(1))
        if not attempt:
            # No provider request could have left this process. The same user
            # and order locks serialize this branch against first creation.
            return await _release_locked(s, order, user, status)
    result = await refresh_doku_payment(order_id)
    if result["order"]["status"] == "expired":
        return True
    if owner_id is not None or status == "cancelled":
        raise HTTPException(409, "Pembayaran DOKU masih aktif atau menunggu rekonsiliasi. Pembatalan tersedia setelah DOKU mengonfirmasi kedaluwarsa.")
    return False


async def _shipment_context(s, order_id: str, *, lock: bool = False):
    oq = select(m.Order).where(m.Order.id == order_id)
    order = await s.scalar(oq.with_for_update() if lock else oq)
    sq = select(m.Shipment).where(m.Shipment.order_id == order_id, m.Shipment.provider == "everpro").order_by(m.Shipment.created_at, m.Shipment.id).limit(1)
    shipment = await s.scalar(sq.with_for_update() if lock else sq)
    if order is None or shipment is None:
        raise HTTPException(404, "Pengiriman Everpro tidak ditemukan")
    if order.payment_status != "paid" or order.status not in {"paid", "processing", "shipped", "completed"}:
        raise HTTPException(409, "Pengiriman hanya tersedia untuk pesanan yang sudah dibayar")
    return order, shipment


async def shipment_response(order_id: str) -> dict:
    async with read_session() as s:
        order, shipment = await _shipment_context(s, order_id)
        data = row_dict(shipment)
        data.pop("request_id", None)
        return {"shipment": data, "order": await order_dict(s, order)}


async def shipment_pickup_times(order_id: str) -> dict:
    client = get_everpro_client()
    async with read_session() as s:
        order, shipment = await _shipment_context(s, order_id)
        quote = await s.get(m.ShippingQuote, order.shipping_quote_id) if order.shipping_quote_id else None
        kind = ((quote.request_payload or {}).get("origin") or {}).get("shipment_type") if quote else client.settings.shipment_type
        rate_code = shipment.service_code
    if kind == "DROP":
        return {"times": [], "shipment_type": "DROP"}
    try:
        response = await client.pickup_times(rate_code)
    except ProviderError as exc:
        raise _safe_error(exc, "membaca jadwal penjemputan") from None
    times, seen = [], set()
    groups = (response.get("data") or {}).get("available_pickup_time") or []
    for group in groups:
        if group.get("rate_code") != rate_code:
            continue
        for day in group.get("pickup_time_list") or []:
            for slot in day.get("pickup_times") or []:
                if slot.get("cut_off") or slot.get("condition") is False:
                    continue
                try:
                    start = datetime.fromisoformat(slot["start_at"].replace("Z", "+00:00"))
                    if start.tzinfo is None or start <= utcnow():
                        continue
                    value = int(start.timestamp())
                except (KeyError, ValueError, TypeError):
                    continue
                if value not in seen:
                    seen.add(value)
                    local = start.astimezone(ZoneInfo("Asia/Jakarta"))
                    times.append({"label": local.strftime("%d/%m/%Y ") + str(slot.get("time_range") or local.strftime("%H:%M")) + " WIB", "value": value})
    return {"times": sorted(times, key=lambda v: v["value"]), "shipment_type": "PICKUP"}


def _booking_payload(order: m.Order, address: m.OrderAddress, quote: m.ShippingQuote, pickup_time: int | None) -> dict:
    stored = quote.request_payload or {}
    origin, rate_request = stored.get("origin") or {}, stored.get("rate_request") or {}
    if not origin or not rate_request:
        raise HTTPException(409, "Snapshot ongkir tidak lengkap; pesanan memerlukan rekonsiliasi")
    payload = {
        "client_order_no": order.order_number, "order_reference_id": order.order_number,
        "package_desc": "Kacamata dan aksesori optik", "package_price": rate_request["item_price"],
        "package_type_id": origin["package_type_id"], "package_count": 1,
        "weight": float(Decimal(quote.weight_gram) / 1000),
        "length": origin["length"], "width": origin["width"], "height": origin["height"],
        "is_cod": False, "is_use_insurance": quote.insurance_cost > 0, "insurance_price": int(quote.insurance_cost),
        "rate_code": quote.service_code, "shipment_price": int(quote.cost), "shipment_type": origin["shipment_type"],
        "receiver_name": address.recipient, "receiver_phone": address.phone, "receiver_address": address.street,
        "receiver_postal_code": address.postal_code, "receiver_sub_district_name": address.subdistrict or "",
        "shipper_name": origin["name"], "shipper_phone": origin["phone"], "shipper_address": origin["address"],
        "shipper_postal_code": origin["postal_code"], "shipper_sub_district_name": origin["subdistrict"],
    }
    if origin.get("email"):
        payload["shipper_email"] = origin["email"]
    if payload["shipment_type"] == "PICKUP":
        if not pickup_time:
            raise HTTPException(422, "Pilih waktu penjemputan Everpro")
        payload["pickup_time"] = pickup_time
    return payload


async def book_shipment(order_id: str, pickup_time: int | None = None) -> dict:
    client = get_everpro_client()
    async with read_session() as s:
        order, shipment = await _shipment_context(s, order_id)
        owner = order.user_id
        previous = await s.scalar(select(m.ShipmentLog).where(m.ShipmentLog.shipment_id == shipment.id,
            m.ShipmentLog.action == "everpro_request").order_by(m.ShipmentLog.created_at).limit(1))
        existing_request = previous.payload if previous else None
        already_created = shipment.external_id is not None or shipment.status != "pending" or shipment.tracking_number is not None
        quote = await s.get(m.ShippingQuote, order.shipping_quote_id) if order.shipping_quote_id else None
        if quote is None or quote.provider != "everpro":
            raise HTTPException(409, "Order tidak memiliki penawaran Everpro yang dapat dipakai untuk pemesanan")
        expected_context = {"environment": client.settings.environment, "base_url": client.settings.base_url,
                            "account": hashlib.sha256(client.settings.client_key.encode()).hexdigest()}
        if (quote.request_payload or {}).get("provider") != expected_context:
            raise HTTPException(409, "Akun/lingkungan Everpro berbeda dari penawaran pesanan; lakukan rekonsiliasi")
        address = await s.get(m.OrderAddress, order_id)
        if existing_request:
            if pickup_time is not None and pickup_time != existing_request.get("pickup_time"):
                raise HTTPException(409, "Permintaan pengiriman sudah tersimpan; jadwal tidak boleh berubah saat retry")
            request = existing_request
        else:
            request = _booking_payload(order, address, quote, pickup_time)
    if already_created:
        return await refresh_shipment(order_id)
    if request["shipment_type"] == "PICKUP" and not existing_request:
        slots = await shipment_pickup_times(order_id)
        if pickup_time not in {slot["value"] for slot in slots["times"]}:
            raise HTTPException(422, "Jadwal penjemputan tidak tersedia; pilih waktu terbaru")
    async with session_scope() as s:
        await lock_user(s, owner, active=False)
        order, shipment = await _shipment_context(s, order_id, lock=True)
        if shipment.external_id or shipment.status != "pending" or shipment.tracking_number:
            return {"shipment": row_dict(shipment), "order": await order_dict(s, order)}
        previous = await s.scalar(select(m.ShipmentLog).where(m.ShipmentLog.shipment_id == shipment.id,
            m.ShipmentLog.action == "everpro_request").order_by(m.ShipmentLog.created_at).limit(1))
        repeated = previous is not None
        if previous and previous.payload != request:
            raise HTTPException(409, "Permintaan pengiriman berubah; gunakan referensi yang sudah tersimpan")
        last = await s.scalar(select(m.ShipmentLog).where(m.ShipmentLog.shipment_id == shipment.id,
            m.ShipmentLog.action == "everpro_booking_attempt").order_by(m.ShipmentLog.created_at.desc(), m.ShipmentLog.id).limit(1))
        if last and last.created_at > utcnow() - timedelta(seconds=30):
            raise HTTPException(409, "Pemesanan Everpro sedang diproses", headers={"Retry-After": "30"})
        if not previous:
            s.add(m.ShipmentLog(id=gen_id("slg"), order_id=order_id, shipment_id=shipment.id,
                               provider="everpro", action="everpro_request", payload=request))
        s.add(m.ShipmentLog(id=gen_id("slg"), order_id=order_id, shipment_id=shipment.id,
                           provider="everpro", action="everpro_booking_attempt"))
        shipment_id = shipment.id
        await s.flush()
    try:
        # If the last POST timed out, the provider may already have created the
        # shipment. Look it up before resending the exact same client_order_no.
        response, recovered = None, False
        if repeated:
            try:
                response = await client.order_detail(request["client_order_no"])
                recovered = True
            except ProviderError as exc:
                if exc.code != "not_found":
                    raise
        if response is None:
            try:
                response = await client.create_shipment(request)
            except ProviderError as exc:
                if exc.code != "duplicate_order":
                    raise
                response = await client.order_detail(request["client_order_no"])
                recovered = True
        data = response.get("data", response)
        if not isinstance(data, dict) or data.get("client_order_no") != request["client_order_no"]:
            raise ProviderError("everpro", "shipment_reference_mismatch", uncertain=True)
        actual_cost = _amount(data.get("actual_price", data.get("shipment_price", request["shipment_price"])), "everpro")
        actual_insurance = _amount(data.get("actual_insurance_price", data.get("insurance_price", request["insurance_price"])), "everpro")
    except ProviderError as exc:
        async with session_scope() as s:
            await lock_user(s, owner, active=False)
            s.add(m.ShipmentLog(id=gen_id("slg"), order_id=order_id, shipment_id=shipment_id, provider="everpro",
                               action="everpro_booking_error", response={"code": exc.code, "uncertain": exc.uncertain}))
        raise _safe_error(exc, "membuat pengiriman") from None
    async with session_scope() as s:
        await lock_user(s, owner, active=False)
        order, shipment = await _shipment_context(s, order_id, lock=True)
        reference = data.get("shipment_order_no") or request["client_order_no"]
        if not isinstance(reference, str) or len(reference) > 191:
            raise HTTPException(502, "Referensi pengiriman tidak valid")
        shipment.external_id = reference
        if shipment.status == "pending":
            shipment.status = "created"
        shipment.cost = actual_cost + actual_insurance
        if order.status == "paid":
            order.status = "processing"
            s.add(m.OrderStatusLog(id=gen_id("ols"), order_id=order_id, status="processing", note="Pemesanan pengiriman Everpro diterima"))
        if order.shipment_status == "pending":
            order.shipment_status = "created"
        s.add(m.ShipmentLog(id=gen_id("slg"), order_id=order_id, shipment_id=shipment.id, provider="everpro",
                           action="everpro_recovered" if recovered else "everpro_created", response=data))
        await s.flush()
    # Booking acceptance and AWB assignment are separate in Everpro. A failed
    # status lookup does not undo the accepted booking or send another POST.
    try:
        result = await refresh_shipment(order_id)
    except HTTPException:
        result = await shipment_response(order_id)
        result["tracking_pending"] = True
    result["price_adjusted"] = actual_cost != Decimal(request["shipment_price"]) or actual_insurance != Decimal(request["insurance_price"])
    return result


TRACKING_STATUS = {
    "WAITING": "created", "CREATED": "created", "PICKEDUP": "picked_up", "PICKED UP": "picked_up",
    "IN PROCESS": "in_transit", "IN_TRANSIT": "in_transit", "ON DELIVERY": "in_transit",
    "REPEAT DELIVERY": "in_transit", "DELIVERED": "delivered", "RETURN": "returned", "RETURNED": "returned",
    "CANCELED": "cancelled", "CANCELLED": "cancelled", "EXPIRED": "cancelled",
    "LOST/BROKEN": "failed", "FORCE MAJEURE": "failed", "FAILED PICKUP": "failed",
    "REJECTED": "failed", "IN TROUBLE": "failed", "IN PROCESS RETURN": "in_transit",
}


def _tracking_update(s, order: m.Order, shipment: m.Shipment, data: dict) -> None:
    awb = data.get("awb_number")
    if awb:
        if not isinstance(awb, str) or len(awb) > 191 or (shipment.tracking_number and shipment.tracking_number != awb):
            raise HTTPException(409, "Nomor resi tidak cocok dengan pengiriman")
        shipment.tracking_number = awb
    code = data.get("tracking_code")
    if code is not None and (not isinstance(code, str) or len(code) > 255):
        raise HTTPException(422, "Status pengiriman tidak valid")
    mapped = TRACKING_STATUS.get((code or "").upper())
    if not mapped and awb and shipment.status == "pending":
        mapped = "created"
    rank = {"pending": 0, "created": 1, "picked_up": 2, "in_transit": 3, "delivered": 4}
    terminal = shipment.status in {"delivered", "returned", "cancelled"} or shipment.carrier_status in {"LOST/BROKEN", "FORCE MAJEURE"}
    regression = (mapped in rank and shipment.status in rank and rank[mapped] < rank[shipment.status]) or (shipment.status == "failed" and mapped == "created")
    if code and ((not terminal and not regression) or mapped == shipment.status):
        shipment.carrier_status = code
    if mapped and not terminal and not regression:
        shipment.status, order.shipment_status = mapped, mapped
        if mapped in {"picked_up", "in_transit", "delivered"}:
            if shipment.shipped_at is None:
                shipment.shipped_at = utcnow()
            if order.status in {"paid", "processing"}:
                order.status = "shipped"
                s.add(m.OrderStatusLog(id=gen_id("ols"), order_id=order.id, status="shipped", note="Everpro mengonfirmasi proses pengiriman"))
        if mapped == "delivered" and shipment.delivered_at is None:
            received = data.get("delivered_at")
            try:
                value = datetime.fromtimestamp(received, timezone.utc) if isinstance(received, (int, float)) and not isinstance(received, bool) else utcnow()
                shipment.delivered_at = value if order.created_at <= value <= utcnow() + timedelta(minutes=5) else utcnow()
            except (ValueError, OverflowError, OSError):
                shipment.delivered_at = utcnow()
    shipment.last_checked_at = utcnow()


async def refresh_shipment(order_id: str) -> dict:
    client = get_everpro_client()
    async with read_session() as s:
        order, shipment = await _shipment_context(s, order_id)
        owner, number, awb, label = order.user_id, order.order_number, shipment.tracking_number, shipment.label_url
        if not shipment.external_id and not awb and shipment.status == "pending":
            previous = await s.scalar(select(m.ShipmentLog.id).where(m.ShipmentLog.shipment_id == shipment.id,
                m.ShipmentLog.action == "everpro_request").limit(1))
            if not previous:
                return {"shipment": row_dict(shipment), "order": await order_dict(s, order)}
    try:
        response = await client.tracking(awb) if awb else await client.order_detail(number)
        data = response.get("data") or {}
        if not isinstance(data, dict):
            raise ProviderError("everpro", "invalid_tracking_response")
        if awb and data.get("awb_number") != awb:
            raise ProviderError("everpro", "tracking_reference_mismatch")
        if not awb and data.get("client_order_no") != number:
            raise ProviderError("everpro", "tracking_reference_mismatch")
        new_awb = awb or data.get("awb_number")
        if new_awb and not label:
            try:
                label_response = await client.label(new_awb)
                label_data = label_response.get("data") or {}
                candidate = label_data.get("url_label_pdf") if isinstance(label_data, dict) else None
                if not isinstance(candidate, str):
                    candidate = ""
                p = urlsplit(candidate or "")
                if p.scheme == "https" and p.hostname and not p.username and not p.password:
                    label = candidate
            except (ProviderError, ValueError):
                pass
    except ProviderError as exc:
        raise _safe_error(exc, "memperbarui status pengiriman") from None
    async with session_scope() as s:
        await lock_user(s, owner, active=False)
        order, shipment = await _shipment_context(s, order_id, lock=True)
        if not shipment.external_id:
            reference = data.get("shipment_order_no") or number
            if not isinstance(reference, str) or not 1 <= len(reference) <= 191:
                raise HTTPException(502, "Referensi pengiriman tidak valid")
            shipment.external_id = reference
        _tracking_update(s, order, shipment, data)
        if label:
            shipment.label_url = label
        s.add(m.ShipmentLog(id=gen_id("slg"), order_id=order_id, shipment_id=shipment.id,
                           provider="everpro", action="tracking_poll", response=data))
        await s.flush()
    return await shipment_response(order_id)


async def apply_everpro_event(payload: dict, payload_hash: str, *, kind: str) -> dict:
    number = payload.get("client_order_no")
    if not isinstance(number, str) or not 1 <= len(number) <= 64:
        raise HTTPException(422, "Referensi pengiriman tidak valid")
    if payload.get("order_reference_id") and payload["order_reference_id"] != number:
        raise HTTPException(409, "Referensi pengiriman tidak cocok")
    if kind == "tracking" and not isinstance(payload.get("tracking_code"), str):
        raise HTTPException(422, "Status pengiriman wajib diisi")
    if kind == "awb" and not payload.get("awb_number"):
        raise HTTPException(422, "Nomor resi wajib diisi")
    async with read_session() as s:
        order = await s.scalar(select(m.Order).where(m.Order.order_number == number))
        if order is None:
            raise HTTPException(404, "Order tidak ditemukan")
        order_id, owner = order.id, order.user_id
    event_key = kind + ":" + payload_hash
    async with session_scope() as s:
        await lock_user(s, owner, active=False)
        order, shipment = await _shipment_context(s, order_id, lock=True)
        existing = await s.scalar(select(m.IntegrationWebhookEvent.id).where(
            m.IntegrationWebhookEvent.provider == "everpro", m.IntegrationWebhookEvent.event_key == event_key))
        if existing:
            return {"ok": True, "duplicate": True}
        _tracking_update(s, order, shipment, payload)
        s.add(m.IntegrationWebhookEvent(id=gen_id("evt"), provider="everpro", event_key=event_key,
            payload_hash=payload_hash, order_id=order_id, event_type=kind, signature_verified=True,
            payload=payload, status="processed", attempts=1, processed_at=utcnow()))
        s.add(m.ShipmentLog(id=gen_id("slg"), order_id=order_id, shipment_id=shipment.id, provider="everpro",
                           action="callback_" + kind, response=payload))
        await s.flush()
    return {"ok": True}


async def stored_tracking(s, order_id: str) -> list[dict] | None:
    last = await s.scalar(select(m.ShipmentLog).where(m.ShipmentLog.order_id == order_id,
        m.ShipmentLog.provider == "everpro", m.ShipmentLog.action == "tracking_poll")
        .order_by(m.ShipmentLog.created_at.desc(), m.ShipmentLog.id).limit(1))
    if not last:
        return None
    events = (last.response or {}).get("tracking_history") or []
    return [{"date": event.get("date"), "status": event.get("status"), "description": event.get("description")}
            for event in events if isinstance(event, dict)]


def integration_status(*, admin: bool = False) -> dict:
    data = {}
    for key, selector, Settings, required in (
        ("payment", payment_provider, DokuSettings, ("DOKU_CLIENT_ID", "DOKU_SECRET_KEY", "PUBLIC_FRONTEND_URL")),
        ("shipping", shipping_provider, EverproSettings, ("EVERPRO_CLIENT_KEY", "EVERPRO_CLIENT_SECRET", "EVERPRO_ORIGIN_POSTAL_CODE",
            "EVERPRO_SHIPPER_NAME", "EVERPRO_SHIPPER_PHONE", "EVERPRO_SHIPPER_ADDRESS")),
    ):
        try:
            provider = selector()
            if provider == "mock":
                item = {"provider": "doku-mock" if key == "payment" else "everpro-mock", "ready": True, "mock": True}
            elif provider == "disabled":
                item = {"provider": "disabled", "ready": False, "mock": False}
            else:
                settings = Settings.from_env()
                item = {"provider": provider, "ready": True, "mock": False}
                if admin:
                    item["environment"] = settings.environment
                    if key == 'payment':
                        item['notification_override_ready'] = bool(settings.notification_override_url)
                        if settings.public_api_url and not settings.notification_override_url:
                            item['configuration_notes'] = ['PUBLIC_API_URL memakai alamat lokal sehingga tidak dikirim sebagai override notifikasi DOKU. Gunakan URL HTTPS publik atau konfigurasi notifikasi pada dashboard DOKU; saat uji lokal, status dapat diperiksa lewat tombol Periksa Status.']
                    if key == "shipping":
                        item["shipment_type"] = settings.shipment_type
                        item["webhook_ready"] = bool(settings.webhook_key)
        except HTTPException as error:
            item = {"provider": "doku" if key == "payment" else "everpro", "ready": False, "mock": False}
            if admin:
                item['configuration_error'] = str(error.detail)
        if admin:
            item["missing"] = [name for name in required if not os.environ.get(name)] if not item["mock"] and not item["ready"] else []
        data[key] = item
    if admin:
        data["webhooks"] = {"doku": os.environ.get("DOKU_NOTIFICATION_PATH", "/api/webhooks/doku"),
                            "everpro_tracking": "/api/webhooks/everpro/tracking", "everpro_awb": "/api/webhooks/everpro/awb"}
    return data
