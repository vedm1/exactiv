"""Health report types and the three component checks."""

import asyncio
from typing import Literal

import asyncpg  # type: ignore[import-untyped]
import psycopg
from pydantic import BaseModel, Field

from exaktiv_core.settings import Settings
from exaktiv_core.storage import ensure_bucket, s3_client

ComponentStatus = Literal["ok", "down"]
CHECK_TIMEOUT_S = 2.0


class HealthReport(BaseModel):
    postgres: ComponentStatus = "down"
    minio: ComponentStatus = "down"
    dbos: ComponentStatus = "down"
    # Exception class names only. No message, host or secret (G9, G11).
    detail: dict[str, str] = Field(default_factory=dict)

    @property
    def all_ok(self) -> bool:
        return self.postgres == self.minio == self.dbos == "ok"


async def _check_postgres(s: Settings) -> None:
    conn = await asyncpg.connect(
        host=s.postgres_host,
        port=s.postgres_port,
        database=s.postgres_db,
        user=s.postgres_user,
        password=s.postgres_password.get_secret_value(),
        timeout=CHECK_TIMEOUT_S,
        **s.connect_kwargs(),
    )
    try:
        await conn.fetchval("SELECT 1")
    finally:
        await conn.close()


async def _check_minio(s: Settings) -> None:
    await asyncio.to_thread(ensure_bucket, s3_client(s), s.minio_bucket)


async def _check_dbos(s: Settings) -> None:
    url = s.dbos_system_url().replace("postgresql+psycopg://", "postgresql://", 1)
    conn = await psycopg.AsyncConnection.connect(url, connect_timeout=int(CHECK_TIMEOUT_S))
    async with conn:
        cur = await conn.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = 'dbos_migrations'",
            (s.dbos_system_schema,),
        )
        if await cur.fetchone() is None:
            raise LookupError("DBOS schema missing")


async def build_report(s: Settings) -> HealthReport:
    checks = {"postgres": _check_postgres, "minio": _check_minio, "dbos": _check_dbos}
    report = HealthReport()

    async def run(name: str) -> None:
        try:
            await asyncio.wait_for(checks[name](s), timeout=CHECK_TIMEOUT_S)
            setattr(report, name, "ok")
        except Exception as exc:  # noqa: BLE001 - any failure means "down"
            report.detail[name] = type(exc).__name__

    await asyncio.gather(*(run(n) for n in checks))
    return report
