# CLAUDE.md — Exaktiv Development Rules

Read this file before you touch code. These rules are non-negotiable guardrails, not style preferences.
The product requirements are in `docs/prd/` (read `PRD-00-exaktiv-core.md` first). The tracker is `PHASES.md`.

**Response language:** write all responses in ASD-STE100 (Simplified Technical English). Code, commands and paths stay as they are.

## Process rules

- **Think before coding.** Read the phase spec, the build plan and the existing modules first. If you do not, you build a second copy of something that already exists.
- **Surgical changes.** Touch only what the current phase needs. Large mixed diffs hide guardrail breaks.
- **TDD.** Write the failing test first. Each guardrail has a test (column "How to check" below). A guardrail without a test is not in force.
- **Document what you create.** Update the tracker docs in the same session as the code. Drifted docs make the next session start from a false premise.
- **One phase = one small PR.** If scope grows, stop. Slice the phase (`-p1`, `-p2`) or add a new phase row.
- **No build on an unconfirmed assumption.** Probe the real API, file or format. Record the result in the spec "Implementation notes". Open items live in `EXAKTIV_BUILD_PLAN.md`.

## Stack (decided 4 Nov 2026)

| Item | Decision |
|---|---|
| Repository | Monorepo: `services/api` (FastAPI), `services/worker` (Temporal workers), `model/` (model service, gateway client, training), `ui/` (React + TypeScript), `config/` (versioned schemas, rules, value lists), `docs/prd/` |
| Backend language | Python 3.12 only. Kotlin is **not** in the stack. |
| Workflows | Temporal (Python SDK). No Kafka in v1. |
| Model gateway | LiteLLM, image pinned by digest. Never a floating tag. |
| Fine-tuning | PEFT/LoRA on an Apache 2.0 or MIT base model only. |
| Datastore | PostgreSQL 16+ (Neon Frankfurt for EU; local Docker for development). Object storage: S3-compatible (MinIO locally and on the EU server). |
| UI | React + TypeScript, Exaktiv brand package tokens and components (`brand/`, phases EXD1 to EXD5). |
| Hosting | Local docker-compose first. EU: Hetzner Germany (EXK0b). India: provider to choose (EXK0c). **Server cost limit: $10 per month per region.** Model API and GPU costs are tracked separately. |
| Commands | Python: `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`. UI: `pnpm test`, `pnpm lint`, `pnpm typecheck`. Stack: `docker compose up -d`. |

## The 13 core guardrails (PRD-00 §6)

| ID | Guardrail | How to check |
|---|---|---|
| G1 | **No value without a source.** Every stored value carries file ID, page, location (bbox or text span), model ID and version. Else the engine drops it and marks the field "not found". | Test: model output without location → nothing stored. |
| G2 | **Abstain, do not guess.** Below threshold or after a validation failure, the value goes to review. Never a default or an estimate. | Test: low-confidence value → review task, no accepted value. |
| G3 | **Rules in code, not in prompts.** Thresholds, validation rules, business rules and value lists live in code or in `config/`. Prompts only ask for extraction. | Code review: no threshold or rule in a prompt file. |
| G4 | **Validate before storage.** Every model output passes schema and domain validation before it becomes a candidate. | Test: invalid unit or code → rejection with a reason. |
| G5 | **Bill only accepted units.** | Test: a job with open review tasks counts zero units. |
| G6 | **Tenant isolation.** Data, adapters, corrections and eval sets never cross tenants. Every table with tenant data has `tenant_id`, and every query filters on it. | Integration test: tenant A key cannot read tenant B data. |
| G7 | **Region stays fixed.** Files, values and model calls stay in the tenant's region. No fallback to another region. | Router test: region mismatch → failure, not fallback. |
| G8 | **No real customer data in development.** Synthetic or public data only. No data from a past employer of the founders. | Every fixture has a source note. Pre-commit check. |
| G9 | **Secrets in the secret store only.** Never in git, a prompt or a log. | Secret scan in CI. |
| G10 | **Release gate.** No model, adapter, prompt or route change goes live without a passed regression gate record. | Registry refuses promotion without a gate record. |
| G11 | **Personal data minimisation.** Mask names, IDs and phone numbers in logs and metrics. | Log-scan test with synthetic personal data. |
| G12 | **Licences.** Base models Apache 2.0 or MIT only. Record each dataset licence before use in `LICENCES.md`. | CI licence check. |
| G13 | **Human approval before any external action.** No submit, publish or decision without an approval record. | No external call path without an approval record. |

## Claims guardrails (PRD-A §7)

- **A-G1** No claim decision by the system. No API or UI path writes approve, reject or a payable amount.
- **A-G2** India only. All claim data, page images, model calls and logs stay in the India region.
- **A-G3** Policy rules (room-rent limit, waiting periods, co-pay, windows) come from tenant policy configuration, never from a model.
- **A-G4** Aadhaar, PAN, bank account and phone numbers are masked on ingest in images and text. Aadhaar is never stored unmasked.
- **A-G5** No real medical records before a signed pilot.
- **A-G6** ICD-10 codes are "suggested" until a human confirms them.

## Product Data guardrails (PRD-B1 §7)

- **B-G1** Every value code and unit comes from the loaded ETIM model version. The model never makes a new code.
- **B-G2** The supplier's datasheet is the source of truth. Not the web, not model memory. Not in the documents → "not found".
- **B-G3** A SKU is "accepted" (billable, deliverable) only after it passes the target pool check.
- **B-G4** The supplier approves before any upload to a pool.
- **B-G5** One supplier's values never fill another supplier's SKUs.

## Website guardrails (PRD-W §2, §6)

- **W-G1** No personal, employer or client names on the site, including metadata, file names and alt text. Grep check with a name list kept outside the repository.
- **W-G2** No claim without evidence. A claim appears only when its PRD-W claims register status is "Ready". The EXD5 build fails on a banned claim.
- **W-G3** No cookies and no requests to third-party domains on any page. Browser check in EXD5 and EXW3.
- **W-G4** Form submissions are stored in the EU region only and deleted after 6 months. Unit tests for region and retention (EXW1).
- **W-G5** Legal pages name Valyrian Tech Pvt Ltd and no person.

## Single source of record per field

| Data | Authoritative source | Cross-check |
|---|---|---|
| Input file content | Object storage original, by SHA-256 | Hash checked on every read |
| Extracted value (candidate) | Engine value store, with model metadata | Validation rules |
| Accepted value | Review action record, or auto-accept record with calibration version | Evidence log |
| Validation rules and value lists | Versioned files in `config/` | Unit tests per rule |
| Model and route versions | Model registry | Gate record |
| Usage for billing | Metering table (accepted units only) | Monthly reconcile with job completion records |
| Tenant region | Tenant configuration | Router check on every call |
| Every state change | Append-only event log (from EXK1) | Evidence pack (EXK8) |

## Design system (UI, reports, PDFs, website)

Use the Exaktiv brand package in `brand/` as the only source of truth. Read `brand/README.md` before UI, report or page work. The Personal Design System is retired: no teal, Inter, Lora, JetBrains Mono or chevron mark.

- **Colour has a job.** Cobalt `--ex-source` = source (footnotes, citations, links, focus). Vermilion `--ex-act` = act (one primary button per screen, Ink text on it). Marker `--ex-evidence` = evidence band behind backed words only.
- **Role tokens only.** Components use `--ex-*` role tokens (or `ex.*` from `tokens.ts`). No hex values, no `--ex-raw-*` tokens, radius 0, no shadows, no blur.
- **Type.** Young Serif (400 only) for headings, Instrument Sans for body and UI, Gelasio italic for citations. No monospace anywhere. Set `font-synthesis: none`. Use tabular figures only in tables and line numbers.
- **No kickers.** No uppercase labels, tags or section numbers above a heading.
- **The Trace.** A footnote number appears only when the claim has a source (G1 applied to the UI and the website).
- **Change tokens** in `brand/tokens/tokens.css` only, then run `python3 brand/tokens/build_tokens.py`. `python3 brand/tokens/check_brand.py` must pass before a commit (CI gate from EXD2).

## Quality bar for high-stakes work

These phases need an independent subagent review before "done": EXK2 (region), EXK3 (G1), EXK4 (G3/G4), EXK5 (G2), EXK9-p2 (G10), EXK10 (G5), EXK11 (G6), EXC4b (A-G4), EXC5 (A-G3), EXC9, EXP5 (B-G3), EXW1 (W-G4), EXW3 (W-G1, W-G2, W-G3).
