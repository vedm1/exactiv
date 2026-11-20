"""Smoke workflow: one row in Postgres and one object in MinIO (DBOS)."""

import asyncio
from dataclasses import asdict, dataclass

import asyncpg  # type: ignore[import-untyped]
from dbos import DBOS
from exaktiv_core.settings import Settings, get_settings
from exaktiv_core.storage import ensure_bucket, s3_client

# Throwaway table. EXK1 drops it.
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

    def to_dict(self) -> dict[str, object]:
        # IDs and keys only. No personal data in workflow output (G11).
        return asdict(self)


def put_smoke_object(s: Settings, key: str) -> None:
    client = s3_client(s)
    ensure_bucket(client, s.minio_bucket)
    client.put_object(Bucket=s.minio_bucket, Key=key, Body=b"exaktiv-smoke")


@DBOS.step(retries_allowed=True, max_attempts=3, interval_seconds=0.1)
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


@DBOS.step(retries_allowed=True, max_attempts=3, interval_seconds=0.1)
async def write_object(run_id: str) -> str:
    s = get_settings()
    key = f"smoke/{run_id}.txt"
    await asyncio.to_thread(put_smoke_object, s, key)
    return key


@DBOS.workflow()
async def smoke_workflow(run_id: str) -> dict[str, object]:
    row = await write_row(run_id)
    key = await write_object(run_id)
    return SmokeResult(run_id=run_id, row_written=row, object_key=key).to_dict()


async def run_smoke_workflow(run_id: str) -> SmokeResult:
    """Run the workflow and wait. Set the workflow ID with `SetWorkflowID` for idempotency."""
    return SmokeResult(**await smoke_workflow(run_id))  # type: ignore[arg-type]
