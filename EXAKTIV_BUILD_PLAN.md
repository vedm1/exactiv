# EXAKTIV_BUILD_PLAN.md — Sequencing, Risks, and Gates

The reasons for the phase order, and the risks to watch at each step.
Capacity: two founders at about 20 hours per week each. Keep each phase to one small PR.

## Decisions log (4 Nov 2026, build-phase interview)

| Decision | Result | Replaces in PRD |
|---|---|---|
| Phase codes | Three prefixes: EXK, EXC, EXP | — |
| Backend language | Python 3.12 only (FastAPI, Temporal Python SDK) | Kotlin / Spring Boot (PRD-00 §8) |
| Repository | Monorepo | — |
| Workflows | Temporal, no Kafka in v1 | — (confirmed) |
| UI | React + TypeScript, Exaktiv brand package (`brand/`) | Personal Design System (PRD-00 §8) |
| Design system (18 Nov 2026) | Exaktiv identity v1.0: Leader mark, Proof palette (Paper, Ink, Cobalt, Vermilion, Marker), Workbench type (Young Serif, Instrument Sans, Gelasio italic), no monospace. Phases EXD1 to EXD5. | Ved Design System v4 tokens (PRD-W §9), Personal Design System |
| Base model licence | Apache 2.0 or MIT only | — (confirmed) |
| Hosting | Local first. Server cost limit $10 per month per region. AWS Mumbai minimum useful stack is about $22 per month, so AWS is out. EU: Hetzner Germany. India: provider to choose. | AWS Mumbai + Frankfurt (PRD-00 §8) |
| Secrets | AWS Secrets Manager no longer applies. Mechanism to choose (open item). | AWS Secrets Manager |

## Phase Sequencing

### EXK0 → EXK1 / EXK2: foundation first
Nothing starts before CI, the secret scan and the licence check run. If these come later, the first real commits can already contain a secret or an unlicensed model.

### EXK1: event log from day 1
The PRD puts the evidence log in EXK8. The append-only event log now starts in EXK1, and EXK8 only builds the export. If the log starts in EXK8, all jobs before EXK8 have no evidence, and the evidence code must be added to every module later.

### EXK2 → EXK3: region check before extraction
No model call may reach a document before the router refuses cross-region routes (G7). The test runs with configuration only, so no cloud region is necessary.

### EXK3 → EXK4 → EXK5: source, then validity, then confidence
A value with no source is dropped first (G1). Only a valid value gets a confidence (G4 before G2). If the order is reversed, an invalid value can get a high confidence and be auto-accepted.

### EXK5 → EXK6 / EXK7
The review queue needs the abstention rule to decide what goes to review. The evaluation harness needs abstention to report the abstention rate.

### EXK7 → EXK9-p2 → EXK9-p3
The regression gate uses the frozen set and the report format from EXK7. No adapter is trained before the gate exists (G10).

### Products after EXK4 / EXK5
EXC1 and EXP1 are configuration only, so they can start after EXK4. Extraction phases (EXC4, EXP4) need EXK5. Claims and Product Data can run in parallel: one founder on each track.

### Hosting phases
EXK0b (EU) gates EXP6, because the free-fill test uses prospect data. EXK0c (India) gates EXC9, because real medical records must stay in India (A-G2). The Claims PoC uses synthetic data only (A-G5), so it runs locally until EXC9.

### EXD5 / EXW1 → EXW2 → EXW3: website order
EXD5 builds the pages and EXW1 builds the form service. EXW2 deploys both on the EXK0b server, so EXK0b must be complete first. EXW3 is the launch gate: the site stays behind the staging password until every claim has evidence and the lawyer review is recorded. If the site goes public first, an unsupported claim can damage trust at the first security review.

## Risks by Phase

### EXK0b / EXK0c
- **Risk**: The $10 limit per region is too small for Postgres + Temporal + MinIO + API on one server (about 4 GB RAM is necessary).
- **Mitigation**: Measure RAM in EXK0 with docker stats. Use Temporal with the Postgres backend (no separate Cassandra or Elasticsearch). Record the real cost in the phase summary.

### EXK2
- **Risk**: Data leaves the region through a router configuration mistake.
- **Mitigation**: G7 test in CI. Region check on every call. No fallback.
- **Risk**: Supply-chain compromise of the model gateway.
- **Mitigation**: Pin LiteLLM by digest. Review each upgrade. Keep the gateway in the private network.

### EXK5
- **Risk**: Reviewers do not trust the confidence score, so every value goes to review and there is no labour saving.
- **Mitigation**: Calibrate per field. Show the source next to each value. Track reviewer overrides.

### EXK7 / EXC7 / EXP6
- **Risk**: Frontier models close the gap on hard inputs, so the accuracy claim weakens.
- **Mitigation**: The moat is the correction data and the evidence log. Re-run the baseline every month.

### EXK9-p3
- **Risk**: A licence problem with a base model forces a model change.
- **Mitigation**: G12. Apache 2.0 / MIT only. Record each licence in `LICENCES.md`.

### EXC2 / EXC7
- **Risk**: The handwriting gain is less than 5 points.
- **Mitigation**: Pitch reviewer speed to TPAs. Collect real handwritten data in the pilot. Fine-tune per tenant (EXC7b).
- **Risk**: Public handwriting datasets are research-only.
- **Mitigation**: Check each licence before use (G12). Use volunteer data as the main source.

### EXC4b / EXC9
- **Risk**: A health data incident.
- **Mitigation**: A-G2, A-G4, G11. No real data before a signed pilot. DPDP controls.

### EXP1 / EXP5
- **Risk**: ETIM model licence terms or pool upload rules block the product.
- **Mitigation**: Confirm with ETIM International, 2BA and ITEK before the phase starts (open items).
- **Risk**: ITEK or 2BA see Exaktiv as a competitor.
- **Mitigation**: Ask early. Position as a supplier-side service.

### EXD: design system before any screen, report or page
EXD1 (the brand package) is done. EXD2 puts the tokens, fonts and the `check_brand.py` gate into `ui/` and CI before the first screen. EXD3 (components) comes before EXK6-ui, and EXD4 (report template) before EXK7 and EXK8. EXD5 (website) can run in parallel with the engine phases, because it needs only EXD2.
- **Risk**: Screens or PDFs built before EXD2 hard-code colours and fonts, and drift from the brand.
- **Mitigation**: `check_brand.py` in CI fails on hex values, raw tokens, monospace fonts, radius and blurred shadows.

### EXW1
- **Risk**: Personal data from the form gets into logs, or stays longer than 6 months.
- **Mitigation**: G11 masking, no message content in logs, a daily deletion job with a test (W-G4), independent subagent review.

### EXW2
- **Risk**: The site goes live on an ad hoc host outside the EU before EXK0b exists.
- **Mitigation**: EXW2 depends on EXK0b. No deploy outside the EU region.

### EXW3
- **Risk**: The site goes public with a claim that has no evidence, or before the lawyer review.
- **Mitigation**: Claims evidence and the recorded lawyer review are EXW3 completion criteria.
- **Risk**: The site describes services that overlap with a team member's current employer.
- **Mitigation**: The employment contract check is an EXW3 completion criterion.

### All phases
- **Risk**: Two founders at 20 hours per week each make the build slow.
- **Mitigation**: One small PR per phase. Build the core once for both products.

## Open Items (resolve before the relevant phase)

| Item | Blocks | Status |
|------|--------|--------|
| Choose an India hosting provider with India data location, ≤ $10 per month for about 4 GB RAM (compare, for example, DigitalOcean Bangalore, Akamai/Linode Mumbai, Vultr Mumbai/Bangalore, E2E Networks) | EXK0c | 🔲 Open |
| Choose a secrets mechanism without AWS Secrets Manager (for example SOPS + age, Infisical, Doppler) | EXK0b | 🔲 Open |
| EU-only engineering access from day 1, or only for personal data? | EXK0b | 🔲 Open |
| Frontier model endpoint per region that keeps data in region (Gemini Flash in India; an EU frontier model), and its data-use terms | EXK2 | 🔲 Open |
| Measure stack RAM to confirm a 4 GB server is enough | EXK0b | ✅ Idle total about 231 MiB (EXK0). Confirm under load in EXK0b |
| Dataset licences for FUNSD, IAM, IIIT Hyderabad Indic handwriting sets | EXC2 | 🔲 Open |
| Volunteers (15–20, paid) for handwritten forms in EN, HI, KN | EXC2 | 🔲 Open |
| Current IRDAI list of non-medical (non-payable) items, with version | EXC5 | 🔲 Open |
| Policy-rule fields a first customer needs (room rent, co-pay, sub-limits) | EXC5 | 🔲 Open |
| ETIM model licence and download terms (ETIM International) | EXP1 | 🔲 Open |
| Exact upload format per pool (2BA, Open Datacheck) | EXP5 | 🔲 Open |
| Does 2BA or ITEK give a test-validation service to outside providers? | EXP5 | 🔲 Open |
| First pool: 2BA (proposed) or Open Datacheck | EXP5 | 🔲 Open |
| Open base model and size with best accuracy per GPU cost (decide after the EXK7 baseline) | EXK9-p3 | 🔲 Open |
| GPU: self-hosted or managed inference per region, and its cost | EXK9-p3 | 🔲 Open |
| ISO 27001 start date (proposed: month 4) | EXC9 | 🔲 Open |
| Mid-size insurers and TPAs in the founders' network for the 30-day test | EXC9 | 🔲 Open |
| Three paying Product Data suppliers | EXP8 | 🔲 Open |
| PRD-W open item O1: repository rules still name the retired Personal Design System | EXD2 | ✅ Done 18 Nov 2026: CLAUDE.md, specs, build plan and PRD notes point to `brand/` |
| Update the live PRD-W master copy (§9 still describes v4 tokens and General Sans) to point to `brand/README.md` | EXD5 | 🔲 Open |
| Where the website code lives: `site/` in this repository, or its own repository | EXD5 | ✅ `site/` in this repository (EXD5, 18 Nov 2026). The form service lives in `services/site_form` (EXW1) |
| PDF renderer for EXD4 (for example WeasyPrint, BSD licence) and its licence check | EXD4 | 🔲 Open |
| MinIO image source and licence (official image no longer public; AGPL-3.0) | EXK0b | 🔲 Open. EXK0 uses the Chainguard build by digest |
| PRD-W D1: domain for the site (a neutral global domain, not .de) | EXD5, EXW2 | 🔲 Open |
| PRD-W D4: form back end. Proposed: our own endpoint on the EU server (EXW1) | EXW1 | ✅ Done 18 Nov 2026: own endpoint, `services/site_form` |
| PRD-W D6: EU mail provider for the form mail and the domain mailbox | EXW2 | ✅ Form mail: Brevo HTTP API (18 Nov 2026). 🔲 Open for the domain mailbox |
| Brevo: sign the DPA, get the sub-processor list, confirm how long Brevo keeps transactional mail content | EXW2, EXW3 | 🔲 Open |
| Team mailbox keeps a copy of each enquiry: add a 6-month deletion routine and say so in the privacy notice (PRD-W §8.3) | EXW2, EXW3 | 🔲 Open |
| EXW2 deploy settings for the form service: `TRUSTED_PROXY_HOPS` (1 behind the proxy, and the app port closed to the outside), timers for `retention` (daily), `retry-mail` (every minute), `purge-hits` (hourly), uvicorn with `--no-access-log`, alert on the log event `enquiry_mail_failed` | EXW2 | 🔲 Open |
| Claims evidence (PRD-W §6): register of AI model endpoints per region, provider no-training terms, traceability demo output | EXW3 | 🔲 Open |
| Lawyer review of the privacy notice (PRD-W §8.3) | EXW3 | 🔲 Open |
| Employment contract check before the public launch | EXW3 | 🔲 Open |
| First client contract close (trigger for the legal notice) | EXW4 | 🔲 Open |
