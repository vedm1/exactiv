import asyncio
import uuid

import asyncpg  # type: ignore[import-untyped]
import pytest
from exaktiv_core.settings import Settings
from exaktiv_core.storage import s3_client
from exaktiv_worker.smoke import SmokeResult, SmokeWorkflow
from exaktiv_worker.worker import ACTIVITIES, WORKFLOWS
from temporalio.client import Client
from temporalio.worker import Worker

pytestmark = pytest.mark.integration


async def run_smoke(s: Settings, run_id: str) -> SmokeResult:
    client = await Client.connect(s.temporal_address, namespace=s.temporal_namespace)
    async with Worker(
        client, task_queue=s.temporal_task_queue, workflows=WORKFLOWS, activities=ACTIVITIES
    ):
        return await client.execute_workflow(
            SmokeWorkflow.run,
            run_id,
            id=f"smoke-{uuid.uuid4()}",
            task_queue=s.temporal_task_queue,
        )


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


async def test_smoke_workflow(stack_settings: Settings) -> None:
    run_id = f"run-{uuid.uuid4()}"
    result = await run_smoke(stack_settings, run_id)
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


async def test_smoke_workflow_retry_is_safe(stack_settings: Settings) -> None:
    run_id = f"run-{uuid.uuid4()}"
    await run_smoke(stack_settings, run_id)
    await run_smoke(stack_settings, run_id)
    assert await count_rows(stack_settings, run_id) == 1
