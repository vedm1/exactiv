"""EXL1: the public-set fetch script pins a commit, keeps licence files and checks size."""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "fetch_legacy_public_sets.py"
REAL_SETS = Path(__file__).resolve().parents[1] / "fixtures" / "legacy" / "public" / "sets.yaml"


def git(repo: Path, *args: str) -> str:
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        "HOME": str(repo),
    }
    out = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=env
    )
    return out.stdout.strip()


def make_upstream(
    tmp_path: Path, with_notice: bool = True, java_lines: int = 50
) -> tuple[Path, str]:
    repo = tmp_path / "upstream"
    (repo / "apps" / "a").mkdir(parents=True)
    (repo / "apps" / "b").mkdir(parents=True)
    (repo / "LICENSE").write_text("Apache License\n")
    if with_notice:
        (repo / "NOTICE").write_text("Notice text\n")
    (repo / "apps" / "a" / "A.java").write_text("class A {}\n" * java_lines)
    (repo / "apps" / "b" / "B.java").write_text("class B {}\n" * 5000)
    git(repo, "init", "-q")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "init")
    return repo, git(repo, "rev-parse", "HEAD")


def write_sets(tmp_path: Path, url: Path, commit: str, lines: tuple[int, int] = (10, 100)) -> Path:
    cfg = {
        "version": 1,
        "sets": {
            "demo": {
                "url": str(url),
                "commit": commit,
                "licence": "Apache-2.0",
                "licence_files": ["LICENSE", "NOTICE"],
                "include": ["apps/a"],
                "java_lines": list(lines),
            }
        },
    }
    path = tmp_path / "sets.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return path


def run(sets: Path, dest: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--sets", str(sets), "--dest", str(dest), "--set", "demo"],
        capture_output=True,
        text=True,
        check=False,
    )


def test_fetch_copies_include_paths_and_licence_files(tmp_path: Path) -> None:
    repo, sha = make_upstream(tmp_path)
    result = run(write_sets(tmp_path, repo, sha), tmp_path / "out")
    assert result.returncode == 0, result.stdout + result.stderr
    out = tmp_path / "out" / "demo"
    assert (out / "apps" / "a" / "A.java").is_file()
    assert not (out / "apps" / "b").exists()
    assert (out / "NOTICE").read_text() == "Notice text\n"
    assert (out / "LICENSE").is_file()
    assert "java lines: 50" in result.stdout


def test_fetch_missing_notice_fails(tmp_path: Path) -> None:
    repo, sha = make_upstream(tmp_path, with_notice=False)
    result = run(write_sets(tmp_path, repo, sha), tmp_path / "out")
    assert result.returncode == 1
    assert "NOTICE" in result.stdout


def test_fetch_line_count_out_of_range_fails(tmp_path: Path) -> None:
    repo, sha = make_upstream(tmp_path, java_lines=500)
    result = run(write_sets(tmp_path, repo, sha), tmp_path / "out")
    assert result.returncode == 1
    assert "java lines" in result.stdout


def test_fetch_unknown_commit_fails(tmp_path: Path) -> None:
    repo, _ = make_upstream(tmp_path)
    result = run(write_sets(tmp_path, repo, "0" * 40), tmp_path / "out")
    assert result.returncode == 1


def test_fetch_refuses_short_commit_in_config(tmp_path: Path) -> None:
    repo, sha = make_upstream(tmp_path)
    result = run(write_sets(tmp_path, repo, sha[:7]), tmp_path / "out")
    assert result.returncode == 1
    assert "40" in result.stdout


def test_fetch_failure_leaves_no_partial_output(tmp_path: Path) -> None:
    repo, sha = make_upstream(tmp_path, with_notice=False)
    run(write_sets(tmp_path, repo, sha), tmp_path / "out")
    assert not (tmp_path / "out" / "demo").exists()


@pytest.mark.parametrize("name", ["petclinic", "ofbiz"])
def test_real_pin_list_is_complete(name: str) -> None:
    sets = yaml.safe_load(REAL_SETS.read_text())["sets"]
    entry = sets[name]
    assert len(entry["commit"]) == 40
    assert entry["licence"] == "Apache-2.0"
    assert entry["url"].startswith("https://")
    if name == "ofbiz":
        assert "NOTICE" in entry["licence_files"]


def test_real_pin_list_matches_licences_md() -> None:
    licences = (Path(__file__).resolve().parents[2] / "LICENCES.md").read_text()
    sets = yaml.safe_load(REAL_SETS.read_text())["sets"]
    for entry in sets.values():
        assert entry["commit"][:7] in licences
