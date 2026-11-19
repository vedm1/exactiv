#!/usr/bin/env bash
# EXW2: properties of the site form image that matter. Usage: services/site_form/test_image.sh <image>
set -euo pipefail
img="${1:?usage: test_image.sh <image>}"
fail() { echo "FAIL: $*" >&2; exit 1; }
[[ "$(docker image inspect --format '{{.Config.User}}' "$img")" == "app" ]] || fail "the image does not run as the user app"
rev="$(docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$img")"
[[ "$rev" =~ ^[0-9a-f]{40}$ ]] || fail "the revision label is '$rev', not a commit SHA"
docker image inspect --format '{{json .Config.Cmd}}' "$img" | grep -q -- '--no-access-log' || fail "the command lacks --no-access-log"
docker run --rm --entrypoint sh "$img" -c 'test ! -e /app/.env && test -f /app/alembic.ini && test -d /app/migrations' \
  || fail ".env present or alembic files missing"
docker run --rm --entrypoint doppler "$img" --version >/dev/null || fail "the doppler CLI is missing"
docker run --rm --entrypoint python "$img" -c 'import exaktiv_site_form.main, exaktiv_core.db, alembic' \
  || fail "the application does not import"
# Fail closed: with no Doppler token the container must exit non-zero and serve nothing.
if docker run --rm "$img" >/dev/null 2>&1; then fail "the container started without a Doppler token"; fi
echo "ok: $img"
