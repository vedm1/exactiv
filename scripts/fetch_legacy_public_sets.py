"""EXL1: fetch a pinned public code base for the legacy corpus into a git-ignored folder.

Usage: fetch_legacy_public_sets.py --set petclinic|ofbiz [--sets FILE] [--dest DIR]
The pin list is tests/fixtures/legacy/public/sets.yaml. Nothing is committed to git.
Exit codes: 0 done, 1 refused (bad pin, missing licence file, size out of range, git failure).
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETS = ROOT / "tests" / "fixtures" / "legacy" / "public" / "sets.yaml"
DEFAULT_DEST = ROOT / ".cache" / "legacy-public"


class Refused(Exception):
    pass


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if done.returncode != 0:
        raise Refused(f"git {args[0]} failed: {done.stderr.strip()[:200]}")
    return done.stdout.strip()


def count_java_lines(root: Path) -> int:
    total = 0
    for path in root.rglob("*.java"):
        total += len(path.read_bytes().splitlines())
    return total


def copy_path(src: Path, dst: Path) -> None:
    if not src.exists():
        raise Refused(f"path not in upstream: {src.name}")
    if src.is_dir():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git"), dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def fetch(name: str, sets_file: Path, dest_root: Path) -> Path:
    config: dict[str, Any] = yaml.safe_load(sets_file.read_text())["sets"]
    if name not in config:
        raise Refused(f"unknown set: {name}")
    entry = config[name]
    commit = str(entry["commit"])
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise Refused("the pinned commit must be a full 40-character SHA")

    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "clone"
        clone.mkdir()
        git(clone, "init", "-q")
        git(clone, "fetch", "-q", "--depth", "1", str(entry["url"]), commit)
        git(clone, "checkout", "-q", "FETCH_HEAD")
        if git(clone, "rev-parse", "HEAD") != commit:
            raise Refused("fetched commit differs from the pin")

        staged = Path(tmp) / "staged"
        staged.mkdir()
        for rel in entry["include"]:
            copy_path(clone / rel if rel != "." else clone, staged / rel if rel != "." else staged)
        for rel in entry["licence_files"]:
            if not (clone / rel).is_file():
                raise Refused(f"licence file missing upstream: {rel}")
            copy_path(clone / rel, staged / rel)

        lines = count_java_lines(staged)
        low, high = entry["java_lines"]
        print(f"{name}: commit {commit[:7]}, java lines: {lines}")
        if not low <= lines <= high:
            raise Refused(f"java lines {lines} outside {low}..{high}")

        target = dest_root / name
        if target.exists():
            shutil.rmtree(target)
        dest_root.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staged), str(target))
        return target


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", required=True, dest="name")
    parser.add_argument("--sets", default=str(DEFAULT_SETS))
    parser.add_argument("--dest", default=str(DEFAULT_DEST))
    args = parser.parse_args(argv)
    try:
        target = fetch(args.name, Path(args.sets), Path(args.dest))
    except Refused as err:
        print(f"refused: {err}")
        return 1
    print(f"ready: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
