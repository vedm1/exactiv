"""Mail: the Mailer interface, the Brevo HTTP sender and the two fixed templates."""

import html
from dataclasses import dataclass
from typing import Protocol

import httpx

from exaktiv_site_form.models import DATA_REGION_LABELS, TOPIC_LABELS, EnquiryIn

BREVO_URL = "https://api.brevo.com/v3/smtp/email"  # The only outbound host of this service.
TIMEOUT_S = 5.0


class MailError(Exception):
    """A send failed. Carries the HTTP status (or None) and nothing else (G11)."""

    def __init__(self, status: int | None) -> None:
        super().__init__(f"mail send failed (status {status})")
        self.status = status


@dataclass(frozen=True)
class MailMessage:
    to_email: str
    subject: str
    text: str
    html: str
    reply_to: str | None = None


class Mailer(Protocol):
    async def send(self, message: MailMessage) -> None: ...


class BrevoMailer:
    def __init__(
        self,
        api_key: str,
        sender_email: str,
        sender_name: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._sender = {"email": sender_email, "name": sender_name}
        self._client = client or httpx.AsyncClient(timeout=TIMEOUT_S)

    def __repr__(self) -> str:
        return "BrevoMailer()"

    async def send(self, message: MailMessage) -> None:
        body: dict[str, object] = {
            "sender": self._sender,
            "to": [{"email": message.to_email}],
            "subject": message.subject,
            "htmlContent": message.html,
            "textContent": message.text,
        }
        if message.reply_to:
            body["replyTo"] = {"email": message.reply_to}
        try:
            response = await self._client.post(
                BREVO_URL, json=body, headers={"api-key": self._api_key}
            )
        except httpx.HTTPError:
            raise MailError(None) from None
        if response.status_code != 201:
            raise MailError(response.status_code)


def build_team_mail(e: EnquiryIn, team_inbox: str) -> MailMessage:
    region = DATA_REGION_LABELS[e.data_region] if e.data_region else "Not given"
    lines = [
        ("Name", e.name),
        ("Email", e.email),
        ("Company", e.company),
        ("Role", e.role or "Not given"),
        ("Topic", TOPIC_LABELS[e.topic]),
        ("Data region", region),
    ]
    text = "\n".join(f"{k}: {v}" for k, v in lines) + f"\n\nMessage:\n{e.message}\n"
    rows = "".join(f"<p><b>{k}:</b> {html.escape(v)}</p>" for k, v in lines)
    body = f"{rows}<p><b>Message:</b></p><p>{html.escape(e.message).replace(chr(10), '<br>')}</p>"
    return MailMessage(
        to_email=team_inbox,
        subject=f"New website enquiry: {TOPIC_LABELS[e.topic]}",
        text=text,
        html=body,
        reply_to=e.email,
    )


def build_autoreply(e: EnquiryIn, privacy_url: str) -> MailMessage:
    text = (
        "Thank you for contacting Exaktiv.\n\n"
        "We received your message. We reply within 1 business day.\n\n"
        "We use your details only to reply to you. "
        f"Read our privacy notice: {privacy_url}\n"
    )
    body = (
        "<p>Thank you for contacting Exaktiv.</p>"
        "<p>We received your message. We reply within 1 business day.</p>"
        "<p>We use your details only to reply to you. "
        f'Read our <a href="{html.escape(privacy_url)}">privacy notice</a>.</p>'
    )
    return MailMessage(to_email=e.email, subject="We received your message", text=text, html=body)
