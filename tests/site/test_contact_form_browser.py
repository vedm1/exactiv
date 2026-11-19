"""EXW1-ui: the contact form in a real browser against the real service (fake store and mailer).

PRD-W section 7 acceptance criteria 1 to 5, the no-JavaScript path, the keyboard path, W-G3 and G11.
Needs Chromium (marker site_browser). The service runs in a thread and also serves site/dist, so the
redirects of the service land on the real pages.
"""

import socket
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import build_site
import pytest
import uvicorn
from exaktiv_site_form.main import create_app
from exaktiv_site_form.spam import make_token
from playwright.sync_api import Browser, Page, sync_playwright
from starlette.staticfiles import StaticFiles

from tests.unit.site_form_fakes import (
    PERSON_EMAIL,
    PERSONAL_VALUES,
    VALID_FORM,
    FakeMailer,
    FakeStore,
    make_settings,
)

pytestmark = pytest.mark.site_browser
ROOT = build_site.ROOT


@dataclass
class Served:
    base: str
    store: FakeStore
    mailer: FakeMailer


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("formbrowser") / "dist"
    build_site.build(ROOT / "site", ROOT / "brand", out)
    return out


@pytest.fixture(scope="module")
def browser() -> Iterator[Browser]:
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except Exception as exc:  # noqa: BLE001
            import os

            if os.environ.get("CI"):
                raise
            pytest.skip(f"Chromium missing: {exc}")
        yield b
        b.close()


@pytest.fixture
def served(dist: Path) -> Iterator[Served]:
    """A fresh service per test, so the rate limit starts empty."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    store, mailer = FakeStore(time.time), FakeMailer()
    app = create_app(make_settings(site_base_url=base), store, mailer)
    app.mount("/", StaticFiles(directory=str(dist), html=True))
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", access_log=False)
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    assert server.started, "test server did not start"
    try:
        yield Served(base, store, mailer)
    finally:
        server.should_exit = True
        thread.join(timeout=5)


def record_requests(page: Page) -> list[str]:
    urls: list[str] = []
    page.on("request", lambda r: urls.append(r.url))
    return urls


def fill(page: Page, data: dict[str, str] | None = None) -> None:
    values = {**VALID_FORM, **(data or {})}
    page.fill("#f-name", values["name"])
    page.fill("#f-email", values["email"])
    page.fill("#f-company", values["company"])
    page.fill("#f-role", values.get("role", ""))
    page.select_option("#f-topic", values["topic"])
    page.select_option("#f-data_region", values.get("data_region", ""))
    page.fill("#f-message", values["message"])


def test_valid_submission_waits_for_the_token_then_confirms(
    served: Served, browser: Browser
) -> None:
    """PRD-W AC1, and the fast-submit case: a quick click still reaches the store."""
    page = browser.new_page()
    page.goto(served.base + "/contact/", wait_until="networkidle")
    fill(page)
    started = time.time()
    page.click("button[type=submit]")
    page.wait_for_url("**/contact/thanks/", timeout=15000)
    assert time.time() - started >= 2.5  # the script waited for the minimum fill time
    assert len(served.store.rows) == 1
    assert served.store.rows[0].enquiry.email == PERSON_EMAIL
    assert [m.to_email for m in served.mailer.sent] == ["team@example.test", PERSON_EMAIL]
    assert "1 business day" in page.content()


def test_missing_field_shows_error_next_to_field_and_sends_nothing(
    served: Served, browser: Browser
) -> None:
    """PRD-W AC2, with JavaScript on."""
    page = browser.new_page()
    page.goto(served.base + "/contact/", wait_until="networkidle")
    fill(page, {"name": "", "message": "too short"})
    page.click("button[type=submit]")
    name_error = page.locator("#f-name-error")
    assert name_error.is_visible() and name_error.inner_text().strip()
    assert page.locator("#f-message-error").is_visible()
    assert page.locator("#f-name").get_attribute("aria-invalid") == "true"
    assert page.evaluate("document.activeElement.id") == "f-name"  # focus on the first error
    assert not page.locator("#f-email-error").is_visible()
    page.wait_for_timeout(500)
    assert served.store.rows == [] and served.mailer.sent == []
    assert page.url.endswith("/contact/")


def test_server_errors_show_next_to_the_field(served: Served, browser: Browser) -> None:
    page = browser.new_page()
    page.goto(served.base + "/contact/", wait_until="networkidle")
    fill(page, {"email": "a@b"})  # valid for the browser, refused by the service
    page.click("button[type=submit]")
    page.wait_for_selector("#f-email-error:not([hidden])", timeout=15000)
    assert "valid email" in page.locator("#f-email-error").inner_text()
    assert served.store.rows == []


def test_honeypot_filled_shows_same_confirmation_and_stores_nothing(
    served: Served, browser: Browser
) -> None:
    """PRD-W AC3."""
    page = browser.new_page()
    page.goto(served.base + "/contact/", wait_until="networkidle")
    fill(page)
    page.evaluate("document.querySelector('[name=website]').value = 'http://spam.invalid'")
    page.click("button[type=submit]")
    page.wait_for_url("**/contact/thanks/", timeout=15000)
    assert served.store.rows == [] and served.mailer.sent == []


def test_sixth_submission_is_refused_with_a_message(served: Served, browser: Browser) -> None:
    """PRD-W AC4: five hits are used up, so the sixth, sent through the page, is refused."""
    secret = make_settings().form_token_secret.get_secret_value()
    page = browser.new_page()
    page.goto(served.base + "/contact/", wait_until="networkidle")
    for _ in range(5):
        status = page.evaluate(
            """async (token) => (await fetch('/enquiries', {method: 'POST',
              headers: {'Content-Type': 'application/json', Accept: 'application/json'},
              body: JSON.stringify({form_token: token})})).status""",
            make_token(secret, time.time() - 10),
        )
        assert status == 422
    fill(page)
    page.click("button[type=submit]")
    page.wait_for_selector("#form-status:not([hidden])", timeout=15000)
    assert "too many" in page.locator("#form-status").inner_text().lower()
    assert served.store.rows == []


def test_no_javascript_post_is_stored_and_lands_on_thanks(served: Served, browser: Browser) -> None:
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    page.goto(served.base + "/contact/")
    fill(page)
    page.click("button[type=submit]")
    page.wait_for_url("**/contact/thanks/", timeout=15000)
    assert len(served.store.rows) == 1  # no token: stored, under the stricter limit
    context.close()


def test_no_javascript_native_validation_blocks_an_empty_form(
    served: Served, browser: Browser
) -> None:
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    page.goto(served.base + "/contact/")
    page.click("button[type=submit]")
    page.wait_for_timeout(500)
    assert page.url.endswith("/contact/")
    assert served.store.rows == []
    context.close()


def test_no_javascript_server_error_lands_on_problem_page(served: Served, browser: Browser) -> None:
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    page.goto(served.base + "/contact/")
    fill(page, {"email": "a@b"})
    page.click("button[type=submit]")
    page.wait_for_url("**/contact/problem/", timeout=15000)
    assert "?" not in page.url
    assert page.locator("form").count() == 1
    assert served.store.rows == []
    context.close()


def test_g11_no_submitted_value_in_any_url_or_page_after_submit(
    served: Served, browser: Browser
) -> None:
    page = browser.new_page()
    urls = record_requests(page)
    page.goto(served.base + "/contact/", wait_until="networkidle")
    fill(page)
    page.click("button[type=submit]")
    page.wait_for_url("**/contact/thanks/", timeout=15000)
    page.wait_for_load_state("networkidle")
    for value in PERSONAL_VALUES:
        assert not any(value in u or value.replace(" ", "%20") in u for u in urls), value
        assert value not in page.content()
    assert not any("?" in u for u in urls if urlparse(u).path.startswith("/contact"))


def test_w_g3_form_pages_set_no_cookie_and_call_only_the_own_origin(
    served: Served, browser: Browser
) -> None:
    host = urlparse(served.base).netloc
    for path in ("/contact/", "/contact/thanks/", "/contact/problem/"):
        context = browser.new_context()
        page = context.new_page()
        urls = record_requests(page)
        page.goto(served.base + path, wait_until="networkidle")
        page.wait_for_timeout(300)
        assert context.cookies() == [], path
        assert page.evaluate("document.cookie") == "", path
        foreign = [u for u in urls if urlparse(u).netloc != host and not u.startswith("data:")]
        assert not foreign, f"{path}: {foreign}"
        context.close()


def test_keyboard_path_follows_the_form_order_and_skips_the_honeypot(
    served: Served, browser: Browser
) -> None:
    page = browser.new_page()
    page.goto(served.base + "/contact/", wait_until="networkidle")
    page.focus("#f-name")
    order = [page.evaluate("document.activeElement.name")]
    for _ in range(7):
        page.keyboard.press("Tab")
        order.append(page.evaluate("document.activeElement.name || document.activeElement.type"))
    assert order == [
        "name",
        "email",
        "company",
        "role",
        "topic",
        "data_region",
        "message",
        "submit",
    ]
    # The focused control has a visible outline (WCAG 2.4.7).
    page.focus("#f-name")
    outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
    assert outline != "none"
