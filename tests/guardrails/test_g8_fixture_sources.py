"""G8: every fixture needs a source note."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_fixture_sources.py"
HEADER = "| File | Origin | Licence | Kind |\n|---|---|---|---|\n"


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True, check=False
    )


def test_g8_fixture_without_source_fails(tmp_path: Path) -> None:
    (tmp_path / "SOURCE.md").write_text(HEADER)
    (tmp_path / "invoice.pdf").write_bytes(b"x")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "invoice.pdf" in result.stdout


def test_g8_fixture_with_source_passes(tmp_path: Path) -> None:
    (tmp_path / "SOURCE.md").write_text(
        HEADER + "| invoice.pdf | made by hand | CC0 | synthetic |\n"
    )
    (tmp_path / "invoice.pdf").write_bytes(b"x")
    assert run(tmp_path).returncode == 0


def test_g8_missing_source_md_fails(tmp_path: Path) -> None:
    (tmp_path / "a.png").write_bytes(b"x")
    assert run(tmp_path).returncode == 1


def test_g8_real_fixture_directory_is_clean() -> None:
    assert run(Path(__file__).resolve().parents[1] / "fixtures").returncode == 0
