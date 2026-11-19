# EXW2: the site form image (web service, migrate and jobs all use it). Build context is the REPO ROOT, and the root
# .dockerignore is an allowlist:
#
#   docker build --platform linux/amd64 --build-arg GIT_SHA=$(git rev-parse HEAD) \
#     -f services/site_form/Dockerfile -t ghcr.io/vedm1/exaktiv/site-form:$(git rev-parse HEAD) .
#
# Base images are pinned by index digest (the same ones the unveilio api image pins, resolved 2026-10-02).
# No uv and no dev dependencies in the final image: the runtime calls the venv's uvicorn and alembic directly.
ARG PYTHON_IMAGE=python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016

# ---- uv: only the binary is taken from here -------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:0.12.7@sha256:95f2aa1fe59274951cfe9b0cbc7972e879ff1004bc8945d130a32eb0dbd85945 AS uv

# ---- builder: the locked production dependencies and the packages as wheels --------------------------------
FROM ${PYTHON_IMAGE} AS builder
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
COPY --from=uv /uv /usr/local/bin/uv
# The workspace lock needs every member's pyproject.toml. Only the site form and the core library are installed.
COPY pyproject.toml uv.lock ./
COPY libs/core ./libs/core
COPY services/api/pyproject.toml ./services/api/pyproject.toml
COPY services/worker/pyproject.toml ./services/worker/pyproject.toml
COPY model/pyproject.toml ./model/pyproject.toml
COPY services/site_form ./services/site_form
RUN uv sync --locked --no-dev --no-editable --package exaktiv-site-form

# ---- doppler: pinned by the SHA-256 of its package; curl never reaches the final image -------------------
# Doppler gets DOPPLER_TOKEN and the form secrets, so it is pinned by content: the package is unpacked only if its
# SHA-256 equals the line for that file in services/site_form/doppler-cli.sha256. To move to a new version, change
# DOPPLER_VERSION here and replace both lines of the pin file.
FROM debian:12-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251 AS doppler
ARG DOPPLER_VERSION=3.76.6
COPY services/site_form/doppler-cli.sha256 /tmp/doppler-cli.sha256
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && deb="doppler_${DOPPLER_VERSION}_linux_$(dpkg --print-architecture).deb" \
 && curl -fsSL --retry 3 --tlsv1.2 --proto "=https" -o "/tmp/${deb}" \
      "https://packages.doppler.com/public/cli/deb/debian/pool/any-version/main/d/do/doppler_${DOPPLER_VERSION}/${deb}" \
 && awk -v f="${deb}" '$2 == f' /tmp/doppler-cli.sha256 | (cd /tmp && sha256sum -c -) \
 && dpkg-deb -x "/tmp/${deb}" / \
 && rm -rf /var/lib/apt/lists/* "/tmp/${deb}" /tmp/doppler-cli.sha256

# ---- runtime: the same base as the builder, so the venv's interpreter links resolve -----------------------
FROM ${PYTHON_IMAGE} AS runtime
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.source="https://github.com/vedm1/exactiv" \
      org.opencontainers.image.revision="${GIT_SHA}"
RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid app --create-home --home-dir /home/app --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=doppler /usr/bin/doppler /usr/local/bin/doppler
COPY --from=builder /app/.venv /app/.venv
# `alembic -c alembic.ini upgrade head` runs from /app (the migrate service).
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER app
EXPOSE 8000
# --no-fallback: Doppler writes no secrets snapshot into the container (G9). Without a reachable Doppler the process
# exits and the container never serves. --no-access-log: the access log would hold the client address (G11).
CMD ["doppler", "run", "--no-fallback", "--", "uvicorn", "exaktiv_site_form.main:create_default_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
