"""Offline ETL contracts: every legacy collection, preservation and safe resume.

These portable tests do not claim MySQL server/trigger/locking verification.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os

import pytest
from sqlalchemy import event, func, select

from mysql.demo_seed import build_demo_documents, seed_with_factory
from mysql.importer import (
    COLLECTIONS, TABLES, ImportRejected, apply_plan, build_plan,
    canonical, decode_extended_json, plan_directory, stable_id,
)
from mysql.import_mongo import main as import_cli
from tests_mysql.sql_helpers import isolated_database


NOW = "2026-11-06T00:00:00+00:00"
NEXT = "2026-11-07T00:00:00+00:00"
PAST = "2026-11-01T00:00:00+00:00"


def full_export():
    """Synthetic source documents in the actual old API shapes, all 37 types."""
    d = {c: [] for c in COLLECTIONS}
    d["users"] = [
        {"user_id": "customer", "email": "customer@example.invalid", "name": "Customer", "password_hash": "keep-this-bcrypt-hash", "pin_hash": "keep-this-pin-hash", "points_balance": 20, "permissions": [], "created_at": PAST, "updated_at": NOW},
        {"user_id": "admin", "email": "admin@example.invalid", "name": "Admin", "role": "admin", "permissions": ["product.view"], "created_at": PAST, "updated_at": NOW},
    ]
    d["user_sessions"] = [{"session_id": "session", "user_id": "customer", "session_token": "secret-source-cookie", "created_at": NOW, "expires_at": NEXT}]
    d["addresses"] = [{"id": "address", "user_id": "customer", "label": "Home", "recipient": "Buyer", "phone": "62000000", "street": "Private street", "city": "City", "province": "Province", "postal_code": "12345", "is_default": True, "created_at": PAST}]
    d["categories"] = [{"id": "frame", "name": "Frame", "slug": "frame", "created_at": PAST}, {"id": "cat-child", "parent_id": "frame", "name": "Child", "slug": "child", "level": 1, "created_at": PAST}]
    d["brands"] = [{"id": "brand", "name": "Brand", "slug": "brand", "created_at": PAST}]
    d["products"] = [{"id": "product", "name": "Original frame name", "slug": "original-frame", "sku": "FRAME", "description": "Frame", "product_type": "frame", "price": "100.00", "main_image": "/frame.png", "created_at": PAST, "updated_at": NOW,
        "category_ids": ["frame", "cat-child"], "primary_category_id": "cat-child", "brand_id": "brand", "segments": ["Unisex"], "badges": ["new"], "gallery": ["/one.png", "/two.png"],
        "variants": [{"id": "variant", "sku": "FRAME-BL", "stock": 9, "reserved": 1, "color": "Black"}], "rating_avg": 5, "rating_count": 1, "sold_count": 2}]
    d["lens_indexes"] = [{"id": "index", "name": "Standard", "index_value": "1.50", "additional_price": "0.00"}]
    d["cart_items"] = [{"id": "cart", "user_id": "customer", "product_id": "product", "variant_id": "variant", "quantity": 1, "created_at": NOW,
        "prescription": {"od_sph": "-1.25", "os_sph": "", "od_cyl": "-0.50", "os_cyl": "", "pd": "62.5", "notes": "Private prescription note"}}]
    d["wishlists"] = [{"id": "wishlist", "user_id": "customer", "product_id": "product", "created_at": NOW}]
    d["product_subscriptions"] = [{"id": "subscription", "user_id": "customer", "product_id": "product", "created_at": NOW}]
    base_order = {"user_id": "customer", "address": deepcopy(d["addresses"][0]), "shipping_courier": "jne", "shipping_service": "REG", "shipping_cost": "2.50", "payment_method": "VA", "payment_url": "https://example.invalid/pay", "reservation_expires_at": NEXT, "created_at": NOW, "updated_at": NOW, "voucher_code": "SAVE", "voucher_discount": "10.00"}
    d["orders"] = [
        {**base_order, "id": "pending-order", "order_number": "ORDER-PENDING", "subtotal": "100.00", "total": "87.50", "roulette_reward_id": "spin", "roulette_discount": "5.00",
         "items": [{"product_id": "product", "variant_id": "variant", "product_name": "Historical frame label", "quantity": 1, "unit_price": "100.00", "subtotal": "100.00"}]},
        {**base_order, "id": "complete-order", "order_number": "ORDER-COMPLETE", "subtotal": "200.00", "total": "192.50", "status": "completed", "payment_status": "paid", "shipment_status": "delivered", "tracking_number": "AWB-1", "completed_at": NOW,
         "items": [{"product_id": "product", "variant_id": "variant", "product_name": "Historical frame label", "quantity": 2, "unit_price": "100.00", "subtotal": "200.00"}]},
    ]
    d["order_status_logs"] = [{"id": "status-log", "order_id": "complete-order", "status": "completed", "admin": "admin", "note": "Complete", "created_at": NOW}]
    d["stock_reservations"] = [{"id": "reservation", "order_id": "pending-order", "product_id": "product", "variant_id": "variant", "quantity": 1, "status": "active", "expires_at": NEXT, "created_at": NOW}]
    d["stock_movements"] = [{"id": "movement", "order_id": "complete-order", "product_id": "product", "variant_id": "variant", "type": "sold", "quantity": 2, "created_at": NOW}]
    d["payment_logs"] = [{"id": "payment-log", "order_id": "complete-order", "provider": "doku-mock", "action": "webhook_paid", "payload": {"order_number": "ORDER-COMPLETE"}, "response": {"status": "paid"}, "created_at": NOW}]
    d["shipment_logs"] = [{"id": "shipment-log", "order_id": "complete-order", "provider": "everpro-mock", "action": "create_shipment", "response": {"awb": "AWB-1"}, "created_at": NOW}]
    d["vouchers"] = [{"id": "voucher", "code": "SAVE", "name": "Save", "discount_type": "nominal", "discount_value": "10.00", "quota": 5, "used_count": 2, "quota_per_user": 5, "start_at": PAST, "end_at": NEXT, "created_at": PAST}]
    d["flash_sales"] = [{"id": "flash", "name": "Sale", "start_at": PAST, "end_at": NEXT, "created_at": PAST, "items": [{"product_id": "product", "flash_price": "80.00", "quota": 10, "sold": 0}]}]
    d["games"] = [{"id": "game", "key": "puzzle", "name": "Puzzle", "created_at": PAST}]
    d["game_scores"] = [{"id": "score", "user_id": "customer", "game": "puzzle", "score": 100, "points_awarded": 20, "played_at": NOW}]
    d["roulette_rewards"] = [{"id": "reward", "label": "Discount", "type": "discount", "value": "5.00", "probability": "0.5"}]
    d["roulette_spins"] = [{"id": "spin", "user_id": "customer", "reward_id": "reward", "reward_label": "Discount", "reward_type": "discount", "reward_value": "5.00", "used": True, "used_order_id": "pending-order", "expires_at": NEXT, "created_at": NOW}]
    d["point_logs"] = [{"id": "points", "user_id": "customer", "delta": 20, "balance_after": 20, "type": "earn_game", "note": "Fixture", "created_at": NOW}]
    d["newsletter_subscribers"] = [{"id": "newsletter", "email": "customer@example.invalid", "user_id": "customer", "created_at": NOW}]
    d["newsletter_campaigns"] = [{"id": "campaign", "subject": "News", "body": "Fixture", "status": "draft", "created_at": NOW}]
    d["article_categories"] = [{"id": "article-category", "name": "News", "slug": "news", "created_at": PAST}]
    d["articles"] = [{"id": "article", "category_id": "article-category", "author_id": "admin", "title": "Article", "slug": "article", "content": "<p>Preserved HTML</p>", "tags": ["eyewear", "news"], "status": "published", "created_at": PAST, "updated_at": NOW, "published_at": NOW}]
    d["product_knowledges"] = [{"id": "knowledge", "knowledge_type": "frame_shape", "title": "Round", "slug": "round", "content": "<p>Knowledge</p>", "pros": ["One", "Two"], "cons": ["Three"], "related_product_ids": ["product"], "is_published": True, "created_at": NOW}]
    d["cms_pages"] = [{"id": "page", "title": "About", "slug": "about", "content": "<p>Page</p>", "status": "published", "created_at": PAST, "updated_at": NOW}]
    d["faq_categories"] = [{"id": "faq-category", "name": "Shopping", "slug": "shopping"}]
    d["faqs"] = [{"id": "faq", "category_id": "faq-category", "question": "How?", "answer": "Like this.", "created_at": NOW}]
    d["cms_banners"] = [{"id": "legacy-banner", "title": "Legacy", "image": "/legacy.png", "link": "/shop-now", "created_at": NOW}]
    d["banners_v2"] = [{"id": "banner", "title": "New", "image_desktop": "/new.png", "link_url": "/products/original-frame", "link_type": "product", "reference_id": "product", "created_at": NOW}]
    d["contact_settings"] = [{"id": "contact", "store_name": "Store", "address": "Store address", "email": "store@example.invalid", "phone": "62000000", "whatsapp": "628000000", "operational_hours": "09:00-17:00", "updated_at": NOW}]
    d["contact_messages"] = [{"id": "message", "name": "Visitor", "email": "visitor@example.invalid", "message": "Hello", "created_at": NOW}]
    d["uploads"] = [{"id": "upload", "url": "/upload.png", "filename": "upload.png", "mime": "image/png", "size": 123, "uploaded_by": "admin", "created_at": NOW}]
    d["product_reviews"] = [{"id": "review", "product_id": "product", "user_id": "customer", "user_name": "Customer", "order_id": "complete-order", "rating": 5, "body": "Great", "images": ["/review.png"], "is_approved": True, "status": "approved", "created_at": NOW}]
    assert len(d) == 37 and all(d.values())
    return d


def test_all_37_collections_expand_without_fabricating_history_or_leaking_secrets():
    plan = build_plan(full_export())
    assert not plan.errors, plan.errors
    assert {s.collection for s in plan.sources} == set(COLLECTIONS)
    assert len(plan.rows) > len(plan.sources)
    rows = {r.table: [] for r in plan.rows}
    for row in plan.rows:
        rows[row.table].append(row.values)
    assert rows["user_sessions"][0]["token_hash"] == hashlib.sha256(b"secret-source-cookie").hexdigest()
    user = next(v for v in rows["users"] if v["user_id"] == "customer")
    assert user["password_hash"] == "keep-this-bcrypt-hash"
    assert rows["prescription_eyes"][0]["sph"] == Decimal("-1.25")
    assert len(rows["prescription_eyes"]) == 1
    assert rows["prescriptions"][0]["pd_total"] == Decimal("62.50")
    assert rows["product_reviews"][0]["verified_purchase"] is True
    assert rows["product_reviews"][0]["order_item_id"] == stable_id("orders", "complete-order", "item", 0)
    assert {r["status"] for r in rows["voucher_redemptions"]} == {"reserved", "redeemed"}
    assert rows["roulette_redemptions"][0]["spin_id"] == "spin"
    assert all(v["product_name"] == "Historical frame label" for v in rows["order_items"])
    assert "order_item_components" not in rows and "order_item_prescriptions" not in rows
    assert len(rows["payments"]) == 2 and rows["shipments"][0]["tracking_number"] == "AWB-1"
    assert all(v["paid_at"] is None for v in rows["payments"])
    report = canonical(plan.report())
    for secret in ["secret-source-cookie", "keep-this-bcrypt-hash", "keep-this-pin-hash", "Private street", "Private prescription note", "-1.25"]:
        assert secret not in report
    assert plan.reconciliation["order_total"] == "280.00"
    assert plan.reconciliation["reserved_units"] == plan.reconciliation["active_reservation_units"] == 1


def test_exact_ids_and_plan_are_deterministic_despite_collection_order():
    data = full_export()
    first = build_plan(data)
    reverse = build_plan(dict(reversed(list(data.items()))))
    assert first.export_checksum == reverse.export_checksum
    assert [(r.table, r.key_text, canonical(r.values)) for r in first.rows] == [(r.table, r.key_text, canonical(r.values)) for r in reverse.rows]


@pytest.mark.parametrize("mutation,code", [
    (lambda d: d["users"][0].update(custom_unmapped="must-not-disappear"), "unknown_field"),
    (lambda d: d["products"][0]["variants"][0].update(unmapped="x"), "unknown_field"),
    (lambda d: d["users"][0].update(created_at="2026-11-06T12:00:00"), "invalid_column_value"),
    (lambda d: d["cart_items"][0].update(quantity=Decimal("1.5")), "invalid_column_value"),
    (lambda d: d["products"][0].update(price="10000000000000000.00"), "invalid_column_value"),
    (lambda d: d["cart_items"][0].update(product_id="missing"), "foreign_key_violation"),
    (lambda d: d["users"][1].update(email="CUSTOMER@example.invalid"), "unique_key_collision"),
    (lambda d: d["banners_v2"][0].update(id="legacy-banner"), "unique_key_collision"),
    (lambda d: d["categories"][0].update(parent_id="cat-child"), "category_cycle"),
    (lambda d: d["product_reviews"][0].update(user_id="admin"), "review_owner_mismatch"),
    (lambda d: d["product_reviews"][0].update(status="hidden"), "review_moderation_conflict"),
    (lambda d: d["products"][0]["variants"][0].update(reserved=2), "inventory_reservation_mismatch"),
    (lambda d: d["users"][0].update(points_balance=21), "point_balance_mismatch"),
    (lambda d: d["vouchers"][0].update(used_count=3), "voucher_redemption_mismatch"),
    (lambda d: d["orders"][0].update(total="999.00"), "order_total_mismatch"),
    (lambda d: d["orders"][0]["items"][0].update(subtotal="99.00"), "order_line_amount_mismatch"),
    (lambda d: d["payment_logs"][0].update(payload={"authorization": "sensitive"}), "provider_secret_present"),
    (lambda d: d["products"][0]["variants"][0].update(sort_order=9), "conflicting_array_order"),
    (lambda d: d["cms_banners"][0].update(image_desktop="/different.png"), "conflicting_banner_alias"),
    (lambda d: d["cms_banners"][0].update(link_url="/different-destination"), "conflicting_banner_alias"),
    (lambda d: d["cart_items"][0].update(prescription_id="explicit-source-prescription"), "conflicting_prescription_reference"),
    (lambda d: d["product_reviews"][0].update(order_item_id="different-source-line"), "conflicting_review_line"),
    (lambda d: d["product_reviews"][0].update(verified_purchase=False), "conflicting_review_verification"),
    (lambda d: d["orders"][0]["items"][0].update(id=""), "invalid_column_value"),
    (lambda d: d["flash_sales"][0]["items"][0].update(id=""), "invalid_column_value"),
    (lambda d: d["stock_reservations"][0].update(variant_id=None), "active_reservation_variant_missing"),
])
def test_source_issues_are_blocking_not_silently_repaired(mutation, code):
    data = full_export()
    mutation(data)
    plan = build_plan(data)
    assert code in {issue.code for issue in plan.errors}, plan.errors
    assert not plan.report()["ready_for_apply"]


def test_matching_explicit_derived_fields_and_canonical_banner_values_are_preserved():
    data = full_export()
    data["products"][0]["variants"][0]["sort_order"] = 0
    data["cart_items"][0]["prescription_id"] = stable_id("cart_items", "cart", "prescription", "cart")
    data["product_reviews"][0]["verified_purchase"] = True
    data["product_reviews"][0]["order_item_id"] = stable_id("orders", "complete-order", "item", 0)
    banner = data["cms_banners"][0]
    banner["image_desktop"] = banner.pop("image")
    banner["link_url"] = banner.pop("link")
    plan = build_plan(data)
    assert not plan.errors, plan.errors
    result = next(r.values for r in plan.rows if r.table == "banners" and r.values["id"] == "legacy-banner")
    assert result["image_desktop"] == "/legacy.png"
    assert result["link_url"] == "/shop-now"


def test_missing_note_uses_literal_default_without_inventing_ids_or_timestamps():
    data = full_export()
    del data["point_logs"][0]["note"]
    plan = build_plan(data)
    assert not plan.errors, plan.errors
    note = next(r.values["note"] for r in plan.rows if r.table == "point_logs")
    assert note == ""
    del data["users"][0]["user_id"]
    del data["point_logs"][0]["created_at"]
    refused = build_plan(data)
    assert {"missing_application_id", "missing_timestamp"} <= {i.code for i in refused.errors}


def test_decimal_rounding_is_explicit_and_requires_acknowledgement():
    data = full_export()
    data["products"][0]["price"] = Decimal("100.105")
    plan = build_plan(data)
    assert not plan.errors
    assert any(i.code == "decimal_rounded" for i in plan.warnings)
    assert next(r for r in plan.rows if r.table == "products").values["price"] == Decimal("100.11")


def test_jsonl_and_canonical_extended_json_default_dry_run(tmp_path, monkeypatch, capsys):
    data = full_export()
    data["users"][0]["_id"] = {"$oid": "0123456789abcdef01234567"}
    data["users"][0]["created_at"] = {"$date": {"$numberLong": "1761955200000"}}
    data["products"][0]["price"] = {"$numberDecimal": "100.00"}
    data["products"][0]["variants"][0]["stock"] = {"$numberInt": "9"}
    export = tmp_path / "export"
    export.mkdir()
    for i, (coll, values) in enumerate(data.items()):
        (export / (coll + (".jsonl" if i % 2 else ".json"))).write_text("\n".join(json.dumps(v) for v in values) if i % 2 else json.dumps(values))
    monkeypatch.delenv("MYSQL_HOST", raising=False)
    monkeypatch.delenv("MYSQL_PASSWORD", raising=False)
    report = tmp_path / "report.json"
    assert import_cli([str(export), "--report", str(report)]) == 0
    result = json.loads(report.read_text())
    assert result["database_connected"] is False and result["target_writes"] == 0
    assert result["plan"]["source_counts"]["users"] == 2
    assert "secret-source-cookie" not in capsys.readouterr().out
    (export / "brands.json").unlink()
    assert any(i.code == "missing_collection_file" for i in plan_directory(export).errors)


@pytest.mark.parametrize("alias", ["direct", "symlink", "hardlink", "nested"])
def test_rejected_report_destination_never_changes_source_bytes(tmp_path, alias, capsys):
    export = tmp_path / "export"
    export.mkdir()
    source = export / "users.json"
    original = b'[{"user_id":"preserve-me","name":"Original source bytes"}]\n'
    source.write_bytes(original)
    report = source
    if alias == "symlink":
        report = tmp_path / "report.json"
        report.symlink_to(source)
    elif alias == "hardlink":
        report = tmp_path / "report.json"
        os.link(source, report)
    elif alias == "nested":
        report = export / "reports" / "report.json"
    assert import_cli([str(export), "--report", str(report)]) == 2
    assert source.read_bytes() == original
    if alias == "nested":
        assert not report.parent.exists()
    else:
        assert report.read_bytes() == original
    assert json.loads(capsys.readouterr().out)["ok"] is False


@pytest.mark.parametrize("value", [float("nan"), {"$numberDouble": "Infinity"}, {"$binary": {"base64": "AA=="}}, {"$date": "2026-11-06"}])
def test_unsupported_or_ambiguous_extended_values_are_rejected(value):
    if isinstance(value, float):
        with pytest.raises(ValueError):
            canonical(value)
    else:
        with pytest.raises(ValueError):
            decode_extended_json(value)


def test_apply_roundtrip_resume_and_verified_provenance():
    async def run():
        plan = build_plan(full_export())
        async with isolated_database() as factory:
            with pytest.raises(ImportRejected, match="warnings"):
                await apply_plan(plan, factory, source_label="fixture")
            first = await apply_plan(plan, factory, source_label="fixture", acknowledge_warnings=True, chunk_size=7)
            assert first["verified_target_rows"] == len(plan.rows)
            second = await apply_plan(plan, factory, source_label="fixture", acknowledge_warnings=True, chunk_size=7)
            assert second["run_id"] == first["run_id"]
            assert second["resumed_rows"] == len(plan.rows)
            async with factory() as session:
                for table, expected in plan.report()["target_counts"].items():
                    assert (await session.execute(select(func.count()).select_from(TABLES[table]))).scalar_one() == expected
                records = (await session.execute(select(TABLES["migration_records"]))).mappings().all()
                assert len(records) == len(plan.rows)
                assert all(r["status"] == "verified" for r in records)
                session_row = (await session.execute(select(TABLES["user_sessions"]))).mappings().one()
                assert session_row["token_hash"] == hashlib.sha256(b"secret-source-cookie").hexdigest()
    asyncio.run(run())


def test_interrupted_chunk_rolls_back_and_resumes_without_duplicate_rows():
    async def run():
        plan = build_plan(full_export())
        async with isolated_database() as factory:
            engine = factory.kw["bind"]
            state = {"fail": True}
            @event.listens_for(engine.sync_engine, "before_cursor_execute")
            def interrupt(conn, cursor, statement, parameters, context, executemany):
                if state["fail"] and statement.startswith("INSERT INTO products "):
                    state["fail"] = False
                    raise RuntimeError("simulated interruption")
            with pytest.raises(RuntimeError, match="simulated"):
                await apply_plan(plan, factory, source_label="fixture", acknowledge_warnings=True, chunk_size=2)
            async with factory() as session:
                imported = (await session.execute(select(func.count()).select_from(TABLES["migration_records"]))).scalar_one()
                assert 0 < imported < len(plan.rows)
                assert (await session.execute(select(TABLES["migration_runs"].c.status))).scalar_one() == "failed"
            result = await apply_plan(plan, factory, source_label="fixture", acknowledge_warnings=True, chunk_size=2)
            assert result["resumed_rows"] == imported
            assert result["verified_target_rows"] == len(plan.rows)
    asyncio.run(run())


def test_existing_data_and_resume_drift_are_never_overwritten():
    async def run():
        plan = build_plan(full_export())
        async with isolated_database() as factory:
            async with factory() as session, session.begin():
                await session.execute(TABLES["users"].insert().values(user_id="real", email="real@example.invalid", name="Keep"))
            with pytest.raises(ImportRejected, match="contains business data"):
                await apply_plan(plan, factory, source_label="fixture", acknowledge_warnings=True)
        async with isolated_database() as factory:
            result = await apply_plan(plan, factory, source_label="fixture", acknowledge_warnings=True)
            async with factory() as session, session.begin():
                await session.execute(TABLES["users"].update().where(TABLES["users"].c.user_id == "customer").values(name="Changed outside import"))
            with pytest.raises(ImportRejected, match="changed or disappeared"):
                await apply_plan(plan, factory, source_label="fixture", acknowledge_warnings=True)
            changed = full_export()
            changed["users"][0]["name"] = "Changed export"
            with pytest.raises(ImportRejected, match="checksum/schema differs"):
                await apply_plan(build_plan(changed), factory, source_label="fixture", run_id=result["run_id"], acknowledge_warnings=True)
    asyncio.run(run())


def test_demo_seed_is_explicit_idempotent_and_refuses_real_data():
    async def run():
        hashes = {role: "fixture-bcrypt-hash" for role in ["super_admin", "customer", "staff"]}
        when = datetime(2026, 11, 6, tzinfo=timezone.utc)
        docs = build_demo_documents(password_hashes=hashes, pin_hash="fixture-pin-hash", when=when)
        assert len(docs["products"]) == 20
        assert len({p["sku"] for p in docs["products"]}) == 20
        assert not build_plan(docs).errors
        async with isolated_database() as factory:
            with pytest.raises(ImportRejected, match="--demo"):
                await seed_with_factory(factory, confirmed=False, environment="test")
            with pytest.raises(ImportRejected, match="outside development/test"):
                await seed_with_factory(factory, confirmed=True, environment="production")
            seeded = await seed_with_factory(factory, confirmed=True, environment="test", password_hashes=hashes, pin_hash="fixture-pin-hash", when=when)
            assert seeded["inserted_rows"] > 300
            again = await seed_with_factory(factory, confirmed=True, environment="test")
            assert again["status"] == "already_seeded" and again["inserted_rows"] == 0
        async with isolated_database() as factory:
            async with factory() as session, session.begin():
                await session.execute(TABLES["users"].insert().values(user_id="real", email="real@example.invalid", name="Keep"))
            with pytest.raises(ImportRejected, match="not empty"):
                await seed_with_factory(factory, confirmed=True, environment="test", password_hashes=hashes, pin_hash="fixture-pin-hash", when=when)
            async with factory() as session:
                assert (await session.execute(select(TABLES["users"].c.name))).scalar_one() == "Keep"
                assert (await session.execute(select(func.count()).select_from(TABLES["products"]))).scalar_one() == 0
    asyncio.run(run())
