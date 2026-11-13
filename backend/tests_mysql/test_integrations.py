"""Provider protocol and SQL orchestration, with zero outbound network access.

SQLite exercises state transitions, not MySQL row-lock semantics. Provider
HTTP contracts use httpx.MockTransport; merchant sandbox approval is separate.
"""
from __future__ import annotations

import asyncio
import base64
from datetime import timedelta, timezone
from decimal import Decimal
import hashlib
import hmac
import json
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
import httpx
import pytest
from sqlalchemy import func, select, update

from auth import current_user
from database import read_session, session_scope
from integrations.common import ProviderError, json_bytes
from integrations.config import DokuSettings, EverproSettings, payment_provider, shipping_provider
from integrations.doku import DokuClient, signature, verify_notification, safe_checkout_url
from integrations.everpro import EverproClient
from mysql import models as m
from mysql.base import utcnow
from mysql.commerce import create_checkout, expire_order, admin_transition_order
from mysql import integration_services as service
from routes_integrations import router
from tests_mysql.commerce_scenarios import seed_commerce_fixture
from tests_mysql.sql_helpers import isolated_database


@pytest.fixture
def env(monkeypatch):
    values = {
        "APP_ENV": "test", "ENABLE_MOCK_PAYMENTS": "0", "PAYMENT_PROVIDER": "doku", "SHIPPING_PROVIDER": "everpro",
        "DOKU_CLIENT_ID": "MCH-FIXTURE", "DOKU_SECRET_KEY": "test-secret-not-a-credential", "DOKU_ENVIRONMENT": "sandbox",
        "PUBLIC_FRONTEND_URL": "https://shop.example.test", "PUBLIC_API_URL": "https://api.example.test",
        "DOKU_NOTIFICATION_PATH": "/api/webhooks/doku", "DOKU_PAYMENT_DUE_MINUTES": "60",
        "EVERPRO_CLIENT_KEY": "fixture-key", "EVERPRO_CLIENT_SECRET": "fixture-secret",
        "EVERPRO_ENVIRONMENT": "sandbox", "EVERPRO_BASE_URL": "https://client-api-sandbox.everpro.id",
        "EVERPRO_ORIGIN_POSTAL_CODE": "40115", "EVERPRO_ORIGIN_SUBDISTRICT": "Citarum",
        "EVERPRO_SHIPPER_NAME": "Fixture Optical", "EVERPRO_SHIPPER_PHONE": "081234567890",
        "EVERPRO_SHIPPER_ADDRESS": "Jl. Fixture 12", "EVERPRO_SHIPMENT_TYPE": "DROP",
        "EVERPRO_WEBHOOK_KEY": "fixture-callback-secret", "EVERPRO_USE_INSURANCE": "0",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return values


class FakeDoku:
    def __init__(self):
        self.settings = DokuSettings.from_env()
        self.calls = []
        self.fail_create = False
        self.status = "PENDING"
        self.last = None
        self.status_calls = []

    async def create_payment(self, request_id, payload):
        self.calls.append((request_id, payload))
        self.last = payload
        if self.fail_create:
            raise ProviderError("doku", "network_error", 503, uncertain=True)
        expiry = (utcnow() + timedelta(minutes=60)).astimezone(ZoneInfo("Asia/Jakarta")).strftime("%Y%m%d%H%M%S")
        return {"response": {"order": payload["order"], "payment": {
            "token_id": "doku-token-" + payload["order"]["invoice_number"],
            "url": "https://sandbox.doku.com/checkout-link-v2/fixture-token", "expired_date": expiry,
        }}}

    async def check_status(self, invoice):
        self.status_calls.append(invoice)
        return {"order": {"invoice_number": invoice, "amount": self.last["order"]["amount"]},
                "transaction": {"status": self.status}}


class FakeEverpro:
    def __init__(self):
        self.settings = EverproSettings.from_env()
        self.rate_requests, self.bookings = [], []
        self.remote = {}
        self.fail_after_booking = False
        self.adjustment = 0
        self.pickup_start = (utcnow() + timedelta(hours=3)).replace(microsecond=0)

    async def rates(self, payload):
        self.rate_requests.append(payload)
        return {"status": "success", "data": {"regular": [{
            "logistic_code": "JNE", "logistic_name": "JNE", "rate_code": "REG23", "rate_name": "Reguler",
            "price": 12000, "insurance_price": 0, "min_duration": 1, "max_duration": 3,
            "duration_type": "day", "is_flat_rate": False, "is_use_wood_packing": False,
        }]}}

    async def locations(self, postal_code):
        return {'data': [{'postal_code': postal_code, 'province_name': 'DKI Jakarta', 'city_name': 'Jakarta',
                          'district_name': 'Gambir', 'sub_district_name': 'Cideng', 'sub_district_id': 8839}]}

    async def create_shipment(self, payload):
        self.bookings.append(payload)
        self.remote[payload["client_order_no"]] = dict(payload)
        if self.fail_after_booking:
            raise ProviderError("everpro", "network_error", 503, uncertain=True)
        return {"client_order_no": payload["client_order_no"], "actual_price": payload["shipment_price"] + self.adjustment}

    async def order_detail(self, number):
        if number not in self.remote:
            raise ProviderError("everpro", "not_found", 404)
        value = self.remote[number]
        return {"data": {"client_order_no": number, "shipment_order_no": "EPR-" + number,
                         "awb_number": "AWB-" + number, "shipment_price": value["shipment_price"] + self.adjustment,
                         "insurance_price": 0, "tracking_code": "CREATED", "tracking_history": []}}

    async def tracking(self, awb):
        return {"data": {"awb_number": awb, "tracking_code": "PICKEDUP", "tracking_history": [
            {"date": utcnow().isoformat(), "status": "PICKEDUP", "description": "Picked up"}
        ]}}

    async def label(self, awb):
        return {"data": {"url_label_pdf": "https://example.everpro.id/label/fixture.pdf"}}

    async def pickup_times(self, rate_code):
        return {"data": {"available_pickup_time": [{"rate_code": rate_code, "pickup_time_list": [{"pickup_times": [
            {"condition": True, "cut_off": False, "start_at": self.pickup_start.isoformat(), "time_range": "09.00 - 12.00"}
        ]}]}]}}


@pytest.fixture
def adapters(env, monkeypatch):
    doku, everpro = FakeDoku(), FakeEverpro()
    monkeypatch.setattr(service, "get_doku_client", lambda: doku)
    monkeypatch.setattr(service, "get_everpro_client", lambda: everpro)
    return doku, everpro


async def prepared(adapters, *, points=0):
    fixture = await seed_commerce_fixture(bundle=False, quantity=1)
    async with session_scope() as s:
        address = await s.get(m.Address, fixture['address'])
        address.district, address.subdistrict = 'Gambir', 'Cideng'
    options = await service.shipping_options(fixture["alice"], fixture["address"], [fixture["cart"]])
    option = options["options"][0]
    fixture["req"] = fixture["req"].model_copy(update={"courier_code": option["courier_code"],
        "service_code": option["service_code"], "shipping_quote_id": option["quote_id"], "use_points": points})
    return fixture


def payment_event(order, *, status="SUCCESS", amount=None, **transaction):
    return {"order": {"invoice_number": order["order_number"], "amount": order["total"] if amount is None else amount},
            "transaction": {"status": status, **transaction}, "channel": {"id": "VIRTUAL_ACCOUNT_BCA"}}


async def paid_order(adapters):
    fixture = await prepared(adapters)
    result = await create_checkout(fixture["alice"], fixture["req"])
    payload = payment_event(result["order"])
    await service.apply_doku_event(payload, "fixture-paid", hashlib.sha256(json_bytes(payload)).hexdigest())
    return fixture, result["order"]


def test_doku_hmac_uses_exact_bytes_target_and_get_omits_digest(env):
    settings = DokuSettings.from_env()
    raw = b'{"order":{"amount":1000,"invoice_number":"TEST"}}'
    stamp = utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    components = "\n".join(["Client-Id:MCH-FIXTURE", "Request-Id:event-1", "Request-Timestamp:" + stamp,
                            "Request-Target:/api/webhooks/doku", "Digest:" + base64.b64encode(hashlib.sha256(raw).digest()).decode()])
    expected = "HMACSHA256=" + base64.b64encode(hmac.new(settings.secret_key.encode(), components.encode(), hashlib.sha256).digest()).decode()
    assert signature(settings.secret_key, settings.client_id, "event-1", stamp, settings.notification_path, raw) == expected
    headers = {"Client-Id": settings.client_id, "Request-Id": "event-1", "Request-Timestamp": stamp, "Signature": expected}
    assert verify_notification(settings, headers, raw) == "event-1"
    for changed in (raw + b" ", raw.replace(b"1000", b"1001")):
        with pytest.raises(ProviderError):
            verify_notification(settings, headers, changed)
    for header, value in [("Client-Id", "é"), ("Signature", "é"), ("Request-Timestamp", "invalid")]:
        with pytest.raises(ProviderError):
            verify_notification(settings, {**headers, header: value}, raw)
    get_components = "\n".join(components.split("\n")[:4])
    get_expected = "HMACSHA256=" + base64.b64encode(hmac.new(settings.secret_key.encode(), get_components.encode(), hashlib.sha256).digest()).decode()
    assert signature(settings.secret_key, settings.client_id, "event-1", stamp, settings.notification_path, None) == get_expected


def test_doku_http_contract_and_signed_response(env):
    settings = DokuSettings.from_env()
    seen = []
    def handler(request):
        assert request.url.host == "api-sandbox.doku.com"
        seen.append((request.method, request.url.path))
        expected = signature(settings.secret_key, settings.client_id, request.headers["Request-Id"],
            request.headers["Request-Timestamp"], request.url.path, request.content if request.method == "POST" else None)
        assert request.headers["Signature"] == expected
        raw = json_bytes({"ok": True})
        stamp = utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        response_sig = signature(settings.secret_key, settings.client_id, request.headers["Request-Id"], stamp,
                                 request.url.path, raw if request.method == "POST" else None, response=True)
        return httpx.Response(200, content=raw, headers={"Response-Timestamp": stamp, "Signature": response_sig})
    async def run():
        client = DokuClient(settings, transport=httpx.MockTransport(handler))
        assert await client.create_payment("request-1", {"order": {"amount": 1000}}) == {"ok": True}
        assert await client.check_status("INV-1") == {"ok": True}
    asyncio.run(run())
    assert seen == [("POST", "/checkout/v1/payment"), ("GET", "/orders/v1/status/INV-1")]


def test_everpro_auth_and_verified_endpoint_contract(env):
    calls = []
    def handler(request):
        calls.append((request.method, request.url.path))
        if request.url.path == "/auth/v1/token":
            assert json.loads(request.content) == {"client_key": "fixture-key", "client_secret": "fixture-secret"}
            return httpx.Response(200, json={"data": {"token": "token-fixture", "token_type": "Bearer", "expires": 86400}})
        assert request.headers["Authorization"] == "Bearer token-fixture"
        if request.url.path == "/shipment/v1/orders":
            assert json.loads(request.content)["client_order_no"] == "INV-1"
            return httpx.Response(200, json={"client_order_no": "INV-1"})
        return httpx.Response(200, json={"status": "success", "data": {}})
    async def run():
        client = EverproClient(EverproSettings.from_env(), transport=httpx.MockTransport(handler))
        await client.rates({"weight": 0.5, "shipment_type": "DROP"})
        await client.create_shipment({"client_order_no": "INV-1"})
        await client.order_detail("INV-1")
        await client.tracking("AWB-1")
    asyncio.run(run())
    assert calls == [("POST", "/auth/v1/token"), ("POST", "/shipment/v2/rates"),
                     ("POST", "/shipment/v1/orders"), ("GET", "/shipment/v1/orders/INV-1"),
                     ("GET", "/shipment/v1/orders/AWB-1/track")]


def test_production_mock_gate_urls_and_public_diagnostics(env, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENABLE_MOCK_PAYMENTS", "1")
    monkeypatch.setenv("PAYMENT_PROVIDER", "mock")
    monkeypatch.setenv("SHIPPING_PROVIDER", "mock")
    for selector in (payment_provider, shipping_provider):
        with pytest.raises(HTTPException):
            selector()
    for value in ("https://evil.test/pay", "javascript:alert(1)", "https://[invalid"):
        with pytest.raises(ProviderError):
            safe_checkout_url(value)
    status = service.integration_status()
    assert "missing" not in str(status) and "fixture-secret" not in str(status)
    monkeypatch.setenv("PUBLIC_FRONTEND_URL", "https://[invalid")
    with pytest.raises(HTTPException) as caught:
        DokuSettings.from_env()
    assert caught.value.status_code == 503


def test_persisted_quotes_checkout_rounding_and_retry_identity(adapters):
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            assert adapters[1].rate_requests[0]["weight"] == 0.1
            first = await create_checkout(d["alice"], d["req"], "checkout-once")
            second = await create_checkout(d["alice"], d["req"], "checkout-once")
            assert first["order"]["id"] == second["order"]["id"]
            assert first["order"]["total"] == 13000
            assert first["payment"]["provider"] == "doku" and not first["payment"]["mock"]
            assert len(adapters[0].calls) == 1
            request = adapters[0].calls[0][1]
            assert request["order"]["amount"] == 13000
            assert request["order"]["callback_url"].endswith("/payment/" + first["order"]["order_number"])
            assert request["additional_info"]["override_notification_url"] == "https://api.example.test/api/webhooks/doku"
            async with read_session() as s:
                assert (await s.get(m.ProductVariant, d["vf"])).reserved == 1
                assert await s.scalar(select(func.count()).select_from(m.Payment)) == 1
                assert (await s.get(m.Order, first["order"]["id"])).shipping_quote_id == d["req"].shipping_quote_id
    asyncio.run(run())


@pytest.mark.parametrize("change", ["address", "quantity", "price", "expiry", "owner", "service"])
def test_shipping_quotes_reject_changed_checkout_snapshot(adapters, change):
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            async with session_scope() as s:
                if change == "address":
                    (await s.get(m.Address, d["address"])).street = "Changed street"
                elif change == "quantity":
                    (await s.get(m.CartItem, d["cart"])).quantity = 2
                elif change == "price":
                    (await s.get(m.Product, d["frame"])).price += 100
                elif change == "expiry":
                    (await s.get(m.ShippingQuote, d["req"].shipping_quote_id)).expires_at = utcnow() - timedelta(seconds=1)
                elif change == "owner":
                    (await s.get(m.ShippingQuote, d["req"].shipping_quote_id)).user_id = d["bob"]
                elif change == "service":
                    d["req"] = d["req"].model_copy(update={"service_code": "FAKE-CHEAP"})
            with pytest.raises(HTTPException) as caught:
                await create_checkout(d["alice"], d["req"])
            assert caught.value.status_code in {409, 422}
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.Order)) == 0
    asyncio.run(run())


def test_payment_timeout_returns_committed_order_and_same_request_on_retry(adapters):
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            adapters[0].fail_create = True
            first = await create_checkout(d["alice"], d["req"])
            assert first["requires_retry"] and first["payment"]["payment_url"] is None
            assert first["order"]["status"] == "pending_payment"
            async with session_scope() as s:
                await s.execute(update(m.PaymentLog).where(m.PaymentLog.action == "doku_attempt").values(created_at=utcnow()-timedelta(seconds=40)))
            adapters[0].fail_create = False
            second = await create_checkout(d["alice"], d["req"])
            assert second["order"]["id"] == first["order"]["id"]
            assert second["payment"]["payment_url"]
            assert adapters[0].calls[0] == adapters[0].calls[1]
    asyncio.run(run())


def test_verified_payment_is_atomic_and_duplicate_events_do_not_resell(adapters):
    async def run():
        async with isolated_database():
            d, order = await paid_order(adapters)
            event = payment_event(order)
            digest = hashlib.sha256(json_bytes(event)).hexdigest()
            assert (await service.apply_doku_event(event, "fixture-paid", digest))["duplicate"]
            await service.apply_doku_event(event, "new-delivery-id-same-success", digest)
            async with read_session() as s:
                variant = await s.get(m.ProductVariant, d["vf"])
                assert (variant.stock, variant.reserved) == (4, 0)
                assert (await s.get(m.Order, order["id"])).payment_status == "paid"
                assert await s.scalar(select(func.count()).select_from(m.Shipment)) == 1
                assert await s.scalar(select(func.count()).select_from(m.StockMovement).where(m.StockMovement.type == "sold")) == 1
            changed = payment_event(order, amount=1)
            with pytest.raises(HTTPException) as caught:
                await service.apply_doku_event(changed, "fixture-paid", hashlib.sha256(json_bytes(changed)).hexdigest())
            assert caught.value.status_code == 409
    asyncio.run(run())


@pytest.mark.parametrize("kind", ["amount", "currency", "FAILED", "PENDING", "UNKNOWN", "AUTHORIZE", "unknown_type"])
def test_nonsettled_or_mismatched_events_cannot_mark_paid(adapters, kind):
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            payload = payment_event(order)
            if kind == "amount": payload["order"]["amount"] = 1
            elif kind == "currency": payload["order"]["currency"] = "USD"
            elif kind == "AUTHORIZE": payload["transaction"]["type"] = "AUTHORIZE"
            elif kind == "unknown_type": payload["transaction"]["type"] = {"unexpected": True}
            else: payload["transaction"]["status"] = kind
            result = await service.apply_doku_event(payload, "event-" + kind, hashlib.sha256(json_bytes(payload)).hexdigest())
            assert result["reconciliation_required"] == (kind in {"amount", "currency"})
            async with read_session() as s:
                assert (await s.get(m.Order, order["id"])).payment_status == "pending"
                assert (await s.get(m.ProductVariant, d["vf"])).reserved == 1
                assert await s.scalar(select(func.count()).select_from(m.Shipment)) == 0
    asyncio.run(run())


def test_real_payment_cannot_be_cancelled_or_expired_without_provider_finality(adapters):
    async def run():
        async with isolated_database():
            d = await prepared(adapters, points=2)
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            async with session_scope() as s:
                (await s.get(m.Order, order["id"])).reservation_expires_at = utcnow() - timedelta(minutes=2)
                payment = await s.scalar(select(m.Payment))
                payment.expires_at = utcnow() - timedelta(minutes=2)
                await s.execute(update(m.PaymentLog).values(created_at=utcnow()-timedelta(minutes=3)))
            with pytest.raises(HTTPException):
                await admin_transition_order(order["id"], "cancelled", None, d["admin"])
            assert not await expire_order(order["id"], due_only=True)
            async with read_session() as s:
                assert (await s.get(m.ProductVariant, d["vf"])).reserved == 1
            async with session_scope() as s:
                await s.execute(update(m.PaymentLog).values(created_at=utcnow()-timedelta(minutes=3)))
            adapters[0].status = "EXPIRED"
            assert await expire_order(order["id"], due_only=True)
            assert not await expire_order(order["id"], due_only=True)
            async with read_session() as s:
                assert (await s.get(m.ProductVariant, d["vf"])).reserved == 0
                assert (await s.get(m.User, d["alice"])).points_balance == 100
            late = payment_event(order)
            result = await service.apply_doku_event(late, "late-paid", hashlib.sha256(json_bytes(late)).hexdigest())
            assert result["reconciliation_required"]
            async with read_session() as s:
                current = await s.get(m.Order, order["id"])
                assert (current.status, current.payment_status) == ("expired", "paid")
                assert (await s.get(m.ProductVariant, d["vf"])).stock == 5
                assert await s.scalar(select(func.count()).select_from(m.Shipment)) == 0
    asyncio.run(run())


def test_payment_receipt_survives_inconsistent_stock_with_reconciliation_flag(adapters):
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            async with session_scope() as s:
                (await s.get(m.ProductVariant, d["vf"])).reserved = 0
            payload = payment_event(order)
            result = await service.apply_doku_event(payload, "needs-reconciliation", hashlib.sha256(json_bytes(payload)).hexdigest())
            assert result["reconciliation_required"]
            response = await service.payment_response(order["id"])
            assert response["order"]["payment_reconciliation_required"]
            assert response["order"]["payment_status"] == "paid" and response["order"]["status"] == "pending_payment"
            async with read_session() as s:
                assert (await s.get(m.ProductVariant, d["vf"])).stock == 5
                assert await s.scalar(select(func.count()).select_from(m.Shipment)) == 0
    asyncio.run(run())


def test_everpro_booking_is_paid_only_and_retry_recovers_uncertain_post(adapters):
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            with pytest.raises(HTTPException):
                await service.book_shipment(order["id"])
            payload = payment_event(order)
            await service.apply_doku_event(payload, "paid", hashlib.sha256(json_bytes(payload)).hexdigest())
            adapters[1].fail_after_booking = True
            with pytest.raises(HTTPException):
                await service.book_shipment(order["id"])
            async with session_scope() as s:
                await s.execute(update(m.ShipmentLog).values(created_at=utcnow()-timedelta(seconds=40)))
            recovered = await service.book_shipment(order["id"])
            assert recovered["shipment"]["tracking_number"]
            assert recovered["shipment"]["label_url"].endswith(".pdf")
            assert len(adapters[1].bookings) == 1
            await service.book_shipment(order["id"])
            assert len(adapters[1].bookings) == 1
            booking = adapters[1].bookings[0]
            assert booking["client_order_no"] == order["order_number"]
            assert booking["shipment_type"] == "DROP" and booking["is_cod"] is False
    asyncio.run(run())


def test_everpro_repricing_does_not_change_customer_paid_amount(adapters):
    async def run():
        async with isolated_database():
            d, order = await paid_order(adapters)
            adapters[1].adjustment = 500
            result = await service.book_shipment(order["id"])
            assert result["price_adjusted"]
            assert result["shipment"]["cost"] == 12500
            assert result["order"]["total"] == order["total"]
    asyncio.run(run())


def test_pickup_uses_provider_slot_and_keeps_booking_payload_immutable(adapters, monkeypatch):
    monkeypatch.setenv("EVERPRO_SHIPMENT_TYPE", "PICKUP")
    adapters[1].settings = EverproSettings.from_env()
    async def run():
        async with isolated_database():
            _, order = await paid_order(adapters)
            with pytest.raises(HTTPException) as missing:
                await service.book_shipment(order["id"])
            assert missing.value.status_code == 422
            slots = await service.shipment_pickup_times(order["id"])
            value = slots["times"][0]["value"]
            with pytest.raises(HTTPException):
                await service.book_shipment(order["id"], value + 100)
            await service.book_shipment(order["id"], value)
            assert adapters[1].bookings[0]["pickup_time"] == value
            assert adapters[1].bookings[0]["shipment_type"] == "PICKUP"
            with pytest.raises(HTTPException):
                await service.book_shipment(order["id"], value + 100)
    asyncio.run(run())


def test_real_shipment_auto_completion_waits_for_delivered_date(adapters):
    from scheduler import job_auto_complete_orders
    async def run():
        async with isolated_database():
            _, order = await paid_order(adapters)
            await service.book_shipment(order["id"])
            await service.refresh_shipment(order["id"])
            async with session_scope() as s:
                shipment = await s.scalar(select(m.Shipment))
                shipment.shipped_at = utcnow() - timedelta(days=10)
            await job_auto_complete_orders()
            async with read_session() as s:
                assert (await s.get(m.Order, order["id"])).status == "shipped"
            async with session_scope() as s:
                shipment = await s.scalar(select(m.Shipment))
                shipment.status = "delivered"
                shipment.delivered_at = utcnow() - timedelta(days=8)
                (await s.get(m.Order, order["id"])).shipment_status = "delivered"
            await job_auto_complete_orders()
            async with read_session() as s:
                assert (await s.get(m.Order, order["id"])).status == "completed"
    asyncio.run(run())


def test_doku_retry_does_not_cross_merchant_account(adapters, monkeypatch):
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            adapters[0].fail_create = True
            result = await create_checkout(d["alice"], d["req"])
            monkeypatch.setenv("DOKU_CLIENT_ID", "MCH-OTHER")
            adapters[0].settings = DokuSettings.from_env()
            with pytest.raises(HTTPException) as caught:
                await service.ensure_doku_payment(result["order"]["id"])
            assert caught.value.status_code == 409
            assert len(adapters[0].calls) == 1
    asyncio.run(run())


@pytest.mark.parametrize("change", ["account", "environment", "missing_context"])
def test_doku_callbacks_and_polling_bind_original_account_context(adapters, monkeypatch, change):
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            if change == "account":
                monkeypatch.setenv("DOKU_CLIENT_ID", "MCH-DIFFERENT")
            elif change == "environment":
                monkeypatch.setenv("DOKU_ENVIRONMENT", "production")
            else:
                async with session_scope() as s:
                    row = await s.scalar(select(m.PaymentLog).where(m.PaymentLog.action == "doku_configuration"))
                    row.action = "legacy_missing_configuration"
            adapters[0].settings = DokuSettings.from_env()
            payload = payment_event(order)
            result = await service.apply_doku_event(payload, "context-changed", hashlib.sha256(json_bytes(payload)).hexdigest(),
                                                    authenticated_context=service.doku_context(adapters[0].settings))
            assert result["reconciliation_required"]
            with pytest.raises(HTTPException) as caught:
                await service.refresh_doku_payment(order["id"])
            assert caught.value.status_code == 409
            assert adapters[0].status_calls == []
            async with read_session() as s:
                assert (await s.get(m.Order, order["id"])).payment_status == "pending"
                assert (await s.get(m.ProductVariant, d["vf"])).reserved == 1
                event = await s.scalar(select(m.IntegrationWebhookEvent))
                assert event.error_code == "payment_account_or_environment_mismatch"
                assert await s.scalar(select(func.count()).select_from(m.Shipment)) == 0
    asyncio.run(run())


def test_repaired_ledger_reconciles_paid_order_once_and_keeps_audit_history(adapters):
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            async with session_scope() as s:
                (await s.get(m.ProductVariant, d["vf"])).reserved = 0
            payload = payment_event(order)
            await service.apply_doku_event(payload, "needs-repair", hashlib.sha256(json_bytes(payload)).hexdigest())
            async with session_scope() as s:
                assert (await s.get(m.Order, order["id"])).status == "pending_payment"
                intent = await s.scalar(select(m.Payment))
                original_paid_at = intent.paid_at
                (await s.get(m.ProductVariant, d["vf"])).reserved = 1
                await s.execute(update(m.PaymentLog).values(created_at=utcnow()-timedelta(minutes=2)))
            adapters[0].status = "SUCCESS"
            result = await service.refresh_doku_payment(order["id"])
            assert result["order"]["status"] == "paid"
            assert not result["order"]["payment_reconciliation_required"]
            async with session_scope() as s:
                await s.execute(update(m.PaymentLog).values(created_at=utcnow()-timedelta(minutes=2)))
            await service.refresh_doku_payment(order["id"])
            async with read_session() as s:
                variant = await s.get(m.ProductVariant, d["vf"])
                assert (variant.stock, variant.reserved) == (4, 0)
                assert (await s.scalar(select(m.Payment))).paid_at == original_paid_at
                assert await s.scalar(select(func.count()).select_from(m.Shipment)) == 1
                assert await s.scalar(select(func.count()).select_from(m.StockMovement).where(m.StockMovement.type == "sold")) == 1
                prior = await s.scalar(select(m.IntegrationWebhookEvent).where(m.IntegrationWebhookEvent.event_key == "needs-repair"))
                assert prior.status == "processed" and prior.error_code == "stock_or_promotion_reconciliation"
                audit = await s.scalar(select(m.PaymentLog).where(m.PaymentLog.action == "doku_reconciliation_resolved"))
                assert prior.id in audit.payload["event_ids"]
    asyncio.run(run())


def test_everpro_delivered_state_cannot_regress_on_callback_retry(adapters):
    async def run():
        async with isolated_database():
            _, order = await paid_order(adapters)
            await service.book_shipment(order["id"])
            body = {"client_order_no": order["order_number"], "awb_number": "AWB-" + order["order_number"], "tracking_code": "DELIVERED"}
            digest = hashlib.sha256(json_bytes(body)).hexdigest()
            await service.apply_everpro_event(body, digest, kind="tracking")
            assert (await service.apply_everpro_event(body, digest, kind="tracking"))["duplicate"]
            earlier = {**body, "tracking_code": "PICKEDUP"}
            await service.apply_everpro_event(earlier, hashlib.sha256(json_bytes(earlier)).hexdigest(), kind="tracking")
            result = await service.shipment_response(order["id"])
            assert result["shipment"]["status"] == "delivered" and result["order"]["shipment_status"] == "delivered"
            wrong_awb = {**body, "awb_number": "OTHER-ORDER"}
            with pytest.raises(HTTPException):
                await service.apply_everpro_event(wrong_awb, hashlib.sha256(json_bytes(wrong_awb)).hexdigest(), kind="tracking")
    asyncio.run(run())


def test_http_webhook_authentication_and_owned_payment_reads(adapters):
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            app = FastAPI()
            app.include_router(router, prefix="/api")
            app.dependency_overrides[current_user] = lambda: d["user"]
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://fixture") as client:
                good = await client.get("/api/payments/" + order["order_number"])
                assert good.status_code == 200 and good.json()["payment"]["provider"] == "doku"
                missing = await client.get("/api/payments/OTHER-CUSTOMER")
                assert missing.status_code == 404
                raw = json_bytes(payment_event(order))
                denied = await client.post("/api/webhooks/doku", content=raw, headers={"Content-Type": "application/json"})
                assert denied.status_code == 401
                settings = DokuSettings.from_env()
                stamp = utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                headers = {"Content-Type": "application/json", "Client-Id": settings.client_id,
                           "Request-Id": "http-event", "Request-Timestamp": stamp,
                           "Signature": signature(settings.secret_key, settings.client_id, "http-event", stamp, settings.notification_path, raw)}
                paid = await client.post("/api/webhooks/doku", content=raw, headers=headers)
                assert paid.status_code == 200
                assert (await client.get("/api/payments/" + order["order_number"])).json()["order"]["payment_status"] == "paid"
                event = {"client_order_no": order["order_number"], "tracking_code": "DELIVERED", "awb_number": "CALLBACK-AWB"}
                assert (await client.post("/api/webhooks/everpro/tracking", json=event)).status_code == 401
                response = await client.post("/api/webhooks/everpro/tracking", json=event, headers={"x-everpro-key": "fixture-callback-secret"})
                assert response.status_code == 200
    asyncio.run(run())
