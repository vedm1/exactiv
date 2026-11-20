"""G8: fail when a fixture file has no row in SOURCE.md.

Usage: check_fixture_sources.py [fixtures_dir]   (default: tests/fixtures)
"""

import sys
from pathlib import Path


def listed_files(source_md: Path) -> set[str]:
    """Rows of the table. A row `dir/**` covers a whole subtree; its Origin must not be empty."""
    names: set[str] = set()
    for line in source_md.read_text().splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        cell = cells[0]
        if cell and cell != "File" and not set(cell) <= {"-", " "}:
            if cell.endswith("/**") and not (len(cells) > 1 and cells[1]):
                continue
            names.add(cell)
    return names


def is_listed(rel: str, listed: set[str]) -> bool:
    if rel in listed:
        return True
    return any(g.endswith("/**") and rel.startswith(g[:-2]) for g in listed)


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
        and not is_listed(str(p.relative_to(root)), listed)
    )
    for name in missing:
        print(f"fixture without source note: {name}")
    return 1 if missing else 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "tests/fixtures"
    sys.exit(main(Path(arg)))
