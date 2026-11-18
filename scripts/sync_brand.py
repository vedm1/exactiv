"""Copy brand files into ui/ (EXD2). The copies are byte for byte and are never edited by hand.

Usage: python3 scripts/sync_brand.py [--check] [--root PATH]
  (no flag)  write the copies
  --check    write nothing; exit 1 if a copy is missing or different
"""

import argparse
import shutil
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def pairs(root: Path) -> list[tuple[Path, Path]]:
    brand, ui = root / "brand", root / "ui"
    out: list[tuple[Path, Path]] = [
        (brand / "tokens" / "tokens.css", ui / "src" / "tokens" / "tokens.css"),
        (brand / "tokens" / "tokens.ts", ui / "src" / "tokens" / "tokens.ts"),
        (brand / "components" / "exaktiv.css", ui / "src" / "styles" / "exaktiv.css"),
    ]
    fonts = brand / "fonts"
    for src in sorted([*fonts.glob("*.woff2"), fonts / "fonts.css", *fonts.glob("OFL-*.txt")]):
        out.append((src, ui / "public" / "fonts" / src.name))
    for name in (
        "favicon.svg",
        "favicon.ico",
        "apple-touch-icon.png",
        "icon-192.png",
        "icon-512.png",
        "site.webmanifest",
    ):
        out.append((brand / "favicon" / name, ui / "public" / name))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root: Path = args.root.resolve()
    bad = 0
    for src, dst in pairs(root):
        same = dst.exists() and dst.read_bytes() == src.read_bytes()
        if same:
            continue
        rel = dst.relative_to(root)
        if args.check:
            print(f"out of sync: {rel}")
            bad += 1
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            print(f"copied: {rel}")
    if bad:
        print("Run: python3 scripts/sync_brand.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
