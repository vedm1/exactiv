"""Build the site for the web image (EXW3). CI runs this in place of a bare `build_site.py`.

Usage: python3 scripts/build_site_for_image.py [--site site] [--out site/dist]

- Without the file `site/launch.flag`: a staging build (noindex, robots closed). Same as before.
- With `site/launch.flag`: the launch build. It needs the name list in the environment variable
  SITE_NAMES_B64 (base64 of the list, from the Doppler `ci` config; W-G1: the list stays out of the
  repository) and a complete launch record (scripts/check_launch_record.py). Else it fails.
The decoded list goes to a temporary file that is deleted after the build.
"""

import argparse
import base64
import binascii
import os
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

import build_site
import check_launch_record

ROOT = Path(__file__).resolve().parents[1]
MIN_NAMES = 3  # a one-line list is not the real list (independent review, 19 Nov 2026)


class LaunchError(Exception):
    pass


def build_for_image(
    site_dir: Path,
    brand_dir: Path,
    out_dir: Path,
    env: Mapping[str, str],
    record: Path = check_launch_record.DEFAULT,
) -> str:
    """Return "staging" or "launch"."""
    if not (site_dir / "launch.flag").is_file():
        build_site.build(site_dir, brand_dir, out_dir)
        return "staging"
    encoded = env.get("SITE_NAMES_B64", "").strip()
    if not encoded:
        raise LaunchError("site/launch.flag is set but SITE_NAMES_B64 is empty (Doppler config ci)")
    try:
        names = base64.b64decode(encoded, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise LaunchError("SITE_NAMES_B64 is not valid base64 text") from exc
    if len([n for n in names.splitlines() if n.strip() and not n.startswith("#")]) < MIN_NAMES:
        raise LaunchError(f"the name list has fewer than {MIN_NAMES} names: is it the real list?")
    open_items = check_launch_record.problems(record)
    if open_items:
        raise LaunchError("launch record is not complete: " + "; ".join(open_items))
    with tempfile.TemporaryDirectory() as tmp:
        names_file = Path(tmp) / "names.txt"
        names_file.write_text(names)
        names_file.chmod(0o600)
        build_site.build(site_dir, brand_dir, out_dir, launch=True, names_file=names_file)
    return "launch"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", type=Path, default=ROOT / "site")
    ap.add_argument("--out", type=Path, default=ROOT / "site" / "dist")
    args = ap.parse_args()
    try:
        mode = build_for_image(args.site, ROOT / "brand", args.out, os.environ)
    except (LaunchError, build_site.BuildError) as exc:
        print(f"Site build failed: {exc}", file=sys.stderr)
        return 1
    print(f"Site built in {args.out} ({mode} mode).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
