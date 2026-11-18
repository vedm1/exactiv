"""Brand guard checks. Run from the repository root:  python3 brand/tokens/check_brand.py [paths...]

1. Contrast: every text pair in PAIRS passes WCAG 2.2 AA (4.5:1) in light and dark mode.
2. Generated files are current: tokens.json and tokens.ts match tokens.css.
3. Component code (default: brand/components and ui/src) has no hex colour, no monospace font,
   no retired font or colour, no border-radius above 0 and no box-shadow blur.
Exit code 1 on any failure, so CI can gate on it (phase EXD2).
"""

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
css = re.sub(r"/\*.*?\*/", "", (HERE / "tokens.css").read_text(), flags=re.S)


def decls(block: str) -> dict[str, str]:
    return {k: v.strip() for k, v in re.findall(r"(--ex-[\w-]+)\s*:\s*([^;]+);", block)}


LIGHT = decls(re.search(r":root\s*\{(.*?)\n\}", css, re.S).group(1))
DARK = {**LIGHT, **decls(re.search(r':root\[data-theme="dark"\]\s*\{(.*?)\n\}', css, re.S).group(1))}

# (text token, background token)
PAIRS = [
    ("text", "ground"), ("text-body", "ground"), ("text-quiet", "ground"), ("text-quiet", "raised"),
    ("text-disabled", "ground"), ("source", "ground"), ("source", "raised"), ("act-text", "ground"),
    ("on-act", "act"), ("on-evidence", "evidence"), ("on-source", "source"),
    ("on-inverse", "inverse"), ("on-inverse-quiet", "inverse"), ("on-inverse-faint", "inverse"),
    ("source-on-inverse", "inverse"),
    ("text", "shade"),
]


def resolve(table: dict[str, str], name: str) -> str:
    v = table[f"--ex-{name}"]
    while m := re.fullmatch(r"var\((--ex-[\w-]+)\)", v):
        v = table[m.group(1)]
    return v


def lum(hexv: str) -> float:
    h = hexv.lstrip("#")
    c = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a: str, b: str) -> float:
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


failures: list[str] = []
for mode, table in (("light", LIGHT), ("dark", DARK)):
    for fg, bg in PAIRS:
        r = ratio(resolve(table, fg), resolve(table, bg))
        if r < 4.5:
            failures.append(f"contrast {mode}: {fg} on {bg} = {r:.2f} (needs 4.5)")

before = {p: (HERE / p).read_text() for p in ("tokens.json", "tokens.ts")}
subprocess.run([sys.executable, str(HERE / "build_tokens.py")], check=True, capture_output=True)
for p, text in before.items():
    if (HERE / p).read_text() != text:
        failures.append(f"{p} was out of date with tokens.css (now regenerated: commit it)")

BANNED = [
    (re.compile(r"#[0-9a-fA-F]{3,8}\b"), "hex colour (use a role token)"),
    (re.compile(r"monospace|\bmono\b|JetBrains|Martian|Fragment Mono|Courier", re.I), "monospace font"),
    (re.compile(r"\bInter\b|\bLora\b|Schibsted|General Sans|Newsreader", re.I), "retired or unapproved font"),
    (re.compile(r"border-radius\s*:(?!\s*(0\b|var\(--ex-radius\)))"), "border-radius above 0"),
    (re.compile(r"box-shadow\s*:[^;]*\b\d+px\s+\d+px\s+[1-9]"), "blurred shadow"),
    (re.compile(r"var\(--ex-raw-"), "raw token in a component"),
]
targets = [Path(a) for a in sys.argv[1:]] or [HERE.parent / "components", ROOT / "ui" / "src"]
for target in targets:
    if not target.exists():
        continue
    files = [target] if target.is_file() else [
        f for f in target.rglob("*") if f.suffix in {".css", ".tsx", ".ts", ".jsx", ".js", ".html"}
        and "tokens" not in f.parts
    ]
    for f in files:
        text = re.sub(r"/\*.*?\*/|<!--.*?-->", lambda m: "\n" * m.group().count("\n"), f.read_text(errors="ignore"), flags=re.S)
        for n, line in enumerate(text.splitlines(), 1):
            code = re.sub(r"(?<!:)//.*$", "", line)
            for rx, why in BANNED:
                if rx.search(code):
                    failures.append(f"{f.relative_to(ROOT) if f.is_relative_to(ROOT) else f}:{n}: {why}")

if failures:
    print("Brand check failed:")
    print("\n".join(f"  - {x}" for x in failures))
    sys.exit(1)
print(f"Brand check passed: {len(PAIRS) * 2} contrast pairs, generated files current, no banned patterns.")
