from pathlib import Path
from sqlalchemy import CheckConstraint
from mysql.base import Base
from mysql.check_integrity import load_loyalty_revision
from tests_mysql.test_migrations import offline

def test_frozen_loyalty_ddl_and_guards_match_metadata_and_export():
    revision=load_loyalty_revision()
    sql=offline('upgrade','20261110_0004:20261111_0005','--sql')
    assert sql==(Path(__file__).resolve().parents[1]/'sql/005_loyalty_games_returns.sql').read_text(encoding='utf-8')
    assert len(revision.ALL_TABLES)==14
    expected={str(c.name):str(c.sqltext) for t in Base.metadata.tables.values() if t.name in revision.ALL_TABLES for c in t.constraints if isinstance(c,CheckConstraint)}
    actual={name:predicate for rules in revision.RULES.values() for name,predicate,_ in rules}
    assert actual==expected
    for rules in revision.RULES.values():
        for _,predicate,new_predicate in rules: assert new_predicate.replace('NEW.','')==predicate
    triggers=revision.trigger_definitions()
    assert all(len(name)<=64 for name in triggers)
    assert {'point_history','point_rate_versions','return_timeline','return_evidence'}<=revision.IMMUTABLE
    assert all('rate_snapshot' in revision.SNAPSHOTS[name] for name in ('point_lots','point_redemptions','cashback_awards'))
    assert 'DELETE FROM' not in sql and 'DROP TABLE' not in sql
    assert "WHERE points_balance>0" in sql and "'locked'" in sql
    # MySQL 5.7 can evaluate a wrapped UUID once for INSERT SELECT. Every
    # imported identity must depend on the original row instead.
    assert "SHA2(CONCAT('legacy-lot:',user_id),256)" in sql
    assert "SHA2(CONCAT('legacy-log:',id),256)" in sql
    assert "SHA2(CONCAT('legacy-ledger:',l.user_id),256)" in sql

def test_recovery_type_normalization_preserves_size_precision_and_binary_ids():
    normal=load_loyalty_revision().normalized_type
    assert normal('VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin')==normal('VARCHAR(64) COLLATE utf8mb4_bin')
    assert normal('VARCHAR(64) COLLATE utf8mb4_bin')!=normal('VARCHAR(64) COLLATE utf8mb4_unicode_ci')
    assert normal('NUMERIC(18, 4)')==normal('DECIMAL(18, 4)')
    assert normal('DECIMAL(18, 4)')!=normal('DECIMAL(18, 2)')
    assert normal('INTEGER(11)')==normal('INTEGER')
