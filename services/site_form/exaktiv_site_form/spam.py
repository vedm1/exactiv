"""Spam controls: signed form token (minimum fill time), IP hash, client IP rule."""

import hashlib
import hmac
from typing import Literal

TOKEN_MAX_AGE_S = 7200
TokenState = Literal["valid", "missing", "rejected"]


def _sign(secret: str, issued: str) -> str:
    return hmac.new(secret.encode(), issued.encode(), hashlib.sha256).hexdigest()


def make_token(secret: str, now: float) -> str:
    issued = str(int(now))
    return f"{issued}.{_sign(secret, issued)}"


def check_token(secret: str, token: str | None, now: float, min_age_s: int) -> TokenState:
    if not token:
        return "missing"
    issued, _, signature = token.partition(".")
    if not (issued.isascii() and issued.isdigit() and signature.isascii()) or not signature:
        return "rejected"
    if not hmac.compare_digest(signature.encode(), _sign(secret, issued).encode()):
        return "rejected"
    age = now - int(issued)
    if age < min_age_s or age > TOKEN_MAX_AGE_S:
        return "rejected"
    return "valid"


def client_ip(peer: str, forwarded_for: str | None, hops: int) -> str:
    """The Nth entry from the right of X-Forwarded-For; the socket peer without a proxy."""
    if hops <= 0 or not forwarded_for:
        return peer
    parts = [p.strip() for p in forwarded_for.split(",") if p.strip()]
    if len(parts) < hops:
        return peer
    return parts[-hops]


def ip_hash(secret: str, ip: str) -> str:
    """Keyed hash. The raw IP is never stored or logged."""
    return hmac.new(secret.encode(), ip.encode(), hashlib.sha256).hexdigest()
