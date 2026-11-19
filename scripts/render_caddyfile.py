"""Render the web Caddyfile (EXW2) from site/Caddyfile.tmpl.

The security headers come from `build_site.HEADERS`, the same dict that writes `dist/_headers`, so the Caddy config
and the headers file cannot drift. Usage: python3 scripts/render_caddyfile.py [--template FILE] [--out FILE]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

MARKER = "{{SECURITY_HEADERS}}"


def _quote(value: str) -> str:
    """A Caddyfile quoted string: escape backslash and quote, and a brace (it would start a placeholder)."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("{", "\\{")


def render(template: str, headers: dict[str, str]) -> str:
    if MARKER not in template:
        raise ValueError(f"the template has no {MARKER} marker")
    lines = ["(security) {", "\theader {", "\t\t-Server"]
    lines += [f'\t\t{name} "{_quote(value)}"' for name, value in headers.items()]
    lines += ["\t}", "}"]
    return template.replace(MARKER, "\n".join(lines))


def main(argv: list[str]) -> int:
    import build_site

    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, default=ROOT / "site/Caddyfile.tmpl")
    parser.add_argument("--out", type=Path, default=ROOT / "site/build/Caddyfile")
    args = parser.parse_args(argv)
    text = render(args.template.read_text(), build_site.HEADERS)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
