"""Catalog/CMS route contracts and transactional writes on disposable SQLite.

These tests exercise the actual SQLAlchemy route implementations. MySQL-specific
collations, row locks and triggers still require the separately gated live suite.
"""
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import zipfile

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openpyxl import Workbook, load_workbook
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import database
from auth import current_user, current_user_optional
from models import User
from mysql import models as m
from mysql.base import Base, utcnow
import routes_admin as admin_routes
import routes_admin_content as cms
import routes_catalog as catalog
import routes_content as content
import routes_export as exports
import routes_uploads as uploads


@asynccontextmanager
async def sql_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    @event.listens_for(engine.sync_engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    database.configure_session_factory(factory)
    admin = User(user_id="admin", email="admin@example.com", name="Admin", role="super_admin")
    auth = {"user": admin}
    app = FastAPI()
    app.dependency_overrides[current_user] = lambda: auth["user"]
    app.dependency_overrides[current_user_optional] = lambda: auth["user"]
    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError):
        return JSONResponse(status_code=409, content={"detail": "Data terkait/duplikat"})
    for module in (catalog, content, admin_routes, cms, exports, uploads):
        app.include_router(module.router, prefix="/api")
    app.add_api_route("/api/uploads-files/{file_path:path}", uploads.public_upload_file,
                      methods=["GET", "HEAD"], include_in_schema=False)
    try:
        async with factory.begin() as s:
            s.add(m.User(user_id="admin", email="admin@example.com", name="Admin", role="super_admin"))
            s.add(m.User(user_id="customer", email="customer@example.com", name="Customer"))
            s.add(m.Category(id="cat", name="Frames", slug="frames", level=0))
            await s.flush()
            s.add(m.Category(id="child", parent_id="cat", name="Round", slug="round", level=1))
            s.add(m.Brand(id="brand", name="Leinz", slug="leinz"))
            await s.flush()
            s.add(m.Product(id="product", name="Frame 100%", slug="frame", sku="FRAME", description="Description",
                            price=Decimal("100.10"), main_image="/frame.png", primary_category_id="child", brand_id="brand"))
            await s.flush()
            s.add_all([m.ProductCategory(product_id="product", category_id="child"),
                       m.ProductVariant(id="variant", product_id="product", sku="VARIANT", stock=10, reserved=2),
                       m.ProductImage(product_id="product", sort_order=0, image_url="/frame.png"),
                       m.ProductBadge(product_id="product", badge="new")])
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            yield client, factory, auth
    finally:
        database.configure_session_factory(None)
        await engine.dispose()


def test_catalog_filters_breadcrumbs_and_stable_pagination():
    async def run():
        async with sql_client() as (client, factory, _):
            async with factory.begin() as s:
                for i in range(5):
                    s.add(m.Product(id=f"p{i}", name=f"Other {i}", slug=f"other-{i}", sku=f"P{i}",
                                    description="", main_image="", price=Decimal("100.10")))
            response = await client.get("/api/products", params={"q": "%"})
            assert response.status_code == 200, response.text
            assert [p["id"] for p in response.json()["products"]] == ["product"]
            filtered = (await client.get("/api/products", params={"category_slug": "frames"})).json()
            assert filtered["total"] == 1
            missing = (await client.get("/api/products", params={"category_slug": "unknown"})).json()
            assert missing["total"] == 0
            p1 = (await client.get("/api/products", params={"page": 1, "limit": 3, "sort": "price_asc"})).json()
            p2 = (await client.get("/api/products", params={"page": 2, "limit": 3, "sort": "price_asc"})).json()
            assert len(p1["products"]) == len(p2["products"]) == 3
            assert set(p["id"] for p in p1["products"]).isdisjoint(p["id"] for p in p2["products"])
            assert (await client.get("/api/products", params={"limit": 0})).status_code == 422
            detail = (await client.get("/api/products/frame")).json()
            assert [c["id"] for c in detail["breadcrumb"]] == ["cat", "child"]
            assert detail["brand"]["id"] == "brand"
            assert detail["product"]["variants"][0]["reserved"] == 2
            assert detail["product"]["price"] == 100.1
    asyncio.run(run())


def test_product_updates_keep_variant_identity_and_reserved_stock():
    async def run():
        async with sql_client() as (client, factory, _):
            response = await client.put("/api/admin/products/product", json={"name": "Updated",
                "discount_price": None, "gallery": ["/a.png", "/b.png"],
                "variants": [{"sku": "VARIANT", "stock": 8, "color": "Black", "price_override": 0}]})
            assert response.status_code == 200, response.text
            item = (await client.get("/api/admin/products/product")).json()["product"]
            assert item["gallery"] == ["/a.png", "/b.png"]
            assert item["variants"][0]["id"] == "variant"
            assert item["variants"][0]["reserved"] == 2
            assert item["variants"][0]["price_override"] == 0
            rejected = await client.put("/api/admin/products/product", json={"name": "Must rollback",
                "variants": [{"sku": "VARIANT", "stock": 1}]})
            assert rejected.status_code == 409
            async with factory() as s:
                assert (await s.get(m.Product, "product")).name == "Updated"
                assert (await s.get(m.ProductVariant, "variant")).stock == 8
                assert await s.scalar(select(func.count()).select_from(m.StockMovement)) == 1
            omitted = await client.put("/api/admin/products/product", json={"variants": []})
            assert omitted.status_code == 200
            detail = (await client.get("/api/products/frame")).json()["product"]
            assert detail["variants"] == []
            async with factory() as s:
                variant = await s.get(m.ProductVariant, "variant")
                assert variant.reserved == 2 and not variant.is_active
    asyncio.run(run())


def test_category_cycles_and_referenced_deletes_are_rejected():
    async def run():
        async with sql_client() as (client, factory, _):
            response = await client.put("/api/admin/categories/cat", json={"name": "Frames", "parent_id": "child"})
            assert response.status_code == 422, response.text
            async with factory() as s:
                assert (await s.get(m.Category, "cat")).parent_id is None
                assert (await s.get(m.Category, "child")).level == 1
            assert (await client.delete("/api/admin/categories/child")).status_code == 409
            assert (await client.delete("/api/admin/brands/brand")).status_code == 409
            created = await client.post("/api/admin/categories", json={"name": "New", "parent_id": "child"})
            assert created.status_code == 200, created.text
            assert created.json()["category"]["level"] == 2
    asyncio.run(run())


def test_article_and_knowledge_relational_children_and_publication():
    async def run():
        async with sql_client() as (client, factory, _):
            created = await client.post("/api/admin/articles", json={"title": "Lens care", "content": "Body", "status": "draft",
                "tags": ["care", "lens"], "author_id": "customer", "view_count": 99})
            assert created.status_code == 200, created.text
            article = created.json()["article"]
            assert article["author_id"] == "admin" and article["view_count"] == 0
            assert (await client.get("/api/articles/" + article["slug"])).status_code == 404
            updated = await client.put("/api/admin/articles/" + article["id"], json={"status": "published", "tags": ["optical", "care"]})
            assert updated.status_code == 200, updated.text
            public = (await client.get("/api/articles/" + article["slug"])).json()["article"]
            assert public["tags"] == ["optical", "care"] and public["published_at"]
            assert public["view_count"] == 1
            kn = await client.post("/api/admin/knowledge", json={"title": "Shape", "content": "Body",
                "pros": ["one", "two"], "cons": ["three"], "related_product_ids": ["product"]})
            assert kn.status_code == 200, kn.text
            knowledge = kn.json()["knowledge"]
            detail = (await client.get("/api/knowledge/" + knowledge["slug"])).json()
            assert detail["knowledge"]["pros"] == ["one", "two"]
            assert detail["related_products"][0]["id"] == "product"
            assert (await client.put("/api/admin/knowledge/" + knowledge["id"], json={"status": "unpublished", "is_published": False, "pros": []})).status_code == 200
            assert (await client.get("/api/knowledge/" + knowledge["slug"])).status_code == 404
            async with factory() as s:
                assert await s.scalar(select(func.count()).select_from(m.ArticleTag)) == 2
                assert await s.scalar(select(func.count()).select_from(m.ProductKnowledgeBullet)) == 1
    asyncio.run(run())


def test_banners_v1_v2_share_rows_and_enforce_window_and_link():
    async def run():
        async with sql_client() as (client, _, __):
            v1 = await client.post("/api/admin/banners", json={"title": "Old", "image": "/old.png", "link": "/shop-now", "sort_order": 10})
            assert v1.status_code == 200, v1.text
            v2 = await client.post("/api/admin/banners-v2", json={"title": "New", "image_desktop": "/new.png",
                "link_type": "product", "reference_id": "product", "link_url": "/product/frame", "sort_order": 1})
            assert v2.status_code == 200, v2.text
            assert v2.json()["banner"]["reference_id"] == "product"
            bad = await client.post("/api/admin/banners-v2", json={"title": "Bad", "image_desktop": "/a.png", "link_url": "javascript:alert(1)"})
            assert bad.status_code == 422
            future = await client.post("/api/admin/banners-v2", json={"title": "Future", "image_desktop": "/a.png",
                "start_at": (utcnow() + timedelta(days=1)).isoformat()})
            assert future.status_code == 200, future.text
            public = (await client.get("/api/banners")).json()["banners"]
            assert [row["title"] for row in public] == ["New", "Old"]
            assert public[1]["image_desktop"] == public[1]["image"] == "/old.png"
            assert len((await client.get("/api/admin/banners")).json()["banners"]) == 3
    asyncio.run(run())


def _workbook(records):
    wb = Workbook()
    ws = wb.active
    ws.append(cms.IMPORT_TEMPLATE_HEADERS)
    for record in records:
        ws.append([record.get(key) for key in cms.IMPORT_TEMPLATE_HEADERS])
    buffer = BytesIO()
    wb.save(buffer)
    wb.close()
    return buffer.getvalue()


def test_product_import_atomic_validation_and_stable_variant_ids():
    async def run():
        async with sql_client() as (client, factory, _):
            record = {"product_name": "Imported frame", "product_type": "frame", "product_slug": "frame",
                "main_category": "Round", "brand": "Leinz", "variant_sku": "VARIANT", "variant_price": 200,
                "variant_stock": 9, "is_active": 0}
            invalid = _workbook([record, {**record, "product_slug": "another", "variant_sku": "OTHER", "variant_stock": -2}])
            preview = await client.post("/api/admin/products/import/preview", files={"file": ("data.xlsx", invalid)})
            assert preview.status_code == 200, preview.text
            assert preview.json()["valid"] == 1
            response = await client.post("/api/admin/products/import/commit", files={"file": ("data.xlsx", invalid)})
            assert response.status_code == 422
            async with factory() as s:
                assert (await s.get(m.Product, "product")).name == "Frame 100%"
            data = _workbook([record])
            for _ in range(2):
                response = await client.post("/api/admin/products/import/commit", files={"file": ("data.xlsx", data)})
                assert response.status_code == 200, response.text
                assert response.json()["updated"] == 1
            async with factory() as s:
                product = await s.get(m.Product, "product")
                assert not product.is_active
                variant = await s.get(m.ProductVariant, "variant")
                assert variant.sku == "VARIANT" and variant.stock == 9 and variant.reserved == 2
                assert await s.scalar(select(func.count()).select_from(m.ProductVariant)) == 1
                assert await s.scalar(select(func.count()).select_from(m.StockMovement)) == 1
    asyncio.run(run())


def test_contact_staff_permissions_and_safe_export():
    async def run():
        async with sql_client() as (client, factory, auth):
            response = await client.put("/api/admin/contact-setting", json={"whatsapp": "62812345678", "store_name": "Meow"})
            assert response.status_code == 200, response.text
            assert (await client.get("/api/contact/info")).json()["contact"]["whatsapp"] == "62812345678"
            created = await client.post("/api/admin/staff", json={"name": "=HYPERLINK(\"https://invalid\")", "email": "staff@example.com",
                "password": "SamplePass123", "permissions": ["article.view"]})
            assert created.status_code == 200, created.text
            uid = created.json()["user_id"]
            async with factory() as s:
                assert (await s.get(m.User, uid)).pin_hash is None
                assert await s.scalar(select(m.UserPermission.permission).where(m.UserPermission.user_id == uid)) == "article.view"
            staff = (await client.get("/api/admin/staff")).json()["staff"]
            assert all("password_hash" not in user and "pin_hash" not in user for user in staff)
            export = await client.get("/api/admin/export/users")
            assert export.status_code == 200
            wb = load_workbook(BytesIO(export.content))
            formula_name = next(cell for row in wb.active for cell in row if isinstance(cell.value, str) and "HYPERLINK" in cell.value)
            assert formula_name.data_type == "s" and formula_name.value.startswith("'")
            wb.close()
            auth["user"] = User(user_id=uid, email="staff@example.com", name="Staff", role="staff", permissions=["article.view"])
            assert (await client.get("/api/admin/articles")).status_code == 200
            assert (await client.get("/api/admin/products")).status_code == 403
            assert (await client.post("/api/admin/articles", json={"title": "Denied", "content": ""})).status_code == 403
    asyncio.run(run())


def test_upload_rollbacks_private_visibility_and_svg_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "UPLOAD_ROOT", tmp_path)
    async def run():
        async with sql_client() as (client, factory, _):
            safe = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10" fill="#fff"/></svg>'
            bad = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
            assert (await client.post("/api/uploads", files={"file": ("bad.svg", bad, "image/svg+xml")})).status_code == 415
            response = await client.post("/api/uploads", files={"file": ("safe.svg", safe, "image/svg+xml")})
            assert response.status_code == 200, response.text
            data = response.json()
            path = tmp_path / data["subdir"] / data["disk_name"]
            assert path.exists()
            served = await client.get(data["url"])
            assert served.status_code == 200 and b"rect" in served.content
            assert served.headers["x-content-type-options"] == "nosniff"
            assert (await client.head(data["url"])).status_code == 200
            private_path = tmp_path / "private.png"
            private_path.write_bytes(b"private fixture bytes")
            async with factory.begin() as s:
                s.add(m.Upload(id="private", filename="private.png", mime="image/png", size=1, visibility="private", uploaded_by="customer",
                               storage_key="private.png"))
                s.add(m.Prescription(id="rx", user_id="customer", attachment_upload_id=data["id"]))
            assert (await client.get("/api/uploads-files/private.png")).status_code == 404
            assert (await client.head("/api/uploads-files/private.png")).status_code == 404
            unregistered = tmp_path / "unregistered.png"
            unregistered.write_bytes(b"not registered")
            assert (await client.get("/api/uploads-files/unregistered.png")).status_code == 404
            # Neither path normalization nor a registered symlink can expose a
            # private/unregistered target.
            symlink = tmp_path / "alias.svg"
            symlink.symlink_to(path)
            async with factory.begin() as s:
                s.add(m.Upload(id="alias", filename="alias.svg", mime="image/svg+xml", size=1, visibility="public", storage_key="alias.svg"))
            assert (await client.get("/api/uploads-files/alias.svg")).status_code == 404
            assert (await client.get("/api/uploads-files/%2e%2e/private.png")).status_code == 404
            assert (await client.get("/api/uploads-files/a%5c..%5cprivate.png")).status_code == 404
            listing = (await client.get("/api/uploads")).json()
            assert listing["total"] == 2 and {row["id"] for row in listing["items"]} == {data["id"], "alias"}
            rejected = await client.delete("/api/uploads/" + data["id"])
            assert rejected.status_code == 409 and path.exists()
            assert (await client.delete("/api/uploads/private")).status_code == 404
            # If metadata validation fails, the newly written disk file is removed.
            response = await client.post("/api/uploads", files={"file": ("x" * 260 + ".svg", safe, "image/svg+xml")})
            assert response.status_code == 422
            assert len([p for p in tmp_path.rglob("*.svg") if not p.is_symlink()]) == 1
    asyncio.run(run())


def test_dashboard_promotion_and_export_routes_execute_relational_queries():
    async def run():
        async with sql_client() as (client, factory, _):
            now = utcnow()
            window = {"start_at": (now - timedelta(days=1)).isoformat(), "end_at": (now + timedelta(days=1)).isoformat()}
            voucher = await client.post("/api/admin/vouchers", json={"code": "SAVE", "name": "Save", **window})
            assert voucher.status_code == 200, voucher.text
            reward = await client.post("/api/admin/roulette/rewards", json={"label": "Points", "type": "points", "value": 1})
            assert reward.status_code == 200, reward.text
            flash = await client.post("/api/admin/flash-sales", json={"name": "Flash", **window,
                "items": [{"product_id": "product", "flash_price": 80, "quota": 5}]})
            assert flash.status_code == 200, flash.text
            flash_public = await client.get("/api/flash-sales/active")
            assert flash_public.status_code == 200, flash_public.text
            card = flash_public.json()["flash_sales"][0]["items"][0]
            assert card["flash_price"] == card["flash_sale_price"] == 80
            lens = await client.post("/api/admin/products", json={"name": "Lens", "description": "Lens", "main_image": "/lens.png",
                "price": 20, "discount_price": 0, "product_type": "lens", "variants": [{"sku": "LENS-V", "stock": 2}]})
            assert lens.status_code == 200, lens.text
            index = await client.post("/api/admin/lens/indexes", json={"name": "Normal", "index_value": "1.56", "additional_price": 10})
            assert index.status_code == 200, index.text
            bundle = await client.get("/api/lens/recommended-bundle/product")
            assert bundle.status_code == 200, bundle.text
            assert bundle.json()["picks"][0]["lens_price"] == 0
            # The active frame Flash Sale is authoritative for a one-frame
            # bundle too: frame 80 + the free lens + index surcharge 10.
            assert bundle.json()["picks"][0]["frame_price"] == 80
            assert bundle.json()["picks"][0]["bundle_total"] == 90
            faq = await client.post("/api/admin/faqs", json={"question": "How?", "answer": "Here"})
            assert faq.status_code == 200, faq.text
            page = await client.post("/api/admin/pages", json={"title": "About", "content": "Body"})
            assert page.status_code == 200, page.text
            page_id = page.json()["page"]["id"]
            assert (await client.put("/api/admin/pages/" + page_id, json={"content": "Updated", "version": 999})).status_code == 200
            assert (await client.get("/api/pages/about")).json()["page"]["version"] == 2
            contact = await client.post("/api/contact/send", json={"name": "Customer", "email": "customer@example.com", "message": "Hello", "status": "replied"})
            assert contact.status_code == 200, contact.text
            async with factory.begin() as s:
                s.add(m.Order(id="order", order_number="ORDER", user_id="customer", subtotal=Decimal("100.10"),
                              shipping_courier="test", shipping_service="REG", shipping_cost=0, total=Decimal("100.10"),
                              payment_status="paid", status="paid"))
                await s.flush()
                s.add(m.OrderItem(id="line", order_id="order", product_id="product", variant_id="variant",
                                 product_name="Historic frame", quantity=1, unit_price=Decimal("100.10"), subtotal=Decimal("100.10"), sort_order=0))
                s.add(m.ProductReview(id="review", product_id="product", user_id="customer", user_name="Customer",
                                      rating=4, body="Legacy review", status="pending"))
            moderated = await client.post("/api/admin/reviews/review/moderate", json={"action": "approve"})
            assert moderated.status_code == 200, moderated.text
            detail = (await client.get("/api/products/frame")).json()
            assert detail["product"]["rating_count"] == 1 and detail["product"]["rating_avg"] == 4
            assert detail["reviews"][0]["is_approved"] is True
            assert (await client.post("/api/admin/reviews/review/moderate", json={"action": "hide"})).status_code == 200
            detail = (await client.get("/api/products/frame")).json()
            assert detail["product"]["rating_count"] == 0 and detail["reviews"] == []
            paths = ["/brands", "/categories", "/categories/tree", "/categories/frames", "/homepage",
                     "/products/search-suggest?q=Frame", "/articles", "/articles/categories", "/knowledge", "/faqs",
                     "/lens/indexes", "/lens/options-for-frame/product", "/admin/products", "/admin/categories", "/admin/brands",
                     "/admin/orders", "/admin/inventory", "/admin/vouchers", "/admin/flash-sales", "/admin/roulette/rewards",
                     "/admin/users", "/admin/newsletter/subscribers", "/admin/newsletter/campaigns", "/admin/banners",
                     "/admin/article-categories", "/admin/articles", "/admin/knowledge", "/admin/lens/indexes", "/admin/faqs",
                     "/admin/pages", "/admin/contact-setting", "/admin/contact-messages", "/admin/banners-v2", "/admin/reviews",
                     "/admin/reviews/analytics", "/admin/staff", "/admin/permissions"]
            paths += ["/admin/dashboard/" + suffix for suffix in ("summary", "sales-chart", "order-status-chart", "top-products",
                     "payment-chart", "shipment-chart", "game-chart", "roulette-chart")]
            for path in paths:
                response = await client.get("/api" + path)
                assert response.status_code == 200, (path, response.status_code, response.text)
            summary = (await client.get("/api/admin/dashboard/summary")).json()
            assert summary["sales_today"] == 100.1 and summary["orders_today"] == 1
            for name in ("sales", "inventory", "flash-sales", "roulette", "games", "newsletter", "users", "points"):
                response = await client.get("/api/admin/export/" + name)
                assert response.status_code == 200, response.text
                assert zipfile.is_zipfile(BytesIO(response.content))
            assert (await client.delete("/api/admin/flash-sales/" + flash.json()["flash_sale"]["id"])).status_code == 200
            assert (await client.get("/api/flash-sales/active")).json()["flash_sales"] == []
            async with factory() as s:
                assert (await s.scalar(select(m.ContactMessage))).status == "new"
    asyncio.run(run())
