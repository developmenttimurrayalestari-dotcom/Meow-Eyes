"""Disposable browser fixture for account-integrated Meowsurement.

Only used by meowsurement-customer-browser.cjs. It runs real application routes
against a temporary SQLite database and serves a copy of the production build.
It does not connect to, migrate, or seed a deployment database.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[2]
TEMP = Path(tempfile.mkdtemp(prefix="meow-customer-browser-"))
STATIC = TEMP / "build"
BUILD = Path(os.environ.get("MEOW_QA_BUILD_DIR", PROJECT / "frontend/build"))
if not (BUILD / "index.html").is_file():
    raise RuntimeError("Build the frontend before running browser acceptance.")
shutil.copytree(BUILD, STATIC)
sys.path.insert(0, str(PROJECT / "backend"))
os.environ.update(
    APP_ENV="test", ENABLE_MOCK_PAYMENTS="1", PAYMENT_PROVIDER="mock",
    SHIPPING_PROVIDER="mock", SCHEDULER_ENABLED="0", PRIVATE_UPLOAD_ROOT=str(TEMP / "private"),
    MEOWSUREMENT_PRIVATE_ROOT=str(TEMP / "private/meowsurement"),
)

from fastapi import HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy import event, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from auth import hash_secret
from database import configure_session_factory
from mysql.base import Base
from mysql.demo_seed import seed_with_factory
from mysql import models as m
import server

fixture = {}
SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400"><rect width="640" height="400" fill="#f4f3ee"/><g fill="#dce8e8" stroke="#18283b" stroke-width="12"><rect x="80" y="130" width="190" height="130" rx="34"/><rect x="370" y="130" width="190" height="130" rx="34"/><path d="M270 170Q320 145 370 170" fill="none"/></g></svg>'


@asynccontextmanager
async def lifespan(_app):
    engine = create_async_engine(
        "sqlite+aiosqlite:///" + str(TEMP / "database.sqlite"),
        connect_args={"timeout": 30},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def pragmas(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=30000")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    configure_session_factory(factory)
    try:
        password = hash_secret(os.environ["MEOW_QA_PASSWORD"])
        await seed_with_factory(
            factory, confirmed=True, environment="test",
            password_hashes={role: password for role in ("super_admin", "customer", "staff")},
            pin_hash=hash_secret("654321"),
        )
        async with factory.begin() as session:
            customer = await session.scalar(select(m.User).where(m.User.role == "customer"))
            admin = await session.scalar(select(m.User).where(m.User.role == "super_admin"))
            staff = await session.scalar(select(m.User).where(m.User.role == "staff"))
            customer.pin_hash = None
            customer.name = "Customer Sintetis QA"
            for permission in ("meowsurement.review", "product.view", "product.update"):
                session.add(m.UserPermission(user_id=staff.user_id, permission=permission))
            frames = (await session.scalars(
                select(m.Product).where(m.Product.product_type == "frame").order_by(m.Product.id)
            )).all()
            frame = frames[0]
            variants = (await session.scalars(
                select(m.ProductVariant).where(m.ProductVariant.product_id == frame.id)
                .order_by(m.ProductVariant.sort_order, m.ProductVariant.id)
            )).all()
            if len(variants) < 2:
                extra = m.ProductVariant(
                    id="qa-frame-large", product_id=frame.id, sku="QA-LARGE",
                    color="QA Large", size="L", stock=20, reserved=0, sort_order=100,
                )
                session.add(extra)
                variants.append(extra)
            for model, field in (
                (m.Product, "main_image"), (m.ProductImage, "image_url"),
                (m.Article, "thumbnail"), (m.ProductKnowledge, "image"),
                (m.Banner, "image_desktop"),
            ):
                await session.execute(update(model).values(**{field: "/qa/product.svg"}))
            await session.flush()
            fixture.update({
                "frame_id": frame.id, "frame_slug": frame.slug, "frame_name": frame.name,
                "variants": [
                    {"id": row.id, "sku": row.sku, "color": row.color, "size": row.size}
                    for row in variants
                ],
                "customer_id": customer.user_id, "customer_email": customer.email,
                "admin_email": admin.email, "staff_email": staff.email,
                "customer_has_pin": False,
            })
        yield
    finally:
        configure_session_factory(None)
        await engine.dispose()
        shutil.rmtree(TEMP, ignore_errors=True)


server.app.router.lifespan_context = lifespan


@server.app.get("/qa/ready", include_in_schema=False)
async def ready():
    return fixture


@server.app.get("/qa/product.svg", include_in_schema=False)
async def product_image():
    return Response(SVG, media_type="image/svg+xml")


@server.app.get("/{asset:path}", include_in_schema=False)
async def spa(asset: str):
    if asset.startswith("api/"):
        raise HTTPException(404, "API route not found")
    target = (STATIC / asset).resolve()
    if not target.is_relative_to(STATIC.resolve()):
        raise HTTPException(404)
    return FileResponse(target if target.is_file() else STATIC / "index.html", headers={"Cache-Control": "no-store"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(server.app, host="127.0.0.1", port=int(os.environ.get("MEOW_QA_PORT", "8829")), log_level="warning")
