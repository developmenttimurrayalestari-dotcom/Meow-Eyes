"""Transaction/contract regressions on isolated relational tables.

These run on SQLite with foreign keys and row predicates enabled. Real MySQL
row-lock behavior is covered only by the separate opt-in integration scenario.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta
from decimal import Decimal

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from sqlalchemy import func, select, update

from auth import current_user
from database import read_session, session_scope
from models import AddressCreate, CartItemCreate, CartUpdate
from mysql import models as m
from mysql.api import row_dict
from mysql.base import utcnow
from mysql.commerce import (
    admin_transition_order, checkout_quote, confirm_mock_payment, create_checkout,
    expire_order, save_prescription,
)
from routes_shopping import add_to_cart, create_address, create_review, set_default_address
from tests_mysql.commerce_scenarios import seed_commerce_fixture
from tests_mysql.sql_helpers import isolated_database


@pytest.fixture(autouse=True)
def local_simulators(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_MOCK_PAYMENTS", "1")
    monkeypatch.setenv('PAYMENT_PROVIDER', 'mock')
    monkeypatch.setenv('SHIPPING_PROVIDER', 'mock')


def test_bundle_checkout_snapshots_and_decimal_totals():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            result = await create_checkout(d["alice"], d["req"])
            order = result["order"]
            assert order["subtotal"] == 2500.70 and order["total"] == 16500.70
            assert order["address"]["recipient"] == "alice"
            item = order["items"][0]
            assert item["prescription"]["od_sph"] == -1.25
            assert [c["component_type"] for c in item["components"]] == ["primary", "lens"]
            assert item["components"][1]["unit_price"] == 250.25
            async with read_session() as s:
                assert (await s.get(m.Order, order["id"])).subtotal == Decimal("2500.70")
                assert (await s.get(m.ProductVariant, d["vf"])).reserved == 2
                assert (await s.get(m.ProductVariant, d["vl"])).reserved == 2
                assert await s.scalar(select(func.count()).select_from(m.StockReservation).where(m.StockReservation.order_id == order["id"])) == 2
                snapshot = await s.scalar(select(m.OrderItemPrescription.prescription_id).where(m.OrderItemPrescription.order_id == order["id"]))
                assert snapshot != d["rx"]
                assert (await s.get(m.Prescription, snapshot)).is_order_snapshot
            async with session_scope() as s:
                (await s.get(m.Prescription, d["rx"])).notes = "Edited later"
            async with read_session() as s:
                assert (await s.get(m.Prescription, snapshot)).notes == "Fixture"
    asyncio.run(run())


def test_combined_stock_demand_rolls_back_every_checkout_write():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(stock=3, bundle=False, quantity=2)
            other_id = d["prefix"] + "_second_cart"
            async with session_scope() as s:
                s.add(m.CartItem(id=other_id, user_id=d["alice"], product_id=d["frame"], variant_id=d["vf"], quantity=2))
                await s.flush()
            req = d["req"].model_copy(update={"selected_item_ids": [d["cart"], other_id], "use_points": 5})
            with pytest.raises(HTTPException) as exc:
                await create_checkout(d["alice"], req)
            assert exc.value.status_code == 409
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.Order)) == 0
                assert await s.scalar(select(func.count()).select_from(m.Payment)) == 0
                assert await s.scalar(select(func.count()).select_from(m.StockReservation)) == 0
                assert (await s.get(m.ProductVariant, d["vf"])).reserved == 0
                assert (await s.get(m.User, d["alice"])).points_balance == 100
                assert await s.scalar(select(func.count()).select_from(m.CartItem)) == 2
    asyncio.run(run())


def test_checkout_retries_do_not_double_charge_points_voucher_or_roulette():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False, quantity=1)
            req = d["req"].model_copy(update={"use_points": 2, "voucher_code": d["voucher"].upper(), "roulette_spin_id": d["spin"]})
            first = await create_checkout(d["alice"], req, "client-order-1")
            second = await create_checkout(d["alice"], req, "client-order-1")
            assert first["order"]["id"] == second["order"]["id"]
            assert first["payment"]["invoice_id"] == second["payment"]["invoice_id"]
            assert first["order"]["total"] == 14650.09
            with pytest.raises(HTTPException) as exc:
                await create_checkout(d["alice"], req.model_copy(update={"use_points": 3}), "client-order-1")
            assert exc.value.status_code == 409
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.Order)) == 1
                assert (await s.get(m.Voucher, d["voucher"])).used_count == 1
                assert (await s.get(m.User, d["alice"])).points_balance == 98
                assert (await s.get(m.RouletteSpin, d["spin"])).used
                assert await s.scalar(select(func.count()).select_from(m.PointLog)) == 1
    asyncio.run(run())


def test_selected_cart_ids_also_make_legacy_client_retry_idempotent():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            first = await create_checkout(d["alice"], d["req"])
            again = await create_checkout(d["alice"], d["req"])
            assert first["order"]["id"] == again["order"]["id"]
            assert first["payment"]["invoice_id"] == again["payment"]["invoice_id"]
    asyncio.run(run())


def test_cancellation_is_one_refund_even_for_disabled_customer():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            req = d["req"].model_copy(update={"use_points": 5, "voucher_code": d["voucher"].upper(), "roulette_spin_id": d["spin"]})
            order = (await create_checkout(d["alice"], req))["order"]
            async with session_scope() as s:
                (await s.get(m.User, d["alice"])).is_active = False
            assert await expire_order(order["id"], "cancelled", owner_id=d["alice"])
            assert not await expire_order(order["id"], "cancelled", owner_id=d["alice"])
            async with read_session() as s:
                for variant_id in (d["vf"], d["vl"]):
                    variant = await s.get(m.ProductVariant, variant_id)
                    assert (variant.stock, variant.reserved) == (5, 0)
                assert (await s.get(m.User, d["alice"])).points_balance == 100
                assert (await s.get(m.Voucher, d["voucher"])).used_count == 0
                assert not (await s.get(m.RouletteSpin, d["spin"])).used
                assert await s.scalar(select(func.count()).select_from(m.PointLog).where(m.PointLog.type == "refund_point")) == 1
                assert set((await s.scalars(select(m.StockReservation.status))).all()) == {"cancelled"}
                assert (await s.scalar(select(m.Payment))).status == "cancelled"
    asyncio.run(run())


def test_expired_payment_commits_release_before_returning_error():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            req = d["req"].model_copy(update={"use_points": 3})
            order = (await create_checkout(d["alice"], req))["order"]
            async with session_scope() as s:
                (await s.get(m.Order, order["id"])).reservation_expires_at = utcnow() - timedelta(seconds=1)
            with pytest.raises(HTTPException) as exc:
                await confirm_mock_payment(order["order_number"], d["alice"])
            assert exc.value.status_code == 409
            async with read_session() as s:
                assert (await s.get(m.Order, order["id"])).status == "expired"
                assert (await s.get(m.ProductVariant, d["vf"])).reserved == 0
                assert (await s.get(m.User, d["alice"])).points_balance == 100
                assert (await s.scalar(select(m.Payment))).status == "expired"
    asyncio.run(run())


def test_payment_confirmation_only_sells_and_ships_once():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            with pytest.raises(HTTPException) as exc:
                await confirm_mock_payment(order["order_number"], d["bob"])
            assert exc.value.status_code == 404
            first = await confirm_mock_payment(order["order_number"], d["alice"])
            second = await confirm_mock_payment(order["order_number"], d["alice"])
            assert first["tracking_number"] == second["tracking_number"]
            async with read_session() as s:
                for variant_id in (d["vf"], d["vl"]):
                    variant = await s.get(m.ProductVariant, variant_id)
                    assert (variant.stock, variant.reserved) == (3, 0)
                assert await s.scalar(select(func.count()).select_from(m.Shipment)) == 1
                assert await s.scalar(select(func.count()).select_from(m.PaymentLog).where(m.PaymentLog.action == "webhook_paid")) == 1
                assert await s.scalar(select(func.count()).select_from(m.StockMovement).where(m.StockMovement.type == "sold")) == 2
            with pytest.raises(HTTPException):
                await expire_order(order["id"], "cancelled", owner_id=d["alice"])
    asyncio.run(run())


@pytest.mark.parametrize("legacy_issue", ["missing_reservation", "untracked_variant"])
def test_payment_refuses_incomplete_legacy_reservation_ledger(legacy_issue):
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False, quantity=1)
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            # No normal route creates these incomplete historical states.
            async with session_scope() as s:
                if legacy_issue == "missing_reservation":
                    s.add(m.OrderItem(id=d["prefix"] + "_unreserved", order_id=order["id"],
                        product_id=d["lens"], variant_id=d["vl"], product_name="Legacy lens",
                        quantity=1, unit_price=200, subtotal=200, sort_order=1))
                else:
                    (await s.scalar(select(m.OrderItem).where(m.OrderItem.order_id == order["id"]))).variant_id = None
                    (await s.scalar(select(m.OrderItemComponent).where(m.OrderItemComponent.order_id == order["id"]))).variant_id = None
                    (await s.scalar(select(m.StockReservation).where(m.StockReservation.order_id == order["id"]))).variant_id = None
                    (await s.get(m.ProductVariant, d["vf"])).reserved = 0
                await s.flush()
            with pytest.raises(HTTPException) as exc:
                await confirm_mock_payment(order["order_number"], d["alice"])
            assert exc.value.status_code == 409
            async with read_session() as s:
                assert (await s.get(m.Order, order["id"])).payment_status == "pending"
                assert (await s.get(m.ProductVariant, d["vf"])).stock == 5
                assert (await s.get(m.ProductVariant, d["vl"])).stock == 5
    asyncio.run(run())


def test_admin_cannot_mark_unpaid_order_paid_or_skip_financial_transition():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            for status in ("paid", "completed", "refunded"):
                with pytest.raises(HTTPException) as exc:
                    await admin_transition_order(order["id"], status, None, d["admin"])
                assert exc.value.status_code == 409
            async with read_session() as s:
                assert (await s.get(m.Order, order["id"])).payment_status == "pending"
                assert (await s.get(m.ProductVariant, d["vf"])).stock == 5
    asyncio.run(run())


def test_review_requires_actual_completed_purchase_and_unique_purchase():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False, quantity=1)
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            await confirm_mock_payment(order["order_number"], d["alice"])
            await admin_transition_order(order["id"], "completed", None, d["admin"])
            with pytest.raises(HTTPException):
                await create_review(d["lens"], {"order_id": order["id"], "body": "Not purchased", "rating": 5}, d["user"])
            review = await create_review(d["frame"], {"order_id": order["id"], "body": "Good", "rating": 4}, d["user"])
            assert review["review"]["verified_purchase"] is True
            assert review["review"]["is_approved"] is True
            with pytest.raises(HTTPException):
                await create_review(d["frame"], {"order_id": order["id"], "body": "Duplicate", "rating": 5}, d["user"])
            async with read_session() as s:
                product = await s.get(m.Product, d["frame"])
                assert product.rating_count == 1 and product.rating_avg == Decimal("4.00")
    asyncio.run(run())


def test_flash_price_precedes_variant_price_and_quota_is_reserved():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            flash_id, item_id = d["prefix"] + "_flash", d["prefix"] + "_flash_item"
            async with session_scope() as s:
                (await s.get(m.ProductVariant, d["vf"])).price_override = Decimal("777.77")
                s.add(m.FlashSale(id=flash_id, name="Fixture", start_at=utcnow() - timedelta(hours=1), end_at=utcnow() + timedelta(hours=1), is_active=True))
                await s.flush()
                s.add(m.FlashSaleItem(id=item_id, flash_sale_id=flash_id, product_id=d["frame"], flash_price=Decimal("500"), quota=2, sold=0, reserved=0, is_active=True))
                await s.flush()
            async with read_session() as s:
                quote = await checkout_quote(s, await s.get(m.User, d["alice"]), d["req"])
                assert quote.subtotal == Decimal("1000.00")
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            async with read_session() as s:
                assert (await s.get(m.FlashSaleItem, item_id)).reserved == 2
            await expire_order(order["id"], "cancelled")
            async with read_session() as s:
                assert (await s.get(m.FlashSaleItem, item_id)).reserved == 0
                assert (await s.get(m.FlashSaleItem, item_id)).sold == 0
    asyncio.run(run())


def test_cart_rejects_foreign_variant_and_keeps_lens_config_separate():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            with pytest.raises(HTTPException):
                await add_to_cart(CartItemCreate(product_id=d["frame"], variant_id=d["vl"]), d["user"])
            request = CartItemCreate(product_id=d["frame"], variant_id=d["vf"], lens_product_id=d["lens"], lens_index_id=d["index"], quantity=1)
            first = await add_to_cart(request, d["user"])
            second = await add_to_cart(request, d["user"])
            assert first["id"] != second["id"]
            async with read_session() as s:
                assert (await s.get(m.CartItem, first["id"])).lens_variant_id == d["vl"]
    asyncio.run(run())


def test_invalid_default_address_does_not_clear_existing_default():
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            with pytest.raises(HTTPException) as exc:
                await set_default_address(d["address_bob"], d["user"])
            assert exc.value.status_code == 404
            async with read_session() as s:
                assert (await s.get(m.Address, d["address"])).is_default
            result = await create_address(AddressCreate(label="Work", recipient="Alice", phone="081234567890", street="Work", city="Jakarta", province="DKI Jakarta", postal_code="12345", is_default=True), d["user"])
            async with read_session() as s:
                assert not (await s.get(m.Address, d["address"])).is_default
                assert (await s.get(m.Address, result["address"]["id"])).is_default
    asyncio.run(run())


def test_async_defaults_are_loaded_without_insert_returning():
    """MySQL 5.7 lacks RETURNING; SQLite's default behavior must not hide IO."""
    async def run():
        async with isolated_database() as factory:
            dialect = factory.kw["bind"].sync_engine.dialect
            dialect.insert_returning = False
            dialect.update_returning = False
            dialect.use_insertmanyvalues = False
            d = await seed_commerce_fixture(bundle=False)
            async with session_scope() as s:
                user = m.User(user_id=d["prefix"] + "_defaults", name="Defaults", email=d["prefix"] + "_defaults@example.com")
                product = m.Product(id=d["prefix"] + "_defaults", name="Defaults", slug=d["prefix"] + "_defaults",
                    sku=d["prefix"] + "_defaults", price=10, description="Fixture", main_image="/fixture.png")
                s.add_all([user, product])
                await s.flush()
                assert row_dict(user)["pin_failed_attempts"] == 0
                assert row_dict(user)["is_active"] is True
                assert row_dict(product)["is_new_arrival"] is False
                assert row_dict(product)["sold_count"] == 0
            address = await create_address(AddressCreate(
                label="No RETURNING", recipient="Alice", phone="081234567890",
                street="Fixture", city="Jakarta", province="DKI Jakarta", postal_code="12345",
            ), d["user"])
            assert address["address"]["country_code"] == "ID"
            result = await create_checkout(d["alice"], d["req"])
            assert result["order"]["currency"] == "IDR"
    asyncio.run(run())


@pytest.mark.parametrize("payload", [
    {"pd": 60, "pd_right": 30, "pd_left": 30}, {"pd_right": 30},
    {"od_axis": 181}, {"od_sph": "NaN"}, {"attachment_upload_id": "foreign-upload"},
])
def test_invalid_prescription_does_not_persist(payload):
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            with pytest.raises(HTTPException):
                async with session_scope() as s:
                    await save_prescription(s, d["alice"], payload)
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.Prescription)) == 0
    asyncio.run(run())


def test_mock_payments_fail_closed_even_if_flag_is_set_in_production(monkeypatch):
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            for environment, flag in (("test", "0"), ("production", "1")):
                monkeypatch.setenv("APP_ENV", environment)
                monkeypatch.setenv("ENABLE_MOCK_PAYMENTS", flag)
                with pytest.raises(HTTPException) as exc:
                    await create_checkout(d["alice"], d["req"])
                assert exc.value.status_code == 503
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.Order)) == 0
                assert (await s.get(m.ProductVariant, d["vf"])).reserved == 0
    asyncio.run(run())


def test_direct_game_score_submission_is_rejected():
    from routes_engagement import submit_game
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            with pytest.raises(HTTPException) as exc:
                await submit_game("matching", {"score": 999999}, d["user"])
            assert exc.value.status_code == 410
            async with read_session() as s:
                assert (await s.get(m.User, d["alice"])).points_balance == 100
    asyncio.run(run())


def test_roulette_points_are_used_with_configured_cooldown_and_expiry():
    from routes_engagement import spin_roulette
    from tests_mysql.test_loyalty_games_returns import game_fixture
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture(bundle=False)
            async with session_scope() as s:
                await game_fixture(s, 'roulette', 'roulette', cooldown=0)
                (await s.get(m.RouletteReward, d["reward"])).is_active = False
                s.add(m.RouletteReward(id=d["prefix"] + "_points", label="Ten points", type="points", value=10, probability=1, is_active=True))
                await s.flush()
            assert (await spin_roulette(d["user"]))["spin"]["used"] is True
            async with session_scope() as s:
                (await s.get(m.GameRule, 'roulette')).cooldown_seconds = 10800
            with pytest.raises(HTTPException) as exc:
                await spin_roulette(d["user"])
            assert exc.value.status_code == 429
            async with read_session() as s:
                assert (await s.get(m.User, d["alice"])).points_balance == 110
                lot = await s.scalar(select(m.PointLot).where(m.PointLot.source == 'earn_roulette'))
                assert lot.rate_snapshot == 100 and lot.expires_at is not None
    asyncio.run(run())


def test_newsletter_subscription_is_idempotent():
    from routes_engagement import subscribe_newsletter, unsubscribe_newsletter
    async def run():
        async with isolated_database():
            await subscribe_newsletter({"email": "MEMBER@example.com"})
            await subscribe_newsletter({"email": "member@example.com"})
            await unsubscribe_newsletter({"email": "member@example.com"})
            await subscribe_newsletter({"email": "member@example.com"})
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.NewsletterSubscriber)) == 1
                assert (await s.scalar(select(m.NewsletterSubscriber))).is_active
    asyncio.run(run())


def test_cart_and_order_http_contract_uses_existing_urls_and_json_numbers():
    from routes_orders import router as orders_router
    from routes_shopping import router as shopping_router
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            app = FastAPI()
            app.include_router(shopping_router, prefix="/api")
            app.include_router(orders_router, prefix="/api")
            app.dependency_overrides[current_user] = lambda: d["user"]
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/cart")
                assert response.status_code == 200
                cart = response.json()
                assert cart["items"][0]["unit_price"] == 1250.35
                assert cart["items"][0]["lens_product"]["id"] == d["lens"]
                preview = await client.post("/api/checkout/preview", json=d["req"].model_dump(exclude={"pin"}))
                assert preview.status_code == 200 and preview.json()["total"] == 16500.70
                order = (await create_checkout(d["alice"], d["req"]))["order"]
                detail = await client.get("/api/orders/" + order["id"])
                assert detail.status_code == 200 and detail.json()["order"]["items"][0]["quantity"] == 2
                other = await client.get("/api/orders/missing")
                assert other.status_code == 404
    asyncio.run(run())


def test_scheduler_respects_disabled_campaign_and_does_not_fake_delivery():
    from scheduler import job_activate_flash_sales, job_auto_complete_orders, job_poll_shipments
    async def run():
        async with isolated_database():
            d = await seed_commerce_fixture()
            disabled_id = d["prefix"] + "_disabled"
            async with session_scope() as s:
                s.add(m.FlashSale(id=disabled_id, name="Disabled", start_at=utcnow() - timedelta(hours=1), end_at=utcnow() + timedelta(hours=1), is_active=False))
                await s.flush()
            await job_activate_flash_sales()
            async with read_session() as s:
                assert not (await s.get(m.FlashSale, disabled_id)).is_active
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            await confirm_mock_payment(order["order_number"], d["alice"])
            await job_poll_shipments()
            async with read_session() as s:
                shipment = await s.scalar(select(m.Shipment))
                assert shipment.last_checked_at is not None
                assert shipment.shipped_at is None
                assert (await s.get(m.Order, order["id"])).status == "processing"
            await admin_transition_order(order["id"], "shipped", None, d["admin"])
            async with session_scope() as s:
                shipment = await s.scalar(select(m.Shipment))
                shipment.shipped_at = utcnow() - timedelta(days=8)
                shipment.last_checked_at = utcnow()
            await job_auto_complete_orders()
            async with read_session() as s:
                assert (await s.get(m.Order, order["id"])).status == "completed"
    asyncio.run(run())
