"""EXD5: the Trace gate (G1 applied to the website) and the claims file schema."""

from collections.abc import Callable
from pathlib import Path

import build_site
import pytest
import yaml


def set_template(mini: Path, body: str) -> None:
    (mini / "pages" / "home.html.j2").write_text(
        '{% extends "base.html.j2" %}{% block content %}<h1>H</h1>' + body + "{% endblock %}"
    )


def test_g1_cite_unready_claim_fails_build(mini: Path, build_mini: Callable[..., Path]) -> None:
    set_template(mini, "{{ cite('open-claim') }}")
    with pytest.raises(build_site.BuildError) as err:
        build_mini()
    assert "open-claim" in str(err.value)


def test_g1_cite_unknown_claim_fails(mini: Path, build_mini: Callable[..., Path]) -> None:
    set_template(mini, "{{ cite('nope') }}")
    with pytest.raises(build_site.BuildError, match="nope"):
        build_mini()


def test_g1_ready_claim_gets_footnote(build_mini: Callable[..., Path]) -> None:
    html = (build_mini() / "index.html").read_text()
    assert '<a class="ex-ref" href="#c1">1</a>' in html
    assert (
        '<li id="c1"><span class="ex-cite__n">1</span>Inbox routine, synthetic fixture.</li>'
        in html
    )


def test_trace_numbers_follow_first_use(mini: Path, tmp_path: Path) -> None:
    claims = yaml.safe_load((mini / "claims.yaml").read_text())
    second = dict(claims["claims"][0], id="second", text="Second.", cite="Second source.")
    claims["claims"].append(second)
    (mini / "claims.yaml").write_text(yaml.safe_dump(claims))
    set_template(mini, "{{ cite('second') }}{{ cite('ready-claim') }}{{ cite('second') }}")
    out = tmp_path / "dist"
    build_site.build(mini, build_site.ROOT / "brand", out)
    html = (out / "index.html").read_text()
    assert html.count('class="ex-ref"') == 3
    assert html.count('<li id="c') == 2
    assert html.index('href="#c1">1<') < html.index('href="#c2">2<') < html.rindex('href="#c1">1<')
    assert html.index("Second source.") < html.index("Inbox routine")


def test_ready_claim_without_cite_text_fails(mini: Path) -> None:
    data = yaml.safe_load((mini / "claims.yaml").read_text())
    del data["claims"][0]["cite"]
    (mini / "claims.yaml").write_text(yaml.safe_dump(data))
    with pytest.raises(build_site.BuildError, match="cite"):
        build_site.load_claims(mini / "claims.yaml")


def test_claims_file_needs_version(mini: Path) -> None:
    data = yaml.safe_load((mini / "claims.yaml").read_text())
    del data["version"]
    (mini / "claims.yaml").write_text(yaml.safe_dump(data))
    with pytest.raises(build_site.BuildError, match="version"):
        build_site.load_claims(mini / "claims.yaml")


def test_source_url_must_be_in_allow_list(mini: Path) -> None:
    data = yaml.safe_load((mini / "claims.yaml").read_text())
    data["claims"][2]["source_url"] = "https://other.example.org/x"
    (mini / "claims.yaml").write_text(yaml.safe_dump(data))
    with pytest.raises(build_site.BuildError, match="external_allow"):
        build_site.load_claims(mini / "claims.yaml")


def test_claim_used_on_page_not_in_its_pages_list_fails(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    data = yaml.safe_load((mini / "claims.yaml").read_text())
    data["claims"][1]["pages"] = ["team"]
    (mini / "claims.yaml").write_text(yaml.safe_dump(data))
    with pytest.raises(build_site.BuildError, match="open-claim"):
        build_mini()


def test_backed_words_get_band_and_number_only_when_ready(
    mini: Path, build_mini: Callable[..., Path]
) -> None:
    set_template(
        mini,
        "<p>{{ backed('ready-claim', 'Ready words') }}</p>"
        "<p>{{ backed('open-claim', 'Open words') }}</p>",
    )
    html = (build_mini() / "index.html").read_text()
    assert '<span class="ex-mark">Ready words</span><a class="ex-ref" href="#c1">1</a>' in html
    assert "<p>Open words</p>" in html
