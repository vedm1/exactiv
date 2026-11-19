"""EXW1-ui: the contact form markup matches the PRD-W section 7 rules and the service."""

from html.parser import HTMLParser
from pathlib import Path

import build_site
import pytest
from exaktiv_site_form.models import DATA_REGION_LABELS, TOPIC_LABELS, DataRegion, Topic
from exaktiv_site_form.validation import MESSAGES, validate

from tests.unit.site_form_fakes import VALID_FORM

ROOT = build_site.ROOT
FORM_PAGES = ["contact/index.html", "contact/problem/index.html"]
FIELDS = ["name", "email", "company", "role", "topic", "data_region", "message"]


class FormInfo(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict[str, str]] = []
        self.controls: dict[str, dict[str, str]] = {}
        self.options: dict[str, list[str]] = {}
        self.labels: set[str] = set()
        self.ids: set[str] = set()
        self.buttons: list[dict[str, str]] = []
        self._select: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v if v is not None else "" for k, v in attrs}
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "form":
            self.forms.append(a)
        elif tag in {"input", "select", "textarea"} and "name" in a:
            self.controls[a["name"]] = {"tag": tag, **a}
            if tag == "select":
                self._select = a["name"]
                self.options[a["name"]] = []
        elif tag == "option" and self._select:
            self.options[self._select].append(a.get("value", ""))
        elif tag == "label" and "for" in a:
            self.labels.add(a["for"])
        elif tag == "button":
            self.buttons.append(a)

    def handle_endtag(self, tag: str) -> None:
        if tag == "select":
            self._select = None


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("form") / "dist"
    build_site.build(ROOT / "site", ROOT / "brand", out)
    return out


def info(dist: Path, rel: str) -> FormInfo:
    parser = FormInfo()
    parser.feed((dist / rel).read_text())
    return parser


@pytest.mark.parametrize("rel", FORM_PAGES)
def test_contact_form_has_every_prd_w_field_with_limits(dist: Path, rel: str) -> None:
    f = info(dist, rel)
    assert len(f.forms) == 1
    assert f.forms[0]["method"] == "post" and f.forms[0]["action"] == "/enquiries"
    assert set(f.controls) >= {*FIELDS, "website", "form_token"}
    required = {n for n in FIELDS if "required" in f.controls[n]}
    assert required == {"name", "email", "company", "topic", "message"}
    assert f.controls["email"]["type"] == "email"
    limits = {
        "name": (2, 100),
        "company": (2, 150),
        "role": (None, 100),
        "message": (20, 2000),
    }
    for name, (lo, hi) in limits.items():
        c = f.controls[name]
        assert int(c["maxlength"]) == hi, name
        assert (int(c["minlength"]) if lo else None) == lo, name
    assert int(f.controls["email"]["maxlength"]) == 254


@pytest.mark.parametrize("rel", FORM_PAGES)
def test_form_limits_match_service_validation(dist: Path, rel: str) -> None:
    """The HTML limits and the service rules are one rule: test both at the boundary."""
    f = info(dist, rel)
    for name in ("name", "company", "role", "message"):
        lo = int(f.controls[name].get("minlength", "0"))
        hi = int(f.controls[name]["maxlength"])
        for length, ok in ((lo, True), (hi, True), (hi + 1, False), (lo - 1, False)):
            if length <= 0:
                continue
            raw = {**VALID_FORM, name: "x" * length}
            assert (not isinstance(validate(raw), list)) is ok, (name, length)


@pytest.mark.parametrize("rel", FORM_PAGES)
def test_form_option_values_match_service_enums(dist: Path, rel: str) -> None:
    f = info(dist, rel)
    assert [v for v in f.options["topic"] if v] == [t.value for t in Topic]
    assert [v for v in f.options["data_region"] if v] == [r.value for r in DataRegion]
    html = (dist / rel).read_text()
    for label in (*TOPIC_LABELS.values(), *DATA_REGION_LABELS.values()):
        assert f">{label}<" in html
    assert f.options["topic"][0] == "" and f.options["data_region"][0] == ""


@pytest.mark.parametrize("rel", FORM_PAGES)
def test_every_visible_control_has_a_label_and_an_error_slot(dist: Path, rel: str) -> None:
    f = info(dist, rel)
    for name in FIELDS:
        c = f.controls[name]
        assert c["id"] in f.labels, f"{name}: no label"
        assert f"{c['id']}-error" in f.ids, f"{name}: no error slot"
        assert f"{c['id']}-error" in c["aria-describedby"], name


@pytest.mark.parametrize("rel", FORM_PAGES)
def test_error_messages_in_the_form_equal_the_service_messages(dist: Path, rel: str) -> None:
    form = info(dist, rel).forms[0]
    for code, text in MESSAGES.items():
        assert form[f"data-msg-{code.replace('_', '-')}"] == text
    assert form["data-msg-rate-limited"] and form["data-msg-failed"]


@pytest.mark.parametrize("rel", FORM_PAGES)
def test_honeypot_is_not_display_none_and_not_focusable(dist: Path, rel: str) -> None:
    c = info(dist, rel).controls["website"]
    assert c["tabindex"] == "-1" and c["autocomplete"] == "off"
    assert "ex-honeypot" in c["class"]
    assert c.get("type") == "text" and "hidden" not in c
    assert c["id"] in info(dist, rel).labels


@pytest.mark.parametrize("rel", FORM_PAGES)
def test_contact_has_privacy_line_and_mailto_second_route(dist: Path, rel: str) -> None:
    html = (dist / rel).read_text()
    assert "We use your details only to reply to you." in html
    assert 'href="/privacy/"' in html
    assert "mailto:" in html
    assert "checkbox" not in html  # no marketing consent box (PRD-W section 7)


@pytest.mark.parametrize("rel", FORM_PAGES)
def test_one_primary_button_on_the_form_pages(dist: Path, rel: str) -> None:
    html = (dist / rel).read_text()
    assert html.count("ex-btn--primary") == 1
    submit = [b for b in info(dist, rel).buttons if b.get("type") == "submit"]
    assert len(submit) == 1 and "ex-btn--primary" in submit[0]["class"]


def test_thanks_page_confirms_and_names_the_next_step(dist: Path) -> None:
    html = (dist / "contact/thanks/index.html").read_text()
    assert "1 business day" in html
    assert "<form" not in html


def test_problem_page_explains_without_echoing_input(dist: Path) -> None:
    html = (dist / "contact/problem/index.html").read_text()
    assert "could not send" in html.lower()
    assert "errors=" not in html


def test_contact_js_is_loaded_only_by_the_form_pages(dist: Path) -> None:
    with_js = {
        str(f.relative_to(dist))
        for f in dist.rglob("*.html")
        if 'src="/assets/contact.js"' in f.read_text()
    }
    assert with_js == {"contact/index.html", "contact/problem/index.html"}
    js = (dist / "assets" / "contact.js").read_text()
    for forbidden in ("localStorage", "sessionStorage", "document.cookie", "http://", "https://"):
        assert forbidden not in js
