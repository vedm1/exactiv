"""Check the EXW3 launch record (docs/launch/EXW3-record.yaml). The launch needs every item done.

Usage: python3 scripts/check_launch_record.py [--file docs/launch/EXW3-record.yaml]
Exit 0 when every required item is `done` or `accepted` with a date, a person role and a note.
The record names no person (W-G1): `by` is a role such as `owner`.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "docs" / "launch" / "EXW3-record.yaml"
REQUIRED = (
    "privacy-review",
    "employment-check",
    "brevo-dpa",
    "brevo-retention",
    "dpa-hosting",
    "dpa-database",
    "dpa-mailbox",
    "mailbox-retention-rule",
    "dmarc-quarantine",
    "neon-restore-test",
    "name-list-run",
    "team-page-review",
    "claims-approved",
    "retention-alert",
    "independent-review",
    "go-live-approval",
)
OK = {"done", "accepted"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def problems(path: Path) -> list[str]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or data.get("version") != 1:
        return [f"{path.name}: missing or unsupported version (expected `version: 1`)"]
    items = {str(i.get("id")): i for i in data.get("items") or [] if isinstance(i, dict)}
    out: list[str] = []
    for rid in REQUIRED:
        item = items.get(rid)
        if item is None:
            out.append(f"{rid}: missing from the record")
            continue
        if item.get("status") not in OK:
            out.append(f"{rid}: status is {item.get('status')!r}, not done or accepted")
            continue
        when = str(item.get("date") or "")
        if not DATE_RE.match(when) or date.fromisoformat(when) > date.today():
            out.append(f"{rid}: needs a date (YYYY-MM-DD) that is not in the future")
        if not str(item.get("by") or "").strip() or not str(item.get("note") or "").strip():
            out.append(f"{rid}: needs `by` (a role) and a `note`")
    out += [f"{rid}: not a known launch item" for rid in items if rid not in REQUIRED]
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=DEFAULT)
    args = parser.parse_args(argv)
    found = problems(args.file)
    if found:
        print("Launch record is not complete:")
        print("\n".join(f"  - {p}" for p in found))
        return 1
    print(f"Launch record complete ({len(REQUIRED)} items).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
