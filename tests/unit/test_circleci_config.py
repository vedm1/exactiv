"""EXK0b: the CircleCI pipeline keeps every former GitHub Actions job and deploys only from main."""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".circleci/config.yml"
JOBS = ["python", "ui", "site", "secrets", "integration"]
ALLOWED_REMOTE_SCRIPTS = ("https://astral.sh/uv/0.12.7/",)


@pytest.fixture(scope="module")
def cfg() -> dict[str, Any]:
    data = yaml.safe_load(CONFIG.read_text())
    assert isinstance(data, dict)
    return data


def workflow_jobs(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = cfg["workflows"]["ci"]["jobs"]
    out: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if isinstance(entry, str):
            out[entry] = {}
        else:
            ((name, body),) = entry.items()
            out[name] = body or {}
    return out


def test_circleci_config_has_every_ci_job(cfg: dict[str, Any]) -> None:
    for job in [*JOBS, "deploy-infra"]:
        assert job in cfg["jobs"], job
    assert set(JOBS) <= set(workflow_jobs(cfg))


def test_deploy_infra_needs_every_job_and_runs_only_on_main(cfg: dict[str, Any]) -> None:
    body = workflow_jobs(cfg)["deploy-infra"]
    assert set(body["requires"]) == set(JOBS)
    assert body["filters"]["branches"]["only"] == "main"
    assert body["context"] == "exaktiv_deploy"


def test_other_jobs_do_not_use_the_deploy_context(cfg: dict[str, Any]) -> None:
    for name, body in workflow_jobs(cfg).items():
        if name != "deploy-infra":
            assert "context" not in body, name


def test_circleci_config_has_planted_checks() -> None:
    text = CONFIG.read_text()
    assert "check_brand.py" in text and "planted" in text.lower()
    assert "gitleaks detect --no-git" in text
    assert "did not catch the planted" in text


def test_no_unpinned_remote_script() -> None:
    text = CONFIG.read_text()
    for url in re.findall(
        r"curl[^\n|]*?(https://[^\s\"']+)[^\n]*\|\s*(?:sudo\s+)?(?:sh|bash)", text
    ):
        assert url.startswith(ALLOWED_REMOTE_SCRIPTS), url
    assert "astral.sh/uv/install.sh" not in text, "pin the uv installer version"


def test_python_and_node_versions_are_pinned() -> None:
    text = CONFIG.read_text()
    assert "uv/0.12.7/install.sh" in text
    assert re.search(r"pnpm@\d+\.\d+\.\d+", text)
    assert "GITLEAKS_VERSION" in text and "sha256sum -c" in text


def test_deploy_pins_the_host_key_from_the_repository() -> None:
    text = CONFIG.read_text()
    assert "deploy/known_hosts" in text
    assert "ssh-keyscan" not in text
    assert "StrictHostKeyChecking=yes" in text
    assert (ROOT / "deploy/known_hosts").is_file()


def test_g9_no_secret_values_in_ci_or_deploy_files() -> None:
    pattern = re.compile(
        r"(dp\.(st|pt|sa)\.[A-Za-z0-9]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16})"
    )
    server_files = [
        p for p in (ROOT / "deploy/server").iterdir() if p.is_file() and p.suffix != ".pyc"
    ]
    for path in [CONFIG, *server_files, ROOT / "deploy/known_hosts"]:
        assert not pattern.search(path.read_text()), path


def test_ci_yml_removed() -> None:
    assert not (ROOT / ".github/workflows/ci.yml").exists()


def test_doppler_cli_is_pinned_and_checksummed() -> None:
    text = CONFIG.read_text()
    assert "cli.doppler.com" not in text
    assert re.search(r"V=\d+\.\d+\.\d+", text)
    assert re.search(r"[0-9a-f]{64}  \$\{F\}\" \| sha256sum -c -", text)


def test_secret_export_filters_key_names() -> None:
    assert 'test("^[A-Za-z_][A-Za-z0-9_]*$")' in CONFIG.read_text()


def test_context_restriction_is_documented() -> None:
    assert 'pipeline.git.branch == "main"' in CONFIG.read_text()


def test_site_job_points_lighthouse_at_the_playwright_chromium(cfg: dict[str, Any]) -> None:
    steps = cfg["jobs"]["site"]["steps"]
    text = yaml.safe_dump(steps)
    assert (
        text.index("playwright install")
        < text.index("CHROME_PATH")
        < text.index("check_lighthouse")
    )


def test_load_doppler_prints_secret_names_but_never_values() -> None:
    text = CONFIG.read_text()
    assert "Doppler returned these secret names" in text
    assert "keys | join" in text
    assert 'echo "$secrets"' not in text and "echo $secrets" not in text
