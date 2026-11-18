"""EXD5: a failed Lighthouse audit names the element, so a CI log is enough to fix it."""

import build_site
import check_lighthouse


def test_failing_nodes_name_selector_snippet_and_reason() -> None:
    audit: dict[str, object] = {
        "details": {
            "items": [
                {
                    "node": {
                        "selector": "main > p.lead",
                        "snippet": '<p class="lead">Text</p>',
                        "explanation": "Fix any of the following:\n  insufficient contrast",
                    }
                },
                {"node": {"selector": "a.link", "snippet": "<a>x</a>"}},
                {"not_a_node": True},
            ]
        }
    }
    lines = check_lighthouse.failing_nodes(audit)
    assert len(lines) == 2
    assert lines[0].startswith("main > p.lead | <p class=")
    assert "insufficient contrast" in lines[0] and "\n" not in lines[0]


def test_failing_nodes_tolerate_an_audit_without_details() -> None:
    assert check_lighthouse.failing_nodes({}) == []
    assert check_lighthouse.failing_nodes({"details": {"type": "table"}}) == []


def test_code_line_numbers_use_a_token_that_passes_on_the_ink_panel() -> None:
    """The panel is Ink in both modes. text-disabled (#6B675C) gave 3.26:1 and failed CI."""
    css = (build_site.ROOT / "brand/components/exaktiv.css").read_text()
    rule = next(line for line in css.splitlines() if line.startswith(".ex-code__ln {"))
    assert "var(--ex-on-inverse-faint)" in rule
    assert "text-disabled" not in rule
