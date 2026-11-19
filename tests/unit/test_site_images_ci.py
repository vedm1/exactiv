"""EXW2: the Dockerfiles, the CI jobs that build and deploy them, and the DNS and smoke scripts."""

import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_dns  # noqa: E402
import smoke_staging  # noqa: E402

CONFIG = ROOT / ".circleci/config.yml"
FORM_DOCKERFILE = ROOT / "services/site_form/Dockerfile"
WEB_DOCKERFILE = ROOT / "site/Dockerfile"
FIVE = ["python", "ui", "site", "secrets", "integration"]


@pytest.fixture(scope="module")
def cfg() -> dict[str, Any]:
    data = yaml.safe_load(CONFIG.read_text())
    assert isinstance(data, dict)
    return data


def workflow(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for entry in cfg["workflows"]["ci"]["jobs"]:
        if isinstance(entry, str):
            out[entry] = {}
        else:
            ((name, body),) = entry.items()
            out[name] = body or {}
    return out


def test_circleci_has_build_images_and_deploy_app(cfg: dict[str, Any]) -> None:
    wf = workflow(cfg)
    assert {"build-images", "deploy-app"} <= set(cfg["jobs"])
    build, app = wf["build-images"], wf["deploy-app"]
    assert set(build["requires"]) == set(FIVE)
    assert app["requires"] == ["build-images"]
    for body in (build, app):
        assert body["filters"]["branches"]["only"] == "main"
        assert body["context"] == "exaktiv_deploy"


def test_deploy_app_uses_the_forced_command_key_and_the_deploy_user(cfg: dict[str, Any]) -> None:
    text = yaml.safe_dump(cfg["jobs"]["deploy-app"], width=10**6)
    assert "SHA256:WfZbao8U9HSoOjcTZcN7d/I0y53qIgb+7dN9Xsqz6Vk" in text  # circleci-exaktiv-app
    assert "SHA256:qk4S2wcjY5rpid5SrpqXCPPs" not in text  # not the key of deploy-infra
    assert "git ls-remote origin refs/heads/main" in text  # only the newest main commit deploys
    assert "GHCR_PUSH_TOKEN" in text  # no image was pushed without it, so nothing deploys
    assert re.search(r'ssh .*deploy@"?\$APPS_HOST"? "?\$CIRCLE_SHA1', text)
    assert "exaktiv-deploy@" not in text  # that user belongs to deploy-infra
    assert "APPS_HOST" in text and "halt" in text  # a no-op with a message when unset


def test_build_images_builds_tests_then_pushes(cfg: dict[str, Any]) -> None:
    text = CONFIG.read_text()
    job = yaml.safe_dump(cfg["jobs"]["build-images"], width=10**6)
    assert job.index("build_site.py") < job.index("render_caddyfile.py") < job.index("docker build")
    assert job.index("test_image.sh") < job.index("docker push")
    assert "ghcr.io/vedm1/exaktiv/web" in job and "ghcr.io/vedm1/exaktiv/site-form" in job
    assert "GIT_SHA=$CIRCLE_SHA1" in job or "GIT_SHA=${CIRCLE_SHA1}" in job
    assert "DATABASE_URL" not in text  # CI holds no production database login
    assert "--password-stdin" in job  # the token never appears on a command line


def test_g9_ci_and_site_files_hold_no_secret_values() -> None:
    pattern = re.compile(
        r"(dp\.(st|pt|sa)\.[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY)"
    )
    paths = [CONFIG, FORM_DOCKERFILE, WEB_DOCKERFILE, *(ROOT / "deploy/site").rglob("*")]
    for path in paths:
        if path.is_file():
            assert not pattern.search(path.read_text()), path


def test_form_image_command_has_no_access_log_and_a_plain_user() -> None:
    text = FORM_DOCKERFILE.read_text()
    assert "--no-access-log" in text and "--factory" in text
    assert re.search(r"^USER app\b", text, re.MULTILINE)
    assert re.search(r"useradd --uid 10001", text)
    assert re.search(r"org\.opencontainers\.image\.revision=\"\$\{GIT_SHA\}\"", text)
    assert re.search(r'"doppler",\s*"run",\s*"--no-fallback",\s*"--"', text)
    assert not re.search(r"COPY .*\.env", text)
    for line in text.splitlines():
        if line.startswith("ARG PYTHON_IMAGE") or (line.startswith("FROM") and "${" not in line):
            assert "@sha256:" in line, line  # every base image is pinned by digest


def test_web_image_is_pinned_and_labelled() -> None:
    text = WEB_DOCKERFILE.read_text()
    assert re.search(r"^FROM caddy:2-alpine@sha256:[0-9a-f]{64}", text, re.MULTILINE)
    assert "COPY dist /srv" in text and "COPY build/Caddyfile /etc/caddy/Caddyfile" in text
    assert "org.opencontainers.image.revision" in text
    assert (
        "RUN cp /usr/bin/caddy /usr/local/bin/caddy" in text
    )  # no file capability: starts with cap_drop ALL
    assert re.search(r"^USER 10001", text, re.MULTILINE)
    assert "HEALTHCHECK" in text and "/healthz" in text


def test_docker_context_excludes_secrets_and_tests() -> None:
    ignore = (ROOT / ".dockerignore").read_text().splitlines()
    assert ignore[0] == "*"  # an allowlist: nothing enters the image by accident
    assert "!.env" not in ignore
    assert not any(line.startswith("!tests") or line.startswith("!.git") for line in ignore)
    assert (ROOT / "site/.dockerignore").read_text().splitlines()[0] == "*"


# ---- scripts/check_dns.py -------------------------------------------------------------------------------


def fake_dig(table: dict[tuple[str, str], list[str]]) -> Any:
    return lambda rtype, name: table.get((rtype, name), [])


GOOD = {
    ("A", "exaktiv.com"): ["188.245.25.106"],
    ("CNAME", "www.exaktiv.com"): ["exaktiv.com."],
    ("TXT", "exaktiv.com"): ['"v=spf1 include:spf.brevo.com ~all"'],
    ("TXT", "_dmarc.exaktiv.com"): ['"v=DMARC1; p=none; rua=mailto:d@exaktiv.com"'],
    ("CNAME", "brevo1._domainkey.exaktiv.com"): ["b1.exaktiv-com.dkim.brevo.com."],
}


def test_check_dns_passes_a_good_zone() -> None:
    results = check_dns.check("exaktiv.com", "188.245.25.106", fake_dig(GOOD))
    assert all(ok for _, ok, _ in results), results


@pytest.mark.parametrize(
    "drop, label",
    [
        (("A", "exaktiv.com"), "A record"),
        (("TXT", "exaktiv.com"), "SPF"),
        (("TXT", "_dmarc.exaktiv.com"), "DMARC"),
        (("CNAME", "brevo1._domainkey.exaktiv.com"), "DKIM"),
    ],
)
def test_check_dns_fails_a_missing_record(drop: tuple[str, str], label: str) -> None:
    zone = {k: v for k, v in GOOD.items() if k != drop}
    failed = [
        n for n, ok, _ in check_dns.check("exaktiv.com", "188.245.25.106", fake_dig(zone)) if not ok
    ]
    assert any(label in n for n in failed), failed


def test_check_dns_wrong_ip_and_two_spf_records_fail() -> None:
    wrong = {**GOOD, ("A", "exaktiv.com"): ["203.0.113.9"]}
    assert not all(
        ok for _, ok, _ in check_dns.check("exaktiv.com", "188.245.25.106", fake_dig(wrong))
    )
    two = {
        **GOOD,
        ("TXT", "exaktiv.com"): ['"v=spf1 include:spf.brevo.com ~all"', '"v=spf1 mx ~all"'],
    }
    failed = [
        n for n, ok, _ in check_dns.check("exaktiv.com", "188.245.25.106", fake_dig(two)) if not ok
    ]
    assert any("SPF" in n for n in failed)


# ---- scripts/smoke_staging.py ---------------------------------------------------------------------------


class _Handler(BaseHTTPRequestHandler):
    good_headers = {
        "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Robots-Tag": "noindex, nofollow",
    }

    def do_GET(self) -> None:
        if self.headers.get("Authorization") != "Basic c3RhZ2luZzpwdw==":  # staging:pw
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="x"')
            self.end_headers()
            return
        self.send_response(200)
        for k, v in self.good_headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args: Any) -> None:  # silence
        pass


@pytest.fixture
def server() -> Any:
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def test_smoke_staging_passes_a_protected_site(server: str) -> None:
    results = smoke_staging.check_site(server, "staging", "pw", ["/"], require_https=False)
    assert all(ok for _, ok, _ in results), results


def test_smoke_staging_fails_with_a_wrong_password(server: str) -> None:
    results = smoke_staging.check_site(server, "staging", "wrong", ["/"], require_https=False)
    assert not all(ok for _, ok, _ in results)


class _OpenHandler(_Handler):
    def do_GET(self) -> None:  # no password wall at all
        self.send_response(200)
        for k, v in self.good_headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(b"ok")


def test_smoke_staging_detects_a_missing_password_wall() -> None:
    httpd = HTTPServer(("127.0.0.1", 0), _OpenHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{httpd.server_port}"
        results = smoke_staging.check_site(base, "staging", "pw", ["/"], require_https=False)
    finally:
        httpd.shutdown()
    failed = [n for n, ok, _ in results if not ok]
    assert any("401 without password" in n for n in failed), failed
