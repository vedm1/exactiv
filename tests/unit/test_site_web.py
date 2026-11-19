"""EXW2: the web tier (Caddy in the site image), the block for the shared Caddy, the timers and the site config."""

import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402
import render_caddyfile  # noqa: E402

TEMPLATE = ROOT / "site/Caddyfile.tmpl"
STAGING = ROOT / "site/caddy/mode-staging.caddy"
LIVE = ROOT / "site/caddy/mode-live.caddy"
SHARED = ROOT / "deploy/site/caddy/exaktiv-site.caddy"
SYSTEMD = ROOT / "deploy/site/systemd"


@pytest.fixture(scope="module")
def rendered() -> str:
    return render_caddyfile.render(TEMPLATE.read_text(), build_site.HEADERS)


def test_web_caddyfile_headers_match_the_build_headers(rendered: str) -> None:
    for name, value in build_site.HEADERS.items():
        assert f'{name} "{value}"' in rendered, name
    assert "{{" not in rendered  # no marker left


def test_render_refuses_a_template_without_the_marker() -> None:
    with pytest.raises(ValueError, match="marker"):
        render_caddyfile.render("no marker here", build_site.HEADERS)


def test_render_escapes_a_quote_in_a_header_value() -> None:
    out = render_caddyfile.render("{{SECURITY_HEADERS}}", {"X-Test": 'a"b'})
    assert 'X-Test "a\\"b"' in out


def test_w_g3_web_sets_no_cookie_and_no_third_party(rendered: str) -> None:
    for text in (rendered, STAGING.read_text(), LIVE.read_text()):
        code = re.sub(r"#.*", "", text)
        assert not re.search(r"https?://", code)  # no URL at all
        assert not re.search(r"header\s+\+?Set-Cookie", code, re.IGNORECASE)
    assert "default-src 'self'" in rendered and "frame-ancestors 'none'" in rendered


def test_web_listens_without_tls_and_without_admin(rendered: str) -> None:
    assert "auto_https off" in rendered and "admin off" in rendered
    assert re.search(
        r"^:8080 \{", rendered, re.MULTILINE
    )  # unprivileged port: no capability needed


def test_staging_mode_requires_basic_auth_and_noindex() -> None:
    staging, live = STAGING.read_text(), LIVE.read_text()
    assert "basic_auth @protected" in staging and "{$STAGING_BASIC_AUTH_HASH}" in staging
    assert "not path /healthz" in staging  # the container healthcheck needs no password
    assert re.search(r'X-Robots-Tag "noindex, nofollow"', staging)
    assert "basic_auth" not in live and "X-Robots-Tag" not in live


def test_web_mode_file_is_chosen_by_site_mode(rendered: str) -> None:
    assert "import /etc/caddy/mode-{$SITE_MODE}.caddy" in rendered
    assert (
        "respond /healthz 200" in rendered
    )  # the order of directives is Caddy's; the integration test proves it


def test_g11_web_log_filter_masks_ip_and_drops_credentials(rendered: str) -> None:
    log = rendered[rendered.index("log {") :]
    for field in ("request>remote_ip", "request>client_ip"):
        assert re.search(rf"{re.escape(field)} ip_mask", log), field
    assert "ipv4 24" in log and "ipv6 48" in log
    for header in ("Authorization", "Cookie", "X-Forwarded-For", "X-Real-Ip", "Set-Cookie"):
        assert f"request>headers>{header} delete" in log or f"resp_headers>{header} delete" in log
    assert re.search(r"request>uri regexp", log)  # the query string is cut off


def test_web_routes_only_form_paths_to_the_form(rendered: str) -> None:
    assert "@form path /enquiries /form-token" in rendered
    assert rendered.count("reverse_proxy") == 1
    assert "reverse_proxy @form exaktiv-form:8000" in rendered
    assert "header_up X-Forwarded-For {client_ip}" in rendered
    assert "header_up -Authorization" in rendered  # the staging password never reaches the form
    assert "trusted_proxies static private_ranges" in rendered
    assert "client_ip_headers X-Forwarded-For" in rendered


def test_shared_caddy_block_has_no_log_and_no_app_import() -> None:
    text = re.sub(r"#.*", "", SHARED.read_text())
    assert "import app" not in text  # the (app) snippet logs full client IPs
    assert not re.search(r"^\s*log\b", text, re.MULTILINE)
    assert "reverse_proxy exaktiv-web:8080" in text
    assert re.search(r"www\.exaktiv\.com \{\s*redir https://exaktiv\.com\{uri\} permanent", text)
    assert re.search(r"^exaktiv\.com \{", text, re.MULTILINE)


@pytest.mark.parametrize(
    "name, calendar",
    [
        ("retention", r"OnCalendar=\*-\*-\* 03:15:00 UTC"),
        ("retry-mail", r"OnUnitActiveSec=1min"),
        ("purge-hits", r"OnCalendar=hourly"),
    ],
)
def test_w_g4_timers_run_the_form_jobs(name: str, calendar: str) -> None:
    timer = (SYSTEMD / f"exaktiv-site-{name}.timer").read_text()
    service = (SYSTEMD / f"exaktiv-site-{name}.service").read_text()
    assert re.search(calendar, timer)
    assert f"Unit=exaktiv-site-{name}.service" in timer or "Unit=" not in timer
    assert "WantedBy=timers.target" in timer
    assert "User=deploy" in service and "Type=oneshot" in service
    assert re.search(rf"--profile jobs run --rm -T --no-deps jobs {name}\b", service)
    assert "IMAGE_TAG=$$(cat .current)" in service  # $$ is a literal dollar sign for systemd
    assert "TimeoutStartSec=300" in service  # a hung call must not block every later run
    if name == "retention":
        assert "Persistent=true" in timer  # a missed daily run still happens (W-G4)
        assert "Restart=on-failure" in service and "RestartSec=300" in service
    assert not re.search(r"dp\.(st|pt|sa)\.|BREVO|DATABASE_URL", timer + service)


def test_site_base_url_is_the_real_domain() -> None:
    cfg = yaml.safe_load((ROOT / "site/site.yaml").read_text())
    assert cfg["base_url"] == "https://exaktiv.com"
