"""Reusable SQL commerce fixtures and opt-in real-MySQL concurrency scenario.

The scenario never resets a schema or deletes existing records. It creates
uniquely named fixture rows in the caller's explicitly disposable test database.
SQLite tests exercise sequential invariants, not MySQL row-lock semantics.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta
from decimal import Decimal
import secrets

from fastapi import HTTPException
from sqlalchemy import func, select

from database import read_session, session_scope
from models import CheckoutConfirm, User
from mysql import models as m
from mysql.base import utcnow
from mysql.commerce import confirm_mock_payment, create_checkout, expire_order, save_prescription


async def seed_commerce_fixture(*, stock: int = 5, bundle: bool = True,
                                quantity: int = 2, prefix: str | None = None) -> dict:
    prefix = prefix or "ct_" + secrets.token_hex(6)
    ids = {key: prefix + "_" + key for key in (
        "alice", "bob", "admin", "frame", "lens", "vf", "vl", "index", "address",
        "address_bob", "cart", "voucher", "reward", "spin",
    )}
    now = utcnow()
    async with session_scope() as s:
        for key in ("alice", "bob", "admin"):
            s.add(m.User(user_id=ids[key], email=ids[key] + "@example.com", name=key,
                         points_balance=100, is_active=True, role="admin" if key == "admin" else "customer"))
        await s.flush()
        for key, price, kind, weight in (("frame", "1000.10", "frame", 100), ("lens", "200.20", "lens", 50)):
            s.add(m.Product(id=ids[key], name=key, slug=ids[key], sku=ids[key].upper(),
                            price=Decimal(price), product_type=kind, description="SQL fixture",
                            main_image="/fixture.png", weight_gram=weight, is_active=True))
        await s.flush()
        for key, product in (("vf", "frame"), ("vl", "lens")):
            s.add(m.ProductVariant(id=ids[key], product_id=ids[product], sku=ids[key].upper(),
                                   stock=stock, reserved=0, is_active=True, color="Black", sort_order=0))
        s.add(m.LensIndex(id=ids["index"], name="Thin", index_value="1.60",
                          additional_price=Decimal("50.05"), is_active=True))
        for key, user in (("address", "alice"), ("address_bob", "bob")):
            s.add(m.Address(id=ids[key], user_id=ids[user], label="Rumah", recipient=user,
                            phone="081234567890", street="Fixture address", city="Jakarta",
                            province="DKI Jakarta", postal_code="12345", is_default=True))
        s.add(m.Voucher(id=ids["voucher"], code=ids["voucher"].upper(), name="Ten percent",
                        discount_type="percent", discount_value=Decimal("10"), min_purchase=0,
                        quota=100, used_count=0, quota_per_user=1,
                        start_at=now - timedelta(days=1), end_at=now + timedelta(days=1), is_active=True))
        s.add(m.RouletteReward(id=ids["reward"], label="Discount", type="discount", value=50,
                               probability=1, is_active=True))
        await s.flush()
        s.add(m.RouletteSpin(id=ids["spin"], user_id=ids["alice"], reward_id=ids["reward"],
                             reward_label="Discount", reward_type="discount", reward_value=50,
                             used=False, expires_at=now + timedelta(days=1)))
        rx = await save_prescription(s, ids["alice"], {
            "od_sph": "-1.25", "os_sph": "-1.00", "od_cyl": "", "os_cyl": "-0.50", "pd": "62", "notes": "Fixture"
        }) if bundle else None
        await s.flush()
        s.add(m.CartItem(id=ids["cart"], user_id=ids["alice"], product_id=ids["frame"],
                         variant_id=ids["vf"], quantity=quantity,
                         lens_product_id=ids["lens"] if bundle else None,
                         lens_variant_id=ids["vl"] if bundle else None,
                         lens_index_id=ids["index"] if bundle else None,
                         prescription_id=rx.id if rx else None))
        await s.flush()
    ids["prefix"] = prefix
    ids["rx"] = rx.id if rx else None
    ids["user"] = User(user_id=ids["alice"], email=ids["alice"] + "@example.com", name="alice", points_balance=100)
    ids["req"] = CheckoutConfirm(address_id=ids["address"], selected_item_ids=[ids["cart"]],
                                  courier_code="jne", service_code="REG", pin="123456")
    return ids


async def live_commerce_concurrency_scenario() -> None:
    """Assert the final unit cannot be purchased twice, using real MySQL locks.

    Caller configures the async session factory against an explicitly empty
    test_meow_* MySQL 5.7 database and opts into mock payments in APP_ENV=test.
    """
    d = await seed_commerce_fixture(stock=1, bundle=False, quantity=1)
    bob_cart = d["prefix"] + "_cart_bob"
    async with session_scope() as s:
        s.add(m.CartItem(id=bob_cart, user_id=d["bob"], product_id=d["frame"], variant_id=d["vf"], quantity=1))
        await s.flush()
    alice_req = d["req"].model_copy(update={"use_points": 1})
    bob_req = CheckoutConfirm(address_id=d["address_bob"], selected_item_ids=[bob_cart],
                              courier_code="jne", service_code="REG", use_points=1, pin="123456")
    attempts = await asyncio.gather(create_checkout(d["alice"], alice_req),
                                    create_checkout(d["bob"], bob_req), return_exceptions=True)
    winners = [r for r in attempts if isinstance(r, dict)]
    rejected = [r for r in attempts if isinstance(r, HTTPException)]
    assert len(winners) == 1 and len(rejected) == 1, [type(x).__name__ for x in attempts]
    assert rejected[0].status_code == 409
    winner = winners[0]["order"]
    owner = winner["user_id"]
    async with read_session() as s:
        variant = await s.get(m.ProductVariant, d["vf"])
        assert (variant.stock, variant.reserved) == (1, 1)
        assert await s.scalar(select(func.count()).select_from(m.Order).where(m.Order.user_id.in_((d["alice"], d["bob"])))) == 1
    confirmations = await asyncio.gather(
        confirm_mock_payment(winner["order_number"], owner),
        confirm_mock_payment(winner["order_number"], owner),
    )
    assert confirmations[0]["tracking_number"] == confirmations[1]["tracking_number"]
    async with read_session() as s:
        variant = await s.get(m.ProductVariant, d["vf"])
        assert (variant.stock, variant.reserved) == (0, 0)
        assert (await s.get(m.User, owner)).points_balance == 99
        assert await s.scalar(select(func.count()).select_from(m.StockMovement).where(
            m.StockMovement.order_id == winner["id"], m.StockMovement.type == "sold")) == 1
        assert await s.scalar(select(func.count()).select_from(m.PaymentLog).where(
            m.PaymentLog.order_id == winner["id"], m.PaymentLog.action == "webhook_paid")) == 1
        assert await s.scalar(select(func.count()).select_from(m.Shipment).where(m.Shipment.order_id == winner["id"])) == 1
    c = await seed_commerce_fixture(stock=1, bundle=False, quantity=1)
    req = c["req"].model_copy(update={"use_points": 1, "voucher_code": c["voucher"].upper(), "roulette_spin_id": c["spin"]})
    pending = (await create_checkout(c["alice"], req))["order"]
    released = await asyncio.gather(
        expire_order(pending["id"], "cancelled", owner_id=c["alice"]),
        expire_order(pending["id"], "cancelled", owner_id=c["alice"]),
    )
    assert sorted(released) == [False, True]
    async with read_session() as s:
        variant = await s.get(m.ProductVariant, c["vf"])
        assert (variant.stock, variant.reserved) == (1, 0)
        assert (await s.get(m.User, c["alice"])).points_balance == 100
        assert (await s.get(m.Voucher, c["voucher"])).used_count == 0
        assert not (await s.get(m.RouletteSpin, c["spin"])).used
        assert await s.scalar(select(func.count()).select_from(m.PointLog).where(
            m.PointLog.order_id == pending["id"], m.PointLog.type == "refund_point")) == 1
