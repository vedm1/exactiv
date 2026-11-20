"""EXL1: the answer-key loader checks its own rules."""

from pathlib import Path

import pytest
from exaktiv_core.legacy_corpus import (
    AnswerKey,
    Rule,
    Span,
    load_answer_key,
    span_hash,
    span_text_hash,
)
from pydantic import ValidationError

H = "0" * 64


def span(path: str = "A.java") -> dict[str, object]:
    return {"path": path, "start_line": 1, "end_line": 2, "span_sha256": H}


def rule(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "R01",
        "kind": "calculation",
        "critical": True,
        "statement": "s",
        "identifiers": ["x"],
        "spans": [span()],
        "expected_label": "confirmed",
        "ambiguity": "none",
    }
    base.update(over)
    return base


def test_valid_rule_loads() -> None:
    assert Rule.model_validate(rule()).id == "R01"


def test_critical_flag_must_match_kind() -> None:
    with pytest.raises(ValidationError):
        Rule.model_validate(rule(critical=False))


def test_ambiguous_rule_is_never_confirmed() -> None:
    with pytest.raises(ValidationError):
        Rule.model_validate(rule(id="A01", ambiguity="split_logic"))
    ok = Rule.model_validate(rule(id="A01", ambiguity="split_logic", expected_label="gap"))
    assert ok.expected_label == "gap"


def test_clear_rule_must_be_confirmed_and_not_ambiguous() -> None:
    with pytest.raises(ValidationError):
        Rule.model_validate(rule(expected_label="inferred"))
    with pytest.raises(ValidationError):
        Rule.model_validate(rule(ambiguity="split_logic"))


def test_span_order_and_hash_shape() -> None:
    with pytest.raises(ValidationError):
        Span(path="a", start_line=5, end_line=4, span_sha256=H)
    with pytest.raises(ValidationError):
        Span(path="a", start_line=1, end_line=1, span_sha256="xyz")


def test_extra_fields_are_refused() -> None:
    with pytest.raises(ValidationError):
        AnswerKey.model_validate(
            {"version": 1, "corpus": "c", "base_commit": "c00", "rules": [], "decoys": [], "x": 1}
        )


def test_span_hash_form(tmp_path: Path) -> None:
    (tmp_path / "A.java").write_bytes(b"one\r\ntwo\r\nthree\r\n")
    s = Span(path="A.java", start_line=2, end_line=3, span_sha256=span_hash(["two", "three"]))
    assert span_text_hash(tmp_path, s) == s.span_sha256
    past = Span(path="A.java", start_line=2, end_line=9, span_sha256=H)
    with pytest.raises(ValueError, match="past the end"):
        span_text_hash(tmp_path, past)


def test_load_answer_key_from_file(tmp_path: Path) -> None:
    path = tmp_path / "k.yaml"
    path.write_text("version: 1\ncorpus: c\nbase_commit: c00\nrules: []\ndecoys: []\n")
    assert load_answer_key(path).corpus == "c"
