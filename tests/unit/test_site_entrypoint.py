"""EXW3: the web image starts in live mode only with a launch build (marker file)."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "site" / "entrypoint.sh"


def run(mode: str, marker: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["sh", str(SCRIPT), "echo", "started"],  # noqa: S607
        env={"SITE_MODE": mode, "LAUNCH_MARKER": str(marker), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )


def test_live_mode_without_the_marker_refuses_to_start(tmp_path: Path) -> None:
    result = run("live", tmp_path / "missing")
    assert result.returncode != 0 and "started" not in result.stdout
    assert "launch build" in result.stderr


def test_live_mode_with_the_marker_starts(tmp_path: Path) -> None:
    marker = tmp_path / ".launch-built"
    marker.write_text("x")
    assert run("live", marker).stdout.strip() == "started"


def test_staging_mode_starts_without_the_marker(tmp_path: Path) -> None:
    assert run("staging", tmp_path / "missing").stdout.strip() == "started"


def test_dockerfile_uses_the_entrypoint_and_keeps_the_caddy_command() -> None:
    text = (ROOT / "site" / "Dockerfile").read_text()
    assert 'ENTRYPOINT ["/usr/local/bin/site-entrypoint"]' in text
    assert '"caddy", "run"' in text and "--chmod=0755 entrypoint.sh" in text
