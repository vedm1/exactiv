"""EXK0b: setup.sh refuses a bad key file before it changes anything."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "deploy/server/setup.sh"
KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHSa/wk47VV+ohKU39JsHVYbSXeJ2A7FpLbeWjTZ4nMF"
    " circleci-exaktiv"
)


def check(tmp: Path, content: str) -> subprocess.CompletedProcess[str]:
    key = tmp / "k.pub"
    key.write_text(content)
    return subprocess.run(  # noqa: S603
        ["bash", str(SCRIPT), str(key)],  # noqa: S607
        env={**os.environ, "SETUP_CHECK_ONLY": "1"},
        capture_output=True,
        text=True,
    )


def test_setup_accepts_one_ed25519_key(tmp_path: Path) -> None:
    result = check(tmp_path, KEY + "\n")
    assert result.returncode == 0 and "key file ok" in result.stdout


@pytest.mark.parametrize(
    "content",
    [
        KEY + "\n" + KEY.replace("IHSa", "IHSb") + "\n",
        KEY + "\nssh-rsa AAAA evil\n",
        "ssh-rsa AAAAB3NzaC1yc2E x\n",
        "",
        'command="x" ' + KEY + "\n",
    ],
)
def test_setup_refuses_a_bad_key_file(tmp_path: Path, content: str) -> None:
    result = check(tmp_path, content)
    assert result.returncode == 1
    assert "key file ok" not in result.stdout
