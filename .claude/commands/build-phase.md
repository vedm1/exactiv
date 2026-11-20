---
description: Start a disciplined build session for an Exaktiv phase, spec-then-code with human in the loop
argument-hint: <phase e.g. EXK1> [spec|implement]
---

You are starting a build session for **Exaktiv** — an extraction engine that gives each value a source link, a calibrated confidence and a human review path, for Exaktiv Claims (India) and Exaktiv Product Data (EU). Arguments: `$ARGUMENTS`
(first token = phase code; optional second token = `spec` or `implement`; default to `spec` if a detailed
implementation spec for this phase does not yet exist in `EXAKTIV_PHASE_SPECS.md`).

Follow this recipe exactly. **Do not skip steps. Do not write code before the plan is approved.**
Generating code ahead of approval is the failure mode this workflow exists to prevent.

**Response language:** Write all responses in ASD-STE100 (Simplified Technical English): short sentences,
approved words, active voice, one meaning for each word. This includes playbacks, plans, questions, and
summaries. Code, commands, and paths stay as they are.

## 1. Prime context (read, don't assume)
- `CLAUDE.md` is already loaded — honour it, especially G1 (no value without a source), G3 (rules in config, not prompts), G6 (tenant isolation) and G7 (region fixed, no fallback).
- Read the matching phase section in `EXAKTIV_PHASE_SPECS.md`, and the requirement IDs it cites in `docs/prd/`.
- Read `EXAKTIV_BUILD_PLAN.md` for sequencing, risks, decisions and open items relevant to this phase.
- Read `PHASES.md` to confirm predecessor phases are ✅ (use the `<!-- deps -->` block; do not read the whole file).
- Read the **existing modules this phase touches** — reuse patterns, don't reinvent.
- Check the open-items table — flag if a prerequisite is unresolved. Do not build on an unconfirmed assumption.
- If this phase adds a migration, read existing Alembic revisions for the correct `down_revision`.

## 2. Play back understanding (required, before anything else)
State: the objective in one sentence · what's in/out of scope for THIS session · existing code you'll reuse
(paths, function names) · new files/tables/endpoints · guardrail implications (G1–G13, A-G*, B-G*) · which gate this phase
closes · region and tenant implications · server cost impact (limit $10 per month per region) · unresolved open items.
Surface tradeoffs. **Stop and ask** where the spec is thin.

## 3. Branch by mode
**If `spec`**: produce a detailed implementation spec — final types and field names, algorithms worked out in
full, and the test plan (specific fixtures and assertions). Where they apply: DDL with types/nullability/indexes,
Alembic migration and backfill strategy, request/response contracts, `config/` file formats with `version:`.
**Do not write code until the spec is approved.**

**If `implement`** (only after spec approval): follow the approved spec. TDD — failing tests first, then build
inside-out (data/types → logic → interface). Surgical changes: touch only what this phase slice needs.
Stack reminders: Python 3.12, uv workspace, FastAPI, DBOS Transact, Postgres 16 + Alembic, MinIO, LiteLLM (pinned digest);
UI in `ui/` with pnpm, React + TypeScript strict, tokens in `ui/src/tokens/`. Local stack: `docker compose -f deploy/docker-compose.yml up -d`.
Fixtures: synthetic or public only, each with a `SOURCE.md` note (G8).

## 4. Plan & approve
Present a concrete, ordered plan (files to add/change, tests to write, order of operations).
**Wait for approval. Do not edit before approval.**

## 5. Verify (do not declare done without this)
- `uv run pytest` passes with all new tests green; `pnpm test` for UI phases.
- `uv run ruff check`, `uv run ruff format --check` and `uv run mypy` clean; `pnpm lint` and `pnpm typecheck` for UI phases.
- Each guardrail this phase touches has a passing test named after it (for example `test_g1_value_without_source_is_dropped`).
- For the high-stakes phases listed in `CLAUDE.md`: launch a **subagent for independent review**.
- Migrations apply cleanly on a fresh database and roll back.
- No threshold, rule or value list appears in a prompt file. No personal data in logs.

## 6. Document (close the loop)
- Flip this phase's row in `PHASES.md` 🔲 → ✅ with a dense summary of what was built.
- If implementation revealed a better design than the spec, update `EXAKTIV_PHASE_SPECS.md` — reconcile, don't drift.
- Append an "Implementation notes" block recording what was discovered.
- Resolve any open items in `EXAKTIV_BUILD_PLAN.md` that this phase answered.
- Regenerate the dashboard: `python3 .claude/phase-dashboard/build_dashboard.py` (the hook usually has already; rerunning is harmless). Mention any new tracker-health warnings.

## Guardrails (project-specific, beyond CLAUDE.md)
- **Never** let a model call route outside the tenant's region, not even as a retry.
- **Never** put a threshold, policy limit, ETIM code or business rule in a prompt.
- **Never** store a value as accepted before validation and the review or calibrated auto-accept step.
- **Never** commit real customer, medical or past-employer data. Never store an unmasked Aadhaar number.
- **Never** add a server or service that pushes a region above $10 per month without asking first.
- **One phase = one small PR.** If scope sprawls, stop and re-scope before continuing.
