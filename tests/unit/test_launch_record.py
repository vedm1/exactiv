"""EXW3: the launch record check."""

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_launch_record as rec  # noqa: E402


def item(rid: str, **over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": rid,
        "status": "done",
        "date": "2026-11-01",
        "by": "owner",
        "note": "Checked.",
    }
    base.update(over)
    return base


def write(tmp_path: Path, items: list[dict[str, object]]) -> Path:
    f = tmp_path / "record.yaml"
    f.write_text(yaml.safe_dump({"version": 1, "items": items}))
    return f


def full() -> list[dict[str, object]]:
    return [item(r) for r in rec.REQUIRED]


def test_complete_record_passes(tmp_path: Path) -> None:
    assert rec.problems(write(tmp_path, full())) == []


def test_pending_item_fails(tmp_path: Path) -> None:
    items = full()
    items[3] = item(rec.REQUIRED[3], status="pending")
    assert any(rec.REQUIRED[3] in p for p in rec.problems(write(tmp_path, items)))


def test_missing_item_fails(tmp_path: Path) -> None:
    assert any("missing" in p for p in rec.problems(write(tmp_path, full()[1:])))


@pytest.mark.parametrize(
    "over",
    [{"date": None}, {"date": "tomorrow"}, {"date": "2999-01-01"}, {"by": ""}, {"note": ""}],
)
def test_done_item_needs_a_real_date_a_role_and_a_note(
    tmp_path: Path, over: dict[str, object]
) -> None:
    items = full()
    items[0] = item(rec.REQUIRED[0], **over)
    assert rec.problems(write(tmp_path, items))


def test_unknown_item_fails(tmp_path: Path) -> None:
    assert rec.problems(write(tmp_path, [*full(), item("surprise")]))


def test_real_record_lists_every_required_item_and_is_not_complete_yet() -> None:
    found = rec.problems(ROOT / "docs" / "launch" / "EXW3-record.yaml")
    assert not any("missing" in p or "unknown" in p for p in found)
    assert any("go-live-approval" in p for p in found)  # not done until the owner says yes


def test_w_g1_real_record_names_no_person_or_company() -> None:
    text = (ROOT / "docs" / "launch" / "EXW3-record.yaml").read_text()
    for bad in ("Valyrian", "Ved", "Pratima"):
        assert bad not in text
