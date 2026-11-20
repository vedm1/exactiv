"""G12: licence allow list."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_licences.py"


def run(packages: list[dict[str, str]], tmp_path: Path) -> subprocess.CompletedProcess[str]:
    data = tmp_path / "licences.json"
    data.write_text(json.dumps(packages))
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(data)], capture_output=True, text=True, check=False
    )


def pkg(name: str, licence: str) -> dict[str, str]:
    return {"Name": name, "Version": "1.0", "License": licence}


def test_g12_disallowed_licence_fails(tmp_path: Path) -> None:
    result = run([pkg("good", "MIT"), pkg("bad", "GPL-3.0-only")], tmp_path)
    assert result.returncode == 1
    assert "bad" in result.stdout


def test_g12_unknown_licence_fails(tmp_path: Path) -> None:
    assert run([pkg("mystery", "UNKNOWN")], tmp_path).returncode == 1


def test_g12_allowed_licences_pass(tmp_path: Path) -> None:
    packages = [
        pkg("a", "MIT License"),
        pkg("b", "BSD License"),
        pkg("c", "Apache Software License"),
        pkg("d", "MPL-2.0"),
        pkg("e", "Apache-2.0 OR BSD-3-Clause"),
        pkg("f", "Python Software Foundation License"),
    ]
    assert run(packages, tmp_path).returncode == 0


def test_g12_and_expression_needs_all_parts(tmp_path: Path) -> None:
    assert run([pkg("x", "MIT AND GPL-3.0-only")], tmp_path).returncode == 1


def test_g12_licences_md_has_headers() -> None:
    lines = (ROOT / "LICENCES.md").read_text().splitlines()
    # The Fonts section (EXD1) lists brand fonts, not models or datasets.
    sections = {"## Models", "## Datasets"}
    current = ""
    tables = []
    for ln in lines:
        if ln.startswith("## "):
            current = ln.strip()
        elif ln.startswith("|") and current in sections:
            tables.append(ln)
    assert "| Model | Version | Licence | Source URL | Checked on |" in tables
    assert any(ln.startswith("| Dataset | Version | Licence |") for ln in tables)
    data_rows = [ln for ln in tables if not ln.startswith(("| Model", "| Dataset", "|--"))]
    # Since EXL0 the Datasets table holds test corpora. A row is valid only with an allowed
    # licence and a check date, or with "not chosen" (licence recorded before first use).
    for row in data_rows:
        if "not chosen" in row:
            continue
        assert "Apache-2.0" in row or "MIT" in row, f"licence not allowed or missing: {row[:60]}"
        assert re.search(r"\d{1,2} \w{3} 20\d\d", row), f"no check date: {row[:60]}"
