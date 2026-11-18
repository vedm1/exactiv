"""Generate tokens.json (W3C design tokens format) and tokens.ts from tokens.css.

Run from the repository root:  python3 brand/tokens/build_tokens.py
tokens.css is the source of truth. Do not edit tokens.json or tokens.ts by hand.
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
css = re.sub(r"/\*.*?\*/", "", (HERE / "tokens.css").read_text(), flags=re.S)
light_block = re.search(r":root\s*\{(.*?)\n\}", css, re.S).group(1)
dark_block = re.search(r':root\[data-theme="dark"\]\s*\{(.*?)\n\}', css, re.S).group(1)


def decls(block: str) -> dict[str, str]:
    return {k: v.strip() for k, v in re.findall(r"(--ex-[\w-]+)\s*:\s*([^;]+);", block)}


LIGHT, DARK = decls(light_block), decls(dark_block)
SHAPE = {"rule-w", "accent-w", "radius", "focus-w", "focus-offset", "control-h", "input-h"}
LAYOUT = {"max", "gutter", "measure", "ease", "dur"}


def ref(value: str) -> str:
    m = re.fullmatch(r"var\(--ex-([\w-]+)\)", value)
    if not m:
        return value
    name = m.group(1)
    return "{raw." + name[4:] + "}" if name.startswith("raw-") else "{role." + name + "}"


def kind(name: str, value: str) -> str | None:
    if value.startswith("#") or value.startswith("var(--ex-raw"):
        return "color"
    if name.startswith("font"):
        return "fontFamily"
    if name == "dur":
        return "duration"
    if name == "ease":
        return "cubicBezier"
    if re.fullmatch(r"-?[\d.]+(px|rem|em|ch)", value) or value == "0":
        return "dimension"
    return None


def resolve(value: str) -> str:
    while m := re.fullmatch(r"var\((--ex-[\w-]+)\)", value):
        value = LIGHT[m.group(1)]
    return value


out: dict = {
    "$description": "Exaktiv design tokens v1.0. Generated from tokens.css. Components read role tokens only.",
    "raw": {}, "role": {}, "type": {}, "space": {}, "shape": {}, "layout": {}, "theme": {"dark": {}},
}
for key, value in LIGHT.items():
    name = key[5:]
    entry = {"$value": ref(value)}
    if t := kind(name, value):
        entry["$type"] = t
    if name.startswith("raw-"):
        out["raw"][name[4:]] = entry
    elif name.startswith(("font", "size", "lh", "track", "band")):
        out["type"][name] = entry
    elif name.startswith("space"):
        out["space"][name[6:]] = entry
    elif name in SHAPE:
        out["shape"][name] = entry
    elif name in LAYOUT:
        out["layout"][name] = entry
    else:
        out["role"][name] = entry
for key, value in DARK.items():
    out["theme"]["dark"][key[5:]] = {"$value": ref(value), "$type": "color"}
(HERE / "tokens.json").write_text(json.dumps(out, indent=2) + "\n")


def camel(s: str) -> str:
    return re.sub(r"-(\w)", lambda m: m.group(1).upper(), s)


roles = [k for k in LIGHT if not k.startswith("--ex-raw")]
dark_resolved = {k: (resolve(v) if v.startswith("var(--ex-raw") else v) for k, v in DARK.items()}
lines = [
    "// Exaktiv design tokens v1.0. Generated from brand/tokens/tokens.css. Do not edit by hand.",
    "// Use `ex.*` (CSS variables) in components. `light` and `dark` hold resolved values for",
    "// canvas, charts and PDF renderers that cannot read CSS variables.",
    "",
    "export const ex = {",
    *[f'  {camel(k[5:])}: "var({k})",' for k in roles],
    "} as const;",
    "",
    "export const light = {",
    *[f"  {camel(k[5:])}: {json.dumps(resolve(LIGHT[k]))}," for k in roles],
    "} as const;",
    "",
    "export const dark = {",
    "  ...light,",
    *[f"  {camel(k[5:])}: {json.dumps(v)}," for k, v in dark_resolved.items()],
    "} as const;",
    "",
    "export type ExToken = keyof typeof ex;",
    "",
]
(HERE / "tokens.ts").write_text("\n".join(lines))
print(f"tokens: {len(LIGHT)} light, {len(DARK)} dark overrides")
