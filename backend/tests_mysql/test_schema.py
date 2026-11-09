"""Relational integrity tests on SQLite plus MySQL-dialect compilation.

SQLite checks exercise portable FK/CHECK/UNIQUE behavior. They deliberately do
not claim to validate MySQL's server-specific DDL, collation or locking behavior.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import io
from pathlib import Path
import re
import subprocess
import sys
import warnings

import pytest
from sqlalchemy import create_engine, event, select, UniqueConstraint
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import IntegrityError, SAWarning
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy.types import Float

from mysql.base import Base, UTCDateTime
from mysql import models  # noqa: F401

TABLES = Base.metadata.tables
NOW = datetime(2026, 11, 6, 7, tzinfo=timezone.utc)
BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture
def connection():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        add(conn, "users", user_id="usr_a", email="a@example.invalid", name="A")
        add(conn, "users", user_id="usr_b", email="b@example.invalid", name="B")
        for suffix in ("a", "b"):
            add(conn, "products", id=f"prd_{suffix}", name=suffix, slug=suffix,
                sku=f"SKU-{suffix}", description="Fixture", price=Decimal("100.10"), main_image="/fixture.png")
            add(conn, "product_variants", id=f"var_{suffix}", product_id=f"prd_{suffix}",
                sku=f"VAR-{suffix}", stock=5)
        add(conn, "orders", id="ord_a", order_number="ORDER-A", user_id="usr_a",
            subtotal=Decimal("100.10"), shipping_courier="fixture", shipping_service="regular",
            shipping_cost=0, total=Decimal("100.10"))
        add(conn, "order_items", id="item_a", order_id="ord_a", product_id="prd_a",
            variant_id="var_a", product_name="Historical A", quantity=1,
            unit_price=Decimal("100.10"), subtotal=Decimal("100.10"), sort_order=0)
        yield conn
    engine.dispose()


def add(connection, table, **values):
    connection.execute(TABLES[table].insert().values(**values))


def test_schema_covers_all_legacy_collections_and_new_domains():
    expected = {
        "users", "user_sessions", "addresses", "products", "categories", "brands",
        "lens_indexes", "cart_items", "wishlists", "product_reviews", "product_subscriptions",
        "orders", "order_status_logs", "stock_reservations", "stock_movements", "payment_logs",
        "shipment_logs", "vouchers", "flash_sales", "games", "game_scores", "roulette_rewards",
        "roulette_spins", "point_logs", "newsletter_subscribers", "newsletter_campaigns",
        "articles", "article_categories", "product_knowledges", "cms_pages", "faq_categories",
        "faqs", "banners", "contact_settings", "contact_messages", "uploads",
        "prescriptions", "prescription_eyes", "order_item_prescriptions", "order_item_components",
        "order_reviews", "flash_sale_categories", "flash_sale_items", "flash_sale_reservations",
        "payments", "shipments", "shipping_quotes", "integration_webhook_events",
        "settings", "whatsapp_settings", "virtual_try_on_assets", "migration_runs",
        "migration_records", "migration_issues",
    }
    assert expected <= set(TABLES)
    # cms_banners and banners_v2 intentionally converge on one banners table.
    assert "cms_banners" not in TABLES and "banners_v2" not in TABLES


def test_mysql_ddl_has_no_cycles_invalid_identifiers_or_float_money():
    dialect = mysql.dialect()
    with warnings.catch_warnings():
        warnings.simplefilter("error", SAWarning)
        ordered = Base.metadata.sorted_tables
    named_constraints = set()
    for table in ordered:
        ddl = str(CreateTable(table).compile(dialect=dialect))
        assert "ENGINE=InnoDB" in ddl
        assert "CHARSET=utf8mb4" in ddl
        assert "utf8mb4_unicode_ci" in ddl
        assert "ROW_FORMAT=DYNAMIC" in ddl
        assert not re.search(r"\bCHECK\s*\(", ddl)
        for column in table.columns:
            assert not isinstance(column.type, Float), (table.name, column.name)
        for constraint in table.constraints:
            if constraint.name:
                assert len(constraint.name) <= 64, constraint.name
                assert constraint.name not in named_constraints, constraint.name
                named_constraints.add(constraint.name)
        for index in table.indexes:
            assert len(index.name) <= 64
            str(CreateIndex(index).compile(dialect=dialect))


def test_every_foreign_key_targets_an_explicit_unique_key():
    # Explicit candidate keys keep the relational ownership constraints sound.
    for table in TABLES.values():
        for fk in table.foreign_key_constraints:
            remote_table = fk.elements[0].column.table
            remote_columns = tuple(element.column.name for element in fk.elements)
            keys = {tuple(c.name for c in remote_table.primary_key.columns)}
            keys.update(tuple(c.name for c in constraint.columns)
                        for constraint in remote_table.constraints
                        if isinstance(constraint, UniqueConstraint))
            assert remote_columns in keys, (table.name, remote_table.name, remote_columns)


def test_mysql_datetime_defaults_match_fractional_precision():
    for table in TABLES.values():
        for column in table.columns:
            if isinstance(column.type, UTCDateTime) and column.server_default is not None:
                expression = str(column.server_default.arg.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})).lower()
                assert expression in {"now(6)", "current_timestamp(6)"}, (table.name, column.name, expression)


@pytest.mark.parametrize("stock,reserved", [(-1, 0), (1, 2), (1, -1)])
def test_inventory_cannot_be_negative_or_over_reserved(connection, stock, reserved):
    with pytest.raises(IntegrityError):
        connection.execute(TABLES["product_variants"].update().where(
            TABLES["product_variants"].c.id == "var_a").values(stock=stock, reserved=reserved))


def test_variant_must_belong_to_cart_product(connection):
    with pytest.raises(IntegrityError):
        add(connection, "cart_items", user_id="usr_a", product_id="prd_a", variant_id="var_b", quantity=1)


def test_lens_variant_requires_its_product(connection):
    with pytest.raises(IntegrityError):
        add(connection, "cart_items", user_id="usr_a", product_id="prd_a", lens_variant_id="var_b", quantity=1)


def test_cart_prescription_must_belong_to_customer(connection):
    add(connection, "prescriptions", id="rx_b", user_id="usr_b")
    with pytest.raises(IntegrityError):
        add(connection, "cart_items", user_id="usr_a", product_id="prd_a", prescription_id="rx_b", quantity=1)


def test_cart_quantity_and_product_price_are_positive_or_nonnegative(connection):
    with pytest.raises(IntegrityError):
        add(connection, "cart_items", user_id="usr_a", product_id="prd_a", quantity=0)
    with pytest.raises(IntegrityError):
        connection.execute(TABLES["products"].update().where(TABLES["products"].c.id == "prd_a").values(price=-1))


def test_unique_email_sku_and_wishlist(connection):
    with pytest.raises(IntegrityError):
        add(connection, "users", user_id="usr_duplicate", email="a@example.invalid", name="Duplicate")
    with pytest.raises(IntegrityError):
        connection.execute(TABLES["products"].update().where(TABLES["products"].c.id == "prd_b").values(sku="SKU-a"))
    add(connection, "wishlists", user_id="usr_a", product_id="prd_a")
    with pytest.raises(IntegrityError):
        add(connection, "wishlists", user_id="usr_a", product_id="prd_a")


def test_only_one_default_address_per_user(connection):
    address = dict(user_id="usr_a", label="Home", recipient="A", phone="000", street="Fixture",
                   city="Fixture", province="Fixture", postal_code="00000", is_default=True)
    add(connection, "addresses", **address)
    with pytest.raises(IntegrityError):
        add(connection, "addresses", **address)
    add(connection, "addresses", **{**address, "is_default": False})


def test_foreign_key_prevents_orphan_and_financial_product_deletion(connection):
    with pytest.raises(IntegrityError):
        add(connection, "product_variants", product_id="missing", sku="ORPHAN")
    with pytest.raises(IntegrityError):
        connection.execute(TABLES["products"].delete().where(TABLES["products"].c.id == "prd_a"))


def test_approved_review_is_bound_to_purchased_product_and_customer(connection):
    review = dict(product_id="prd_a", user_id="usr_a", order_id="ord_a", order_item_id="item_a",
                  verified_purchase=True, user_name="A", rating=5, body="Fixture", status="approved")
    with pytest.raises(IntegrityError):
        add(connection, "product_reviews", **{**review, "user_id": "usr_b"})
    with pytest.raises(IntegrityError):
        add(connection, "product_reviews", **{**review, "product_id": "prd_b"})
    add(connection, "product_reviews", **review)
    with pytest.raises(IntegrityError):
        add(connection, "product_reviews", **review)


@pytest.mark.parametrize("rating", [0, 6])
def test_review_rating_range(connection, rating):
    with pytest.raises(IntegrityError):
        add(connection, "product_reviews", product_id="prd_a", user_id="usr_a", user_name="A", rating=rating, body="Fixture")


def test_verified_review_requires_purchase_link(connection):
    with pytest.raises(IntegrityError):
        add(connection, "product_reviews", product_id="prd_a", user_id="usr_a", user_name="A",
            rating=5, body="Fixture", verified_purchase=True)


def test_unverified_review_cannot_bypass_purchase_foreign_key_with_null_order(connection):
    with pytest.raises(IntegrityError):
        add(connection, "product_reviews", product_id="prd_a", user_id="usr_a", user_name="A",
            rating=5, body="Fixture", order_item_id="item_a", verified_purchase=False)


def test_order_prescription_snapshot_requires_same_customer(connection):
    add(connection, "prescriptions", id="rx_wrong_owner", user_id="usr_b", is_order_snapshot=True)
    with pytest.raises(IntegrityError):
        add(connection, "order_item_prescriptions", order_item_id="item_a", order_id="ord_a",
            user_id="usr_a", prescription_id="rx_wrong_owner")


def test_order_rating_requires_actual_order_owner(connection):
    with pytest.raises(IntegrityError):
        add(connection, "order_reviews", order_id="ord_a", user_id="usr_b", rating=5)


def test_prescription_pd_modes_and_axis(connection):
    with pytest.raises(IntegrityError):
        add(connection, "prescriptions", user_id="usr_a", pd_right=31)
    with pytest.raises(IntegrityError):
        add(connection, "prescriptions", user_id="usr_a", pd_total=62, pd_right=31, pd_left=31)
    add(connection, "prescriptions", id="rx_a", user_id="usr_a", pd_total=62)
    with pytest.raises(IntegrityError):
        add(connection, "prescription_eyes", prescription_id="rx_a", eye="right", axis=181)
    add(connection, "prescription_eyes", prescription_id="rx_a", eye="right", sph=Decimal("-1.25"),
        cyl=Decimal("-0.50"), axis=90, add=Decimal("1.00"))
    stored = connection.execute(select(TABLES["prescription_eyes"].c.sph)).scalar_one()
    assert stored == Decimal("-1.25")


def test_flash_sale_window_and_reserved_quota(connection):
    with pytest.raises(IntegrityError):
        add(connection, "flash_sales", name="Invalid", start_at=NOW, end_at=NOW)
    add(connection, "flash_sales", id="flash_a", name="Fixture", start_at=NOW, end_at=NOW + timedelta(hours=1))
    with pytest.raises(IntegrityError):
        add(connection, "flash_sale_items", flash_sale_id="flash_a", product_id="prd_a",
            flash_price=80, quota=2, sold=1, reserved=2)
    add(connection, "flash_sale_items", flash_sale_id="flash_a", product_id="prd_a", flash_price=80, quota=2, sold=1, reserved=1)


def test_payment_and_webhook_keys_are_unique(connection):
    payment = dict(order_id="ord_a", provider="doku", request_id="req-a", merchant_reference="reference-a", amount=Decimal("100.10"))
    add(connection, "payments", **payment)
    with pytest.raises(IntegrityError):
        add(connection, "payments", **{**payment, "merchant_reference": "reference-b"})
    webhook = dict(provider="doku", event_key="event-a", payload_hash="a" * 64, payload={"status": "test"})
    add(connection, "integration_webhook_events", **webhook)
    with pytest.raises(IntegrityError):
        add(connection, "integration_webhook_events", **webhook)


def test_decimal_prices_and_utc_round_trip(connection):
    table = TABLES["products"]
    row = connection.execute(select(table.c.price, table.c.created_at).where(table.c.id == "prd_a")).one()
    assert row.price == Decimal("100.10")
    assert row.created_at.tzinfo == timezone.utc


def test_mysql_foundation_import_does_not_load_mongo():
    code = "import sys; from mysql import models, config, database; import mysql_bootstrap; assert not any(n == 'motor' or n.startswith('motor.') or n == 'pymongo' or n.startswith('pymongo.') for n in sys.modules); print('isolated')"
    result = subprocess.run([sys.executable, "-c", code], cwd=BACKEND, text=True, capture_output=True, check=True)
    assert result.stdout.strip() == "isolated"
