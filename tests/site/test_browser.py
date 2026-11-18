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
