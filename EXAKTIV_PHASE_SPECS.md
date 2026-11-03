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

Reviewer UI and HTML reports use the Personal Design System: teal accent, Inter + Lora + JetBrains Mono, dark default with a light mirror, chevron mark. Tokens live in `ui/src/tokens/`.

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
**Rough scope**: Server, firewall, compose deploy, secrets store, Postgres backups with one tested restore, cost record.

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
**Prerequisites**: EXK6 ✅.
**Rough scope**: Queue list, field review with marked page area, keyboard map, tokens. Target ≤ 8 s median per simple field; open in < 1 s.

## EXK7 — Evaluation harness

**Objective**: Compare the pipeline with a frontier baseline on a frozen set.
**Prerequisites**: EXK5 ✅.
**Rough scope**: Frozen set format, runner, per-field metrics, hard subset, cost per unit, HTML + JSON report in the design system.

## EXK8 — Evidence pack (Exaktiv Proof)

**Objective**: Export a per-job evidence pack (PDF + JSON) from the event log.
**Prerequisites**: EXK6 ✅.
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
**Prerequisites**: EXC5 ✅, EXK6 ✅.

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
