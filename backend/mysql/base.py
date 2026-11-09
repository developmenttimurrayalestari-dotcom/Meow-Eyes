"""Shared SQLAlchemy metadata and explicit UTC datetime handling.

The business schema is independent of the legacy ``models.py`` Pydantic API
models and does not import MongoDB.  MySQL stores UTC without a time-zone tag;
application datetimes must be aware so an accidental local-time write fails.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any

from sqlalchemy import DateTime, MetaData, String, Table, Text
from sqlalchemy.dialects.mysql import DATETIME, MEDIUMTEXT, VARCHAR
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator

from . import ddl as _mysql57_ddl  # noqa: F401: register target-specific DDL


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """MySQL DATETIME(6), bound as UTC and returned as aware UTC.

    The driver returns naive MySQL datetimes; their interpretation is always
    UTC.  Import code must parse ISO strings and attach a verified source time
    zone *before* using this type.  It must not silently guess a missing zone.
    """

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "mysql":
            return dialect.type_descriptor(DATETIME(fsp=6))
        return dialect.type_descriptor(DateTime())

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("UTCDateTime requires a timezone-aware datetime")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def _scope(constraint: Any, table: Table) -> str:
    """Deterministic names below MySQL's 64-character identifier limit."""
    columns = "_".join(column.name for column in constraint.columns)
    scope = f"{table.name}_{columns}"
    elements = getattr(constraint, "elements", ())
    if elements:
        scope += "_" + "_".join(element.target_fullname.replace(".", "_") for element in elements)
    if len(scope) > 56:
        scope = scope[:43] + "_" + hashlib.sha256(scope.encode()).hexdigest()[:12]
    return scope


NAMING_CONVENTION = {
    "scope": _scope,
    "ix": "ix_%(scope)s",
    "uq": "uq_%(scope)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(scope)s",
    "pk": "pk_%(table_name)s",
}

# Existing public IDs are strings such as usr_0123456789abcdef.  Keeping them
# avoids changing URLs, sessions, imported references, and API payloads.
# Binary collation prevents otherwise distinct opaque IDs comparing equal.
ID = String(64).with_variant(VARCHAR(64, collation="utf8mb4_bin"), "mysql")
TOKEN = String(64).with_variant(VARCHAR(64, collation="utf8mb4_bin"), "mysql")
OPAQUE = String(191).with_variant(VARCHAR(191, collation="utf8mb4_bin"), "mysql")
CONTENT = Text().with_variant(MEDIUMTEXT(), "mysql")


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # MySQL 5.7 has no INSERT RETURNING. Fetch server defaults during awaited
    # flush(), not as implicit IO while serializing an ORM object afterwards.
    # This setting affects ORM loading only, never the immutable DDL history.
    __mapper_args__ = {"eager_defaults": True}

    @classmethod
    def __table_cls__(cls, *args: Any, **kwargs: Any) -> Table:
        kwargs.setdefault("mysql_engine", "InnoDB")
        kwargs.setdefault("mysql_charset", "utf8mb4")
        kwargs.setdefault("mysql_collate", "utf8mb4_unicode_ci")
        kwargs.setdefault("mysql_row_format", "DYNAMIC")
        return Table(*args, **kwargs)
