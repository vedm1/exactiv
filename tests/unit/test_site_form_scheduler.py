"""EXW3: the form job scheduler (retention freshness, W-G4)."""

import asyncio
import logging

import pytest
from exaktiv_site_form.scheduler import INTERVALS_S, run_scheduler


class Fake:
    """A clock that `sleep` moves forward, and a recorder of the runs."""

    def __init__(self, ticks: int) -> None:
        self.t = 0.0
        self.calls: list[tuple[str, float]] = []
        self.ticks = ticks
        self.fail: set[str] = set()
        self.hang: set[str] = set()

    def now(self) -> float:
        return self.t

    async def sleep(self, seconds: float) -> None:
        self.t += seconds
        self.ticks -= 1

    def stop(self) -> bool:
        return self.ticks <= 0

    async def run(self, name: str) -> int:
        self.calls.append((name, self.t))
        if name in self.fail:
            raise RuntimeError("synthetic failure with a sentinel: test.person@example.com")
        if name in self.hang:
            await asyncio.sleep(3600)
        return 0


def names(calls: list[tuple[str, float]], job: str) -> list[float]:
    return [t for n, t in calls if n == job]


async def go(f: Fake, **kw: object) -> None:
    await run_scheduler(f.run, now=f.now, sleep=f.sleep, stop=f.stop, **kw)  # type: ignore[arg-type]


async def test_every_job_runs_at_start() -> None:
    f = Fake(ticks=1)
    await go(f)
    assert {n for n, _ in f.calls} == set(INTERVALS_S)


async def test_w_g4_retention_runs_every_day_and_retry_mail_every_minute() -> None:
    f = Fake(ticks=int(2 * 86400 / 5) + 2)
    await go(f)
    retention = names(f.calls, "retention")
    assert len(retention) == 3 and retention[1] - retention[0] == pytest.approx(86400, abs=5)
    retry = names(f.calls, "retry-mail")
    assert retry[1] - retry[0] == pytest.approx(60, abs=5)
    assert len(names(f.calls, "purge-hits")) in {48, 49, 50}


async def test_a_failing_job_is_logged_without_data_and_the_others_still_run(
    caplog: pytest.LogCaptureFixture,
) -> None:
    f = Fake(ticks=30)
    f.fail = {"retention"}
    with caplog.at_level(logging.INFO):
        await go(f)
    assert len(names(f.calls, "retry-mail")) >= 2
    failed = [r for r in caplog.records if r.getMessage() == "job_failed"]
    assert failed and failed[0].fields == {"job": "retention", "error": "RuntimeError"}  # type: ignore[attr-defined]
    text = " ".join(f"{r.getMessage()} {getattr(r, 'fields', '')}" for r in caplog.records)
    assert "test.person" not in text and "sentinel" not in text  # G11


async def test_a_failing_job_is_tried_again_after_its_interval_not_in_a_loop() -> None:
    f = Fake(ticks=int(3 * 86400 / 5) + 2)
    f.fail = {"retention"}
    await go(f)
    assert len(names(f.calls, "retention")) == 4  # start, day 1, day 2, day 3


async def test_a_hung_job_times_out_and_does_not_block_the_loop() -> None:
    f = Fake(ticks=40)
    f.hang = {"purge-hits"}
    await go(f, timeout_s=0.05)
    assert len(names(f.calls, "retry-mail")) >= 2
