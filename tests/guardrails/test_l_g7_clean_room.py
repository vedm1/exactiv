"""L-G7: the clean-room term check. The term list lives outside the repository."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_clean_room.py"
# Synthetic stand-in term. It is not a real name (G8, L-G7).
TERM = "zzqx-forbidden-term"


def run(
    tree: Path, terms: Path | None, *extra: str, set_env: bool = True
) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != "EXAKTIV_CLEAN_ROOM_TERMS"}
    if set_env and terms is not None:
        env["EXAKTIV_CLEAN_ROOM_TERMS"] = str(terms)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tree), *extra],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def make_terms(tmp_path: Path, text: str = f"{TERM}\n") -> Path:
    terms = tmp_path / "terms.txt"
    terms.write_text(text)
    return terms


def make_tree(tmp_path: Path) -> Path:
    tree = tmp_path / "tree"
    tree.mkdir()
    return tree


def test_l_g7_term_in_file_content_fails(tmp_path: Path) -> None:
    tree = make_tree(tmp_path)
    (tree / "a.java").write_text(f"class A {{}}\n// from {TERM.upper()} code\n")
    result = run(tree, make_terms(tmp_path))
    assert result.returncode == 1
    assert "a.java:2" in result.stdout
    assert TERM not in (result.stdout + result.stderr).lower()


def test_l_g7_term_in_file_name_fails(tmp_path: Path) -> None:
    tree = make_tree(tmp_path)
    (tree / f"{TERM}.txt").write_text("clean\n")
    result = run(tree, make_terms(tmp_path))
    assert result.returncode == 1
    assert TERM not in (result.stdout + result.stderr).lower()


def test_l_g7_clean_tree_passes(tmp_path: Path) -> None:
    tree = make_tree(tmp_path)
    (tree / "a.java").write_text("class A {}\n")
    assert run(tree, make_terms(tmp_path)).returncode == 0


def test_l_g7_unset_variable_exits_2(tmp_path: Path) -> None:
    tree = make_tree(tmp_path)
    assert run(tree, None, set_env=False).returncode == 2


def test_l_g7_missing_file_and_empty_list_exit_2(tmp_path: Path) -> None:
    tree = make_tree(tmp_path)
    assert run(tree, tmp_path / "nope.txt").returncode == 2
    assert run(tree, make_terms(tmp_path, "# only a comment\n\n")).returncode == 2


def test_l_g7_allow_missing_warns_and_passes(tmp_path: Path) -> None:
    tree = make_tree(tmp_path)
    result = run(tree, None, "--allow-missing", set_env=False)
    assert result.returncode == 0
    assert "warning" in (result.stdout + result.stderr).lower()


def test_l_g7_comment_and_blank_lines_ignored(tmp_path: Path) -> None:
    tree = make_tree(tmp_path)
    (tree / "a.txt").write_text("a comment about nothing\n")
    terms = make_terms(tmp_path, f"# comment line with a comment\n\n{TERM}\n")
    assert run(tree, terms).returncode == 0


def test_l_g7_binary_file_skipped(tmp_path: Path) -> None:
    tree = make_tree(tmp_path)
    (tree / "blob.bin").write_bytes(b"\x00\x01" + TERM.encode() + b"\x00")
    assert run(tree, make_terms(tmp_path)).returncode == 0


def test_l_g7_explicit_paths_limit_the_scan(tmp_path: Path) -> None:
    tree = make_tree(tmp_path)
    (tree / "bad.txt").write_text(f"{TERM}\n")
    (tree / "good.txt").write_text("fine\n")
    result = run(tree, make_terms(tmp_path), "good.txt")
    assert result.returncode == 0


def test_l_g7_hook_registered_in_pre_commit_config() -> None:
    config = (ROOT / ".pre-commit-config.yaml").read_text()
    assert "scripts/check_clean_room.py" in config
