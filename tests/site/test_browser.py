"""EXD5 browser checks on the built site: 0 cookies, 0 third-party requests, page weight.

Needs Chromium: `uv run playwright install chromium`. Marker: site_browser (own CI job).
Locally the tests skip when Chromium is missing. In CI (CI=true) a missing browser is an error.
"""

import functools
import http.server
import os
import threading
from collections.abc import Iterator
from urllib.parse import urlparse

import build_site
import pytest
from playwright.sync_api import Browser, Response, sync_playwright

pytestmark = pytest.mark.site_browser

ROOT = build_site.ROOT
MAX_PAGE_BYTES = 1_000_000  # PRD-W section 10: page weight under 1 MB


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/form-token":  # the form service is not part of this static check
            body = b'{"token": "static-check"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


@pytest.fixture(scope="module")
def served(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[str, list[str]]]:
    out = tmp_path_factory.mktemp("browser") / "dist"
    build_site.build(ROOT / "site", ROOT / "brand", out)
    _, pages = build_site.load_config(ROOT / "site")
    handler = functools.partial(QuietHandler, directory=str(out))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", [p.path for p in pages]
    finally:
        server.shutdown()


@pytest.fixture(scope="module")
def browser() -> Iterator[Browser]:
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except Exception as exc:  # noqa: BLE001
            if os.environ.get("CI"):
                raise
            pytest.skip(f"Chromium missing: {exc}")
        yield b
        b.close()


class Collector:
    """Records every response of one page load."""

    def __init__(self) -> None:
        self.urls: list[str] = []
        self.failed: list[str] = []
        self.weight = 0

    def on_response(self, resp: Response) -> None:
        self.urls.append(resp.url)
        if resp.status >= 400:
            self.failed.append(f"{resp.status} {resp.url}")
        try:
            self.weight += len(resp.body())
        except Exception:  # noqa: BLE001, S110
            pass  # a response without a body (for example a redirect) adds no weight


@pytest.mark.parametrize("viewport", [(1440, 900), (390, 844)], ids=["desktop", "mobile"])
def test_every_page_has_no_cookies_no_third_party_request_and_is_light(
    served: tuple[str, list[str]], browser: Browser, viewport: tuple[int, int]
) -> None:
    base, paths = served
    host = urlparse(base).netloc
    for path in paths:
        context = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
        page = context.new_page()
        seen = Collector()
        page.on("response", seen.on_response)
        page.goto(base + path, wait_until="networkidle")
        assert context.cookies() == [], f"{path}: cookies set"
        assert page.evaluate("document.cookie") == "", f"{path}: document.cookie not empty"
        other = [u for u in seen.urls if urlparse(u).netloc != host and not u.startswith("data:")]
        assert not other, f"{path}: third-party requests {other}"
        assert not seen.failed, f"{path}: failed requests {seen.failed}"
        assert 0 < seen.weight < MAX_PAGE_BYTES, f"{path}: page weight {seen.weight} bytes"
        assert page.locator("h1").count() == 1, f"{path}: not one H1"
        overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        assert not overflow, f"{path}: horizontal scroll at {viewport[0]}px"
        context.close()


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_evidence_band_text_and_logo_are_readable_in_both_colour_schemes(
    served: tuple[str, list[str]], browser: Browser, scheme: str
) -> None:
    """EXW3: Lighthouse runs in light mode only. A visitor in dark mode must read the page."""
    base, paths = served
    for path in paths:
        context = browser.new_context(color_scheme=scheme)  # type: ignore[arg-type]
        page = context.new_page()
        page.goto(base + path, wait_until="networkidle")
        bad = page.evaluate(
            """() => {
              const probe = document.createElement('span');
              probe.style.color = 'var(--ex-on-evidence)';
              document.body.appendChild(probe);
              const want = getComputedStyle(probe).color;
              return [...document.querySelectorAll('.ex-mark')]
                .map(e => getComputedStyle(e).color).filter(c => c !== want);
            }"""
        )
        assert not bad, f"{path} ({scheme}): evidence-band text is not the on-evidence colour"
        shown = page.evaluate(
            """() => [...document.querySelectorAll('.ex-header__logo img')]
                 .filter(i => getComputedStyle(i).display !== 'none').map(i => i.currentSrc)"""
        )
        want = "exaktiv-lockup-reversed.svg" if scheme == "dark" else "exaktiv-lockup.svg"
        assert len(shown) == 1 and shown[0].endswith(want), f"{path} ({scheme}): wrong header logo"
        context.close()


def test_theme_button_switches_the_theme_keeps_it_and_stores_no_cookie(
    served: tuple[str, list[str]], browser: Browser
) -> None:
    """EXW3: the visitor can choose the other theme. The choice stays in localStorage (W-G3)."""
    base, _ = served
    context = browser.new_context(color_scheme="dark")
    page = context.new_page()
    page.goto(base + "/", wait_until="networkidle")
    button = page.locator("#theme-toggle")
    assert button.is_visible() and button.get_attribute("aria-pressed") == "true"
    ground = "getComputedStyle(document.body).backgroundColor"
    dark_ground = page.evaluate(ground)
    button.click()
    assert page.evaluate("document.documentElement.dataset.theme") == "light"
    assert button.get_attribute("aria-pressed") == "false"
    assert page.evaluate(ground) != dark_ground
    page.goto(base + "/team/", wait_until="networkidle")  # the choice holds on the next page
    assert page.evaluate("document.documentElement.dataset.theme") == "light"
    assert page.evaluate("localStorage.getItem('ex-theme')") == "light"
    assert context.cookies() == [] and page.evaluate("document.cookie") == ""
    page.locator("#theme-toggle").click()
    assert page.evaluate("document.documentElement.dataset.theme") == "dark"
    context.close()


def test_theme_button_is_hidden_without_javascript(
    served: tuple[str, list[str]], browser: Browser
) -> None:
    base, _ = served
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    page.goto(base + "/", wait_until="networkidle")
    assert not page.locator("#theme-toggle").is_visible()
    context.close()


@pytest.mark.parametrize("width", [320, 390, 768, 1024, 1180, 1181, 1440])
def test_every_page_fits_the_screen_at_each_width(
    served: tuple[str, list[str]], browser: Browser, width: int
) -> None:
    """EXW3: no page scrolls sideways and no element sticks out, at any width."""
    base, paths = served
    context = browser.new_context(viewport={"width": width, "height": 800})
    page = context.new_page()
    for path in paths:
        page.goto(base + path, wait_until="networkidle")
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth"), (
            f"{path} at {width}px: sideways scroll"
        )
        wide = page.evaluate(
            """() => [...document.querySelectorAll('body *')]
              .filter(e => !e.closest('.ex-table-box, .ex-code')
                           && getComputedStyle(e).display !== 'none'
                           && e.getBoundingClientRect().right > innerWidth + 1)
              .map(e => e.tagName + '.' + e.className).slice(0, 5)"""
        )
        assert not wide, f"{path} at {width}px: elements past the right edge {wide}"
    context.close()


def test_menu_collapses_on_narrow_screens_and_opens_by_button_and_closes_on_escape(
    served: tuple[str, list[str]], browser: Browser
) -> None:
    base, _ = served
    context = browser.new_context(viewport={"width": 390, "height": 800})
    page = context.new_page()
    page.goto(base + "/", wait_until="networkidle")
    nav, menu = page.locator(".ex-nav"), page.locator("#menu-toggle")
    assert menu.is_visible() and not nav.is_visible()
    assert page.locator(".ex-header").bounding_box()["height"] < 100  # type: ignore[index]
    menu.click()
    assert nav.is_visible() and menu.get_attribute("aria-expanded") == "true"
    page.keyboard.press("Escape")
    assert not nav.is_visible() and menu.get_attribute("aria-expanded") == "false"
    context.close()
    wide = browser.new_context(viewport={"width": 1280, "height": 800})
    page = wide.new_page()
    page.goto(base + "/", wait_until="networkidle")
    assert page.locator(".ex-nav").is_visible() and not page.locator("#menu-toggle").is_visible()
    wide.close()


def test_without_javascript_the_nav_stays_visible_on_a_phone(
    served: tuple[str, list[str]], browser: Browser
) -> None:
    base, _ = served
    context = browser.new_context(viewport={"width": 390, "height": 800}, java_script_enabled=False)
    page = context.new_page()
    page.goto(base + "/", wait_until="networkidle")
    assert page.locator(".ex-nav").is_visible() and not page.locator("#menu-toggle").is_visible()
    context.close()


def test_touch_targets_on_a_phone_are_at_least_the_brand_minimum(
    served: tuple[str, list[str]], browser: Browser
) -> None:
    """Brand rule 13: every control is at least --ex-target-min (44 px) tall."""
    base, paths = served
    context = browser.new_context(viewport={"width": 390, "height": 800})
    page = context.new_page()
    for path in paths:
        page.goto(base + path, wait_until="networkidle")
        if page.locator("#menu-toggle").is_visible():
            page.locator("#menu-toggle").click()
        small = page.evaluate(
            """() => [...document.querySelectorAll(
                'button, input:not([type=hidden]):not(.ex-honeypot), select, textarea, '
                + '.ex-btn, .ex-nav a')]
              .filter(e => e.getBoundingClientRect().height > 0
                           && e.getBoundingClientRect().height < 43.5)
              .map(e => e.tagName + '.' + e.className)"""
        )
        assert not small, f"{path}: controls under 44 px tall {small}"
    context.close()
