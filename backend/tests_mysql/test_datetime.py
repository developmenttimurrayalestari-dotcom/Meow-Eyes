"""Validate the UTC boundary used when converting legacy ISO timestamps."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.dialects import mysql, sqlite

from mysql.base import UTCDateTime


def test_datetime_normalizes_offset_and_preserves_microseconds():
    column_type = UTCDateTime()
    source = datetime(2026, 11, 6, 14, 30, 10, 123456, tzinfo=timezone(timedelta(hours=7)))
    stored = column_type.process_bind_param(source, mysql.dialect())
    assert stored == datetime(2026, 11, 6, 7, 30, 10, 123456)
    assert stored.tzinfo is None
    restored = column_type.process_result_value(stored, mysql.dialect())
    assert restored == source
    assert restored.tzinfo == timezone.utc


@pytest.mark.parametrize("value", [datetime(2026, 11, 6), "2026-11-06T00:00:00", 0])
def test_unknown_timezone_or_unparsed_value_is_rejected(value):
    with pytest.raises(ValueError, match="timezone-aware"):
        UTCDateTime().process_bind_param(value, mysql.dialect())


def test_null_dates_remain_null_and_mysql_precision_is_explicit():
    column_type = UTCDateTime()
    assert column_type.process_bind_param(None, mysql.dialect()) is None
    assert column_type.process_result_value(None, mysql.dialect()) is None
    assert column_type.compile(dialect=mysql.dialect()) == "DATETIME(6)"
    assert column_type.compile(dialect=sqlite.dialect()) == "DATETIME"
