"""Async SQLAlchemy connections targeting MySQL 5.7.24-log."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging
import re
from typing import AsyncIterator, Mapping, Any

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker, create_async_engine

from .config import MySQLSettings


logger = logging.getLogger("meow.mysql")
MYSQL_VERSION_FAMILY = (5, 7)
MINIMUM_MYSQL_VERSION = (5, 7, 24)
TARGET_MYSQL_VERSION = "5.7.24-log"
EXPECTED_SCHEMA_REVISION = "20261112_0012"


def supported_mysql_version(version: str) -> bool:
    """Accept MySQL 5.7.24+ within 5.7, including the server's -log suffix.

    The suffix is server metadata, not a separate SQLAlchemy dialect. New major
    versions and MariaDB require their own reviewed migration/runtime policy.
    """
    if "mariadb" in version.lower():
        return False
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+][A-Za-z0-9._-]+)?", version)
    if not match:
        return False
    parsed = tuple(map(int, match.groups()))
    return parsed[:2] == MYSQL_VERSION_FAMILY and parsed >= MINIMUM_MYSQL_VERSION


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    ready: bool
    reason: str


def innodb_compatibility(profile: Mapping[str, Any]) -> ReadinessResult:
    """Validate the existing server's index-storage prerequisites without writes.

    The schema explicitly requests DYNAMIC rows. Its widest composite utf8mb4
    key is 2552 bytes, so older 767-byte prefixes and 4/8 KiB pages cannot work.
    No application account changes these server-wide DBA settings.
    """
    def enabled(value: Any) -> bool:
        return str(value).strip().lower() in {"1", "on", "true"}

    if not enabled(profile.get("large_prefix")):
        return ReadinessResult(False, "innodb_large_prefix_required")
    try:
        page_size = int(profile.get("page_size", 0))
    except (ValueError, TypeError):
        return ReadinessResult(False, "innodb_page_size_unsupported")
    if page_size < 16384:
        return ReadinessResult(False, "innodb_page_size_unsupported")
    return ReadinessResult(True, "server_compatible")


async def check_server_compatibility(connection: AsyncConnection) -> ReadinessResult:
    """Read-only check shared by application readiness and Alembic preflight.

    Check the version first: MySQL8 removed innodb_large_prefix.
    This needs no application tables or trigger-inspection privileges and does
    not infer binary logging from the '-log' version suffix.
    """
    version = str((await connection.execute(text("SELECT VERSION()"))).scalar_one())
    if not supported_mysql_version(version):
        return ReadinessResult(False, "unsupported_mysql_version")
    result = await connection.execute(text(
        "SELECT @@global.innodb_large_prefix AS large_prefix, "
        "@@global.innodb_page_size AS page_size"
    ))
    return innodb_compatibility(result.mappings().one())


class Database:
    """Explicit lifecycle; no connection, table creation, or seed at import time."""

    def __init__(self, settings: MySQLSettings) -> None:
        self.settings = settings
        self.engine = create_async_engine(
            settings.sqlalchemy_url,
            connect_args=settings.connect_args(),
            pool_pre_ping=True,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            pool_timeout=settings.pool_timeout_seconds,
            pool_recycle=settings.pool_recycle_seconds,
            # MySQL5.7's native level also works with statement-format binary
            # logging; READ COMMITTED would require ROW/MIXED logging. Future
            # checkout services must use explicit locking and atomic writes.
            isolation_level="REPEATABLE READ",
            echo=False,
            hide_parameters=True,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Close every session; application services own their commit boundary.

        Write services must use `async with session.begin():` or explicitly call
        commit(). Successful dependency exit never commits automatically. This
        allows stock, order, payment, and ledger writes to share one transaction.
        """
        async with self.session_factory() as session:
            try:
                yield session
            except BaseException:
                await session.rollback()
                raise

    async def session_dependency(self) -> AsyncIterator[AsyncSession]:
        """FastAPI dependency available to the approved Step 2 repositories."""
        async with self.session() as session:
            yield session

    async def _probe(self) -> ReadinessResult:
        async with self.engine.connect() as connection:
            compatibility = await check_server_compatibility(connection)
            if not compatibility.ready:
                return compatibility
            result = await connection.execute(text("SELECT version_num FROM alembic_version"))
            revisions = set(result.scalars().all())
            if revisions != {EXPECTED_SCHEMA_REVISION}:
                return ReadinessResult(False, "schema_revision_mismatch")
            return ReadinessResult(True, "ready")

    async def check_readiness(self) -> ReadinessResult:
        """Check connectivity, MySQL5.7 storage settings and migration head.

        Return only safe reason codes. Driver exception text may contain host,
        account, SQL, or other sensitive values and is never returned or logged.
        """
        try:
            return await asyncio.wait_for(self._probe(), self.settings.health_timeout_seconds)
        except TimeoutError:
            return ReadinessResult(False, "database_timeout")
        except DBAPIError as exc:
            code = (getattr(exc.orig, "args", ()) or (None,))[0]
            if code == 1146:
                return ReadinessResult(False, "schema_not_initialized")
            logger.warning("MySQL readiness failed (%s)", type(exc).__name__)
            return ReadinessResult(False, "database_unavailable")
        except (SQLAlchemyError, OSError):
            logger.warning("MySQL readiness failed; connection unavailable")
            return ReadinessResult(False, "database_unavailable")

    async def dispose(self) -> None:
        await self.engine.dispose()
