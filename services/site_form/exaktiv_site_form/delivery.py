"""Send the team mail and the automatic reply. Shared by the request and the retry job."""

import logging

from exaktiv_site_form.logging import log_event
from exaktiv_site_form.mail import Mailer, MailError, MailMessage, build_autoreply, build_team_mail
from exaktiv_site_form.models import PendingMail
from exaktiv_site_form.settings import SiteFormSettings
from exaktiv_site_form.store import Store

log = logging.getLogger("exaktiv_site_form.delivery")


async def deliver_one(
    store: Store, mailer: Mailer, settings: SiteFormSettings, pending: PendingMail
) -> None:
    """One delivery round. A failure is logged (ID and status only) and never raised.

    The two mails are independent: a failed team mail does not block the automatic reply.
    """
    enquiry_id = str(pending.id)
    try:
        attempt = await store.record_mail_attempt(pending.id)
        failed = False
        if pending.team_pending:
            failed |= not await _send(
                mailer,
                build_team_mail(pending.enquiry, settings.team_inbox_email),
                enquiry_id,
                attempt,
            )
            if not failed:
                await store.mark_team_notified(pending.id)
        if pending.reply_pending:
            privacy = f"{settings.site_base_url}/privacy/"
            ok = await _send(mailer, build_autoreply(pending.enquiry, privacy), enquiry_id, attempt)
            if ok:
                await store.mark_autoreply_sent(pending.id)
            failed |= not ok
        if failed and attempt >= settings.mail_max_attempts:
            log_event(log, logging.ERROR, "enquiry_mail_failed", enquiry_id=enquiry_id)
    except Exception as exc:  # noqa: BLE001 - class name only, the message may hold personal data
        log_event(
            log,
            logging.ERROR,
            "mail_delivery_error",
            enquiry_id=enquiry_id,
            error=type(exc).__name__,
        )


async def _send(mailer: Mailer, message: MailMessage, enquiry_id: str, attempt: int) -> bool:
    try:
        await mailer.send(message)
    except MailError as exc:
        log_event(
            log,
            logging.WARNING,
            "mail_attempt_failed",
            enquiry_id=enquiry_id,
            attempt=attempt,
            status=exc.status,
        )
        return False
    return True


async def deliver_pending(store: Store, mailer: Mailer, settings: SiteFormSettings) -> int:
    pending = await store.get_pending_mail(settings.mail_max_attempts)
    for item in pending:
        await deliver_one(store, mailer, settings, item)
    return len(pending)
