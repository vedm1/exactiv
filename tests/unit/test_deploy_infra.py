"""EXK0b: deploy-infra, run with fake git, docker, curl and flock. Nothing real is touched."""

import copy
import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tests.unit.test_deploy_policy import good

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "deploy/server/deploy-infra"
POLICY = ROOT / "deploy/server/policy.py"
SHA = "a" * 40
OLD_SHA = "b" * 40
TOKEN_SENTINEL = "dp.st.sentinel-token-123"
SECRET_SENTINEL = "minio-secret-sentinel-456"
OTHER_SENTINEL = "neon-password-sentinel-789"
OLD_ENV = "MINIO_ACCESS_KEY='oldkey123'\nMINIO_SECRET_KEY='oldsecret123'\n"
OLD_COMPOSE = "name: exaktiv\n# previous\n"
NEW_COMPOSE = "name: exaktiv\nservices:\n  minio:\n    image: x\n"

FAKE_GIT = """#!/usr/bin/env bash
echo "git $*" >> "$FAKE_LOG"
case " $* " in
  *" fetch "*) exit 0 ;;
  *" cat-file "*) exit 0 ;;
  *"--is-ancestor $FAKE_OLD_SHA "*) exit "${FAKE_STALE_EXIT:-0}" ;;
  *" merge-base "*) exit "${FAKE_ANCESTOR_EXIT:-0}" ;;
  *" show "*) cat "$FAKE_COMPOSE_FILE" ;;
  *" init "*) exit 0 ;;
esac
"""
FAKE_DOCKER = """#!/usr/bin/env bash
echo "docker $* [COMPOSE_FILE=${COMPOSE_FILE:-} DOCKER_HOST=${DOCKER_HOST:-}]" >> "$FAKE_LOG"
if [[ " $* " == *" config "* ]]; then
  [[ "${FAKE_CONFIG_FAIL:-0}" == "1" ]] && exit 1
  cat "$FAKE_CONFIG_JSON"; exit 0
fi
if [[ " $* " == *" pull"* ]]; then
  [[ "${FAKE_PULL_FAIL:-0}" == "1" ]] && { echo "pull failed" >&2; exit 1; }
  exit 0
fi
if [[ " $* " == *" up "* ]]; then
  n=$(grep -c "^docker .* up " "$FAKE_LOG")
  if [[ "${FAKE_UP_FAIL:-0}" == "1" && "$n" == "1" ]]; then
    echo "health check failed" >&2; exit 1
  fi
fi
exit 0
"""
FAKE_CURL = """#!/usr/bin/env bash
echo "curl $*" >> "$FAKE_LOG"
cat > /dev/null
[[ "${FAKE_CURL_FAIL:-0}" == "1" ]] && exit 22
if [[ "${FAKE_NO_SECRET:-0}" == "1" ]]; then echo '{"MINIO_ACCESS_KEY":"exaktivtest"}'; exit 0; fi
printf '{"MINIO_ACCESS_KEY":"exaktivtest","MINIO_SECRET_KEY":"%s","POSTGRES_PASSWORD":"%s"}' \\
  "$FAKE_SECRET" "$FAKE_OTHER"
"""
FAKE_FLOCK = "#!/usr/bin/env bash\nexit 0\n"
CONF = (
    "REPO=git@github.com:example/exaktiv.git\nBRANCH=main\n"
    "SSH_KEY=/home/x/.ssh/key\nKNOWN_HOSTS=/home/x/.ssh/known\n"
)


@dataclass
class Run:
    code: int
    out: str
    log: str
    project: Path


def run(
    tmp: Path,
    sha: str = SHA,
    *,
    config: dict[str, object] | None = None,
    compose_text: str = NEW_COMPOSE,
    conf: str = CONF,
    token: str = TOKEN_SENTINEL,
    live: bool = False,
    **extra: str,
) -> Run:
    bindir = tmp / "bin"
    bindir.mkdir()
    for name, body in (
        ("git", FAKE_GIT),
        ("docker", FAKE_DOCKER),
        ("curl", FAKE_CURL),
        ("flock", FAKE_FLOCK),
    ):
        path = bindir / name
        path.write_text(body)
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
    stack = tmp / "stack"
    project = stack / "exaktiv"
    project.mkdir(parents=True)
    (project / "doppler.token").write_text(token)
    if live:
        (project / ".current").write_text(OLD_SHA + "\n")
        (project / "docker-compose.yml").write_text(OLD_COMPOSE)
        (project / ".env").write_text(OLD_ENV)
    conf_file = tmp / "deploy.conf"
    conf_file.write_text(conf)
    compose_file = tmp / "compose.yml"
    compose_file.write_text(compose_text)
    config_json = tmp / "config.json"
    config_json.write_text(json.dumps(config if config is not None else good()))
    log = tmp / "calls.log"
    log.write_text("")
    env = {
        **os.environ,
        "PATH": f"{bindir}:{os.environ['PATH']}",
        "STACK_ROOT": str(stack),
        "DEPLOY_CONF": str(conf_file),
        "POLICY_PY": str(POLICY),
        "FAKE_LOG": str(log),
        "FAKE_COMPOSE_FILE": str(compose_file),
        "FAKE_CONFIG_JSON": str(config_json),
        "FAKE_SECRET": SECRET_SENTINEL,
        "FAKE_OTHER": OTHER_SENTINEL,
        "FAKE_OLD_SHA": OLD_SHA,
        "SSH_ORIGINAL_COMMAND": sha,
        "COMPOSE_FILE": "/evil/compose.yml",
        "DOCKER_HOST": "tcp://evil:2375",
        **extra,
    }
    proc = subprocess.run(  # noqa: S603
        ["bash", str(SCRIPT)],  # noqa: S607
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return Run(proc.returncode, proc.stdout + proc.stderr, log.read_text(), project)


def docker_calls(log: str) -> list[str]:
    return [c for c in log.splitlines() if c.startswith("docker ")]


@pytest.mark.parametrize(
    "bad", ["", "abc", "A" * 40, "a" * 39, "a" * 41, '"; rm -rf /', f"{SHA}; id", f"{SHA}\n{SHA}"]
)
def test_deploy_infra_rejects_non_sha_input(tmp_path: Path, bad: str) -> None:
    result = run(tmp_path, bad)
    assert result.code == 2
    assert result.log == ""


def test_deploy_infra_happy_path(tmp_path: Path) -> None:
    result = run(tmp_path)
    assert result.code == 0, result.out
    assert f"{SHA} is live" in result.out
    assert (result.project / ".current").read_text().strip() == SHA
    env_file = result.project / ".env"
    assert env_file.read_text() == (
        f"MINIO_ACCESS_KEY='exaktivtest'\nMINIO_SECRET_KEY='{SECRET_SENTINEL}'\n"
    )
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600
    assert (result.project / "docker-compose.yml").read_text() == NEW_COMPOSE
    calls = result.log.splitlines()
    pull = next(i for i, c in enumerate(calls) if " pull" in c)
    up = next(i for i, c in enumerate(calls) if " up " in c)
    assert pull < up


def test_deploy_infra_only_the_two_secrets_reach_the_env_file(tmp_path: Path) -> None:
    result = run(tmp_path)
    assert OTHER_SENTINEL not in (result.project / ".env").read_text()


def test_deploy_infra_pins_project_and_profiles_and_clears_caller_env(tmp_path: Path) -> None:
    result = run(tmp_path)
    calls = docker_calls(result.log)
    assert calls
    for call in calls:
        assert " -p exaktiv " in call and "--profile *" in call and "--env-file " in call
        assert "COMPOSE_FILE= DOCKER_HOST=" in call, "caller env must not reach docker"
    assert "docker compose -f docker-compose.yml" in calls[-1]


def test_deploy_infra_never_prints_secrets(tmp_path: Path) -> None:
    result = run(tmp_path)
    for sentinel in (TOKEN_SENTINEL, SECRET_SENTINEL, OTHER_SENTINEL):
        assert sentinel not in result.out
        assert sentinel not in result.log, "a secret must not appear in any command line"


def test_deploy_infra_policy_violation_stops_before_pull(tmp_path: Path) -> None:
    bad = copy.deepcopy(good())
    bad["services"]["minio"]["privileged"] = True
    result = run(tmp_path, config=bad)
    assert result.code == 1
    assert "privileged" in result.out
    assert " pull" not in result.log and " up " not in result.log
    assert not (result.project / ".env").exists()
    assert not (result.project / ".current").exists()


@pytest.mark.parametrize(
    "text",
    [
        'services:\n  a:\n    "env_file": /opt/stack/unveilio/.env\n',
        "services:\n  a:\n    environment:\n      X: ${POSTGRES_PASSWORD}\n",
    ],
)
def test_deploy_infra_raw_violation_stops_before_any_docker_call(tmp_path: Path, text: str) -> None:
    result = run(tmp_path, compose_text=text)
    assert result.code == 1
    assert not docker_calls(result.log)


def test_deploy_infra_refuses_a_sha_outside_main(tmp_path: Path) -> None:
    result = run(tmp_path, FAKE_ANCESTOR_EXIT="1")
    assert result.code == 1 and "history" in result.out
    assert not docker_calls(result.log)


def test_deploy_infra_refuses_a_sha_older_than_the_live_one(tmp_path: Path) -> None:
    result = run(tmp_path, live=True, FAKE_STALE_EXIT="1")
    assert result.code == 1 and "older than the live commit" in result.out
    assert not docker_calls(result.log)
    assert (result.project / ".current").read_text().strip() == OLD_SHA


def test_deploy_infra_rolls_back_when_health_check_fails(tmp_path: Path) -> None:
    result = run(tmp_path, live=True, FAKE_UP_FAIL="1")
    assert result.code == 1
    assert result.log.count(" up ") == 2
    assert (result.project / ".current").read_text().strip() == OLD_SHA
    assert (result.project / "docker-compose.yml").read_text() == OLD_COMPOSE
    assert (result.project / ".env").read_text() == OLD_ENV
    assert f"rolled back to {OLD_SHA}" in result.out


def test_deploy_infra_first_deploy_failure_has_nothing_to_roll_back_to(tmp_path: Path) -> None:
    result = run(tmp_path, FAKE_UP_FAIL="1")
    assert result.code == 1
    assert result.log.count(" up ") == 1
    assert not (result.project / ".current").exists()


def test_deploy_infra_pull_failure_changes_nothing_live(tmp_path: Path) -> None:
    result = run(tmp_path, live=True, FAKE_PULL_FAIL="1")
    assert result.code == 1
    assert (result.project / "docker-compose.yml").read_text() == OLD_COMPOSE
    assert (result.project / ".env").read_text() == OLD_ENV
    assert " up " not in result.log


def test_deploy_infra_docker_config_failure_is_a_refusal(tmp_path: Path) -> None:
    result = run(tmp_path, live=True, FAKE_CONFIG_FAIL="1")
    assert result.code == 1
    assert " pull" not in result.log and " up " not in result.log
    assert (result.project / ".env").read_text() == OLD_ENV


@pytest.mark.parametrize("extra", [{"FAKE_CURL_FAIL": "1"}, {"FAKE_NO_SECRET": "1"}])
def test_deploy_infra_secret_failure_keeps_the_live_env(
    tmp_path: Path, extra: dict[str, Any]
) -> None:
    result = run(tmp_path, live=True, **extra)
    assert result.code == 1
    assert (result.project / ".env").read_text() == OLD_ENV
    assert not docker_calls(result.log)


@pytest.mark.parametrize(
    "conf",
    [
        CONF.replace("git@github.com:example/exaktiv.git", "--upload-pack=touch /tmp/x"),
        CONF.replace("git@github.com:example/exaktiv.git", "https://evil.example/x.git"),
        CONF.replace("BRANCH=main", "BRANCH=--exec=x"),
        CONF.replace("/home/x/.ssh/key", "relative/key"),
        CONF + "EXTRA=1\n",
    ],
)
def test_deploy_infra_rejects_a_bad_deploy_conf(tmp_path: Path, conf: str) -> None:
    result = run(tmp_path, conf=conf)
    assert result.code == 1
    assert "git fetch" not in result.log


def test_deploy_infra_rejects_a_token_file_with_odd_characters(tmp_path: Path) -> None:
    result = run(tmp_path, token='x"\nuser = "evil')
    assert result.code == 1
    assert "curl" not in result.log
