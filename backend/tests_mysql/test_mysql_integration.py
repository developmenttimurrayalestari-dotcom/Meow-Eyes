"""Opt-in server acceptance check; never runs against an inferred destination.

This test leaves its schema and uniquely named commerce fixtures for inspection.
It never drops a database or resets an existing schema. See STEP_1.md before explicitly enabling it.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from mysql.base import Base
from mysql import models  # noqa: F401
from mysql.config import MySQLSettings
from mysql.database import Database, supported_mysql_version
from mysql.check_integrity import load_revision

pytestmark = [
    pytest.mark.mysql_integration,
    pytest.mark.skipif(os.environ.get("MYSQL_INTEGRATION_TESTS") != "1",
                       reason="Requires an explicitly configured empty test_meow_* MySQL 5.7.24-log database"),
]


def test_initial_migration_and_server_integrity(monkeypatch):
    required = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD")
    if not all(os.environ.get(name) for name in required):
        pytest.fail("Set every MYSQL_HOST/PORT/DATABASE/USER/PASSWORD explicitly for this test")
    if os.environ.get("APP_ENV") != "test":
        pytest.fail("This integration test requires APP_ENV=test")
    settings = MySQLSettings.from_env(env_file=None)
    if not settings.database.startswith("test_meow_"):
        pytest.fail("Integration target database must start with test_meow_")

    async def preflight():
        database = Database(settings)
        try:
            async with database.engine.connect() as conn:
                version = str((await conn.execute(text("SELECT VERSION()"))).scalar_one())
                if not supported_mysql_version(version):
                    pytest.fail("Integration target is not supported MySQL 5.7.24-log")
                names = await conn.run_sync(lambda sync: inspect(sync).get_table_names())
                if names:
                    pytest.fail("Integration test requires a completely empty target; nothing was changed")
        finally:
            await database.dispose()

    asyncio.run(preflight())
    backend = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=backend,
                            env=dict(os.environ), capture_output=True, text=True)
    if result.returncode:
        pytest.fail("Initial MySQL migration failed; run alembic upgrade head locally for diagnostic output")

    async def verify():
        database = Database(settings)
        try:
            assert (await database.check_readiness()).ready
            async with database.engine.connect() as conn:
                names = await conn.run_sync(lambda sync: inspect(sync).get_table_names())
                assert set(names) == set(Base.metadata.tables) | {"alembic_version"}
                assert (await conn.execute(text("SELECT @@session.time_zone"))).scalar_one() == "+00:00"
                revision = load_revision()
                assert await conn.run_sync(revision.table_issues) == []
                assert await conn.run_sync(revision.trigger_issues) == []
                await conn.rollback()
                users = Base.metadata.tables["users"]
                await conn.execute(users.insert().values(user_id="test_owner", email="test@example.invalid", name="Meow 👓"))
                products = Base.metadata.tables["products"]
                await conn.execute(products.insert().values(id="test_frame", name="Frame 👓", slug="test-frame",
                    sku="TEST-FRAME", description="Integration fixture", main_image="/fixture.png", price=Decimal("100.10")))
                price = (await conn.execute(select(products.c.price).where(products.c.id == "test_frame"))).scalar_one()
                assert price == Decimal("100.10")
                variants = Base.metadata.tables["product_variants"]
                with pytest.raises(DBAPIError) as error:
                    async with conn.begin_nested():
                        await conn.execute(variants.insert().values(id="test_invalid", product_id="test_frame",
                            sku="TEST-INVALID", stock=1, reserved=2))
                assert error.value.orig.args[0] == 1644
                await conn.execute(variants.insert().values(id="test_valid", product_id="test_frame",
                    sku="TEST-VALID", stock=2, reserved=1))
                with pytest.raises(DBAPIError) as error:
                    async with conn.begin_nested():
                        await conn.execute(variants.update().where(variants.c.id == "test_valid").values(stock=0))
                assert error.value.orig.args[0] == 1644
                with pytest.raises(IntegrityError):
                    async with conn.begin_nested():
                        await conn.execute(variants.insert().values(id="test_orphan", product_id="missing",
                            sku="TEST-ORPHAN", stock=1))
                # Roll back basic guard fixtures before independent concurrent
                # commerce transactions use the same disposable database.
                await conn.rollback()
            from database import configure_session_factory
            from tests_mysql.commerce_scenarios import live_commerce_concurrency_scenario
            monkeypatch.setenv("ENABLE_MOCK_PAYMENTS", "1")
            configure_session_factory(database.session_factory)
            try:
                await live_commerce_concurrency_scenario()
            finally:
                configure_session_factory(None)
        finally:
            await database.dispose()

    asyncio.run(verify())
