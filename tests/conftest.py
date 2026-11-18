import pytest
from exaktiv_core.settings import Settings, get_settings


@pytest.fixture(scope="session")
def stack_settings() -> Settings:
    """Settings for the local compose stack. Reads .env (see scripts/make_env.sh)."""
    return get_settings()


# ---- site form (EXW1): a throwaway database per test, built by Alembic ----
import asyncio  # noqa: E402
import uuid  # noqa: E402
from collections.abc import AsyncIterator  # noqa: E402
from pathlib import Path  # noqa: E402

import asyncpg  # type: ignore[import-untyped]  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from exaktiv_core.db import PostgresSettings  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def alembic_config(dsn: str) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.attributes["dsn"] = dsn
    return cfg


@pytest.fixture
async def temp_dsn() -> AsyncIterator[str]:
    """An empty throwaway database on the compose Postgres. Dropped after the test."""
    pg = PostgresSettings()  # type: ignore[call-arg]
    name = f"exaktiv_test_{uuid.uuid4().hex[:12]}"
    admin = await asyncpg.connect(pg.dsn())
    try:
        await admin.execute(f'CREATE DATABASE "{name}"')
        yield pg.dsn(name)
    finally:
        await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await admin.close()


@pytest.fixture
async def migrated_dsn(temp_dsn: str) -> str:
    await asyncio.to_thread(command.upgrade, alembic_config(temp_dsn), "head")
    return temp_dsn


@pytest.fixture
async def pg_pool(migrated_dsn: str) -> AsyncIterator[asyncpg.Pool]:
    pool = await asyncpg.create_pool(migrated_dsn, min_size=1, max_size=12)
    try:
        yield pool
    finally:
        await pool.close()
