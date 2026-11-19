"""EXW2: the real web image (Caddy), built from site/Dockerfile, in front of a fake form upstream.

Needs a local Docker daemon and network access for the pinned caddy image. Marked `integration`.
Everything here is synthetic: a one-page site, a fake password and documentation IP addresses.
"""

import base64
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402
import render_caddyfile  # noqa: E402

pytestmark = pytest.mark.integration
CADDY = (ROOT / "site/Dockerfile").read_text().split("FROM ")[1].split()[0]
PASSWORD = "synthetic-staging-pw"  # noqa: S105  (a throwaway value for this test only)


def docker(*args: str, check: bool = True) -> str:
    out = subprocess.run(["docker", *args], capture_output=True, text=True, check=check)  # noqa: S603, S607
    return out.stdout.strip()


def request(
    url: str, *, auth: bool = False, method: str = "GET", headers: dict[str, str] | None = None
) -> tuple[int, dict[str, str], str]:
    req = urllib.request.Request(  # noqa: S310
        url, method=method, headers=headers or {}, data=b"x" if method == "POST" else None
    )  # noqa: S310
    if auth:
        token = base64.b64encode(f"staging:{PASSWORD}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            return resp.status, dict(resp.headers), resp.read().decode()
    except urllib.error.HTTPError as err:
        return err.code, dict(err.headers), err.read().decode()


@pytest.fixture(scope="module")
def stack(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, str]]:
    if shutil.which("docker") is None:
        pytest.skip("docker is not available")
    tag = f"exaktiv-web-test-{uuid.uuid4().hex[:8]}"
    net = f"net-{tag}"
    ctx = tmp_path_factory.mktemp("ctx")
    (ctx / "dist").mkdir()
    (ctx / "dist/index.html").write_text("<!doctype html><title>synthetic</title>")
    (ctx / "dist/404.html").write_text("<!doctype html><title>missing</title>")
    (ctx / "dist/.launch-built").write_text("synthetic launch build\n")  # live mode needs it (EXW3)
    (ctx / "build").mkdir()
    (ctx / "build/Caddyfile").write_text(
        render_caddyfile.render((ROOT / "site/Caddyfile.tmpl").read_text(), build_site.HEADERS)
    )
    shutil.copytree(ROOT / "site/caddy", ctx / "caddy")
    shutil.copy(ROOT / "site/Dockerfile", ctx / "Dockerfile")
    shutil.copy(ROOT / "site/entrypoint.sh", ctx / "entrypoint.sh")
    upstream_conf = (
        "{\n\tadmin off\n\tauto_https off\n}\n:8000 {\n"
        '\trespond "xff={http.request.header.X-Forwarded-For};auth={http.request.header.Authorization};path={http.request.uri.path}"\n}\n'
    )  # passed by environment: a bind mount of a temp folder is not shared with every Docker Desktop
    names: list[str] = []
    try:
        docker("network", "create", net)
        docker("build", "-q", "-t", tag, "--build-arg", "GIT_SHA=" + "0" * 40, str(ctx))
        pw_hash = docker("run", "--rm", CADDY, "caddy", "hash-password", "--plaintext", PASSWORD)
        up = f"{tag}-up"
        names.append(up)
        docker(
            "run", "-d", "--name", up, "--network", net, "--network-alias", "exaktiv-form",
            "-e", f"CFG={upstream_conf}", "--entrypoint", "sh", CADDY,
            "-c", 'printf "%s" "$CFG" > /tmp/C && exec caddy run --config /tmp/C --adapter caddyfile',
        )  # fmt: skip
        ports: dict[str, str] = {}
        for mode in ("staging", "live"):
            name = f"{tag}-{mode}"
            names.append(name)
            docker(
                "run", "-d", "--name", name, "--network", net, "--user", "10001", "--read-only",
                "--cap-drop", "ALL", "--tmpfs", "/config:uid=10001,gid=10001", "--tmpfs", "/data:uid=10001,gid=10001", "--tmpfs", "/tmp",  # noqa: S108
                "-e", f"SITE_MODE={mode}", "-e", f"STAGING_BASIC_AUTH_HASH={pw_hash}",
                "-p", "127.0.0.1::8080", tag,
            )  # fmt: skip
            ports[mode] = docker("port", name, "8080/tcp").splitlines()[0].rsplit(":", 1)[1]
        for _ in range(30):
            if request(f"http://127.0.0.1:{ports['staging']}/healthz")[0] == 200:
                break
            subprocess.run(["sleep", "0.5"], check=False)  # noqa: S603, S607
        yield {
            "tag": tag,
            "staging": ports["staging"],
            "live": ports["live"],
            "name": f"{tag}-staging",
        }
    finally:
        for name in names:
            docker("rm", "-f", name, check=False)
        docker("network", "rm", net, check=False)
        docker("rmi", "-f", tag, check=False)


def url(stack: dict[str, str], mode: str, path: str) -> str:
    return f"http://127.0.0.1:{stack[mode]}{path}"


def test_staging_without_password_is_401_and_with_password_is_200(stack: dict[str, str]) -> None:
    assert request(url(stack, "staging", "/"))[0] == 401
    status, headers, body = request(url(stack, "staging", "/"), auth=True)
    assert status == 200 and "synthetic" in body
    assert headers["X-Robots-Tag"] == "noindex, nofollow"
    for name, value in build_site.HEADERS.items():
        assert headers[name] == value, name
    assert "Set-Cookie" not in headers and "Server" not in headers  # W-G3


def test_healthcheck_needs_no_password(stack: dict[str, str]) -> None:
    assert request(url(stack, "staging", "/healthz"))[0] == 200


def test_missing_page_is_404_with_headers(stack: dict[str, str]) -> None:
    status, headers, _ = request(url(stack, "staging", "/nope"), auth=True)
    assert status == 404 and "Content-Security-Policy" in headers


def test_live_mode_has_no_password_and_no_noindex_header(stack: dict[str, str]) -> None:
    status, headers, _ = request(url(stack, "live", "/"))
    assert status == 200 and "X-Robots-Tag" not in headers


def test_form_paths_reach_the_upstream_with_one_forwarded_address(stack: dict[str, str]) -> None:
    status, _, body = request(
        url(stack, "staging", "/enquiries"), auth=True, method="POST",
        headers={"X-Forwarded-For": "203.0.113.7"},
    )  # fmt: skip
    assert status == 200
    assert "xff=203.0.113.7;" in body  # exactly one value: the visitor
    assert "auth=;" in body  # the staging password does not reach the form
    assert "path=/enquiries" in body
    assert request(url(stack, "staging", "/form-token"), auth=True)[0] == 200


def test_other_paths_never_reach_the_upstream(stack: dict[str, str]) -> None:
    for path in ("/health", "/docs", "/enquiries/1"):
        status, _, body = request(url(stack, "staging", path), auth=True)
        assert status == 404 and "xff=" not in body, path


def test_g11_access_log_masks_the_address_and_drops_credentials(stack: dict[str, str]) -> None:
    request(
        url(stack, "staging", "/?q=secret-query"),
        auth=True,
        headers={"X-Forwarded-For": "203.0.113.77"},
    )
    lines = [ln for ln in docker("logs", stack["name"]).splitlines() if ln.startswith("{")]
    entries = [json.loads(ln) for ln in lines if '"request"' in ln]
    assert entries
    last = entries[-1]
    assert last["request"]["client_ip"] == "203.0.113.0"
    assert last["request"]["remote_ip"].endswith(".0")
    dumped = json.dumps(entries)
    assert "203.0.113.77" not in dumped and "secret-query" not in dumped
    assert "Authorization" not in dumped and PASSWORD not in dumped
    assert "X-Forwarded-For" not in dumped


def run_web(stack: dict[str, str], *env: str) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "run", "--rm", "--user", "10001", "--read-only", "--cap-drop", "ALL"]  # noqa: S607
    for item in env:
        cmd += ["-e", item]
    return subprocess.run(
        [*cmd, stack["tag"]], capture_output=True, text=True, timeout=30, check=False
    )  # noqa: S603


def test_staging_with_an_empty_hash_fails_closed(stack: dict[str, str]) -> None:
    out = run_web(stack, "SITE_MODE=staging", "STAGING_BASIC_AUTH_HASH=")
    assert out.returncode != 0  # no password wall means no server


def test_an_unknown_site_mode_fails_closed(stack: dict[str, str]) -> None:
    for mode in ("", "*", "prod"):
        assert run_web(stack, f"SITE_MODE={mode}").returncode != 0, mode


def test_g11_a_failed_upstream_is_a_masked_502(stack: dict[str, str]) -> None:
    up = f"{stack['tag']}-up"
    docker("stop", up)
    try:
        status, _, _ = request(
            url(stack, "staging", "/enquiries"),
            auth=True,
            method="POST",
            headers={"X-Forwarded-For": "203.0.113.99"},
        )
    finally:
        docker("start", up)
    assert status == 502
    logs = docker("logs", stack["name"])
    assert "203.0.113.99" not in logs  # the error path never prints the full address
