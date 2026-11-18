"""G9: secrets stay out of git, logs and config examples."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from exaktiv_core.settings import Settings

ROOT = Path(__file__).resolve().parents[2]


def fake_key_file(directory: Path) -> None:
    # Built at run time from two parts, so this source file does not hold a key.
    key = "AKIA" + "QYLPMN5HHHFPZAM2"
    (directory / "config.py").write_text(f'aws_access_key_id = "{key}"\n')


def gitleaks() -> str:
    path = shutil.which("gitleaks")
    if path is None:
        if os.environ.get("CI"):
            pytest.fail("gitleaks must be installed in CI")
        pytest.skip("gitleaks not installed")
    return path


def scan(path: Path) -> int:
    cmd = [gitleaks(), "detect", "--no-git", "--source", str(path), "--no-banner", "--redact"]
    return subprocess.run(
        [*cmd, "--config", str(ROOT / ".gitleaks.toml")], capture_output=True, check=False
    ).returncode


def test_g9_planted_secret_fails_scan(tmp_path: Path) -> None:
    fake_key_file(tmp_path)
    assert scan(tmp_path) != 0


def test_g9_clean_directory_passes_scan(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    assert scan(tmp_path) == 0


def test_g9_env_example_has_no_values() -> None:
    lines = [ln for ln in (ROOT / ".env.example").read_text().splitlines() if ln.strip()]
    assert lines
    for line in lines:
        name, sep, value = line.partition("=")
        assert sep == "=" and name.isupper() and value == "", line


def test_g9_gitignore_covers_env() -> None:
    assert ".env" in (ROOT / ".gitignore").read_text().splitlines()


def test_g9_settings_hide_secrets() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        postgres_password="pw-should-not-show",  # type: ignore[arg-type]
        minio_access_key="ak-should-not-show",  # type: ignore[arg-type]
        minio_secret_key="sk-should-not-show",  # type: ignore[arg-type]
    )
    text = repr(settings) + str(settings)
    for secret in ("pw-should-not-show", "ak-should-not-show", "sk-should-not-show"):
        assert secret not in text
