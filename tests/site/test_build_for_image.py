"""EXW3: the launch build needs the flag, the name list and a complete record."""

import base64
from pathlib import Path

import build_site
import pytest
import yaml
from build_site_for_image import LaunchError, build_for_image

from tests.site.test_checks import make_launch_ready
from tests.unit.test_launch_record import full

ROOT = build_site.ROOT
BRAND = ROOT / "brand"


def names_env(text: str = "zzqx person\nyyqx person\nxxqx person\n") -> dict[str, str]:
    return {"SITE_NAMES_B64": base64.b64encode(text.encode()).decode()}


def record(tmp_path: Path, *, complete: bool) -> Path:
    items = full()
    if not complete:
        items[0] = {**items[0], "status": "pending"}
    f = tmp_path / "record.yaml"
    f.write_text(yaml.safe_dump({"version": 1, "items": items}))
    return f


def test_no_flag_builds_staging_and_needs_no_names(mini: Path, tmp_path: Path) -> None:
    out = tmp_path / "d"
    assert build_for_image(mini, BRAND, out, {}) == "staging"
    assert "noindex" in (out / "index.html").read_text()


def test_flag_without_names_fails(mini: Path, tmp_path: Path) -> None:
    (mini / "launch.flag").write_text("go\n")
    with pytest.raises(LaunchError, match="SITE_NAMES_B64"):
        build_for_image(mini, BRAND, tmp_path / "d", {}, record(tmp_path, complete=True))


def test_flag_with_bad_base64_fails(mini: Path, tmp_path: Path) -> None:
    (mini / "launch.flag").write_text("go\n")
    with pytest.raises(LaunchError, match="base64"):
        build_for_image(
            mini, BRAND, tmp_path / "d", {"SITE_NAMES_B64": "%%%"}, record(tmp_path, complete=True)
        )


def test_flag_with_an_incomplete_record_fails(mini: Path, tmp_path: Path) -> None:
    (mini / "launch.flag").write_text("go\n")
    make_launch_ready(mini)
    with pytest.raises(LaunchError, match="launch record"):
        build_for_image(mini, BRAND, tmp_path / "d", names_env(), record(tmp_path, complete=False))


def test_flag_names_and_complete_record_build_the_launch_site(mini: Path, tmp_path: Path) -> None:
    (mini / "launch.flag").write_text("go\n")
    make_launch_ready(mini)
    out = tmp_path / "d"
    assert (
        build_for_image(mini, BRAND, out, names_env(), record(tmp_path, complete=True)) == "launch"
    )
    assert "noindex" not in (out / "index.html").read_text()
    assert "Allow: /" in (out / "robots.txt").read_text()


def test_a_one_line_name_list_is_refused(mini: Path, tmp_path: Path) -> None:
    (mini / "launch.flag").write_text("go\n")
    make_launch_ready(mini)
    with pytest.raises(LaunchError, match="fewer than"):
        build_for_image(
            mini, BRAND, tmp_path / "d", names_env("zzqx person\n"), record(tmp_path, complete=True)
        )


def test_launch_build_writes_the_marker_and_staging_does_not(mini: Path, tmp_path: Path) -> None:
    staging = tmp_path / "s"
    build_for_image(mini, BRAND, staging, {})
    assert not (staging / ".launch-built").exists()
    (mini / "launch.flag").write_text("go\n")
    make_launch_ready(mini)
    out = tmp_path / "l"
    build_for_image(mini, BRAND, out, names_env(), record(tmp_path, complete=True))
    assert (out / ".launch-built").is_file()


def test_w_g1_a_name_from_the_list_fails_the_launch_build(mini: Path, tmp_path: Path) -> None:
    (mini / "launch.flag").write_text("go\n")
    make_launch_ready(mini)
    (mini / "pages" / "home.html.j2").write_text(
        '{% extends "base.html.j2" %}{% block content %}'
        "<h1>H</h1><p>By Zzqx Person.</p>{% endblock %}"
    )
    with pytest.raises(build_site.BuildError, match="name list"):
        build_for_image(mini, BRAND, tmp_path / "d", names_env(), record(tmp_path, complete=True))


def test_real_repository_has_no_launch_flag_yet() -> None:
    assert not (ROOT / "site" / "launch.flag").exists()  # the go-live commit adds it
