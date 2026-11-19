"""Smoke test of the staging site (EXW2). Run by hand after a deploy.

Usage: STAGING_PASSWORD=... python3 scripts/smoke_staging.py [--base https://exaktiv.com] [--user staging]
The password comes from the environment, never from an argument (it would show in the process list).
Checks: 401 without the password, 200 with it, security headers, noindex, no cookie, robots.txt, redirect from HTTP,
TLS 1.2 or later only. Exit 0 when every check passes.
"""

import argparse
import base64
import os
import socket
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

Result = tuple[str, bool, str]
PAGES = ["/", "/contact/", "/ai-product-delivery/", "/robots.txt"]
HEADER_RULES = {
    "Content-Security-Policy": "frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=",
    "X-Robots-Tag": "noindex",
}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None


def get(
    url: str, user: str | None = None, password: str | None = None
) -> tuple[int, dict[str, str], str]:
    req = urllib.request.Request(url)  # noqa: S310
    if user is not None and password is not None:
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=15) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, dict(err.headers), ""


def check_site(
    base: str, user: str, password: str, paths: list[str], *, require_https: bool = True
) -> list[Result]:
    out: list[Result] = []
    for path in paths:
        status, _, _ = get(base + path)
        out.append((f"401 without password {path}", status == 401, f"status {status}"))
        status, headers, body = get(base + path, user, password)
        out.append((f"200 with password {path}", status == 200, f"status {status}"))
        if status != 200:
            continue
        out.append((f"no cookie {path}", "Set-Cookie" not in headers, "Set-Cookie absent"))
        if path == "/robots.txt":
            out.append(("robots.txt disallows all", "Disallow: /" in body, "Disallow: /"))
        for name, needle in HEADER_RULES.items():
            if name == "Strict-Transport-Security" and not require_https:
                continue
            value = headers.get(name, "")
            out.append((f"{name} {path}", needle in value, value or "missing"))
    return out


def check_transport(host: str) -> list[Result]:
    out: list[Result] = []
    status, headers, _ = get(f"http://{host}/")
    location = headers.get("Location", "")
    out.append(
        (
            "HTTP redirects to HTTPS",
            status in (301, 308) and location.startswith("https://"),
            f"{status} {location}",
        )
    )
    ctx12 = ssl.create_default_context()
    ctx12.minimum_version = ssl.TLSVersion.TLSv1_2
    try:
        with (
            socket.create_connection((host, 443), timeout=10) as sock,
            ctx12.wrap_socket(sock, server_hostname=host) as tls,
        ):
            out.append(("TLS 1.2 or later accepted", True, str(tls.version())))
    except OSError as err:
        out.append(("TLS 1.2 or later accepted", False, str(err)))
    old = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    old.check_hostname = False
    old.verify_mode = ssl.CERT_NONE
    try:
        old.maximum_version = ssl.TLSVersion.TLSv1_1
        old.minimum_version = ssl.TLSVersion.TLSv1
        with (
            socket.create_connection((host, 443), timeout=10) as sock,
            old.wrap_socket(sock, server_hostname=host),
        ):
            out.append(("TLS 1.1 refused", False, "the server accepted TLS 1.1"))
    except (OSError, ValueError):
        out.append(("TLS 1.1 refused", True, "refused or not offered by this client"))
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="https://exaktiv.com")
    parser.add_argument("--user", default="staging")
    args = parser.parse_args(argv)
    password = os.environ.get("STAGING_PASSWORD", "")
    if not password:
        print("Set STAGING_PASSWORD in the environment.", file=sys.stderr)
        return 2
    results = check_site(args.base, args.user, password, PAGES)
    if args.base.startswith("https://"):
        results += check_transport(urlparse(args.base).netloc)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
