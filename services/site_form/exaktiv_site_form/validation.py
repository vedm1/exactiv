"""Field rules from PRD-W section 7. Pure function: no I/O, no logging."""

import unicodedata
from collections.abc import Mapping

from email_validator import EmailNotValidError, validate_email

from exaktiv_site_form.models import DataRegion, EnquiryIn, FieldError, Topic

MESSAGES = {
    "required": "Enter a value for this field.",
    "too_short": "This value is too short.",
    "too_long": "This value is too long.",
    "invalid_email": "Enter a valid email address.",
    "invalid_choice": "Choose one of the listed options.",
}
EMAIL_MAX = 254


def _clean(raw: Mapping[str, str], key: str) -> str:
    return unicodedata.normalize("NFC", (raw.get(key) or "").strip())


def _has_control(value: str, allow_newline: bool) -> bool:
    for ch in value:
        if unicodedata.category(ch) == "Cc" and not (allow_newline and ch in "\n\r\t"):
            return True
    return False


def validate(raw: Mapping[str, str]) -> EnquiryIn | list[FieldError]:
    errors: list[FieldError] = []

    def fail(field: str, code: str) -> None:
        errors.append(FieldError(field, code, MESSAGES[code]))

    def text(field: str, lo: int, hi: int, required: bool, newlines: bool = False) -> str | None:
        value = _clean(raw, field)
        if not value:
            if required:
                fail(field, "required")
            return None
        if _has_control(value, newlines):
            fail(field, "invalid_choice")
        elif len(value) < lo:
            fail(field, "too_short")
        elif len(value) > hi:
            fail(field, "too_long")
        else:
            return value
        return None

    name = text("name", 2, 100, True)

    email: str | None = None
    raw_email = _clean(raw, "email")
    if not raw_email:
        fail("email", "required")
    elif len(raw_email) > EMAIL_MAX or _has_control(raw_email, False):
        fail("email", "invalid_email")
    else:
        try:
            email = validate_email(
                raw_email, check_deliverability=False, allow_smtputf8=False
            ).normalized
        except EmailNotValidError:
            fail("email", "invalid_email")

    company = text("company", 2, 150, True)
    role = text("role", 0, 100, False)

    topic: Topic | None = None
    raw_topic = _clean(raw, "topic")
    if not raw_topic:
        fail("topic", "required")
    else:
        try:
            topic = Topic(raw_topic)
        except ValueError:
            fail("topic", "invalid_choice")

    region: DataRegion | None = None
    raw_region = _clean(raw, "data_region")
    if raw_region:
        try:
            region = DataRegion(raw_region)
        except ValueError:
            fail("data_region", "invalid_choice")

    message = text("message", 20, 2000, True, newlines=True)

    if (
        errors
        or name is None
        or email is None
        or company is None
        or topic is None
        or message is None
    ):
        return errors
    return EnquiryIn(name, email, company, role, topic, region, message)
