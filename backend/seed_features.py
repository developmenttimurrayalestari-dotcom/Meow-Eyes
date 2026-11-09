"""Add the requested optical knowledge and New Arrival category safely.

    python seed_features.py          # inspect planned additions only
    python seed_features.py --apply  # insert missing content; preserve edits

The database must already be migrated. This is content initialization, not a
demo-data reset, and is available in production through an explicit --apply.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from mysql.config import MySQLSettings, load_runtime_environment
from mysql.database import Database
from mysql.feature_content import ensure_feature_content


async def run(apply: bool):
    load_runtime_environment(Path(__file__).parent / ".env.mysql")
    database = Database(MySQLSettings.from_env())
    try:
        ready = await database.check_readiness()
        if not ready.ready:
            raise RuntimeError(f"Database belum siap: {ready.reason}")
        async with database.session_factory() as session:
            async with session.begin():
                report = await ensure_feature_content(session, apply=apply)
                if not apply:
                    await session.rollback()
                return {"ok": True, **report}
    finally:
        await database.dispose()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write missing optical content and the one-time badge backfill")
    args = parser.parse_args(argv)
    try:
        result = asyncio.run(run(args.apply))
    except Exception:
        result = {"ok": False, "error": "seed_features_failed_check_database_environment_and_schema"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
