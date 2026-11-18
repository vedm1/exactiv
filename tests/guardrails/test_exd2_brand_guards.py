"""EXD2: brand sync and guards for ui/."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / "scripts" / "sync_brand.py"
CHECK_BRAND = ROOT / "brand" / "tokens" / "check_brand.py"
CHECK_EXTERNAL = ROOT / "scripts" / "check_no_external.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def tree(tmp_path: Path) -> Path:
    """Copy only what the sync script reads and writes."""
    for rel in ("brand", "ui/src", "ui/public"):
        shutil.copytree(ROOT / rel, tmp_path / rel)
    return tmp_path


def test_tokens_in_sync() -> None:
    result = run(str(SYNC), "--check")
    assert result.returncode == 0, result.stdout + result.stderr


def test_sync_detects_edited_copy(tmp_path: Path) -> None:
    root = tree(tmp_path / "copy")
    target = root / "ui/src/tokens/tokens.css"
    target.write_text(target.read_text() + "\n")
    result = run(str(SYNC), "--check", "--root", str(root))
    assert result.returncode == 1
    assert "tokens.css" in result.stdout


def test_sync_detects_missing_font(tmp_path: Path) -> None:
    root = tree(tmp_path / "copy")
    next((root / "ui/public/fonts").glob("*.woff2")).unlink()
    result = run(str(SYNC), "--check", "--root", str(root))
    assert result.returncode == 1


def test_sync_writes_copies(tmp_path: Path) -> None:
    root = tree(tmp_path / "copy")
    (root / "ui/src/styles/exaktiv.css").unlink()
    assert run(str(SYNC), "--root", str(root)).returncode == 0
    assert run(str(SYNC), "--check", "--root", str(root)).returncode == 0


def test_planted_hex_fails_brand_check(tmp_path: Path) -> None:
    folder = tmp_path / "planted"
    folder.mkdir()
    (folder / "Planted.tsx").write_text(
        'export const P = () => <p style={{ color: "#ff0000" }}>x</p>;\n'
    )
    result = run(str(CHECK_BRAND), str(folder))
    assert result.returncode == 1
    assert "hex colour" in result.stdout


def test_clean_component_passes_brand_check(tmp_path: Path) -> None:
    folder = tmp_path / "clean"
    folder.mkdir()
    (folder / "Clean.tsx").write_text(
        'export const C = () => <p style={{ color: "var(--ex-act)" }}>x</p>;\n'
    )
    assert run(str(CHECK_BRAND), str(folder)).returncode == 0


def test_external_font_host_in_build_fails(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">'
    )
    result = run(str(CHECK_EXTERNAL), str(tmp_path))
    assert result.returncode == 1
    assert "fonts.googleapis.com" in result.stdout


def test_clean_build_passes_external_check(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text('<link rel="stylesheet" href="/fonts/fonts.css">')
    (tmp_path / "a.css").write_text(
        "a{background:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E\")}"
    )
    assert run(str(CHECK_EXTERNAL), str(tmp_path)).returncode == 0
