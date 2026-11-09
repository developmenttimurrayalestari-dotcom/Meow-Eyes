"""Alembic entry point for the staged MySQL migration.

Offline SQL generation needs neither secrets nor a running server. Online DDL
uses the same validated connection settings as the isolated bootstrap app.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from mysql.base import Base
from mysql import models  # noqa: F401: register all tables
from mysql.config import STRICT_SQL_MODE

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        dialect_name="mysql",
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        output = context.get_context().impl.static_output
        output("SET @meow_previous_sql_mode = @@SESSION.sql_mode;")
        output("SET @meow_previous_time_zone = @@SESSION.time_zone;")
        output("SET @meow_previous_innodb_strict_mode = @@SESSION.innodb_strict_mode;")
        output(f"SET SESSION sql_mode = '{STRICT_SQL_MODE}', time_zone = '+00:00', innodb_strict_mode = ON;")
        context.run_migrations()
        output("SET SESSION sql_mode = @meow_previous_sql_mode, time_zone = @meow_previous_time_zone, innodb_strict_mode = @meow_previous_innodb_strict_mode;")


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # Importing online-only dependencies here keeps offline generation isolated.
    from mysql.config import MySQLSettings
    from mysql.database import Database, check_server_compatibility

    database = Database(MySQLSettings.from_env())
    try:
        async with database.engine.connect() as connection:
            compatibility = await check_server_compatibility(connection)
            if not compatibility.ready:
                raise RuntimeError(
                    "MySQL 5.7.24-log target prerequisites failed: " + compatibility.reason
                )
            # The version query starts an implicit transaction. Finish it before
            # handing transaction management to Alembic.
            await connection.rollback()
            await connection.run_sync(do_run_migrations)
    finally:
        await database.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
