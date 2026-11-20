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
| Repository | Monorepo: `services/api` (FastAPI), `services/worker` (DBOS workflows), `model/` (model service, gateway client, training), `ui/` (React + TypeScript), `config/` (versioned schemas, rules, value lists), `docs/prd/` |
| Backend language | Python 3.12 only. Kotlin is **not** in the stack. |
| Workflows | DBOS Transact (Python library, MIT, state in Postgres), decided 20 Nov 2026. Replaces Temporal. No Kafka in v1. |
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
- **W-G5** The company name Valyrian Tech Pvt Ltd stands once, in the controller sentence of the privacy notice, and nowhere else on the site (no footer, no schema.org `legalName`, no `llms.txt` line). No person is named. The build fails on any other mention (`check_company_name`). Changed 19 Nov 2026 (user decision); EXW4 adds the legal notice.

## Legacy Analyser guardrails (PRD-L §11)

PRD-L §11 is the source. These rows copy it; `tests/guardrails/test_exl0_legacy_guardrails.py` fails if they differ. Source of record additions: PRD-L §12. Decisions and accepted risks: `docs/decisions/EXL0-record.md`.

| ID | Guardrail | How to check |
|---|---|---|
| L-G1 | **No finding without a verified code span.** Every finding cites path, lines, commit and span hash, and passes V1 to V6. Else it is dropped or becomes a gap. | Tests: invented path, line past the end of the file, changed text under the span, invented identifier: nothing is stored |
| L-G2 | **The code is the source of truth.** Comments, documents, client answers and model memory are supporting evidence only. A finding with only such evidence is never "confirmed". | Test: a comment that contradicts the code gives "inferred" at best |
| L-G3 | **Labels come from rules, not from the model.** The model's own certainty does not set confirmed, inferred or gap. | Test: model output that says "certain" with one pass and no graph support gives "inferred" |
| L-G4 | **Client code stays private and in region.** No client code in logs, metrics, eval sets, prompts for another tenant, CLI or MCP results, or training. Model calls only on the tenant's region route (G7). | Log-scan test with a planted code marker; router test; CLI and MCP result test; no eval set reads tenant data |
| L-G5 | **Read-only and sandboxed.** The analyser never writes to the client's repository. A build for the SCIP index runs in a throw-away container with no network, no secrets and resource limits. | Test: a build script that tries a network call fails; the container has no secret variables |
| L-G6 | **Deletion on time.** Snapshot, index and findings are deleted at the end of the retention period, with a deletion record. | Unit test for the retention job, as in W-G4 |
| L-G7 | **Clean room.** No code, prompts, templates, test data or methods from any current or past employer of the founders. No client code from past employers (G8). | Each fixture has a `SOURCE.md`. Pre-commit term check with a list kept outside the repository |
| L-G8 | **Human approval before anything leaves.** A report goes to the client only after a named reviewer approves it. No change to the client's code without the client's approval (G13). | No export path without an approval record |
| L-G9 | **No precision claim without its numbers.** Every precision figure in a report, on the website or in sales material states the sample size, the method and the 95% confidence interval. | Report renderer test: a precision value without these fields fails the build |
| L-G10 | **Agents propose, people accept.** No API, MCP or CLI path accepts a finding, changes a label, re-accepts a changed `critical` finding or releases a report. | Test: every write tool creates a review task only |
| L-G11 | **Writes to the client's systems need a standing approval.** A pull-request status check, a comment or a specification pull request needs a recorded approval from the client for that repository. | No outbound call to a git host without an approval record (G13) |
| L-G12 | **Lean agent access.** All MCP tool definitions together cost 2,000 tokens or less; a typical tool result 1,500 tokens or less; the skill file 800 tokens or less. | Test counts tokens of the definitions, the skill file and recorded typical results; the build fails above the budget |
| L-G13 | **Qualified routes, or a visible label.** A report uses precision figures only from qualified routes, or from the tenant's own review sample for an unqualified route. Every finding and report names its route and its qualified status. | Test: a run on an unqualified route renders the label and uses the tenant sample only |
| L-G14 | **Independent cross-check.** The S5 cross-check route uses a different provider from the S4 route. | Test: same provider for S4 and S5 is refused at configuration and at run start |
| L-G15 | **Client keys are secrets.** Stored encrypted per tenant, write-only in the UI, never in logs, metrics, events or prompts, never used for another tenant, never replaced by an Exaktiv key without the client choosing managed models. | Log-scan test with a planted key; tenant isolation test on the key vault; no-fallback test |

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

These phases need an independent subagent review before "done": EXK2 (region), EXK3 (G1), EXK4 (G3/G4), EXK5 (G2), EXK9-p2 (G10), EXK10 (G5), EXK11 (G6), EXC4b (A-G4), EXC5 (A-G3), EXC9, EXP5 (B-G3), EXW1 (W-G4), EXW3 (W-G1, W-G2, W-G3), EXL4 (L-G1, L-G2, L-G3), EXL10 (L-G4, L-G5, client environment), EXL14 (L-G13, L-G14, L-G15).
