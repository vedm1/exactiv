# PRD-L — Exaktiv Legacy Analyser (traceable reverse engineering for the Assess stage)

Version 0.1 · 19 November 2026 · Status: plan for review, not yet in `PHASES.md` · Written in ASD-STE100

## 1. Summary

The Legacy Analyser reads a legacy code base and writes a specification in plain language. Each statement in the specification links to a file, a line range and a commit in the client's code. A deterministic verifier checks every link before a statement becomes a finding. A statement that fails the check is not stored. It goes to the "gaps" list. A person reviews each finding before it goes to the client.

The analyser is the engine behind the **Assess** stage on the website and in the capability deck: a traceable specification, a system map, a risk register, target architecture options and a roadmap, in 3 to 4 weeks at a fixed price.

The analyser is a third product track on the Exaktiv core. It reuses the core contract: no value without a source (G1), abstain and do not guess (G2), validate before storage (G4), review queue (EXK6) and evidence pack (EXK8). The only new idea for the core is a new location type: a **code span** in place of a page area.

## 2. Why now

| Driver | What it needs from the analyser | Where it is recorded |
|---|---|---|
| A European software vendor asked for a legacy modernisation proposal | A sample output to show on the discovery call, and a tool to deliver the Assess stage | Capability deck, slides 4 to 6 (`docs/sales/`) |
| Website claim `findings-sourced` ("Every finding links to its source") | "A demo output from our legacy analyser that shows file and line links". The claim is `to_confirm`. The EXD5 build refuses its footnote until it is `ready` | `site/claims.yaml`, PRD-W §6, EXW3 |
| Sample finding on the site and in the deck (`billing/Invoice.java:142`) | Today it is invented code. The analyser can make it a real output on our own synthetic code | `site/pages/legacy-modernisation.html.j2` |
| EU rules for software vendors (CRA, Data Act, NIS2) | A dependency inventory and an SBOM as Assess outputs | PRD-W §5, deck slide 7 |

## 3. Goals and non-goals

### Goals (v1)

1. Turn a code base snapshot into a traceable specification. Every statement cites file, lines, commit and a hash of the cited text.
2. Collect structural facts without a model: inventory, modules, entry points, call and dependency graph, data access, external integrations, SBOM.
3. Use models only to explain and to extract rules, and only on top of the facts.
4. Label each statement **confirmed**, **inferred** or **gap** with rules in code. The model does not choose its own label.
5. Send every finding to human review until the review history allows auto-accept (FR-CNF-5).
6. Produce the Assess deliverables: traceable specification, system map, risk register, dependency inventory with SBOM, open questions, evidence pack.
7. Run in our EU region, or inside the client's own environment.

### Non-goals (v1)

- No automatic code change, refactor or migration. Stage 2 (Pilot) is a separate track (EXL9).
- No "fully automated modernisation" claim (banned in PRD-W §6).
- No binary or black-box reverse engineering (no source code). Possible later.
- No model training or fine-tuning on client code.
- No languages beyond Java and Kotlin with full depth in v1. Other languages get "structure only" through tree-sitter until a language pack exists (EXL11).
- No self-serve upload. The team sets up each engagement.

## 4. Users

| User | Need |
|---|---|
| Exaktiv delivery lead (today: one founder) | Produce an Assess report in 3 to 4 weeks with most effort on judgement, not on reading code |
| Client engineer (reviewer and system owner) | Check a statement in the code in seconds: the statement on one side, the highlighted lines on the other |
| Client engineering leader (buyer) | A clear system map, a risk register and options, with evidence |
| Client security reviewer | Proof that the code stayed in region, was not used for training, was deleted on time, and that only named people saw it |

## 5. What the research says, and the design choice it drives

| Finding | Design choice |
|---|---|
| An industry pipeline on 3.4M lines of COBOL put deterministic parsing first. LLM-only trials gave more hallucinations, higher token cost and weaker structural coverage. It reported a speed-up of about 3.2 to 3.3 times and 93% agreement with manual rule analysis, and it still needed human correction | Facts first (EXL3), model second (EXL5). The model gets graph facts and code, not the whole repository |
| The same pipeline checks that every program, paragraph and data item the model names exists in the symbol tables | Verifier check V5: every identifier in a statement must exist in the cited span |
| A 2026 framework (Reversa) labels each claim confirmed, inferred or gap, and writes `questions.md` and `gaps.md`. Its own confidence index was not an independent audit | Same three labels, but computed by the verifier and by rules in code (L-G3), plus an independent precision check in EXL8 |
| A study of citation-grounded code comprehension found models that invent files and cite line ranges past the end of a file. Mechanical citation checks catch these | Verifier checks V1 to V3 run on every statement. A failed check drops the statement (L-G1) |
| Tree-sitter based code graphs in SQLite or Postgres are enough for agent queries over large repositories; heavy graph databases are not necessary | Code graph in Postgres tables with recursive queries. No Neo4j (cost limit, stack rule) |
| scip-java gives precise definitions and references, but it runs as a compiler plugin: the build must work. It does not support Java 7 or Ant builds | SCIP when the build works, in a sandbox. Tree-sitter as the fallback for every file. Record which source each edge came from |
| AWS Transform custom has general availability of codebase analysis in Frankfurt since March 2026 | Our difference must be checkable evidence per statement, human review, labelled gaps, vendor-neutral models, and the option to run inside the client's environment |
| Characterisation (golden master) tests pin what legacy code does today, and are a standard way to prove old and new behave the same | Stage 2 pilot kit (EXL9) generates characterisation tests from accepted findings, and uses mutation testing to prove the tests can fail |

## 6. Inputs and outputs

### Inputs

- A code snapshot: a git bundle (preferred, gives history) or an archive of the source tree, with the commit SHA. Upload by the client, or a read-only clone that the client starts. No standing access to the client's repository.
- Optional: build files and a build command for the SCIP index, database schema (DDL), API specifications, existing documents. Documents are supporting evidence only (L-G2).
- Engagement configuration: tenant, region, retention period, reviewers, scope (modules in and out).

### Outputs (map to deck slide 6)

| Output | Content | Built from |
|---|---|---|
| Traceable specification | Per module: purpose, entry points, business rules, validations, calculations, state changes, error handling, integrations. Each statement with its citation and label | Accepted findings |
| System map | Modules, dependencies, data flows, external systems, third-party components | Code graph (deterministic) plus accepted integration findings |
| Risk register | Untested areas, complexity hot spots, high-churn files, knowledge held by few people (counts only, no names), outdated or vulnerable dependencies, dead code candidates | Deterministic signals plus accepted risk findings |
| Dependency inventory and SBOM | CycloneDX JSON, with licences and known vulnerabilities | cdxgen or Syft, plus a vulnerability scan |
| Questions and gaps | Each gap with the code it concerns and the question for the client | Gap list |
| Target options and roadmap | Two or three options with trade-offs, and a staged roadmap | Written by the delivery lead from the outputs above. The analyser gives inputs only |
| Evidence pack | Snapshot hash, every model call, every check result, every review action | Core event log (EXK1) and EXK8 |

## 7. How it works

### 7.1 Pipeline (one Temporal workflow per snapshot)

```
S0 Ingest      snapshot → object storage (SHA-256 per file and per tree), manifest, line index
S1 Facts       tree-sitter on all files; SCIP index in a sandbox if the build works;
               entry points, data access, integrations, SBOM, git signals  →  code graph tables
S2 Partition   modules from packages and build modules, refined by communities in the call graph
S3 Explain     bottom-up: symbol → file → module summaries; each sentence cites spans      [model]
S4 Extract     per module: rules, validations, calculations, state changes, integrations  [model]
               schema-constrained JSON; kinds and limits come from config/legacy/
S5 Verify      deterministic checks V1–V7 on every statement; second independent pass for
               cross-check; label confirmed / inferred / gap by rule
S6 Review      core review queue (EXK6) with a code-span screen
S7 Synthesise  system map, module specs, cross-module flows from accepted findings only
S8 Render      HTML and PDF report (EXD4), SBOM, questions, evidence pack (EXK8)
```

### 7.2 Finding record (extends FR-EXT-3 with a code location)

| Field | Content |
|---|---|
| `finding_id`, `tenant_id`, `job_id` | Core identifiers |
| `snapshot_id` | Snapshot of one commit: commit SHA plus tree manifest hash |
| `kind` | From `config/legacy/finding_kinds.yaml` (for example `business_rule`, `validation`, `calculation`, `state_transition`, `entry_point`, `integration`, `data_access`, `error_handling`, `security_control`, `risk_signal`) |
| `statement` | Plain language, length limit from configuration |
| `spans[]` | `path`, `start_line`, `end_line`, `span_sha256` (of the normalised text), `symbol_id` (SCIP or tree-sitter qualified name), `role` (`primary` or `supporting`) |
| `identifiers[]` | Code names the statement uses (class, method, field, table, constant) |
| `label` | `confirmed`, `inferred` or `gap`, set by rules (L-G3) |
| `model_id`, `model_version`, `route_version`, `prompt_version`, `raw_output_ref` | Model metadata (G1) |
| `checks[]` | Result of V1 to V7 with reasons |
| `confidence`, `calibration_version` | Core EXK5 fields |

### 7.3 Verifier (deterministic, runs before storage)

| Check | Rule | On failure |
|---|---|---|
| V1 | The path exists in the snapshot manifest | Drop the statement. Record the reason |
| V2 | The line range is inside the file, and not longer than the limit in configuration | Drop |
| V3 | The hash of the cited lines, read again from the original in object storage, equals `span_sha256` | Drop |
| V4 | The cited symbol's definition overlaps the span | Drop |
| V5 | Each identifier in `identifiers[]` and in the statement text appears in the cited spans or in their direct graph neighbours | Drop |
| V6 | `kind` is in the configured list. Fields match the schema | Drop |
| V7 | A statement about a call, a dependency or a data flow matches an edge in the code graph | Label `inferred` at best |

Label rules (in code, not in prompts):

- **Confirmed**: V1 to V7 pass, and either the fact comes from the graph, or a second independent pass (other prompt and, where possible, other model provider) gives the same rule with overlapping spans.
- **Inferred**: V1 to V6 pass, but there is only one pass, or V7 fails, or the evidence is names or comments only.
- **Gap**: the system cannot answer safely. It records the question and the code area. A gap is a deliverable, not a failure.

### 7.4 Data store

Postgres tables (Alembic revisions on top of EXK1): `legacy_snapshots`, `legacy_files`, `legacy_symbols`, `legacy_edges` (with `source` = `scip` or `tree_sitter`), `legacy_findings`, `legacy_finding_spans`, `legacy_checks`. Every table has `tenant_id` (G6). Object storage: original snapshot, SCIP index, rendered reports. Search: Postgres full text plus graph expansion in v1. Embeddings (pgvector) only if EXL8 shows a recall gain.

### 7.5 Models and regions

All calls go through the core gateway (EXK2). No second model path.

| Route | Use | Notes |
|---|---|---|
| EU primary | Explain and extract (S3, S4) | A frontier model through an EU endpoint. Candidate: Claude through Amazon Bedrock in an EU region (in-region where the model is offered, else the EU geographic profile, which keeps prompts and outputs inside the EU) |
| EU cross-check | Second pass (S5) | A different provider where possible. Candidate: Mistral through its EU regional endpoint with zero data retention |
| Client environment | All model steps | The client's own endpoint, or an open model under Apache 2.0 (for example Qwen3-Coder-30B-A3B or Devstral Small 2) on the client's hardware |
| India | Later | Only when an India client exists (EXK0c) |

Each route, its data terms and its licence go into the model endpoint register (open item in the build plan) and `LICENCES.md` (G12).

## 8. Functional requirements

### 8.1 Ingest

- FR-LEG-ING-1: Accept a git bundle or a source archive with a commit SHA. Store it unchanged with SHA-256 per file and a tree manifest hash.
- FR-LEG-ING-2: Exclude vendored and generated folders by configurable patterns. Record what was excluded.
- FR-LEG-ING-3: Reject a snapshot above the tenant size limit, with the reason.
- FR-LEG-ING-4: Write one event per state change (core event log).

### 8.2 Facts

- FR-LEG-FCT-1: Parse every file with tree-sitter. Record parse errors per file. A parse error never stops the job.
- FR-LEG-FCT-2: For Java and Kotlin, try the SCIP index in the build sandbox (L-G5). If the build fails, continue with tree-sitter only and record the reason.
- FR-LEG-FCT-3: Detect entry points by rules in `config/legacy/` (for example `main` methods, HTTP controllers, scheduled jobs, message listeners, servlets).
- FR-LEG-FCT-4: Detect data access (JPA entities, SQL strings, stored procedure calls) and external integrations (HTTP clients, message queues, file transfer, mail).
- FR-LEG-FCT-5: Produce a CycloneDX SBOM and a vulnerability report.
- FR-LEG-FCT-6: From git history, compute churn and knowledge concentration per module. Store counts and shares only. Never store or show author names or e-mail addresses (G11).

### 8.3 Explain and extract

- FR-LEG-EXT-1: Prompts ask for explanation and extraction only. Kinds, limits, thresholds and labels live in `config/legacy/` and in code (G3).
- FR-LEG-EXT-2: The model returns JSON against a fixed schema per kind. Invalid JSON goes to retry once, then to "failed" (FR-RTR-5).
- FR-LEG-EXT-3: The model receives the code of the unit, its graph neighbours and the summaries of its callees. It does not receive the whole repository.
- FR-LEG-EXT-4: Every statement carries at least one span. A statement with no valid span is dropped (L-G1).

### 8.4 Verify, label, review

- FR-LEG-VER-1: Run V1 to V7 on every statement before storage (G4).
- FR-LEG-VER-2: Set the label by the rules in section 7.3 (L-G3).
- FR-LEG-REV-1: Every finding goes to review until its kind has 200 or more reviewed findings for the tenant (FR-CNF-5). In v1 this means all findings.
- FR-LEG-REV-2: The review screen shows the statement, the label, the check results and the cited lines with a highlight. Actions: accept, correct (statement or span), reject, change to gap. Each action records user, time, old and new value.
- FR-LEG-REV-3: A correction re-runs V1 to V7.

### 8.5 Deliverables

- FR-LEG-OUT-1: Render the deliverables in section 6 from accepted findings, plus clearly labelled inferred findings and gaps.
- FR-LEG-OUT-2: Each statement in the report shows its citation as a footnote (the Trace in `brand/README.md`). A statement with no citation is not rendered.
- FR-LEG-OUT-3: Export the evidence pack (EXK8) per snapshot.
- FR-LEG-OUT-4: Delete the snapshot, index and findings at the end of the retention period. Write a deletion record (L-G6).

## 9. Legacy guardrails (in addition to core G1–G13)

| ID | Guardrail | How to check |
|---|---|---|
| L-G1 | **No finding without a verified code span.** Every finding cites path, lines, commit and span hash, and passes V1 to V6. Else it is dropped or becomes a gap. | Tests: invented path, line past the end of the file, changed text under the span, invented identifier: nothing is stored |
| L-G2 | **The code is the source of truth.** Comments, documents and model memory are supporting evidence only. A finding with only comment or name evidence is never "confirmed". | Test: a comment that contradicts the code gives "inferred" at best |
| L-G3 | **Labels come from rules, not from the model.** The model's own certainty does not set confirmed, inferred or gap. | Test: model output that says "certain" with one pass and no graph support gives "inferred" |
| L-G4 | **Client code stays private and in region.** No client code in logs, metrics, eval sets, prompts for another tenant, or training. Model calls only on the tenant's region route (G7). | Log-scan test with a planted code marker; router test; no eval set reads tenant data |
| L-G5 | **Read-only and sandboxed.** The analyser never writes to the client's repository. A build for the SCIP index runs in a throw-away container with no network, no secrets and resource limits. | Test: a build script that tries a network call fails; the container has no secret variables |
| L-G6 | **Deletion on time.** Snapshot, index and findings are deleted at the end of the retention period, with a deletion record. | Unit test for the retention job, as in W-G4 |
| L-G7 | **Clean room.** No code, prompts, templates, test data or methods from any current or past employer of the founders. No client code from past employers (G8). | Each fixture has a `SOURCE.md`. Pre-commit term check with a list kept outside the repository |
| L-G8 | **Human approval before anything leaves.** A report goes to the client only after a named reviewer approves it. No change to the client's code without the client's approval (G13). | No export path without an approval record |

## 10. Source of record additions

| Data | Authoritative source | Cross-check |
|---|---|---|
| Code content | Snapshot original in object storage, by SHA-256 | Hash check on every read (V3) |
| Structural facts | Code graph tables, with the source of each edge | Re-run on the same snapshot gives the same graph |
| Finding (candidate) | `legacy_findings` with spans and model metadata | Verifier results |
| Accepted finding | Review action record | Evidence log |
| Finding kinds, limits, entry-point rules, exclude patterns | Versioned files in `config/legacy/` | Unit tests per rule |

## 11. Data for the build and the tests (G8)

| Set | Purpose | Licence action |
|---|---|---|
| **Synthetic legacy repository** we write: a small Java 8 billing and order system (about 5,000 to 10,000 lines), an old Maven or Ant build, mixed styles, dead code, misleading comments, 40 seeded business rules, 5 deliberately ambiguous rules | Answer key for recall and precision. Source of the real sample finding for the site and the deck | Our own code. `SOURCE.md` |
| Spring PetClinic | Smoke test for a modern build and the SCIP path | Record in `LICENCES.md` (datasets) |
| Apache OFBiz (subset of about 100,000 lines) | Scale, cost and time per thousand lines on a real legacy-style ERP | Record in `LICENCES.md` |
| One public C# or C++ project | Only when a language pack is in scope (EXL11) | Record before use |

## 12. Metrics and pass rules

### Demo gate (closes the evidence for claim `findings-sourced`)

On the synthetic repository, after human review:

- 100% of rendered statements have a citation that passes V1 to V6 (by construction, and tested).
- Statement precision 90% or more (reviewer judgement against the answer key).
- Recall of seeded rules 80% or more.
- Each of the 5 ambiguous rules is labelled inferred or gap, never confirmed.
- Baseline: the same frontier model with whole files and no verifier. Record its rate of invalid citations. The comparison goes into the sales material only with its numbers.

### Assess-ready gate (before the first paid Assess)

On the OFBiz subset:

- Model cost and wall-clock time per 1,000 lines recorded.
- Median reviewer time per finding recorded. Proposed target: 60 seconds or less.
- Gap rate and label distribution recorded.
- Evidence pack complete for the run.

### Ongoing

- Re-run the baseline every month (as EXK7). A drop of more than 1 point in precision blocks a route or prompt change (G10).

## 13. Cost estimate (to confirm in EXL2)

- **Model cost.** Assumption: about 10 to 12 tokens per line of Java, and about 4 to 5 reads of each line across S3 to S5 with context. A 500,000-line system then needs about 25 to 30 million input tokens and about 3 million output tokens. At an assumed list price of 3 US dollars per million input tokens and 15 per million output tokens, this is about 120 to 140 US dollars per full run. This is below 1% of the planned Assess fee. Model costs are tracked apart from the server limit (CLAUDE.md).
- **Compute.** SCIP builds need more memory than the shared EU host has. Proposal: an on-demand EU server per job, deleted after the job, or the client's own environment. A permanent server for analysis would break the 10 dollar limit. Decision needed (section 17).

## 14. Proposed phases

Prefix **EXL** (Legacy). Estimates are founder hours, to check against real phases.

| Phase | Objective | Depends on | Gate | Est. hours |
|---|---|---|---|---|
| **EXL0** | Scope and clean-room gate. No code. Employment check recorded. L-G1 to L-G8 added to `CLAUDE.md`. Decision on any earlier analyser code (section 17). Corpus licences recorded | — | Nothing else in EXL starts before it | 4 |
| **EXL1** | Test corpus: synthetic legacy repository, answer key (40 rules, 5 ambiguous), public sets with `SOURCE.md` | EXL0 | Gates EXL2, EXL8 | 20 |
| **EXL2** | Probe, time-boxed to 5 working days: tree-sitter facts, one model route, a prototype verifier on the corpus. Measure tokens per line, invalid-citation rate, precision on seeded rules. Record results in the spec implementation notes. Probe code is not merged | EXL1 | Decisions on SCIP, model routes and cost | 20 |
| **EXL3** | Snapshot ingest and code facts: S0 to S2, code graph tables, sandboxed SCIP, entry points, data access, integrations, SBOM, git signals without names | EXK1, EXL2 | L-G5 test; FCT tests | 30 |
| **EXL4** | Finding contract and verifier: record of section 7.2, checks V1 to V7, label rules | EXK3, EXK4, EXL3 | L-G1, L-G2, L-G3 tests. Independent subagent review | 20 |
| **EXL5** | Explain and extract: S3 to S5 through the gateway, schemas per kind, second pass | EXK2, EXK5, EXL4 | G3 grep check; L-G4 log test | 30 |
| **EXL6** | Code-span review screen on the core queue | EXK6, EXK6-ui, EXL5 | Review actions with audit; correction re-runs checks | 20 |
| **EXL7-p1** | Traceable specification in HTML (brand components, the Trace), system map, questions and gaps | EXL6, EXD3 | **Demo gate** (section 12). Then set claim `findings-sourced` to `ready` and replace the invented sample finding with a real one | 16 |
| **EXL7-p2** | PDF report, risk register, SBOM, evidence pack, retention job | EXL7-p1, EXD4, EXK8 | L-G6, L-G8 tests | 16 |
| **EXL8** | Analyser evaluation and baseline on the corpus and the OFBiz subset | EXL7-p1, EXK7 | **Assess-ready gate** | 16 |
| **EXL9** | Pilot kit (Stage 2): characterisation tests from accepted findings, mutation check that the tests can fail | EXL7-p2 | Gates the first Pilot offer | 30 |
| **EXL10** | Client-environment bundle: compose file, the client's own model endpoint or an Apache 2.0 open model, offline mode | EXL5 | Runs end to end with no outbound call except the configured model | 24 |
| **EXL11** | Second language pack (C# or C++, choose after the first client call) | EXL5 | Facts and verifier tests for the new language | 30 |

### Order and the fast lane

```
EXL0 → EXL1 → EXL2 (probe)
EXK1 ─┐
EXK2 ─┼→ EXK3 → EXK4 → EXK5 → EXK6 ──────────────┐
      └→ EXL3 → EXL4 → EXL5 ───────────────────────┼→ EXL6 → EXL7-p1 → EXL7-p2 → EXL9
                                     EXD3 → EXK6-ui ┘          └→ EXL8      EXL5 → EXL10, EXL11
```

- The analyser needs the core up to EXK6. That is the "build the core once" rule. Build only the slices the analyser needs first: in EXK1, tenants, jobs, files, hashes and the event log (page split can wait as EXK1-p2 for Claims and Product Data).
- **EXL2 gives a private sample output in about 2 to 3 weeks.** It can go to the discovery call only if it is labelled "prototype output on public or synthetic code". The public site claim waits for EXL7-p1. The EXD5 build gate already enforces this.
- Rough total to the demo gate: about 270 hours (EXL0 to EXL7-p1 plus the core slices). That is about 13 to 14 weeks at 20 hours per week, or about 7 weeks with both founders.

### Fit with the proposal timeline

1. Discovery call: show the method, the deck and, if ready, the labelled probe output. Ask for language, size, build tool, target state and data region.
2. Proposal: offer Assess at a fixed price. State that the analyser runs in the EU region or in the client's environment.
3. If the client signs before EXL8, deliver Assess with the analyser at its current phase and more human review. Do not sell a capability the analyser does not have yet.

## 15. Market and competition (desk research, 19 November 2026)

- Hyperscaler tools now offer analysis and transformation at scale. AWS Transform custom has codebase analysis in Frankfurt. A vendor with strong in-house engineers can try this first.
- Consultancies publish AI-assisted reverse engineering results (for example, module analysis cut from weeks to fewer weeks). Speed alone is not a difference.
- Academic and industry work agrees on three points: deterministic parsing first, traceability per claim, and human review. None of the public tools sells a mechanically verified citation per statement with a labelled gap list as the core promise. This is our position: "AI you can audit".

## 16. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| A founder's employment contract blocks work in this service line | The work and the site stop | EXL0 gate. EXW3 already needs the contract check. Clean room (L-G7) |
| The client's build does not compile in our sandbox (old JDK, Ant, private repositories) | No SCIP index, weaker call graph | Tree-sitter fallback for every file. Label calls from the fallback as "inferred". Ask for the build command on the call |
| The verifier passes a statement whose meaning is wrong | A wrong rule with a valid citation | The citation proves where, not what. Human review of every finding in v1. Precision measured in EXL8 |
| Too many findings for one reviewer in 3 to 4 weeks | Assess overruns | Scope by module. Review only `business_rule`, `calculation` and `state_transition` by default. Show the rest as inferred |
| The model provider changes terms or region support | In-region promise at risk | Endpoint register with terms. Second provider. Client-environment option with an open model |
| Client code leaks through logs or support tickets | Loss of trust, legal exposure | L-G4 tests. No code in logs. Retention job |
| Running client build scripts executes hostile code | Host compromise | L-G5 sandbox: no network, no secrets, throw-away container |
| Frontier models get much better at whole-repository reading | The analyser looks less needed | The asset is the verified, reviewed evidence and the process, not one model. Monthly baseline |
| One founder delivers alone | Slow build | Small phases. Fast lane. Probe first |

## 17. Open questions and decisions needed

| Item | Blocks | Proposal |
|---|---|---|
| Employment contract check for work in legacy modernisation, recorded | EXL0 | Do it before any analyser code |
| Is any earlier analyser code (for example a LangGraph build) personal work made outside employment? | EXL0 | Reuse only if yes, and only with a written note. Else start clean |
| Orchestration: Temporal only (stack rule), or a LangGraph agent inside a Temporal activity | EXL5 | Temporal plus plain schema-constrained calls in v1. Add agent loops only if EXL2 shows a gain |
| EU primary and cross-check model routes, with data terms | EXL2, EXL5 | Bedrock EU (Claude) plus Mistral EU with zero data retention. Record in the endpoint register |
| Compute for SCIP builds and large runs within the server cost limit | EXL3 | On-demand EU server per job, deleted after, or the client's environment |
| Default retention for client code after handover | EXL7-p2 | 30 days, set per contract |
| First client's languages and build tools | EXL11 | Ask on the discovery call. Java and Kotlin first; job adverts of the prospect name Java, Kotlin, Spring, Hibernate and SQL, and some C# |
| Do we show the probe output to a prospect before the demo gate? | EXL2 | Yes, privately, labelled as a prototype on public or synthetic code |

## Sources

- Industry COBOL and PL/I requirements pipeline, ACL 2026 Industry Track: https://aclanthology.org/2026.acl-industry.4.pdf
- Reversa framework (confirmed, inferred, gap labels): https://www.alphaxiv.org/abs/2605.18684
- Citation-grounded code comprehension and mechanical citation checks: https://arxiv.org/abs/2512.12117v1
- Codebase-Memory, tree-sitter knowledge graph via MCP: https://arxiv.org/abs/2603.27277
- scip-java (Apache 2.0, compiler plugin, build tool support): https://sourcegraph.github.io/scip-java/docs/getting-started.html
- AWS Transform custom codebase analysis, general availability (Frankfurt): https://aws.amazon.com/about-aws/whats-new/2026/03/transform-custom-new-codebase-analysis
- Bedrock inference options and data residency: https://docs.aws.amazon.com/bedrock/latest/userguide/models-region-compatibility.html
- Mistral regional inference and zero data retention: https://mistral.ai/cloud/inference/
- Apache 2.0 open coding models: https://www.morphllm.com/qwen3-coder and https://community.groq.com/t/new-model-family-devstral-2/827
- cdxgen (CycloneDX generator): https://github.com/cdxgen/cdxgen
- Characterisation testing: https://en.wikipedia.org/wiki/Characterization_test
- Prospect job advert (Kotlin or Java, Spring, Hibernate, SQL): https://jobleads.com/de/job/e13e3a736351cbfaf9d5e4f80f9083d0e
