"""Render the current relational metadata without connecting to a database."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from sqlalchemy import CheckConstraint, UniqueConstraint  # noqa: E402
from sqlalchemy.dialects import mysql  # noqa: E402
from mysql.base import Base  # noqa: E402
from mysql import models  # noqa: F401,E402


def render() -> str:
    tables = Base.metadata.sorted_tables
    dialect = mysql.dialect()
    out = [
        "# MySQL 5.7.24-log schema reference", "",
        "Generated from `backend/mysql/models.py`; schema only, with no database access.", "",
        f"**{len(tables)} business/support tables**, excluding Alembic's `alembic_version` table.", "",
        "All tables use InnoDB, ROW_FORMAT=DYNAMIC and utf8mb4. Imported string IDs are retained. "
        "Dates use UTC DATETIME(6); money uses DECIMAL(18,2).", "",
        "MySQL 5.7 does not enforce CHECK constraints. The 97 row rules shown below "
        "are enforced by 90 BEFORE INSERT/UPDATE validation triggers installed by "
        "revision `20261106_0002`, across 45 tables. Metadata CHECK objects remain "
        "for documentation and portable SQLite tests; they are omitted from MySQL DDL.", "",
        "`prescriptions` attached to orders are separate snapshots; future services "
        "must enforce ownership, private access and immutability. SQL constraints "
        "do not check cross-row order status, category cycles or external webhook signatures.", "",
        "## Table index", "",
        "| Table | Columns | Foreign keys |", "| --- | ---: | ---: |",
    ]
    for table in sorted(tables, key=lambda t: t.name):
        out.append(f"| `{table.name}` | {len(table.columns)} | {len(table.foreign_key_constraints)} |")
    for table in sorted(tables, key=lambda t: t.name):
        out.extend(["", f"## {table.name}", "", "| Column | MySQL type | Null | Default / generated |",
                    "| --- | --- | --- | --- |"])
        for col in table.columns:
            if col.computed is not None:
                default = "GENERATED: " + str(col.computed.sqltext)
            elif col.server_default is not None:
                default = str(col.server_default.arg.compile(dialect=dialect, compile_kwargs={"literal_binds": True})) if hasattr(col.server_default.arg, "compile") else str(col.server_default.arg)
            elif col.default is not None and col.default.is_callable:
                default = "application generated"
            elif col.default is not None and col.default.is_scalar:
                default = "application: " + repr(col.default.arg)
            else:
                default = "—"
            default = default.replace("|", "\\|").replace("\n", " ")
            out.append(f"| `{col.name}`{' (PK)' if col.primary_key else ''} | `{col.type.compile(dialect=dialect)}` | {'yes' if col.nullable else 'no'} | {default} |")
        if table.foreign_key_constraints:
            out.extend(["", "Foreign keys:", ""])
            for fk in sorted(table.foreign_key_constraints, key=lambda x: str(x.name)):
                source = ", ".join(c.name for c in fk.columns)
                target = ", ".join(e.target_fullname for e in fk.elements)
                out.append(f"- `{source}` → `{target}`; delete `{fk.ondelete or 'RESTRICT'}`.")
        unique = sorted((c for c in table.constraints if isinstance(c, UniqueConstraint)), key=lambda x: str(x.name))
        if unique:
            out.extend(["", "Unique keys:", ""])
            out.extend(f"- `{', '.join(c.name for c in constraint.columns)}`." for constraint in unique)
        checks = sorted((c for c in table.constraints if isinstance(c, CheckConstraint)), key=lambda x: str(x.name))
        if checks:
            out.extend(["", "Row rules (enforced by MySQL 5.7 validation triggers):", ""])
            out.extend(f"- `{constraint.sqltext}`." for constraint in checks)
        if table.indexes:
            out.extend(["", "Indexes:", ""])
            for index in sorted(table.indexes, key=lambda x: str(x.name)):
                prefix = index.dialect_options['mysql'].get('prefix') or ""
                out.append(f"- `{index.name}`: {prefix + ' ' if prefix else ''}`{', '.join(c.name for c in index.columns)}`.")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BACKEND.parent / "docs/mysql-migration/SCHEMA_REFERENCE.md")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(), encoding="utf-8")
    print(args.output)
