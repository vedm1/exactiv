"""EXL1: the synthetic repository "harbour-billing" and its answer key."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from exaktiv_core.legacy_corpus import load_answer_key, span_text_hash

CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "legacy" / "synthetic"
BASE = CORPUS / "base"
KEY = CORPUS / "answer_key.yaml"


def java_files() -> list[Path]:
    return sorted(BASE.rglob("*.java"))


def java_line_count() -> int:
    return sum(len(p.read_bytes().splitlines()) for p in java_files())


def test_java_line_count_between_5000_and_10000() -> None:
    assert 5000 <= java_line_count() <= 10000


@pytest.mark.skipif(shutil.which("javac") is None, reason="no JDK on this machine")
def test_base_compiles_with_javac_release_8(tmp_path: Path) -> None:
    files = [str(p) for p in java_files()]
    done = subprocess.run(
        ["javac", "--release", "8", "-Xlint:-options", "-d", str(tmp_path), *files],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr[:2000]


def test_key_has_40_clear_and_5_ambiguous_rules() -> None:
    key = load_answer_key(KEY)
    ids = [r.id for r in key.rules]
    assert len(ids) == len(set(ids)) == 45
    assert sorted(i for i in ids if i.startswith("R")) == [f"R{n:02d}" for n in range(1, 41)]
    assert sorted(i for i in ids if i.startswith("A")) == [f"A{n:02d}" for n in range(1, 6)]


def test_ambiguous_rules_never_expected_confirmed() -> None:
    for rule in load_answer_key(KEY).rules:
        if rule.id.startswith("A"):
            assert rule.expected_label in {"inferred", "gap"}, rule.id
            assert rule.ambiguity != "none", rule.id


def test_critical_flag_matches_kind_and_coverage() -> None:
    key = load_answer_key(KEY)
    clear = [r for r in key.rules if r.id.startswith("R")]
    assert sum(r.critical for r in clear) >= 12
    assert len({r.kind for r in clear}) >= 4


def test_every_span_hash_matches_base_tree() -> None:
    key = load_answer_key(KEY)
    for rule in key.rules:
        for span in rule.spans:
            assert (BASE / span.path).is_file(), f"{rule.id}: {span.path} missing"
            assert span_text_hash(BASE, span) == span.span_sha256, rule.id
    for decoy in key.decoys:
        assert span_text_hash(BASE, decoy.span) == decoy.span.span_sha256, decoy.id


def test_decoys_have_5_dead_code_and_5_misleading_comments() -> None:
    key = load_answer_key(KEY)
    kinds = [d.type for d in key.decoys]
    assert kinds.count("dead_code") == 5
    assert kinds.count("misleading_comment") == 5


def test_decoy_spans_do_not_overlap_rule_spans() -> None:
    key = load_answer_key(KEY)
    rule_spans = [s for r in key.rules for s in r.spans]
    for decoy in key.decoys:
        d = decoy.span
        for s in rule_spans:
            if s.path == d.path:
                assert d.end_line < s.start_line or d.start_line > s.end_line, (
                    f"{decoy.id} overlaps a rule span"
                )


def test_no_person_company_or_author_tag_in_source() -> None:
    pattern = re.compile(r"@author|\(c\)\s+\d|copyright|\bGmbH\b|\bInc\.|\bLtd\b", re.IGNORECASE)
    for path in java_files():
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            assert not pattern.search(line), f"{path.name}:{number}"


def test_no_rule_marker_in_source() -> None:
    pattern = re.compile(r"\b(RULE|R[0-3]\d|A0[1-5])\b")
    for path in java_files():
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            assert not pattern.search(line), f"{path.name}:{number}"
