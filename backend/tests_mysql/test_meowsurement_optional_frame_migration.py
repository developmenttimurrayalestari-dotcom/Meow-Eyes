"""The incremental nullable-frame migration preserves frozen history guards."""
from pathlib import Path
import subprocess

import pytest

from tests_mysql.test_migrations import offline
from mysql.check_integrity import load_meowsurement_revision


def test_optional_frame_export_only_relaxes_source_column_and_replaces_session_guards():
    sql = offline('upgrade', '20261109_0003:20261110_0004', '--sql')
    assert sql == (Path(__file__).resolve().parents[1] / 'sql/004_optional_customer_frame.sql').read_text(encoding='utf-8')
    assert 'MODIFY product_id VARCHAR(64) COLLATE utf8mb4_bin NULL' in sql
    assert sql.count('CREATE TRIGGER ') == 2
    assert sql.count('DROP TRIGGER IF EXISTS ') == 2
    assert 'Measurement source snapshots are immutable' in sql
    assert "spec_scope = 'manual' AND NEW.product_id IS NULL AND NEW.variant_id IS NULL" in sql
    assert "version_num='20261110_0004'" in sql
    for forbidden in ['DROP TABLE', 'DELETE FROM', 'TRUNCATE', 'FOREIGN_KEY_CHECKS']:
        assert forbidden not in sql
    revision = load_meowsurement_revision()
    assert revision.down_revision == '20261109_0003'


def test_optional_frame_downgrade_refuses_silent_data_loss():
    with pytest.raises(subprocess.CalledProcessError) as error:
        offline('downgrade', '20261110_0004:20261109_0003', '--sql')
    assert 'Manual-frame sessions may exist' in error.value.stderr
