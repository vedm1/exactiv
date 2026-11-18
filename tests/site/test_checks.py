"""EXD5: banned claims, third-party URLs, page rules, names, launch mode, brand guard."""

from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

import build_site
import pytest
import yaml

ROOT = build_site.ROOT


def set_body(mini: Path, body: str) -> None:
    (mini / "pages" / "home.html.j2").write_text(
        '{% extends "base.html.j2" %}{% block content %}<h1>H</h1>' + body + "{% endblock %}"
    )


def make_launch_ready(mini: Path) -> Path:
    """Every claim ready and a near expiry date. Returns a synthetic name list."""
    data = yaml.safe_load((mini / "claims.yaml").read_text())
    for c in data["claims"]:
        c["status"] = "ready"
        c["cite"] = "Evidence on file."
    (mini / "claims.yaml").write_text(yaml.safe_dump(data))
    site = mini / "site.yaml"
    soon = (date.today() + timedelta(days=30)).isoformat()
    site.write_text(site.read_text().replace("2099-01-01", soon))
    names = mini.parent / "names.txt"
    names.write_text("# synthetic\nzzqx person\n")
    return names


@pytest.mark.parametrize(
    "text",
    ["We are GDPR compliant.", "gdpr-certified", "Trusted by many teams."],
)
def test_banned_claim_fails_build(mini: Path, build_mini: Callable[..., Path], text: str) -> None:
    set_body(mini, f"<p>{text}</p>")
    with pytest.raises(build_site.BuildError, match="banned"):
        build_mini()


def test_banned_claim_in_title_fails(mini: Path, build_mini: Callable[..., Path]) -> None:
    pages = mini / "pages.yaml"
    pages.write_text(pages.read_text().replace("Fixture home", "Trusted by all"))
    with pytest.raises(build_site.BuildError, match="banned"):
        build_mini()


def test_clean_text_passes(mini: Path, build_mini: Callable[..., Path]) -> None:
    set_body(mini, "<p>Built on stated principles.</p>")
    build_mini()


@pytest.mark.parametrize(
    "markup",
    [
        '<script src="https://cdn.example.net/a.js"></script>',
        '<link rel="stylesheet" href="https://fonts.example.net/x.css">',
        '<img src="https://img.example.net/a.png" alt="x">',
        '<a href="https://rules.example.org/a" rel="noopener noreferrer">x</a>'
        '<img src="https://rules.example.org/a" alt="x">',
        '<a href="https://elsewhere.example.net/">x</a>',
        '<a href="https://rules.example.org/a">x</a>',
    ],
)
def test_third_party_url_fails(mini: Path, build_mini: Callable[..., Path], markup: str) -> None:
    set_body(mini, markup)
    with pytest.raises(build_site.BuildError, match="third-party|inline|script"):
        build_mini()


def test_third_party_url_in_css_fails(mini: Path, build_mini: Callable[..., Path]) -> None:
    out = build_mini()
    css = out / "assets" / "exaktiv.css"
    css.write_text(css.read_text() + '\n@import url("https://fonts.example.net/x.css");\n')
    config, _ = build_site.load_config(mini)
    claims = build_site.load_claims(mini / "claims.yaml")
    problems = build_site.check_dist(out, config, claims, launch=False, names=[])
    assert any("third-party" in p for p in problems)


def test_allowed_urls_pass(build_mini: Callable[..., Path]) -> None:
    html = (build_mini() / "index.html").read_text()
    assert 'href="https://rules.example.org/a" rel="noopener noreferrer"' in html


@pytest.mark.parametrize(
    "markup",
    [
        '<p style="color:red">x</p>',
        "<style>p{margin:0}</style>",
        "<script>1</script>",
        "<h1>Two</h1>",
    ],
)
def test_page_rules_fail(mini: Path, build_mini: Callable[..., Path], markup: str) -> None:
    set_body(mini, markup)
    with pytest.raises(build_site.BuildError):
        build_mini()


def test_page_rules_pass_on_mini(build_mini: Callable[..., Path]) -> None:
    out = build_mini()
    html = (out / "index.html").read_text()
    assert html.count("<h1") == 1
    assert '<html lang="en-GB">' in html
    assert '<link rel="canonical" href="https://example.test/">' in html
    assert (out / "404.html").is_file()


def test_staging_is_noindex(build_mini: Callable[..., Path]) -> None:
    staging = build_mini()
    assert 'name="robots" content="noindex"' in (staging / "index.html").read_text()
    assert "Disallow: /" in (staging / "robots.txt").read_text()


def test_generated_files(build_mini: Callable[..., Path]) -> None:
    out = build_mini()
    sitemap = (out / "sitemap.xml").read_text()
    assert "<loc>https://example.test/</loc>" in sitemap
    assert "404" not in sitemap
    sec = (out / ".well-known" / "security.txt").read_text()
    for field in ("Contact: mailto:security@example.test", "Expires: 2099-01-01T00:00:00Z"):
        assert field in sec
    assert "Canonical: https://example.test/.well-known/security.txt" in sec
    assert "Preferred-Languages: en" in sec
    assert (out / "llms.txt").is_file()
    html = (out / "index.html").read_text()
    assert '"@type": "Organization"' in html
    assert '"legalName": "Example Test Ltd"' in html
    assert "Person" not in html


def test_security_txt_expiry_must_be_in_the_future(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    site = mini / "site.yaml"
    site.write_text(site.read_text().replace("2099-01-01", "2020-01-01"))
    with pytest.raises(build_site.BuildError, match="security_expires"):
        build_mini()


def test_headers_exact_csp(build_mini: Callable[..., Path]) -> None:
    text = (build_mini() / "_headers").read_text()
    assert (
        "Content-Security-Policy: default-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
        in text
    )
    for h in (
        "X-Content-Type-Options: nosniff",
        "Referrer-Policy:",
        "Permissions-Policy:",
        "Strict-Transport-Security:",
    ):
        assert h in text


def test_brand_assets_are_copied(build_mini: Callable[..., Path]) -> None:
    out = build_mini()
    for rel in (
        "assets/tokens.css",
        "assets/exaktiv.css",
        "assets/fonts/fonts.css",
        "favicon.ico",
        "site.webmanifest",
        "assets/og-image.png",
    ):
        assert (out / rel).is_file(), rel


def test_g8_names_in_text_filename_and_metadata_fail(tmp_path: Path) -> None:
    names = ["zzqx person"]
    out = tmp_path / "dist"
    out.mkdir()
    (out / "a.html").write_text("<p>By Zzqx Person.</p>")
    assert build_site.check_names(out, names)
    (out / "a.html").write_text("<p>clean</p>")
    assert not build_site.check_names(out, names)
    (out / "zzqx-person.txt").write_text("x")
    assert build_site.check_names(out, names)
    (out / "zzqx-person.txt").unlink()
    (out / "img.png").write_bytes(b"\x89PNG....Author=ZZQX PERSON....")
    assert build_site.check_names(out, names)


def test_launch_mode_gates(mini: Path, build_mini: Callable[..., Path], tmp_path: Path) -> None:
    names = tmp_path / "names.txt"
    names.write_text("zzqx person\n")
    build_mini()  # staging passes with unready claims and no names file
    with pytest.raises(build_site.BuildError) as err:
        build_mini(launch=True, names_file=names)
    msg = str(err.value)
    assert "open-claim" in msg  # unready claim used
    with pytest.raises(build_site.BuildError, match="--names"):
        build_mini(launch=True)


def test_launch_mode_passes_when_everything_is_ready(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    names = make_launch_ready(mini)
    out = build_mini(launch=True, names_file=names)
    assert "noindex" not in (out / "index.html").read_text()
    assert "Sitemap: https://example.test/sitemap.xml" in (out / "robots.txt").read_text()


def test_launch_mode_rejects_unready_claim_text_typed_by_hand(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    names = make_launch_ready(mini)
    data = yaml.safe_load((mini / "claims.yaml").read_text())
    data["claims"][1]["status"] = "to_confirm"
    (mini / "claims.yaml").write_text(yaml.safe_dump(data))
    set_body(mini, "<p>Models run in your region.</p>")
    with pytest.raises(build_site.BuildError, match="unready claim"):
        build_mini(launch=True, names_file=names)


def test_launch_mode_rejects_placeholders(mini: Path, build_mini: Callable[..., Path]) -> None:
    names = make_launch_ready(mini)
    set_body(mini, "<p>[[TODO registered address]]</p>")
    with pytest.raises(build_site.BuildError, match="TODO"):
        build_mini(launch=True, names_file=names)
    set_body(mini, "<p>ok</p>")
    site = mini / "site.yaml"
    site.write_text(site.read_text().replace("example.test", "example.invalid"))
    with pytest.raises(build_site.BuildError, match="invalid"):
        build_mini(launch=True, names_file=names)


def test_launch_mode_rejects_far_expiry(mini: Path, build_mini: Callable[..., Path]) -> None:
    names = make_launch_ready(mini)
    site = mini / "site.yaml"
    site.write_text(site.read_text().replace(date.today().isoformat()[:4], "2099", 1))
    site.write_text(
        "\n".join(
            ln if not ln.startswith("security_expires") else 'security_expires: "2099-01-01"'
            for ln in site.read_text().splitlines()
        )
    )
    with pytest.raises(build_site.BuildError, match="year"):
        build_mini(launch=True, names_file=names)


def test_brand_guard_on_site_fails_on_planted_hex(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    (mini / "templates" / "extra.css").write_text("a { color: #ff0000; }\n")
    with pytest.raises(build_site.BuildError, match="brand"):
        build_mini()
