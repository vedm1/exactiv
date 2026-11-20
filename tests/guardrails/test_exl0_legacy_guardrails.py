"""EXL0: the legacy guardrails L-G1 to L-G15 are in force, and the scope decisions are recorded."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLAUDE_MD = ROOT / "CLAUDE.md"
PRD_L = ROOT / "docs" / "prd" / "PRD-L-exaktiv-legacy-analyser.md"
RECORD = ROOT / "docs" / "decisions" / "EXL0-record.md"
LICENCES = ROOT / "LICENCES.md"


def guardrail_rows(path: Path) -> dict[str, list[str]]:
    """Map each L-G ID to its table cells (guardrail text, how to check)."""
    rows: dict[str, list[str]] = {}
    for line in path.read_text().splitlines():
        match = re.match(r"\|\s*(L-G\d+)\s*\|(.*)\|\s*$", line)
        if match:
            rows[match.group(1)] = [c.strip() for c in match.group(2).split("|")]
    return rows


def test_l_guardrails_in_claude_md_match_prd() -> None:
    expected = {f"L-G{n}" for n in range(1, 16)}
    prd = guardrail_rows(PRD_L)
    claude = guardrail_rows(CLAUDE_MD)
    assert set(prd) == expected
    assert set(claude) == expected
    for gid, cells in claude.items():
        assert len(cells) >= 2 and all(cells[:2]), f"{gid} has an empty cell"
        assert cells == prd[gid], f"{gid} differs from PRD-L section 11"


def test_high_stakes_list_has_legacy_phases() -> None:
    text = CLAUDE_MD.read_text()
    section = text.split("## Quality bar for high-stakes work", 1)[1]
    for phase in ("EXL4", "EXL10", "EXL14"):
        assert phase in section


def test_exl0_record_has_required_decisions() -> None:
    assert RECORD.is_file()
    text = RECORD.read_text()
    assert "Employment risk" in text
    assert "Earlier analyser code" in text
    assert "start clean" in text.lower()


def test_corpus_licences_recorded() -> None:
    rows = [ln for ln in LICENCES.read_text().splitlines() if ln.startswith("|")]
    for name in ("Spring PetClinic", "Apache OFBiz"):
        row = next((r for r in rows if name in r), None)
        assert row is not None, f"no licence row for {name}"
        assert "Apache-2.0" in row
        assert re.search(r"\d{1,2} \w{3} 20\d\d", row), f"{name} row has no check date"
