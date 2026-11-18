"""Fail if a built UI references an external host (EXD2, PRD-W §8.2: no font or CDN service).

Usage: python3 scripts/check_no_external.py ui/dist
"""

import re
import sys
from pathlib import Path

ALLOWED = ("http://www.w3.org/2000/svg",)
URL = re.compile(r"https?://[^\s\"'()<>]+")
JS_HOSTS = re.compile(
    r"fonts\.googleapis|fonts\.gstatic|typekit|bunny\.net|jsdelivr|unpkg|cdnjs|//cdn\.", re.I
)


def main() -> int:
    root = Path(sys.argv[1])
    hits: list[str] = []
    for f in sorted(root.rglob("*")):
        if f.suffix not in {".html", ".css", ".js"}:
            continue
        text = f.read_text(errors="ignore")
        if f.suffix == ".js":
            hits += [f"{f}: {m.group()}" for m in JS_HOSTS.finditer(text)]
            continue
        for m in URL.finditer(text):
            if not m.group().startswith(ALLOWED):
                hits.append(f"{f}: {m.group()}")
    if hits:
        print("External host found in build:")
        print("\n".join(f"  - {h}" for h in hits))
        return 1
    print("No external host in build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
