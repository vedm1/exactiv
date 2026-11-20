"""L-G7: fail when a file or file name holds a term from the private clean-room list.

The term list is a local file outside the repository. Its path is in the
environment variable EXAKTIV_CLEAN_ROOM_TERMS. One term per line; lines that
start with # and blank lines are ignored; matching is case-insensitive.
The output never prints a term, only path, line and the term number.

Usage: check_clean_room.py [--root DIR] [--allow-missing] [PATH ...]
Exit codes: 0 clean, 1 hit, 2 term list unusable (unset, missing or empty).
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ENV_VAR = "EXAKTIV_CLEAN_ROOM_TERMS"
SKIP_PARTS = {"node_modules", ".cache", ".git", ".venv"}
SKIP_NAMES = {"uv.lock", "pnpm-lock.yaml"}


def load_terms(path: Path) -> list[str]:
    terms: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            terms.append(line.lower())
    return terms


def tracked_files(root: Path) -> list[Path]:
    git = subprocess.run(
        ["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=False
    )
    if git.returncode == 0 and git.stdout.strip():
        return [root / name for name in git.stdout.splitlines()]
    return sorted(p for p in root.rglob("*") if p.is_file())


def skipped(path: Path, root: Path) -> bool:
    rel = path.relative_to(root) if path.is_absolute() else path
    return bool(SKIP_PARTS & set(rel.parts)) or path.name in SKIP_NAMES


def scan(files: list[Path], root: Path, terms: list[str]) -> list[str]:
    hits: list[str] = []
    for path in files:
        if not path.is_file() or skipped(path, root):
            continue
        rel = path.relative_to(root)
        name = str(rel).lower()
        for number, term in enumerate(terms, start=1):
            if term in name:
                hits.append(f"{rel.parent}/[name hidden]: file name matches term #{number}")
        data = path.read_bytes()
        if b"\x00" in data:
            continue
        for line_no, line in enumerate(data.decode("utf-8", errors="ignore").splitlines(), 1):
            low = line.lower()
            for number, term in enumerate(terms, start=1):
                if term in low:
                    hits.append(f"{rel}:{line_no}: matches term #{number}")
    return hits


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    value = os.environ.get(ENV_VAR)
    terms: list[str] = []
    problem = ""
    if not value:
        problem = f"{ENV_VAR} is not set"
    elif not Path(value).is_file():
        problem = f"term list file not found (from {ENV_VAR})"
    else:
        terms = load_terms(Path(value))
        if not terms:
            problem = "term list is empty"
    if problem:
        if args.allow_missing and not value:
            print(f"warning: clean-room check skipped: {problem}")
            return 0
        print(f"error: clean-room check cannot run: {problem}")
        return 2

    files = [root / p for p in args.paths] if args.paths else tracked_files(root)
    hits = scan(files, root, terms)
    for hit in hits:
        print(hit)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
