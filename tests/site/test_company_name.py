"""EXW3: the company name stands on one line of the privacy notice (W-G5, rewritten).

Decision of 19 Nov 2026: Valyrian Tech Pvt Ltd is named once, as the controller, with its registered
address. No footer, no schema.org legalName, no llms.txt line. No person is named anywhere (W-G1).
"""

from pathlib import Path

import build_site
import pytest
import yaml

ROOT = build_site.ROOT
NAME = "Valyrian"
ADDRESS = "Nyati Meadows, Pune, India 411014"


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("name") / "dist"
    build_site.build(ROOT / "site", ROOT / "brand", out)
    return out


def test_w_g5_company_name_is_in_the_privacy_notice_once_and_nowhere_else(dist: Path) -> None:
    hits: dict[str, int] = {}
    for f in dist.rglob("*"):
        if f.is_file() and f.suffix in {".html", ".txt", ".xml", ".json", ".webmanifest", ""}:
            n = f.read_text(errors="ignore").count(NAME)
            if n:
                hits[str(f.relative_to(dist))] = n
    assert hits == {"privacy/index.html": 1}


def test_company_name_is_in_the_controller_sentence_with_the_registered_address(
    dist: Path,
) -> None:
    html = (dist / "privacy" / "index.html").read_text()
    sentence = next(p for p in html.split("<p") if NAME in p)
    assert "is the controller" in sentence
    assert ADDRESS in sentence
    assert "hello@exaktiv.com" in html


def test_no_legal_name_in_the_footer_the_schema_or_llms_txt(dist: Path) -> None:
    home = (dist / "index.html").read_text()
    assert "legalName" not in home
    assert "brand of" not in home
    assert "© 2026 Exaktiv" in home
    assert "brand of" not in (dist / "llms.txt").read_text()


def test_page_titles_and_descriptions_do_not_name_the_company() -> None:
    _, pages = build_site.load_config(ROOT / "site")
    for p in pages:
        assert NAME not in p.title + p.description, p.slug


def test_site_yaml_has_real_mail_addresses_and_no_placeholder() -> None:
    cfg = yaml.safe_load((ROOT / "site" / "site.yaml").read_text())
    assert cfg["contact_email"] == "hello@exaktiv.com"
    assert cfg["security_email"] == "security@exaktiv.com"
    assert ".invalid" not in (ROOT / "site" / "site.yaml").read_text()
    assert cfg["registered_address"] == ADDRESS
