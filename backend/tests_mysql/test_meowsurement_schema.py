"""Customer ownership and immutable-history structure for Meowsurement.

SQLite executes portable FK/UNIQUE/CHECK rules. Frozen MySQL trigger definitions
and emitted DDL are checked separately; these are not live MySQL trigger tests.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import re

import pytest
from sqlalchemy import CheckConstraint, String, UniqueConstraint, select
from sqlalchemy.exc import IntegrityError

from mysql.base import Base
from mysql.check_integrity import load_meowsurement_revision, load_revision, load_loyalty_revision, load_flat_master_revision
from tests_mysql.test_schema import NOW, TABLES, add, connection  # noqa: F401
from tests_mysql.test_migrations import BACKEND, offline


def session_values(suffix="a", **overrides):
    return dict(id=f"ms_{suffix}", user_id="usr_a", product_id="prd_a", variant_id="var_a",
                prescription_id="rx_a", profile_version=1, spec_version=1,
                examination_date=date(2026, 11, 9), algorithm_version="meow-fixture-1",
                profile_snapshot={"name": "A", "prescription": {"right": {"sph": "-1.00"}}},
                frame_snapshot={"a": "50.00", "b": "40.00", "dbl": "18.00", "ed": "54.00"},
                **overrides)


def revision_values(suffix="a", *, session="a", number=1, **overrides):
    return dict(id=f"mr_{suffix}", session_id=f"ms_{session}", user_id="usr_a",
                revision_number=number, data={"results": {}}, reason="Initial capture",
                actor_id="usr_a", algorithm_version="meow-fixture-1", **overrides)


def photo_values(suffix="a", *, session="a", **overrides):
    return dict(id=f"mp_{suffix}", session_id=f"ms_{session}", user_id="usr_a",
                storage_path=f"/private/{suffix}.jpg", sha256="a" * 64, source_sha256="b" * 64,
                mime_type="image/jpeg", width=1280, height=720, byte_size=10240,
                consent=True, expires_at=NOW + timedelta(days=30), **overrides)


def capture_values(suffix="a", *, revision="a", session="a", **overrides):
    values = dict(id=f"mc_{suffix}", revision_id=f"mr_{revision}", session_id=f"ms_{session}",
                  user_id="usr_a", capture_id=f"logical_{suffix}", view="frontal", width=1280,
                  height=720, data={"view": "frontal"})
    return {**values, **overrides}


def measurement_values(suffix="a", *, revision="a", session="a", **overrides):
    values = dict(id=f"mm_{suffix}", revision_id=f"mr_{revision}", session_id=f"ms_{session}",
                  user_id="usr_a", parameter="distance_pd", unit="mm", method="manual",
                  algorithm_version="meow-fixture-1", valid=True, values={"total": 62}, data={})
    return {**values, **overrides}


@pytest.fixture
def graph(connection):
    for suffix in ("a", "b"):
        add(connection, "prescriptions", id=f"rx_{suffix}", user_id=f"usr_{suffix}", pd_total=62)
        add(connection, "prescription_eyes", prescription_id=f"rx_{suffix}", eye="right", sph=-1, cyl=0, axis=0)
        add(connection, "prescription_eyes", prescription_id=f"rx_{suffix}", eye="left", sph=-1, cyl=0, axis=0)
    add(connection, "customer_profiles", user_id="usr_a", phone="6281234567890",
        birth_date=date(1990, 1, 1), active_prescription_id="rx_a", prescription_date=date(2026, 10, 1))
    add(connection, "product_frame_specifications", product_id="prd_a", a=50, b=40, dbl=18, ed=54,
        temple_length=140, enabled=True, symmetric=True, updated_by="usr_b")
    add(connection, "meowsurement_sessions", **session_values())
    add(connection, "meowsurement_sessions", **session_values("other"))
    add(connection, "meowsurement_sessions", **{**session_values("b"), "user_id": "usr_b", "prescription_id": "rx_b"})
    add(connection, "meowsurement_revisions", **revision_values())
    add(connection, "meowsurement_revisions", **revision_values("other", session="other"))
    add(connection, "meowsurement_revisions", **{**revision_values("b", session="b"), "user_id": "usr_b", "actor_id": "usr_b"})
    add(connection, "meowsurement_photos", **photo_values())
    add(connection, "meowsurement_photos", **photo_values("other", session="other"))
    add(connection, "meowsurement_captures", **capture_values(photo_id="mp_a", photo_hash="b" * 64))
    add(connection, "meowsurement_captures", **capture_values("other", revision="other", session="other"))
    add(connection, "meowsurement_measurements", **measurement_values())
    return connection


def test_valid_customer_graph_uses_catalog_and_existing_prescription(graph):
    graph.execute(TABLES["meowsurement_sessions"].update().where(TABLES["meowsurement_sessions"].c.id == "ms_a")
                  .values(current_revision_id="mr_a", revision_number=1))
    add(graph, "meowsurement_measurement_sources", revision_id="mr_a", measurement_id="mm_a", capture_row_id="mc_a")
    row = graph.execute(select(TABLES["meowsurement_sessions"]).where(TABLES["meowsurement_sessions"].c.id == "ms_a")).mappings().one()
    assert row["current_revision_id"] == "mr_a" and row["prescription_id"] == "rx_a"
    assert row["profile_snapshot"]["prescription"]["right"]["sph"] == "-1.00"
    assert graph.execute(select(TABLES["product_frame_specifications"].c.a)).scalar_one() == Decimal("50.00")


def test_profile_cannot_select_another_customers_prescription(graph):
    with pytest.raises(IntegrityError):
        graph.execute(TABLES["customer_profiles"].update().values(active_prescription_id="rx_b"))


@pytest.mark.parametrize("changed", [{"variant_id": "var_b"}, {"prescription_id": "rx_b"}])
def test_session_binds_variant_to_product_and_prescription_to_owner(graph, changed):
    with pytest.raises(IntegrityError):
        add(graph, "meowsurement_sessions", **{**session_values("invalid"), **changed})


def test_variant_specification_cannot_reference_another_product(graph):
    with pytest.raises(IntegrityError):
        add(graph, "product_variant_frame_specifications", variant_id="var_b", product_id="prd_a", a=50)


@pytest.mark.parametrize("revision", ["mr_other", "mr_b"])
def test_current_revision_must_belong_to_exact_session_and_customer(graph, revision):
    with pytest.raises(IntegrityError):
        graph.execute(TABLES["meowsurement_sessions"].update().where(TABLES["meowsurement_sessions"].c.id == "ms_a")
                      .values(current_revision_id=revision, revision_number=1))


def test_revision_parent_cannot_cross_sessions_even_for_same_customer(graph):
    with pytest.raises(IntegrityError):
        add(graph, "meowsurement_revisions", **revision_values("bad_parent", number=2, parent_revision_id="mr_other"))
    add(graph, "meowsurement_revisions", **revision_values("a2", number=2, parent_revision_id="mr_a"))
    with pytest.raises(IntegrityError):
        add(graph, "meowsurement_revisions", **revision_values("duplicate", number=2, parent_revision_id="mr_a"))


@pytest.mark.parametrize("changed", [{"photo_id": "mp_other"}, {"revision_id": "mr_other"}, {"user_id": "usr_b"}])
def test_capture_photo_and_revision_share_session_owner(graph, changed):
    with pytest.raises(IntegrityError):
        add(graph, "meowsurement_captures", **capture_values("bad", **changed))


def test_measurement_sources_cannot_cross_revisions(graph):
    with pytest.raises(IntegrityError):
        add(graph, "meowsurement_measurement_sources", revision_id="mr_a", measurement_id="mm_a", capture_row_id="mc_other")
    with pytest.raises(IntegrityError):
        add(graph, "meowsurement_measurement_sources", revision_id="mr_other", measurement_id="mm_a", capture_row_id="mc_other")
    add(graph, "meowsurement_measurement_sources", revision_id="mr_a", measurement_id="mm_a", capture_row_id="mc_a")
    with pytest.raises(IntegrityError):
        add(graph, "meowsurement_measurement_sources", revision_id="mr_a", measurement_id="mm_a", capture_row_id="mc_a")


@pytest.mark.parametrize("changed", [{"width": 0}, {"height": 0}, {"width": 5000, "height": 5000},
                                    {"byte_size": 8388609}, {"byte_size": 0}, {"consent": False}, {"mime_type": "image/svg+xml"}])
def test_private_photo_limits_and_explicit_consent(graph, changed):
    with pytest.raises(IntegrityError):
        add(graph, "meowsurement_photos", **{**photo_values("invalid"), **changed})


@pytest.mark.parametrize("changed", [{"parameter": "unknown"}, {"unit": "px"}, {"side": "back"}])
def test_canonical_measurement_keys_units_and_sides(graph, changed):
    with pytest.raises(IntegrityError):
        # Use an otherwise unused parameter so UNIQUE cannot hide a bad rule.
        add(graph, "meowsurement_measurements", **measurement_values("invalid", **{"parameter": "near_pd", **changed}))


@pytest.mark.parametrize("changed", [{"a": 0}, {"b": -1}, {"dbl": 0}, {"ed": -1}, {"temple_length": 0}, {"version": 0}])
def test_catalog_dimensions_and_versions_must_be_positive(graph, changed):
    with pytest.raises(IntegrityError):
        add(graph, "product_frame_specifications", product_id="prd_b", **changed)


def test_profile_rx_replacement_retains_session_source_and_prescription_history(graph):
    add(graph, "prescriptions", id="rx_new", user_id="usr_a", pd_total=64)
    graph.execute(TABLES["customer_profiles"].update().values(active_prescription_id="rx_new", version=2))
    row = graph.execute(select(TABLES["meowsurement_sessions"]).where(TABLES["meowsurement_sessions"].c.id == "ms_a")).mappings().one()
    assert row["prescription_id"] == "rx_a" and row["profile_version"] == 1
    assert row["profile_snapshot"]["prescription"]["right"]["sph"] == "-1.00"
    with pytest.raises(IntegrityError):
        graph.execute(TABLES["prescriptions"].delete().where(TABLES["prescriptions"].c.id == "rx_a"))


def test_audit_revision_requires_session_and_correct_customer(graph):
    values = dict(id="audit_bad", user_id="usr_a", actor_id="usr_a", action="revision.saved", revision_id="mr_a")
    with pytest.raises(IntegrityError):
        add(graph, "meowsurement_audit_events", **values)
    with pytest.raises(IntegrityError):
        add(graph, "meowsurement_audit_events", **{**values, "session_id": "ms_b"})
    add(graph, "meowsurement_audit_events", **{**values, "session_id": "ms_a"})


def test_new_tables_and_guard_predicates_cover_all_metadata_without_organization_model():
    old, new, loyalty = load_revision(), load_meowsurement_revision(), load_loyalty_revision()
    assert len(new.ALL_TABLES) == 11
    assert not set(old.ALL_TABLES).intersection(new.ALL_TABLES)
    from mysql.check_integrity import load_lens_index_types_revision, load_accessories_revision
    assert set(old.ALL_TABLES).union(new.ALL_TABLES, loyalty.ALL_TABLES, load_lens_index_types_revision().ALL_TABLES) == set(Base.metadata.tables)
    assert not any(name.startswith("of_") or name in {"organizations", "patients", "operators"} for name in new.ALL_TABLES)
    expected = {str(check.name): (table.name, str(check.sqltext)) for table in Base.metadata.tables.values()
                for check in table.constraints if isinstance(check, CheckConstraint)}
    actual = {}
    old.RULES = {key:value for key,value in old.RULES.items() if key != "categories"}
    updated, flat = load_accessories_revision(), load_flat_master_revision()
    old.RULES['products'] = updated.RULES['products']
    flat.RULES['categories'] = updated.RULES['categories']
    for revision in (old, new, loyalty, flat):
        for table, rules in revision.RULES.items():
            for name, predicate, qualified in rules:
                assert qualified.replace("NEW.", "") == predicate
                actual[name] = (table, predicate.replace("`", ""))
    assert actual == expected
    assert len(expected) == 139


def test_manual_frame_source_enforces_absent_catalog_ids(graph):
    values = {**session_values('manual'), 'product_id': None, 'variant_id': None, 'spec_scope': 'manual'}
    add(graph, 'meowsurement_sessions', **values)
    for changes in ({'spec_scope': 'product'}, {'product_id': 'prd_a'}, {'variant_id': 'var_a'}):
        with pytest.raises(IntegrityError):
            with graph.begin_nested():
                add(graph, 'meowsurement_sessions', **{**values, 'id': 'ms_bad', **changes})


def test_frozen_guards_protect_history_snapshots_review_and_current_revision():
    revision = load_meowsurement_revision()
    definitions = revision.trigger_definitions()
    for name, definition in definitions.items():
        assert len(name) <= 64
        for message in re.findall(r"MESSAGE_TEXT = '([^']+)'", definition["body"]):
            assert len(message) <= 128
    for table in revision.IMMUTABLE:
        for event in ("UPDATE", "DELETE"):
            body = next(d["body"] for d in definitions.values() if d["table"] == table and d["event"] == event)
            assert "Measurement history is append-only" in body
    update = "\n".join(revision.custom_checks("meowsurement_sessions", "UPDATE"))
    assert "NEW.`profile_snapshot` <=> OLD.`profile_snapshot`" in update
    assert "NEW.`frame_snapshot` <=> OLD.`frame_snapshot`" in update
    assert "revision_number = NEW.revision_number" in update
    assert "Approval requires an independent stored review" in update
    review = "\n".join(revision.custom_checks("meowsurement_reviews", "INSERT"))
    assert "meowsurement.review" in review and "u.is_active = 1" in review
    assert "r.actor_id <> NEW.reviewer_id" in review and "s.user_id <> NEW.reviewer_id" in review
    assert "s.current_revision_id" in review
    photo_update = "\n".join(revision.custom_checks("meowsurement_photos", "UPDATE"))
    assert "NEW.`source_sha256` <=> OLD.`source_sha256`" in photo_update
    assert "A deleted private photo cannot be reactivated" in photo_update


def test_incremental_schema_export_is_frozen_additive_and_targets_correct_head():
    revision = load_meowsurement_revision()
    sql = offline("upgrade", "20261106_0002:20261109_0003", "--sql")
    assert sql == (BACKEND / "sql/003_customer_meowsurement.sql").read_text(encoding="utf-8")
    assert sql == (BACKEND.parent / "docs/optifit/SCHEMA_MYSQL57.sql").read_text(encoding="utf-8")
    source = (BACKEND / "migrations/versions/20261109_0003_customer_meowsurement.py").read_text(encoding="utf-8")
    assert "from mysql" not in source and "create_all(" not in source
    assert "DROP TABLE" not in sql and "DELETE FROM" not in sql and "TRUNCATE" not in sql
    assert sql.count("CREATE TABLE ") == 11
    assert sql.count("CREATE TRIGGER ") == len(revision.trigger_definitions())
    assert "FOREIGN_KEY_CHECKS" not in sql
    assert "version_num='20261109_0003'" in sql
    assert not re.search(r"\bCHECK\s*\(|\bWITH\s+RECURSIVE\b|\bOVER\s*\(", sql)


def test_new_index_keys_fit_mysql57_dynamic_prefix_limit():
    new = load_meowsurement_revision()
    for name in new.ALL_TABLES:
        table = TABLES[name]
        keys = [tuple(table.primary_key.columns)]
        keys += [tuple(c.columns) for c in table.constraints if isinstance(c, UniqueConstraint)]
        keys += [tuple(index.columns) for index in table.indexes]
        keys += [tuple(c.columns) for c in table.foreign_key_constraints]
        for columns in keys:
            # Conservative upper bounds, including four bytes per utf8mb4 char.
            size = sum(c.type.length * 4 if isinstance(c.type, String) else 16 for c in columns)
            assert size <= 3072, (name, [c.name for c in columns], size)


def test_downgrade_explicitly_breaks_current_revision_cycle_before_dropping_tables():
    sql = offline("downgrade", "20261109_0003:20261106_0002", "--sql")
    assert sql.index("DROP FOREIGN KEY fk_meowsurement_current_revision") < sql.index("DROP TABLE ")
    assert sql.count("DROP TABLE ") == 11
