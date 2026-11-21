# LICENCES.md — Models and datasets (G12)

Record each model and dataset here before first use. Base models: Apache 2.0 or MIT only.

## Models

| Model | Version | Licence | Source URL | Checked on |
|-------|---------|---------|------------|------------|

## Fonts (brand package)

| Font | Version | Licence | Source URL | Used for | Checked on |
|------|---------|---------|------------|----------|------------|
| Young Serif | Fontsource 5.3.0 | SIL OFL 1.1 (`brand/fonts/OFL-young-serif.txt`) | https://fonts.google.com/specimen/Young+Serif | Wordmark, headings | 18 Nov 2026 |
| Instrument Sans | Fontsource 5.3.0 | SIL OFL 1.1 (`brand/fonts/OFL-instrument-sans.txt`) | https://fonts.google.com/specimen/Instrument+Sans | Body, UI | 18 Nov 2026 |
| Gelasio | Fontsource 5.3.0 | SIL OFL 1.1 (`brand/fonts/OFL-gelasio.txt`) | https://fonts.google.com/specimen/Gelasio | Citations | 18 Nov 2026 |

## Infrastructure software (container images)

| Component | Version | Licence | Source | Image (pinned by digest) | Use | Checked on |
|-----------|---------|---------|--------|--------------------------|-----|------------|
| MinIO (S3-compatible object storage) | RELEASE.2026-10-23 | AGPL-3.0 | https://github.com/minio/minio (the official image is no longer public; built by Chainguard) | `cgr.dev/chainguard/minio:latest@sha256:3c60a2a8c4d33409a9bc7a623a7fcbfb4605adc3d89422d2f53b3f673a6e5597` | Internal object storage. Unmodified. Bound to 127.0.0.1 on the EU server (`deploy/server/docker-compose.yml`) and to localhost in development. Not offered to any user over a network. | 19 Nov 2026 |
| Caddy (web server of the site image) | 2.11.4 | Apache-2.0 | https://github.com/caddyserver/caddy | `caddy:2-alpine@sha256:6aeddd44c3078b0f9a35206472a11420648a79c184603ef95957d0a20044cb2b` | Serves the static site behind the shared Caddy (`site/Dockerfile`). Unmodified. | 19 Nov 2026 |
| Doppler CLI | 3.76.6 | Apache-2.0 (upstream `LICENSE`, read 19 Nov 2026) | https://github.com/DopplerHQ/cli | package pinned by SHA-256 in `services/site_form/doppler-cli.sha256` | Hands secrets to the form service at start (`doppler run`). Unmodified. | 19 Nov 2026 |

## Python libraries of note

| Library | Version | Licence | Source | Use | Checked on |
|---------|---------|---------|--------|-----|------------|
| DBOS Transact | 3.6.0 | MIT | https://github.com/dbos-inc/dbos-transact-py | Workflow engine in `services/worker`. State in our Postgres (schema `dbos`). No Conductor, no cloud service. | 20 Nov 2026 |
| psycopg and psycopg-binary | 3.3.9 | LGPL-3.0-only | https://github.com/psycopg/psycopg | Required by DBOS (and used by `/health`). Unmodified, used as a library through import, not distributed. Exception in `config/licence_exceptions.yaml`. | 20 Nov 2026 |
| tree-sitter and tree-sitter-java | 0.26.1 and 0.23.5 | MIT (per upstream package metadata; LICENSE files not re-read) | https://github.com/tree-sitter/tree-sitter | EXL2 probe only (git-ignored, not in the workspace). EXL3 records the licence check before use in a product package. | 20 Nov 2026 |
| anthropic (Python SDK) | 2.12.0 | MIT (per package metadata; LICENSE not re-read) | https://github.com/anthropics/anthropic-sdk-python | EXL2 probe only. | 20 Nov 2026 |
| scip-java image | `sha256:2ad40207…e372ee618` | Apache-2.0 per PRD-L §5 (upstream LICENSE not read in EXL2) | https://github.com/sourcegraph/scip-java | EXL2 spike only (failed). EXL3 checks the licence before any use. | 20 Nov 2026 |

AGPL-3.0 note: Exaktiv runs MinIO unmodified for its own internal use. It does not distribute MinIO and does not offer it as a network service to others. If we ever modify MinIO, or expose it to customers, record a new review here first.

## Datasets

| Dataset | Version | Licence | Source URL | Used for | Checked on |
|---------|---------|---------|------------|----------|------------|
| Spring PetClinic | commit `500158f` (main, 20 Nov 2026) | Apache-2.0 (upstream `LICENSE.txt`, read 20 Nov 2026) | https://github.com/spring-projects/spring-petclinic | Legacy analyser smoke test for a modern build and the SCIP path (EXL1, EXL3). Test input only, never training data. | 20 Nov 2026 |
| Apache OFBiz (subset of about 100,000 lines) | commit `9e79def` (trunk, 20 Nov 2026) | Apache-2.0 (upstream `LICENSE`, read 20 Nov 2026); the `NOTICE` file travels with the subset | https://github.com/apache/ofbiz-framework | Legacy analyser cost and time per thousand lines on a real ERP code base (EXL1, EXL2). Test input only, never training data. | 20 Nov 2026 |
| Large public code base, toward 5 million lines | not chosen | not recorded | choose in EXL8 | Legacy analyser scale test. Record the licence before first use (G12). | not checked |
| One public C# or C++ project | not chosen | not recorded | choose in EXL11 | Second language pack. Record the licence before first use (G12). | not checked |
