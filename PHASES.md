# PHASES.md — Exaktiv Build Tracker

One row per phase. Flip 🔲 → ✅ when the phase is complete (all tests green, docs updated, PR merged).
Prefixes: **EXK** = core engine, **EXC** = Exaktiv Claims, **EXP** = Exaktiv Product Data.

| Phase | Name | Status | Summary |
|-------|------|--------|---------|
| **EXK0** | Foundation | 🔲 Planned | Monorepo layout, uv + pnpm workspaces, docker-compose (Postgres 16, MinIO, Temporal), GitHub Actions CI (ruff, mypy, pytest, eslint, vitest, secret scan, licence check), one smoke test end to end. |
| **EXK0b** | EU host (Hetzner) | 🔲 Planned | Deploy the compose stack to Hetzner Germany. Secrets mechanism, backups, firewall. Server cost ≤ $10 per month. |
| **EXK0c** | India host | 🔲 Planned | Deploy to the India provider chosen in the open items. Server cost ≤ $10 per month. Required for A-G2 before any pilot. |
| **EXK1** | Ingestion, storage, event log | 🔲 Planned | Tenants, jobs, files with SHA-256, page split, normalised page images, size limit, append-only event log for every state change. |
| **EXK2** | Model gateway and router | 🔲 Planned | LiteLLM (pinned digest) as the one gateway; cost/latency/token log per call; versioned routes; region check with no fallback (G7). |
| **EXK3** | Extraction contract | 🔲 Planned | Value record (FR-EXT-3) with source metadata; values without a source are dropped and the field marked "not found" (G1). |
| **EXK4** | Validation layer | 🔲 Planned | Schema and domain validation from versioned `config/`; failures go to review with a reason (G3, G4). |
| **EXK5** | Confidence and abstention | 🔲 Planned | Confidence score, per-field thresholds, "always review" fields, 200-review rule, calibration version (G2). |
| **EXK6** | Review queue backend | 🔲 Planned | Review tasks per tenant, accept/correct/not-present actions with audit, job completion rule (FR-REV-5), product screen extension points. |
| **EXK6-ui** | Core reviewer UI | 🔲 Planned | Keyboard-first review screen with source crop, Personal Design System tokens, dark default. Target ≤ 8 s per simple field. |
| **EXK7** | Evaluation harness | 🔲 Planned | Pipeline vs frontier baseline on a frozen set; per-field precision, recall, exact match, abstention, cost, latency; hard subset; HTML + JSON report. |
| **EXK8** | Evidence pack (Exaktiv Proof) | 🔲 Planned | Evidence pack per job (PDF + JSON) from the event log, with source crops per value. |
| **EXK9-p1** | Corrections store and training sets | 🔲 Planned | Labelled examples per tenant and task; training sets with a frozen evaluation split; consent flag for cross-tenant use. |
| **EXK9-p2** | Model registry and regression gate | 🔲 Planned | Versioned models, adapters, prompts and routes; promotion only with a passed gate record (G10); one-step rollback. |
| **EXK9-p3** | LoRA adapter pipeline | 🔲 Planned | Train a private LoRA adapter per tenant and task on an Apache/MIT base model; register through the gate. |
| **EXK10** | Metering and usage export | 🔲 Planned | Accepted units per tenant per month, count once, monthly export, reconcile with job records (G5). |
| **EXK11** | Public API | 🔲 Planned | REST API (create job, upload, status, results, evidence pack), webhook on completion, API keys with scopes per tenant (G6). |
| **EXC1** | Claims schema and config | 🔲 Planned | 12 document types, field definitions (PRD-A §6.1) and value rules as versioned configuration. |
| **EXC2** | Claims test set | 🔲 Planned | 300–500 synthetic and volunteer-handwritten documents in 40–60 claim files (EN, HI, KN), answer key, source notes. |
| **EXC3** | Page classification | 🔲 Planned | Classify pages into the 12 document types. Gate: 95% or more on the test set. |
| **EXC4** | Field extraction | 🔲 Planned | Field extraction per document type through the core contract. |
| **EXC4b** | Identifier masking | 🔲 Planned | Mask Aadhaar, PAN, bank account and phone numbers on ingest in images and text (A-G4). |
| **EXC5** | Cross-document checks | 🔲 Planned | Checks X1–X10 with pass/fail/cannot-check and source values; flags state facts only; policy rules from tenant configuration (A-G3). |
| **EXC6** | Case summary | 🔲 Planned | Case summary model and PDF with source links and "draft" watermark. |
| **EXC6-ui** | Case view | 🔲 Planned | Page thumbnails, case summary, filtered field queue; mouse-free completion. |
| **EXC7** | Claims benchmark | 🔲 Planned | Pipeline vs Gemini Flash (India region): overall, printed and handwritten accuracy, cost and time per file. |
| **EXC7b** | Handwriting LoRA | 🔲 Planned | Handwriting fine-tune through EXK9-p3. Gate: demo pass rule (PRD-A §9). |
| **EXC8** | Claims evidence pack | 🔲 Planned | Core evidence pack plus IRDAI / DPDP / FREE-AI mapping page (template). |
| **EXC9** | Pilot hardening | 🔲 Planned | Tenant set-up, India deployment, access roles, retention and deletion; ISO 27001 work started. |
| **EXP1** | ETIM 10 model | 🔲 Planned | Load ETIM 10 electrical classes, features, value lists and units as versioned configuration; code and unit validation (B-G1). |
| **EXP2** | Product Data test set | 🔲 Planned | 500 SKUs from 10+ suppliers and 20+ classes with an answer key checked against datasheets. |
| **EXP3** | ETIM classification | 🔲 Planned | Top 3 classes with confidence; low confidence to review; class change re-runs extraction. |
| **EXP4** | Feature extraction | 🔲 Planned | Features from tables, text and drawings; unit conversion with original kept; value-code mapping; variant split by article number. |
| **EXP5** | Pool check and export | 🔲 Planned | Pool check rules (versioned), ETIM xChange and BMEcat export; "accepted" only after pool pass (B-G3). |
| **EXP5-ui** | SKU and family views | 🔲 Planned | SKU view, family view, bulk accept across variants. |
| **EXP6** | Benchmark and quality report | 🔲 Planned | Batch quality report and benchmark; free-fill test for prospects on the EU host. Gate: 30-day test pass rule (PRD-B1 §9). |
| **EXP7** | ETIM upkeep | 🔲 Planned | Version-change mapping with official change files; work report before start. |
| **EXP8** | ECLASS support | 🔲 Planned | ECLASS (v1.1). Starts only after 3 paying suppliers. |

<!-- deps
EXK0: -
EXK0b: EXK0
EXK0c: EXK0
EXK1: EXK0
EXK2: EXK0
EXK3: EXK1, EXK2
EXK4: EXK3
EXK5: EXK4
EXK6: EXK5
EXK6-ui: EXK6
EXK7: EXK5
EXK8: EXK6
EXK9-p1: EXK6
EXK9-p2: EXK7
EXK9-p3: EXK9-p1, EXK9-p2
EXK10: EXK6
EXK11: EXK6
EXC1: EXK4
EXC2: EXC1
EXC3: EXC1, EXK3
EXC4: EXC3, EXK5
EXC4b: EXC4
EXC5: EXC4
EXC6: EXC5, EXK6
EXC6-ui: EXC6, EXK6-ui
EXC7: EXC2, EXC4, EXK7
EXC7b: EXC7, EXK9-p3
EXC8: EXK8, EXC6
EXC9: EXK0c, EXC4b, EXC8, EXK10, EXK11
EXP1: EXK4
EXP2: EXP1
EXP3: EXP1, EXK3
EXP4: EXP3, EXK5
EXP5: EXP4
EXP5-ui: EXP4, EXK6-ui
EXP6: EXP2, EXP5, EXP5-ui, EXK7, EXK0b
EXP7: EXP6
EXP8: EXP6
-->

---

## Gate Dependencies

```
EXK0 ─┬→ EXK1 ─┐
      ├→ EXK2 ─┴→ EXK3 → EXK4 → EXK5 ─┬→ EXK6 ─┬→ EXK6-ui
      ├→ EXK0b (EU host)              │        ├→ EXK8
      └→ EXK0c (India host)           │        ├→ EXK9-p1 ─┐
                                      │        ├→ EXK10    ├→ EXK9-p3
                                      │        └→ EXK11    │
                                      └→ EXK7 → EXK9-p2 ───┘

Claims:   EXK4 → EXC1 → EXC2 ─────────────────┐
                 EXC1 → EXC3 → EXC4 → EXC5 → EXC6 → EXC6-ui
                               EXC4 → EXC4b    └→ EXC8 → EXC9
                               EXC4 + EXC2 + EXK7 → EXC7 → EXC7b (needs EXK9-p3)

Product:  EXK4 → EXP1 → EXP2 ─────────────────┐
                 EXP1 → EXP3 → EXP4 → EXP5 ───┼→ EXP6 → EXP7, EXP8
                               EXP4 → EXP5-ui ┘  (EXP6 also needs EXK7, EXK0b)
```

- **EXK2 before EXK3:** no model call may reach any data before the region check (G7) is in place and tested.
- **EXK4 before EXK5 and before any product schema:** a value must be valid before it gets a confidence. A product schema is configuration that the EXK4 loader reads.
- **EXK5 gates any auto-accept.** Before EXK5, every value goes to review.
- **EXK7 before EXK9-p2:** the regression gate compares against the frozen set and report format that EXK7 defines.
- **Claims and Product Data run in parallel after EXK5.** Their first phases (EXC1, EXP1) need only EXK4.
- **EXC9 needs EXK0c:** no pilot with real medical records before the India host exists (A-G2, A-G5).
- **EXP6 needs EXK0b:** the free-fill test uses prospect data, so it runs on the EU host, not on a laptop.

---

## What "Complete" Means Per Phase

**EXK0**: `docker compose up -d` starts Postgres 16, MinIO and Temporal locally. `uv run pytest`, `uv run ruff check`, `uv run mypy`, `pnpm test`, `pnpm lint` and `pnpm typecheck` pass locally and in CI. The CI secret scan fails on a planted test secret. The smoke test sends one Temporal workflow that writes one row to Postgres and one object to MinIO. `LICENCES.md` exists.

**EXK0b**: The stack runs on a Hetzner Germany server. The monthly server cost is recorded and is ≤ $10. Secrets come from the chosen secret store, not from files in git. A backup restore was tested once.

**EXK0c**: As EXK0b, on the India provider. The provider and its data-location terms are recorded in the build plan.

**EXK1**: Upload of a PDF, JPEG, PNG, HEIC, TIFF, CSV, XLSX and BMEcat file creates a job. Each file has a SHA-256, tenant ID, upload time and uploader. PDF and image files split into pages with a normalised image; the original stays unchanged. A file above the tenant limit is rejected with a reason. Each state change writes one append-only event; an update or delete on the event table fails.

**EXK2**: All model calls go through LiteLLM. Each call logs model, cost, latency and tokens, with no personal data (G11). A route lookup for a tenant in region A to a model in region B fails and creates no call (G7 test). An endpoint failure retries once, then marks the task "failed".

**EXK3**: A value record has every FR-EXT-3 field. The G1 test passes: a model output without a location stores nothing and marks the field "not found".

**EXK4**: Rules load from versioned files in `config/`. The G4 test passes: an invalid unit or code is rejected with a reason and creates a review task. No threshold or rule string appears in a prompt file (a CI grep check).

**EXK5**: The G2 test passes. A field with fewer than 200 reviewed values sends every value to review. Each auto-accept record stores the calibration version.
