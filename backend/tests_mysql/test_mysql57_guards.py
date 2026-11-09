"""Frozen trigger rules, retry/preflight behavior, and portable NULL semantics.

The SQLite tests below disable native CHECK enforcement and exercise the frozen
trigger predicates. They do not claim execution of MySQL SIGNAL syntax.
"""
from __future__ import annotations

import re

import pytest
from sqlalchemy import CheckConstraint
from sqlalchemy.exc import IntegrityError

from mysql.base import Base
from mysql.check_integrity import load_revision
from mysql.config import STRICT_SQL_MODE
from tests_mysql.test_schema import NOW, add, connection  # noqa: F401: reuse isolated fixture


def test_frozen_rules_cover_every_metadata_check_without_changing_literals():
    revision = load_revision()
    expected = {str(check.name): (table.name, str(check.sqltext))
                for table in Base.metadata.tables.values() for check in table.constraints
                if isinstance(check, CheckConstraint)}
    actual = {}
    for table, rules in revision.RULES.items():
        columns = Base.metadata.tables[table].columns
        for name, predicate, new_predicate in rules:
            actual[name] = (table, predicate.replace("`", ""))
            assert new_predicate.replace("NEW.", "") == predicate
            refs = re.findall(r"NEW\.`([^`]+)`", new_predicate)
            assert refs
            assert all(column in columns and columns[column].computed is None for column in refs)
    assert actual == expected
    assert len(actual) == 97
    assert len(revision.RULES) == 45
    assert set(revision.ALL_TABLES) == set(Base.metadata.tables)
    assert revision.EXPECTED_SQL_MODES == set(STRICT_SQL_MODE.split(","))
    definitions = revision.trigger_definitions()
    assert len(definitions) == 90
    for name, definition in definitions.items():
        assert len(name) <= 64
        assert definition["sql"].count("SIGNAL SQLSTATE '45000'") == len(revision.RULES[definition["table"]])
        assert "IF NOT " not in definition["body"]
        for message in re.findall(r"MESSAGE_TEXT = '([^']+)'", definition["body"]):
            assert len(message) <= 128


def installed(definition, *, name, order=1):
    revision = load_revision()
    return {"name": name, "table_name": definition["table"], "event": definition["event"],
            "timing": "BEFORE", "body": definition["body"],
            "sql_mode": ",".join(sorted(revision.EXPECTED_SQL_MODES)), "action_order": order}


class Result:
    def __init__(self, rows=None, first=None):
        self.rows, self.value = rows or [], first

    def mappings(self):
        return iter(self.rows)

    def first(self):
        return self.value


class FakeConnection:
    def __init__(self, revision):
        self.revision = revision
        self.definitions = revision.trigger_definitions()
        self.triggers = {}
        self.invalid_tables = set()
        self.table_overrides = {}
        self.created = []
        self.fail_after = None
        self.inject_invalid_after_install = False

    def execute(self, statement):
        sql = str(statement)
        if "information_schema.TABLES" in sql:
            return Result([{"table_name": table, "engine": "InnoDB", "row_format": "Dynamic",
                            **self.table_overrides.get(table, {})} for table in self.revision.ALL_TABLES])
        if "information_schema.TRIGGERS" in sql:
            return Result(list(self.triggers.values()))
        raise AssertionError(sql)

    def exec_driver_sql(self, sql):
        if sql.startswith("SELECT 1 FROM "):
            table = re.match(r"SELECT 1 FROM `([^`]+)`", sql).group(1)
            return Result(first=(1,) if table in self.invalid_tables else None)
        if sql.startswith("CREATE TRIGGER "):
            if self.fail_after is not None and len(self.created) >= self.fail_after:
                raise RuntimeError("simulated DDL interruption")
            name = re.match(r"CREATE TRIGGER `([^`]+)`", sql).group(1)
            assert name not in self.triggers
            self.triggers[name] = installed(self.definitions[name], name=name)
            self.created.append(name)
            if self.inject_invalid_after_install and len(self.triggers) == 90:
                self.invalid_tables.add("product_variants")
            return Result()
        raise AssertionError(sql)


def setup_upgrade(monkeypatch):
    revision = load_revision()
    database = FakeConnection(revision)
    monkeypatch.setattr(revision.context, "is_offline_mode", lambda: False)
    monkeypatch.setattr(revision.op, "get_bind", lambda: database)
    return revision, database


def test_upgrade_validates_rows_and_installs_both_events(monkeypatch):
    revision, database = setup_upgrade(monkeypatch)
    revision.upgrade()
    assert len(database.created) == 90
    assert revision.trigger_issues(database) == []
    revision.upgrade()
    assert len(database.created) == 90  # exact matching guards are reused, never dropped


def test_upgrade_refuses_existing_bad_data_before_ddl(monkeypatch):
    revision, database = setup_upgrade(monkeypatch)
    database.invalid_tables.add("product_variants")
    with pytest.raises(RuntimeError, match="row_rule_violation:product_variants"):
        revision.upgrade()
    assert not database.created


def test_upgrade_refuses_wrong_table_storage_before_ddl(monkeypatch):
    revision, database = setup_upgrade(monkeypatch)
    database.table_overrides["products"] = {"row_format": "Compact"}
    with pytest.raises(RuntimeError, match="table_storage_mismatch:products"):
        revision.upgrade()
    assert not database.created


def test_upgrade_can_resume_partial_nontransactional_ddl(monkeypatch):
    revision, database = setup_upgrade(monkeypatch)
    database.fail_after = 7
    with pytest.raises(RuntimeError, match="DDL interruption"):
        revision.upgrade()
    assert len(database.created) == 7
    database.fail_after = None
    revision.upgrade()
    assert len(database.created) == 90
    assert len(set(database.created)) == 90


def test_upgrade_will_not_replace_changed_existing_trigger(monkeypatch):
    revision, database = setup_upgrade(monkeypatch)
    name, definition = next(iter(database.definitions.items()))
    database.triggers[name] = {**installed(definition, name=name), "body": "BEGIN SET @changed = 1; END"}
    with pytest.raises(RuntimeError, match="trigger_definition_mismatch"):
        revision.upgrade()
    assert not database.created


def test_final_row_scan_catches_installation_gap(monkeypatch):
    revision, database = setup_upgrade(monkeypatch)
    database.inject_invalid_after_install = True
    with pytest.raises(RuntimeError, match="row_rule_violation:product_variants"):
        revision.upgrade()
    assert len(database.created) == 90


def test_trigger_audit_rejects_different_creation_mode_and_later_mutators():
    revision = load_revision()
    database = FakeConnection(revision)
    for name, definition in database.definitions.items():
        database.triggers[name] = installed(definition, name=name)
    name = next(iter(database.triggers))
    database.triggers[name]["sql_mode"] = "NO_ENGINE_SUBSTITUTION"
    assert f"trigger_sql_mode_mismatch:{name}" in revision.trigger_issues(database)
    database.triggers[name]["sql_mode"] = STRICT_SQL_MODE
    database.triggers["later_custom_mutator"] = {**database.triggers[name], "name": "later_custom_mutator", "action_order": 2}
    assert f"trigger_not_last:{name}" in revision.trigger_issues(database)


@pytest.fixture
def guarded_connection(connection):
    connection.exec_driver_sql("PRAGMA ignore_check_constraints=ON")
    assert connection.exec_driver_sql("PRAGMA ignore_check_constraints").scalar_one() == 1
    revision = load_revision()
    for name, definition in revision.trigger_definitions().items():
        lines = [f"CREATE TRIGGER `{name}` BEFORE {definition['event']} ON `{definition['table']}` FOR EACH ROW BEGIN"]
        for rule_name, _, predicate in revision.RULES[definition["table"]]:
            lines.append(f"SELECT CASE WHEN ({predicate}) IS FALSE THEN RAISE(ABORT, '{rule_name}') END;")
        lines.append("END")
        connection.exec_driver_sql("\n".join(lines))
    return connection


def test_frozen_trigger_predicates_reject_bad_insert_and_update_without_native_checks(guarded_connection):
    conn = guarded_connection
    with pytest.raises(IntegrityError, match="ck_product_variants_inventory"):
        add(conn, "product_variants", product_id="prd_a", sku="bad-stock", stock=-1)
    with pytest.raises(IntegrityError, match="ck_product_variants_inventory"):
        conn.exec_driver_sql("UPDATE product_variants SET reserved=stock+1 WHERE id='var_a'")
    with pytest.raises(IntegrityError, match="ck_cart_items_quantity"):
        add(conn, "cart_items", user_id="usr_a", product_id="prd_a", quantity=0)
    with pytest.raises(IntegrityError, match="ck_product_reviews_rating"):
        add(conn, "product_reviews", product_id="prd_a", user_id="usr_a", user_name="A", rating=6, body="Fixture")
    with pytest.raises(IntegrityError, match="ck_flash_sales_window"):
        add(conn, "flash_sales", name="Invalid", start_at=NOW, end_at=NOW)


def test_frozen_trigger_predicates_keep_sql_null_semantics(guarded_connection):
    conn = guarded_connection
    # Optional monetary values and incomplete draft prescriptions remain NULL.
    conn.exec_driver_sql("UPDATE products SET discount_price=NULL WHERE id='prd_a'")
    add(conn, "prescriptions", id="nullable_rx", user_id="usr_a")
    add(conn, "prescription_eyes", prescription_id="nullable_rx", eye="right", axis=None)
    with pytest.raises(IntegrityError, match="ck_prescriptions_pd_pair"):
        conn.exec_driver_sql("UPDATE prescriptions SET pd_right=31 WHERE id='nullable_rx'")
    with pytest.raises(IntegrityError, match="ck_prescription_eyes_axis"):
        conn.exec_driver_sql("UPDATE prescription_eyes SET axis=181 WHERE prescription_id='nullable_rx'")
