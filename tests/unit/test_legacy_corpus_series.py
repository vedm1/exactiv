"""EXL1: the scripted commit series on the synthetic repository."""

import subprocess
import sys
from pathlib import Path

from exaktiv_core.legacy_corpus import (
    load_answer_key,
    load_series,
    span_text_hash,
    spans_at,
)

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "tests" / "fixtures" / "legacy" / "synthetic"
BUILDER = ROOT / "scripts" / "build_legacy_corpus.py"


def build(dest: Path) -> list[tuple[str, str]]:
    done = subprocess.run(
        [sys.executable, str(BUILDER), str(dest)], capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stderr + done.stdout
    return [tuple(line.split()) for line in done.stdout.splitlines()]  # type: ignore[misc]


def checkout(repo: Path, sha: str) -> None:
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", sha], check=True, capture_output=True)


def test_builder_makes_14_commits_and_is_deterministic(tmp_path: Path) -> None:
    first = build(tmp_path / "one")
    second = build(tmp_path / "two")
    assert [n for n, _ in first] == [f"c{i:02d}" for i in range(14)]
    assert first == second


def test_builder_refuses_non_empty_destination(tmp_path: Path) -> None:
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "f").write_text("a")
    done = subprocess.run(
        [sys.executable, str(BUILDER), str(tmp_path / "x")], capture_output=True, text=True
    )
    assert done.returncode != 0


def test_exactly_10_rules_change_and_3_are_critical() -> None:
    key = load_answer_key(CORPUS / "answer_key.yaml")
    series = load_series(CORPUS / "commit_series.yaml")
    changed = [c.rule for s in series.steps for c in s.changed]
    assert len(changed) == len(set(changed)) == 10
    critical = {r.id for r in key.rules if r.critical}
    assert len(set(changed) & critical) >= 3
    assert all(r.startswith("R") for r in changed)


def test_replayed_spans_match_text_at_every_commit(tmp_path: Path) -> None:
    key = load_answer_key(CORPUS / "answer_key.yaml")
    series = load_series(CORPUS / "commit_series.yaml")
    repo = tmp_path / "repo"
    commits = build(repo)
    for name, sha in commits:
        checkout(repo, sha)
        for rule_id, spans in spans_at(key, series, name).items():
            for span in spans:
                assert span_text_hash(repo, span) == span.span_sha256, f"{name} {rule_id}"


def test_move_only_commits_keep_rule_text_hash() -> None:
    key = load_answer_key(CORPUS / "answer_key.yaml")
    series = load_series(CORPUS / "commit_series.yaml")
    move_only = [s for s in series.steps if s.moved and not s.changed]
    assert len(move_only) == 3
    before = {r.id: [s.span_sha256 for s in r.spans] for r in key.rules}
    for step in series.steps:
        for change in step.changed:
            before[change.rule] = [s.span_sha256 for s in change.spans]
        for move in step.moved:
            assert [s.span_sha256 for s in move.spans] == before[move.rule], (
                f"{step.commit} {move.rule}: text changed in a move-only commit"
            )


def test_every_move_only_commit_moves_at_least_one_line_range() -> None:
    key = load_answer_key(CORPUS / "answer_key.yaml")
    series = load_series(CORPUS / "commit_series.yaml")
    for step in series.steps:
        if step.moved and not step.changed:
            now = spans_at(key, series, step.commit)
            previous = spans_at(
                key,
                series,
                series.steps[series.steps.index(step) - 1].commit
                if series.steps.index(step)
                else key.base_commit,
            )
            assert any(now[m.rule] != previous[m.rule] for m in step.moved)


def test_expected_stale_equals_changed_and_excludes_moved() -> None:
    series = load_series(CORPUS / "commit_series.yaml")
    for step in series.steps:
        assert sorted(step.expected_stale) == sorted(c.rule for c in step.changed)
        assert not set(step.expected_stale) & {m.rule for m in step.moved}


def test_every_unmentioned_rule_keeps_its_span_text(tmp_path: Path) -> None:
    """A rule that is neither changed nor moved has the same text at every commit."""
    key = load_answer_key(CORPUS / "answer_key.yaml")
    series = load_series(CORPUS / "commit_series.yaml")
    repo = tmp_path / "repo"
    commits = dict(build(repo))
    mentioned = {c.rule for s in series.steps for c in s.changed} | {
        m.rule for s in series.steps for m in s.moved
    }
    checkout(repo, commits[series.steps[-1].commit])
    for rule in key.rules:
        if rule.id not in mentioned:
            for span in rule.spans:
                assert span_text_hash(repo, span) == span.span_sha256, rule.id
