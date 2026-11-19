"""One long-lived runner for the form jobs (EXW3).

Why: the shared Alloy collector does not capture the short-lived `jobs` containers, so no alert
could see `job_done`. This process stays up and logs to the container output. It runs the three
jobs: retry-mail every minute, purge-hits every hour, retention (W-G4) every day.
The log line `job_done job=retention` is the freshness signal: an alert fires when it is missing
for 26 hours. A failing job is logged as `job_failed` (job name and error class only, no personal
data, G11) and the loop goes on.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from exaktiv_site_form.jobs import run_job
from exaktiv_site_form.logging import configure_logging, log_event
from exaktiv_site_form.mail import BrevoMailer
from exaktiv_site_form.settings import SiteFormSettings
from exaktiv_site_form.store import PgStore

log = logging.getLogger("exaktiv_site_form.scheduler")
INTERVALS_S: dict[str, float] = {"retry-mail": 60, "purge-hits": 3600, "retention": 86400}
JOB_TIMEOUT_S = 120.0  # a hung call must not block the later runs
TICK_S = 5.0

Run = Callable[[str], Awaitable[int]]
Sleep = Callable[[float], Awaitable[None]]


async def run_scheduler(
    run: Run,
    *,
    now: Callable[[], float],
    sleep: Sleep,
    stop: Callable[[], bool] = lambda: False,
    intervals: dict[str, float] | None = None,
    timeout_s: float = JOB_TIMEOUT_S,
    tick_s: float = TICK_S,
) -> None:
    """Run every job at start, then each again after its interval. Returns when `stop()` is true."""
    every = intervals or INTERVALS_S
    due = {name: now() for name in every}
    while not stop():
        for name, when in sorted(due.items(), key=lambda item: item[1]):
            if now() < when:
                continue
            try:
                await asyncio.wait_for(run(name), timeout=timeout_s)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - one failing job must not stop the others
                log_event(log, logging.ERROR, "job_failed", job=name, error=type(exc).__name__)
            due[name] = now() + every[name]
        await sleep(tick_s)


async def _main() -> None:
    settings = SiteFormSettings()  # type: ignore[call-arg]
    store = PgStore()
    await store.open(settings.dsn(), **settings.connect_kwargs())
    mailer = BrevoMailer(
        settings.brevo_api_key.get_secret_value(),
        settings.mail_sender_email,
        settings.mail_sender_name,
    )
    loop = asyncio.get_running_loop()

    async def run(name: str) -> int:
        return await run_job(name, store, mailer, settings)

    log_event(log, logging.INFO, "scheduler_started", jobs=sorted(INTERVALS_S))
    try:
        await run_scheduler(run, now=loop.time, sleep=asyncio.sleep)
    finally:
        await store.close()


def main() -> int:
    configure_logging()
    asyncio.run(_main())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
