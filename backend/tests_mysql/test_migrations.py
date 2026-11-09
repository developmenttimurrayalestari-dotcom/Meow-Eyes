"""The committed Alembic snapshot must emit the reviewed MySQL schema."""
from __future__ import annotations

import os
import hashlib
from pathlib import Path
import re
import subprocess
import sys

from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable, CreateIndex

from mysql.base import Base
from mysql import models  # noqa: F401
from mysql.database import EXPECTED_SCHEMA_REVISION

BACKEND = Path(__file__).resolve().parents[1]


def offline(*args: str) -> str:
    # This operation must not depend on database credentials or a running DB.
    environment = {k: v for k, v in os.environ.items() if not k.startswith(("MYSQL_", "MONGO_"))}
    result = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND,
                            env=environment, text=True, capture_output=True, check=True)
    return result.stdout


def normalize(value: str) -> str:
    value = " ".join(value.split()).strip().rstrip(";")
    if not value.startswith("CREATE TABLE "):
        return value
    # Alembic orders constraints/options differently from declarative metadata.
    # Compare full definitions while treating their declaration order as neutral.
    start, end = value.index("("), value.rfind(")")
    body = value[start + 1:end]
    parts, fragment, depth, quote = [], [], 0, None
    for character in body:
        if quote:
            fragment.append(character)
            if character == quote:
                quote = None
        elif character in ("'", '"', "`"):
            quote = character
            fragment.append(character)
        elif character == "(":
            depth += 1
            fragment.append(character)
        elif character == ")":
            depth -= 1
            fragment.append(character)
        elif character == "," and depth == 0:
            parts.append("".join(fragment).strip())
            fragment = []
        else:
            fragment.append(character)
    parts.append("".join(fragment).strip())
    options = re.findall(r"(?:ENGINE|CHARSET|ROW_FORMAT)=\w+|COLLATE\s+\w+", value[end + 1:])
    return value[:start] + "(" + ", ".join(sorted(parts)) + ")" + " ".join(sorted(options))


def test_upgrade_sql_matches_committed_export_and_current_metadata():
    generated = offline("upgrade", "head", "--sql")
    stored = (BACKEND / "sql/001_initial_schema.sql").read_text(encoding="utf-8")
    assert generated == stored
    assert generated.count("CREATE TABLE ") == len(Base.metadata.tables) + 1
    assert f"version_num='{EXPECTED_SCHEMA_REVISION}'" in generated
    assert not re.search(r"\bCHECK\s*\(", generated)
    assert generated.count("CREATE TRIGGER ") == 90
    assert generated.count("DELIMITER $$") == 1
    assert generated.count("DELIMITER ;") == 1
    # The first table after Alembic's header has a leading comment; remove all
    # standalone comment lines before comparing complete DDL statements.
    no_comments = "\n".join(line for line in generated.splitlines() if not line.lstrip().startswith("--"))
    emitted = {normalize(statement) for statement in re.split(r";\s*(?:\n|$)", no_comments) if statement.strip()}
    dialect = mysql.dialect()
    for table in Base.metadata.sorted_tables:
        assert normalize(str(CreateTable(table).compile(dialect=dialect))) in emitted, table.name
        for index in table.indexes:
            assert normalize(str(CreateIndex(index).compile(dialect=dialect))) in emitted, index.name


def test_downgrade_sql_drops_children_before_parents():
    generated = offline("downgrade", f"{EXPECTED_SCHEMA_REVISION}:base", "--sql")
    positions = {name: generated.index(f"DROP TABLE {name};") for name in Base.metadata.tables}
    for table in Base.metadata.tables.values():
        for fk in table.foreign_key_constraints:
            parent = fk.elements[0].column.table.name
            if parent != table.name:
                assert positions[table.name] < positions[parent], (table.name, parent)


def test_revision_is_frozen_and_single_head():
    revision = BACKEND / "migrations/versions/20261106_0001_initial_relational_schema.py"
    source = revision.read_text(encoding="utf-8")
    assert hashlib.sha256(revision.read_bytes()).hexdigest() == "79c191750eda0eea805bbdcf8c1ea748c090f8bfc9b11f632d0c14d5c18d72c1"
    assert "from mysql" not in source
    assert "create_all(" not in source and "drop_all(" not in source
    assert "allow_schema_drop" in source
    assert offline("heads").strip() == f"{EXPECTED_SCHEMA_REVISION} (head)"


def test_incremental_mysql57_export_contains_no_table_replacement():
    sql = offline("upgrade", f"20261106_0001:{EXPECTED_SCHEMA_REVISION}", "--sql")
    assert sql == (BACKEND / "sql/002_mysql57_compatibility.sql").read_text(encoding="utf-8")
    assert sql.count("CREATE TRIGGER ") == 90
    assert "CREATE TABLE " not in sql and "DROP TABLE " not in sql
    assert "DELETE FROM " not in sql and "TRUNCATE " not in sql
    assert "--preflight-only" in sql


def test_mysql57_has_no_unsupported_text_defaults_and_frozen_replay_matches():
    from sqlalchemy import Column, MetaData, Table, Text, text
    from sqlalchemy.exc import CompileError
    import pytest
    original = Table("point_logs", MetaData(), Column("note", Text, nullable=False, server_default=text("('')")))
    rendered = str(CreateTable(original).compile(dialect=mysql.dialect()))
    assert "note TEXT NOT NULL" in rendered and "DEFAULT" not in rendered
    # The compiler clones the legacy column and must not mutate frozen metadata.
    assert str(original.c.note.server_default.arg) == "('')"
    current = Base.metadata.tables["point_logs"].c.note
    assert current.server_default is None and current.default.arg == ""
    invalid = Table("future_table", MetaData(), Column("body", Text, server_default="unexpected"))
    with pytest.raises(CompileError, match="forbids"):
        str(CreateTable(invalid).compile(dialect=mysql.dialect()))
    sql = offline("upgrade", "head", "--sql")
    assert not re.search(r"\b(?:TEXT|BLOB|JSON|GEOMETRY)\b[^,\n]*\bDEFAULT\b", sql)
