import asyncio
import uuid

import asyncpg  # type: ignore[import-untyped]
import pytest
from dbos import DBOS, SetWorkflowID
from exaktiv_core.settings import Settings
from exaktiv_core.storage import s3_client
from exaktiv_worker import smoke
from exaktiv_worker.smoke import SmokeResult, run_smoke_workflow

pytestmark = pytest.mark.integration


async def run_smoke(run_id: str, workflow_id: str | None = None) -> SmokeResult:
    with SetWorkflowID(workflow_id or f"smoke-{uuid.uuid4()}"):
        return await run_smoke_workflow(run_id)


async def count_rows(s: Settings, run_id: str) -> int:
    conn = await asyncpg.connect(
        host=s.postgres_host,
        port=s.postgres_port,
        database=s.postgres_db,
        user=s.postgres_user,
        password=s.postgres_password.get_secret_value(),
    )
    try:
        return int(await conn.fetchval("SELECT count(*) FROM smoke_runs WHERE id = $1", run_id))
    finally:
        await conn.close()


async def test_smoke_workflow(stack_settings: Settings, dbos_runtime: None) -> None:
    run_id = f"run-{uuid.uuid4()}"
    result = await run_smoke(run_id)
    assert result.run_id == run_id
    assert result.row_written is True
    assert await count_rows(stack_settings, run_id) == 1
    obj = await asyncio.to_thread(
        s3_client(stack_settings).get_object,
        Bucket=stack_settings.minio_bucket,
        Key=result.object_key,
    )
    assert obj["Body"].read() == b"exaktiv-smoke"
    assert result.object_key == f"smoke/{run_id}.txt"


async def test_smoke_workflow_retry_is_safe(stack_settings: Settings, dbos_runtime: None) -> None:
    run_id = f"run-{uuid.uuid4()}"
    wid = f"smoke-{uuid.uuid4()}"
    first = await run_smoke(run_id, wid)
    second = await run_smoke(run_id, wid)
    assert first == second
    # A new workflow ID for the same run still writes one row (ON CONFLICT DO NOTHING).
    await run_smoke(run_id)
    assert await count_rows(stack_settings, run_id) == 1


async def test_smoke_workflow_recovers_after_step_failure(
    stack_settings: Settings, dbos_runtime: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_id = f"run-{uuid.uuid4()}"
    real_put = smoke.put_smoke_object
    calls = {"n": 0}

    def flaky(s: Settings, key: str) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("simulated")
        real_put(s, key)

    monkeypatch.setattr(smoke, "put_smoke_object", flaky)
    result = await run_smoke(run_id)
    assert calls["n"] == 2
    assert result.row_written is True
    assert await count_rows(stack_settings, run_id) == 1


async def test_dbos_schema_is_separate(stack_settings: Settings, dbos_runtime: None) -> None:
    conn = await asyncpg.connect(
        host=stack_settings.postgres_host,
        port=stack_settings.postgres_port,
        database=stack_settings.postgres_db,
        user=stack_settings.postgres_user,
        password=stack_settings.postgres_password.get_secret_value(),
    )
    try:
        assert await conn.fetchval(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'dbos' AND table_name = 'dbos_migrations'"
        )
        assert not await conn.fetchval(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name LIKE 'workflow_status%'"
        )
    finally:
        await conn.close()
    assert DBOS is not None
