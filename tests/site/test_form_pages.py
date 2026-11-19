"""EXW1-ui: utility pages and the allowed script, as build rules (W-G3), on the mini-site."""

from collections.abc import Callable
from pathlib import Path

import build_site
import pytest

from tests.site.test_checks import make_launch_ready

UTILITY_ROW = (
    '  - {slug: thanks, path: "/contact/thanks/", title: "Fixture thanks", '
    'description: "A synthetic confirmation page for the site builder tests.", '
    "in_nav: false, utility: true, cta: null}\n"
)
FORM_ROW = (
    '  - {slug: form, path: "/contact/", title: "Fixture form", '
    'description: "A synthetic form page for the site builder tests.", '
    'in_nav: false, scripts: ["/assets/app.js"], cta: null}\n'
)


def add_pages(mini: Path, *rows: str) -> None:
    pages = mini / "pages.yaml"
    pages.write_text(pages.read_text() + "".join(rows))
    for row in rows:
        slug = row.split("slug: ")[1].split(",")[0]
        (mini / "pages" / f"{slug}.html.j2").write_text(
            '{% extends "base.html.j2" %}{% block content %}<h1>H</h1>'
            '<form method="post" action="/enquiries"></form>{% endblock %}'
        )


def add_script(mini: Path, body: str = "// synthetic\n") -> None:
    (mini / "assets").mkdir(exist_ok=True)
    (mini / "assets" / "app.js").write_text(body)


def test_utility_page_is_noindex_and_left_out_of_sitemap_and_llms_txt(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    add_pages(mini, UTILITY_ROW)
    out = build_mini()
    assert "noindex" in (out / "contact/thanks/index.html").read_text()
    assert "/contact/thanks/" not in (out / "sitemap.xml").read_text()
    assert "/contact/thanks/" not in (out / "llms.txt").read_text()
    assert "<loc>https://example.test/</loc>" in (out / "sitemap.xml").read_text()


def test_launch_build_allows_noindex_only_on_utility_pages(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    add_pages(mini, UTILITY_ROW)
    out = build_mini(launch=True, names_file=make_launch_ready(mini))
    assert "noindex" in (out / "contact/thanks/index.html").read_text()
    assert "noindex" not in (out / "index.html").read_text()


def test_w_g3_declared_self_hosted_script_is_allowed_and_copied(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    add_pages(mini, FORM_ROW)
    add_script(mini)
    out = build_mini()
    assert '<script src="/assets/app.js"' in (out / "contact/index.html").read_text()
    assert (out / "assets" / "app.js").is_file()


def test_w_g3_script_on_a_page_that_did_not_declare_it_fails(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    add_pages(mini, FORM_ROW)
    add_script(mini)
    (mini / "pages" / "home.html.j2").write_text(
        '{% extends "base.html.j2" %}{% block content %}<h1>H</h1>'
        '<script src="/assets/app.js"></script>{% endblock %}'
    )
    with pytest.raises(build_site.BuildError, match="script"):
        build_mini()


@pytest.mark.parametrize(
    "tag",
    [
        "<script>alert(1)</script>",
        '<script src="https://cdn.example.net/a.js"></script>',
        '<script src="//cdn.example.net/a.js"></script>',
        '<script src="/assets/other.js"></script>',
    ],
)
def test_w_g3_inline_or_foreign_script_fails_even_on_the_form_page(
    mini: Path, build_mini: Callable[..., Path], tag: str
) -> None:
    add_pages(mini, FORM_ROW)
    add_script(mini)
    (mini / "pages" / "form.html.j2").write_text(
        '{% extends "base.html.j2" %}{% block content %}<h1>H</h1>' + tag + "{% endblock %}"
    )
    with pytest.raises(build_site.BuildError, match="script|third-party"):
        build_mini()


def test_declared_script_without_a_source_file_fails(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    add_pages(mini, FORM_ROW)
    with pytest.raises(build_site.BuildError, match="app.js"):
        build_mini()


def test_w_g3_form_that_posts_to_another_origin_fails(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    add_pages(mini, FORM_ROW)
    add_script(mini)
    (mini / "pages" / "form.html.j2").write_text(
        '{% extends "base.html.j2" %}{% block content %}<h1>H</h1>'
        '<form method="post" action="https://forms.example.net/x"></form>{% endblock %}'
    )
    with pytest.raises(build_site.BuildError, match="form|third-party"):
        build_mini()


def test_csp_has_form_action_self() -> None:
    assert "form-action 'self'" in build_site.CSP
