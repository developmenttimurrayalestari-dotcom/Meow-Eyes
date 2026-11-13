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
from mysql.check_integrity import load_meowsurement_revision, load_loyalty_revision

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
    generated = offline("upgrade", "20261111_0005", "--sql")
    stored = (BACKEND / "sql/001_initial_schema.sql").read_text(encoding="utf-8")
    # The released baseline export remains frozen at 0002. New DDL has its own
    # incremental export; a fresh replay still matches all current metadata.
    assert offline("upgrade", "20261106_0002", "--sql") == stored
    assert generated.count("CREATE TABLE ") == len(Base.metadata.tables)  # 0010 adds lens_index_types later.
    assert "version_num='20261111_0005'" in generated
    assert not re.search(r"\bCHECK\s*\(", generated)
    assert generated.count("CREATE TRIGGER ") == 92 + len(load_meowsurement_revision().trigger_definitions()) + len(load_loyalty_revision().trigger_definitions())
    assert generated.count("DELIMITER $$") == 4
    assert generated.count("DELIMITER ;") == 4
    assert 'ALTER TABLE meowsurement_sessions MODIFY product_id VARCHAR(64) COLLATE utf8mb4_bin NULL' in generated
    # The first table after Alembic's header has a leading comment; remove all
    # standalone comment lines before comparing complete DDL statements.
    no_comments = "\n".join(line for line in generated.splitlines() if not line.lstrip().startswith("--"))
    emitted = {normalize(statement) for statement in re.split(r";\s*(?:\n|$)", no_comments) if statement.strip()}
    dialect = mysql.dialect()
    for table in Base.metadata.sorted_tables:
        if table.name in ("categories", "lens_index_types"): continue  # Later incremental revisions.
        ddl = str(CreateTable(table).compile(dialect=dialect))
        if table.name == 'users':
            # Native Google identity is additive in 0011, after the frozen export.
            ddl = re.sub(r'\s*google_subject VARCHAR\(255\) COLLATE utf8mb4_bin,', '', ddl)
            ddl = re.sub(r',\s*CONSTRAINT uq_users_google_subject UNIQUE \(google_subject\)', '', ddl)
        if table.name == 'products':
            # 0007 adds the nullable deletion marker after the frozen 0005 export.
            ddl = re.sub(r'\s*deleted_at DATETIME\(6\),', '', ddl)
        if table.name == 'stock_movements':
            ddl = re.sub(r'\s*ttb_number VARCHAR\(128\),', '', ddl)  # Added by 0009.
        if table.name == 'meowsurement_sessions':
            # Frozen 0003 creates NOT NULL; 0004 explicitly relaxes this column.
            ddl = ddl.replace('product_id VARCHAR(64) COLLATE utf8mb4_bin,', 'product_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,')
        assert normalize(ddl) in emitted, table.name
        for index in table.indexes:
            if index.name == 'ix_products_admin_list': continue  # Added by 0007.
            assert normalize(str(CreateIndex(index).compile(dialect=dialect))) in emitted, index.name


def test_product_deletion_incremental_sql_preserves_existing_products():
    sql = offline('upgrade', '20261111_0006:20261112_0007', '--sql')
    assert sql == (BACKEND / 'sql/007_product_deletion.sql').read_text(encoding='utf-8')
    assert 'ALTER TABLE products ADD COLUMN deleted_at DATETIME(6)' in sql
    assert 'CREATE INDEX ix_products_admin_list ON products (deleted_at, created_at, id)' in sql
    assert 'DELETE FROM products' not in sql and 'UPDATE products' not in sql
    assert "version_num='20261112_0007'" in sql


def test_downgrade_sql_drops_children_before_parents():
    generated = offline("downgrade", "20261109_0003:base", "--sql")
    statements = generated.replace("`", "")
    positions = {name: statements.index(f"DROP TABLE {name};") for name in Base.metadata.tables if name not in load_loyalty_revision().ALL_TABLES and name != 'lens_index_types'}
    for table in Base.metadata.tables.values():
        if table.name not in positions: continue
        for fk in table.foreign_key_constraints:
            parent = fk.elements[0].column.table.name
            if parent != table.name and not fk.use_alter:
                assert positions[table.name] < positions[parent], (table.name, parent)


def test_lens_index_types_incremental_sql_matches_metadata_without_rewriting_existing_data():
    sql = offline('upgrade', '20261112_0009:20261112_0010', '--sql')
    assert sql == (BACKEND / 'sql/010_lens_index_types.sql').read_text(encoding='utf-8')
    assert sql.count('CREATE TABLE ') == 1
    table = Base.metadata.tables['lens_index_types']
    no_comments = '\n'.join(line for line in sql.splitlines() if not line.lstrip().startswith('--'))
    emitted = {normalize(statement) for statement in re.split(r';\s*(?:\n|$)', no_comments) if statement.strip()}
    assert normalize(str(CreateTable(table).compile(dialect=mysql.dialect()))) in emitted
    assert 'DELETE FROM' not in sql and 'TRUNCATE' not in sql and 'UPDATE products' not in sql


def test_native_google_incremental_sql_preserves_existing_users():
    sql = offline('upgrade', '20261112_0010:20261112_0011', '--sql')
    assert sql == (BACKEND / 'sql/011_native_google_identity.sql').read_text(encoding='utf-8')
    assert 'ALTER TABLE users ADD COLUMN google_subject VARCHAR(255) COLLATE utf8mb4_bin' in sql
    assert 'UNIQUE (google_subject)' in sql
    assert 'UPDATE users' not in sql and 'DELETE FROM users' not in sql and 'DROP TABLE' not in sql


def test_revision_is_frozen_and_single_head():
    revision = BACKEND / "migrations/versions/20261106_0001_initial_relational_schema.py"
    source = revision.read_text(encoding="utf-8")
    assert hashlib.sha256(revision.read_bytes()).hexdigest() == "79c191750eda0eea805bbdcf8c1ea748c090f8bfc9b11f632d0c14d5c18d72c1"
    assert "from mysql" not in source
    assert "create_all(" not in source and "drop_all(" not in source
    assert "allow_schema_drop" in source
    assert offline("heads").strip() == f"{EXPECTED_SCHEMA_REVISION} (head)"


def test_accessories_guard_migration_preserves_data_and_other_integrity_rules():
    from mysql.check_integrity import load_revision, load_flat_master_revision, load_accessories_revision
    revision = load_accessories_revision()
    sql = offline('upgrade', '20261112_0011:20261112_0012', '--sql')
    assert sql == (BACKEND / 'sql/012_accessories_product_type.sql').read_text(encoding='utf-8')
    assert sql.count('DROP TRIGGER ') == sql.count('CREATE TRIGGER ') == 4
    assert not any(word in sql for word in ('CREATE TABLE ', 'DROP TABLE ', 'INSERT INTO ', 'UPDATE products', 'DELETE FROM '))
    base, flat = load_revision(), load_flat_master_revision()
    before = {**{name: item for name, item in base.trigger_definitions().items() if item['table'] == 'products'}, **flat.trigger_definitions()}
    after = revision.trigger_definitions()
    for name in before:
        assert revision.canonical_body(after[name]['body'].replace("('frame','lens','package','accessories')", "('frame','lens','package')")) == revision.canonical_body(before[name]['body'])
    # Audit helpers must expect the same installed definitions after the upgrade.
    base.RULES['products'] = revision.RULES['products']
    flat.RULES['categories'] = revision.RULES['categories']
    for name, item in {**base.trigger_definitions(), **flat.trigger_definitions()}.items():
        if name in after:
            assert revision.canonical_body(item['body']) == revision.canonical_body(after[name]['body'])


def test_incremental_mysql57_export_contains_no_table_replacement():
    sql = offline("upgrade", "20261106_0001:20261106_0002", "--sql")
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
    sql = offline("upgrade", "20261111_0005", "--sql")
    assert not re.search(r"\b(?:TEXT|BLOB|JSON|GEOMETRY)\b[^,\n]*\bDEFAULT\b", sql)
