#!/usr/bin/env python3
"""Build-phase dashboard generator (build-phase-kit), version 1.0.

Reads PHASES.md, <PROJECT>_BUILD_PLAN.md and <PROJECT>_PHASE_SPECS.md from the
project root and writes PHASES_DASHBOARD.html: one self-contained, interactive
page. The markdown files stay the source of truth; this page is derived from
them and is safe to delete and regenerate at any time.

Usage:
  python3 .claude/phase-dashboard/build_dashboard.py            # regenerate once
  python3 .claude/phase-dashboard/build_dashboard.py --watch    # regenerate on every save
  python3 .claude/phase-dashboard/build_dashboard.py --hook     # Claude Code PostToolUse hook
Options: --root DIR (default: nearest ancestor holding PHASES.md), --out FILE.
Python 3.8+, standard library only.
"""
import argparse, datetime, glob, json, os, re, sys, time

DASHBOARD_VERSION = "1.0"
DASHBOARD_NAME = "PHASES_DASHBOARD.html"
CODE_RE = re.compile(r"^([A-Z][A-Z]{0,5})(\d+)([A-Za-z0-9._\-]*)$")
SPEC_CAP, RISK_CAP, TEXT_CAP = 9000, 5000, 6000


def clean_code(cell):
    return re.sub(r"[*~`\s]", "", cell)


def find_root(start):
    d = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(d, "PHASES.md")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def read(path):
    if not path or not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def section(text, pattern):
    """Body of the first '## ' section whose heading matches pattern (to the next '## ')."""
    m = re.search(r"^##\s+[^\n]*" + pattern + r"[^\n]*\n", text, re.M | re.I)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def table_rows(text):
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|") or re.match(r"^\|[\s:\-|]+\|?$", s):
            continue
        yield s


def status_of(cell, struck):
    c = cell.lower()
    if struck or "❌" in cell or "dropped" in c or "superseded" in c or "cancel" in c:
        return "dropped"
    if "✅" in cell:
        return "done"
    if "🔲" in cell:
        return "planned"
    return "other"


def family_of(code):
    m = CODE_RE.match(code)
    return (m.group(1) + m.group(2)) if m else code


def codes_in(text, known):
    """Phase codes mentioned in free text; the boundaries stop QP5 matching inside QP5b."""
    found = []
    for code in sorted(known, key=len, reverse=True):
        if re.search(r"(?<![A-Za-z0-9\-])" + re.escape(code) + r"(?![A-Za-z0-9\-])", text):
            found.append(code)
    return found


def parse_phases(text):
    phases, seen, dupes = [], set(), []
    for row in table_rows(text):
        parts = row.split("|")
        if len(parts) < 5:
            continue
        code_cell = parts[1]
        code = clean_code(code_cell)
        if not CODE_RE.match(code):
            continue
        name, status_cell = parts[2].strip(), parts[3].strip()
        summary = "|".join(parts[4:]).strip()
        if summary.endswith("|"):
            summary = summary[:-1].rstrip()
        struck = code_cell.strip().startswith("~~") or (name.startswith("~~") and name.endswith("~~"))
        if code in seen:
            dupes.append(code)
        seen.add(code)
        phases.append({
            "code": code, "family": family_of(code),
            "name": name.strip("~* ").strip(),
            "status": status_of(status_cell, struck), "statusLabel": status_cell.strip("~ "),
            "summary": summary, "order": len(phases),
        })
    return phases, dupes


def parse_deps(text):
    m = re.search(r"<!--\s*deps\b(.*?)-->", text, re.S | re.I)
    if not m:
        return None
    deps = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.split("#", 1)[0]
        items = [clean_code(x) for x in re.split(r"[,\s]+", v) if clean_code(x)]
        deps[clean_code(k)] = [x for x in items if x.lower() not in ("-", "none", "—")]
    return deps


def parse_criteria(text):
    body = section(text, r"What\s+.?Complete.?\s+Means")
    out = {}
    for m in re.finditer(r"^\*\*([^*]+)\*\*\s*:?\s*(.+?)(?=^\*\*[^*]+\*\*|\Z)", body, re.M | re.S):
        code = clean_code(m.group(1))
        if CODE_RE.match(code):
            out[code] = m.group(2).strip()[:TEXT_CAP]
    return out


def parse_open_items(plan, known):
    body = section(plan, r"Open\s+Items")
    items, header_skipped = [], False
    for row in table_rows(body):
        parts = [p.strip() for p in row.strip("|").split("|")]
        if not header_skipped:
            header_skipped = True
            if parts and parts[0].lower().startswith("item"):
                continue
        if len(parts) < 3:
            continue
        item, blocks, status = parts[0], parts[1], " | ".join(parts[2:])
        struck = item.startswith("~~")
        is_open = ("🔲" in status) and not struck
        items.append({
            "item": item, "blocks": blocks, "status": status, "open": is_open,
            "struck": struck, "codes": codes_in(blocks, known),
        })
    return items


def parse_risks(plan, known):
    body = section(plan, r"Risks")
    out = {}
    for chunk in re.split(r"^###\s+", body, flags=re.M)[1:]:
        heading, _, rest = chunk.partition("\n")
        codes = codes_in(heading, known)
        if not codes and heading.split():
            codes = [clean_code(heading.split()[0])]
        risks = len(re.findall(r"\*\*Risk\*\*", rest))
        resolved = len(re.findall(r"\*\*Resolution\*\*", rest))
        for c in codes:
            prev = out.get(c, {"risks": 0, "resolved": 0, "text": ""})
            out[c] = {"risks": prev["risks"] + risks, "resolved": prev["resolved"] + resolved,
                      "text": (prev["text"] + "\n### " + chunk)[:RISK_CAP]}
    return out


def parse_specs(specs):
    out, shared = {}, []
    for chunk in re.split(r"^##\s+", specs, flags=re.M)[1:]:
        heading, _, body = chunk.partition("\n")
        token = clean_code(re.split(r"[\s—:(]", heading.strip(), 1)[0])
        if CODE_RE.match(token):
            detailed = bool(re.search(r"\*\*(Tests|Gating check|In scope)\*\*", body)) or len(body) > 1500
            out[token] = {"heading": heading.strip(), "text": body.strip()[:SPEC_CAP],
                          "truncated": len(body.strip()) > SPEC_CAP, "detailed": detailed,
                          "implNotes": bool(re.search(r"implementation notes", body, re.I))}
        else:
            shared.append(heading.strip())
    return out, shared


def spec_for(code, specs):
    if code in specs:
        return code
    best = None
    for k in specs:  # umbrella spec: longest spec code that prefixes this code at a boundary
        if code.startswith(k) and len(code) > len(k) and code[len(k)] in "-._" and (not best or len(k) > len(best)):
            best = k
    return best


def build(root):
    phases_md = read(os.path.join(root, "PHASES.md"))
    plan_path = (sorted(glob.glob(os.path.join(root, "*_BUILD_PLAN.md"))) or [None])[0]
    spec_path = (sorted(glob.glob(os.path.join(root, "*_PHASE_SPECS.md"))) or [None])[0]
    plan, specs_md = read(plan_path), read(spec_path)

    m = re.search(r"^#\s+(?:PHASES\.md\s*[—\-:]\s*)?(.+?)(?:\s+Build Tracker)?\s*$", phases_md, re.M)
    project = m.group(1).strip() if m else os.path.basename(root)
    if plan_path and (not m or project.upper() == "PHASES.MD"):
        project = os.path.basename(plan_path).replace("_BUILD_PLAN.md", "").title()

    phases, dupes = parse_phases(phases_md)
    known = [p["code"] for p in phases]
    deps = parse_deps(phases_md)
    criteria = parse_criteria(phases_md)
    open_items = parse_open_items(plan, known)
    risks = parse_risks(plan, known)
    specs, shared_specs = parse_specs(specs_md)
    gate_raw = re.sub(r"<!--.*?-->", "", section(phases_md, r"Gate\s+Dependencies"), flags=re.S).strip()

    by_code = {p["code"]: p for p in phases}
    warnings = []
    if dupes:
        warnings.append("Duplicate phase codes in PHASES.md: " + ", ".join(sorted(set(dupes))))
    for p in phases:
        if p["status"] == "other":
            warnings.append("%s has an unrecognised status '%s' (expected ✅ or 🔲)" % (p["code"], p["statusLabel"]))
    if deps is not None:
        for k, vs in deps.items():
            for v in [k] + vs:
                if v not in by_code:
                    warnings.append("deps block mentions %s, which is not a row in PHASES.md" % v)
        missing = [p["code"] for p in phases if p["code"] not in deps and p["status"] != "dropped"]
        if missing:
            warnings.append("%d phase(s) missing from the deps block: %s" % (len(missing), ", ".join(missing[:12]) + (" …" if len(missing) > 12 else "")))
    for it in open_items:
        if it["open"] and not it["codes"] and re.search(r"[A-Z]{1,6}\d", it["blocks"]):
            warnings.append("Open item '%s' blocks '%s', which matches no phase row" % (re.sub(r"[*~`]", "", it["item"])[:60], it["blocks"]))

    for p in phases:
        c = p["code"]
        sk = spec_for(c, specs)
        p["spec"] = sk
        p["deps"] = deps.get(c) if deps is not None and c in deps else None
        p["criteria"] = criteria.get(c)
        p["risk"] = risks.get(c)
        p["openItems"] = [i for i, it in enumerate(open_items) if it["open"] and c in it["codes"]]
    for p in phases:
        p["dependents"] = [q["code"] for q in phases if q["deps"] and p["code"] in q["deps"]]
        if p["status"] == "done" or p["status"] == "dropped":
            p["readiness"] = p["status"]
        elif p["openItems"]:
            p["readiness"] = "blocked"
        elif p["deps"] is None:
            p["readiness"] = "unknown"
        elif all(by_code.get(d, {}).get("status") in ("done", "dropped") for d in p["deps"]):
            p["readiness"] = "ready"
        else:
            p["readiness"] = "waiting"

    def mtime(path):
        return datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone().isoformat(timespec="seconds") if path and os.path.isfile(path) else None

    return {
        "project": project,
        "generated": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "sources": [{"file": os.path.basename(f), "modified": mtime(f)}
                    for f in [os.path.join(root, "PHASES.md"), plan_path, spec_path] if f],
        "phases": phases, "hasDeps": deps is not None, "gateRaw": gate_raw[:20000],
        "openItems": open_items, "specs": specs, "sharedSpecs": shared_specs, "warnings": warnings,
    }


def render(data, out):
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__TITLE__", (data["project"] + " — Build Phases").replace("<", "&lt;")).replace("__DATA__", blob)
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(html)
    os.replace(tmp, out)


def run(root, out, quiet=False):
    data = build(root)
    render(data, out)
    if not quiet:
        ph = data["phases"]
        done = sum(p["status"] == "done" for p in ph)
        print("Dashboard → %s  (%d/%d phases complete, %d warning(s))" % (out, done, len([p for p in ph if p["status"] != "dropped"]), len(data["warnings"])))
        for w in data["warnings"]:
            print("  ! " + w)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root")
    ap.add_argument("--out")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--hook", action="store_true")
    a = ap.parse_args()

    if a.hook:  # Claude Code PostToolUse: only rebuild when a tracker doc changed
        try:
            payload = json.load(sys.stdin)
        except Exception:
            return 0
        fp = (payload.get("tool_input") or {}).get("file_path") or ""
        base = os.path.basename(fp)
        if not (base == "PHASES.md" or base.endswith("_BUILD_PLAN.md") or base.endswith("_PHASE_SPECS.md")):
            return 0
        root = a.root or os.environ.get("CLAUDE_PROJECT_DIR") or find_root(os.path.dirname(fp))
        if not root or not os.path.isfile(os.path.join(root, "PHASES.md")):
            return 0
        try:
            run(root, a.out or os.path.join(root, DASHBOARD_NAME), quiet=True)
        except Exception as e:
            print("phase dashboard not regenerated: %s" % e, file=sys.stderr)
            return 1
        return 0

    root = a.root or find_root(os.getcwd()) or find_root(os.path.dirname(os.path.abspath(__file__)))
    if not root:
        print("No PHASES.md found in this directory or any parent. Pass --root.", file=sys.stderr)
        return 2
    out = a.out or os.path.join(root, DASHBOARD_NAME)
    run(root, out)
    if a.watch:
        print("Watching tracker docs — Ctrl+C to stop.")
        def stamp():
            fs = [os.path.join(root, "PHASES.md")] + glob.glob(os.path.join(root, "*_BUILD_PLAN.md")) + glob.glob(os.path.join(root, "*_PHASE_SPECS.md"))
            return tuple(sorted((f, os.path.getmtime(f)) for f in fs if os.path.isfile(f)))
        last = stamp()
        try:
            while True:
                time.sleep(1.5)
                now = stamp()
                if now != last:
                    last = now
                    try:
                        run(root, out)
                    except Exception as e:
                        print("  ! regenerate failed: %s" % e, file=sys.stderr)
        except KeyboardInterrupt:
            pass
    return 0


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Lora:ital,wght@0,500;0,600;1,500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0E1216;--panel:#161B22;--panel2:#1C232C;--fg:#E6EAF0;--dim:#A8B2BD;--muted:#7A8896;--rule:#222932;--rule-soft:#1A2028;
  --accent:#5EEAD4;--accent-soft:#2DD4BF;--accent-deep:#0F766E;--accent-ink:#5EEAD4;--accent-wash:rgba(94,234,212,.10);
  --warn:#F5B454;--warn-wash:rgba(245,180,84,.12);--on-accent:#0E1216;
  --sans:"Inter",system-ui,-apple-system,sans-serif;--serif:"Lora",Georgia,serif;--mono:"JetBrains Mono",ui-monospace,monospace;
  --r:10px;color-scheme:dark;
}
:root[data-theme="light"]{
  --bg:#F4F2ED;--panel:#FBFAF7;--panel2:#FFFFFF;--fg:#0E1216;--dim:#2C3340;--muted:#6B7280;--rule:#D8D4CB;--rule-soft:#E8E5DE;
  --accent:#0F766E;--accent-soft:#2DD4BF;--accent-ink:#0F766E;--accent-wash:rgba(15,118,110,.09);--warn:#B45309;--warn-wash:rgba(180,83,9,.09);--on-accent:#FFFFFF;
  color-scheme:light;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.55 var(--sans);-webkit-font-smoothing:antialiased}
button,input{font:inherit;color:inherit}
a{color:var(--accent-ink)}
code,.mono{font-family:var(--mono);font-size:.92em}
.wrap{max-width:1240px;margin:0 auto;padding:28px 24px 64px}
header.top{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding-bottom:20px;border-bottom:1px solid var(--rule)}
.brand{display:flex;align-items:center;gap:14px;min-width:0;flex:1}
.eyebrow{font:500 11px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
h1{font:600 28px/1.15 var(--serif);margin:6px 0 0;letter-spacing:-.01em;overflow-wrap:anywhere}
h2{font:600 18px/1.3 var(--serif);margin:0 0 12px}
h3{font:600 13px/1.3 var(--sans);margin:0 0 10px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}
.meta{font:12px/1.5 var(--mono);color:var(--muted);text-align:right}
.icon-btn{background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:7px 11px;cursor:pointer;font-size:12px}
.icon-btn:hover{border-color:var(--accent)}
nav.tabs{display:flex;gap:4px;margin:18px 0 22px;overflow-x:auto;border-bottom:1px solid var(--rule)}
nav.tabs button{background:none;border:0;border-bottom:2px solid transparent;padding:10px 14px;cursor:pointer;color:var(--muted);white-space:nowrap;font-weight:500}
nav.tabs button[aria-selected="true"]{color:var(--fg);border-bottom-color:var(--accent)}
nav.tabs .n{font:11px var(--mono);color:var(--muted);margin-left:6px}
.grid-kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:22px}
.card{background:var(--panel);border:1px solid var(--rule);border-radius:var(--r);padding:16px}
.kpi .v{font:600 28px/1.1 var(--serif);margin-top:8px}
.kpi .s{font-size:12px;color:var(--muted);margin-top:4px}
.bar{height:6px;border-radius:3px;background:var(--rule);overflow:hidden;margin-top:10px}
.bar>i{display:block;height:100%;background:var(--accent)}
.cols{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:16px}
.stack{display:grid;gap:16px;align-content:start}
.strip{display:flex;flex-wrap:wrap;gap:4px}
.cell{width:16px;height:16px;border-radius:3px;border:1px solid var(--rule);background:transparent;cursor:pointer;padding:0}
.cell.done{background:var(--accent);border-color:var(--accent)}
.cell.ready{border:2px solid var(--accent)}
.cell.blocked{border-color:var(--warn);background:var(--warn-wash)}
.cell.dropped{opacity:.35;background:repeating-linear-gradient(45deg,var(--rule) 0 2px,transparent 2px 5px)}
.cell:hover,.cell:focus-visible{outline:2px solid var(--fg);outline-offset:1px}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:12px;font-size:12px;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend .cell{width:11px;height:11px;cursor:default}
.list{display:grid;gap:2px}
.item{display:flex;gap:10px;align-items:baseline;padding:8px 10px;border-radius:8px;cursor:pointer;border:1px solid transparent;background:none;text-align:left;width:100%}
.item:hover{background:var(--panel2);border-color:var(--rule)}
.code{font:500 12px var(--mono);color:var(--accent-ink);white-space:nowrap}
.muted{color:var(--muted)}
.dim{color:var(--dim)}
.fam{display:grid;grid-template-columns:minmax(64px,auto) 1fr auto;gap:10px;align-items:center;font-size:12px;padding:3px 0}
.fam .bar{margin:0}
.pill{display:inline-flex;align-items:center;gap:5px;font:500 11px/1 var(--mono);padding:4px 7px;border-radius:999px;border:1px solid var(--rule);color:var(--dim);white-space:nowrap}
.pill.done{background:var(--accent-wash);border-color:transparent;color:var(--accent-ink)}
.pill.ready{border-color:var(--accent);color:var(--accent-ink)}
.pill.blocked{background:var(--warn-wash);border-color:transparent;color:var(--warn)}
.pill.dropped{text-decoration:line-through;opacity:.6}
.warn-list{margin:0;padding-left:18px;color:var(--warn);font-size:13px}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px}
.search{flex:1 1 220px;background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:9px 12px;min-width:0}
.search:focus{outline:none;border-color:var(--accent)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{background:var(--panel);border:1px solid var(--rule);border-radius:999px;padding:6px 11px;font-size:12px;cursor:pointer}
.chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
.toggle{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--dim);cursor:pointer;user-select:none}
.toggle input{accent-color:var(--accent)}
.rows{border:1px solid var(--rule);border-radius:var(--r);overflow:hidden;background:var(--panel)}
.row{display:grid;grid-template-columns:150px minmax(0,1fr) auto;gap:14px;padding:12px 16px;border-top:1px solid var(--rule-soft);cursor:pointer;align-items:start}
.row:first-child{border-top:0}
.row:hover,.row:focus-visible{background:var(--panel2);outline:none}
.row .nm{font-weight:600}
.row .sm{color:var(--dim);font-size:13px;margin-top:3px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.row.expanded .sm{-webkit-line-clamp:unset;display:block}
.row .tags{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;max-width:260px}
.row.dropped .nm{text-decoration:line-through;color:var(--muted)}
.grp{padding:10px 16px;background:var(--panel2);border-top:1px solid var(--rule);display:flex;gap:12px;align-items:center;font-size:12px}
.grp:first-child{border-top:0}
.grp .bar{flex:0 0 120px;margin:0}
.empty{padding:28px;text-align:center;color:var(--muted)}
.graph-wrap{overflow:auto;border:1px solid var(--rule);border-radius:var(--r);background:var(--panel);max-height:72vh}
svg.dag text{font:500 11px var(--mono);fill:var(--fg)}
svg.dag .node rect{fill:var(--panel2);stroke:var(--rule);stroke-width:1}
svg.dag .node.done rect{fill:var(--accent-wash);stroke:var(--accent)}
svg.dag .node.ready rect{stroke:var(--accent);stroke-width:2}
svg.dag .node.blocked rect{stroke:var(--warn);fill:var(--warn-wash)}
svg.dag .node.dropped{opacity:.4}
svg.dag .node text.sub{fill:var(--muted);font:400 10px var(--sans)}
svg.dag .node{cursor:pointer}
svg.dag path.edge{fill:none;stroke:var(--muted);stroke-width:1.2;opacity:.55}
svg.dag path.edge.hot{stroke:var(--accent);opacity:1;stroke-width:1.8}
svg.dag .faded{opacity:.15}
pre.raw{font:12px/1.5 var(--mono);background:var(--panel);border:1px solid var(--rule);border-radius:var(--r);padding:16px;overflow:auto;margin:0;white-space:pre}
table.oi{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--rule);border-radius:var(--r);overflow:hidden}
table.oi th,table.oi td{text-align:left;padding:10px 14px;border-top:1px solid var(--rule-soft);vertical-align:top;font-size:13px}
table.oi th{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--muted);border-top:0;background:var(--panel2)}
.codechip{font:500 11px var(--mono);background:var(--panel2);border:1px solid var(--rule);border-radius:6px;padding:2px 6px;cursor:pointer;color:var(--accent-ink);margin:0 4px 4px 0;display:inline-block}
.codechip.done{border-color:var(--accent)}
.md p{margin:0 0 8px}.md ul{margin:0 0 8px;padding-left:18px}.md li{margin:2px 0}
.md pre{font:12px/1.45 var(--mono);background:var(--bg);border:1px solid var(--rule);border-radius:8px;padding:10px;overflow:auto}
.md code{background:var(--panel2);padding:1px 4px;border-radius:4px}
.md pre code{background:none;padding:0}
.md h4{font:600 13px var(--sans);margin:12px 0 6px}
.scrim{position:fixed;inset:0;background:rgba(0,0,0,.45);opacity:0;pointer-events:none;transition:opacity .15s}
.scrim.on{opacity:1;pointer-events:auto}
aside.drawer{position:fixed;top:0;right:0;height:100%;width:min(640px,100%);background:var(--bg);border-left:1px solid var(--rule);transform:translateX(100%);transition:transform .2s ease;overflow-y:auto;z-index:5}
aside.drawer.on{transform:none}
.drawer .hd{position:sticky;top:0;background:var(--bg);padding:20px 24px 14px;border-bottom:1px solid var(--rule);z-index:1}
.drawer .bd{padding:18px 24px 48px;display:grid;gap:20px}
.drawer h2{margin:6px 0 10px}
details{border:1px solid var(--rule);border-radius:var(--r);background:var(--panel)}
details>summary{cursor:pointer;padding:12px 14px;font-weight:600;list-style:none}
details>summary::-webkit-details-marker{display:none}
details>summary::before{content:"›";display:inline-block;margin-right:8px;transition:transform .15s;color:var(--muted)}
details[open]>summary::before{transform:rotate(90deg)}
details>.md{padding:0 14px 12px}
.callout{border-left:2px solid var(--accent);padding:10px 14px;background:var(--accent-wash);border-radius:0 8px 8px 0;font-size:13px}
.callout.w{border-left-color:var(--warn);background:var(--warn-wash)}
@media (max-width:860px){.cols{grid-template-columns:1fr}}
@media (max-width:640px){
  .wrap{padding:20px 16px 48px}
  .meta{text-align:left;width:100%}
  .row{grid-template-columns:1fr;gap:6px}
  .row .tags{justify-content:flex-start;max-width:none}
  .drawer .hd,.drawer .bd{padding-left:16px;padding-right:16px}
  h1{font-size:23px}
}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div class="brand">
      <svg width="44" height="44" viewBox="0 0 68 68" aria-hidden="true"><rect x=".5" y=".5" width="67" height="67" fill="none" stroke="var(--rule)"/><path d="M14 18 L34 50 L54 18" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="square"/><circle cx="34" cy="50" r="2.6" fill="var(--accent-soft)"/></svg>
      <div style="min-width:0"><div class="eyebrow">Build phases</div><h1 id="project"></h1></div>
    </div>
    <div class="meta" id="meta"></div>
    <button class="icon-btn" id="theme" type="button" aria-label="Toggle light or dark theme">◐ Theme</button>
  </header>
  <nav class="tabs" role="tablist" id="tabs"></nav>
  <main id="view"></main>
</div>
<div class="scrim" id="scrim"></div>
<aside class="drawer" id="drawer" aria-hidden="true" role="dialog" aria-label="Phase details"></aside>
<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
const D = JSON.parse(document.getElementById('data').textContent);
const P = D.phases, BY = Object.fromEntries(P.map(p=>[p.code,p]));
const $ = (s,el=document)=>el.querySelector(s);
const esc = s => String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const store = { get(k,d){try{const v=localStorage.getItem('bpd:'+k);return v==null?d:JSON.parse(v)}catch(e){return d}}, set(k,v){try{localStorage.setItem('bpd:'+k,JSON.stringify(v))}catch(e){}} };

// ---------- theme ----------
const root = document.documentElement;
function setTheme(t){ if(t==='light') root.setAttribute('data-theme','light'); else root.removeAttribute('data-theme'); store.set('theme',t); }
setTheme(store.get('theme','dark'));
$('#theme').onclick = ()=> setTheme(root.getAttribute('data-theme')==='light'?'dark':'light');

// ---------- markdown-lite ----------
function inline(s){
  s = esc(s);
  s = s.replace(/`([^`]+)`/g,'<code>$1</code>')
       .replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>')
       .replace(/~~([^~]+)~~/g,'<del>$1</del>')
       .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');
  return s.replace(/&lt;br\s*\/?&gt;/gi,'<br>');
}
function md(text){
  if(!text) return '';
  const out=[]; const lines=String(text).split('\n'); let i=0, list=null, para=[];
  const flushP=()=>{ if(para.length){ out.push('<p>'+inline(para.join(' '))+'</p>'); para=[]; } };
  const flushL=()=>{ if(list){ out.push('<ul>'+list.map(x=>'<li>'+inline(x)+'</li>').join('')+'</ul>'); list=null; } };
  while(i<lines.length){
    const l=lines[i];
    if(/^\s*```/.test(l)){ flushP(); flushL(); const buf=[]; i++; while(i<lines.length && !/^\s*```/.test(lines[i])){buf.push(lines[i]);i++;} out.push('<pre><code>'+esc(buf.join('\n'))+'</code></pre>'); i++; continue; }
    if(/^\s*#{2,6}\s+/.test(l)){ flushP(); flushL(); out.push('<h4>'+inline(l.replace(/^\s*#+\s+/,''))+'</h4>'); i++; continue; }
    const m=l.match(/^\s*(?:[-*]|\d+\.)\s+(.*)$/);
    if(m){ flushP(); (list=list||[]).push(m[1]); i++; continue; }
    if(!l.trim()){ flushP(); flushL(); i++; continue; }
    if(list && /^\s{2,}\S/.test(l)){ list[list.length-1]+=' '+l.trim(); i++; continue; }
    flushL(); if(/^\s*\*\*[^*]+\*\*\s*:/.test(l)) flushP(); para.push(l.trim()); i++;
  }
  flushP(); flushL(); return out.join('');
}

// ---------- derived facts ----------
const live = P.filter(p=>p.status!=='dropped');
const done = live.filter(p=>p.status==='done');
const planned = live.filter(p=>p.status!=='done');
const ready = P.filter(p=>p.readiness==='ready');
const blocked = P.filter(p=>p.readiness==='blocked');
const waiting = P.filter(p=>p.readiness==='waiting');
const openItems = D.openItems.filter(o=>o.open);
const pct = live.length? Math.round(100*done.length/live.length):0;
const families = (()=>{ const m=new Map(); P.forEach(p=>{ if(!m.has(p.family)) m.set(p.family,[]); m.get(p.family).push(p); }); return [...m.entries()]; })();
const specCovered = planned.filter(p=>p.spec && D.specs[p.spec] && D.specs[p.spec].detailed).length;

const READY_LABEL = {ready:'Ready',blocked:'Blocked',waiting:'Waiting',unknown:'Deps unrecorded',done:'Complete',dropped:'Dropped'};
function statusPill(p){
  if(p.status==='done') return '<span class="pill done">✓ Complete</span>';
  if(p.status==='dropped') return '<span class="pill dropped">Dropped</span>';
  if(p.status==='other') return '<span class="pill">'+esc(p.statusLabel||'?')+'</span>';
  const r=p.readiness; return '<span class="pill '+(r==='ready'?'ready':r==='blocked'?'blocked':'')+'">'+(r==='ready'?'● ':r==='blocked'?'■ ':'○ ')+READY_LABEL[r]+'</span>';
}
function cellClass(p){ return p.status==='done'?'done':p.status==='dropped'?'dropped':p.readiness==='blocked'?'blocked':p.readiness==='ready'?'ready':''; }
function ago(iso){ const s=(Date.now()-new Date(iso).getTime())/1000; if(!(s>=0)) return iso; if(s<60) return 'just now'; if(s<3600) return Math.round(s/60)+' min ago'; if(s<86400) return Math.round(s/3600)+' h ago'; return Math.round(s/86400)+' d ago'; }

$('#project').textContent = D.project;
$('#meta').innerHTML = 'Generated '+esc(ago(D.generated))+'<br>'+D.sources.map(s=>esc(s.file)).join(' · ');
$('#meta').title = 'Generated '+D.generated+'\n'+D.sources.map(s=>s.file+' — modified '+s.modified).join('\n');

// ---------- tabs ----------
const TABS=[['overview','Overview',null],['phases','Phases',live.length],['graph','Dependencies',null],['items','Open items',openItems.length]];
let tab = store.get('tab','overview'); if(!TABS.some(t=>t[0]===tab)) tab='overview';
function renderTabs(){
  $('#tabs').innerHTML = TABS.map(([k,l,n])=>'<button role="tab" aria-selected="'+(k===tab)+'" data-tab="'+k+'">'+l+(n!=null?'<span class="n">'+n+'</span>':'')+'</button>').join('');
}
$('#tabs').addEventListener('click',e=>{ const b=e.target.closest('button[data-tab]'); if(!b) return; tab=b.dataset.tab; store.set('tab',tab); render(); });
function render(){ renderTabs(); ({overview:viewOverview,phases:viewPhases,graph:viewGraph,items:viewItems})[tab](); }

// ---------- overview ----------
function viewOverview(){
  const next = ready.length? ready : (D.hasDeps? [] : planned.filter(p=>p.status==='planned'));
  const nextTitle = ready.length? 'Ready to start' : D.hasDeps? 'Ready to start' : 'Planned, in tracker order';
  const nextNote = ready.length? 'Planned phases whose dependencies are all complete and that no open item blocks.' : D.hasDeps? 'Nothing is unblocked right now — see Blocked and Waiting below.' : 'Dependencies are not recorded yet, so readiness cannot be computed. Add a deps block to PHASES.md (the skill can do this for you).';
  const kpis = [
    ['Complete', pct+'%', done.length+' of '+live.length+' phases', pct],
    ['Planned', planned.length, (()=>{const h=P.filter(p=>/-hf/.test(p.code)).length; return families.length+' families · '+h+' hotfix'+(h===1?'':'es');})()],
    ['Ready now', D.hasDeps? ready.length : '—', D.hasDeps? waiting.length+' waiting on phases' : 'deps not recorded'],
    ['Blocked', blocked.length, 'by '+openItems.length+' open item'+(openItems.length===1?'':'s')],
    ['Specced', planned.length? specCovered+'/'+planned.length : '—', 'planned phases with a detailed spec'],
  ];
  const famRows = families.filter(([,ps])=>ps.some(p=>p.status!=='dropped')).map(([f,ps])=>{ const l=ps.filter(p=>p.status!=='dropped'); const d=l.filter(p=>p.status==='done').length; return [f,ps,d,l.length]; });
  $('#view').innerHTML =
    '<div class="grid-kpi">'+kpis.map(k=>'<div class="card kpi"><div class="eyebrow">'+k[0]+'</div><div class="v">'+k[1]+'</div><div class="s">'+k[2]+'</div>'+(k[3]!=null?'<div class="bar"><i style="width:'+k[3]+'%"></i></div>':'')+'</div>').join('')+'</div>'+
    '<div class="cols"><div class="stack">'+
      '<section class="card"><h3>Every phase, in tracker order</h3><div class="strip">'+P.map(p=>'<button class="cell '+cellClass(p)+'" data-code="'+esc(p.code)+'" title="'+esc(p.code+' — '+p.name+' ('+(READY_LABEL[p.readiness]||p.status)+')')+'" aria-label="'+esc(p.code)+'"></button>').join('')+'</div>'+
        '<div class="legend"><span><i class="cell done"></i>Complete</span><span><i class="cell ready"></i>Ready</span><span><i class="cell"></i>Planned</span><span><i class="cell blocked"></i>Blocked by open item</span><span><i class="cell dropped"></i>Dropped</span></div></section>'+
      '<section class="card"><h3>'+nextTitle+'</h3><p class="muted" style="margin:0 0 10px;font-size:13px">'+nextNote+'</p><div class="list">'+
        (next.length? next.slice(0,8).map(p=>itemBtn(p)).join('') + (next.length>8?'<div class="muted" style="padding:6px 10px;font-size:12px">+'+(next.length-8)+' more in Phases</div>':'') : '')+'</div></section>'+
      (blocked.length? '<section class="card"><h3>Blocked by open items</h3><div class="list">'+blocked.map(p=>itemBtn(p, p.openItems.map(i=>stripMd(D.openItems[i].item)).join('; '))).join('')+'</div></section>' : '')+
      (D.warnings.length? '<section class="card"><h3>Tracker health</h3><ul class="warn-list">'+D.warnings.map(w=>'<li>'+esc(w)+'</li>').join('')+'</ul></section>' : '')+
    '</div><div class="stack">'+
      '<section class="card"><h3>Progress by family</h3>'+famRows.map(([f,ps,d,n])=>'<div class="fam"><button class="code item" style="padding:2px 0;width:auto" data-family="'+esc(f)+'">'+esc(f)+'</button><div class="bar"><i style="width:'+(n?100*d/n:0)+'%"></i></div><span class="muted mono">'+d+'/'+n+'</span></div>').join('')+'</section>'+
      (openItems.length? '<section class="card"><h3>Open items</h3><div class="list">'+openItems.slice(0,6).map(o=>'<div style="padding:6px 0;border-top:1px solid var(--rule-soft);font-size:13px"><div class="md">'+inline(o.item)+'</div><div class="muted" style="font-size:12px">Blocks '+esc(o.blocks)+'</div></div>').join('')+(openItems.length>6?'<button class="chip" data-goto="items" style="margin-top:8px">All '+openItems.length+' open items</button>':'')+'</div></section>' : '')+
    '</div></div>';
}
function stripMd(s){ return String(s).replace(/[*`~]/g,''); }
function itemBtn(p, note){ return '<button class="item" data-code="'+esc(p.code)+'"><span class="code">'+esc(p.code)+'</span><span style="flex:1;min-width:0"><span>'+esc(p.name)+'</span>'+(note?'<br><span class="muted" style="font-size:12px">'+esc(note)+'</span>':'')+'</span></button>'; }

// ---------- phases ----------
const st = { q: store.get('q',''), f: store.get('f','all'), group: store.get('group',false), expand: store.get('expand',false), famFilter: null };
const FILTERS=[['all','All',P.length],['planned','Planned',planned.length],['done','Complete',done.length],['ready','Ready',ready.length],['blocked','Blocked',blocked.length],['waiting','Waiting',waiting.length]];
function match(p){
  if(st.famFilter && p.family!==st.famFilter) return false;
  const f=st.f;
  if(f==='planned' && !(p.status!=='done'&&p.status!=='dropped')) return false;
  if(f==='done' && p.status!=='done') return false;
  if(['ready','blocked','waiting'].includes(f) && p.readiness!==f) return false;
  if(st.q){ const q=st.q.toLowerCase(); return (p.code+' '+p.name+' '+p.summary).toLowerCase().includes(q); }
  return true;
}
function rowHtml(p){
  const tags=[statusPill(p)];
  if(p.spec && D.specs[p.spec]) tags.push('<span class="pill" title="'+esc(D.specs[p.spec].heading)+'">'+(D.specs[p.spec].detailed?'spec':'spec stub')+(p.spec!==p.code?' ↑':'')+'</span>');
  if(p.risk && p.risk.risks) tags.push('<span class="pill">'+p.risk.risks+' risk'+(p.risk.risks>1?'s':'')+'</span>');
  if(p.openItems.length) tags.push('<span class="pill blocked">'+p.openItems.length+' open item'+(p.openItems.length>1?'s':'')+'</span>');
  return '<div class="row '+(st.expand?'expanded ':'')+(p.status==='dropped'?'dropped':'')+'" tabindex="0" data-code="'+esc(p.code)+'"><div class="code">'+esc(p.code)+'</div><div style="min-width:0"><div class="nm">'+esc(p.name)+'</div>'+(p.summary?'<div class="sm md">'+inline(p.summary)+'</div>':'')+'</div><div class="tags">'+tags.join('')+'</div></div>';
}
function viewPhases(){
  $('#view').innerHTML =
    '<div class="toolbar"><input class="search" id="q" type="search" placeholder="Search code, name or summary…" value="'+esc(st.q)+'" aria-label="Search phases">'+
    '<label class="toggle"><input type="checkbox" id="grp" '+(st.group?'checked':'')+'> Group by family</label>'+
    '<label class="toggle"><input type="checkbox" id="exp" '+(st.expand?'checked':'')+'> Full summaries</label></div>'+
    '<div class="toolbar"><div class="chips" id="chips">'+FILTERS.map(([k,l,n])=>'<button class="chip" aria-pressed="'+(st.f===k)+'" data-f="'+k+'">'+l+' <span class="mono">'+n+'</span></button>').join('')+
    (st.famFilter?'<button class="chip" aria-pressed="true" data-clearfam="1">Family '+esc(st.famFilter)+' ✕</button>':'')+'</div></div>'+
    '<div class="rows" id="rows"></div>';
  drawRows();
  const q=$('#q'); q.addEventListener('input',()=>{ st.q=q.value; store.set('q',st.q); drawRows(); });
  $('#grp').onchange=e=>{ st.group=e.target.checked; store.set('group',st.group); drawRows(); };
  $('#exp').onchange=e=>{ st.expand=e.target.checked; store.set('expand',st.expand); drawRows(); };
  $('#chips').onclick=e=>{ const b=e.target.closest('button'); if(!b) return; if(b.dataset.clearfam){ st.famFilter=null; } else { st.f=b.dataset.f; store.set('f',st.f); } viewPhases(); };
}
function drawRows(){
  const list=P.filter(match); let html='';
  if(!list.length) html='<div class="empty">No phases match.</div>';
  else if(st.group){
    const seen=new Map(); list.forEach(p=>{ if(!seen.has(p.family)) seen.set(p.family,[]); seen.get(p.family).push(p); });
    seen.forEach((ps,f)=>{ const all=P.filter(p=>p.family===f&&p.status!=='dropped'); const d=all.filter(p=>p.status==='done').length;
      html+='<div class="grp"><span class="code">'+esc(f)+'</span><span class="muted">'+all.length+' row'+(all.length>1?'s':'')+'</span><div class="bar"><i style="width:'+(all.length?100*d/all.length:0)+'%"></i></div><span class="muted mono">'+d+'/'+all.length+'</span></div>'+ps.map(rowHtml).join(''); });
  } else html=list.map(rowHtml).join('');
  $('#rows').innerHTML=html;
}

// ---------- dependency graph ----------
let hideDone = store.get('hideDone',false);
function viewGraph(){
  const raw = D.gateRaw? '<details style="margin-top:16px"><summary>Gate Dependencies section, as written in PHASES.md</summary><div class="md">'+md(D.gateRaw)+'</div></details>' : '';
  if(!D.hasDeps){
    $('#view').innerHTML='<div class="callout w" style="margin-bottom:16px">No machine-readable <code>&lt;!-- deps --&gt;</code> block in PHASES.md, so the graph and the Ready / Waiting states can’t be computed. Ask Claude to “add the dashboard deps block” — it derives one from the Gate Dependencies section and asks you to confirm it.</div>'+(D.gateRaw?'<pre class="raw">'+esc(D.gateRaw)+'</pre>':'<div class="empty">PHASES.md has no Gate Dependencies section either.</div>');
    return;
  }
  const nodes=P.filter(p=>p.deps!==null && !(hideDone && p.status==='done'));
  const ids=new Set(nodes.map(p=>p.code));
  const depth={}; const visiting=new Set();
  function dep(c){ if(depth[c]!=null) return depth[c]; if(visiting.has(c)) return 0; visiting.add(c);
    const ds=(BY[c].deps||[]).filter(x=>ids.has(x)); const v=ds.length? 1+Math.max(...ds.map(dep)) : 0; visiting.delete(c); return depth[c]=v; }
  nodes.forEach(p=>dep(p.code));
  const cols=[]; nodes.forEach(p=>{ (cols[depth[p.code]]=cols[depth[p.code]]||[]).push(p); });
  const W=168,H=40,CW=228,RH=54,PAD=20; const pos={}, rank={};
  cols.forEach((col,ci)=>{ // barycentre ordering: sit each phase near the phases it depends on
    if(ci>0){ const key=p=>{ const r=(p.deps||[]).filter(d=>rank[d]!=null).map(d=>rank[d]); return r.length? r.reduce((a,b)=>a+b,0)/r.length : 1e9+p.order; };
      col.sort((a,b)=>key(a)-key(b)||a.order-b.order); }
    col.forEach((p,ri)=>{ rank[p.code]=ri; pos[p.code]={x:PAD+ci*CW,y:PAD+ri*RH}; }); });
  const width=PAD*2+Math.max(1,cols.length)*CW-(CW-W), height=PAD*2+Math.max(1,...cols.map(c=>c.length))*RH-(RH-H);
  let edges=''; nodes.forEach(p=>(p.deps||[]).filter(d=>ids.has(d)).forEach(d=>{ const a=pos[d], b=pos[p.code]; const x1=a.x+W,y1=a.y+H/2,x2=b.x,y2=b.y+H/2,mx=(x1+x2)/2;
    edges+='<path class="edge" data-from="'+esc(d)+'" data-to="'+esc(p.code)+'" d="M'+x1+','+y1+' C'+mx+','+y1+' '+mx+','+y2+' '+x2+','+y2+'"/>'; }));
  const nodeSvg=nodes.map(p=>{ const q=pos[p.code]; const nm=p.name.length>24?p.name.slice(0,23)+'…':p.name;
    return '<g class="node '+cellClass(p)+'" data-code="'+esc(p.code)+'" transform="translate('+q.x+','+q.y+')" tabindex="0"><title>'+esc(p.code+' — '+p.name)+'</title><rect width="'+W+'" height="'+H+'" rx="7"/><text x="10" y="16">'+esc(p.code)+'</text><text class="sub" x="10" y="31">'+esc(nm)+'</text></g>'; }).join('');
  const outside=P.filter(p=>p.deps===null && p.status!=='dropped');
  $('#view').innerHTML='<div class="toolbar"><span class="muted" style="font-size:13px;flex:1">Columns are dependency depth; hover a phase to trace what it needs and what it unlocks.</span><label class="toggle"><input type="checkbox" id="hd" '+(hideDone?'checked':'')+'> Hide completed</label></div>'+
    '<div class="graph-wrap"><svg class="dag" width="'+width+'" height="'+height+'" viewBox="0 0 '+width+' '+height+'">'+edges+nodeSvg+'</svg></div>'+
    (outside.length?'<div class="callout w" style="margin-top:14px">Not in the deps block, so not drawn: '+outside.map(p=>'<span class="codechip" data-code="'+esc(p.code)+'">'+esc(p.code)+'</span>').join('')+'</div>':'')+raw;
  $('#hd').onchange=e=>{ hideDone=e.target.checked; store.set('hideDone',hideDone); viewGraph(); };
  const svg=$('svg.dag');
  function trace(c){ const up=new Set([c]), dn=new Set([c]);
    (function a(x){ (BY[x].deps||[]).forEach(d=>{ if(!up.has(d)){up.add(d);a(d);} }); })(c);
    (function b(x){ (BY[x].dependents||[]).forEach(d=>{ if(!dn.has(d)){dn.add(d);b(d);} }); })(c);
    return new Set([...up,...dn]); }
  svg.addEventListener('mouseover',e=>{ const g=e.target.closest('.node'); if(!g) return; const s=trace(g.dataset.code);
    svg.querySelectorAll('.node').forEach(n=>n.classList.toggle('faded',!s.has(n.dataset.code)));
    svg.querySelectorAll('.edge').forEach(p=>{ const on=s.has(p.dataset.from)&&s.has(p.dataset.to); p.classList.toggle('hot',on); p.classList.toggle('faded',!on); }); });
  svg.addEventListener('mouseleave',()=>svg.querySelectorAll('.faded,.hot').forEach(n=>n.classList.remove('faded','hot')));
}

// ---------- open items ----------
let showResolved = store.get('showResolved',false);
function viewItems(){
  const list=D.openItems.filter(o=>showResolved||o.open);
  $('#view').innerHTML='<div class="toolbar"><span class="muted" style="flex:1;font-size:13px">From the Open Items table in the build plan. Anything unconfirmed lives here until a phase answers it.</span><label class="toggle"><input type="checkbox" id="sr" '+(showResolved?'checked':'')+'> Show resolved ('+(D.openItems.length-openItems.length)+')</label></div>'+
    (list.length?'<div style="overflow-x:auto"><table class="oi"><thead><tr><th>Item</th><th>Blocks</th><th>Status</th></tr></thead><tbody>'+
    list.map(o=>'<tr><td class="md">'+inline(o.item)+'</td><td>'+(o.codes.length?o.codes.map(c=>'<span class="codechip '+(BY[c]&&BY[c].status==='done'?'done':'')+'" data-code="'+esc(c)+'">'+esc(c)+'</span>').join(''):esc(o.blocks))+'</td><td class="md">'+inline(o.status)+'</td></tr>').join('')+'</tbody></table></div>'
    :'<div class="empty">'+(D.openItems.length?'No open items — everything is resolved.':'No Open Items table found in the build plan.')+'</div>');
  $('#sr').onchange=e=>{ showResolved=e.target.checked; store.set('showResolved',showResolved); viewItems(); };
}

// ---------- drawer ----------
const drawer=$('#drawer'), scrim=$('#scrim'); let lastFocus=null;
function chip(c){ const p=BY[c]; return '<span class="codechip '+(p&&p.status==='done'?'done':'')+'" data-code="'+esc(c)+'" title="'+esc(p?p.name+' — '+(READY_LABEL[p.readiness]||''):'not in PHASES.md')+'">'+(p&&p.status==='done'?'✓ ':'')+esc(c)+'</span>'; }
function openPhase(code){
  const p=BY[code]; if(!p) return; lastFocus=document.activeElement;
  const sp=p.spec?D.specs[p.spec]:null;
  let why='';
  if(p.readiness==='ready') why='All dependencies are complete and no open item blocks it.';
  else if(p.readiness==='waiting') why='Waiting on: '+(p.deps||[]).filter(d=>!BY[d]||!['done','dropped'].includes(BY[d].status)).map(chip).join('');
  else if(p.readiness==='blocked') why='Blocked by an open item in the build plan (below).';
  else if(p.readiness==='unknown') why='This phase is not in the deps block, so readiness can’t be computed.';
  const sec=(t,b)=>b?'<section><h3>'+t+'</h3>'+b+'</section>':'';
  drawer.innerHTML='<div class="hd"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><span class="code" style="font-size:14px">'+esc(p.code)+'</span><button class="icon-btn" id="x" aria-label="Close">✕ Close</button></div><h2>'+esc(p.name)+'</h2><div style="display:flex;gap:6px;flex-wrap:wrap">'+statusPill(p)+(p.family!==p.code?'<span class="pill">family '+esc(p.family)+'</span>':'')+'</div></div>'+
    '<div class="bd">'+
      (why?'<div class="callout '+(p.readiness==='blocked'||p.readiness==='unknown'?'w':'')+'">'+why+'</div>':'')+
      sec('Summary', p.summary?'<div class="md">'+md(p.summary)+'</div>':'<p class="muted">No summary yet.</p>')+
      (p.deps!==null||p.dependents.length? sec('Dependencies','<div><span class="muted" style="font-size:12px">Needs</span><br>'+((p.deps&&p.deps.length)?p.deps.map(chip).join(''):'<span class="muted">nothing</span>')+'</div><div style="margin-top:8px"><span class="muted" style="font-size:12px">Unlocks</span><br>'+(p.dependents.length?p.dependents.map(chip).join(''):'<span class="muted">nothing recorded</span>')+'</div>'):'')+
      (p.openItems.length? sec('Open items blocking this', p.openItems.map(i=>'<div class="md" style="margin-bottom:8px">'+inline(D.openItems[i].item)+'<div class="muted" style="font-size:12px">'+inline(D.openItems[i].status)+'</div></div>').join('')):'')+
      sec('What complete means', p.criteria?'<div class="md">'+md(p.criteria)+'</div>':'')+
      (sp? '<details '+(p.status!=='done'?'open':'')+'><summary>Spec'+(p.spec!==p.code?' (umbrella: '+esc(p.spec)+')':'')+(sp.detailed?'':' — stub')+(sp.implNotes?' · has implementation notes':'')+'</summary><div class="md">'+md(sp.text)+(sp.truncated?'<p class="muted">… truncated — see the specs file for the rest.</p>':'')+'</div></details>' : '<p class="muted" style="margin:0">No spec section for this phase.</p>')+
      (p.risk? '<details><summary>Risks · '+p.risk.risks+' logged, '+p.risk.resolved+' resolved</summary><div class="md">'+md(p.risk.text)+'</div></details>':'')+
    '</div>';
  drawer.classList.add('on'); scrim.classList.add('on'); drawer.setAttribute('aria-hidden','false'); drawer.scrollTop=0;
  $('#x').onclick=closeDrawer; $('#x').focus();
  history.replaceState(null,'','#'+encodeURIComponent(code));
}
function closeDrawer(){ drawer.classList.remove('on'); scrim.classList.remove('on'); drawer.setAttribute('aria-hidden','true'); history.replaceState(null,'',location.pathname+location.search); if(lastFocus&&lastFocus.focus) lastFocus.focus(); }
scrim.onclick=closeDrawer;
document.addEventListener('keydown',e=>{
  if(e.key==='Escape' && drawer.classList.contains('on')) closeDrawer();
  if(e.key==='/' && document.activeElement.tagName!=='INPUT'){ e.preventDefault(); if(tab!=='phases'){ tab='phases'; store.set('tab',tab); render(); } $('#q').focus(); }
  if((e.key==='Enter'||e.key===' ') && e.target.matches('.row,.node')){ e.preventDefault(); openPhase(e.target.dataset.code); }
});
document.addEventListener('click',e=>{
  const fam=e.target.closest('[data-family]'); if(fam){ st.famFilter=fam.dataset.family; st.f='all'; tab='phases'; store.set('tab',tab); render(); return; }
  const go=e.target.closest('[data-goto]'); if(go){ tab=go.dataset.goto; store.set('tab',tab); render(); return; }
  const el=e.target.closest('[data-code]'); if(el && !e.target.closest('#tabs')) openPhase(el.dataset.code);
});

render();
if(location.hash){ const c=decodeURIComponent(location.hash.slice(1)); if(BY[c]) openPhase(c); }
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
