"""Worker entry point: `uv run python -m exaktiv_worker.worker`."""

import asyncio
from collections.abc import Callable, Sequence
from typing import Any

from exaktiv_core.settings import get_settings
from temporalio.client import Client
from temporalio.worker import Worker

from exaktiv_worker.smoke import SmokeWorkflow, write_object, write_row

WORKFLOWS: Sequence[type] = [SmokeWorkflow]
ACTIVITIES: Sequence[Callable[..., Any]] = [write_row, write_object]


async def main() -> None:
    s = get_settings()
    client = await Client.connect(s.temporal_address, namespace=s.temporal_namespace)
    await Worker(
        client, task_queue=s.temporal_task_queue, workflows=WORKFLOWS, activities=ACTIVITIES
    ).run()


if __name__ == "__main__":
    asyncio.run(main())
