import pytest
from exaktiv_site_form.models import DataRegion, EnquiryIn, FieldError, Topic
from exaktiv_site_form.validation import validate

from tests.unit.site_form_fakes import VALID_FORM


def errors(raw: dict[str, str]) -> dict[str, str]:
    result = validate(raw)
    assert isinstance(result, list)
    return {e.field: e.code for e in result}


def test_valid_input_parses() -> None:
    result = validate(VALID_FORM)
    assert isinstance(result, EnquiryIn)
    assert result.topic is Topic.legacy_modernisation
    assert result.data_region is DataRegion.eu_uk


@pytest.mark.parametrize("field", ["name", "email", "company", "topic", "message"])
def test_missing_required_field(field: str) -> None:
    raw = {k: v for k, v in VALID_FORM.items() if k != field}
    assert errors(raw) == {field: "required"}


def test_all_errors_listed_together() -> None:
    assert errors({}) == {
        "name": "required",
        "email": "required",
        "company": "required",
        "topic": "required",
        "message": "required",
    }


@pytest.mark.parametrize(
    ("field", "length", "ok"),
    [
        ("name", 1, False),
        ("name", 2, True),
        ("name", 100, True),
        ("name", 101, False),
        ("company", 1, False),
        ("company", 2, True),
        ("company", 150, True),
        ("company", 151, False),
        ("role", 100, True),
        ("role", 101, False),
        ("message", 19, False),
        ("message", 20, True),
        ("message", 2000, True),
        ("message", 2001, False),
    ],
)
def test_field_length_boundaries(field: str, length: int, ok: bool) -> None:
    raw = {**VALID_FORM, field: "a" * length}
    result = validate(raw)
    if ok:
        assert isinstance(result, EnquiryIn)
    else:
        assert isinstance(result, list)
        assert [e.field for e in result] == [field]
        assert result[0].code in {"too_short", "too_long"}


def test_values_are_trimmed_before_counting() -> None:
    result = validate({**VALID_FORM, "name": "  A  "})
    assert isinstance(result, list)
    assert result[0].code == "too_short"


def test_bad_topic_and_region() -> None:
    assert errors({**VALID_FORM, "topic": "nope"}) == {"topic": "invalid_choice"}
    assert errors({**VALID_FORM, "data_region": "mars"}) == {"data_region": "invalid_choice"}


def test_empty_optional_fields_become_none() -> None:
    result = validate({**VALID_FORM, "role": "  ", "data_region": ""})
    assert isinstance(result, EnquiryIn)
    assert result.role is None
    assert result.data_region is None


@pytest.mark.parametrize(
    "email",
    [
        "not-an-email",
        "a@b",
        "test.person@example.com\r\nBcc: victim@example.test",
        "test.person@example.com\nX: y",
        "a" * 250 + "@example.test",
    ],
)
def test_email_with_newline_or_bad_format_is_rejected(email: str) -> None:
    assert errors({**VALID_FORM, "email": email}) == {"email": "invalid_email"}


def test_nul_and_control_characters_rejected() -> None:
    assert errors({**VALID_FORM, "name": "Test\x00Person"}) == {"name": "invalid_choice"}


def test_message_keeps_newlines() -> None:
    result = validate({**VALID_FORM, "message": "line one is here\nline two is here"})
    assert isinstance(result, EnquiryIn)
    assert "\n" in result.message


def test_error_messages_never_contain_input() -> None:
    result = validate({**VALID_FORM, "name": "x", "email": "SECRET-INPUT-VALUE"})
    assert isinstance(result, list)
    for e in result:
        assert isinstance(e, FieldError)
        assert "SECRET-INPUT-VALUE" not in e.message


def test_non_ascii_local_part_is_rejected() -> None:
    assert errors({**VALID_FORM, "email": "tëst@example.com"}) == {"email": "invalid_email"}
