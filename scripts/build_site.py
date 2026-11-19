"""Build the Exaktiv website (EXD5, PRD-W) from site/ and brand/ into a static dist/.

Usage: python3 scripts/build_site.py [--site site] [--out site/dist] [--launch] [--names FILE]

The build is also the gate. It fails (exit 1, no dist left behind) on:
- a footnote for a claim whose status is not "ready" (the Trace gate, G1 applied to the site),
- a banned claim (site/claims.yaml, PRD-W section 6),
- a third-party URL,
- a page rule break (one H1, lang, canonical, no inline style or script, no script that the page
  did not declare in pages.yaml (W-G3)),
- a personal, employer or client name from the name list (G8),
- an off-brand pattern (brand/tokens/check_brand.py).
`--launch` is the stricter launch gate: every used claim ready, no placeholder, names list required.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"ready", "to_confirm", "to_write"}
LAUNCH_MARKER = ".launch-built"
CSP = "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'; form-action 'self'"
HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Cross-Origin-Opener-Policy": "same-origin",
}
# Namespaces and the JSON-LD context are identifiers, not requests.
URL_NAMESPACES = (
    "http://www.w3.org/",
    "https://schema.org",
    "http://www.sitemaps.org/schemas/sitemap/0.9",
)
URL_SCAN_SUFFIXES = {".html", ".css", ".txt", ".xml", ".webmanifest", ".json", ".svg"}
URL_SCAN_SKIP_PREFIXES = ("assets/fonts/OFL-",)  # licence texts name the licence host
URL_RE = re.compile(r"https?://[^\s\"'()<>\\]+")
XMLNS_RE = re.compile(r"""xmlns(:[\w-]+)?\s*=\s*["'][^"']*["']""")
SCHEME_RELATIVE_RE = re.compile(r"[\s\"'(=]//[a-z0-9-]+(\.[a-z0-9-]+)+/", re.I)
BRAND_FILES = (
    "favicon.svg",
    "favicon.ico",
    "favicon-16.png",
    "favicon-32.png",
    "apple-touch-icon.png",
    "icon-192.png",
    "icon-512.png",
    "site.webmanifest",
)


class BuildError(Exception):
    """One or more build problems. `problems` holds one line each."""

    def __init__(self, problems: list[str] | str) -> None:
        self.problems = [problems] if isinstance(problems, str) else problems
        super().__init__("\n".join(self.problems))


@dataclass(frozen=True)
class Claim:
    id: str
    text: str
    status: str
    evidence: str
    cite: str | None
    pages: tuple[str, ...]
    source_url: str | None


@dataclass(frozen=True)
class Claims:
    claims: dict[str, Claim]
    banned: list[tuple[str, re.Pattern[str]]]
    external_allow: dict[str, str]  # url -> claim id


@dataclass(frozen=True)
class SiteConfig:
    base_url: str
    legal_name: str
    registered_address: str
    brand: str
    lang: str
    contact_email: str
    security_email: str
    security_expires: date

    @property
    def host(self) -> str:
        return urlparse(self.base_url).netloc


@dataclass(frozen=True)
class Page:
    slug: str
    path: str
    title: str
    description: str
    in_nav: bool
    nav_label: str
    cta: dict[str, str] | None
    # EXW1-ui: a utility page is a state of the form (thanks, problem), not a PRD-W page. It is
    # always noindex and stays out of the sitemap and llms.txt.
    utility: bool = False
    # Self-hosted scripts this page may load (W-G3). Any other <script> fails the build.
    scripts: tuple[str, ...] = ()

    @property
    def out_file(self) -> str:
        if self.path.endswith("/"):
            return self.path.lstrip("/") + "index.html"
        return self.path.lstrip("/")


def _load_yaml(path: Path) -> dict[str, object]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or data.get("version") != 1:
        raise BuildError(f"{path.name}: missing or unsupported version (expected `version: 1`)")
    return data


def load_claims(path: Path) -> Claims:
    data = _load_yaml(path)
    problems: list[str] = []
    claims: dict[str, Claim] = {}
    for raw in data.get("claims") or []:  # type: ignore[attr-defined]
        cid = str(raw.get("id", ""))
        status = raw.get("status")
        if not cid or cid in claims:
            problems.append(f"claims: missing or duplicate id {cid!r}")
            continue
        if status not in STATUSES:
            problems.append(f"claim {cid}: status must be one of {sorted(STATUSES)}")
        if not raw.get("evidence"):
            problems.append(f"claim {cid}: evidence is required")
        if status == "ready" and not raw.get("cite"):
            problems.append(f"claim {cid}: a ready claim needs a cite text")
        claims[cid] = Claim(
            id=cid,
            text=str(raw.get("text", "")),
            status=str(status),
            evidence=str(raw.get("evidence", "")),
            cite=raw.get("cite"),
            pages=tuple(raw.get("pages") or ()),
            source_url=raw.get("source_url"),
        )
    allow = {str(e["url"]): str(e["claim"]) for e in data.get("external_allow") or []}  # type: ignore[attr-defined]
    for url, cid in allow.items():
        if cid not in claims:
            problems.append(f"external_allow {url}: unknown claim {cid}")
    for c in claims.values():
        if c.source_url and allow.get(c.source_url) != c.id:
            problems.append(f"claim {c.id}: source_url must be listed in external_allow for it")
    banned = [(str(b["id"]), re.compile(str(b["pattern"]))) for b in data.get("banned") or []]  # type: ignore[attr-defined]
    if problems:
        raise BuildError(problems)
    return Claims(claims, banned, allow)


def load_config(site_dir: Path) -> tuple[SiteConfig, list[Page]]:
    s = _load_yaml(site_dir / "site.yaml")
    cfg = SiteConfig(
        base_url=str(s["base_url"]).rstrip("/"),
        legal_name=str(s["legal_name"]),
        registered_address=str(s["registered_address"]),
        brand=str(s["brand"]),
        lang=str(s["lang"]),
        contact_email=str(s["contact_email"]),
        security_email=str(s["security_email"]),
        security_expires=date.fromisoformat(str(s["security_expires"])),
    )
    if cfg.security_expires <= date.today():
        raise BuildError("site.yaml: security_expires must be in the future (RFC 9116)")
    p = _load_yaml(site_dir / "pages.yaml")
    pages = [
        Page(
            slug=str(r["slug"]),
            path=str(r["path"]),
            title=str(r["title"]),
            description=str(r["description"]),
            in_nav=bool(r.get("in_nav")),
            nav_label=str(r.get("nav") or r["title"]),
            cta=(
                {k: str(v).format(contact_email=cfg.contact_email) for k, v in r["cta"].items()}
                if r.get("cta")
                else None
            ),
            utility=bool(r.get("utility")),
            scripts=tuple(str(x) for x in r.get("scripts") or ()),
        )
        for r in p["pages"]  # type: ignore[attr-defined]
    ]
    return cfg, pages


# ---------------------------------------------------------------- the Trace (per page)


@dataclass
class Trace:
    """Footnotes and claim use for one page. cite() is the only way to make a footnote number."""

    page: Page
    claims: Claims
    numbers: dict[str, int] = field(default_factory=dict)
    used: set[str] = field(default_factory=set)

    def _get(self, claim_id: str) -> Claim:
        if claim_id not in self.claims.claims:
            raise BuildError(f"{self.page.slug}: unknown claim {claim_id!r}")
        claim = self.claims.claims[claim_id]
        self.used.add(claim_id)
        if self.page.slug not in claim.pages:
            raise BuildError(
                f"{self.page.slug}: claim {claim_id} is not listed for this page in claims.yaml"
            )
        return claim

    def cite(self, claim_id: str) -> Markup:
        claim = self._get(claim_id)
        if claim.status != "ready":
            raise BuildError(
                f"{self.page.slug}: footnote for claim {claim_id} but its status is "
                f"{claim.status!r}, not 'ready' (no evidence, no number)"
            )
        n = self.numbers.setdefault(claim_id, len(self.numbers) + 1)
        return Markup(f'<a class="ex-ref" href="#c{n}">{n}</a>')

    def backed(self, claim_id: str, words: str) -> Markup:
        """The words a claim backs. A ready claim gets the evidence band and a footnote number.
        An unready claim gets plain words, no band and no number."""
        claim = self._get(claim_id)
        if claim.status != "ready":
            return Markup(escape(words))
        return Markup(f'<span class="ex-mark">{escape(words)}</span>') + self.cite(claim_id)

    def claim(self, claim_id: str) -> str:
        return self._get(claim_id).text

    def ready(self, claim_id: str) -> bool:
        """True when the claim has its evidence. Pages wrap an unevidenced sentence in
        `{% if ready(id) %}`, so it appears by itself the day the claim becomes ready."""
        if claim_id not in self.claims.claims:
            raise BuildError(f"{self.page.slug}: unknown claim {claim_id!r}")
        return self.claims.claims[claim_id].status == "ready"

    def source_link(self, claim_id: str, label: str) -> Markup:
        claim = self._get(claim_id)
        if not claim.source_url:
            raise BuildError(f"{self.page.slug}: claim {claim_id} has no source_url")
        return Markup(
            f'<a href="{escape(claim.source_url)}" rel="noopener noreferrer">{escape(label)}</a>'
        )

    def cites(self) -> Markup:
        if not self.numbers:
            return Markup("")
        items = "".join(
            f'<li id="c{n}"><span class="ex-cite__n">{n}</span>'
            f"{escape(self.claims.claims[cid].cite or '')}</li>"
            for cid, n in self.numbers.items()
        )
        return Markup(
            '<section class="ex-section"><div class="ex-wrap">'
            f'<ol class="ex-cites">{items}</ol></div></section>'
        )


# ---------------------------------------------------------------- HTML inspection


class PageInfo(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.h1 = 0
        self.title = ""
        self.description: str | None = None
        self.canonical: str | None = None
        self.robots: str | None = None
        self.text: list[str] = []
        self.alts: list[str] = []
        self.anchors: list[tuple[str, str]] = []  # (href, rel)
        self.refs: list[str] = []
        self.cite_ids: set[str] = set()
        self.problems: list[str] = []
        self.scripts: list[str] = []
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "meta" and a.get("name") == "description":
            self.description = a.get("content", "")
        elif tag == "meta" and a.get("name") == "robots":
            self.robots = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        elif tag == "a":
            self.anchors.append((a.get("href", ""), a.get("rel", "")))
            if "ex-ref" in a.get("class", "").split():
                self.refs.append(a.get("href", ""))
        elif tag == "img":
            if "alt" not in a:
                self.problems.append("image without alt attribute")
            self.alts.append(a.get("alt", ""))
        elif tag == "style":
            self.problems.append("inline <style> (the CSP blocks it)")
        elif tag == "script":
            if a.get("src"):
                self.scripts.append(a["src"])
            elif a.get("type") != "application/ld+json":
                self.problems.append("inline <script> (the CSP blocks it)")
        if "style" in a:
            self.problems.append("inline style attribute (the CSP blocks it)")
        if "id" in a and "ex-cite__n" not in a.get("class", ""):
            self.cite_ids.add(a["id"])
        if tag in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif not self._skip:
            self.text.append(data)

    def visible(self) -> str:
        return " ".join(" ".join(self.text).split())


def inspect_html(path: Path) -> PageInfo:
    info = PageInfo()
    info.feed(path.read_text())
    return info


# ---------------------------------------------------------------- checks


def _dist_files(out: Path) -> list[Path]:
    return sorted(p for p in out.rglob("*") if p.is_file())


def _rel(out: Path, p: Path) -> str:
    return p.relative_to(out).as_posix()


def check_banned(out: Path, claims: Claims) -> list[str]:
    problems: list[str] = []
    for p in _dist_files(out):
        rel = _rel(out, p)
        if p.suffix not in {".html", ".txt", ".xml"} or rel.startswith("assets/fonts/"):
            continue
        if p.suffix == ".html":
            info = inspect_html(p)
            text = " ".join([info.visible(), info.title, info.description or "", *info.alts])
        else:
            text = p.read_text()
        for bid, rx in claims.banned:
            if rx.search(text):
                problems.append(f"{rel}: banned claim {bid}")
    return problems


def check_urls(out: Path, cfg: SiteConfig, claims: Claims) -> list[str]:
    problems: list[str] = []
    for p in _dist_files(out):
        rel = _rel(out, p)
        if p.suffix not in URL_SCAN_SUFFIXES or rel.startswith(URL_SCAN_SKIP_PREFIXES):
            continue
        text = XMLNS_RE.sub("", p.read_text(errors="ignore"))  # namespace names are not requests
        valid_anchor_hits: dict[str, int] = {}
        if p.suffix == ".html":
            for href, rel_attr in inspect_html(p).anchors:
                tokens = rel_attr.split()
                if (
                    href in claims.external_allow
                    and "noopener" in tokens
                    and "noreferrer" in tokens
                ):
                    valid_anchor_hits[href] = valid_anchor_hits.get(href, 0) + 1
        seen: dict[str, int] = {}
        for m in URL_RE.finditer(text):
            url = m.group().rstrip(".,;")
            if urlparse(url).netloc == cfg.host or url.startswith(URL_NAMESPACES):
                continue
            seen[url] = seen.get(url, 0) + 1
        for url, n in seen.items():
            if n > valid_anchor_hits.get(url, 0):
                problems.append(f"{rel}: third-party URL {url}")
        if SCHEME_RELATIVE_RE.search(text):
            problems.append(f"{rel}: third-party scheme-relative URL")
    return problems


def check_pages(out: Path, cfg: SiteConfig, pages: list[Page], *, launch: bool) -> list[str]:
    problems: list[str] = []
    titles: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    for page in pages:
        f = out / page.out_file
        if not f.is_file():
            problems.append(f"{page.slug}: output file {page.out_file} missing")
            continue
        info = inspect_html(f)
        where = page.out_file
        problems += [f"{where}: {x}" for x in info.problems]
        if info.h1 != 1:
            problems.append(f"{where}: expected one H1, found {info.h1}")
        if info.lang != cfg.lang:
            problems.append(f"{where}: lang must be {cfg.lang}")
        if info.canonical != cfg.base_url + page.path:
            problems.append(f"{where}: canonical must be {cfg.base_url + page.path}")
        if not info.title.strip() or not info.description:
            problems.append(f"{where}: title and description are required")
        if info.title in titles or (info.description or "") in descriptions:
            problems.append(f"{where}: title or description repeats another page")
        titles[info.title] = where
        descriptions[info.description or ""] = where
        noindex = "noindex" in (info.robots or "")
        if launch and noindex and not page.utility:
            problems.append(f"{where}: noindex in a launch build")
        if (not launch or page.utility) and not noindex:
            problems.append(f"{where}: this build must be noindex for this page")
        for src in info.scripts:
            if src not in page.scripts:
                problems.append(f"{where}: script {src} is not declared for this page (W-G3)")
        for src in page.scripts:
            if not (out / src.lstrip("/")).is_file():
                problems.append(f"{page.slug}: declared script {src} is missing from the build")
        for ref in info.refs:
            if ref.lstrip("#") not in info.cite_ids:
                problems.append(f"{where}: footnote {ref} has no citation")
    return problems


def check_company_name(out: Path, cfg: SiteConfig) -> list[str]:
    """W-G5 (EXW3): the company name stands once, in the privacy notice, and nowhere else."""
    problems: list[str] = []
    total = 0
    for p in _dist_files(out):
        n = p.read_bytes().decode("utf-8", errors="ignore").count(cfg.legal_name)
        if not n:
            continue
        total += n
        if _rel(out, p) != "privacy/index.html":
            problems.append(
                f"{_rel(out, p)}: names the company ({cfg.legal_name}); only the privacy notice may"
            )
    if total > 1:
        problems.append(
            f"the company name appears {total} times; the privacy notice may name it once"
        )
    return problems


def check_names(out: Path, names: list[str]) -> list[str]:
    """G8: no person, employer or client name in text, file names or file metadata."""
    problems: list[str] = []
    wanted = [n.strip().lower() for n in names if n.strip() and not n.startswith("#")]
    for p in _dist_files(out):
        rel = _rel(out, p)
        norm_rel = re.sub(r"[-_./]+", " ", rel.lower())
        body = p.read_bytes().decode("latin-1").lower()
        for name in wanted:
            if name in norm_rel or name in body:
                problems.append(f"{rel}: contains a name from the name list")
    return problems


def check_launch(out: Path, cfg: SiteConfig, claims: Claims, names: list[str]) -> list[str]:
    problems: list[str] = []
    if not [n for n in names if n.strip() and not n.startswith("#")]:
        problems.append("launch build needs a name list (--names FILE)")
    if cfg.security_expires > date.today() + timedelta(days=366):
        problems.append("site.yaml: security_expires is more than a year away (RFC 9116)")
    unready = [c for c in claims.claims.values() if c.status != "ready"]
    for p in _dist_files(out):
        rel = _rel(out, p)
        if p.suffix not in {".html", ".txt", ".xml", ".webmanifest"} or rel.startswith(
            "assets/fonts/"
        ):
            continue
        raw = p.read_text()
        if "[[TODO" in raw:
            problems.append(f"{rel}: placeholder [[TODO left in a launch build")
        if ".invalid" in raw:
            problems.append(f"{rel}: a .invalid placeholder is left in a launch build")
        if p.suffix == ".html":
            info = inspect_html(p)
            text = " ".join(info.visible().lower().split())
            for c in unready:
                if " ".join(c.text.lower().split()) in text:
                    problems.append(f"{rel}: unready claim {c.id} is on the page")
    return problems


def check_brand(site_dir: Path, out: Path) -> list[str]:
    targets = [site_dir / "templates", site_dir / "pages"]
    targets += [p for p in out.rglob("*.html")] + [out / "assets" / "exaktiv.css"]
    result = subprocess.run(
        [sys.executable, str(ROOT / "brand" / "tokens" / "check_brand.py"), *map(str, targets)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return []
    return [f"brand guard: {line.strip()}" for line in result.stdout.splitlines() if line.strip()]


def check_dist(
    out: Path,
    cfg: SiteConfig,
    claims: Claims,
    *,
    launch: bool,
    names: list[str],
    pages: list[Page] | None = None,
) -> list[str]:
    problems = check_banned(out, claims) + check_urls(out, cfg, claims)
    problems += check_company_name(out, cfg)
    if pages is not None:
        problems += check_pages(out, cfg, pages, launch=launch)
    if names:
        problems += check_names(out, names)
    if launch:
        problems += check_launch(out, cfg, claims, names)
    return problems


# ---------------------------------------------------------------- build


def _write(out: Path, rel: str, text: str) -> None:
    f = out / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)


def _copy(src: Path, out: Path, rel: str) -> None:
    dst = out / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def copy_brand(brand: Path, out: Path) -> None:
    _copy(brand / "tokens" / "tokens.css", out, "assets/tokens.css")
    _copy(brand / "components" / "exaktiv.css", out, "assets/exaktiv.css")
    _copy(brand / "social" / "og-image.png", out, "assets/og-image.png")
    for f in sorted(
        [
            *(brand / "fonts").glob("*.woff2"),
            brand / "fonts" / "fonts.css",
            *(brand / "fonts").glob("OFL-*.txt"),
        ]
    ):
        _copy(f, out, f"assets/fonts/{f.name}")
    for name in ("exaktiv-lockup.svg", "exaktiv-lockup-reversed.svg", "exaktiv-mark.svg"):
        _copy(brand / "logo" / "svg" / name, out, f"assets/logo/{name}")
    for name in BRAND_FILES:
        _copy(brand / "favicon" / name, out, name)


def copy_site_assets(site_dir: Path, out: Path) -> None:
    """Copy site/assets (the self-hosted scripts) next to the brand assets. A clash is an error."""
    src = site_dir / "assets"
    if not src.is_dir():
        return
    for f in sorted(p for p in src.rglob("*") if p.is_file()):
        rel = f"assets/{f.relative_to(src).as_posix()}"
        if (out / rel).exists():
            raise BuildError(f"site/{rel} clashes with a brand asset")
        _copy(f, out, rel)


def generated_files(cfg: SiteConfig, pages: list[Page], *, launch: bool) -> dict[str, str]:
    urls = "".join(
        f"  <url><loc>{cfg.base_url}{p.path}</loc></url>\n"
        for p in pages
        if p.slug != "404" and not p.utility
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n"
    )
    robots = (
        f"User-agent: *\nAllow: /\n\nSitemap: {cfg.base_url}/sitemap.xml\n"
        if launch
        else "User-agent: *\nDisallow: /\n"
    )
    listing = "\n".join(
        f"- [{p.title}]({cfg.base_url}{p.path}): {p.description}"
        for p in pages
        if p.slug != "404" and not p.utility
    )
    llms = (
        f"# {cfg.brand}\n\n> Legacy modernisation and AI product delivery.\n\n"
        f"## Pages\n\n{listing}\n"
    )
    security = (
        f"Contact: mailto:{cfg.security_email}\n"
        f"Expires: {cfg.security_expires.isoformat()}T00:00:00Z\n"
        f"Preferred-Languages: en\n"
        f"Canonical: {cfg.base_url}/.well-known/security.txt\n"
    )
    headers = "/*\n" + "".join(f"  {k}: {v}\n" for k, v in HEADERS.items())
    return {
        "sitemap.xml": sitemap,
        "robots.txt": robots,
        "llms.txt": llms,
        ".well-known/security.txt": security,
        "_headers": headers,
    }


def json_ld(cfg: SiteConfig) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": cfg.brand,
        "url": cfg.base_url + "/",
        "logo": f"{cfg.base_url}/assets/logo/exaktiv-mark.svg",
    }
    return json.dumps(data, indent=2)


def render_pages(
    site_dir: Path, cfg: SiteConfig, pages: list[Page], claims: Claims, *, launch: bool
) -> dict[str, str]:
    """Render every page. In a launch build an unready claim used on a page is a problem, even
    when the page shows its words with no footnote."""
    env = Environment(
        loader=FileSystemLoader([str(site_dir / "templates"), str(site_dir / "pages")]),
        autoescape=True,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    nav = [p for p in pages if p.in_nav]
    out: dict[str, str] = {}
    problems: list[str] = []
    for page in pages:
        trace = Trace(page, claims)
        try:
            html = env.get_template(f"{page.slug}.html.j2").render(
                cfg=cfg,
                page=page,
                pages=pages,
                nav=nav,
                noindex=not launch or page.utility,
                canonical=cfg.base_url + page.path,
                json_ld=Markup(json_ld(cfg).replace("<", "\\u003c")),
                cite=trace.cite,
                claim=trace.claim,
                source_link=trace.source_link,
                backed=trace.backed,
                ready=trace.ready,
                cites=trace.cites,
            )
        except BuildError as e:
            problems += e.problems
            continue
        out[page.out_file] = html
        if launch:
            problems += [
                f"{page.slug}: unready claim {cid} is used (status {claims.claims[cid].status!r})"
                for cid in sorted(trace.used)
                if claims.claims[cid].status != "ready"
            ]
    if problems:
        raise BuildError(problems)
    return out


def build(
    site_dir: Path,
    brand_dir: Path,
    out_dir: Path,
    *,
    launch: bool = False,
    names_file: Path | None = None,
) -> None:
    site_dir, out_dir = site_dir.resolve(), out_dir.resolve()
    if out_dir in {site_dir, ROOT, brand_dir.resolve()} or site_dir.is_relative_to(out_dir):
        raise BuildError(f"refusing to write the build into {out_dir}")
    cfg, pages = load_config(site_dir)
    claims = load_claims(site_dir / "claims.yaml")
    names = names_file.read_text().splitlines() if names_file else []
    if launch and not names:
        raise BuildError("launch build needs a name list (--names FILE)")
    rendered = render_pages(site_dir, cfg, pages, claims, launch=launch)
    shutil.rmtree(out_dir, ignore_errors=True)
    try:
        for rel, html in rendered.items():
            _write(out_dir, rel, html)
        copy_brand(brand_dir, out_dir)
        copy_site_assets(site_dir, out_dir)
        for rel, text in generated_files(cfg, pages, launch=launch).items():
            _write(out_dir, rel, text)
        problems = check_dist(out_dir, cfg, claims, launch=launch, names=names, pages=pages)
        problems += check_brand(site_dir, out_dir)
        if problems:
            raise BuildError(problems)
        if (
            launch
        ):  # EXW3: the web image starts in live mode only with this marker (site/entrypoint.sh)
            _write(out_dir, LAUNCH_MARKER, "launch build: every launch check passed\n")
    except BuildError:
        shutil.rmtree(out_dir, ignore_errors=True)  # a failed build leaves nothing to deploy
        raise


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--site", type=Path, default=ROOT / "site")
    ap.add_argument("--out", type=Path, default=ROOT / "site" / "dist")
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--names", type=Path, help="name list kept outside the repository (G8)")
    args = ap.parse_args()
    try:
        build(args.site, ROOT / "brand", args.out, launch=args.launch, names_file=args.names)
    except BuildError as e:
        print("Site build failed:")
        print("\n".join(f"  - {p}" for p in e.problems))
        return 1
    print(f"Site built in {args.out} ({'launch' if args.launch else 'staging'} mode).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
