#!/usr/bin/env bash
# EXW2: properties of the web image that matter. Usage: site/test_image.sh <image>
set -euo pipefail
img="${1:?usage: test_image.sh <image>}"
fail() { echo "FAIL: $*" >&2; exit 1; }
user="$(docker image inspect --format '{{.Config.User}}' "$img")"
[[ "$user" == "10001" ]] || fail "the image runs as '$user', not 10001"
rev="$(docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$img")"
[[ "$rev" =~ ^[0-9a-f]{40}$ ]] || fail "the revision label is '$rev', not a commit SHA"
docker image inspect --format '{{json .Config.Healthcheck}}' "$img" | grep -q healthz || fail "no healthcheck on /healthz"
docker run --rm --entrypoint sh "$img" -c 'test -f /srv/index.html && test -f /etc/caddy/mode-staging.caddy && test -f /etc/caddy/mode-live.caddy' \
  || fail "site files or mode files missing"
docker run --rm --entrypoint sh "$img" -c 'test -z "$(ls -A /srv /etc/caddy | grep -E "^(\.env|id_|.*\.pem)")"' \
  || fail "a secret-like file is inside the image"
docker run --rm -e SITE_MODE=staging -e STAGING_BASIC_AUTH_HASH='$2a$14$invalidinvalidinvalidinvalidinvalidinvalidinvalidinvalidin' \
  "$img" caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1 || fail "caddy validate failed in staging mode"
docker run --rm -e SITE_MODE=live --entrypoint caddy "$img" validate --config /etc/caddy/Caddyfile >/dev/null 2>&1 \
  || fail "caddy validate failed in live mode"
# EXW3: live mode starts only with a launch build (the marker file). A staging build must refuse it.
if docker run --rm --entrypoint sh "$img" -c 'test -f /srv/.launch-built'; then
  docker run --rm -e SITE_MODE=live "$img" true >/dev/null 2>&1 || fail "a launch build refused SITE_MODE=live"
else
  if docker run --rm -e SITE_MODE=live "$img" true >/dev/null 2>&1; then fail "a staging build accepted SITE_MODE=live"; fi
fi
echo "ok: $img"
