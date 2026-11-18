"""The contact form service (PRD-W section 7)."""

import json
import logging
import time
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import asdict
from typing import Any
from urllib.parse import parse_qsl

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from exaktiv_site_form.delivery import deliver_one
from exaktiv_site_form.logging import configure_logging, log_event
from exaktiv_site_form.mail import BrevoMailer, Mailer
from exaktiv_site_form.models import PendingMail
from exaktiv_site_form.settings import SiteFormSettings
from exaktiv_site_form.spam import check_token, client_ip, ip_hash, make_token
from exaktiv_site_form.store import PgStore, Store
from exaktiv_site_form.validation import validate

log = logging.getLogger("exaktiv_site_form")
HONEYPOT = "website"
Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


class _TooLarge(Exception):
    pass


async def _read_body(request: Request, limit: int) -> bytes:
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > limit:
        raise _TooLarge
    body = b""
    async for chunk in request.stream():
        body += chunk
        if len(body) > limit:
            raise _TooLarge
    return body


def _parse(body: bytes, is_json: bool) -> dict[str, str] | None:
    if is_json:
        try:
            data = json.loads(body)
        except (ValueError, RecursionError):
            return None
        if not isinstance(data, dict):
            return None
        # A non-string value never passes as text. A non-string honeypot counts as filled.
        out = {str(k): v if isinstance(v, str) else "" for k, v in data.items()}
        if HONEYPOT in data and not isinstance(data[HONEYPOT], str):
            out[HONEYPOT] = "1"
        return out
    result: dict[str, str] = {}
    for key, value in parse_qsl(body.decode("utf-8", errors="replace"), keep_blank_values=True):
        result.setdefault(key, value)
    return result


def create_app(
    settings: SiteFormSettings,
    store: Store,
    mailer: Mailer,
    clock: Callable[[], float] = time.time,
    lifespan: Lifespan | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Exaktiv site form",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    token_secret = settings.form_token_secret.get_secret_value()
    hash_secret = settings.ip_hash_secret.get_secret_value()
    base = settings.site_base_url

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/form-token")
    async def form_token() -> JSONResponse:
        return JSONResponse(
            {"token": make_token(token_secret, clock())}, headers={"Cache-Control": "no-store"}
        )

    @app.post("/enquiries")
    async def enquiries(request: Request, background: BackgroundTasks) -> Response:
        content_type = request.headers.get("content-type", "")
        is_json = content_type.startswith("application/json")
        wants_json = is_json or "application/json" in request.headers.get("accept", "")

        def success() -> Response:
            if wants_json:
                return JSONResponse({"status": "received"}, status_code=201)
            return RedirectResponse(f"{base}/contact/thanks/", status_code=303)

        def refused(code: str, status: int, headers: dict[str, str] | None = None) -> Response:
            if wants_json:
                return JSONResponse({"error": code}, status_code=status, headers=headers)
            return RedirectResponse(f"{base}/contact/?errors={code}", status_code=303)

        try:
            try:
                body = await _read_body(request, settings.max_body_bytes)
            except _TooLarge:
                return JSONResponse({"error": "too_large"}, status_code=413)
            raw = _parse(body, is_json)
            if raw is None:
                return JSONResponse({"error": "bad_request"}, status_code=400)

            peer = request.client.host if request.client else "unknown"
            ip = client_ip(
                peer, request.headers.get("x-forwarded-for"), settings.trusted_proxy_hops
            )
            fill_check = check_token(
                token_secret, raw.get("form_token"), clock(), settings.min_fill_seconds
            )
            limit = (
                settings.rate_limit_max
                if fill_check != "missing"
                else settings.rate_limit_max_no_token
            )
            allowed = await store.check_and_record_hit(
                ip_hash(hash_secret, ip), limit, settings.rate_limit_window_s
            )
            if not allowed:
                log_event(log, logging.INFO, "rate_limited")
                window = str(settings.rate_limit_window_s)
                return refused("rate_limited", 429, {"Retry-After": window})
            if raw.get(HONEYPOT):
                log_event(log, logging.INFO, "honeypot_dropped")
                return success()
            if fill_check == "rejected":
                log_event(log, logging.INFO, "token_rejected")
                return success()

            result = validate(raw)
            if isinstance(result, list):
                log_event(log, logging.INFO, "validation_failed", fields=[e.field for e in result])
                if wants_json:
                    return JSONResponse({"errors": [asdict(e) for e in result]}, status_code=422)
                names = ",".join(e.field for e in result)
                return RedirectResponse(f"{base}/contact/?errors={names}", status_code=303)

            enquiry_id = await store.insert_enquiry(result)
            log_event(log, logging.INFO, "enquiry_stored", enquiry_id=str(enquiry_id))
            background.add_task(
                deliver_one, store, mailer, settings, PendingMail(enquiry_id, result, True, True)
            )
            return success()
        except Exception as exc:  # noqa: BLE001 - never let a message with personal data escape
            log_event(log, logging.ERROR, "unhandled_error", error=type(exc).__name__)
            return JSONResponse({"error": "server_error"}, status_code=500)

    return app


def create_default_app() -> FastAPI:
    """Entry: uvicorn exaktiv_site_form.main:create_default_app --factory --no-access-log."""
    configure_logging()
    settings = SiteFormSettings()  # type: ignore[call-arg]
    store = PgStore()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await store.open(settings.dsn(), **settings.connect_kwargs())
        try:
            yield
        finally:
            await store.close()

    mailer = BrevoMailer(
        settings.brevo_api_key.get_secret_value(),
        settings.mail_sender_email,
        settings.mail_sender_name,
    )
    return create_app(settings, store, mailer, lifespan=lifespan)


__all__: list[Any] = ["create_app", "create_default_app"]
