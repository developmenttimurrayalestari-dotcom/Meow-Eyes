"""Isolated relational test store. SQLite does not test MySQL locking/DDL."""
from contextlib import asynccontextmanager
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from database import configure_session_factory
from mysql.base import Base
from mysql import models  # noqa: F401


@asynccontextmanager
async def isolated_database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    @event.listens_for(engine.sync_engine, "connect")
    def foreign_keys(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    configure_session_factory(factory)
    try:
        yield factory
    finally:
        configure_session_factory(None)
        await engine.dispose()
