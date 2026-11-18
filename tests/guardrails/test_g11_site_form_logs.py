"""G11: the site form service writes no personal data to logs, on any path."""

import io
import logging
from collections.abc import Iterator

import httpx
import pytest
from exaktiv_site_form.delivery import deliver_pending
from exaktiv_site_form.logging import JsonFormatter
from exaktiv_site_form.main import create_app
from exaktiv_site_form.spam import make_token

from tests.unit.site_form_fakes import (
    PERSONAL_VALUES,
    TEST_IP,
    VALID_FORM,
    Clock,
    FakeMailer,
    FakeStore,
    make_settings,
)


@pytest.fixture
def log_output() -> Iterator[io.StringIO]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    # No MaskingFilter here on purpose: the code must not log personal data in the first place.
    root = logging.getLogger()
    old_level = root.level
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    yield stream
    root.removeHandler(handler)
    root.setLevel(old_level)


async def test_g11_logs_contain_no_personal_data(log_output: io.StringIO) -> None:
    clock = Clock()
    store, mailer = FakeStore(clock), FakeMailer()
    settings = make_settings()
    app = create_app(settings, store, mailer, clock=clock)
    token = make_token(settings.form_token_secret.get_secret_value(), clock() - 10)
    transport = httpx.ASGITransport(app=app, client=(TEST_IP, 1))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:

        def good() -> dict[str, str]:
            return {**VALID_FORM, "form_token": token}

        await client.post("/enquiries", json=good())  # success
        await client.post("/enquiries", json={**good(), "email": "bad", "name": ""})  # invalid
        await client.post("/enquiries", json={**good(), "website": "x"})  # honeypot
        await client.post("/enquiries", json={**VALID_FORM, "form_token": "forged"})  # bad token
        mailer.fail = True
        await client.post("/enquiries", json=good())  # mail failure
        await deliver_pending(store, mailer, settings)
        store.fail_on_insert = True
        await client.post("/enquiries", json=good())  # database failure
        store.fail_on_insert = False
        for _ in range(8):
            await client.post("/enquiries", json=good())  # rate limit
    output = log_output.getvalue()
    assert output, "the service logged nothing; the test would pass for the wrong reason"
    for value in (*PERSONAL_VALUES, TEST_IP):
        assert value not in output
    assert "@" not in output


async def test_g11_real_brevo_mailer_and_jobs_log_no_personal_data(log_output: io.StringIO) -> None:
    """Brevo answers with an error body that echoes the address. The service must not log it."""
    from exaktiv_site_form.jobs import run_job
    from exaktiv_site_form.mail import BrevoMailer
    from exaktiv_site_form.models import EnquiryIn
    from exaktiv_site_form.validation import validate

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400, json={"code": "invalid_parameter", "message": PERSONAL_VALUES[1]}
        )

    mailer = BrevoMailer(
        "k",
        "noreply@example.test",
        "Exaktiv",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    store = FakeStore(Clock())
    parsed = validate(VALID_FORM)
    assert isinstance(parsed, EnquiryIn)
    await store.insert_enquiry(parsed)
    settings = make_settings()
    for _ in range(6):
        await run_job("retry-mail", store, mailer, settings)
    await run_job("retention", store, mailer, settings)
    output = log_output.getvalue()
    assert "mail_attempt_failed" in output and "enquiry_mail_failed" in output
    for value in PERSONAL_VALUES:
        assert value not in output
    assert "@" not in output
