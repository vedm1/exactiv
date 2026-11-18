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


def test_real_site_has_the_ten_prd_w_pages() -> None:
    _, pages = build_site.load_config(ROOT / "site")
    assert {p.slug for p in pages} == SLUGS


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


def test_real_site_launch_build_fails_while_claims_are_open(tmp_path: Path) -> None:
    names = tmp_path / "names.txt"
    names.write_text("zzqx person\n")
    with pytest.raises(build_site.BuildError) as err:
        build_site.build(
            ROOT / "site", ROOT / "brand", tmp_path / "d", launch=True, names_file=names
        )
    msg = str(err.value)
    assert "unready claim" in msg


def test_real_site_has_no_script_and_no_inline_style(dist: Path) -> None:
    for f in dist.rglob("*.html"):
        text = f.read_text()
        assert "<script" not in text.replace('<script type="application/ld+json">', "")
        assert "<style" not in text
