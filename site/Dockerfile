# EXW2: the web image. Static site plus Caddy, behind the shared Caddy of the host. Build context is site/ (not the repo root):
#
#   python3 scripts/build_site.py && python3 scripts/render_caddyfile.py
#   docker build --platform linux/amd64 --build-arg GIT_SHA=$(git rev-parse HEAD) \
#     -f site/Dockerfile -t ghcr.io/vedm1/exaktiv/web:$(git rev-parse HEAD) site
#
# The base image is the one the unveilio landing image pins (index digest, resolved 2026-10-02).
FROM caddy:2-alpine@sha256:6aeddd44c3078b0f9a35206472a11420648a79c184603ef95957d0a20044cb2b
COPY dist /srv
COPY build/Caddyfile /etc/caddy/Caddyfile
COPY caddy/mode-staging.caddy caddy/mode-live.caddy /etc/caddy/
# EXW3: SITE_MODE=live starts only when the site was built with --launch (marker /srv/.launch-built).
COPY --chmod=0755 entrypoint.sh /usr/local/bin/site-entrypoint
# The official binary carries a file capability (bind to ports below 1024). With `cap_drop: [ALL]` the kernel then refuses to
# start it ("operation not permitted"). A copy has no file capability, and this site listens on 8080, so it needs none.
RUN cp /usr/bin/caddy /usr/local/bin/caddy
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.source="https://github.com/vedm1/exactiv" \
      org.opencontainers.image.revision="${GIT_SHA}"
USER 10001
ENTRYPOINT ["/usr/local/bin/site-entrypoint"]
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
