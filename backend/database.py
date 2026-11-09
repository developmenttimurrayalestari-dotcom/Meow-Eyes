"""MySQL application lifecycle; explicit SQL transactions and no Mongo fallback."""
from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from mysql.config import MySQLSettings
from mysql.database import Database, ReadinessResult

_database: Database | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def configure_session_factory(factory: async_sessionmaker[AsyncSession] | None) -> None:
    """Inject an isolated test factory; caller owns engine disposal and reset."""
    global _session_factory
    _session_factory = factory


def get_database() -> Database:
    global _database
    if _database is None:
        _database = Database(MySQLSettings.from_env())
    return _database


async def initialize(settings: MySQLSettings | None = None) -> ReadinessResult:
    global _database
    if _database is None:
        _database = Database(settings or MySQLSettings.from_env())
    return await _database.check_readiness()


def _factory() -> async_sessionmaker[AsyncSession]:
    return _session_factory or get_database().session_factory


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Commit one complete unit of work; rollback all writes on any exception.

    Flush before selecting pending rows (autoflush is disabled). Do not share
    this session among concurrent tasks or hold locks during network requests.
    """
    async with _factory()() as session:
        async with session.begin():
            yield session


@asynccontextmanager
async def read_session() -> AsyncIterator[AsyncSession]:
    """Close/rollback the read session; never implicitly commit writes."""
    async with _factory()() as session:
        yield session


async def close_client() -> None:
    global _database
    if _database is not None:
        await _database.dispose()
        _database = None
