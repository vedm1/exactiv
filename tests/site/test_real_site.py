"""EXD5: the real site in site/ builds in staging mode and meets the PRD-W page list."""

import html
import re
from pathlib import Path

import build_site
import pytest

ROOT = build_site.ROOT
FOOTNOTE = r'<li id="c\d+"><span class="ex-cite__n">\d+</span>(.*?)</li>'
SLUGS = {
    "home",
    "legacy-modernisation",
    "ai-product-delivery",
    "product-data",
    "how-we-work",
    "security",
    "team",
    "contact",
    "privacy",
    "404",
}


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("real") / "dist"
    build_site.build(ROOT / "site", ROOT / "brand", out)
    return out


UTILITY_SLUGS = {"contact-thanks", "contact-problem"}  # EXW1-ui: form states, not PRD-W pages


def test_real_site_has_the_ten_prd_w_pages() -> None:
    _, pages = build_site.load_config(ROOT / "site")
    assert {p.slug for p in pages if not p.utility} == SLUGS
    assert {p.slug for p in pages if p.utility} == UTILITY_SLUGS


def test_real_site_page_meta_lengths() -> None:
    _, pages = build_site.load_config(ROOT / "site")
    for p in pages:
        assert len(p.title) <= 60, p.slug
        assert 50 <= len(p.description) <= 160, p.slug


def test_real_site_staging_build_passes_and_is_noindex(dist: Path) -> None:
    assert "noindex" in (dist / "index.html").read_text()
    assert (dist / "404.html").is_file()


def test_g1_real_site_footnotes_belong_to_ready_claims_only(dist: Path) -> None:
    claims = build_site.load_claims(ROOT / "site" / "claims.yaml")
    ready = {html.escape(c.cite or "") for c in claims.claims.values() if c.status == "ready"}
    found = 0
    for f in dist.rglob("*.html"):
        for text in re.findall(
            r'<li id="c\d+"><span class="ex-cite__n">\d+</span>(.*?)</li>', f.read_text()
        ):
            found += 1
            assert text in ready, f"{f.name}: footnote text of a claim that is not ready"
    assert found >= 2  # the home and contact pages carry the two ready claims


def test_real_site_launch_build_passes_without_unready_claims(tmp_path: Path) -> None:
    """EXW3: a launch build of the real site passes. Unevidenced sentences stay off."""
    names = tmp_path / "names.txt"
    names.write_text("zzqx person\n")
    out = tmp_path / "d"
    build_site.build(ROOT / "site", ROOT / "brand", out, launch=True, names_file=names)
    assert "noindex" not in (out / "index.html").read_text()
    claims = build_site.load_claims(ROOT / "site" / "claims.yaml")
    text = " ".join(f.read_text() for f in out.rglob("*.html"))
    for c in claims.claims.values():
        if c.status != "ready":
            assert c.text not in html.unescape(text), f"unready claim {c.id} is on a page"


def test_w_g2_launch_build_fails_when_an_unready_claim_is_forced_onto_a_page(
    tmp_path: Path,
) -> None:
    """The guard is in the templates. The build still fails on a hand-typed claim."""
    site = tmp_path / "site"
    import shutil

    shutil.copytree(ROOT / "site", site, ignore=shutil.ignore_patterns("dist", "build"))
    home = site / "pages" / "home.html.j2"
    home.write_text(
        home.read_text().replace(
            "We modernise legacy software and ship AI products.",
            "We modernise legacy software. AI processing stays in your region.",
        )
    )
    names = tmp_path / "names.txt"
    names.write_text("zzqx person\n")
    with pytest.raises(build_site.BuildError, match="unready claim"):
        build_site.build(site, ROOT / "brand", tmp_path / "d", launch=True, names_file=names)


def test_a_claim_that_becomes_ready_makes_its_sentence_appear(tmp_path: Path) -> None:
    import shutil

    import yaml

    site = tmp_path / "site"
    shutil.copytree(ROOT / "site", site, ignore=shutil.ignore_patterns("dist", "build"))
    data = yaml.safe_load((site / "claims.yaml").read_text())
    for c in data["claims"]:
        if c["id"] == "access-logged":
            c["status"] = "ready"
            c["cite"] = "Synthetic evidence for the test."
    (site / "claims.yaml").write_text(yaml.safe_dump(data))
    out = tmp_path / "d"
    build_site.build(site, ROOT / "brand", out)
    sentence = "Access to client code is limited to the named delivery team"
    assert sentence in (out / "security" / "index.html").read_text()
    plain = tmp_path / "plain"
    build_site.build(ROOT / "site", ROOT / "brand", plain)
    assert sentence not in (plain / "security" / "index.html").read_text()


def test_launch_claims_state_of_the_real_register() -> None:
    claims = build_site.load_claims(ROOT / "site" / "claims.yaml")
    status = {c.id: c.status for c in claims.claims.values()}
    ready = ("team-experience", "reply-time", "human-approval")
    for cid in (*ready, "eu-cra", "eu-data-act", "eu-nis2", "eu-ai-act"):
        assert status[cid] == "ready", cid
    for cid in (
        "findings-sourced",
        "in-region",
        "no-training",
        "nda-dpa",
        "access-logged",
        "retention",
    ):
        assert status[cid] != "ready", f"{cid} has no evidence yet"


def test_real_site_scripts_are_self_hosted_theme_everywhere_and_contact_on_the_form_pages(
    dist: Path,
) -> None:
    theme = '<script src="/assets/theme.js"></script>'
    contact = '<script src="/assets/contact.js" defer></script>'
    form_pages = {"contact/index.html", "contact/problem/index.html"}
    for f in dist.rglob("*.html"):
        text = f.read_text().replace('<script type="application/ld+json">', "")
        assert theme in text, f.name
        if str(f.relative_to(dist)) in form_pages:
            assert text.count("<script") == 2 and contact in text, f.name
        else:
            assert text.count("<script") == 1, f.name
        assert "<style" not in text
