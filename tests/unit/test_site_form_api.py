import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
import pytest
from exaktiv_site_form.delivery import deliver_pending
from exaktiv_site_form.mail import MailError, MailMessage
from exaktiv_site_form.main import create_app
from exaktiv_site_form.spam import make_token

from tests.unit.site_form_fakes import (
    PERSON_EMAIL,
    TEST_IP,
    VALID_FORM,
    Clock,
    FakeMailer,
    FakeStore,
    make_settings,
)


@dataclass
class Env:
    client: httpx.AsyncClient
    store: FakeStore
    mailer: FakeMailer
    clock: Clock

    def token(self, age: float = 10) -> str:
        return make_token(make_settings().form_token_secret.get_secret_value(), self.clock() - age)

    async def post(self, data: dict[str, str] | None = None, **kw: object) -> httpx.Response:
        body = {"form_token": self.token(), **(VALID_FORM if data is None else data)}
        return await self.client.post("/enquiries", json=body, **kw)  # type: ignore[arg-type]


@pytest.fixture
async def env() -> AsyncIterator[Env]:
    clock = Clock()
    store, mailer = FakeStore(clock), FakeMailer()
    app = create_app(make_settings(), store, mailer, clock=clock)
    transport = httpx.ASGITransport(app=app, client=(TEST_IP, 4242))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        yield Env(client, store, mailer, clock)


async def test_valid_submission_stores_and_sends_both_mails(env: Env) -> None:
    response = await env.post()
    assert response.status_code == 201
    assert response.json() == {"status": "received"}
    assert len(env.store.rows) == 1
    assert [m.to_email for m in env.mailer.sent] == ["team@example.test", PERSON_EMAIL]
    assert env.mailer.sent[0].reply_to == PERSON_EMAIL
    assert env.store.rows[0].team_notified and env.store.rows[0].autoreply_sent


@pytest.mark.parametrize("field", ["name", "email", "company", "topic", "message"])
async def test_missing_required_field_returns_field_error_and_stores_nothing(
    env: Env, field: str
) -> None:
    data = {k: v for k, v in VALID_FORM.items() if k != field}
    response = await env.post(data)
    assert response.status_code == 422
    errors = response.json()["errors"]
    assert [(e["field"], e["code"]) for e in errors] == [(field, "required")]
    assert env.store.rows == [] and env.mailer.sent == []


async def test_g11_validation_response_does_not_echo_input(env: Env) -> None:
    response = await env.post({**VALID_FORM, "email": "ECHO-SENTINEL", "name": "x"})
    assert response.status_code == 422
    assert "ECHO-SENTINEL" not in response.text


async def test_honeypot_filled_drops_silently(env: Env) -> None:
    ok = await env.post()
    env.store.rows.clear()
    env.mailer.sent.clear()
    response = await env.post({**VALID_FORM, "website": "https://spam.example.test"})
    assert (response.status_code, response.json()) == (ok.status_code, ok.json())
    assert env.store.rows == [] and env.mailer.sent == []


async def test_too_fast_or_bad_token_is_dropped(env: Env) -> None:
    for token in (env.token(age=1), "forged.token", env.token(age=8000)):
        response = await env.client.post("/enquiries", json={**VALID_FORM, "form_token": token})
        assert response.status_code == 201
    assert env.store.rows == [] and env.mailer.sent == []


async def test_missing_token_is_stored_under_stricter_limit(env: Env) -> None:
    statuses = []
    for _ in range(3):
        r = await env.client.post("/enquiries", json=VALID_FORM)
        statuses.append(r.status_code)
    assert statuses == [201, 201, 429]
    assert len(env.store.rows) == 2


async def test_sixth_submission_in_ten_minutes_is_refused(env: Env) -> None:
    statuses = [(await env.post()).status_code for _ in range(6)]
    assert statuses == [201] * 5 + [429]
    refused = await env.post()
    assert refused.headers["retry-after"]
    assert refused.json() == {"error": "rate_limited"}
    env.clock.advance(601)
    assert (await env.post()).status_code == 201


async def test_invalid_attempts_count_toward_rate_limit(env: Env) -> None:
    for _ in range(5):
        await env.post({})
    assert (await env.post()).status_code == 429


async def test_form_client_gets_303_and_no_values_in_url(env: Env) -> None:
    body = urlencode({"form_token": env.token(), **VALID_FORM})
    headers = {"content-type": "application/x-www-form-urlencoded"}
    ok = await env.client.post("/enquiries", content=body, headers=headers)
    assert ok.status_code == 303
    assert ok.headers["location"] == "https://site.example.test/contact/thanks/"
    bad = urlencode({"form_token": env.token(), **{**VALID_FORM, "name": "", "email": "x"}})
    err = await env.client.post("/enquiries", content=bad, headers=headers)
    assert err.status_code == 303
    location = err.headers["location"]
    # EXW1-ui: a path with no query string. The static page cannot read a query, and no value may
    # travel in a URL (G11).
    assert location == "https://site.example.test/contact/problem/"
    assert "?" not in location and "Test" not in location


async def test_service_redirects_to_problem_path_without_values(env: Env) -> None:
    headers = {"content-type": "application/x-www-form-urlencoded"}
    for _ in range(5):
        body = urlencode({"form_token": env.token()})
        await env.client.post("/enquiries", content=body, headers=headers)
    limited = await env.client.post(
        "/enquiries", content=urlencode({"form_token": env.token(), **VALID_FORM}), headers=headers
    )
    assert limited.status_code == 303
    assert limited.headers["location"] == "https://site.example.test/contact/problem/"


async def test_oversize_body_returns_413(env: Env) -> None:
    response = await env.client.post("/enquiries", content=b"a=" + b"x" * 20000)
    assert response.status_code == 413


async def test_malformed_json_returns_400(env: Env) -> None:
    response = await env.client.post(
        "/enquiries", content=b"{not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 400


async def test_form_token_endpoint(env: Env) -> None:
    response = await env.client.get("/form-token")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    token = response.json()["token"]
    env.clock.advance(5)
    r = await env.client.post("/enquiries", json={**VALID_FORM, "form_token": token})
    assert r.status_code == 201 and len(env.store.rows) == 1


async def test_no_set_cookie_header_anywhere(env: Env) -> None:
    for response in (
        await env.client.get("/form-token"),
        await env.client.get("/health"),
        await env.post(),
        await env.post({}),
    ):
        assert "set-cookie" not in response.headers


async def test_mail_failure_keeps_row_and_client_still_gets_201(env: Env) -> None:
    env.mailer.fail = True
    response = await env.post()
    assert response.status_code == 201
    row = env.store.rows[0]
    assert not row.team_notified and row.mail_attempts == 1
    env.mailer.fail = False
    await deliver_pending(env.store, env.mailer, make_settings())
    assert row.team_notified and row.autoreply_sent
    assert len(env.mailer.sent) == 2


async def test_retry_stops_after_five_attempts(env: Env) -> None:
    env.mailer.fail = True
    await env.post()
    for _ in range(10):
        await deliver_pending(env.store, env.mailer, make_settings())
    assert env.store.rows[0].mail_attempts == 5


async def test_store_failure_returns_500_without_leaking(env: Env) -> None:
    env.store.fail_on_insert = True
    response = await env.post()
    assert response.status_code == 500
    assert response.json() == {"error": "server_error"}
    for leak in (PERSON_EMAIL, "Test Person", "MSG-SENTINEL"):
        assert leak not in response.text


async def test_health_ok(env: Env) -> None:
    assert (await env.client.get("/health")).json() == {"status": "ok"}


def test_json_body_must_be_object() -> None:
    assert json.loads("[]") == []  # guard for the next test's intent


async def test_json_array_body_is_400(env: Env) -> None:
    response = await env.client.post("/enquiries", json=["a"])
    assert response.status_code == 400


async def test_concurrent_posts_do_not_break_fake(env: Env) -> None:
    results = await asyncio.gather(*(env.post() for _ in range(3)))
    assert [r.status_code for r in results] == [201, 201, 201]


async def test_non_ascii_token_gets_201_not_500(env: Env) -> None:
    response = await env.client.post("/enquiries", json={**VALID_FORM, "form_token": "1.é"})
    assert response.status_code == 201
    assert env.store.rows == []


async def test_non_string_honeypot_counts_as_filled(env: Env) -> None:
    response = await env.post({**VALID_FORM, "website": 1})  # type: ignore[dict-item]
    assert response.status_code == 201
    assert env.store.rows == []


async def test_deeply_nested_json_is_400_not_500(env: Env) -> None:
    body = b"[" * 5000 + b"]" * 5000
    response = await env.client.post(
        "/enquiries", content=body, headers={"content-type": "application/json"}
    )
    assert response.status_code == 400


async def test_failed_team_mail_does_not_block_autoreply(env: Env) -> None:
    class TeamFails(FakeMailer):
        async def send(self, message: MailMessage) -> None:
            if message.to_email == "team@example.test":
                raise MailError(400)
            await super().send(message)

    env.mailer = TeamFails()
    app = create_app(make_settings(), env.store, env.mailer, clock=env.clock)
    transport = httpx.ASGITransport(app=app, client=(TEST_IP, 4242))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        await client.post("/enquiries", json={**VALID_FORM, "form_token": env.token()})
    row = env.store.rows[0]
    assert row.autoreply_sent and not row.team_notified


async def test_db_error_in_background_delivery_is_contained(env: Env) -> None:
    async def boom(enquiry_id: object) -> int:
        raise RuntimeError(f"db error with {PERSON_EMAIL}")

    env.store.record_mail_attempt = boom  # type: ignore[method-assign]
    response = await env.post()
    assert response.status_code == 201
