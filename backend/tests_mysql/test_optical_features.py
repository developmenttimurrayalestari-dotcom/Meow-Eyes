"""Feature-level regressions with real normalized SQL writes and HTTP contracts.

SQLite verifies ownership, snapshots, constraints and API behavior here. It does
not substitute for the separately gated MySQL 5.7 locking/migration test.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

import httpx
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from auth import current_user, current_user_optional
from database import read_session, session_scope
from models import User
from mysql import models as m
from mysql.base import utcnow
from mysql.commerce import confirm_mock_payment, create_checkout, priced_cart
from mysql.feature_content import FEATURE_SEED_KEY, KNOWLEDGE_ENTRIES, ensure_feature_content
from tests_mysql.commerce_scenarios import seed_commerce_fixture
from tests_mysql.sql_helpers import isolated_database
import routes_admin
import routes_admin_content
import routes_catalog
import routes_content
import routes_features
import routes_shopping
import routes_uploads


@pytest.fixture(autouse=True)
def isolated_feature_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_MOCK_PAYMENTS", "1")
    monkeypatch.setenv("PAYMENT_PROVIDER", "mock")
    monkeypatch.setenv("SHIPPING_PROVIDER", "mock")


@asynccontextmanager
async def feature_client(*, bundle=True):
    async with isolated_database() as factory:
        d = await seed_commerce_fixture(bundle=bundle, quantity=1)
        auth = {"user": d["user"]}
        d["admin_user"] = User(user_id=d["admin"], email="admin@example.com", name="Admin", role="admin")
        d["bob_user"] = User(user_id=d["bob"], email="bob@example.com", name="Bob")
        app = FastAPI()
        app.dependency_overrides[current_user] = lambda: auth["user"]
        app.dependency_overrides[current_user_optional] = lambda: auth["user"]
        @app.exception_handler(IntegrityError)
        async def conflict(request, exc):
            return JSONResponse(status_code=409, content={"detail": "Data terkait/duplikat"})
        for module in (routes_catalog, routes_shopping, routes_admin, routes_admin_content,
                       routes_content, routes_features, routes_uploads):
            app.include_router(module.router, prefix="/api")
        app.add_api_route("/api/uploads-files/{file_path:path}", routes_uploads.public_upload_file,
                          methods=["GET", "HEAD"], include_in_schema=False)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            yield client, auth, d, factory


def png_bytes():
    image = Image.new("RGB", (20, 20), "white")
    data = BytesIO()
    image.save(data, "PNG")
    return data.getvalue()


def test_flash_sale_uses_regular_price_and_excludes_other_checkout_discounts():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            await category_fixture(d)
            async with session_scope() as s:
                product = await s.get(m.Product, d["frame"])
                product.price, product.discount_price = Decimal("420000"), Decimal("350000")
            auth["user"] = d["admin_user"]
            now = utcnow()
            created = await client.post("/api/admin/flash-sales", json={"name": "Exclusive 60%",
                "start_at": (now - timedelta(hours=1)).isoformat(), "end_at": (now + timedelta(hours=1)).isoformat(),
                "category_rules": [{"category_id": "root_frames", "include_descendants": True,
                    "discount_type": "percent", "discount_value": 60, "quota_per_product": 5}]})
            assert created.status_code == 200, created.text
            flash = created.json()["flash_sale"]
            item = flash["items"][0]
            assert item["flash_price"] == 168000
            public = (await client.get(f'/api/products/{d["frame"]}')).json()["product"]
            assert public["flash_sale_price"] == 168000 and public["discount_price"] is None
            async with session_scope() as s:
                (await s.get(m.FlashSaleItem, item["id"])).flash_price = Decimal("140000")
            refresh = await client.post(f'/api/admin/flash-sales/{flash["id"]}/refresh-categories')
            assert refresh.status_code == 200, refresh.text
            assert refresh.json()["flash_sale"]["items"][0]["flash_price"] == 168000
            req = d["req"].model_copy(update={"use_points": 2, "voucher_code": d["voucher"].upper(), "roulette_spin_id": d["spin"]})
            from mysql.commerce import checkout_quote
            async with read_session() as s:
                quote = await checkout_quote(s, await s.get(m.User, d["alice"]), req)
                assert quote.payload()["flash_sale_exclusive"]
                assert quote.subtotal == Decimal("168000")
                assert quote.voucher is None and quote.roulette is None and quote.points_used == 0
                assert quote.voucher_discount == quote.roulette_discount == quote.points_discount == 0
            order = (await create_checkout(d["alice"], req))["order"]
            async with read_session() as s:
                assert (await s.get(m.User, d["alice"])).points_balance == 100
                assert (await s.get(m.Voucher, d["voucher"])).used_count == 0
                assert not (await s.get(m.RouletteSpin, d["spin"])).used
            denied = await client.delete(f'/api/admin/flash-sales/{flash["id"]}')
            assert denied.status_code == 409
            assert order["id"]
    asyncio.run(run())


def test_admin_can_delete_unused_flash_sale_and_its_category_children():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            await category_fixture(d)
            auth["user"] = d["admin_user"]
            now = utcnow()
            response = await client.post("/api/admin/flash-sales", json={"name": "Delete me",
                "start_at": (now - timedelta(hours=1)).isoformat(), "end_at": (now + timedelta(hours=1)).isoformat(),
                "category_rules": [{"category_id": "root_frames", "include_descendants": True,
                    "discount_type": "percent", "discount_value": 60, "quota_per_product": 5}]})
            assert response.status_code == 200, response.text
            flash = response.json()["flash_sale"]
            auth["user"] = d["user"]
            assert (await client.delete(f'/api/admin/flash-sales/{flash["id"]}')).status_code == 403
            auth["user"] = d["admin_user"]
            assert (await client.delete(f'/api/admin/flash-sales/{flash["id"]}')).status_code == 200
            async with read_session() as s:
                assert await s.get(m.FlashSale, flash["id"]) is None
                assert await s.scalar(select(m.FlashSaleItem.id).where(m.FlashSaleItem.flash_sale_id == flash["id"])) is None
                assert (await s.execute(select(m.FlashSaleCategory).where(m.FlashSaleCategory.flash_sale_id == flash["id"])) ).first() is None
            assert (await client.delete(f'/api/admin/flash-sales/{flash["id"]}')).status_code == 404
    asyncio.run(run())


def test_whatsapp_admin_persistence_normalization_and_permissions():
    async def run():
        async with feature_client() as (client, auth, d, _):
            assert (await client.get("/api/settings/whatsapp")).json() == {
                "enabled": False, "phone_number": "", "default_text": ""}
            payload = {"enabled": True, "phone_number": "0812-3456-7890", "default_text": "Halo, saya ingin bertanya."}
            assert (await client.put("/api/admin/settings/whatsapp", json=payload)).status_code == 403
            auth["user"] = d["admin_user"]
            saved = await client.put("/api/admin/settings/whatsapp", json=payload)
            assert saved.status_code == 200, saved.text
            assert saved.json()["phone_number"] == "6281234567890"
            assert (await client.get("/api/settings/whatsapp")).json()["default_text"] == payload["default_text"]
            assert (await client.put("/api/admin/settings/whatsapp", json={**payload, "phone_number": "javascript:42"})).status_code == 422
            assert (await client.put("/api/admin/settings/whatsapp", json={**payload, "phone_number": ""})).status_code == 422
            await client.put("/api/admin/settings/whatsapp", json={**payload, "enabled": False})
            assert not (await client.get("/api/settings/whatsapp")).json()["enabled"]
            legacy = await client.put("/api/admin/contact-setting", json={"whatsapp": "0812 5555 6666"})
            assert legacy.status_code == 200, legacy.text
            assert (await client.get("/api/settings/whatsapp")).json()["phone_number"] == "6281255556666"
            assert (await client.put("/api/admin/contact-setting", json={"whatsapp": "invalid"})).status_code == 422
    asyncio.run(run())


def test_try_on_sources_visibility_variants_and_published_filter():
    async def run():
        async with feature_client() as (client, auth, d, _):
            payload = {"product_id": d["frame"], "asset_type": "image", "source_url": "https://cdn.example.com/frame.png",
                       "scale": 1.25, "offset_y": .1, "status": "draft", "sort_order": 2}
            assert (await client.post("/api/admin/try-on-assets", json=payload)).status_code == 403
            auth["user"] = d["bob_user"].model_copy(update={"role": "staff", "permissions": ["product.view"]})
            frame_choices = await client.get("/api/admin/products?product_type=frame")
            assert frame_choices.status_code == 200
            assert [p["id"] for p in frame_choices.json()["products"]] == [d["frame"]]
            assert (await client.post("/api/admin/try-on-assets", json=payload)).status_code == 403
            auth["user"] = d["admin_user"]
            response = await client.post("/api/admin/try-on-assets", json=payload)
            assert response.status_code == 200, response.text
            asset_id = response.json()["asset"]["id"]
            assert (await client.get(f'/api/products/{d["frame"]}/try-on')).json()["assets"] == []
            response = await client.patch(f"/api/admin/try-on-assets/{asset_id}", json={"status": "published"})
            assert response.status_code == 200, response.text
            public = (await client.get(f'/api/products/{d["frame"]}/try-on')).json()["assets"]
            assert len(public) == 1 and public[0]["scale"] == 1.25
            detail = (await client.get(f'/api/products/{d["frame"]}')).json()
            assert detail["product"]["supports_try_on"]
            for change in ({"source_url": "javascript:alert(1)"}, {"source_url": "//untrusted.example/frame.png"},
                           {"source_url": "/api/prescriptions/uploads/private"}, {"variant_id": d["vl"]},
                           {"product_id": d["lens"]}, {"scale": 0}, {"asset_type": "html"}):
                failed = await client.post("/api/admin/try-on-assets", json={**payload, **change})
                assert failed.status_code == 422, (change, failed.text)
            async with session_scope() as s:
                s.add(m.Upload(id="public_asset", url="/api/uploads-files/asset.png", filename="asset.png", mime="image/png",
                    size=8, visibility="public", uploaded_by=d["admin"]))
                s.add(m.Upload(id="private_asset", url="/api/prescriptions/uploads/private_asset", filename="rx.jpg", mime="image/jpeg",
                    size=8, visibility="private", uploaded_by=d["alice"]))
            invalid = await client.post("/api/admin/try-on-assets", json={"product_id": d["frame"], "upload_id": "private_asset"})
            assert invalid.status_code == 422
            created = await client.post("/api/admin/try-on-assets", json={"product_id": d["frame"], "upload_id": "public_asset", "status": "published"})
            assert created.status_code == 200, created.text
            assert created.json()["asset"]["source_url"] == "/api/uploads-files/asset.png"
            await client.patch(f"/api/admin/try-on-assets/{asset_id}", json={"status": "archived"})
            assets = (await client.get(f'/api/products/{d["frame"]}/try-on')).json()["assets"]
            assert [a["id"] for a in assets] == [created.json()["asset"]["id"]]
            specific = await client.post("/api/admin/try-on-assets", json={"product_id": d["frame"], "variant_id": d["vf"],
                "asset_type": "glb", "source_url": "https://cdn.example.com/frame.glb", "status": "published"})
            assert specific.status_code == 200, specific.text
            await client.delete('/api/admin/try-on-assets/' + created.json()["asset"]["id"])
            async with session_scope() as s:
                (await s.get(m.ProductVariant, d["vf"])).is_active = False
            assert (await client.get(f'/api/products/{d["frame"]}/try-on')).json()["assets"] == []
            assert not (await client.get(f'/api/products/{d["frame"]}')).json()["product"]["supports_try_on"]
    asyncio.run(run())


def test_private_rx_photo_is_decoded_nonpublic_and_owner_or_fulfilment_only(tmp_path, monkeypatch):
    monkeypatch.setattr(routes_features, "PRIVATE_UPLOAD_ROOT", tmp_path / "private")
    monkeypatch.setattr(routes_uploads, "UPLOAD_ROOT", tmp_path / "public")
    async def run():
        async with feature_client() as (client, auth, d, _):
            uploaded = await client.post("/api/uploads/prescription", files={"file": ("resep.png", png_bytes(), "image/png")})
            assert uploaded.status_code == 200, uploaded.text
            asset = uploaded.json()
            assert asset["visibility"] == "private" and asset["mime"] == "image/jpeg"
            owner = await client.get(asset["url"])
            assert owner.status_code == 200 and owner.content.startswith(b"\xff\xd8\xff")
            assert "no-store" in owner.headers["cache-control"]
            async with read_session() as s:
                key = (await s.get(m.Upload, asset["id"])).storage_key
            assert (await client.get("/api/uploads-files/" + key)).status_code == 404
            auth["user"] = d["bob_user"]
            assert (await client.get(asset["url"])).status_code == 404
            auth["user"] = d["bob_user"].model_copy(update={"role": "staff", "permissions": ["product.update"]})
            assert (await client.get(asset["url"])).status_code == 404
            auth["user"] = d["bob_user"].model_copy(update={"role": "staff", "permissions": ["order.view"]})
            assert (await client.get(asset["url"])).status_code == 404  # Not attached to an order yet.
            auth["user"] = d["user"]
            patched = await client.patch(f'/api/cart/{d["cart"]}/prescription', json={
                "od_sph": -1.25, "os_sph": -1, "od_cyl": -.5, "od_axis": 120, "od_add": 1.5,
                "pd_right": 31, "pd_left": 30.5, "attachment_upload_id": asset["id"], "notes": "Resep asli"})
            assert patched.status_code == 200, patched.text
            assert patched.json()["prescription"]["pd_left"] == 30.5
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            assert order["items"][0]["prescription"]["attachment_upload_id"] == asset["id"]
            auth["user"] = d["bob_user"].model_copy(update={"role": "staff", "permissions": ["order.view"]})
            assert (await client.get(asset["url"])).status_code == 200
            assert (await client.get("/api/admin/orders")).status_code == 200
            assert (await client.post(f'/api/admin/orders/{order["id"]}/status', json={"status": "shipped"})).status_code == 403
            auth["user"] = d["admin_user"]
            assert (await client.get(asset["url"])).status_code == 200
            bad = await client.post("/api/uploads/prescription", files={"file": ("fake.png", b"\x89PNG\r\n\x1a\nmalformed", "image/png")})
            assert bad.status_code == 415
            assert (await client.post("/api/uploads/prescription", files={"file": ("bad.svg", b"<svg/>", "image/svg+xml")})).status_code == 415
    asyncio.run(run())


def test_each_standalone_cart_line_keeps_its_own_photo_and_notes_in_order_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(routes_features, "PRIVATE_UPLOAD_ROOT", tmp_path / "private")
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            package_id, package_variant, package_cart = (d["prefix"] + suffix for suffix in ("_package", "_pv", "_pc"))
            async with session_scope() as s:
                (await s.get(m.CartItem, d["cart"])).quantity = 2
                s.add(m.Product(id=package_id, name="Paket", slug=package_id, sku=package_id.upper(),
                    price=Decimal("1500"), product_type="package", description="Paket fixture",
                    main_image="/fixture.png", weight_gram=150, is_active=True))
                await s.flush()
                s.add(m.ProductVariant(id=package_variant, product_id=package_id, sku=package_variant.upper(),
                    stock=5, reserved=0, is_active=True, color="Black", sort_order=0))
                await s.flush()
                s.add(m.CartItem(id=package_cart, user_id=d["alice"], product_id=package_id, variant_id=package_variant, quantity=1))
            expected = {}
            for cart_id, notes in ((d["cart"], "Resep frame"), (package_cart, "Resep paket")):
                upload = await client.post("/api/uploads/prescription", files={"file": ("resep.png", png_bytes(), "image/png")})
                assert upload.status_code == 200, upload.text
                photo_id = upload.json()["id"]
                response = await client.patch(f"/api/cart/{cart_id}/prescription", json={"notes": notes, "attachment_upload_id": photo_id})
                assert response.status_code == 200, response.text
                expected[cart_id] = response.json()["prescription"]
                assert expected[cart_id]["notes"] == notes and expected[cart_id]["attachment_upload_id"] == photo_id
            cart = {row["id"]: row for row in (await client.get("/api/cart")).json()["items"]}
            assert cart[d["cart"]]["quantity"] == 2
            async with read_session() as s:
                sources = {row.id: row.prescription_id for row in (await s.scalars(select(m.CartItem))).all()}
            assert len(set(sources.values())) == 2
            for cart_id, rx in expected.items():
                assert cart[cart_id]["prescription"] == rx
            auth["user"] = d["bob_user"]
            assert (await client.patch(f'/api/cart/{d["cart"]}/prescription', json={"notes": "forbidden"})).status_code == 404
            bob_upload = await client.post("/api/uploads/prescription", files={"file": ("bob.png", png_bytes(), "image/png")})
            assert bob_upload.status_code == 200, bob_upload.text
            auth["user"] = d["user"]
            assert (await client.patch(f"/api/cart/{package_cart}/prescription", json={"attachment_upload_id": bob_upload.json()["id"]})).status_code == 400
            req = d["req"].model_copy(update={"selected_item_ids": [d["cart"], package_cart]})
            order = (await create_checkout(d["alice"], req))["order"]
            items = {row["product_id"]: row for row in order["items"]}
            assert len(items) == 2 and items[d["frame"]]["quantity"] == 2
            for cart_id, product_id in ((d["cart"], d["frame"]), (package_cart, package_id)):
                rx = items[product_id]["prescription"]
                assert rx["notes"] == expected[cart_id]["notes"]
                assert rx["attachment_upload_id"] == expected[cart_id]["attachment_upload_id"]
            # Editing source data cannot change either order's saved prescription.
            async with session_scope() as s:
                (await s.get(m.Prescription, sources[d["cart"]])).notes = "Changed source"
            async with read_session() as s:
                links = list((await s.scalars(select(m.OrderItemPrescription).where(m.OrderItemPrescription.order_id == order["id"]))).all())
                assert len(links) == 2
                assert all(link.prescription_id not in sources.values() for link in links)
                snapshots = list((await s.scalars(select(m.Prescription).where(m.Prescription.id.in_(
                    [link.prescription_id for link in links])))).all())
                assert {rx.notes for rx in snapshots} == {"Resep frame", "Resep paket"}
                assert all(rx.is_order_snapshot for rx in snapshots)
    asyncio.run(run())


def test_add_standalone_prescription_does_not_merge_into_plain_cart_line():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            response = await client.post("/api/cart", json={"product_id": d["frame"], "variant_id": d["vf"],
                "quantity": 2, "prescription": {"notes": "Resep baris baru"}})
            assert response.status_code == 200, response.text
            assert response.json()["id"] != d["cart"]
            cart = {row["id"]: row for row in (await client.get("/api/cart")).json()["items"]}
            assert len(cart) == 2
            assert cart[d["cart"]]["quantity"] == 1 and cart[d["cart"]]["prescription"] is None
            assert cart[response.json()["id"]]["quantity"] == 2
            assert cart[response.json()["id"]]["prescription"]["notes"] == "Resep baris baru"
    asyncio.run(run())


def test_prescription_ownership_and_measurement_validation():
    async def run():
        async with feature_client() as (client, auth, d, _):
            endpoint = f'/api/cart/{d["cart"]}/prescription'
            auth["user"] = d["bob_user"]
            assert (await client.patch(endpoint, json={"od_sph": -1})).status_code == 404
            auth["user"] = d["user"]
            for payload in ({"pd_total": 62, "pd_left": 31, "pd_right": 31}, {"pd_left": 31},
                            {"od_axis": 181}, {"os_axis": 12.5}, {"pd_total": -1}, {"attachment_upload_id": "not-mine"}):
                failed = await client.patch(endpoint, json=payload)
                assert failed.status_code == 400, (payload, failed.text)
            response = await client.patch(endpoint, json={"od_sph": 0, "os_sph": -2.25, "od_cyl": -.5,
                "os_cyl": -.25, "od_axis": 0, "os_axis": 180, "od_add": 1.25, "os_add": 1.5, "pd_total": 63})
            assert response.status_code == 200, response.text
            cart = (await client.get("/api/cart")).json()["items"][0]["prescription"]
            assert cart["od_axis"] == 0 and cart["os_axis"] == 180 and cart["od_add"] == 1.25
            assert cart["pd"] == 63
    asyncio.run(run())


def test_paid_checkout_enables_product_lens_and_transaction_ratings_once():
    async def run():
        async with feature_client() as (client, auth, d, _):
            order = (await create_checkout(d["alice"], d["req"]))["order"]
            eligibility = f'/api/orders/{order["id"]}/review-eligibility'
            assert not (await client.get(eligibility)).json()["eligible"]
            assert (await client.post(f'/api/orders/{order["id"]}/review', json={"rating": 5})).status_code == 409
            assert (await client.post(f'/api/products/{d["frame"]}/reviews', json={"order_id": order["id"], "rating": 5})).status_code == 400
            await confirm_mock_payment(order["order_number"], d["alice"])
            eligible = (await client.get(eligibility)).json()
            assert eligible["eligible"] and len(eligible["products"]) == 2
            for product_id in (d["frame"], d["lens"]):
                response = await client.post(f"/api/products/{product_id}/reviews", json={"order_id": order["id"], "rating": 4, "body": "Sesuai"})
                assert response.status_code == 200, response.text
                review = response.json()["review"]
                assert review["verified_purchase"]
                if product_id == d["lens"]:
                    assert review["order_component_id"] and review["order_item_id"] is None
                assert (await client.post(f"/api/products/{product_id}/reviews", json={"order_id": order["id"], "rating": 4})).status_code == 400
            rated = await client.post(f'/api/orders/{order["id"]}/review', json={"rating": 5})
            assert rated.status_code == 200, rated.text
            assert (await client.post(f'/api/orders/{order["id"]}/review', json={"rating": 4})).status_code == 409
            after = (await client.get(eligibility)).json()
            assert after["order_review"]["rating"] == 5 and all(not p["eligible"] for p in after["products"])
            auth["user"] = d["bob_user"]
            assert (await client.get(eligibility)).status_code == 404
            assert (await client.post(f'/api/orders/{order["id"]}/review', json={"rating": 5})).status_code == 404
            async with read_session() as s:
                assert (await s.get(m.Order, order["id"])).status in {"paid", "processing"}  # No fulfilment completion gate.
                assert (await s.get(m.Product, d["lens"])).rating_avg == Decimal("4.00")
    asyncio.run(run())


async def category_fixture(d):
    async with session_scope() as s:
        s.add(m.Category(id="root_frames", name="Frames", slug="frames"))
        await s.flush()
        s.add(m.Category(id="child_frames", name="Round", slug="round"))
        await s.flush()
        s.add(m.ProductCategory(product_id=d["frame"], category_id="child_frames"))
        s.add(m.ProductCategory(product_id=d["frame"], category_id="root_frames"))
        (await s.get(m.Product, d["frame"])).primary_category_id = "child_frames"
        (await s.get(m.Product, d["frame"])).flash_sale_price = Decimal("1.00")  # Stale legacy cache must be ignored.
        s.add(m.ProductBadge(product_id=d["lens"], badge="flashsale"))


def test_category_flash_sale_materialization_public_price_quota_and_checkout_match():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            await category_fixture(d)
            assert (await client.get("/api/products?badge=flashsale")).json()["products"] == []
            assert (await client.get(f'/api/products/{d["frame"]}')).json()["product"]["flash_sale_price"] is None
            auth["user"] = d["admin_user"]
            now = utcnow()
            payload = {"name": "Category campaign", "start_at": (now - timedelta(hours=1)).isoformat(),
                "end_at": (now + timedelta(hours=1)).isoformat(), "category_rules": [
                    {"category_id": "root_frames", "include_descendants": True, "discount_type": "percent",
                     "discount_value": 20, "quota_per_product": 3}], "items": []}
            created = await client.post("/api/admin/flash-sales", json=payload)
            assert created.status_code == 200, created.text
            flash = created.json()["flash_sale"]
            assert len(flash["category_rules"]) == 1 and len(flash["items"]) == 1
            item = flash["items"][0]
            assert item["source_category_id"] == "root_frames" and item["flash_price"] == 800.08
            listing = (await client.get("/api/products?badge=flashsale")).json()
            assert listing["total"] == 1 and listing["products"][0]["id"] == d["frame"]
            detail = (await client.get(f'/api/products/{d["frame"]}')).json()
            assert detail["product"]["flash_sale_price"] == detail["flash_item"]["flash_price"] == 800.08
            async with read_session() as s:
                cart, _ = await priced_cart(s, d["alice"], [d["cart"]])
                assert float(cart[0].frame_price) == 800.08
            assert (await client.get("/api/flash-sales/active")).json()["flash_sales"][0]["items"][0]["flash_price"] == 800.08
            async with session_scope() as s:
                sale_item = await s.get(m.FlashSaleItem, item["id"])
                sale_item.sold, sale_item.reserved = 1, 2
            assert (await client.get("/api/products?badge=flashsale")).json()["total"] == 0
            assert (await client.get("/api/flash-sales/active")).json()["flash_sales"] == []
            assert (await client.get(f'/api/products/{d["frame"]}')).json()["product"]["flash_sale_price"] is None
            failure = await client.patch(f'/api/admin/flash-sales/{flash["id"]}', json={"items": [{"id": item["id"], "quota": 2}]})
            assert failure.status_code == 409
            updated = await client.patch(f'/api/admin/flash-sales/{flash["id"]}', json={"items": [{"id": item["id"], "quota": 4}]})
            assert updated.status_code == 200, updated.text
            changed = updated.json()["flash_sale"]["items"][0]
            assert changed["id"] == item["id"] and (changed["sold"], changed["reserved"], changed["available_quota"]) == (1, 2, 1)
    asyncio.run(run())


def test_flash_sale_refresh_only_adds_new_matches_and_manual_items_override():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            await category_fixture(d)
            auth["user"] = d["admin_user"]
            now = utcnow()
            payload = {"name": "Category", "start_at": (now - timedelta(hours=1)).isoformat(),
                "end_at": (now + timedelta(hours=1)).isoformat(), "category_rules": [
                    {"category_id": "root_frames", "include_descendants": True, "discount_type": "percent",
                     "discount_value": 10, "quota_per_product": 5}],
                "items": [{"product_id": d["frame"], "flash_price": 750, "quota": 2}]}
            flash = (await client.post("/api/admin/flash-sales", json=payload)).json()["flash_sale"]
            original = flash["items"][0]
            assert original["flash_price"] == 750 and original["source_category_id"] is None
            await client.patch(f'/api/admin/flash-sales/{flash["id"]}', json={"items": [{"id": original["id"], "is_active": False}]})
            async with session_scope() as s:
                s.add(m.Product(id="newframe", name="New frame", slug="new-frame", sku="NEW_FRAME", description="", price=200,
                    product_type="frame", main_image="", primary_category_id="child_frames"))
                await s.flush()
                s.add(m.ProductCategory(product_id="newframe", category_id="child_frames"))
                s.add(m.ProductCategory(product_id="newframe", category_id="root_frames"))
            refreshed = await client.post(f'/api/admin/flash-sales/{flash["id"]}/refresh-categories')
            assert refreshed.status_code == 200, refreshed.text
            assert refreshed.json()["added_products"] == 1
            items = refreshed.json()["flash_sale"]["items"]
            previous = next(i for i in items if i["id"] == original["id"])
            assert previous["flash_price"] == 750 and previous["quota"] == 2 and not previous["is_active"]
            new_item = next(i for i in items if i["product_id"] == "newframe")
            assert new_item["flash_price"] == 180 and new_item["quota"] == 5
            assert (await client.post(f'/api/admin/flash-sales/{flash["id"]}/refresh-categories')).json()["added_products"] == 0
            invalid = await client.post("/api/admin/flash-sales", json={**payload, "category_rules": [
                {"category_id": "root_frames", "discount_type": "percent", "discount_value": 101, "quota_per_product": 5}]})
            assert invalid.status_code == 422
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.FlashSale)) == 1
    asyncio.run(run())


def test_overlapping_flash_sales_use_the_same_best_offer_in_filters_detail_and_checkout():
    async def run():
        async with feature_client(bundle=False) as (client, auth, d, _):
            auth["user"] = d["admin_user"]
            now = utcnow()
            window = {"start_at": (now - timedelta(hours=1)).isoformat(), "end_at": (now + timedelta(hours=1)).isoformat()}
            campaigns = []
            for price in (700, 600):
                result = await client.post("/api/admin/flash-sales", json={"name": f"Sale {price}", **window,
                    "items": [{"product_id": d["frame"], "flash_price": price, "quota": 1}]})
                assert result.status_code == 200, result.text
                campaigns.append(result.json()["flash_sale"])
            public = (await client.get("/api/flash-sales/active")).json()["flash_sales"]
            assert len(public) == 1 and public[0]["id"] == campaigns[1]["id"]
            assert public[0]["items"][0]["flash_sale_price"] == 600
            listing = (await client.get("/api/products?badge=flashsale&min_price=550&max_price=650")).json()
            assert listing["total"] == 1 and listing["products"][0]["flash_sale_price"] == 600
            assert (await client.get("/api/products?badge=flashsale&min_price=650")).json()["total"] == 0
            detail = (await client.get(f'/api/products/{d["frame"]}')).json()
            assert detail["flash_item"]["id"] == campaigns[1]["items"][0]["id"]
            async with read_session() as s:
                cart, _ = await priced_cart(s, d["alice"], [d["cart"]])
                assert cart[0].frame_price == Decimal("600.00")
            await client.patch(f'/api/admin/flash-sales/{campaigns[1]["id"]}', json={"is_active": False})
            assert (await client.get(f'/api/products/{d["frame"]}')).json()["product"]["flash_sale_price"] == 700
    asyncio.run(run())


def test_recommended_bundle_uses_selected_frame_variant_flash_price_and_exact_lens_sku():
    async def run():
        async with feature_client(bundle=False) as (client, _, d, _):
            chosen_frame_variant = d["prefix"] + "_frame_large"
            other_lens_variant = d["prefix"] + "_lens_other"
            now = utcnow()
            async with session_scope() as s:
                (await s.get(m.ProductVariant, d["vf"])).price_override = Decimal("1200.00")
                (await s.get(m.ProductVariant, d["vl"])).price_override = Decimal("70.25")
                s.add(m.ProductVariant(id=chosen_frame_variant, product_id=d["frame"], sku=chosen_frame_variant,
                    stock=3, reserved=0, sort_order=1, price_override=Decimal("1500.00"), is_active=True))
                s.add(m.ProductVariant(id=other_lens_variant, product_id=d["lens"], sku=other_lens_variant,
                    stock=10, reserved=0, sort_order=2, price_override=Decimal("1.00"), is_active=True))
            endpoint = f'/api/lens/recommended-bundle/{d["frame"]}'
            default = await client.get(endpoint)
            assert default.status_code == 200, default.text
            assert default.json()["frame"]["variant_id"] == d["vf"]
            chosen = (await client.get(endpoint, params={"variant_id": chosen_frame_variant})).json()
            pick = chosen["picks"][0]
            assert pick["frame_price"] == 1500 and pick["lens_price"] == 70.25 and pick["bundle_total"] == 1620.30
            assert pick["lens_variant_id"] == d["vl"] and pick["available_stock"] == 3 and pick["available"]
            assert (await client.get(endpoint, params={"variant_id": d["vl"]})).status_code == 404
            async with session_scope() as s:
                s.add(m.FlashSale(id="bundle_sale", name="Bundle flash", start_at=now - timedelta(hours=1),
                    end_at=now + timedelta(hours=1), is_active=True))
                await s.flush()
                s.add(m.FlashSaleItem(id="bundle_frame_offer", flash_sale_id="bundle_sale", product_id=d["frame"],
                    flash_price=Decimal("650.00"), quota=2, sold=0, reserved=0))
                s.add(m.FlashSaleItem(id="bundle_lens_offer", flash_sale_id="bundle_sale", product_id=d["lens"],
                    flash_price=Decimal("1.00"), quota=2, sold=0, reserved=0))
            result = (await client.get(endpoint, params={"variant_id": chosen_frame_variant})).json()
            pick = result["picks"][0]
            assert pick["frame_price"] == 650 and pick["lens_price"] == 70.25 and pick["bundle_total"] == 770.30
            assert result["frame"]["variant_id"] == pick["frame_variant_id"] == chosen_frame_variant
            cart = await client.post("/api/cart", json={"product_id": d["frame"], "variant_id": pick["frame_variant_id"],
                "lens_product_id": pick["lens_product_id"], "lens_variant_id": pick["lens_variant_id"],
                "lens_index_id": pick["lens_index_id"], "quantity": 1})
            assert cart.status_code == 200, cart.text
            async with read_session() as s:
                priced, _ = await priced_cart(s, d["alice"], [cart.json()["id"]])
                assert priced[0].unit_price == Decimal(str(pick["bundle_total"]))
                assert priced[0].frame_price == Decimal("650.00")
                assert priced[0].lens_variant.id == pick["lens_variant_id"]
            async with session_scope() as s:
                (await s.get(m.ProductVariant, chosen_frame_variant)).reserved = 3
            unavailable = (await client.get(endpoint, params={"variant_id": chosen_frame_variant})).json()["picks"][0]
            assert unavailable["available_stock"] == 0 and not unavailable["available"]
    asyncio.run(run())


def test_new_arrival_expiry_dynamic_frame_category_and_fifteen_item_pages():
    async def run():
        async with feature_client() as (client, auth, d, _):
            now = utcnow()
            async with session_scope() as s:
                (await s.get(m.Product, d["frame"])).is_new_arrival = True
                (await s.get(m.Product, d["lens"])).is_new_arrival = True
                s.add(m.ProductBadge(product_id=d["frame"], badge="new"))
                for i in range(15):
                    s.add(m.Product(id=f"page_{i}", slug=f"page-{i}", sku=f"PAGE_{i}", name=f"Frame {i}",
                        description="", main_image="", price=10, is_new_arrival=i == 0,
                        new_arrival_until=now - timedelta(minutes=1) if i == 0 else None))
            page1 = (await client.get("/api/products")).json()
            page2 = (await client.get("/api/products?page=2")).json()
            assert page1["limit"] == 15 and len(page1["products"]) == 15 and len(page2["products"]) == 2
            assert set(p["id"] for p in page1["products"]).isdisjoint(p["id"] for p in page2["products"])
            assert (await client.get("/api/products?new_arrival=true")).json()["total"] == 2
            frames = (await client.get("/api/products?category_slug=frame-new-arrival")).json()
            assert [p["id"] for p in frames["products"]] == [d["frame"]]
            auth["user"] = d["admin_user"]
            changed = await client.put(f'/api/admin/products/{d["frame"]}', json={"is_new_arrival": False})
            assert changed.status_code == 200, changed.text
            assert (await client.get("/api/products?category_slug=frame-new-arrival")).json()["total"] == 0
            frame = (await client.get(f'/api/products/{d["frame"]}')).json()["product"]
            assert not frame["is_new_arrival"] and "new" not in frame["badges"]
    asyncio.run(run())


def test_publish_unpublish_and_banner_sort_destination_are_persisted():
    async def run():
        async with feature_client() as (client, auth, d, _):
            auth["user"] = d["admin_user"]
            article = (await client.post("/api/admin/articles", json={"title": "Guide", "slug": "guide", "content": "<p>Guide</p>"})).json()["article"]
            knowledge = (await client.post("/api/admin/knowledge", json={"title": "Frame", "slug": "frame-guide", "content": "<p>Frame</p>"})).json()["knowledge"]
            for prefix, key, slug, entity in (("articles", "article", "guide", article), ("knowledge", "knowledge", "frame-guide", knowledge)):
                assert (await client.get(f"/api/{prefix}/{slug}")).status_code == 200
                off = await client.put(f'/api/admin/{prefix}/{entity["id"]}', json={"status": "unpublished"})
                assert off.status_code == 200, off.text
                assert (await client.get(f"/api/{prefix}/{slug}")).status_code == 404
                on = await client.put(f'/api/admin/{prefix}/{entity["id"]}', json={"status": "published"})
                assert on.status_code == 200, on.text
                assert (await client.get(f"/api/{prefix}/{slug}")).json()[key]["status"] == "published"
            for title, order, url in (("Later", 8, "/shop-now"), ("First", 1, "https://example.com/event")):
                response = await client.post("/api/admin/banners-v2", json={"title": title, "image_desktop": "/banner.png", "sort_order": order, "link_url": url})
                assert response.status_code == 200, response.text
            banners = (await client.get("/api/homepage")).json()["banners"]
            assert [b["title"] for b in banners] == ["First", "Later"]
            assert banners[0]["link_url"] == "https://example.com/event"
            for url in ("javascript:alert(1)", "//bad.example", "http:bad.example", "https://user:password@example.com"):
                bad = await client.post("/api/admin/banners-v2", json={"title": "Bad", "image_desktop": "/banner.png", "link_url": url})
                assert bad.status_code == 422, bad.text
    asyncio.run(run())


def test_feature_content_dry_run_idempotency_and_editorial_changes_preserved():
    async def run():
        async with feature_client() as (_, _, d, _):
            async with session_scope() as s:
                s.add(m.ProductBadge(product_id=d["frame"], badge="new"))
            async with session_scope() as s:
                report = await ensure_feature_content(s, apply=False)
                assert report["knowledge_created"] == 11 and report["legacy_new_badges_backfilled"] == 1
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.ProductKnowledge)) == 0
                assert await s.get(m.Setting, FEATURE_SEED_KEY) is None
            async with session_scope() as s:
                report = await ensure_feature_content(s)
                assert report["knowledge_created"] == len(KNOWLEDGE_ENTRIES)
            async with session_scope() as s:
                assert (await s.get(m.Product, d["frame"])).is_new_arrival
                (await s.get(m.Product, d["frame"])).is_new_arrival = False
                knowledge = await s.scalar(select(m.ProductKnowledge).where(m.ProductKnowledge.slug == "lensa-minus"))
                knowledge.title = "Edited by shop owner"
                knowledge.status = "unpublished"
            async with session_scope() as s:
                again = await ensure_feature_content(s)
                assert again["knowledge_created"] == 0 and not again["new_arrival_category_created"]
                assert again["legacy_new_badges_backfilled"] == 0 and again["backfill_already_applied"]
            async with read_session() as s:
                assert not (await s.get(m.Product, d["frame"])).is_new_arrival
                knowledge = await s.scalar(select(m.ProductKnowledge).where(m.ProductKnowledge.slug == "lensa-minus"))
                assert knowledge.title == "Edited by shop owner" and knowledge.status == "unpublished"
                assert await s.scalar(select(func.count()).select_from(m.ProductKnowledge)) == 11
    asyncio.run(run())
