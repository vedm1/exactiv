"""Smoke workflow: one row in Postgres and one object in MinIO."""

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow

# Activity-only imports (database, S3) must not load inside the workflow sandbox.
with workflow.unsafe.imports_passed_through():
    import asyncpg  # type: ignore[import-untyped]
    from exaktiv_core.settings import get_settings
    from exaktiv_core.storage import ensure_bucket, s3_client

# Throwaway table. EXK1 adds Alembic and drops it.
CREATE_SQL = (
    "CREATE TABLE IF NOT EXISTS smoke_runs "
    "(id text PRIMARY KEY, created_at timestamptz NOT NULL DEFAULT now())"
)
INSERT_SQL = "INSERT INTO smoke_runs (id) VALUES ($1) ON CONFLICT DO NOTHING"


@dataclass
class SmokeResult:
    run_id: str
    row_written: bool
    object_key: str


@activity.defn
async def write_row(run_id: str) -> bool:
    s = get_settings()
    conn = await asyncpg.connect(
        host=s.postgres_host,
        port=s.postgres_port,
        database=s.postgres_db,
        user=s.postgres_user,
        password=s.postgres_password.get_secret_value(),
        **s.connect_kwargs(),
    )
    try:
        await conn.execute(CREATE_SQL)
        await conn.execute(INSERT_SQL, run_id)
        return bool(await conn.fetchval("SELECT count(*) FROM smoke_runs WHERE id = $1", run_id))
    finally:
        await conn.close()


@activity.defn
async def write_object(run_id: str) -> str:
    s = get_settings()
    client = s3_client(s)
    key = f"smoke/{run_id}.txt"

    def put() -> None:
        ensure_bucket(client, s.minio_bucket)
        client.put_object(Bucket=s.minio_bucket, Key=key, Body=b"exaktiv-smoke")

    await asyncio.to_thread(put)
    return key


@workflow.defn
class SmokeWorkflow:
    @workflow.run
    async def run(self, run_id: str) -> SmokeResult:
        timeout = timedelta(seconds=30)
        row = await workflow.execute_activity(write_row, run_id, start_to_close_timeout=timeout)
        key = await workflow.execute_activity(write_object, run_id, start_to_close_timeout=timeout)
        return SmokeResult(run_id=run_id, row_written=row, object_key=key)
