"""EXD5: a failed Lighthouse audit names the element, so a CI log is enough to fix it."""

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
