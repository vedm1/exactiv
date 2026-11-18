"""Health report types and the three component checks."""

import asyncio
from typing import Literal

import asyncpg  # type: ignore[import-untyped]
from pydantic import BaseModel, Field
from temporalio.api.workflowservice.v1 import DescribeNamespaceRequest
from temporalio.client import Client

from exaktiv_core.settings import Settings
from exaktiv_core.storage import ensure_bucket, s3_client

ComponentStatus = Literal["ok", "down"]
CHECK_TIMEOUT_S = 2.0


class HealthReport(BaseModel):
    postgres: ComponentStatus = "down"
    minio: ComponentStatus = "down"
    temporal: ComponentStatus = "down"
    # Exception class names only. No message, host or secret (G9, G11).
    detail: dict[str, str] = Field(default_factory=dict)

    @property
    def all_ok(self) -> bool:
        return self.postgres == self.minio == self.temporal == "ok"


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


async def _check_temporal(s: Settings) -> None:
    client = await Client.connect(s.temporal_address, namespace=s.temporal_namespace)
    await client.workflow_service.describe_namespace(
        DescribeNamespaceRequest(namespace=s.temporal_namespace)
    )


async def build_report(s: Settings) -> HealthReport:
    checks = {"postgres": _check_postgres, "minio": _check_minio, "temporal": _check_temporal}
    report = HealthReport()

    async def run(name: str) -> None:
        try:
            await asyncio.wait_for(checks[name](s), timeout=CHECK_TIMEOUT_S)
            setattr(report, name, "ok")
        except Exception as exc:  # noqa: BLE001 - any failure means "down"
            report.detail[name] = type(exc).__name__

    await asyncio.gather(*(run(n) for n in checks))
    return report
