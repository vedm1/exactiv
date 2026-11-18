"""Alembic environment (async, asyncpg). The URL comes from PostgresSettings (G9)."""

import asyncio

from alembic import context
from exaktiv_core.db import PostgresSettings
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config
target_metadata = None  # Hand-written revisions, no autogenerate.


def _url() -> str:
    dsn = config.attributes.get("dsn") or PostgresSettings().dsn()  # type: ignore[call-arg]
    return str(dsn).replace("postgresql://", "postgresql+asyncpg://", 1)


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_online() -> None:
    engine = create_async_engine(_url(), poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    context.configure(url=_url(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(_run_online())
