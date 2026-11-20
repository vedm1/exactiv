"""EXK0-dbos: Temporal is gone from the stack (one workflow engine)."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()


def test_no_temporal_left() -> None:
    files = subprocess.run(  # noqa: S603
        ["git", "ls-files", "*.py", "*.toml", "*.yml", "*.yaml", ".env.example", "scripts/*.sh"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    hits = [
        f
        for f in files
        if (ROOT / f).is_file()
        and (ROOT / f) != SELF
        and "temporal" in (ROOT / f).read_text(errors="ignore").lower()
    ]
    assert hits == []
