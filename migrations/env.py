"""Alembic environment (async, asyncpg). The URL comes from PostgresSettings (G9)."""

import asyncio
from typing import Any

from alembic import context
from exaktiv_core.db import PostgresSettings
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config
target_metadata = None  # Hand-written revisions, no autogenerate.


def _options() -> tuple[str, dict[str, Any]]:
    """Tests pass their own dsn (local, no TLS). A real run takes everything from settings."""
    dsn = config.attributes.get("dsn")
    if dsn:
        return str(dsn).replace("postgresql://", "postgresql+asyncpg://", 1), {}
    return PostgresSettings().sqlalchemy_options()


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_online() -> None:
    url, connect_args = _options()
    engine = create_async_engine(url, poolclass=pool.NullPool, connect_args=connect_args)
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    context.configure(url=_options()[0], literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(_run_online())
