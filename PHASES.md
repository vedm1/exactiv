# PHASES.md — Exaktiv Build Tracker

One row per phase. Flip 🔲 → ✅ when the phase is complete (all tests green, docs updated, PR merged).
Prefixes: **EXK** = core engine, **EXC** = Exaktiv Claims, **EXP** = Exaktiv Product Data, **EXD** = design system (brand package in `brand/`), **EXW** = website operations (PRD-W: contact form, hosting, launch).

| Phase | Name | Status | Summary |
|-------|------|--------|---------|
| **EXK0** | Foundation | ✅ Done | Monorepo (uv + pnpm workspaces; core, api, worker, model packages; React/TS UI). Compose stack with Postgres 16.4, MinIO (Chainguard build), Temporal 1.25 + UI, all pinned by digest, ports on 127.0.0.1 (Postgres on 5442). `GET /health` and `SmokeWorkflow` (row + object). CI: ruff, mypy strict, pytest, eslint, tsc, vitest, gitleaks (planted-key check), licence checks (Python + UI), integration job. Pre-commit hooks. 18 Python tests + 1 UI test green, also on a clean copy. Idle RAM of the 4 containers: about 231 MiB. First CI run is pending the GitHub remote. |
| **EXK0b** | EU host (Hetzner) | ✅ Done | CircleCI replaces GitHub Actions (`.circleci/config.yml`: python, ui, site, secrets, integration, then `deploy-infra` on main; context `exaktiv_deploy`, restricted to main). Shared Hetzner Nuremberg host: user `exaktiv-deploy`, forced-command `deploy-infra` plus allowlist `policy.py` (root-owned), MinIO-only stack in `deploy/server/` (127.0.0.1:9000, named volume, 1 GiB, user 65532), secrets from Doppler (two keys only). Live: deploy of `7ebe52a` healthy, other projects unchanged. Postgres on Neon Frankfurt, pooled host: `DATABASE_URL`, TLS and pooler settings; `alembic upgrade head`, rate limit and lock race verified live. Independent review: 3 critical gaps fixed. MinIO licence recorded. Cost: Neon 10 dollars per month, server share zero. Restore test moved to EXW3. Doppler region EU and DPA confirmed. Temporal DB decision parked for its phase. |
| **EXK0c** | India host | 🔲 Planned | Deploy to the India provider chosen in the open items. Server cost ≤ $10 per month. Required for A-G2 before any pilot. |
| **EXK1** | Ingestion, storage, event log | 🔲 Planned | Alembic exists since EXW1 (`alembic.ini`, `migrations/`, baseline `0001`, `exaktiv_core.db.PostgresSettings`): add revisions on top and drop `smoke_runs`. Tenants, jobs, files with SHA-256, page split, normalised page images, size limit, append-only event log for every state change. |
| **EXK2** | Model gateway and router | 🔲 Planned | LiteLLM (pinned digest) as the one gateway; cost/latency/token log per call; versioned routes; region check with no fallback (G7). |
| **EXK3** | Extraction contract | 🔲 Planned | Value record (FR-EXT-3) with source metadata; values without a source are dropped and the field marked "not found" (G1). |
| **EXK4** | Validation layer | 🔲 Planned | Schema and domain validation from versioned `config/`; failures go to review with a reason (G3, G4). |
| **EXK5** | Confidence and abstention | 🔲 Planned | Confidence score, per-field thresholds, "always review" fields, 200-review rule, calibration version (G2). |
| **EXK6** | Review queue backend | 🔲 Planned | Review tasks per tenant, accept/correct/not-present actions with audit, job completion rule (FR-REV-5), product screen extension points. |
| **EXK6-ui** | Core reviewer UI | 🔲 Planned | Keyboard-first review screen with source crop, built on the EXD3 components, dark default through `data-theme`. Target ≤ 8 s per simple field. |
| **EXK7** | Evaluation harness | 🔲 Planned | Pipeline vs frontier baseline on a frozen set; per-field precision, recall, exact match, abstention, cost, latency; hard subset; HTML + JSON report. |
| **EXK8** | Evidence pack (Exaktiv Proof) | 🔲 Planned | Evidence pack per job (PDF + JSON) from the event log, with source crops per value. |
| **EXK9-p1** | Corrections store and training sets | 🔲 Planned | Labelled examples per tenant and task; training sets with a frozen evaluation split; consent flag for cross-tenant use. |
| **EXK9-p2** | Model registry and regression gate | 🔲 Planned | Versioned models, adapters, prompts and routes; promotion only with a passed gate record (G10); one-step rollback. |
| **EXK9-p3** | LoRA adapter pipeline | 🔲 Planned | Train a private LoRA adapter per tenant and task on an Apache/MIT base model; register through the gate. |
| **EXK10** | Metering and usage export | 🔲 Planned | Accepted units per tenant per month, count once, monthly export, reconcile with job records (G5). |
| **EXK11** | Public API | 🔲 Planned | REST API (create job, upload, status, results, evidence pack), webhook on completion, API keys with scopes per tenant (G6). |
| **EXD1** | Brand package | ✅ Done | `brand/`: guidelines page, Leader mark and lockups (SVG with outlined wordmark, PNG at 3 sizes), favicon set (SVG, ICO, PNG, touch and app icons, web manifest), Open Graph image, self-hosted fonts (Young Serif, Instrument Sans, Gelasio italic; OFL), tokens (`tokens.css` source, generated `tokens.json` + `tokens.ts`), `components/exaktiv.css`, `check_brand.py` (30 contrast pairs, banned patterns). Replaces the Personal Design System (PRD-W open item O1). |
| **EXD2** | Tokens, fonts and guards in the UI | ✅ Done | `scripts/sync_brand.py` (`--check`, `--root`) copies tokens, `exaktiv.css`, fonts and favicons from `brand/` into `ui/` byte for byte. `main.tsx` loads tokens then base CSS; `index.html` links `/fonts/fonts.css`, favicons and manifest, `data-theme="dark"`. `useTheme` (default dark, `localStorage`, safe fallback). CI: sync check, `check_brand.py`, planted `#ff0000` must fail, `pnpm build`, `check_no_external.py` on `ui/dist`. Pre-commit hooks for brand check and sync. 8 Python guard tests, 6 vitest tests. |
| **EXD3** | React component library | 🔲 Planned | Typed React components for every part in `exaktiv.css` (button, the Trace, cards, finding card, table, form fields, notices, header, footer) plus the reviewer source-crop frame. Accessibility tests, 0 axe violations. Dev gallery page. |
| **EXD4** | Report and PDF template | 🔲 Planned | One HTML + print template for the EXK7 evaluation report, the EXK8 evidence pack and the EXC6 case summary. A4, embedded fonts, citations as footnotes, "draft" watermark variant. |
| **EXD5** | Website kit (PRD-W) | ✅ Done | `site/` (config, `claims.yaml`, 10 page templates on the brand package) and `scripts/build_site.py`, which is also the gate: it fails on a footnote for a claim that is not "ready" (`cite()`, `backed()`), a banned claim, any third-party URL, an inline style or script, a wrong H1, lang or canonical, a name from the name list, or an off-brand pattern. Writes sitemap, robots, `llms.txt`, `security.txt`, `_headers` (CSP `default-src 'self'; img-src 'self' data:; frame-ancestors 'none'`) and the Organization JSON-LD. Staging builds are noindex. `--launch` also fails on any unready claim, placeholder (`.invalid`, `[[TODO`) or missing name list. 47 tests. Browser check: 0 cookies, 0 third-party requests, under 1 MB, no horizontal scroll at 390 px. Lighthouse 100 on all four categories on all 10 pages. CI job `site`. Open: name-list run, keyboard test, domain and mail (D1, D6). |
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
| **EXW1** | Contact form endpoint | ✅ Done | `services/site_form` (FastAPI): `POST /enquiries` (JSON or form post, field-level errors, 303 redirects without values), `GET /form-token` (signed token, 3 s minimum fill time; no token = stricter limit of 2 per 10 min), honeypot, rate limit 5 per IP per 10 min in Postgres (HMAC IP hash, advisory lock, no raw IP stored). Brevo HTTP API (D6) behind a `Mailer` interface: team mail plus automatic reply, independent sends, retry job (5 attempts). Alembic added here: `0001` (`site_enquiries`, `site_form_hits`). Jobs: `retention` (W-G4), `retry-mail`, `purge-hits`. Logs: event + ID only, masking filter (G11). Independent review done, findings fixed. Unit, guardrail and integration tests green; deploy, timers and Dockerfile are EXW2. |
| **EXW1-ui** | Contact form on the site | 🔲 Planned | The Contact page form on the EXD5 templates, connected to EXW1: plain POST without JavaScript, field errors, confirmation state, privacy line under the button. |
| **EXW2** | EU hosting and deploy | ✅ Done | Live on the shared Hetzner host (project `exaktiv-site`, deploy through the shared `bin/deploy`, first deploy 19 Nov 2026). `exaktiv.com` (D1): TLS by the shared Caddy, `www` redirect, staging behind Basic Auth + noindex (`SITE_MODE`), fails closed. Web image (Caddy: headers from `build_site.HEADERS`, /24-masked access log checked live, one-hop `X-Forwarded-For`, only `/enquiries` and `/form-token` reach the form), form image (Doppler `run`, `--no-access-log`, non-root), `migrate` and `jobs` profiles, three systemd timers (verified: each ran, `job_done`, retry-mail every minute), CI `build-images` + `deploy-app`, `check_dns.py` and `smoke_staging.py` (all pass), Brevo mail with DKIM, SPF and DMARC pass (policy `p=none`). Real test enquiries stored, team mail and automatic reply delivered. Mail: Google Workspace (D6), Europe region. Grafana data source and mail-failure alert built. Independent review done, findings fixed. 372 unit and 10 image integration tests green. **Accepted or open, not blocking**: shared Caddy error log keeps full IPs on a 502 (PRD-W 8.2 not met for those lines); Brevo open-tracking pixel kept in anonymous mode (privacy notice must say so, EXW3); retention freshness alert needs Alloy to see the job containers (EXW3, before real data); failing-migration rehearsal not run (the shared `bin/deploy` stops before `up` by design; migrate ran green at head on the first deploy); `.invalid` mail addresses stay until EXW3; DMARC to `quarantine` before EXW3; Brevo DPA open. Cost: EU region about 17 to 18 dollars per month vs the 10 dollar limit, overrun accepted by the user. |
| **EXW3** | Launch gate | 🔲 Planned | PRD-W §11 definition of done on staging: all claims "Ready" with evidence, lawyer review of the privacy notice recorded, employment contract check recorded, EXD5 build checks green. Then remove the staging password. Gates the public launch. |
| **EXW4** | Legal notice and analytics | 🔲 Planned | PRD-W phase 2: legal notice (Impressum) for Valyrian Tech Pvt Ltd and cookie-free analytics hosted in the EU. Starts when the first client contract is close. |

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
EXK6-ui: EXK6, EXD3
EXK7: EXK5, EXD4
EXK8: EXK6, EXD4
EXK9-p1: EXK6
EXK9-p2: EXK7
EXK9-p3: EXK9-p1, EXK9-p2
EXK10: EXK6
EXK11: EXK6
EXD1: -
EXD2: EXK0, EXD1
EXD3: EXD2
EXD4: EXD2
EXD5: EXD2
EXC1: EXK4
EXC2: EXC1
EXC3: EXC1, EXK3
EXC4: EXC3, EXK5
EXC4b: EXC4
EXC5: EXC4
EXC6: EXC5, EXK6, EXD4
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
EXW1: EXK0
EXW1-ui: EXW1, EXD5
EXW2: EXW1, EXD5, EXK0b
EXW3: EXW2, EXW1-ui
EXW4: EXW3
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

Design:   EXD1 → EXD2 ─┬→ EXD3 → EXK6-ui (then EXC6-ui, EXP5-ui)
                       ├→ EXD4 → EXK7, EXK8, EXC6 (reports and PDFs)
                       └→ EXD5 (website, PRD-W)

Website:  EXK0 → EXW1 → EXW1-ui (also EXD5) ─┐
          EXW1 + EXD5 + EXK0b → EXW2 ─────────┴→ EXW3 → EXW4
```

- **EXK2 before EXK3:** no model call may reach any data before the region check (G7) is in place and tested.
- **EXK4 before EXK5 and before any product schema:** a value must be valid before it gets a confidence. A product schema is configuration that the EXK4 loader reads.
- **EXK5 gates any auto-accept.** Before EXK5, every value goes to review.
- **EXK7 before EXK9-p2:** the regression gate compares against the frozen set and report format that EXK7 defines.
- **Claims and Product Data run in parallel after EXK5.** Their first phases (EXC1, EXP1) need only EXK4.
- **EXC9 needs EXK0c:** no pilot with real medical records before the India host exists (A-G2, A-G5).
- **EXP6 needs EXK0b:** the free-fill test uses prospect data, so it runs on the EU host, not on a laptop.
- **EXD2 before any screen, report or page:** the tokens, fonts and the `check_brand.py` gate must be in CI first. Otherwise each screen hard-codes its own colours and fonts, and each one must be fixed later.
- **EXD3 before EXK6-ui, EXD4 before EXK7 and EXK8:** reviewer screens and evidence packs use one component set and one report template. Each product screen and PDF reuses them.
- **EXW1 before EXW1-ui:** the form contract (fields, error format, responses) is fixed before the page uses it.
- **EXW2 needs EXK0b:** the site and the form service run on the EU host, inside the $10 per month limit.
- **EXW3 gates the public launch:** no page goes public before every claim has evidence and the lawyer review is recorded (W-G2).

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

**EXD1**: `brand/` holds the guidelines, logos (SVG and PNG), favicons, social image, fonts with licences, tokens and component CSS. `python3 brand/tokens/check_brand.py` passes. No file in `brand/` names a person, employer or client.

**EXD2**: `ui/src/tokens/tokens.css` and `tokens.ts` match `brand/tokens/` byte for byte (a test checks this). Fonts load from `ui/public/fonts/`, with no request to a font service. `check_brand.py` runs in CI and in pre-commit, and a planted hex value in a test component makes CI fail. `data-theme="dark"` and `"light"` switch all role tokens.

**EXD3**: Each component has a vitest test. Keyboard focus is visible on every control. `<Ref>` without a source throws in development, and `<Citations>` numbers sources in order of first use. The axe check reports 0 violations on the gallery page. No component contains a hex value, a raw token or a monospace font.

**EXD4**: One function renders a synthetic report to HTML and to an A4 PDF. The PDF embeds Young Serif, Instrument Sans and Gelasio (font check on the file). The HTML has no external URL. The "draft" variant shows the watermark on every page.

**EXD5**: The site build fails on a footnote for a claim whose register status is not "Ready", on a banned claim (PRD-W §6), and on any third-party URL. A browser check shows 0 cookies and 0 third-party requests. Lighthouse is 90 or more on every page. Page weight is under 1 MB.
