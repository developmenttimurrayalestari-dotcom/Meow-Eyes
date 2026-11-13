"""Read-only operator audit for the MySQL 5.7 schema and validation guards.

Run with the stable migration/DBA account, which can see trigger metadata:
    python -m mysql.check_integrity
    python -m mysql.check_integrity --preflight-only
Normal application readiness does not need TRIGGER privilege.
The audit verifies structure, predicates, SQL mode and guard ordering; it does
not certify the existence/effective privileges of trigger definer accounts.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from .config import ConfigurationError, MySQLSettings
from .database import Database, check_server_compatibility


def load_revision():
    path = Path(__file__).resolve().parents[1] / "migrations/versions/20261106_0002_mysql57_integrity.py"
    spec = importlib.util.spec_from_file_location("_meow_mysql57_integrity", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing MySQL 5.7 integrity revision")
    revision = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(revision)
    return revision


def load_meowsurement_revision(*, previous=False):
    filename = "20261109_0003_customer_meowsurement.py" if previous else "20261110_0004_optional_customer_frame.py"
    path = Path(__file__).resolve().parents[1] / "migrations/versions" / filename
    spec = importlib.util.spec_from_file_location("_meow_customer_measurement", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing customer Meowsurement revision")
    revision = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(revision)
    return revision


def load_loyalty_revision():
    path = Path(__file__).resolve().parents[1] / 'migrations/versions/20261111_0005_loyalty_games_returns.py'
    spec = importlib.util.spec_from_file_location('_meow_loyalty', path)
    revision = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(revision)
    return revision

def load_flat_master_revision():
    path = Path(__file__).resolve().parents[1] / 'migrations/versions/20261111_0006_flat_product_masters.py'
    spec = importlib.util.spec_from_file_location('_meow_flat_masters', path)
    revision = importlib.util.module_from_spec(spec); spec.loader.exec_module(revision)
    return revision

def load_product_deletion_revision():
    path = Path(__file__).resolve().parents[1] / 'migrations/versions/20261112_0007_product_deletion.py'
    spec = importlib.util.spec_from_file_location('_meow_product_deletion', path)
    revision = importlib.util.module_from_spec(spec); spec.loader.exec_module(revision)
    return revision


def load_retired_collections_revision():
    path = Path(__file__).resolve().parents[1] / 'migrations/versions/20261112_0008_retire_collections.py'
    spec = importlib.util.spec_from_file_location('_meow_retired_collections', path)
    revision = importlib.util.module_from_spec(spec); spec.loader.exec_module(revision)
    return revision


def load_stock_ttb_revision():
    path = Path(__file__).resolve().parents[1] / 'migrations/versions/20261112_0009_stock_ttb.py'
    spec = importlib.util.spec_from_file_location('_meow_stock_ttb', path)
    revision = importlib.util.module_from_spec(spec); spec.loader.exec_module(revision)
    return revision


def load_lens_index_types_revision():
    path = Path(__file__).resolve().parents[1] / 'migrations/versions/20261112_0010_lens_index_types.py'
    spec = importlib.util.spec_from_file_location('_meow_lens_index_types', path)
    revision = importlib.util.module_from_spec(spec); spec.loader.exec_module(revision)
    return revision


def load_native_google_revision():
    path = Path(__file__).resolve().parents[1] / 'migrations/versions/20261112_0011_native_google_identity.py'
    spec = importlib.util.spec_from_file_location('_meow_native_google', path)
    revision = importlib.util.module_from_spec(spec); spec.loader.exec_module(revision)
    return revision


def load_accessories_revision():
    path = Path(__file__).resolve().parents[1] / 'migrations/versions/20261112_0012_accessories_product_type.py'
    spec = importlib.util.spec_from_file_location('_meow_accessories', path)
    revision = importlib.util.module_from_spec(spec); spec.loader.exec_module(revision)
    return revision


async def audit(*, preflight_only: bool = False) -> dict:
    database = Database(MySQLSettings.from_env())
    try:
        revisions = [load_revision(), load_meowsurement_revision()]
        revisions.append(load_loyalty_revision())
        async with database.engine.connect() as connection:
            compatibility = await check_server_compatibility(connection)
            if not compatibility.ready:
                return {"ok": False, "issues": [compatibility.reason]}
            # Pre-upgrade audits check the installed 0003 rules. Full audits
            # always require the latest nullable source column and guards.
            if preflight_only and await connection.run_sync(lambda conn: inspect(conn).has_table('alembic_version')):
                installed = (await connection.execute(text('SELECT version_num FROM alembic_version'))).scalars().all()
                if installed == ['20261109_0003']:
                    revisions[1] = load_meowsurement_revision(previous=True)
            installed = []
            if await connection.run_sync(lambda conn: inspect(conn).has_table('alembic_version')):
                installed = (await connection.execute(text('SELECT version_num FROM alembic_version'))).scalars().all()
            if installed in (['20261111_0006'], ['20261112_0007'], ['20261112_0008'], ['20261112_0009'], ['20261112_0010'], ['20261112_0011'], ['20261112_0012']):
                # 0006 replaces the historical category predicates/guards only.
                revisions[0].RULES = {key: value for key,value in revisions[0].RULES.items() if key != 'categories'}
                revisions.append(load_flat_master_revision())
            if installed in (['20261112_0007'], ['20261112_0008'], ['20261112_0009'], ['20261112_0010'], ['20261112_0011'], ['20261112_0012']):
                revisions.append(load_product_deletion_revision())
            if installed in (['20261112_0008'], ['20261112_0009'], ['20261112_0010'], ['20261112_0011'], ['20261112_0012']):
                revisions.append(load_retired_collections_revision())
            if installed in (['20261112_0009'], ['20261112_0010'], ['20261112_0011'], ['20261112_0012']):
                revisions.append(load_stock_ttb_revision())
            if installed in (['20261112_0010'], ['20261112_0011'], ['20261112_0012']):
                revisions.append(load_lens_index_types_revision())
            if installed in (['20261112_0011'], ['20261112_0012']):
                revisions.append(load_native_google_revision())
            if installed == ['20261112_0012']:
                # Replace only the affected predicates; all other guards remain.
                updated = load_accessories_revision()
                revisions[0].RULES['products'] = updated.RULES['products']
                for revision in revisions[1:]:
                    if 'categories' in revision.RULES:
                        revision.RULES['categories'] = updated.RULES['categories']
            issues = []
            if not preflight_only and installed != ['20261112_0012']: issues.append('schema_revision_mismatch')
            for revision in revisions:
                table_issues = await connection.run_sync(revision.table_issues)
                # Before 0003, all its new tables may legitimately be absent.
                # A partial installation is never treated as an empty baseline.
                absent = {"missing_table:" + table for table in revision.ALL_TABLES}
                if preflight_only and set(table_issues) == absent:
                    continue
                issues.extend(table_issues)
                if not table_issues:
                    issues.extend(await connection.run_sync(revision.row_issues))
                if not preflight_only:
                    issues.extend(await connection.run_sync(revision.trigger_issues))
            return {
                "ok": not issues,
                "mode": "preflight_only" if preflight_only else "full_integrity_audit",
                "expected_triggers": sum(len(revision.trigger_definitions()) for revision in revisions),
                "row_rules": sum(len(rules) for revision in revisions for rules in revision.RULES.values()),
                "definer_privileges_verified": False,
                "issues": issues,
            }
    finally:
        await database.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-only", action="store_true",
                        help="Validate existing tables/data before migration; permit absent 0003 tables and do not require triggers")
    args = parser.parse_args()
    try:
        result = asyncio.run(audit(preflight_only=args.preflight_only))
    except ConfigurationError as error:
        result = {"ok": False, "issues": [str(error)]}
    except (SQLAlchemyError, OSError, RuntimeError, TimeoutError):
        # Driver errors can contain private connection details. Do not echo them.
        result = {"ok": False, "issues": ["integrity_audit_unavailable_check_connection_and_privileges"]}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
