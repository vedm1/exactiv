#!/bin/sh
# EXW3: the live mode (no password wall, indexable) is allowed only for a launch build of the site.
# build_site.py --launch writes /srv/.launch-built after every launch check passed. A staging build has no such file,
# so SITE_MODE=live on the host cannot make it public by mistake.
set -eu
if [ "${SITE_MODE:-}" = "live" ] && [ ! -f "${LAUNCH_MARKER:-/srv/.launch-built}" ]; then
  echo "SITE_MODE=live needs a launch build of the site (no .launch-built marker). Refusing to start." >&2
  exit 1
fi
exec "$@"
