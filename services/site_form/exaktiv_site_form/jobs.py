"""Jobs for a timer or cron (EXW2): retention (daily), retry-mail (every minute), purge-hits."""

import asyncio
import logging
import sys

from exaktiv_site_form.delivery import deliver_pending
from exaktiv_site_form.logging import configure_logging, log_event
from exaktiv_site_form.mail import BrevoMailer, Mailer
from exaktiv_site_form.settings import SiteFormSettings
from exaktiv_site_form.store import PgStore, Store

log = logging.getLogger("exaktiv_site_form.jobs")
JOBS = ("retention", "retry-mail", "purge-hits")
HITS_MAX_AGE_S = 3600


async def run_job(name: str, store: Store, mailer: Mailer, settings: SiteFormSettings) -> int:
    if name == "retention":
        count = await store.delete_expired()  # W-G4
    elif name == "retry-mail":
        count = await deliver_pending(store, mailer, settings)
    elif name == "purge-hits":
        count = await store.purge_hits(HITS_MAX_AGE_S)
    else:
        raise ValueError(f"unknown job: {name}")
    log_event(log, logging.INFO, "job_done", job=name, count=count)  # a count, no personal data
    return count


async def _main(name: str) -> None:
    settings = SiteFormSettings()  # type: ignore[call-arg]
    store = PgStore()
    await store.open(settings.dsn())
    mailer = BrevoMailer(
        settings.brevo_api_key.get_secret_value(),
        settings.mail_sender_email,
        settings.mail_sender_name,
    )
    try:
        await run_job(name, store, mailer, settings)
    finally:
        await store.close()


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in JOBS:
        print(f"usage: python -m exaktiv_site_form.jobs {{{'|'.join(JOBS)}}}", file=sys.stderr)
        return 2
    configure_logging()
    asyncio.run(_main(argv[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
