"""Typed loader for the legacy test corpus (EXL1): answer key and commit series.

Span hash form (EXL1; EXL4 may adopt or replace it): SHA-256 over the lines
start_line..end_line (1-based, inclusive), UTF-8, LF line ends, no final newline.
"""

import hashlib
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Kind = Literal[
    "business_rule",
    "validation",
    "calculation",
    "state_transition",
    "security_control",
    "integration",
    "data_access",
]
CRITICAL_KINDS: frozenset[str] = frozenset(
    {"calculation", "state_transition", "security_control", "business_rule"}
)
Label = Literal["confirmed", "inferred", "gap"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Span(_Strict):
    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    span_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _ordered(self) -> "Span":
        if self.end_line < self.start_line:
            raise ValueError("end_line before start_line")
        return self


class Rule(_Strict):
    id: str = Field(pattern=r"^[RA]\d{2}$")
    kind: Kind
    critical: bool
    statement: str = Field(min_length=1)
    identifiers: list[str] = Field(min_length=1)
    spans: list[Span] = Field(min_length=1)
    expected_label: Label
    ambiguity: str

    @model_validator(mode="after")
    def _consistent(self) -> "Rule":
        if self.critical != (self.kind in CRITICAL_KINDS):
            raise ValueError(f"{self.id}: critical flag does not match kind")
        ambiguous = self.id.startswith("A")
        if ambiguous and self.expected_label == "confirmed":
            raise ValueError(f"{self.id}: an ambiguous rule is never confirmed")
        if not ambiguous and (self.expected_label != "confirmed" or self.ambiguity != "none"):
            raise ValueError(f"{self.id}: a clear rule is confirmed with ambiguity none")
        if ambiguous and self.ambiguity == "none":
            raise ValueError(f"{self.id}: an ambiguous rule names its ambiguity")
        return self


class Decoy(_Strict):
    id: str = Field(pattern=r"^D\d{2}$")
    type: Literal["dead_code", "misleading_comment"]
    span: Span
    note: str


class AnswerKey(_Strict):
    version: int
    corpus: str
    base_commit: str
    rules: list[Rule]
    decoys: list[Decoy]


class Change(_Strict):
    rule: str
    new_statement: str
    spans: list[Span] = Field(min_length=1)


class Moved(_Strict):
    rule: str
    spans: list[Span] = Field(min_length=1)


class Step(_Strict):
    commit: str
    patch: str
    message: str
    changed: list[Change] = []
    moved: list[Moved] = []
    expected_stale: list[str] = []


class Series(_Strict):
    version: int
    steps: list[Step]


def span_hash(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def span_text_hash(root: Path, span: Span) -> str:
    """Hash of the span's lines as they are in the tree at `root`."""
    lines = (root / span.path).read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    if span.end_line > len(lines):
        raise ValueError(f"{span.path}: line {span.end_line} is past the end of the file")
    return span_hash(lines[span.start_line - 1 : span.end_line])


def load_answer_key(path: Path) -> AnswerKey:
    return AnswerKey.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_series(path: Path) -> Series:
    return Series.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def spans_at(key: AnswerKey, series: Series, commit: str) -> dict[str, list[Span]]:
    """Spans of every rule after the given commit, by replaying `changed` and `moved`."""
    current = {rule.id: list(rule.spans) for rule in key.rules}
    if commit == key.base_commit:
        return current
    for step in series.steps:
        for change in step.changed:
            current[change.rule] = list(change.spans)
        for move in step.moved:
            current[move.rule] = list(move.spans)
        if step.commit == commit:
            return current
    raise KeyError(f"unknown commit {commit}")
