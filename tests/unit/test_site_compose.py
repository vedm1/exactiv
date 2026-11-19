"""EXW2: the server compose file of the site (web + form), checked against the rules of the shared bin/deploy.

`bin/deploy` lives in the unveilio repository (deploy/host/apps-nbg/bin/deploy, section "2. the policy") and is root-owned
on the host. `violations()` below is a copy of its jq rules (read 19 Nov 2026). If the host script changes, update the copy.
"""

import copy
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy/site/docker-compose.yml"
PREFIX = "ghcr.io/vedm1/exaktiv/"
FORBIDDEN_KEYS = [
    "privileged", "pid", "ipc", "network_mode", "userns_mode", "devices", "sysctls",
    "volumes", "ports", "build", "env_file", "secrets", "configs",
]  # fmt: skip


def violations(cfg: dict[str, Any], prefix: str = PREFIX) -> list[str]:
    out: list[str] = []
    for name, s in (cfg.get("services") or {}).items():
        for key in FORBIDDEN_KEYS:
            if key in s:
                out.append(f"{name}: {key} is not allowed")
        if any(c != "NET_BIND_SERVICE" for c in s.get("cap_add") or []):
            out.append(f"{name}: cap_add beyond NET_BIND_SERVICE")
        if any(re.search("unconfined|seccomp|apparmor", o) for o in s.get("security_opt") or []):
            out.append(f"{name}: security_opt weakens confinement")
        if re.match(r"^(0|root)(:|$)", str(s.get("user", ""))):
            out.append(f"{name}: runs as root")
        if not str(s.get("image", "")).startswith(prefix):
            out.append(f"{name}: image is outside {prefix}")
    for key in ("volumes", "secrets", "configs"):
        if key in cfg:
            out.append(f"top-level {key} is not allowed")
    nets = cfg.get("networks") or {}
    if list(nets) != ["edge"] or nets["edge"].get("external") is not True:
        out.append("networks must be exactly the external network edge")
    return out


@pytest.fixture(scope="module")
def cfg() -> dict[str, Any]:
    data = yaml.safe_load(COMPOSE.read_text())
    assert isinstance(data, dict)
    return data


def test_site_compose_passes_the_shared_policy(cfg: dict[str, Any]) -> None:
    assert violations(cfg) == []


def test_site_compose_is_its_own_project(cfg: dict[str, Any]) -> None:
    assert cfg["name"] == "exaktiv-site"  # not "exaktiv": deploy-infra owns that project


def _mutate(cfg: dict[str, Any], fn: Any) -> dict[str, Any]:
    bad = copy.deepcopy(cfg)
    fn(bad)
    return bad


@pytest.mark.parametrize(
    "fn, fragment",
    [
        (lambda c: c["services"]["web"].update(ports=["80:80"]), "ports is not allowed"),
        (lambda c: c["services"]["web"].update(volumes=["/:/host"]), "volumes is not allowed"),
        (lambda c: c["services"]["form"].update(user="root"), "runs as root"),
        (lambda c: c["services"]["form"].update(user="0:0"), "runs as root"),
        (lambda c: c["services"]["form"].update(privileged=True), "privileged is not allowed"),
        (lambda c: c["services"]["form"].update(network_mode="host"), "network_mode"),
        (lambda c: c["services"]["form"].update(cap_add=["SYS_ADMIN"]), "cap_add beyond"),
        (lambda c: c["services"]["form"].update(env_file=[".env"]), "env_file is not allowed"),
        (lambda c: c["services"]["form"].update(image="docker.io/library/nginx:1"), "outside"),
        (lambda c: c.update(volumes={"x": {}}), "top-level volumes"),
        (lambda c: c.update(networks={"edge": {"external": True}, "other": {}}), "networks must"),
        (lambda c: c.update(networks={"edge": {}}), "networks must"),
    ],
)
def test_site_compose_policy_mirror_rejects(cfg: dict[str, Any], fn: Any, fragment: str) -> None:
    assert any(fragment in v for v in violations(_mutate(cfg, fn)))


def test_site_compose_services_are_hardened(cfg: dict[str, Any]) -> None:
    assert set(cfg["services"]) == {"web", "form", "migrate", "jobs", "scheduler"}
    aliases: list[str] = []
    for name, s in cfg["services"].items():
        assert s["read_only"] is True, name
        assert s["cap_drop"] == ["ALL"], name
        assert "no-new-privileges:true" in s["security_opt"], name
        assert re.fullmatch(r"[1-9][0-9]*", str(s["user"])), name
        assert s.get("mem_limit"), name
        assert s["cpus"] == 0.5 and s["pids_limit"] == 200, (
            name
        )  # one noisy client cannot starve the host
        assert str(s["image"]).startswith(PREFIX + ("web:" if name == "web" else "site-form:"))
        assert "${IMAGE_TAG:?" in s["image"], name  # the deployed commit, never a floating tag
        aliases += list(s["networks"]["edge"].get("aliases", []))
    for name in ("web", "form"):
        assert cfg["services"][name]["healthcheck"]["test"], name
    assert sorted(aliases) == ["exaktiv-form", "exaktiv-web"]


def test_site_compose_has_migrate_and_jobs_profiles(cfg: dict[str, Any]) -> None:
    mig, jobs, form = (cfg["services"][n] for n in ("migrate", "jobs", "form"))
    assert mig["profiles"] == ["migrate"] and mig["restart"] == "no"
    assert jobs["profiles"] == ["jobs"] and jobs["restart"] == "no"
    assert mig["image"] == form["image"] and jobs["image"] == form["image"]
    cmd = " ".join(mig["command"])
    assert cmd.endswith("alembic -c alembic.ini upgrade head")
    assert "doppler run --no-fallback --" in cmd
    assert "profiles" not in cfg["services"]["web"] and "profiles" not in form


def test_g9_site_compose_holds_only_the_doppler_token(cfg: dict[str, Any]) -> None:
    for name in ("form", "migrate", "jobs", "scheduler"):
        env = cfg["services"][name]["environment"]
        assert list(env) == ["DOPPLER_TOKEN"], name
        assert env["DOPPLER_TOKEN"].startswith("${DOPPLER_TOKEN:?")
    web_env = cfg["services"]["web"]["environment"]
    assert set(web_env) == {"SITE_MODE", "STAGING_BASIC_AUTH_HASH"}
    text = COMPOSE.read_text()
    for pattern in (r"dp\.(st|pt|sa)\.", r"BREVO_API_KEY", r"DATABASE_URL", r"postgres(ql)?://"):
        assert not re.search(pattern, text), pattern


def test_site_compose_web_mode_is_required(cfg: dict[str, Any]) -> None:
    assert cfg["services"]["web"]["environment"]["SITE_MODE"].startswith("${SITE_MODE:?")


def test_w_g4_scheduler_is_one_long_lived_hardened_service_on_the_form_image(
    cfg: dict[str, Any],
) -> None:
    """EXW3: the jobs run in a container that stays up, so Alloy sees `job_done` (retention freshness)."""
    s, form = cfg["services"]["scheduler"], cfg["services"]["form"]
    assert "profiles" not in s and s["restart"] == "unless-stopped"  # `up` starts it
    assert s["image"] == form["image"]
    assert s["read_only"] is True and s["cap_drop"] == ["ALL"] and str(s["user"]) == "10001"
    cmd = " ".join(s["entrypoint"])
    assert cmd.endswith("python -m exaktiv_site_form.scheduler")
    assert "doppler run --no-fallback --" in cmd
    assert "ports" not in s and "volumes" not in s
