"""EXK0b: Neon needs TLS. Every direct Postgres connection takes its ssl argument from settings."""

from typing import Any

import asyncpg  # type: ignore[import-untyped]
import pytest
from exaktiv_core import health
from exaktiv_core.db import PostgresSettings
from exaktiv_core.settings import Settings
from exaktiv_site_form.store import PgStore


def pg(**over: object) -> PostgresSettings:
    return PostgresSettings(_env_file=None, postgres_password="pw-sentinel", **over)  # type: ignore[arg-type,call-arg]


def test_db_ssl_kwargs_default_is_empty() -> None:
    assert pg().connect_kwargs() == {}


def test_db_ssl_kwargs_require_when_enabled() -> None:
    assert pg(postgres_ssl=True).connect_kwargs() == {"ssl": "require"}


def test_core_settings_inherit_the_ssl_setting() -> None:
    s = Settings(  # type: ignore[call-arg]
        _env_file=None,
        postgres_password="pw",  # type: ignore[arg-type]
        postgres_ssl=True,
        minio_access_key="a",  # type: ignore[arg-type]
        minio_secret_key="b",  # type: ignore[arg-type]
    )
    assert s.connect_kwargs() == {"ssl": "require"}
    assert "pw-sentinel" not in repr(pg(postgres_ssl=True))


async def test_health_check_passes_ssl_to_asyncpg(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    class Conn:
        async def fetchval(self, _: str) -> int:
            return 1

        async def close(self) -> None:
            return None

    async def fake_connect(**kwargs: Any) -> Conn:
        seen.update(kwargs)
        return Conn()

    monkeypatch.setattr(asyncpg, "connect", fake_connect)
    s = Settings(  # type: ignore[call-arg]
        _env_file=None,
        postgres_password="pw",  # type: ignore[arg-type]
        postgres_ssl=True,
        minio_access_key="a",  # type: ignore[arg-type]
        minio_secret_key="b",  # type: ignore[arg-type]
    )
    await health._check_postgres(s)
    assert seen["ssl"] == "require"


async def test_pgstore_open_passes_ssl_to_asyncpg(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    async def fake_pool(dsn: str, **kwargs: Any) -> object:
        seen.update(kwargs)
        return object()

    monkeypatch.setattr(asyncpg, "create_pool", fake_pool)
    await PgStore().open(pg().dsn(), **pg(postgres_ssl=True).connect_kwargs())
    assert seen["ssl"] == "require"
