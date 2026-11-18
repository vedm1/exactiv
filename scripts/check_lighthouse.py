"""Run Lighthouse (pinned) on every page of a built site and fail below the PRD-W bar (EXD5).

Usage: python3 scripts/check_lighthouse.py [--dist site/dist] [--site site]
Needs Node with pnpm, and Chrome. Set CHROME_PATH if Chrome is not found.

Bar (PRD-W section 10): 90 or more in performance, accessibility, best practices and SEO,
on a mobile profile, and no failed accessibility audit at all.
A staging build is noindex by design and would fail the SEO crawl audit. So the script audits a
temporary copy with the noindex meta removed and robots.txt open, the same pages a launch build
serves. Tests in tests/site/test_checks.py check that a launch build has no noindex.
"""

import argparse
import functools
import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import build_site

LIGHTHOUSE = "lighthouse@13.6.0"
CATEGORIES = ("performance", "accessibility", "best-practices", "seo")
BAR = 0.9


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


def run_one(url: str, out: Path) -> dict[str, object]:
    cmd = [
        "pnpm", "dlx", LIGHTHOUSE, url,
        "--only-categories=" + ",".join(CATEGORIES),
        "--output=json", f"--output-path={out}", "--quiet",
        "--chrome-flags=--headless=new --no-sandbox",
    ]  # fmt: skip
    subprocess.run(cmd, check=True, capture_output=True, text=True)  # noqa: S603
    data: dict[str, object] = json.loads(out.read_text())
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", type=Path, default=build_site.ROOT / "site")
    ap.add_argument("--dist", type=Path, default=build_site.ROOT / "site" / "dist")
    args = ap.parse_args()
    _, pages = build_site.load_config(args.site)
    indexable = Path(tempfile.mkdtemp()) / "dist"
    shutil.copytree(args.dist, indexable)
    for f in indexable.rglob("*.html"):
        f.write_text(re.sub(r'<meta name="robots" content="noindex">\n?', "", f.read_text()))
    (indexable / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(Quiet, directory=str(indexable))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        for page in pages:
            report = run_one(base + page.path, Path(tmp) / f"{page.slug}.json")
            cats = report["categories"]
            audits = report["audits"]
            line = []
            for cat in CATEGORIES:
                score = cats[cat]["score"]  # type: ignore[index]
                line.append(f"{cat} {round(score * 100)}")
                if score < BAR:
                    failures.append(f"{page.slug}: {cat} {round(score * 100)} is below 90")
            for ref in cats["accessibility"]["auditRefs"]:  # type: ignore[index]
                a = audits[ref["id"]]  # type: ignore[index]
                if a["score"] == 0:
                    failures.append(f"{page.slug}: failed accessibility audit {ref['id']}")
            print(f"{page.slug:24s} " + "  ".join(line))
    server.shutdown()
    if failures:
        print("Lighthouse bar not met:")
        print("\n".join(f"  - {f}" for f in failures))
        return 1
    print("Lighthouse bar met on every page.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
