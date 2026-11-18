"""Fakes and synthetic data for the site form tests. All personal data here is invented (G8)."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from exaktiv_site_form.mail import MailError, MailMessage
from exaktiv_site_form.models import EnquiryIn, PendingMail
from exaktiv_site_form.settings import SiteFormSettings

# Synthetic person on the reserved domain example.com (RFC 2606). No real data.
PERSON_NAME = "Test Person"
PERSON_EMAIL = "test.person@example.com"
PERSON_COMPANY = "Example Test Ltd"
MESSAGE_SENTINEL = "MSG-SENTINEL-7c1e"
PHONE_SENTINEL = "+00 000 000000"
TEST_IP = "203.0.113.7"  # TEST-NET-3, reserved for documentation

VALID_FORM: dict[str, str] = {
    "name": PERSON_NAME,
    "email": PERSON_EMAIL,
    "company": PERSON_COMPANY,
    "role": "Tester",
    "topic": "legacy_modernisation",
    "data_region": "eu_uk",
    "message": f"{MESSAGE_SENTINEL} please call {PHONE_SENTINEL} about a modernisation pilot.",
}
PERSONAL_VALUES = (PERSON_NAME, PERSON_EMAIL, PERSON_COMPANY, MESSAGE_SENTINEL, PHONE_SENTINEL)


def make_settings(**over: object) -> SiteFormSettings:
    values: dict[str, object] = {
        "_env_file": None,
        "postgres_password": "pw-sentinel-9f3a",
        "brevo_api_key": "brevo-sentinel-1b2c",
        "ip_hash_secret": "iphash-sentinel-3d4e",
        "form_token_secret": "token-sentinel-5f6a",
        "mail_sender_email": "noreply@example.test",
        "team_inbox_email": "team@example.test",
        "site_base_url": "https://site.example.test",
    }
    values.update(over)
    return SiteFormSettings(**values)  # type: ignore[arg-type]


class Clock:
    def __init__(self, start: float = 1_800_000_000.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


@dataclass
class Row:
    id: uuid.UUID
    enquiry: EnquiryIn
    created_at: float
    team_notified: bool = False
    autoreply_sent: bool = False
    mail_attempts: int = 0


@dataclass
class FakeStore:
    clock: Callable[[], float]
    rows: list[Row] = field(default_factory=list)
    hits: list[tuple[str, float]] = field(default_factory=list)
    fail_on_insert: bool = False

    async def check_and_record_hit(self, ip_hash: str, limit: int, window_s: int) -> bool:
        now = self.clock()
        recent = [h for h in self.hits if h[0] == ip_hash and h[1] > now - window_s]
        if len(recent) >= limit:
            return False
        self.hits.append((ip_hash, now))
        return True

    async def insert_enquiry(self, e: EnquiryIn) -> uuid.UUID:
        if self.fail_on_insert:
            raise RuntimeError(f"Failing row contains ({e.name}, {e.email}, {e.message})")
        row = Row(uuid.uuid4(), e, self.clock())
        self.rows.append(row)
        return row.id

    async def get_pending_mail(self, max_attempts: int) -> list[PendingMail]:
        return [
            PendingMail(r.id, r.enquiry, not r.team_notified, not r.autoreply_sent)
            for r in self.rows
            if (not r.team_notified or not r.autoreply_sent) and r.mail_attempts < max_attempts
        ]

    async def record_mail_attempt(self, enquiry_id: uuid.UUID) -> int:
        row = self._row(enquiry_id)
        row.mail_attempts += 1
        return row.mail_attempts

    async def mark_team_notified(self, enquiry_id: uuid.UUID) -> None:
        self._row(enquiry_id).team_notified = True

    async def mark_autoreply_sent(self, enquiry_id: uuid.UUID) -> None:
        self._row(enquiry_id).autoreply_sent = True

    async def delete_expired(self) -> int:
        return 0

    async def purge_hits(self, older_than_s: int) -> int:
        return 0

    def _row(self, enquiry_id: uuid.UUID) -> Row:
        return next(r for r in self.rows if r.id == enquiry_id)


@dataclass
class FakeMailer:
    sent: list[MailMessage] = field(default_factory=list)
    fail: bool = False

    async def send(self, message: MailMessage) -> None:
        if self.fail:
            raise MailError(503)
        self.sent.append(message)
