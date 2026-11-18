"""Logging with personal data masking (G11). Log event names and IDs only, never values."""

import json
import logging
import re
from typing import Any

EMAIL_RE = re.compile(
    r"([A-Za-z0-9._%+\-])[A-Za-z0-9._%+\-]*@([A-Za-z0-9])[A-Za-z0-9.\-]*?(\.[A-Za-z]{2,})\b"
)


def mask_email(value: str) -> str:
    return EMAIL_RE.sub(r"\1***@\2***\3", value)


class MaskingFilter(logging.Filter):
    """Second line of defence: rewrite any email address in a record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = mask_email(record.getMessage())
        record.args = None
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            record.fields = {
                k: mask_email(v) if isinstance(v, str) else v for k, v in fields.items()
            }
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {"level": record.levelname, "event": record.getMessage()}
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            data.update(fields)
        return json.dumps(data, default=str)


def log_event(logger: logging.Logger, level: int, event: str, **fields: object) -> None:
    logger.log(level, event, extra={"fields": fields})


def configure_logging() -> None:
    """JSON lines to stderr, with the masking filter on the handler. Call once at start."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(MaskingFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
