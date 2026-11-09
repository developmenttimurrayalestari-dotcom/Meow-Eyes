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


async def audit(*, preflight_only: bool = False) -> dict:
    database = Database(MySQLSettings.from_env())
    try:
        revision = load_revision()
        async with database.engine.connect() as connection:
            compatibility = await check_server_compatibility(connection)
            if not compatibility.ready:
                return {"ok": False, "issues": [compatibility.reason]}
            issues = await connection.run_sync(revision.table_issues)
            if not issues:
                issues.extend(await connection.run_sync(revision.row_issues))
            if not preflight_only:
                issues.extend(await connection.run_sync(revision.trigger_issues))
            return {
                "ok": not issues,
                "mode": "preflight_only" if preflight_only else "full_integrity_audit",
                "expected_triggers": len(revision.trigger_definitions()),
                "row_rules": sum(len(rules) for rules in revision.RULES.values()),
                "definer_privileges_verified": False,
                "issues": issues,
            }
    finally:
        await database.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-only", action="store_true",
                        help="Validate target tables/data before 0002; do not require installed triggers")
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
