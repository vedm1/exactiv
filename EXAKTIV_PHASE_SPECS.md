# EXAKTIV_PHASE_SPECS.md — Phase Specs

Specs are written just in time, at the start of each phase build session. EXK0 and EXK1 are full specs. Later phases are stubs.
Requirement IDs (FR-…, G…, A-G…, B-G…) refer to `docs/prd/`.

## Shared: repository layout

```
exaktiv/
  services/api/        FastAPI app (package exaktiv_api)
  services/worker/     Temporal workers and workflows (package exaktiv_worker)
  model/               gateway client, router, training (package exaktiv_model)
  libs/core/           shared types: value record, tenant, events (package exaktiv_core)
  config/              versioned schemas, rules, value lists, routes (YAML, each file has `version:`)
  ui/                  React + TypeScript (pnpm), tokens in ui/src/tokens/
  tests/fixtures/      synthetic/public fixtures only; each has a SOURCE.md note (G8)
  deploy/              docker-compose.yml, server configs
  docs/prd/            PRD files
```

One uv workspace for all Python packages. One pnpm workspace for `ui/`.

## Shared: value record (FR-EXT-3)

Every extracted value uses one type in `libs/core`. Fields: `tenant_id`, `job_id`, `field_id`, `value`, `unit` (nullable), `source_file_id`, `page`, `location` (bbox `[x0,y0,x1,y1]` in page pixels, or text span `[start,end]`), `model_id`, `model_version`, `prompt_version`, `raw_output`, `confidence` (nullable until EXK5), `status` (`candidate` | `in_review` | `accepted` | `not_found` | `not_present` | `rejected`), `created_at`. EXK3 defines the final schema.

## Shared: design system

Reviewer UI, HTML reports, PDFs and the website use the Exaktiv brand package in `brand/` (read `brand/README.md` first). Colours by job: Paper ground, Ink text, Cobalt source, Vermilion act, Marker evidence. Type: Young Serif headings, Instrument Sans body and UI, Gelasio italic citations. No monospace. Components read role tokens (`--ex-*`) only. `brand/tokens/tokens.css` is the source; `ui/src/tokens/` holds synced copies (EXD2). The reviewer UI defaults to dark through `data-theme`; the website and reports default to light. The Personal Design System is retired.

---

## EXK0 — Foundation

**Objective**: A monorepo where the local stack starts with one command and CI runs every check on one passing smoke test.

**Prerequisites**: None.

**In scope**:
- Repository layout above, `pyproject.toml` (uv workspace), `ui/package.json` (pnpm, Vite, React, TypeScript strict).
- `deploy/docker-compose.yml`: Postgres 16, MinIO, Temporal (auto-setup with the Postgres backend), Temporal UI. Pinned image tags or digests.
- `.env.example` with names only, no values. `.gitignore` for `.env`.
- GitHub Actions: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` (strict), `uv run pytest`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, gitleaks secret scan, licence check script (fails on a dependency licence outside an allow list).
- Pre-commit hooks: ruff, gitleaks, fixture source-note check (G8).
- `LICENCES.md` (models and datasets; empty tables with headers).
- Smoke test: a Temporal workflow `SmokeWorkflow` that writes one row to Postgres and one object to MinIO, and an API endpoint `GET /health` that reports Postgres, MinIO and Temporal status.
- Measure the RAM of the full stack with `docker stats` and record it (input for the hosting open items).

**Out of scope for EXK0**: Any cloud server (EXK0b, EXK0c). Database schema for tenants and jobs (EXK1). Model calls.

**Tests**:
- `test_health` — `/health` returns 200 and three `ok` statuses with the compose stack up.
- `test_smoke_workflow` — the workflow completes; the row and the object exist.
- CI fails when a test file contains a fake AWS-style key (planted in a CI-only check).
- Fixture check fails when a file in `tests/fixtures/` has no `SOURCE.md` entry.

**Gating check**: Green CI on the first PR. `docker compose up -d && uv run pytest` passes on a clean clone.

### EXK0 detailed implementation spec (approved 4 Nov 2026)

**Decisions**: rename `master` to `main`. The founder creates the GitHub remote. Licence allow list: MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC, PSF-2.0, MPL-2.0. The smoke table `smoke_runs` is throwaway; EXK1 adds Alembic and drops it. Integration tests carry the marker `integration` and need the compose stack up.

**Probes first** (record results in Implementation notes): P1 `temporalio/auto-setup` works with the Postgres backend (else `temporalio/server` plus an admin-tools setup container). P2 resolve each image tag to a digest. P3 licence tools report no UNKNOWN. P4 `docker stats --no-stream` RAM after the smoke test.

**Layout**: `libs/core/exaktiv_core` (settings, health types), `services/api/exaktiv_api` (FastAPI, `/health`), `services/worker/exaktiv_worker` (worker, `SmokeWorkflow`), `model/exaktiv_model` (placeholder), `config/`, `ui/` (Vite, React, strict TS, `src/tokens/`), `tests/{fixtures,integration,guardrails}`, `scripts/{check_licences,check_fixture_sources}.py`, `deploy/docker-compose.yml`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `.gitleaks.toml`, `.env.example`, `.gitignore`, `LICENCES.md`, `pnpm-workspace.yaml`.

**Types**: `Settings` (pydantic-settings, env only; secret fields `SecretStr`): `POSTGRES_{HOST,PORT,DB,USER,PASSWORD}`, `MINIO_{ENDPOINT,ACCESS_KEY,SECRET_KEY,BUCKET}`, `TEMPORAL_{ADDRESS,NAMESPACE,TASK_QUEUE}`. `ComponentStatus = Literal["ok","down"]`. `HealthReport`: `postgres`, `minio`, `temporal`, `detail: dict[str,str]` (exception class name only).

**`GET /health`**: 2 s timeout per check (Postgres `SELECT 1`; MinIO `head_bucket`, create bucket if missing; Temporal `describe_namespace`). All ok → 200. Any down → 503, same body shape. No host name or secret in the body.

**`SmokeWorkflow.run(run_id) -> SmokeResult(run_id,row_written,object_key)`**: activity `write_row` (create `smoke_runs(id text PK, created_at timestamptz default now())` if absent; insert with `ON CONFLICT DO NOTHING`), then activity `write_object` (key `smoke/{run_id}.txt`). Task queue `exaktiv-smoke`. The test starts a worker in-process.

**Compose**: postgres 16 (databases `exaktiv` and `temporal`, init script, healthcheck), minio (ports 9000/9001, healthcheck), temporal (Postgres backend), temporal-ui (8233). Tag plus digest pinned. Ports bind to `127.0.0.1`. Credentials from `${VAR}`, no defaults.

**Checks**: ruff (line length 100), mypy strict, eslint, `tsc --noEmit`, vitest. `check_licences.py` (pip-licenses JSON + license-checker for the UI; exceptions in `config/licence_exceptions.yaml` with `version:`). `check_fixture_sources.py` (G8). gitleaks in CI and pre-commit. CI jobs: `python`, `ui`, `secrets`, `integration` (`docker compose up -d --wait`).

**Tests**: `test_health`; `test_health_reports_down` (503, no host or password in body); `test_smoke_workflow`; `test_smoke_workflow_retry_is_safe`; `test_g9_planted_secret_fails_scan` (key built at run time from two parts); `test_g9_env_example_has_no_values`; `test_g9_gitignore_covers_env`; `test_g9_settings_hide_secrets`; `test_g8_fixture_without_source_fails`; `test_g12_disallowed_licence_fails`; `test_g12_licences_md_has_headers`; vitest `App.test.tsx`.

**Close-out**: clean-clone gate check; record RAM; update `PHASES.md`, this file, the build plan open item "Measure stack RAM"; regenerate the dashboard. No independent review needed (EXK0 is not on the list).

### EXK0 Implementation notes (4 Nov 2026)

- **P1 confirmed**: `temporalio/auto-setup:1.25.0` works with the Postgres backend (`DB=postgres12`). It creates its own databases, so no Postgres init script exists.
- **P2 done**: digests pinned for postgres 16.4, temporal auto-setup 1.25.0, temporal-ui 2.31.2 and MinIO. **The official MinIO image is no longer public** (Docker Hub: none; `quay.io/minio/minio`: 401 for every tag). The compose file uses `cgr.dev/chainguard/minio:latest@sha256:3c60a2a8…` (MinIO RELEASE.2026-10-23, chosen by the founder). The digest pins it; upgrade only by a reviewed digest change. Healthcheck `mc ready local` works in this image. EXK0b must re-check the image source and its licence terms (AGPL-3.0 for MinIO itself) before a hosted deployment.
- **P3 confirmed**: licence tools report all packages. Python needed alias entries (MPL, "3-Clause BSD"). Workspace packages are skipped by name prefix. The UI allow list also has MIT-0, 0BSD, BlueOak-1.0.0, CC0-1.0 and CC-BY-4.0 (the `caniuse-lite` data package). This is wider than the agreed Python list.
- **Host port**: a host Postgres already uses 5432 on the dev machine. The stack uses host port **5442**.
- **Driver**: `asyncpg` (Apache-2.0) replaces psycopg, because psycopg is LGPL-3.0 and not on the allow list.
- **UI**: TypeScript is pinned to 6.x. `typescript-eslint` does not support 7.x yet.
- **Temporal sandbox**: activity-only imports (asyncpg, boto3) need `workflow.unsafe.imports_passed_through()` in the workflow module.
- **Tooling trap**: `ruff format .` changes `.claude/phase-dashboard/build_dashboard.py`. `pyproject.toml` now has `extend-exclude` and `force-exclude` for `.claude`.
- **RAM (P4)**: idle, with the test run done: postgres 82 MiB, temporal 81 MiB, minio 58 MiB, temporal-ui 10 MiB. Total about 231 MiB. The API and a worker process add more (not measured as separate processes yet). A 4 GB server looks enough for the stack; measure under load in EXK0b.
- **Not done in EXK0**: the first CI run (no GitHub remote yet); `pre-commit install` is the developer's one-time step. UI licence list is wider than the Python list (MIT-0, 0BSD, BlueOak-1.0.0, CC0-1.0, CC-BY-4.0).

---

## EXK1 — Ingestion, storage, event log

**Objective**: Accept files into a tenant's job, store originals unchanged with a hash, split them into normalised pages, and log every state change in an append-only event log.

**Prerequisites**: EXK0 ✅.

**In scope**:
- Tables: `tenants` (id, name, region `IN`|`EU`, file size limit default 50 MB), `jobs` (id, tenant_id, product `claims`|`product_data`, status, created_at), `files` (id, tenant_id, job_id, sha256, mime, size, uploader, uploaded_at, object_key), `pages` (id, file_id, page_no, original_key, normalised_key, width, height), `events` (id, tenant_id, job_id, type, payload JSONB, created_at).
- Migration tool: Alembic. First migration creates the tables above.
- `events` is append-only: a Postgres trigger rejects UPDATE and DELETE.
- File types: PDF (scanned and digital), JPEG, PNG, HEIC, TIFF, CSV, XLSX, BMEcat XML (FR-ING-1). Page split for PDF and image types only; CSV, XLSX and XML are stored as one file with no pages.
- Normalisation: deskew, rotate, contrast. Keep the original object unchanged (FR-ING-3).
- Hash check on every read of an original.
- Temporal workflow `IngestFileWorkflow`: store → hash → split → normalise → event per step.
- Internal endpoints (no public auth yet; EXK11 adds keys): `POST /jobs`, `POST /jobs/{id}/files`, `GET /jobs/{id}`.
- Every query filters on `tenant_id` (G6).

**Out of scope for EXK1**: Classification and extraction (EXK3+). Identifier masking (EXC4b). Public API keys (EXK11). Evidence pack export (EXK8).

**Migration**: Alembic revision 0001 (no down_revision). Down migration drops the tables.

**Tests**:
- One fixture per file type (synthetic or public, with a source note). Each upload creates a `files` row with the correct SHA-256.
- A file above the tenant limit returns 413 with a reason and stores nothing.
- A 3-page scanned PDF gives 3 `pages` rows; the original bytes are unchanged.
- An UPDATE on `events` raises an error.
- A changed object in MinIO fails the hash check on read.
- Tenant A cannot read tenant B's job through the endpoints.

**Gating check**: The tests above pass. One upload shows the full event chain in `events`.

---

## EXK0b — EU host (Hetzner)

**Objective**: Run the stack on a Hetzner Germany server for ≤ $10 per month.
**Prerequisites**: EXK0 ✅; open items "secrets mechanism", "stack RAM", "EU-only engineering access".
**Rough scope (superseded by the detailed spec below)**: Server, firewall, compose deploy, secrets store, Postgres backups with one tested restore, cost record.

### EXK0b detailed implementation spec (DRAFT, waits for approval, 18 Nov 2026)

**Decisions taken in the session**: one combined slice (CircleCI port + server + deploy). CircleCI replaces GitHub Actions. Secrets: Doppler + one CircleCI context variable. The server is shared (Nuremberg, `eu-central nbg1`, Ubuntu 24.04, 4 vCPU, 7.7 GB RAM, about 5 GB available) with unveilio, foundry, wevit and observability. A new script `deploy-infra` carries the Exaktiv data stack; the shared `/opt/stack/bin/deploy` stays untouched (its policy forbids volumes, published ports and third-party images). **Postgres is on Neon, Frankfurt (`aws-eu-central-1`)**, not on the server. The Temporal database decision is parked for the Temporal phase.

**Changes against the phase list**: (1) no Postgres container and no Postgres backups on the server; Neon point-in-time restore replaces them, with one tested restore. (2) Temporal is not deployed here. The server stack of this phase is MinIO only. (3) The CLAUDE.md "Datastore" row must say "PostgreSQL 16+ (Neon Frankfurt for EU; local Docker for development)". (4) Neon is a new processor: DPA, sub-processor list and the privacy notice recipients (PRD-W §8.3) need updates. (5) No application image exists yet (no Dockerfiles); app deploys come with EXK1 and EXW2.

**Probed on the server (read-only, 18 Nov 2026)**: `/opt/stack/<project>` per project; shared Caddy on 80/443; Docker network `edge`; ufw allows 22 only (Docker-published ports bypass ufw, so bind to `127.0.0.1`); `bin/deploy <project>` is an SSH forced command (a CircleCI key can only deploy a 40-character SHA); per-project users exist (`dossura-deploy`, `/opt/dossura/doppler.env`); Doppler is already used; no Doppler CLI on the host; Docker log rotation set; no backup jobs. The existing pattern in `productManager/.circleci/config.yml` is reused: one context variable `DOPPLER_TOKEN`, `load-doppler`, `APPS_HOST`/`APPS_KNOWN_HOSTS` from Doppler.

#### 1. Files (repository)

| Path | Content |
|---|---|
| `.circleci/config.yml` | Port of every job in `.github/workflows/ci.yml`: `python`, `ui`, `site`, `secrets`, `integration`, plus `deploy-infra` (main only, after all others). Keeps the planted-key and planted-hex checks. |
| `.github/workflows/ci.yml` | Deleted in the same change (one CI only). |
| `deploy/server/docker-compose.yml` | Server stack: MinIO only (Chainguard image pinned by digest, as in `deploy/docker-compose.yml`), port `127.0.0.1:9000`, one named volume, a healthcheck, project network `exaktiv`. |
| `deploy/server/deploy-infra` | Root-owned script on the server (installed by hand from a reviewed commit, never run from the deployed repository). Forced command; input is a 40-character SHA. |
| `deploy/server/policy.py` | Compose policy check used by `deploy-infra` (stdlib only, reads `docker compose config --format json`). |
| `deploy/server/setup.sh` | Idempotent root setup: user `exaktiv-deploy`, `/opt/stack/exaktiv`, read-only GitHub deploy key, forced-command line in `authorized_keys`, install of `deploy-infra` and `policy.py`. Prints what it changed. Dry-run flag. |
| `deploy/server/README.md` | Runbook: one-time setup, deploy, rollback, Neon restore test, cost record. |
| `deploy/known_hosts` | Public SSH host key of the server (pinned; no `ssh-keyscan` at deploy time). |
| `libs/core/exaktiv_core/db.py` and `settings.py` | New setting `postgres_ssl: bool = False`; helper `connect_kwargs()` returns `{"ssl": "require"}` when true. Used by `health.py`, `smoke.py`, `PgStore` and `migrations/env.py` (`connect_args`). Neon needs TLS. |
| `tests/unit/test_deploy_policy.py`, `test_circleci_config.py`, `test_db_ssl.py` | See section 6. |

#### 2. `deploy-infra` algorithm (policy-first, nothing from the repository is executed)

1. Input: `SSH_ORIGINAL_COMMAND` must match `^[0-9a-f]{40}$`, else exit 2.
2. `flock` on `/opt/stack/exaktiv/.deploy.lock`.
3. `git fetch` the branch `main` from `git@github.com:vedm1/exactiv.git` with the read-only deploy key and the pinned GitHub host key (fingerprint checked, as `init-deploy-source` does).
4. Refuse a SHA that is not an ancestor of `origin/main`.
5. Write `deploy/server/docker-compose.yml` from that SHA to a temp file, atomic rename.
6. Run `docker compose config --format json | python3 /opt/stack/bin/exaktiv-policy.py`; any violation stops before a pull.
7. Fetch secrets from Doppler (service token in `/opt/stack/exaktiv/doppler.token`, mode 600) into `/opt/stack/exaktiv/.env` (mode 600). Secrets never print. The Doppler config holds `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`.
8. `docker compose pull`, then `up -d --wait --wait-timeout 300`.
9. On success write the SHA to `.current`. On failure bring the previous SHA back up and exit 1.

**Policy (`policy.py`)**: every image is pinned by `@sha256:`; no `privileged`, `pid`, `ipc`, `network_mode`, `userns_mode`, `devices`, `sysctls`, `build`, `env_file`, `secrets`, `configs`; no `cap_add`; no root `user`; volumes only as named volumes of this project (no bind mounts, no host paths, no docker socket); ports only with host IP `127.0.0.1`; networks only the project network, never `edge`; each service has a healthcheck and a memory limit (`mem_limit`, at most 1 GB for MinIO).

#### 3. CircleCI pipeline

- Jobs map one to one from `ci.yml`: `python` (docker executor `cimg/python:3.12`, uv, ruff, format check, mypy, fixture check, licence check, unit/guardrail/site tests), `ui` (node 24 + pnpm, lint, typecheck, test, brand checks, planted hex, build, no-external, licence check), `site` (build gates, Playwright browser checks, pinned Lighthouse), `secrets` (gitleaks pinned with checksum, planted key must fail, secret-scan test), `integration` (machine executor, `scripts/make_env.sh`, compose up, `pytest -m integration`, logs on failure, `down -v`).
- Commands for repeated steps: `load-doppler` (as in `productManager`).
- `deploy-infra` job: `add_ssh_keys` with the fingerprint from Doppler `ci`, host key from `deploy/known_hosts`, then `ssh exaktiv-deploy@$APPS_HOST "$CIRCLE_SHA1"`. Filter: branch `main`, `requires` all other jobs. A no-op with a clear message if `APPS_HOST` is unset.
- The CircleCI context `exaktiv-production` holds one variable: `DOPPLER_TOKEN` (service token for the Doppler `ci` config). Doppler `ci` holds `APPS_HOST`, `DEPLOY_SSH_FINGERPRINT`.
- Validate with `circleci config validate` before merge.

#### 4. Server setup (done once, by me over SSH as root, after the plan is approved)

Create user `exaktiv-deploy` (docker group; note: docker group is root-equivalent, so the forced command and the policy are the control). Create `/opt/stack/exaktiv` (owner `exaktiv-deploy`, 750). Generate a new ed25519 deploy key pair for CircleCI **on this machine** (`~/vultr-keys/circleci-exaktiv`), install only the public key with the forced command `command="/opt/stack/bin/deploy-infra",no-pty,no-port-forwarding,no-agent-forwarding,no-X11-forwarding` in `/home/exaktiv-deploy/.ssh/authorized_keys`. The key `vultr-unveilio` is used only for this one-time root setup. No change to Caddy, to `bin/deploy` or to another project's files or containers.

**Steps only the user can do** (secrets): create the Doppler project and a `ci` and a `prd` config with the values above; put the Doppler service token for `prd` into `/opt/stack/exaktiv/doppler.token` on the server (I give the one-line command, the user runs it); add `DOPPLER_TOKEN` to the CircleCI context; add the private key `circleci-exaktiv` to the CircleCI project (Additional SSH Keys); link the GitHub repository in CircleCI after the first push; create the Neon project in Frankfurt and the Neon DPA.

#### 5. Neon (not deployed by this phase, prepared by it)

`POSTGRES_HOST` (direct endpoint, not the pooler, for migrations and advisory locks), `POSTGRES_PORT=5432`, `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD`, `POSTGRES_SSL=true` live in Doppler. If the pooler is used later, asyncpg needs `statement_cache_size=0`. The first live connection to Neon is **not tested in this phase** (no credentials here): it is the user's smoke test with `uv run python -c` on the health check once the Doppler values exist. Restore test: create a Neon branch from a point in time, check a known row, delete the branch; record the date in the runbook.

#### 6. Test plan (TDD, failing first)

| Test | Asserts |
|---|---|
| `test_policy_accepts_the_real_server_compose` | `deploy/server/docker-compose.yml` has no violation |
| `test_policy_rejects_*` (parametrised) | privileged; bind mount; docker socket; port without `127.0.0.1`; `0.0.0.0` port; image without digest; `network_mode: host`; `cap_add`; `env_file`; root user; network `edge`; missing healthcheck; missing memory limit; `build` |
| `test_policy_reports_all_violations` | two bad services give two messages |
| `test_deploy_infra_rejects_non_sha_input` | runs the script in a temp dir with a fake `docker` and `git`: `"; rm -rf /"`, short SHA, uppercase give exit 2 and no command runs |
| `test_deploy_infra_never_prints_secrets` | fake Doppler answer with a sentinel; output has none |
| `test_circleci_config_has_every_ci_job` | each former Actions job exists; `deploy-infra` requires all and filters to `main`; no job uses an unpinned remote script |
| `test_circleci_config_has_planted_checks` | planted key and planted hex steps present |
| `test_g9_no_secret_values_in_circleci_or_deploy_files` | gitleaks config passes; no token pattern |
| `test_db_ssl_kwargs` | `postgres_ssl=True` gives `{"ssl": "require"}`; default gives `{}`; `repr(settings)` hides the password |
| `test_ci_yml_removed` | `.github/workflows/ci.yml` does not exist |

Existing tests stay green. `circleci config validate` runs on the file. `setup.sh --dry-run` output is checked on the server before the real run.

#### 7. Verify and close

`uv run pytest`, ruff, mypy, `circleci config validate`, `bash -n` and `shellcheck` on the scripts. Independent subagent review (server access, G9, policy bypass). On the server after setup: `ssh -i circleci-exaktiv` with a valid SHA deploys MinIO; a bad input is refused; the key cannot get a shell; `docker ps` shows the other projects unchanged (same container IDs and uptime as before). Docs: `PHASES.md` row, build plan (secrets mechanism resolved = Doppler; MinIO licence; new open items: Neon DPA and sub-processor, Doppler workplace region, EU-only access, Temporal DB, off-box copy not needed for Postgres but needed for MinIO data), CLAUDE.md Datastore row, a cost record (server share, Neon plan).

**Cost**: the server is shared, so the marginal cost is zero. Neon plan cost counts next to it against the $10 limit; the user states the plan.

#### Implementation notes (EXK0b, 18 Nov 2026)

- **CircleCI context** is `exaktiv_deploy` (the spec text above said `exaktiv-production`). The Doppler token is in it already.
- **Independent review found 3 critical gaps in the first policy draft; all fixed before any deploy ran**: (1) a volume with `driver_opts` could bind-mount the host root, and volume or network names of another project were not checked; (2) the project name was not pinned, so `name: wevit` could recreate another project's containers; (3) the policy checked uninterpolated text while `up` ran the interpolated one, and Doppler keys such as `COMPOSE_FILE` could steer docker. Now: allowlist policy, project name and `-p exaktiv` pinned, check on the interpolated config with all profiles, `.env` reduced to two keys (single-quoted), the `COMPOSE_*` and `DOCKER_*` variables of the caller unset, only `${MINIO_ACCESS_KEY}` and `${MINIO_SECRET_KEY}` allowed as variables, registry limited to `cgr.dev/chainguard/`.
- **Other review fixes**: a deploy of a commit older than the live one is refused; `pull` runs before the switch and the old files are restored on any failure; the secrets go to a temporary file first; `flock -w 600`; `deploy.conf` moved to root-owned `/etc/exaktiv/` and its values are shape-checked (no option injection); the Doppler CLI is pinned (3.75.3) with a checksum; `setup.sh` refuses a key file of more than one line; `docker image prune` removed (it would prune other projects' unused images on the shared host).
- **Residual risk (user steps)**: the CircleCI context must be restricted to `main` in the CircleCI settings, and `main` must be protected in GitHub. Docker group membership is root-equivalent, so the forced command plus the policy are the whole control.
- **DATABASE_URL (added 18 Nov 2026)**: `PostgresSettings` accepts `DATABASE_URL` (Neon) and splits it into the `POSTGRES_*` parts; its `sslmode` sets TLS (`require`, `verify-ca`, `verify-full`; `disable`, `allow` and `prefer` mean no TLS). It wins over `POSTGRES_*`; a blank value is ignored. Validation errors hide the input, so the URL never prints. `dsn()` now percent-encodes user and password. **Pooled host only (decision 18 Nov 2026)**: a host with `-pooler.` (or `POSTGRES_POOLED=true`) turns the asyncpg statement cache off (`statement_cache_size=0`), and Alembic gets `prepared_statement_cache_size=0` plus unique prepared-statement names, because PgBouncer in transaction mode keeps no session state. The rate limit uses a transaction-level advisory lock, which works in that mode. Session-level features (`LISTEN`, session locks, `SET`) must not be used. **Probed 18 Nov 2026 against a throwaway PgBouncer 1.26.1 (transaction mode, scram) in front of Postgres 16.4**: `alembic upgrade head`, `downgrade base` and `upgrade head` again all ran; the site form store gave the sixth refusal, exactly 5 accepted out of 20 concurrent calls (the advisory lock holds), insert, pending mail and the two jobs' queries worked. With the statement cache on, 30 rounds also worked on this PgBouncer version, so the cache-off setting is a safe default for older poolers, not a proven need. **Not verified against Neon itself.** Probe containers and network were removed. Tests: `tests/unit/test_db_url.py`.
- **Live checks, 19 Nov 2026**: the CircleCI deploy of `7ebe52a` ran; MinIO is healthy on `127.0.0.1:9000` (user 65532 on a fresh named volume works, 1 GiB limit, port closed from outside); other projects unchanged. Neon pooled URL (PostgreSQL 18.7, host in `eu-central-1`): connect with TLS `require`, `alembic upgrade head`, constraint and index checks, the rate limit and an advisory-lock race all passed. `pg_stat_ssl` shows `ssl = false` for the backend because Neon's pooler talks to its compute over its own leg; the client leg used `ssl=require`, which fails if TLS is missing. Tables `alembic_version`, `site_enquiries`, `site_form_hits` now exist on that database (empty).

## EXK0c — India host

**Objective**: Run the stack on an India provider for ≤ $10 per month, with India data location.
**Prerequisites**: EXK0 ✅; open item "India hosting provider".
**Rough scope**: As EXK0b. Record the provider's data-location terms.

## EXK2 — Model gateway and router

**Objective**: One gateway for all model calls, with versioned routes and a region check that never falls back.
**Prerequisites**: EXK0 ✅; open item "frontier model endpoint per region".
**Rough scope**: LiteLLM pinned by digest; call log (model, cost, latency, tokens) without personal data; `config/routes/*.yaml`; retry once then "failed"; G7 test.

## EXK3 — Extraction contract

**Objective**: Final value record type and storage; drop values without a source (G1).
**Prerequisites**: EXK1 ✅, EXK2 ✅.
**Rough scope**: Value table, extraction task interface for products, OCR text + page image inputs (FR-EXT-5), G1 test.

## EXK4 — Validation layer

**Objective**: Schema and domain validation from versioned configuration (G3, G4).
**Prerequisites**: EXK3 ✅.
**Rough scope**: Rule loader for `config/`, rule types (type, format, required, allowed list, unit list, date range, sum check), review reason codes, CI grep check for rules in prompts.

## EXK5 — Confidence and abstention

**Objective**: Calibrated confidence per value and the auto-accept decision (G2).
**Prerequisites**: EXK4 ✅.
**Rough scope**: Score from model signals + validation; per-field thresholds; "always review"; 200-review rule; calibration version.

## EXK6 — Review queue backend

**Objective**: Review tasks and actions with full audit.
**Prerequisites**: EXK5 ✅.
**Rough scope**: Queue per tenant (priority, age), accept/correct/not-present, job completion rule (FR-REV-5), extension points for product screens.

## EXK6-ui — Core reviewer UI

**Objective**: Keyboard-first review screen with the source crop next to the value.
**Prerequisites**: EXK6 ✅, EXD3 ✅.
**Rough scope**: Queue list, field review with marked page area, keyboard map, tokens. Target ≤ 8 s median per simple field; open in < 1 s.

## EXK7 — Evaluation harness

**Objective**: Compare the pipeline with a frontier baseline on a frozen set.
**Prerequisites**: EXK5 ✅, EXD4 ✅.
**Rough scope**: Frozen set format, runner, per-field metrics, hard subset, cost per unit, HTML + JSON report on the EXD4 template.

## EXK8 — Evidence pack (Exaktiv Proof)

**Objective**: Export a per-job evidence pack (PDF + JSON) from the event log.
**Prerequisites**: EXK6 ✅, EXD4 ✅.
**Rough scope**: Pack builder, source crop per value, product mapping hook (FR-PRF-4).

## EXK9-p1 — Corrections store and training sets

**Objective**: Labelled examples per tenant and task, with a frozen evaluation split.
**Prerequisites**: EXK6 ✅.
**Rough scope**: Example store, set builder, consent and anonymisation flags (FR-LRN-4).

## EXK9-p2 — Model registry and regression gate

**Objective**: No model, adapter, prompt or route goes live without a passed gate (G10).
**Prerequisites**: EXK7 ✅.
**Rough scope**: Registry tables, gate rule (no field −1 point, overall not lower), promotion and one-step rollback.

## EXK9-p3 — LoRA adapter pipeline

**Objective**: Train private LoRA adapters per tenant and task.
**Prerequisites**: EXK9-p1 ✅, EXK9-p2 ✅; open items "base model", "GPU hosting".
**Rough scope**: PEFT training job, tenant source log (G6), registration through the gate.

## EXK10 — Metering and usage export

**Objective**: Count accepted units once per tenant per month (G5).
**Prerequisites**: EXK6 ✅.
**Rough scope**: Metering table, unit definition hook per product, monthly export, reconcile report.

## EXK11 — Public API

**Objective**: External REST API with tenant API keys and a completion webhook.
**Prerequisites**: EXK6 ✅.
**Rough scope**: Keys with scopes, endpoints of FR-API-1, signed webhook, G6 integration test.

## EXD1 — Brand package

**Status**: ✅ Done (18 Nov 2026).
**Objective**: One folder holds the whole Exaktiv identity, so every screen, report and page uses the same source.
**Prerequisites**: None.
**Delivered**: `brand/README.md`, `brand/guidelines/index.html`, `brand/logo/svg` and `brand/logo/png`, `brand/favicon`, `brand/social/og-image.png`, `brand/fonts` (woff2 + OFL texts + `fonts.css`), `brand/tokens` (`tokens.css` source, `tokens.json`, `tokens.ts`, `build_tokens.py`, `check_brand.py`), `brand/components/exaktiv.css`, `brand/icons/arrow-right.svg`.
**Tests**: `python3 brand/tokens/check_brand.py` passes: 30 text pairs pass WCAG 2.2 AA in light and dark mode, generated files match `tokens.css`, and no component has a hex value, raw token, monospace font, radius or blurred shadow.

### EXD1 Implementation notes (18 Nov 2026)

- Fonts come from Fontsource 5.3.0 (Google Fonts builds), Latin and Latin Extended subsets only. Recorded in `LICENCES.md`.
- The fonts have no "→" glyph (U+2192). Buttons and links draw the arrow with an inline SVG data URI in `exaktiv.css`. A CSP must allow `img-src 'self' data:`.
- `font-variant-numeric: tabular-nums` on running text also widens full stops, commas and semicolons in these fonts. Use `.ex-tnum` only in tables and line numbers.
- Young Serif has one weight. Every page sets `font-synthesis: none`, so browsers do not fake a bold.
- The evidence band (`.ex-mark`) is a gradient from 0.3 em to 1.02 em. At a display line height below 0.98 it covers the descenders of the line above.
- The wordmark in all logo files is outlined from Young Serif with −0.035 em letter spacing, so logos never depend on an installed font.

## EXD2 — Tokens, fonts and guards in the UI

**Objective**: `ui/` uses only the brand tokens and fonts, and CI blocks off-brand code.
**Prerequisites**: EXK0 ✅, EXD1 ✅.
**In scope**:
- `scripts/sync_brand.py`: copy `brand/tokens/tokens.css` and `tokens.ts` to `ui/src/tokens/`, and `brand/fonts/*.woff2` + `fonts.css` to `ui/public/fonts/`. Copy only, never edit the copies.
- `ui/src/main.tsx` imports, in this order: fonts, tokens, `brand/components/exaktiv.css` (base styles).
- A `useTheme` hook that sets `data-theme` on `<html>`. Reviewer UI default: `dark`. A user setting can change it.
- Favicons and the web manifest in `ui/index.html` and `ui/public/`.
- CI step and pre-commit hook: `python3 brand/tokens/check_brand.py`.
**Out of scope**: Components (EXD3).
**Tests**:
- `test_tokens_in_sync`: the copies in `ui/` match `brand/` byte for byte.
- CI fails when a CI-only fixture component contains `#ff0000` (planted, like the EXK0 secret check).
- `App.test.tsx`: `data-theme="dark"` changes `--ex-ground` on the root.
- No network request to a font or CDN host during `vite build` and in the built HTML.
**Gating check**: CI green with the brand step. The planted violation fails CI.

### EXD2 Implementation notes (18 Nov 2026)

- Three changes to the spec. (1) `sync_brand.py` also copies `exaktiv.css` to `ui/src/styles/`, so `ui/` builds without `brand/`. (2) Fonts load from a `<link href="/fonts/fonts.css">` in `index.html`, not from `main.tsx`, so Vite does not re-hash them. (3) The planted violation is a temp file written at CI time, because `check_brand.py` scans `ui/src` by default.
- `check_brand.py` skips any path with a `tokens` folder. A planted fixture must not sit in such a folder.
- Vitest stubs CSS by default: `?raw` imports of CSS return an empty string. `test.css: true` in `vite.config.ts` fixes it. With it, jsdom resolves `--ex-ground` per `data-theme`, but it does not follow `var()` chains. The test compares the unresolved values.
- `check_brand.py` also scans `ui/src/**/*.test.tsx`: tests must not name `--ex-raw-*` tokens.
- `brand/` is excluded from ruff (EXD1 scripts, own style). The G12 `LICENCES.md` test now counts rows only in the Models and Datasets sections (the Fonts table is from EXD1).
- Not run locally: the GitHub Actions workflow and the pre-commit hooks (YAML written, not executed). The first CI run confirms them.

## EXD3 — React component library

**Objective**: Every part in `exaktiv.css` as a typed, accessible React component, plus the reviewer parts.
**Prerequisites**: EXD2 ✅.
**In scope** (`ui/src/components/`): `Button` (primary, secondary, link form), `GoLink`, `Mark`, `Ref` and `Citations` (the Trace: numbers in order of first use, per page, through a React context), `Cards` and `Card` (also early access), `Pillars`, `Steps`, `FindingCard` (code lines, hit line, claim, source), `Table`, `Field` with `Input`, `Select`, `Textarea` and error state, `Notice`, `Header`, `Footer`, `ThemeToggle`. Reviewer parts: `SourceCrop` (page image with the value's bbox outlined in `--ex-source` and the evidence band over the text span) and `ValueRow` (value, status, confidence later in EXK5). A dev-only gallery route mirrors `brand/guidelines/index.html`.
**Out of scope**: Product screens (EXK6-ui, EXC6-ui, EXP5-ui).
**Tests**:
- One vitest file per component. Keyboard: Tab reaches every control, and focus is visible.
- `Ref` without a `source` prop throws in development. G1 applies to the UI: no number without a source.
- `Citations` numbers 1, 2, 3 in order of first use, and each `Ref` links to its citation id.
- axe (vitest-axe or equivalent with an allowed licence) reports 0 violations on the gallery.
- `check_brand.py` passes on `ui/src`.
**Gating check**: All component tests green, 0 axe violations, gallery checked side by side with the guidelines page.

## EXD4 — Report and PDF template

**Objective**: One template for every HTML report and PDF: the EXK7 evaluation report, the EXK8 evidence pack and the EXC6 case summary.
**Prerequisites**: EXD2 ✅.
**In scope**: A Python render function in `libs/core` (HTML from a template, PDF from the HTML). A4, light mode only, fonts embedded from `brand/fonts`. Header with the lockup, footer with page number, job ID and render time. Source references as Trace footnotes with the source crop. Tables use `.ex-table` with tabular figures. A "draft" watermark variant (EXC6). Renderer choice is an open item (licence check first).
**Tests**:
- Render a synthetic report (fixture with a `SOURCE.md` note, G8) to HTML and PDF.
- The PDF embeds Young Serif, Instrument Sans and Gelasio, and its page size is A4.
- The HTML contains no `http://` or `https://` URL other than links in the content.
- The draft variant shows the watermark on every page.
**Gating check**: EXK7 and EXK8 can call one render function with their data.

## EXD5 — Website kit (PRD-W)

**Objective**: The static site for the 10 PRD-W pages, built on the brand package.
**Prerequisites**: EXD2 ✅. PRD-W decisions D1 to D6 closed. Where the site code lives is an open item.
**In scope**: Static page templates with `exaktiv.css`; favicons and manifest at the site root; Open Graph image; `sitemap.xml`, `robots.txt`, `llms.txt`, `security.txt`; schema.org Organization with `legalName` Valyrian Tech Pvt Ltd; security headers with CSP `default-src 'self'; img-src 'self' data:; frame-ancestors 'none'`. A claims file (`claims.yaml`, from PRD-W §6) that the build reads: a footnote renders only for a claim with status "Ready".
**Out of scope**: The form endpoint (its own phase under PRD-W §7), analytics (phase 2).
**Tests**:
- The build fails on a footnote for a claim that is not "Ready", on any banned claim string (PRD-W §6), and on any third-party URL.
- A browser check on every page: 0 cookies, 0 third-party requests.
- Lighthouse 90 or more for performance, accessibility, best practices and SEO. Page weight under 1 MB. One H1 per page.
- No personal, employer or client names in pages, file names or metadata (grep check with a name list kept outside the repo).
**Gating check**: The build-related items of the PRD-W definition of done pass on staging.

### EXD5 Implementation notes (18 Nov 2026)

- **Built as specced:** `site/` in this repository, `scripts/build_site.py` (Python, Jinja2), claims file with `ready | to_confirm | to_write`, zero JavaScript, staging noindex by default, `--launch` gate. `cite()` is the only way to make a footnote. `backed(id, words)` gives the evidence band and number only when the claim is ready, and plain words otherwise, so a page upgrades itself when a claim becomes ready.
- **Changes to the spec.**
  - Decisions D1, D4 and D6 are still open. `base_url` and both mail addresses are `*.invalid` placeholders, and the privacy notice has a `[[TODO registered address]]`. `--launch` fails on all of them.
  - The nav is flat (6 links and a Contact button). There is no "Capabilities" menu, because a menu needs JavaScript or extra CSS.
  - The Contact page has a mailto link and no form until EXW1-ui. (Done in EXW1-ui: the form is on the page, the mailto link stays as the second route.)
  - The sample finding uses the brand form "billing/Invoice.java, line 142" in Instrument Sans (the PRD copy deck sets it in monospace, which the brand bans).
  - The header button is secondary. The hero button is the one vermilion button (brand rule 9).
- **Claims added to the register:** `access-logged` and `retention` (`to_write`), because the Security page states them. Four "Why now" claims (`to_confirm`): nobody has checked their dates against the sources. The `pages:` lists of the pillar claims include Home and How we work.
- **Checks.** Brand SVGs carry an `xmlns:c2pa` namespace declaration. The URL check ignores `xmlns` values (they are names, not requests). Font licence texts are skipped by the URL check. The unready-claim text check in `--launch` also catches a claim typed by hand.
- **Lighthouse** runs on an indexable copy of the build (noindex removed, robots open), because a staging build fails the SEO crawl audit by design. It found one real issue: heading order on How we work (fixed). Score 100 in all four categories on all 10 pages. The script uses a pinned `lighthouse@13.6.0` through `pnpm dlx`; it adds nothing to the repository. Chrome comes from the runner or `CHROME_PATH`.
- **New dev dependencies:** `jinja2` (BSD-3) and `playwright` (Apache-2.0). `mypy_path` gains `scripts`. Ruff ignores S704 in `scripts/build_site.py` (every interpolated value is escaped first).
- **Not done or not verified.**
  - The name check ran only on synthetic names. The real list stays outside the repo, so CI cannot run it. Run `--launch --names FILE` locally before launch.
  - The manual keyboard test, the browser matrix and the WCAG 2.2 AA review beyond Lighthouse's axe rules are open.
  - The GitHub Actions `site` job and the pre-commit hook are written but not run.
  - Staging password and HTTPS headers on a real server belong to EXW2. `_headers` is a neutral file that EXW2 turns into server config.

## EXC1 — Claims schema and config

**Objective**: Claims document types and fields as versioned configuration.
**Prerequisites**: EXK4 ✅.
**Rough scope**: 12 document types (PRD-A §5), fields (PRD-A §6.1), validation rules, checklist per claim type.

## EXC2 — Claims test set

**Objective**: A labelled synthetic and handwritten test set.
**Prerequisites**: EXC1 ✅; open items "dataset licences", "volunteers".
**Rough scope**: 40–60 claim files, 300–500 documents, EN/HI/KN, answer key, source notes.

## EXC3 — Page classification

**Objective**: Classify claim pages into the 12 types at 95% or more.
**Prerequisites**: EXC1 ✅, EXK3 ✅.

## EXC4 — Field extraction

**Objective**: Extract the claims fields per document type through the core contract.
**Prerequisites**: EXC3 ✅, EXK5 ✅.

## EXC4b — Identifier masking

**Objective**: Mask Aadhaar, PAN, bank account and phone numbers on ingest (A-G4).
**Prerequisites**: EXC4 ✅.
**Rough scope**: Detection in text and images, masked page images, role that can see unmasked values (never Aadhaar), synthetic-identifier tests.

## EXC5 — Cross-document checks

**Objective**: Checks X1–X10 and fact-only flags.
**Prerequisites**: EXC4 ✅; open items "IRDAI non-payable list", "policy-rule fields".

## EXC6 — Case summary

**Objective**: Case summary model and PDF with source links.
**Prerequisites**: EXC5 ✅, EXK6 ✅, EXD4 ✅.

## EXC6-ui — Case view

**Objective**: Case view in the reviewer UI; mouse-free completion.
**Prerequisites**: EXC6 ✅, EXK6-ui ✅.

## EXC7 — Claims benchmark

**Objective**: Pipeline vs Gemini Flash (India region) on the test set.
**Prerequisites**: EXC2 ✅, EXC4 ✅, EXK7 ✅.

## EXC7b — Handwriting LoRA

**Objective**: Handwriting fine-tune that meets the demo pass rule.
**Prerequisites**: EXC7 ✅, EXK9-p3 ✅.

## EXC8 — Claims evidence pack

**Objective**: Core evidence pack plus the IRDAI / DPDP / FREE-AI mapping page.
**Prerequisites**: EXK8 ✅, EXC6 ✅.

## EXC9 — Pilot hardening

**Objective**: Make a tenant ready for a pilot on real data in India.
**Prerequisites**: EXK0c ✅, EXC4b ✅, EXC8 ✅, EXK10 ✅, EXK11 ✅; open item "ISO 27001 start".

## EXP1 — ETIM 10 model

**Objective**: ETIM 10 electrical model as versioned configuration, with code and unit validation (B-G1).
**Prerequisites**: EXK4 ✅; open item "ETIM licence".

## EXP2 — Product Data test set

**Objective**: 500 labelled SKUs from 10+ suppliers and 20+ classes.
**Prerequisites**: EXP1 ✅.

## EXP3 — ETIM classification

**Objective**: Top 3 classes with confidence; 95% or more top-1 after review.
**Prerequisites**: EXP1 ✅, EXK3 ✅.

## EXP4 — Feature extraction

**Objective**: Feature values with unit conversion, value-code mapping and variant split.
**Prerequisites**: EXP3 ✅, EXK5 ✅.

## EXP5 — Pool check and export

**Objective**: Pool check rules and upload-ready exports; "accepted" only after pool pass (B-G3).
**Prerequisites**: EXP4 ✅; open items "pool upload format", "2BA/ITEK test validation", "first pool".

## EXP5-ui — SKU and family views

**Objective**: SKU view, family view and bulk accept.
**Prerequisites**: EXP4 ✅, EXK6-ui ✅.

## EXP6 — Benchmark and quality report

**Objective**: Batch quality report, benchmark and the free-fill test.
**Prerequisites**: EXP2 ✅, EXP5 ✅, EXP5-ui ✅, EXK7 ✅, EXK0b ✅.

## EXP7 — ETIM upkeep

**Objective**: Map catalogues to a new ETIM version with the official change files.
**Prerequisites**: EXP6 ✅.

## EXP8 — ECLASS support

**Objective**: ECLASS support (v1.1).
**Prerequisites**: EXP6 ✅; open item "three paying suppliers".

## EXW1 — Contact form endpoint

**Objective**: Receive PRD-W §7 contact form submissions, store them in the EU, notify the team and delete them after 6 months.
**Prerequisites**: EXK0 ✅; open items "where the website code lives", "PRD-W D4" and "PRD-W D6".
**In scope**:
- A FastAPI service (Python 3.12). Proposed path: `services/site_form` (depends on the open item for the code location).
- Table `site_enquiries`: `id`, `created_at`, `name`, `email`, `company`, `role` (nullable), `topic`, `data_region` (nullable), `message`, `delete_after`.
- Field rules from PRD-W §7. Server-side validation with a field-level error format.
- Spam controls: hidden honeypot field, minimum fill time, rate limit of 5 submissions per IP address in 10 minutes.
- Team mail and automatic reply through the EU mail provider (D6).
- Daily deletion job for rows past `delete_after` (W-G4).
- Logs with masked email addresses and no message content (G11).
**Out of scope for EXW1**: the form on the page (EXW1-ui), deploy (EXW2).
**Tests**: the PRD-W §7 acceptance criteria; a retention test (a row past `delete_after` is gone after the job runs); a log-scan test with synthetic personal data (G11).
**Gating check**: all tests green, then an independent subagent review (W-G4).

### EXW1 detailed implementation spec (DRAFT, waits for approval, 18 Nov 2026)

**Decisions taken in the spec session**: code in `services/site_form` (monorepo). D6 = Brevo, HTTP API. Alembic is added in EXW1 (scope moved from EXK1; EXK1 builds on `0001`). Rate-limit state in Postgres with a salted IP hash.

**Probed, not assumed (Brevo docs, 18 Nov 2026)**: `POST https://api.brevo.com/v3/smtp/email`; header `api-key`; body `sender{email,name}`, `to[{email,name}]`, `replyTo{email}`, `subject`, `htmlContent` (required without a template), `textContent` (optional); success `201 {"messageId": "..."}`; `400 {"code","message"}`. Brevo hosts in the EU (France, Belgium; vendor help page). **Not confirmed** (open items): DPA signed, sub-processor list, retention of transactional mail content in Brevo logs.

#### 1. Files

| Path | Content |
|---|---|
| `libs/core/exaktiv_core/db.py` | `PostgresSettings` (postgres_* only) and `dsn()`; reused by Alembic and EXK1. `Settings` stays unchanged. |
| `alembic.ini`, `migrations/env.py` (async, asyncpg via `run_sync`), `migrations/versions/0001_site_form.py` | `down_revision = None`. Upgrade creates 2 tables. Downgrade drops them. |
| `services/site_form/pyproject.toml` | package `exaktiv_site_form`. Deps: `exaktiv-core`, fastapi, uvicorn, httpx, python-multipart, email-validator, alembic, sqlalchemy. |
| `exaktiv_site_form/settings.py` | `SiteFormSettings(PostgresSettings)`: `brevo_api_key: SecretStr`, `ip_hash_secret: SecretStr`, `form_token_secret: SecretStr`, `mail_sender_email`, `mail_sender_name="Exaktiv"`, `team_inbox_email`, `site_base_url`, `trusted_proxy_hops: int = 0`, `min_fill_seconds: int = 3`, `rate_limit_max: int = 5`, `rate_limit_window_s: int = 600`. |
| `models.py` | `Topic`, `DataRegion` enums; `EnquiryIn`; `FieldError`. |
| `validation.py` | `validate(raw: Mapping[str, str]) -> EnquiryIn \| list[FieldError]`. Pure function. |
| `spam.py` | `client_ip()`, `ip_hash()`, `make_token()`, `check_token()`, honeypot test. |
| `store.py` | `Store` protocol + `PgStore` (asyncpg). |
| `mail.py` | `Mailer` protocol, `BrevoMailer`, mail templates (plain functions, text + escaped HTML). |
| `logging.py` | `mask_email()`, `MaskingFilter`, `get_logger()`. |
| `main.py` | FastAPI app, routes, exception handlers. |
| `jobs.py` | CLI: `python -m exaktiv_site_form.jobs retention \| retry-mail \| purge-hits`. |
| `tests/unit/site_form/*`, `tests/integration/site_form/*`, `tests/guardrails/test_w_g4_*.py`, `test_g11_*.py` | See section 8. |

Root `pyproject.toml`: add the member and `mypy_path` entry. No compose change. Dockerfile and timers are EXW2.

#### 2. DDL (migration `0001_site_form`)

```sql
CREATE TABLE site_enquiries (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at       timestamptz NOT NULL DEFAULT now(),
  name             text        NOT NULL CHECK (char_length(name)    BETWEEN 2 AND 100),
  email            text        NOT NULL CHECK (char_length(email)   BETWEEN 3 AND 254),
  company          text        NOT NULL CHECK (char_length(company) BETWEEN 2 AND 150),
  role             text        NULL     CHECK (char_length(role) <= 100),
  topic            text        NOT NULL CHECK (topic IN ('legacy_modernisation','ai_product_delivery',
                                          'product_data_early_access','partnership','other')),
  data_region      text        NULL     CHECK (data_region IN ('eu_uk','india','other')),
  message          text        NOT NULL CHECK (char_length(message) BETWEEN 20 AND 2000),
  delete_after     timestamptz NOT NULL DEFAULT (now() + interval '6 months'),
  team_notified_at timestamptz NULL,
  autoreply_sent_at timestamptz NULL,
  mail_attempts    int         NOT NULL DEFAULT 0
);
CREATE INDEX site_enquiries_delete_after_idx ON site_enquiries (delete_after);
CREATE INDEX site_enquiries_mail_pending_idx ON site_enquiries (created_at)
  WHERE team_notified_at IS NULL OR autoreply_sent_at IS NULL;

CREATE TABLE site_form_hits (
  id      bigserial   PRIMARY KEY,
  ip_hash text        NOT NULL,
  hit_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX site_form_hits_ip_idx ON site_form_hits (ip_hash, hit_at);
```

Deviation from the phase list: three extra columns (`team_notified_at`, `autoreply_sent_at`, `mail_attempts`) so a mail failure does not lose an enquiry and the retry job knows what is open. No `tenant_id` (the form has no tenant; G6 not applicable). No raw IP column anywhere. The table `smoke_runs` stays (EXK1 drops it). A contract case: staff move `delete_after` by hand (documented in the runbook of EXW2).

#### 3. API contract

`GET /form-token` -> `200 {"token": "<issued_unix>.<hmac_sha256_hex>"}`. HMAC over `issued_unix` with `form_token_secret`. `Cache-Control: no-store`.

`POST /enquiries` (`application/json` or `application/x-www-form-urlencoded`). Body limit 16 KiB (else `413`). Fields: `name`, `email`, `company`, `role`, `topic`, `data_region`, `message`, `form_token`, and the honeypot `website`.

| Case | JSON client | Form client (no `Accept: application/json`) |
|---|---|---|
| Stored, or honeypot filled (identical on purpose) | `201 {"status":"received"}` | `303` to `{site_base_url}/contact/thanks/` |
| Invalid | `422 {"errors":[{"field","code","message"}]}` | `303` to `{site_base_url}/contact/problem/` (changed in EXW1-ui: a path, no query string, no values) |
| Rate limited | `429 {"error":"rate_limited"}` + `Retry-After` | `303` to `/contact/problem/` (changed in EXW1-ui) |
| Token present but too fast, forged or expired | silently dropped as spam: `201` | `303` to thanks |
| Token missing (no JavaScript) | stored, but counted against the stricter limit of 2 per 10 minutes per IP (`429` above that) | same |

Error codes: `required`, `too_short`, `too_long`, `invalid_email`, `invalid_choice`. Messages are fixed en-GB strings, never include the input. Override the FastAPI default 422 handler (it echoes input). No `Set-Cookie` on any response.

#### 4. Validation (`validate`)

Trim each value, normalise to NFC, reject NUL and other control characters except newline in `message`. `name` 2-100; `email` 3-254, parsed with `email_validator` (`check_deliverability=False`), no CR/LF; `company` 2-150; `role` empty becomes `None`, max 100; `topic` in enum; `data_region` empty becomes `None`, else in enum; `message` 20-2000. Counts are characters after trimming. All fields are checked, so one response lists every error.

#### 5. Spam controls (order inside `POST /enquiries`)

1. Read the body (size cap). 2. `ip = client_ip(request, trusted_proxy_hops)`: socket peer when hops = 0; else the Nth entry from the right of `X-Forwarded-For`. 3. `ip_hash = HMAC-SHA256(ip_hash_secret, ip)`; the raw IP is never stored or logged. 4. In one transaction: `pg_advisory_xact_lock(hashtext(ip_hash))`, count hits in the last `rate_limit_window_s`, refuse if count >= 5, else insert a hit (every attempt counts, including invalid and honeypot ones, so the 6th in 10 minutes is refused). 5. Honeypot `website` non-empty -> drop, `201`. 6. Token: valid signature and age between `min_fill_seconds` and 2 h; else drop as spam (`201`). 7. Validate. 8. Store. `purge-hits` deletes hits older than 1 hour. Correctness never depends on the purge (queries filter by time).

#### 6. Mail

`Mailer.send(MailMessage(to, subject, text, html, reply_to=None))`. `BrevoMailer`: httpx `POST`, `api-key` from `SecretStr`, timeout 5 s, success only on `201`; any other result raises `MailError(status_code)` (class and code only, no body). Base URL is a constant; a test proves no other host is called.
- **Team mail**: to `team_inbox_email`, `reply_to` = enquirer, fixed subject `New website enquiry: <topic label>` (no user input in headers or subject), text + HTML-escaped body with all fields.
- **Automatic reply**: to enquirer, fixed text: received, we reply within 1 business day, link to the privacy notice. It does not repeat the message (limits reflected spam and personal data).
- **Flow**: insert row, commit, answer the client, then `BackgroundTasks` sends team mail (set `team_notified_at`) then reply (set `autoreply_sent_at`), and increments `mail_attempts`. `retry-mail` (run every minute by EXW2) retries open rows with `mail_attempts < 5` and logs `enquiry_mail_failed id=<uuid>` after the 5th failure. A mail failure never changes the client response.

#### 7. Logs, retention, jobs

- **Logs (G11)**: JSON lines with event name and `enquiry_id` only. Never log field values, message, request body, exception messages (pydantic errors contain input) or IP. `MaskingFilter` also rewrites any email pattern in a record to `j***@a***.com` as a second line of defence. Uvicorn runs with `--no-access-log`.
- **Retention (W-G4)**: `retention` runs `DELETE FROM site_enquiries WHERE delete_after <= now()` and logs the count. EXW2 runs it daily.
- **Limit of this phase**: the team mailbox and Brevo logs keep their own copy of each message. The DB deletion does not remove them. See open items.

#### 8. Test plan (write first, TDD)

Fixtures: synthetic only. Persons `Test Person`, `test.person@example.test`, company `Example Test Ltd`, sentinel strings `MSG-SENTINEL-7c1e`, `+00 000 000000`. Source note added to `tests/fixtures/SOURCE.md` (G8). Unit tests use `FakeStore` + `FakeMailer` + a controllable clock. Integration tests (marker `integration`) create a throwaway database, run `alembic upgrade head`, and drop it.

| Test | Asserts |
|---|---|
| `test_valid_submission_stores_and_sends_both_mails` (§7 AC1) | `201`; 1 row; 2 mails (team: reply_to = sender, fixed subject; reply: to sender) |
| `test_missing_required_field_returns_field_error_and_stores_nothing` (AC2, parametrised over 5 required fields) | `422`; right `field` and code; 0 rows; 0 mails |
| `test_field_length_and_choice_rules` | boundaries 1/2/100/101, 19/20/2000/2001, bad topic, bad region, empty role/region become null |
| `test_email_with_newline_is_rejected` | header-injection input gives `invalid_email` |
| `test_honeypot_filled_drops_silently` (AC3) | same `201` body as success; 0 rows; 0 mails |
| `test_sixth_submission_in_ten_minutes_is_refused` (AC4, integration) | 5 accepted, 6th `429` with `Retry-After`; after 10 min the next is accepted; another IP unaffected |
| `test_rate_limit_is_race_safe` (integration) | 10 concurrent posts from one IP: exactly 5 accepted |
| `test_too_fast_or_bad_token_is_dropped` | token age < 3 s, forged signature, expired token: `201`, 0 rows |
| `test_form_client_gets_303_and_no_values_in_url` | redirect targets contain field names only |
| `test_no_set_cookie_and_only_brevo_host_called` (AC5, service part) | no `Set-Cookie`; recorded outbound hosts = `{api.brevo.com}` |
| `test_brevo_request_shape` | method, URL, `api-key` header, body fields, HTML escaped, 201 ok, 400 raises `MailError` |
| `test_mail_failure_keeps_row_and_client_still_gets_201` | row stored; `team_notified_at` null; `retry-mail` sends and sets it; stops at 5 attempts |
| `test_oversize_body_returns_413` | |
| `test_w_g4_row_past_delete_after_is_deleted` (integration) | after `retention`, the row is gone |
| `test_w_g4_row_before_delete_after_is_kept` | |
| `test_w_g4_delete_after_defaults_to_six_months` | `delete_after - created_at` is 6 months |
| `test_w_g4_no_raw_ip_stored` | no column or row contains the test IP; `ip_hash` differs per secret |
| `test_g11_logs_contain_no_personal_data` | run success, validation error, honeypot, rate limit, mail failure, DB failure; capture all log output; none of name, email, company, message, phone sentinel, IP appears |
| `test_g11_mask_email` and `test_g11_masking_filter_rewrites_emails` | `test.person@example.test` becomes `t***@e***.test` |
| `test_g11_validation_response_does_not_echo_input` | response text has no input value |
| `test_g9_secrets_not_in_repr_or_logs` | `repr(settings)` and logs hide the three secrets |
| `test_migration_0001_up_and_down` (integration) | tables, checks and indexes exist after upgrade; gone after downgrade; `down_revision is None` |

Verify: `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`, `scripts/check_licences.py` for the new Python packages, secret scan. Then an independent subagent review focused on W-G4 and G11 (gating check).

#### 9. Tracker changes at close

`PHASES.md` EXW1 to ✅ and an EXK1 note (Alembic baseline `0001` exists). Build plan: resolve D4 (own endpoint) and D6 (Brevo); resolve "code location" for EXW1 only (`site/` for EXD5 stays open); add open items below.

**New open items**: (a) sign the Brevo DPA, get its sub-processor list, confirm retention of transactional mail content; (b) team mailbox copy of enquiries needs a 6-month deletion routine, and the privacy notice (PRD-W §8.3) must say it; (c) decision 1 below.

#### Implementation notes (EXW1, done 18 Nov 2026)

- **Built as specced**, with these changes: the `python-multipart` dependency was dropped (form posts are parsed with `urllib.parse.parse_qsl`); `sqlalchemy[asyncio]` is needed for the async Alembic environment (adds `greenlet`); the test person uses `example.com` because `email_validator` rejects the special-use `.test` domain; email addresses must be ASCII (`allow_smtputf8=False`) so a rejected `replyTo` cannot strand an enquiry.
- **Brevo probe**: `POST /v3/smtp/email`, header `api-key`, `201` on success, `400 {code,message}` (docs, 18 Nov 2026). Not tested against the live API: there is no key yet. First live send is an EXW2 check.
- **Review findings fixed**: non-ASCII token raised `TypeError` (500, never rate limited); the G11 test now logs without the masking filter and also covers the real `BrevoMailer` and the jobs; the whole `deliver_one` is inside the `try`; the team mail and the automatic reply are independent; a non-string honeypot counts as filled; deeply nested JSON gives 400.
- **Known limits, accepted**: (1) the retry job and the request's background task can send the same mail twice (low harm: a duplicate reply); fix later with a claim step. (2) The automatic reply goes to any address with a limit per IP only, not per recipient. (3) With `TRUSTED_PROXY_HOPS=0` behind a proxy all visitors share one bucket. (4) `X-Forwarded-For` is tested at unit level only. (5) A copy of each message stays in the team mailbox and in Brevo's logs (open items). (6) `jobs.main` and `create_default_app` are not tested; EXW2 smoke-tests them on the host.
- **Alembic**: baseline `0001` has `down_revision = None`. EXK1 adds its revisions after it.

#### 10. Decision 1 (taken 18 Nov 2026: option A, spec approved)

Add settings `rate_limit_max_no_token: int = 2` and a test `test_missing_token_is_stored_under_stricter_limit`. Step 6 in §5 reads: token missing -> use the stricter limit and continue; token present but invalid -> drop.

**Decision 1: minimum fill time without JavaScript.** A static page cannot write a fresh timestamp into the form. Options: **(A, recommended)** token from `GET /form-token` fetched by JS; a post with no token goes through a stricter limit of 2 per 10 minutes per IP, and is still stored. Cost: a bot can skip the token but gets the stricter limit. **(B)** token required; no-JS users must use the mailto link. This conflicts with the EXW1-ui scope. **(C)** The service renders the form page. This breaks the static-site rule. The table in §3 shows (B) for a missing token; with (A), a missing token is stored and counted against the stricter limit instead of being dropped.

## EXW1-ui — Contact form on the site

**Objective**: Put the PRD-W §7 form on the EXD5 Contact page and connect it to EXW1.
**Prerequisites**: EXW1 ✅, EXD5 ✅.
**Rough scope**: plain HTML form that works without JavaScript (POST to EXW1); inline validation when JavaScript is on; field errors; confirmation state; privacy line under the button; no new third-party request (W-G3).

### EXW1-ui Implementation notes (19 Nov 2026)

- **Built as specced.** Form include `site/pages/_contact_form.html.j2` (used by Contact and the problem page), `site/assets/contact.js`, utility pages `contact-thanks` and `contact-problem`, `pages.yaml` keys `utility: true` and `scripts: [...]`, `build_site.py` rules, service redirects to `/contact/problem/`, CSP `form-action 'self'`.
- **Changes to the spec.** On success the script goes to `/contact/thanks/` (the same page as the no-JavaScript path) in place of replacing the form in place. The contact page has no hero button (`cta: null`), so the submit button is the one vermilion button (brand rule 9); the mailto link is in the body. The script reads the limits from the field attributes. The service checks them again, and a test checks that the HTML limits equal the service rules at the boundaries.
- **EXD5 rule changed.** "No JavaScript" became "no inline script, and only a script that `pages.yaml` declares for that page". Only `/assets/contact.js` on the Contact and problem pages is declared. The build fails on any other script and on a declared script that is missing.
- **Utility pages.** Always noindex, also in a launch build (the launch noindex check skips them), not in `sitemap.xml` or `llms.txt`, not in the PRD-W count of 10 pages.
- **Token timing.** The script waits until 3.5 s after the token arrived before it sends, because the service drops an earlier post silently. It refreshes a token older than 1 hour (the service refuses 2 hours).
- **Tests.** `tests/site/test_form_pages.py` (build rules), `test_contact_form.py` (markup against the service), `test_contact_form_browser.py` (real service with fakes, PRD-W AC1 to AC5, no JavaScript, keyboard, G11, W-G3). The static browser check answers `/form-token` with a stub.
- **Lighthouse.** 100 everywhere, except best practices 96 on the two form pages: the Lighthouse static server has no `/form-token`, so the console shows one 404. The real service answers it.
- **Not verified.** The live Caddy path (POST through the web image and the shared Caddy to the form service on the staging host) and the web image build with the new assets. Check both after the next deploy with `scripts/smoke_staging.py` plus one real submission. The browser matrix (Safari, Firefox) and a screen reader test are open (EXW3).

## EXW2 — EU hosting and deploy

**Objective**: Deploy the EXD5 site and the EXW1 service to the EU host.
**Prerequisites**: EXW1 ✅, EXD5 ✅, EXK0b ✅; open items "PRD-W D1" and "PRD-W D6".
**Rough scope**: static files and the form service behind the reverse proxy on the EXK0b server; TLS and HSTS; staging with a password and noindex; DNS; SPF, DKIM and DMARC; server logs with truncated IP addresses kept 14 days; cost record (≤ $10 per month per region).

### EXW2 database migration step (decided 19 Nov 2026)

**Rule**: migrations run on the server, as part of the application deploy. They never run from CircleCI. `DATABASE_URL` (Neon pooled host) stays in Doppler `prd`. CI holds no production database login (the `ci` config and the `exaktiv_deploy` context hold `APPS_HOST` only).

**Design** (the pattern of the unveilio deploy, `bin/deploy` step 4):
1. The server compose file of the site form has a service `migrate`: same image as the site form, profile `migrate`, `restart: "no"`, command `doppler run --no-fallback -- alembic -c alembic.ini upgrade head`. The image contains `alembic.ini`, `migrations/`, `exaktiv_core` and `exaktiv_site_form`.
2. The deploy script runs it after `pull` and before anything restarts: `compose --profile migrate run --rm -T --no-deps migrate`. On a failure the script exits 1 and restarts nothing. The old containers keep serving.
3. `flock` on the project lock already stops two deploys, so two migrations cannot overlap. Alembic itself has no lock.
4. The migration runs with the pooled Neon settings that EXK0b added (`sqlalchemy_options()`: statement cache off, unique statement names). No session-level features in a revision (`LISTEN`, session advisory locks, `SET`).

**Migration rules** (the old version keeps serving while the migration runs):
- Expand then contract: a revision must work with the previous application version. Drop or rename a column only in a later release, after no running version uses it.
- The deploy never runs `downgrade`. Rolling the application back does not roll the database back.
- One head only. Every revision has a `downgrade()`.
- Before the first production migration, and before any revision that drops or rewrites data, create a Neon branch as a restore point. Record its name and date in the runbook (`deploy/server/README.md`).

**Which deploy script**: the stateless site form image fits the shared `bin/deploy` (images `ghcr.io/vedm1/exaktiv/...`, no volumes or published ports, network `edge`, Caddy route). It already supports a `migrate` service. This needs a second forced-command key (for example `circleci-exaktiv-app`) and `init-deploy-source`, a change of the shared host that needs the user's yes. The MinIO `deploy-infra` stays separate.

**Tests (TDD)**:
| Test | Asserts |
|---|---|
| `test_server_compose_has_a_migrate_service` | service `migrate`, profile `migrate`, `restart: "no"`, same image as the site form, command ends with `upgrade head` |
| `test_migrations_have_one_head_and_every_revision_downgrades` | `ScriptDirectory.get_heads()` has length 1; each revision defines `downgrade()` with a body other than `pass` |
| `test_migrations_run_from_empty_up_down_up` | on a throwaway database: `upgrade head`, `downgrade base`, `upgrade head` |
| `test_failed_migration_stops_the_deploy_before_up` (script test with a fake `docker`) | `migrate` exits 1: no `up`, the live files stay, exit code 1 |
| `test_migrate_runs_after_pull_and_before_up` (script test) | the call order is pull, migrate, up |
| `test_g9_database_url_not_in_ci_config` | `.circleci/config.yml` has no `DATABASE_URL` |

**Done when**: a deploy with a deliberately failing revision left the previous version running. No restore test in EXW2: staging holds test data only (see EXW3). The live Neon check of `alembic upgrade head` was done on 19 Nov 2026.


### EXW2 detailed implementation spec (DRAFT, waits for approval, 19 Nov 2026)

**Decisions taken in the session (19 Nov 2026)**: domain `exaktiv.com`. Deploy through the shared `bin/deploy` (the migrate decision above). Own Caddy container in the stack for Basic Auth, headers, log filter and the form route; the shared Caddy only gets one route block. Images built by CircleCI and pushed to `ghcr.io/vedm1/exaktiv/`. Cost: the EU region is already at the 10 dollar limit (Neon); the domain (about 1 dollar per month) is a recorded overrun, and Brevo must stay on the free plan.

**Probed on the server (read-only, 19 Nov 2026)**: one shared Caddy (`caddy:2`, compose `/opt/stack/caddy`, on network `edge` only, 256 MB, config `/opt/stack/caddy/Caddyfile`, no `conf.d`, no `import` of project files). Project blocks are appended by hand after DNS points, then `caddy reload`. The shared snippet `(app)` logs the full client IP as JSON to Alloy, so the Exaktiv block must not import it. Loki keeps logs 336 h (14 days) for all containers (`loki.yml`). `bin/deploy` policy: no volumes, no ports, no `build`, networks exactly external `edge`, images only under `IMAGE_PREFIX`, `REQUIRE_REVISION_LABEL=yes`, `migrate` service run before `up`. Free: about 4.9 GB RAM, 130 GB disk. A pattern exists for a static Caddy site image behind the shared Caddy (`unveilio-landing`, `auto_https off`, `admin off`, tmpfs, read-only). **Consequence for the earlier answer "own network, Caddy joins it"**: `bin/deploy` allows `edge` only, so this spec uses `edge` with unique aliases `exaktiv-web` and `exaktiv-form`.

#### 1. Slices (one phase = one small PR)

- **EXW2-p1 (repository only, no server change)**: Dockerfiles, web Caddyfile, server compose, CI `build-images` and `deploy-app` jobs, site `base_url`, tests.
- **EXW2-p2 (host, DNS, mail, first deploy)**: shared-host steps (key, `init-deploy-source`, Caddy block, timers), DNS records, Brevo domain, runbook, smoke script, cost record. Independent subagent review of p2 (shared host, key, log filter), because the shared host is root-equivalent and EXK0b's review found 3 critical gaps.

#### 2. Files (repository)

| Path | Content |
|---|---|
| `deploy/site/docker-compose.yml` | Project `exaktiv-site` (REPO_PATH `deploy/site`). Services `web`, `form`, `migrate` (profile `migrate`, `restart: "no"`, command `doppler run --no-fallback -- alembic -c alembic.ini upgrade head`), `jobs` (profile `jobs`). Images `ghcr.io/vedm1/exaktiv/web:${IMAGE_TAG:?}` and `.../site-form:${IMAGE_TAG:?}`. All: `read_only`, `tmpfs`, `cap_drop: [ALL]`, `no-new-privileges`, `init`, `mem_limit` (web 128m, form 256m, migrate 256m, jobs 256m), healthcheck, network `edge` external with aliases. No ports, no volumes. `form` environment: `DOPPLER_TOKEN: ${DOPPLER_TOKEN:?}` only. `web` environment: `SITE_MODE` and `STAGING_BASIC_AUTH_HASH` from the server `.env`. |
| `services/site_form/Dockerfile` | Python 3.12 slim pinned by digest, `uv sync --frozen --package exaktiv-site-form`, contains `alembic.ini`, `migrations/`, `exaktiv_core`, `exaktiv_site_form`; Doppler CLI pinned with checksum (same method as unveilio `web/Dockerfile`); numeric non-root user; labels `org.opencontainers.image.revision` and `source`; command `doppler run --no-fallback -- uvicorn exaktiv_site_form.main:create_default_app --factory --host 0.0.0.0 --port 8000 --no-access-log` (`jobs` overrides the command with `python -m exaktiv_site_form.jobs <name>`). `.dockerignore` excludes `.env*`, `node_modules`, `.git`, tests. |
| `site/Dockerfile`, `site/Caddyfile`, `site/caddy/mode-staging.caddy`, `site/caddy/mode-live.caddy` | `caddy:2-alpine` pinned by the same digest as unveilio. `dist/` copied to `/srv`. `auto_https off`, `admin off`. Headers rendered from `dist/_headers` (see section 4). `import /etc/caddy/mode-{$SITE_MODE}.caddy`: staging has `basic_auth` and `X-Robots-Tag: noindex, nofollow`; live is empty. `/healthz` answers 200 before auth. `/enquiries` and `/form-token` go to `exaktiv-form:8000`; nothing else does (`/health` of the form is not routed). |
| `scripts/render_caddyfile.py` | Reads `site/dist/_headers` and writes the header block into the Caddyfile, so the file and the Caddy config cannot drift. |
| `deploy/site/caddy/exaktiv-site.caddy` | The block the operator appends to the shared Caddyfile (section 5). Not applied by CI. |
| `deploy/site/systemd/exaktiv-site-{retention,retry-mail,purge-hits}.{service,timer}` | Timers (section 6). Installed by root by hand. |
| `deploy/site/README.md` | Runbook: one-time host steps, DNS and mail records, deploy, rollback, staging password change, logs, alert, cost record. |
| `scripts/check_dns.py`, `scripts/smoke_staging.py` | Stdlib checks run by hand (section 7). |
| `.circleci/config.yml` | New jobs `build-images` and `deploy-app` (section 4). |
| `site/site.yaml` | `base_url: https://exaktiv.com`. Mail addresses stay `.invalid` until D6 (domain mailbox) is decided; `--launch` keeps failing on them, which is the EXW3 gate. |

#### 3. Secrets and settings (no value in git, G9)

- Doppler project `exaktiv`, **new config `site_prd`** (least privilege: the form never sees the MinIO keys): `DATABASE_URL` (Neon pooled), `BREVO_API_KEY`, `IP_HASH_SECRET`, `FORM_TOKEN_SECRET`, `MAIL_SENDER_EMAIL`, `MAIL_SENDER_NAME`, `TEAM_INBOX_EMAIL`, `SITE_BASE_URL=https://exaktiv.com`, `TRUSTED_PROXY_HOPS=1`. Its service token goes into `/opt/stack/exaktiv-site/.env` as `DOPPLER_TOKEN` (by you, by hand).
- `/opt/stack/exaktiv-site/.env` (mode 600, by hand) also holds `SITE_MODE=staging` and `STAGING_BASIC_AUTH_HASH` (bcrypt, from `caddy hash-password`). Assumption to probe: a `$` in an env-file value reaches Caddy unchanged. If not, store the hash escaped (`$$`).
- Doppler `ci` config gets `GHCR_PUSH_TOKEN` (write:packages) and `DEPLOY_APP_SSH_FINGERPRINT`. The `exaktiv_deploy` context stays restricted to `main`.
- The deploy user's docker config already holds a read-only GHCR pull token (unveilio pattern). Probe in p2 that it can pull `ghcr.io/vedm1/exaktiv/*`; if not, you add one.

#### 4. CI (`.circleci/config.yml`)

- `build-images` (main only; requires `python, ui, site, secrets, integration`): `scripts/build_site.py` (staging build), then `scripts/render_caddyfile.py`, `docker build` of both images with `--build-arg GIT_SHA=$CIRCLE_SHA1`, image tests (`site/test_image.sh` and `services/site_form/test_image.sh`: non-root, labels, healthcheck present, no `.env` in the image, `--no-access-log` in the command), `docker login ghcr.io` with `GHCR_PUSH_TOKEN`, push tag `:$CIRCLE_SHA1`. No `DATABASE_URL` in the config.
- `deploy-app` (main only; requires `build-images`): `add_ssh_keys` with `DEPLOY_APP_SSH_FINGERPRINT`, then `ssh deploy@$APPS_HOST "$CIRCLE_SHA1"`. The forced command on the host fixes the project to `exaktiv-site`. No-op with a message if `APPS_HOST` is unset.
- Order on the host: `bin/deploy` pulls, checks the revision label equals the SHA, runs `migrate` (a failure stops before anything restarts), then `up -d --wait`.

#### 5. Shared host changes (EXW2-p2, **each needs your yes**; I give the exact commands, you run them)

1. New key pair `~/vultr-keys/circleci-exaktiv-app`. Line in the `deploy` user's `authorized_keys`: `command="/opt/stack/bin/deploy exaktiv-site",no-pty,no-port-forwarding,no-agent-forwarding,no-X11-forwarding ssh-ed25519 ...`.
2. `install -d -o deploy -g deploy /opt/stack/exaktiv-site`, then `init-deploy-source exaktiv-site git@github.com:vedm1/exactiv.git deploy/site ghcr.io/vedm1/exaktiv/` and `--check`. Add the printed public key as a read-only GitHub deploy key (the repository is the same one; one more read-only key).
3. `.env` of section 3.
4. After DNS points at the server and the first deploy is healthy, append to the shared Caddyfile and reload:
   ```
   www.exaktiv.com { redir https://exaktiv.com{uri} permanent }
   exaktiv.com {
   	reverse_proxy exaktiv-web:80 { lb_try_duration 30s }
   }
   ```
   No `import app`, no `log` directive: the shared tier writes no access log for this site. The security headers and the masked access log come from the `web` container.
5. Install the six systemd files and `systemctl enable --now` the three timers.
6. Grafana (shared): one alert rule for the log event `enquiry_mail_failed` of project `exaktiv-site`, to a contact point you choose.

#### 6. Timers and jobs

`ExecStart` (user `deploy`): `/bin/bash -c 'cd /opt/stack/exaktiv-site && IMAGE_TAG=$(cat .current) docker compose --env-file .env --profile jobs run --rm -T --no-deps jobs <name>'`. `retention` daily 03:15 UTC (`Persistent=true`; W-G4), `retry-mail` every minute (`OnUnitActiveSec=1min`), `purge-hits` hourly. `jobs` is not started by `up` (profile). A job failure exits non-zero and shows in `systemctl status`; the log event `enquiry_mail_failed` raises the Grafana alert.

#### 7. Logs, IP truncation, 14 days

- `form`: `--no-access-log`; the EXW1 masking filter stays (G11). The peer of `form` is `web`. `web` sets `servers { trusted_proxies static private_ranges; client_ip_headers X-Forwarded-For }` and sends `header_up X-Forwarded-For {client_ip}`, so the form sees exactly one hop (`TRUSTED_PROXY_HOPS=1`).
- `web` access log to stdout as JSON with a filter: `request>remote_ip` and `request>client_ip` `ip_mask` 24 (IPv4) and 48 (IPv6); delete `request>headers>X-Forwarded-For`, `X-Real-Ip`, `Authorization`, `Cookie`, `Set-Cookie` and the query string. Alloy ships it to Loki; Loki deletes after 336 h (confirmed 19 Nov 2026). Docker json-file rotation stays as set on the host.
- **Residual, to accept or fix**: the shared Caddy writes runtime error logs (for example TLS handshake errors) with the full IP, kept 14 days by the same Loki. The privacy notice says "truncated IP addresses". Decide before EXW3: accept and word the notice ("access logs are truncated; error logs may hold the full address for 14 days"), or ask the host owner to filter.
- **Residual, accepted**: any container on `edge` can reach `exaktiv-form:8000` directly and could set `X-Forwarded-For` to dodge the per-IP limit. Only our own trusted projects share `edge`.

#### 8. DNS and mail (domain `exaktiv.com`; DNS host not stated yet)

| Record | Value | Note |
|---|---|---|
| `A exaktiv.com` | `188.245.25.106` | AAAA only if the host has a public IPv6 (probe in p2) |
| `CNAME www` | `exaktiv.com` | the shared block redirects to the apex |
| `CAA` | `0 issue "letsencrypt.org"` | optional |
| `TXT exaktiv.com` (SPF) | one record: `v=spf1 include:spf.brevo.com <mailbox include> ~all` | Brevo value to confirm in the Brevo UI |
| DKIM | the CNAME or TXT records the Brevo "authenticate domain" page shows | copy from Brevo; not from memory |
| `TXT _dmarc` | start `v=DMARC1; p=none; adkim=s; aspf=s; rua=mailto:<dmarc mailbox>`; change to `p=quarantine` after two clean weeks and before EXW3 | needs the domain mailbox |
| MX, `hello@`, `security@`, DMARC mailbox | from the D6 mailbox decision | **open** |

`scripts/check_dns.py` reads the records with `dig` and prints pass or fail for A, SPF (one record, includes Brevo), DKIM, DMARC.

#### 9. Test plan (TDD, failing first)

| Test | Asserts |
|---|---|
| `test_site_compose_passes_the_shared_policy` | a Python mirror of the `bin/deploy` rules (documented as a copy, with its source) accepts `deploy/site/docker-compose.yml`: no volumes, ports, build, env_file; network exactly `edge` external; images under `ghcr.io/vedm1/exaktiv/` |
| `test_site_compose_policy_rejects_*` (parametrised) | the mirror refuses a port, a volume, root user, `privileged`, a foreign image, `network_mode: host` |
| `test_site_compose_services_are_hardened` | every service: `read_only`, `cap_drop: [ALL]`, `no-new-privileges`, `mem_limit`, healthcheck; aliases are `exaktiv-*` and unique |
| `test_site_compose_has_migrate_and_jobs_profiles` | the migrate tests of the earlier section; `jobs` has profile `jobs` and `restart: "no"` |
| `test_g9_site_compose_holds_only_the_doppler_token` | `form` environment is `DOPPLER_TOKEN` only; no secret name or value in compose, Dockerfiles, units, README, CI |
| `test_web_caddyfile_headers_match_headers_file` | every header in `dist/_headers` is in the rendered Caddyfile with the same value |
| `test_w_g3_web_sets_no_cookie_and_no_third_party` | no `Set-Cookie`; the CSP has no third-party host; no external URL in Caddy files |
| `test_staging_mode_requires_basic_auth_and_noindex` | `mode-staging.caddy` has `basic_auth` and `X-Robots-Tag`; `mode-live.caddy` has neither; `/healthz` is before auth |
| `test_g11_web_log_filter_masks_ip_and_drops_credentials` | rendered log block has `ip_mask` for `remote_ip` and `client_ip`, deletes `Authorization`, `Cookie`, `X-Forwarded-For` |
| `test_web_routes_only_form_paths_to_the_form` | only `/enquiries` and `/form-token` reach `exaktiv-form:8000` |
| `test_shared_caddy_block_has_no_log_and_no_app_import` | `exaktiv-site.caddy` has no `import app` and no `log` |
| `test_w_g4_retention_timer_runs_daily` | the timer file has a daily `OnCalendar` and `Persistent=true`; the service runs `jobs retention`; `retry-mail` every minute; `purge-hits` hourly |
| `test_form_image_command_has_no_access_log` | Dockerfile command has `--no-access-log` and `--factory`; user is numeric non-root; no `.env` copied |
| `test_circleci_has_build_images_and_deploy_app` | both jobs filter to `main`; `deploy-app` requires `build-images`; `build-images` requires all five CI jobs; no `DATABASE_URL`; no unpinned remote script |
| `test_site_base_url_is_the_real_domain` | `site.yaml` `base_url` is `https://exaktiv.com`; canonical and sitemap use it |
| integration (`-m integration`, local Docker) | the built `web` image with a fake form upstream: no password gives 401; password gives 200; `X-Robots-Tag` present; `/enquiries` reaches the upstream with one `X-Forwarded-For` value; the access log line holds the masked address and no `Authorization` |

Existing 47 site tests and the EXW1 tests stay green. Verify: `uv run pytest`, ruff, mypy, `circleci config validate`, `bash -n` and `shellcheck` on scripts, `docker build` of both images.

#### 10. Gating check (EXW2-p2, on the host)

1. `scripts/smoke_staging.py`: no password gives 401; password gives 200 on all 10 pages; `X-Robots-Tag: noindex`; no `Set-Cookie`; all security headers; HTTP redirects to HTTPS; HSTS; TLS 1.2 and later only; `robots.txt` disallows.
2. A real test enquiry through `POST /enquiries`: the row is stored, the team inbox and the sender get mail within 1 minute, the received headers show SPF, DKIM and DMARC pass. This is the first live Brevo send (not tested before).
3. Loki shows an access line with a masked address and no credential header.
4. `systemctl list-timers` lists three timers; `retention` removes a synthetic expired row.
5. The migration rehearsal with a deliberately failing revision runs on the local rehearsal (a copy of `bin/deploy` with `STACK_ROOT` set to a temp directory and a fake `docker`), **not** by committing a failing revision to `main` (a branch is not allowed, and a bad revision on `main` could break a later deploy). The earlier "done when" line is read this way.
6. `docker ps` shows the other projects unchanged (same IDs and uptime). `check_dns.py` is green.

#### 11. Cost (limit 10 dollars per month, EU)

Server share zero. Neon 10 dollars (already the whole limit). Domain about 1 dollar per month: a **recorded overrun, accepted by you on 19 Nov 2026**. Brevo free plan (300 mails per day) must be confirmed against the account. GHCR private storage within the free allowance. Extra RAM about 0.6 GB of the 4.9 GB free.

#### 12. Open items this phase touches

Resolved by this spec: the EXW2 deploy settings row (`TRUSTED_PROXY_HOPS`, timers, `--no-access-log`, alert), the migrate step, PRD-W D1 (exaktiv.com, your answer 19 Nov 2026). Still open and **not closed by EXW2**: D6 domain mailbox (MX, `hello@`, `security@`, DMARC mailbox), Brevo DPA and retention, the 6-month deletion of the team mailbox copy, the shared-Caddy error-log IP question, the Neon restore test (EXW3).

#### Implementation notes (EXW2, 19 Nov 2026)

Built as ONE phase (the user's decision), repository side. **Not closed**: the host steps, DNS, mail and first live deploy are in `deploy/site/README.md` and wait for the user.

- **Port**: `web` listens on 8080, not 80 (no capability needed). The shared Caddy block proxies `exaktiv-web:8080`.
- **Headers**: `scripts/render_caddyfile.py` takes `build_site.HEADERS` (the dict that writes `_headers`), not the generated file. One source, and the unit tests need no built `dist/`.
- **Found by running the image with `cap_drop: [ALL]`**: the official Caddy binary has a file capability, and the kernel then refuses to start it ("operation not permitted"). `site/Dockerfile` copies the binary (`cp` drops the capability). A unit test and the integration test hold this.
- **`jobs` uses `entrypoint`, not `command`**: `docker compose run ... jobs <name>` replaces `command`, so the job name would have been lost.
- **Probed**: `docker compose config` prints a `$` in an env value as `$$`, but the container gets the single `$`. The bcrypt hash in the server `.env` works unchanged (single-quoted).
- **Probed**: Caddy 2.11.4 accepts the log filters (`ip_mask`, `delete`, `regexp`). The integration test (`tests/integration/test_site_web_image.py`, real image, read-only, all capabilities dropped, fake upstream) proves: 401 without the password, 200 with it, noindex only in staging, every header of `build_site.HEADERS`, `/healthz` open, one `X-Forwarded-For` value reaches the form and no `Authorization`, only two paths reach the form, the log line holds `203.0.113.0` and no query string, credential or full address.
- **Network**: `edge` (bin/deploy allows nothing else). This replaced the "own network" answer once the migrate decision pointed at `bin/deploy`.
- **Local builds**: an amd64 Caddy under emulation on Apple silicon crashes. Build native images locally; CI builds amd64 natively.
- **Deploy key fingerprint** (19 Nov 2026): `deploy-app` uses `SHA256:WfZbao8U9HSoOjcTZcN7d/I0y53qIgb+7dN9Xsqz6Vk` (`circleci-exaktiv-app`). The key must be added to CircleCI before the first push to `main`, or the job fails at `add_ssh_keys`. `build-images` stops without pushing when `GHCR_PUSH_TOKEN` is missing, and `deploy-app` then skips.
- **Mirror of the host policy**: `tests/unit/test_site_compose.py` copies the jq rules of `bin/deploy` (unveilio repository, read 19 Nov 2026). It must follow that script.
- **Independent review (19 Nov 2026, subagent, no critical finding)**. Fixed: systemd `TimeoutStartSec=300` and a retention retry (a hung call blocked all later runs); `cpus: 0.5` and `pids_limit: 200` (bcrypt attempts on a shared host); tmpfs owned by uid 10001; `deploy-app` stops when `GHCR_PUSH_TOKEN` is missing and when a newer commit is on `main` (out-of-order pipelines could roll the site back); weak tests replaced (smoke test with no password wall, the vacuous fingerprint assertion, the directive-order assertion) and three integration tests added (empty hash, unknown `SITE_MODE`, a 502 log line). Documented, not fixable here: the shared Caddy error log keeps the full address (PRD-W §8.2 not met for those lines), the `GHCR_PUSH_TOKEN` scope, and the alias gap in the shared `bin/deploy`.
- **Not tested here**: a live deploy through `bin/deploy`, the shared Caddy block and certificate, the systemd timers (quoting of `$$`), a live Brevo send, DNS, the Grafana alert, the GHCR pull from the host, the migrate service against Neon from inside the image (the image test only proves the imports and the fail-closed start).
- **Closed 19 Nov 2026 (live checks done by the user, read by Claude)**: first deploy healthy, other projects unchanged; timers installed and each job run by hand; shared Caddy block and certificate; `smoke_staging.py` all PASS; `check_dns.py` all PASS; real test enquiries stored, mail delivered, DKIM/SPF/DMARC PASS; web access log masked for a real request; Grafana data source `Exaktiv site logs` and the mail-failure alert. **Found live, not by tests**: the first `build-images` push was refused once (rerun passed); Brevo refused the host IP until it was added to the authorised IPs (`401`); Brevo domain authentication was missing (DKIM signed by `brevosend.com`, DMARC fail) until the records were verified; `MAIL_SENDER_NAME` had a typo; Brevo injects a tracking pixel and has no per-message switch; Alloy does not capture the short-lived `jobs` containers and makes one Loki tenant per compose project. **Not done**: the failing-migration rehearsal (the spec's gating check 5; the shared `bin/deploy` is owned by the unveilio repository and stops before `up` by design); the migrate service ran only as a no-op at head.

## EXW3 — Launch gate

**Objective**: Prove that the site meets every PRD-W launch rule, then make it public.
**Prerequisites**: EXW2 ✅, EXW1-ui ✅; open items "claims evidence", "lawyer review" and "employment contract check".
**Rough scope**: the PRD-W §11 definition of done on staging; every claim in the register "Ready" with its evidence; the lawyer review and the employment check recorded in the build plan; the EXD5 browser and Lighthouse checks green on staging; one Neon restore test (create a Neon branch from a point in time, read one known row, delete the branch, record the date and the result in `deploy/server/README.md`) before the staging password is removed, because the first real enquiries (personal data that cannot be recreated) arrive after that; then remove the staging password.
**Gating check**: an independent subagent review of the definition of done (W-G1, W-G2, W-G3).

### EXW3 Implementation notes (19 Nov 2026, build done, site not live)

- **Decisions of the user, 19 Nov 2026.** The legacy analyser does not exist (it needs to be built: see `docs/prd/PRD-L-exaktiv-legacy-analyser.md`). `hello@` and `security@` exist. Registered address Nyati Meadows, Pune, India 411014. The company name stands on one privacy-notice line and nowhere else (W-G5 rewritten in `CLAUDE.md`, build gate `check_company_name`, no footer, no `legalName`, no `llms.txt` line). No person is named. Employment contract risk accepted. Brevo DPA signed. The privacy notice wording was reviewed by the user. DMARC, the name list, the go-live yes and the Neon restore test are the user's steps.
- **Built.** `ready()` helper: a page shows an unevidenced sentence only while its claim is `ready` (`{% if ready(id) %}`), so launch builds pass and pages upgrade themselves. Four claims are off the pages (`findings-sourced`, `in-region`, `no-training`, `nda-dpa`). Four why-now claims are `ready` after a date check (`docs/evidence/why-now-dates.md`; the NIS2 text was narrowed to its source, the AI Act source changed to a post-adoption page). Three claims have drafts (`human-approval` complete and waiting for the owner; `access-logged` and `retention` need real mechanisms). `site/launch.flag` + `scripts/build_site_for_image.py` (launch build in CI only with the flag, the name list from Doppler `SITE_NAMES_B64` with at least 3 names, and a complete record). `scripts/check_launch_record.py` and `docs/launch/EXW3-record.yaml` (16 items). `check_dns.py --launch` (DMARC quarantine or reject). `scheduler` container replaces the systemd timers (retention freshness is now visible to Alloy; two Grafana rules in `deploy/site/README.md`). Go-live and rollback runbook, mailbox Vault rule and Neon restore steps in the READMEs.
- **Independent review (subagent, 19 Nov 2026).** W-G3: no finding. W-G1 and W-G5: no finding. **Fixed:** the gate bypass (SITE_MODE=live with a staging build): the launch build writes `.launch-built`, and `site/entrypoint.sh` refuses live mode without it (tested in the image); a one-line name list is refused; implied claims reworded or hidden (home description, "traceable", "line by line", Product Data "designed to", "tests that compare", "region to set up", "approvals in writing", Security h1, lead and CTA, empty Security section, the finding sample now needs `findings-sourced`); NIS2 "several member states"; the privacy notice now names the browser headers in the access log and the 1 hour IP hash for spam limits. **Not fixed, for the user:** see the final report of this session (home title and h1 "AI you can audit", Team "Past work" lines, Brevo "anonymous" tracking and its legal basis, Art. 49(1)(b) basis, the residential-looking address, C2PA metadata in brand PNGs, the record is self-attested: protect `main`, `docs/launch` and `site/launch.flag` with a review).
- **Verified.** 454 unit and site tests, ruff, mypy, brand check, Lighthouse 96 to 100 on all 12 pages, the web image test (`site/test_image.sh`) and the 10 image integration tests, native build. **Not verified:** the scheduler against the live database and Brevo, the CI launch build in CircleCI (needs the Doppler variable), and every human item in the record.

## EXW4 — Legal notice and analytics

**Objective**: Add the PRD-W phase 2 items.
**Prerequisites**: EXW3 ✅; open item "first client contract close".
**Rough scope**: legal notice (Impressum) under § 5 DDG for Valyrian Tech Pvt Ltd (legal form, registered address, authorised representatives, register entry); cookie-free analytics hosted in the EU; privacy notice update for the analytics.
