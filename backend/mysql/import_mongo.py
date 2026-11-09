"""Plan/apply an audited local MongoDB export. Default: offline dry-run only."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import tempfile

from sqlalchemy.exc import SQLAlchemyError

from .check_integrity import audit
from .config import ConfigurationError, MySQLSettings
from .database import Database
from .importer import ImportRejected, apply_plan, inspect_target, plan_directory, stable_id


def _validate_report_destination(report: Path | None, export_directory: Path) -> None:
    """Validate before the exception/reporting path can perform any write."""
    if report is None:
        return
    export_root = export_directory.resolve()
    if report.resolve().is_relative_to(export_root) or report.is_symlink():
        raise ImportRejected("Report must be a non-symlink path outside the export directory")
    if report.exists():
        if not report.is_file():
            raise ImportRejected("Report destination must be a regular file")
        if export_root.is_dir():
            for input_path in export_root.iterdir():
                if input_path.is_file() and report.samefile(input_path):
                    raise ImportRejected("Report destination aliases a source input file")


def _write_report(report: Path, encoded: str) -> None:
    """Replace one report atomically, never follow its existing hard/symlink."""
    report.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=report.parent,
                                         prefix=".migration-report-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
        os.replace(temporary, report)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


async def execute_target(plan, args) -> dict:
    database = Database(MySQLSettings.from_env())
    try:
        ready = await database.check_readiness()
        if not ready.ready:
            raise ImportRejected(f"Target readiness failed: {ready.reason}")
        integrity = await audit()
        if not integrity["ok"]:
            raise ImportRejected("Target integrity guard audit failed; run python -m mysql.check_integrity")
        run_id = args.run_id or stable_id("run", plan.export_checksum)
        if not args.apply:
            return {"target_check": await inspect_target(plan, database.session_factory, run_id), "run_id": run_id}
        if not args.writers_stopped:
            raise ImportRejected("Apply requires --writers-stopped after stopping all application/scheduler writers")
        return await apply_plan(plan, database.session_factory, source_label=args.source_label,
                                run_id=run_id, acknowledge_warnings=args.acknowledge_warnings,
                                chunk_size=args.chunk_size)
    finally:
        await database.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_directory", type=Path)
    parser.add_argument("--report", type=Path, help="Write sanitized JSON report outside the export directory")
    parser.add_argument("--allow-partial", action="store_true", help="Explicitly treat missing collections as empty; requires warning acknowledgement on apply")
    parser.add_argument("--target-check", action="store_true", help="Also connect read-only to the target and check emptiness/resume provenance")
    parser.add_argument("--apply", action="store_true", help="Write only a preflight-clean plan to an empty target or exact matching interrupted run")
    parser.add_argument("--writers-stopped", action="store_true", help="Operator attests all old/new application and scheduler writes are stopped")
    parser.add_argument("--acknowledge-warnings", action="store_true", help="Accept reported, explicitly known preservation limits; never overrides errors")
    parser.add_argument("--source-label", default="reviewed-local-export")
    parser.add_argument("--run-id", help="Exact existing run ID for resume; otherwise a deterministic export-based ID is used")
    parser.add_argument("--chunk-size", type=int, default=200)
    args = parser.parse_args(argv)
    # Return immediately on a rejected destination. In particular, an error
    # report must never overwrite the source file that triggered this guard.
    try:
        _validate_report_destination(args.report, args.export_directory)
    except (ImportRejected, OSError, RuntimeError) as exc:
        message = str(exc) if isinstance(exc, ImportRejected) else "report_destination_could_not_be_validated"
        print(json.dumps({"ok": False, "error": message}))
        return 2
    result: dict = {"ok": False, "mode": "apply" if args.apply else "dry_run"}
    exit_code = 2
    try:
        plan = plan_directory(args.export_directory, allow_partial=args.allow_partial)
        result["plan"] = plan.report()
        if plan.errors:
            result["error"] = "source_preflight_errors"
        elif args.apply or args.target_check:
            result["target"] = asyncio.run(execute_target(plan, args))
            result["ok"] = True
            exit_code = 0
        else:
            result["ok"] = True
            result["database_connected"] = False
            result["target_writes"] = 0
            exit_code = 0
    except (ImportRejected, ConfigurationError) as exc:
        result["error"] = str(exc)
    except (SQLAlchemyError, OSError, RuntimeError, TimeoutError):
        # Never echo a driver exception/traceback containing connection or row data.
        result["error"] = "import_failed_check_local_files_database_configuration_privileges_and_run_status"
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        try:
            _write_report(args.report, encoded)
        except OSError:
            print(json.dumps({"ok": False, "error": "report_file_could_not_be_written"}))
            return 2
    print(encoded, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
