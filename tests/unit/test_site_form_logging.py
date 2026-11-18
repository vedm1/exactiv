import json
import logging

import pytest
from exaktiv_site_form.logging import JsonFormatter, MaskingFilter, log_event, mask_email

from tests.unit.site_form_fakes import PERSON_EMAIL


def test_g11_mask_email() -> None:
    assert mask_email(PERSON_EMAIL) == "t***@e***.com"
    assert mask_email("a@b.co") == "a***@b***.co"


def test_g11_masking_filter_rewrites_emails_in_message_and_fields() -> None:
    record = logging.LogRecord("x", logging.INFO, "f", 1, f"sent to {PERSON_EMAIL}", None, None)
    fields: dict[str, object] = {"note": f"from {PERSON_EMAIL}", "n": 3}
    record.__dict__["fields"] = fields
    assert MaskingFilter().filter(record) is True
    assert PERSON_EMAIL not in record.getMessage()
    assert PERSON_EMAIL not in json.dumps(record.__dict__["fields"])
    assert record.__dict__["fields"]["n"] == 3


def test_json_formatter_outputs_event_and_fields() -> None:
    record = logging.LogRecord("x", logging.INFO, "f", 1, "enquiry_stored", None, None)
    record.__dict__["fields"] = {"id": "1"}
    data = json.loads(JsonFormatter().format(record))
    assert data == {"level": "INFO", "event": "enquiry_stored", "id": "1"}


def test_log_event_attaches_fields(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("exaktiv_site_form.test_event")
    with caplog.at_level(logging.INFO, logger=logger.name):
        log_event(logger, logging.INFO, "enquiry_stored", enquiry_id="abc")
    assert caplog.records[0].__dict__["fields"] == {"enquiry_id": "abc"}
