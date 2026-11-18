"""G12: fail when a dependency licence is outside the allow list.

Usage: check_licences.py [licences.json]
Input: `pip-licenses --from=mixed --format=json` output (file, or stdin when no argument).
Exceptions: config/licence_exceptions.yaml.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ALLOWED = {
    "MIT",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "Apache-2.0",
    "ISC",
    "PSF-2.0",
    "MPL-2.0",
    "0BSD",
    "Unlicense",
}

ALIASES = {
    "mit license": "MIT",
    "mit": "MIT",
    "bsd license": "BSD-3-Clause",
    "bsd": "BSD-3-Clause",
    "3-clause bsd license": "BSD-3-Clause",
    "2-clause bsd license": "BSD-2-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "new bsd license": "BSD-3-Clause",
    "simplified bsd license": "BSD-2-Clause",
    "apache software license": "Apache-2.0",
    "apache 2.0": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "apache license, version 2.0": "Apache-2.0",
    "isc license (iscl)": "ISC",
    "isc license": "ISC",
    "isc": "ISC",
    "python software foundation license": "PSF-2.0",
    "psf-2.0": "PSF-2.0",
    "mozilla public license 2.0 (mpl 2.0)": "MPL-2.0",
    "mpl-2.0": "MPL-2.0",
    "0bsd": "0BSD",
    "the unlicense (unlicense)": "Unlicense",
    "unlicense": "Unlicense",
}


def normalise(term: str) -> str:
    cleaned = term.strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1]
    return ALIASES.get(cleaned.lower(), cleaned)


def term_ok(term: str) -> bool:
    """One licence text: 'A AND B' needs all parts, 'A OR B' needs any part."""
    and_parts = re.split(r"\s+AND\s+", term)
    return all(
        any(normalise(alt) in ALLOWED for alt in re.split(r"\s+OR\s+", part)) for part in and_parts
    )


def licence_ok(text: str) -> bool:
    # pip-licenses joins several classifiers with ';'. All of them must be allowed.
    return all(term_ok(t) for t in text.split(";") if t.strip())


def load_exceptions(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    data = yaml.safe_load(path.read_text()) or {}
    return {str(e["package"]).lower() for e in data.get("exceptions", [])}


INTERNAL_PREFIX = "exaktiv-"  # our own workspace packages have no licence metadata


def main(packages: list[dict[str, Any]], exceptions: set[str]) -> int:
    bad = [
        p
        for p in packages
        if not str(p["Name"]).lower().startswith(INTERNAL_PREFIX)
        and str(p["Name"]).lower() not in exceptions
        and not licence_ok(str(p["License"]))
    ]
    for p in bad:
        print(f"licence not allowed: {p['Name']} {p.get('Version', '')} -> {p['License']}")
    return 1 if bad else 0


if __name__ == "__main__":
    raw = Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else sys.stdin.read()
    root = Path(__file__).resolve().parents[1]
    sys.exit(main(json.loads(raw), load_exceptions(root / "config" / "licence_exceptions.yaml")))
