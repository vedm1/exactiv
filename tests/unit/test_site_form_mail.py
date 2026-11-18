import json

import httpx
import pytest
from exaktiv_site_form.mail import (
    BREVO_URL,
    BrevoMailer,
    MailError,
    MailMessage,
    build_autoreply,
    build_team_mail,
)
from exaktiv_site_form.models import EnquiryIn
from exaktiv_site_form.validation import validate

from tests.unit.site_form_fakes import PERSON_EMAIL, VALID_FORM

API_KEY = "brevo-sentinel-1b2c"


def enquiry(**over: str) -> EnquiryIn:
    result = validate({**VALID_FORM, **over})
    assert isinstance(result, EnquiryIn)
    return result


def message() -> MailMessage:
    return MailMessage(
        to_email="team@example.test", subject="S", text="t", html="<p>t</p>", reply_to=PERSON_EMAIL
    )


async def test_brevo_request_shape() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json={"messageId": "<x@y>"})

    mailer = BrevoMailer(
        API_KEY,
        "noreply@example.test",
        "Exaktiv",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    await mailer.send(message())
    request = seen[0]
    assert request.method == "POST"
    assert str(request.url) == BREVO_URL == "https://api.brevo.com/v3/smtp/email"
    assert request.headers["api-key"] == API_KEY
    body = json.loads(request.content)
    assert body["sender"] == {"email": "noreply@example.test", "name": "Exaktiv"}
    assert body["to"] == [{"email": "team@example.test"}]
    assert body["replyTo"] == {"email": PERSON_EMAIL}
    assert body["subject"] == "S"
    assert body["htmlContent"] == "<p>t</p>"
    assert body["textContent"] == "t"


@pytest.mark.parametrize("status", [400, 401, 429, 500, 200])
async def test_brevo_error_raises_mail_error_with_status_only(status: int) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"code": "invalid_parameter", "message": PERSON_EMAIL})

    mailer = BrevoMailer(
        API_KEY,
        "noreply@example.test",
        "Exaktiv",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(MailError) as info:
        await mailer.send(message())
    assert info.value.status == status
    assert PERSON_EMAIL not in str(info.value)
    assert API_KEY not in repr(mailer)


async def test_brevo_network_error_raises_mail_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom " + PERSON_EMAIL)

    mailer = BrevoMailer(
        API_KEY,
        "noreply@example.test",
        "Exaktiv",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(MailError) as info:
        await mailer.send(message())
    assert info.value.status is None
    assert PERSON_EMAIL not in str(info.value)


def test_team_mail_has_fixed_subject_and_reply_to() -> None:
    mail = build_team_mail(enquiry(), "team@example.test")
    assert mail.to_email == "team@example.test"
    assert mail.reply_to == PERSON_EMAIL
    assert mail.subject == "New website enquiry: Legacy modernisation"
    assert "Test Person" not in mail.subject
    assert "MSG-SENTINEL-7c1e" in mail.text


def test_team_mail_html_is_escaped() -> None:
    mail = build_team_mail(
        enquiry(message="<script>alert(1)</script> and some more text here"), "team@example.test"
    )
    assert "<script>" not in mail.html
    assert "&lt;script&gt;" in mail.html


def test_autoreply_goes_to_sender_and_does_not_echo_message() -> None:
    mail = build_autoreply(enquiry(), "https://site.example.test/privacy/")
    assert mail.to_email == PERSON_EMAIL
    assert mail.reply_to is None
    assert "1 business day" in mail.text
    assert "https://site.example.test/privacy/" in mail.text
    assert "MSG-SENTINEL-7c1e" not in mail.text + mail.html
