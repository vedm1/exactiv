"""EXL1: build the synthetic legacy repository with its scripted commit series.

Usage: build_legacy_corpus.py DEST
Creates a new git repository in DEST (must not exist or be empty): commit c00 holds
`synthetic/base/`; each later commit applies one patch from `commit_series.yaml`.
Author, committer, dates and messages are fixed, so two builds give the same commit IDs.
Prints one line per commit: `<name> <sha>`. Never writes inside the Exaktiv repository.
"""

import os
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

CORPUS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "legacy" / "synthetic"
FIXED = {
    "GIT_AUTHOR_NAME": "Corpus Bot",
    "GIT_AUTHOR_EMAIL": "corpus@example.invalid",
    "GIT_COMMITTER_NAME": "Corpus Bot",
    "GIT_COMMITTER_EMAIL": "corpus@example.invalid",
}
FIRST_DAY = date(2026, 1, 5)


def run(repo: Path, env: dict[str, str], *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False, env=env
    )
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])} failed: {done.stderr.strip()[:300]}")
    return done.stdout.strip()


def commit_env(index: int) -> dict[str, str]:
    stamp = f"{(FIRST_DAY + timedelta(days=index)).isoformat()}T10:00:00 +0000"
    base = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    base.update(FIXED)
    base["GIT_AUTHOR_DATE"] = stamp
    base["GIT_COMMITTER_DATE"] = stamp
    base["GIT_CONFIG_GLOBAL"] = os.devnull
    base["GIT_CONFIG_SYSTEM"] = os.devnull
    return base


def build(dest: Path, corpus: Path = CORPUS) -> list[tuple[str, str]]:
    """Build the repository in `dest`. Returns (commit name, sha) in order."""
    if dest.exists() and any(dest.iterdir()):
        raise RuntimeError(f"{dest} is not empty")
    dest.mkdir(parents=True, exist_ok=True)
    series = yaml.safe_load((corpus / "commit_series.yaml").read_text())
    key = yaml.safe_load((corpus / "answer_key.yaml").read_text())

    env = commit_env(0)
    run(dest, env, "init", "-q", "-b", "main")
    shutil.copytree(corpus / "base", dest, dirs_exist_ok=True)
    run(dest, env, "add", "-A")
    run(dest, env, "commit", "-q", "-m", "Initial import")
    result = [(str(key["base_commit"]), run(dest, env, "rev-parse", "HEAD"))]

    for index, step in enumerate(series["steps"], start=1):
        env = commit_env(index)
        run(dest, env, "apply", "--whitespace=nowarn", str(corpus / step["patch"]))
        run(dest, env, "add", "-A")
        run(dest, env, "commit", "-q", "-m", str(step["message"]))
        result.append((str(step["commit"]), run(dest, env, "rev-parse", "HEAD")))
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    for name, sha in build(Path(argv[0])):
        print(name, sha)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
