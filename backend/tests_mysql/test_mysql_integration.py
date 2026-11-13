"""Opt-in server acceptance check; never runs against an inferred destination.

This test leaves its schema and uniquely named commerce fixtures for inspection.
It never drops a database or resets an existing schema. See STEP_1.md before explicitly enabling it.
"""
from __future__ import annotations

import asyncio
from datetime import date
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
from mysql.database import Database, EXPECTED_SCHEMA_REVISION, supported_mysql_version
from mysql.check_integrity import audit

pytestmark = [
    pytest.mark.mysql_integration,
    pytest.mark.skipif(os.environ.get("MYSQL_INTEGRATION_TESTS") != "1",
                       reason="Requires an explicitly configured empty test_meow_* MySQL 5.7.24-log database"),
]


def test_head_migration_and_server_integrity(monkeypatch):
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
                assert (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalars().all() == [EXPECTED_SCHEMA_REVISION]
                assert (await conn.execute(text("SELECT @@session.time_zone"))).scalar_one() == "+00:00"
                # Audit the installed head, including superseded category and
                # product-kind rules, rather than the historical 0002 bodies.
                result = await audit()
                assert result['ok'], result['issues']
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
                await _verify_customer_measurement_guards(conn)
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


async def _verify_customer_measurement_guards(conn):
    """Run 0003-specific native guard checks only on the opted-in empty target.

    The outer test rolls these fixtures back. Portable ownership cases and
    byte-for-byte SQL export verification live in test_meowsurement_schema.py.
    """
    tables = Base.metadata.tables
    await conn.execute(tables["users"].insert().values(user_id="test_reviewer", email="reviewer@example.invalid",
                                                      name="Existing web reviewer", role="staff"))
    await conn.execute(tables["user_permissions"].insert().values(user_id="test_reviewer", permission="meowsurement.review"))
    await conn.execute(tables["prescriptions"].insert().values(id="test_rx", user_id="test_owner", pd_total=62))
    await conn.execute(tables["customer_profiles"].insert().values(user_id="test_owner", phone="6281234567890",
        birth_date=date(1990, 1, 1), active_prescription_id="test_rx", prescription_date=date(2026, 11, 1)))
    await conn.execute(tables["product_frame_specifications"].insert().values(product_id="test_frame",
        a=52, b=40, dbl=18, ed=56, enabled=True, symmetric=True, updated_by="test_reviewer"))
    sessions, revisions, reviews = (tables[name] for name in
        ("meowsurement_sessions", "meowsurement_revisions", "meowsurement_reviews"))
    await conn.execute(sessions.insert().values(id="test_measurement", user_id="test_owner", product_id="test_frame",
        variant_id="test_valid", prescription_id="test_rx", profile_version=1, spec_version=1,
        examination_date=date(2026, 11, 9), algorithm_version="test-native-1",
        profile_snapshot={"name": "Meow 👓", "prescription": {"pd_total": 62}},
        frame_snapshot={"a": 52, "b": 40, "dbl": 18, "ed": 56}))
    await conn.execute(revisions.insert().values(id="test_revision", session_id="test_measurement", user_id="test_owner",
        revision_number=1, data={}, reason="Initial native fixture", actor_id="test_owner", algorithm_version="test-native-1"))
    session_update = sessions.update().where(sessions.c.id == "test_measurement")
    await conn.execute(session_update.values(current_revision_id="test_revision", revision_number=1))

    invalid_updates = (
        session_update.values(profile_snapshot={"name": "Changed source"}),
        session_update.values(frame_snapshot={"a": 99}),
        session_update.values(revision_number=2),
        session_update.values(status="approved"),
        revisions.update().where(revisions.c.id == "test_revision").values(reason="Overwrite old history"),
    )
    for statement in invalid_updates:
        with pytest.raises(DBAPIError) as error:
            async with conn.begin_nested():
                await conn.execute(statement)
        assert error.value.orig.args[0] == 1644

    await conn.execute(session_update.values(status="pending_review"))
    await conn.execute(reviews.insert().values(id="test_review", session_id="test_measurement", user_id="test_owner",
        revision_id="test_revision", reviewer_id="test_reviewer", decision="approved",
        note="Independent native guard fixture", evidence={"reference": "test"}))
    await conn.execute(session_update.values(status="approved"))
    assert (await conn.execute(select(sessions.c.status).where(sessions.c.id == "test_measurement"))).scalar_one() == "approved"
