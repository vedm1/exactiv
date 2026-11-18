"""EXK0b: the compose policy of deploy-infra (an allowlist). Each rule has a test that breaks it."""

import copy
import importlib.util
import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("exaktiv_policy", ROOT / "deploy/server/policy.py")
assert _spec and _spec.loader
policy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(policy)

DIGEST = "@sha256:" + "a" * 64


def good() -> dict[str, Any]:
    return {
        "name": "exaktiv",
        "services": {
            "minio": {
                "image": "cgr.dev/chainguard/minio:latest" + DIGEST,
                "command": ["server", "/data"],
                "user": "65532",
                "environment": {"MINIO_ROOT_USER": "u" * 8, "MINIO_ROOT_PASSWORD": "p" * 12},
                "ports": [
                    {"mode": "ingress", "host_ip": "127.0.0.1", "target": 9000, "published": "9000"}
                ],
                "volumes": [
                    {"type": "volume", "source": "miniodata", "target": "/data", "volume": {}}
                ],
                "healthcheck": {"test": ["CMD", "mc", "ready", "local"]},
                "mem_limit": "1g",
                "restart": "unless-stopped",
                "networks": {"default": None},
            }
        },
        "networks": {"default": {"name": "exaktiv_default"}},
        "volumes": {"miniodata": {"name": "exaktiv_miniodata"}},
    }


def svc(c: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = c["services"]["minio"]
    return out


def test_policy_accepts_a_good_config() -> None:
    assert policy.check(good()) == []


MUTATIONS: dict[str, Callable[[dict[str, Any]], None]] = {
    # keys that are not on the allowlist (a few of many)
    "privileged": lambda c: svc(c).update(privileged=True),
    "pid": lambda c: svc(c).update(pid="host"),
    "ipc": lambda c: svc(c).update(ipc="host"),
    "uts": lambda c: svc(c).update(uts="host"),
    "cgroup": lambda c: svc(c).update(cgroup="host"),
    "network_mode": lambda c: svc(c).update(network_mode="host"),
    "userns_mode": lambda c: svc(c).update(userns_mode="host"),
    "devices": lambda c: svc(c).update(devices=["/dev/sda"]),
    "sysctls": lambda c: svc(c).update(sysctls={"a": "1"}),
    "build": lambda c: svc(c).update(build={"context": "."}),
    "env_file_left_in_config": lambda c: svc(c).update(env_file=["x.env"]),
    "secrets": lambda c: svc(c).update(secrets=["s"]),
    "configs": lambda c: svc(c).update(configs=["c"]),
    "cap_add": lambda c: svc(c).update(cap_add=["NET_ADMIN"]),
    "security_opt": lambda c: svc(c).update(security_opt=["seccomp=unconfined"]),
    "volumes_from": lambda c: svc(c).update(volumes_from=["container:wevit-backend-1"]),
    "group_add": lambda c: svc(c).update(group_add=["docker"]),
    "extra_hosts": lambda c: svc(c).update(extra_hosts=["a:1.1.1.1"]),
    "labels": lambda c: svc(c).update(labels={"caddy": "x.example"}),
    "entrypoint": lambda c: svc(c).update(entrypoint=["sh"]),
    "deploy": lambda c: svc(c).update(deploy={"replicas": 50}),
    "scale": lambda c: svc(c).update(scale=50),
    "runtime": lambda c: svc(c).update(runtime="nvidia"),
    # user
    "root_user": lambda c: svc(c).update(user="root"),
    "root_uid": lambda c: svc(c).update(user="0:0"),
    "root_uid_zero_padded": lambda c: svc(c).update(user="00"),
    "no_user": lambda c: svc(c).pop("user"),
    # environment
    "foreign_environment_key": lambda c: svc(c)["environment"].update(POSTGRES_PASSWORD="x"),
    # mounts and volumes
    "bind_mount": lambda c: svc(c).update(
        volumes=[{"type": "bind", "source": "/etc", "target": "/etc"}]
    ),
    "docker_socket": lambda c: svc(c).update(
        volumes=[{"type": "bind", "source": "/var/run/docker.sock", "target": "/s"}]
    ),
    "unknown_named_volume": lambda c: svc(c).update(
        volumes=[{"type": "volume", "source": "other", "target": "/data", "volume": {}}]
    ),
    "volume_subpath": lambda c: svc(c).update(
        volumes=[
            {"type": "volume", "source": "miniodata", "target": "/d", "volume": {"subpath": "x"}}
        ]
    ),
    "volume_driver_opts_bind_root": lambda c: c["volumes"].update(
        miniodata={
            "name": "exaktiv_miniodata",
            "driver": "local",
            "driver_opts": {"type": "none", "o": "bind", "device": "/"},
        }
    ),
    "volume_name_of_another_project": lambda c: c["volumes"].update(
        miniodata={"name": "unveilio_pgdata"}
    ),
    "external_volume": lambda c: c["volumes"].update(
        miniodata={"name": "exaktiv_v", "external": True}
    ),
    # ports
    "port_all_interfaces": lambda c: svc(c).update(
        ports=[{"mode": "ingress", "host_ip": "0.0.0.0", "target": 9000, "published": "9000"}]  # noqa: S104
    ),
    "port_ipv6_all": lambda c: svc(c).update(
        ports=[{"mode": "ingress", "host_ip": "::", "target": 9000, "published": "9000"}]
    ),
    "port_no_host_ip": lambda c: svc(c).update(
        ports=[{"mode": "ingress", "target": 9000, "published": "9000"}]
    ),
    # image
    "image_without_digest": lambda c: svc(c).update(image="cgr.dev/chainguard/minio:latest"),
    "image_from_another_registry": lambda c: svc(c).update(image="evil.example/x" + DIGEST),
    "no_image": lambda c: svc(c).pop("image"),
    # health and limits
    "no_healthcheck": lambda c: svc(c).pop("healthcheck"),
    "healthcheck_disabled": lambda c: svc(c).update(healthcheck={"disable": True}),
    "healthcheck_none": lambda c: svc(c).update(healthcheck={"test": ["NONE"]}),
    "healthcheck_none_string": lambda c: svc(c).update(healthcheck={"test": "NONE"}),
    "no_memory_limit": lambda c: svc(c).pop("mem_limit"),
    "memory_limit_zero": lambda c: svc(c).update(mem_limit=0),
    "memory_limit_zero_string": lambda c: svc(c).update(mem_limit="0"),
    "memory_limit_too_big": lambda c: svc(c).update(mem_limit="2g"),
    "too_many_services": lambda c: c["services"].update(
        {f"s{i}": copy.deepcopy(svc(c)) for i in range(5)}
    ),
    # project, networks, top level
    "project_name_of_another_project": lambda c: c.update(name="wevit"),
    "no_project_name": lambda c: c.pop("name"),
    "edge_network": lambda c: c["networks"].update(edge={"name": "edge", "external": True}),
    "network_name_of_another_project": lambda c: c["networks"].update(
        default={"name": "unveilio_default"}
    ),
    "service_on_another_network": lambda c: svc(c).update(networks={"edge": None}),
    "top_level_secrets": lambda c: c.update(secrets={"s": {}}),
    "top_level_configs": lambda c: c.update(configs={"c": {}}),
    "top_level_extension": lambda c: c.update({"x-anything": {}}),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_policy_rejects(name: str) -> None:
    config = copy.deepcopy(good())
    MUTATIONS[name](config)
    assert policy.check(config), f"{name} was not rejected"


def test_policy_reports_all_violations() -> None:
    config = good()
    svc(config).update(privileged=True, image="minio:latest")
    assert len(policy.check(config)) >= 2


def test_policy_messages_never_contain_values() -> None:
    config = good()
    svc(config)["environment"]["MINIO_ROOT_PASSWORD"] = "SECRET-VALUE-XYZ"
    svc(config)["environment"]["POSTGRES_PASSWORD"] = "SECRET-VALUE-XYZ"
    svc(config)["user"] = "SECRET-VALUE-XYZ"
    assert policy.check(config)
    assert "SECRET-VALUE-XYZ" not in " ".join(policy.check(config))


@pytest.mark.parametrize("value", ["1g", "512m", "1073741824", 1073741824, "1024m"])
def test_policy_accepts_memory_limit_forms(value: object) -> None:
    config = good()
    svc(config)["mem_limit"] = value
    assert policy.check(config) == []


@pytest.mark.parametrize(
    "text",
    [
        "services:\n  a:\n    env_file: x.yml\n",
        'services:\n  a:\n    "env_file": /opt/stack/unveilio/.env\n',
        "services:\n  a:\n    'extends': {file: x.yml, service: b}\n",
        'include:\n  - "x.yml"\n',
        "services:\n  a:\n    environment:\n      X: ${POSTGRES_PASSWORD}\n",
        "services:\n  a:\n    user: ${U:-0}\n",
        "services:\n  a:\n    user: $U\n",
        "services:\n  a:\n    image: ${IMAGE}\n",
    ],
)
def test_policy_raw_check_rejects(text: str) -> None:
    assert policy.check_raw(text)


def test_policy_raw_check_accepts_the_allowed_variables_and_comments() -> None:
    text = (
        "# env_file: not a directive, a comment, and ${OTHER} too\n"
        "services:\n  a:\n    environment:\n"
        "      U: ${MINIO_ACCESS_KEY:?set}\n      P: ${MINIO_SECRET_KEY:?set}\n      Q: price $$5\n"
    )
    assert policy.check_raw(text) == []


def test_policy_env_mode_keeps_only_the_two_keys() -> None:
    lines, problems = policy.env_lines(
        {
            "MINIO_ACCESS_KEY": "exaktivabc",
            "MINIO_SECRET_KEY": "s3cretvalue1",
            "POSTGRES_PASSWORD": "x",
        }
    )
    assert problems == []
    assert lines == ["MINIO_ACCESS_KEY='exaktivabc'", "MINIO_SECRET_KEY='s3cretvalue1'"]


@pytest.mark.parametrize(
    "secrets",
    [
        {},
        {"MINIO_ACCESS_KEY": "exaktivabc"},
        {"MINIO_ACCESS_KEY": "ok-value", "MINIO_SECRET_KEY": "has'quote"},
        {"MINIO_ACCESS_KEY": "ok-value", "MINIO_SECRET_KEY": "has\nnewline"},
        {"MINIO_ACCESS_KEY": "ok-value", "MINIO_SECRET_KEY": "has $dollar"},
        {"MINIO_ACCESS_KEY": "ok-value", "MINIO_SECRET_KEY": 5},
    ],
)
def test_policy_env_mode_refuses_missing_or_unsafe_values(secrets: dict[str, Any]) -> None:
    lines, problems = policy.env_lines(secrets)
    assert problems and len(lines) < 2


def run_cli(*args: str, stdin: str) -> subprocess.CompletedProcess[str]:
    script = ROOT / "deploy/server/policy.py"
    return subprocess.run(  # noqa: S603
        ["python3", str(script), *args],  # noqa: S607
        input=stdin,
        text=True,
        capture_output=True,
    )


def test_policy_cli_exit_codes() -> None:
    assert run_cli(stdin=json.dumps(good())).returncode == 0
    bad = good()
    svc(bad)["privileged"] = True
    refused = run_cli(stdin=json.dumps(bad))
    assert refused.returncode == 1 and "privileged" in refused.stderr
    assert run_cli(stdin="not json").returncode == 1
    assert run_cli(stdin="").returncode == 1


def test_policy_cli_env_mode_writes_nothing_on_failure() -> None:
    result = run_cli("--env", stdin=json.dumps({"MINIO_ACCESS_KEY": "exaktivabc"}))
    assert result.returncode == 1 and result.stdout == ""


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("docker") is None, reason="needs the docker CLI with compose")
def test_policy_accepts_the_real_server_compose(tmp_path: Path) -> None:
    compose = ROOT / "deploy/server/docker-compose.yml"
    env = tmp_path / "env"
    env.write_text("MINIO_ACCESS_KEY='exaktivabc'\nMINIO_SECRET_KEY='s3cretvalue1'\n")
    out = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "docker",
            "compose",
            "-f",
            str(compose),
            "-p",
            "exaktiv",
            "--profile",
            "*",
            "--env-file",
            str(env),
            "config",
            "--format",
            "json",
        ],  # fmt: skip
        capture_output=True,
        text=True,
        check=True,
    )
    assert policy.check(json.loads(out.stdout)) == []
    assert policy.check_raw(compose.read_text()) == []
