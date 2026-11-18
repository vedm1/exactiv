#!/usr/bin/env python3
"""Compose policy for deploy-infra (EXK0b). Standard library only.

An ALLOWLIST: a key that is not listed is refused, so a new compose feature cannot slip through.

Usage:
  python3 policy.py --raw docker-compose.yml        text checks on the file as written
  python3 policy.py --env < doppler.json            write the two allowed secrets as .env lines
  docker compose ... config --format json | python3 policy.py     structure check

The structure check runs on the INTERPOLATED config (final env file, all profiles), so what is
checked is what runs. Exit 0 when the input passes; exit 1 with one line per problem on stderr.
Messages name keys and services only, never values (they can hold secrets).
The policy is installed by root. A deployed repository never changes it.
"""

import json
import re
import sys
from typing import Any

PROJECT = "exaktiv"
MAX_SERVICES = 4
MAX_MEM_BYTES = 1024**3  # 1 GiB for each service
REGISTRIES = ("cgr.dev/chainguard/",)
TOP_KEYS = {"name", "services", "volumes", "networks"}
SERVICE_KEYS = {
    "image", "command", "environment", "ports", "volumes", "healthcheck",
    "mem_limit", "restart", "networks", "user",
}  # fmt: skip
PORT_KEYS = {"mode", "host_ip", "target", "published", "protocol"}
MOUNT_KEYS = {"type", "source", "target", "volume"}
ENV_KEYS = {"MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD"}  # environment a service may carry
VARIABLES = ("MINIO_ACCESS_KEY", "MINIO_SECRET_KEY")  # the only ${...} references allowed
SECRET_VALUE = re.compile(r"^[A-Za-z0-9._~+/=-]{3,128}$")
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
USER = re.compile(r"^[1-9][0-9]*(:[1-9][0-9]*)?$")
MEM = re.compile(r"^(\d+)([bkmg]?)b?$", re.IGNORECASE)
UNITS = {"": 1, "b": 1, "k": 1024, "m": 1024**2, "g": 1024**3}
DIRECTIVE = re.compile(r"""(^|[^A-Za-z_])["']?(env_file|extends|include)["']?\s*:""")
VARIABLE = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)|([A-Za-z_][A-Za-z0-9_]*))")


def parse_bytes(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    match = MEM.match(str(value).strip())
    return int(match.group(1)) * UNITS[match.group(2).lower()] if match else None


def check_raw(text: str) -> list[str]:
    """Text checks. `docker compose config` resolves env_file, extends and include away."""
    stripped = re.sub(r"(^|\s)#.*", "", text, flags=re.MULTILINE).replace("$$", "")
    out: list[str] = []
    if DIRECTIVE.search(stripped):
        out.append("env_file, extends and include are not allowed")
    for match in VARIABLE.finditer(stripped):
        name = match.group(1) or match.group(2)
        if name not in VARIABLES:
            out.append(f"variable {name} may not be used (allowed: {', '.join(VARIABLES)})")
    return out


def _set(d: dict[str, Any]) -> list[str]:
    """Keys that carry a value. `docker compose config` prints some unset keys as null or {}."""
    return [k for k, v in d.items() if v is not None and v != {} and v != []]


def _unknown(keys: Any, allowed: set[str]) -> list[str]:
    return sorted(set(keys) - allowed)


def _check_named(kind: str, items: dict[str, Any], only: set[str] | None) -> list[str]:
    out: list[str] = []
    for name, body in items.items():
        if only is not None and name not in only:
            out.append(f"{kind} {name}: not allowed")
        extra = _unknown(_set(body or {}), {"name"})
        if extra:
            out.append(f"{kind} {name}: {', '.join(extra)} not allowed")
        if not str((body or {}).get("name", "")).startswith(f"{PROJECT}_"):
            out.append(f"{kind} {name}: the name must start with {PROJECT}_")
    return out


def check(config: dict[str, Any]) -> list[str]:
    out = [f"top-level {k} is not allowed" for k in _unknown(config.keys(), TOP_KEYS)]
    if config.get("name") != PROJECT:
        out.append(f"the project name must be {PROJECT}")
    volumes = config.get("volumes") or {}
    out += _check_named("volume", volumes, None)
    out += _check_named("network", config.get("networks") or {}, {"default"})

    services = config.get("services") or {}
    if len(services) > MAX_SERVICES:
        out.append(f"more than {MAX_SERVICES} services")
    for sname, s in services.items():

        def bad(msg: str, sname: str = sname) -> None:
            out.append(f"{sname}: {msg}")

        for key in _unknown(_set(s), SERVICE_KEYS):
            bad(f"{key} is not allowed")
        image = str(s.get("image") or "")
        if not image:
            bad("no image")
        else:
            if not DIGEST.search(image):
                bad("the image is not pinned by digest (@sha256:...)")
            if not image.startswith(REGISTRIES):
                bad(f"the image is outside {', '.join(REGISTRIES)}")
        if not USER.match(str(s.get("user", ""))):
            bad("user is required and must be a numeric non-root id")
        for key in _unknown((s.get("environment") or {}).keys(), ENV_KEYS):
            bad(f"environment {key} is not allowed")
        for vol in s.get("volumes") or []:
            if not isinstance(vol, dict) or _unknown(vol.keys(), MOUNT_KEYS):
                bad("mounts must be plain named volumes")
            elif (
                vol.get("type") != "volume" or vol.get("source") not in volumes or vol.get("volume")
            ):
                bad("mounts must be plain named volumes of this project")
        for port in s.get("ports") or []:
            if not isinstance(port, dict) or _unknown(port.keys(), PORT_KEYS):
                bad("ports must use the long form")
            elif port.get("host_ip") != "127.0.0.1":
                bad("ports must be published on 127.0.0.1 only")
        hc = s.get("healthcheck") or {}
        test = hc.get("test")
        first = test[0] if isinstance(test, list) and test else test
        if not test or hc.get("disable") or str(first).upper() == "NONE":
            bad("a healthcheck is required")
        mem = parse_bytes(s["mem_limit"]) if "mem_limit" in s else None
        if mem is None or mem <= 0:
            bad("mem_limit is required and must be above 0")
        elif mem > MAX_MEM_BYTES:
            bad("mem_limit is above 1 GiB")
        nets = s.get("networks") or {}
        if not isinstance(nets, dict) or _unknown(nets.keys(), {"default"}):
            bad("only the default network is allowed")
    return out


def env_lines(secrets: dict[str, Any]) -> tuple[list[str], list[str]]:
    """The two allowed secrets as single-quoted .env lines. Everything else in Doppler is dropped."""
    lines: list[str] = []
    problems: list[str] = []
    for name in VARIABLES:
        value = secrets.get(name)
        if not isinstance(value, str) or not SECRET_VALUE.match(value):
            problems.append(f"{name} is missing or has characters that are not allowed")
        else:
            lines.append(f"{name}='{value}'")
    return lines, problems


def main(argv: list[str]) -> int:
    if argv[:1] == ["--raw"]:
        with open(argv[1], encoding="utf-8") as fh:
            problems = check_raw(fh.read())
    elif argv[:1] == ["--env"]:
        try:
            data = json.load(sys.stdin)
        except ValueError:
            data = None
        lines, problems = env_lines(data) if isinstance(data, dict) else ([], ["not a JSON object"])
        if not problems:
            sys.stdout.write("\n".join(lines) + "\n")
    else:
        try:
            problems = check(json.load(sys.stdin))
        except ValueError:
            problems = ["the compose config is not valid JSON"]
    for line in problems:
        print(f"policy: {line}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
