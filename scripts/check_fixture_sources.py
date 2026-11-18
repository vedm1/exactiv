"""G8: fail when a fixture file has no row in SOURCE.md.

Usage: check_fixture_sources.py [fixtures_dir]   (default: tests/fixtures)
"""

import sys
from pathlib import Path


def listed_files(source_md: Path) -> set[str]:
    names: set[str] = set()
    for line in source_md.read_text().splitlines():
        if not line.startswith("|"):
            continue
        cell = line.strip().strip("|").split("|")[0].strip()
        if cell and cell != "File" and not set(cell) <= {"-", " "}:
            names.add(cell)
    return names


def main(root: Path) -> int:
    source_md = root / "SOURCE.md"
    if not source_md.is_file():
        print(f"missing {source_md}")
        return 1
    listed = listed_files(source_md)
    missing = sorted(
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file()
        and p.name not in {"SOURCE.md", ".gitkeep"}
        and str(p.relative_to(root)) not in listed
    )
    for name in missing:
        print(f"fixture without source note: {name}")
    return 1 if missing else 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "tests/fixtures"
    sys.exit(main(Path(arg)))
