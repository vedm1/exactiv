# PRD-L — Exaktiv Legacy Analyser (traceable reverse engineering for the Assess stage)

Version 0.4 · 20 November 2026 · Status: approved by the user on 20 November 2026. Phases EXL0 to EXL14 are in `PHASES.md` · Written in ASD-STE100

## Change log

| Version | Date | Change |
|---|---|---|
| 0.1 | 19 Nov 2026 | First plan |
| 0.2 | 20 Nov 2026 | Decisions recorded (section 19). Workflow engine: DBOS Transact. Positioning corrected: line citations are table stakes, not a difference (section 6). Tiered review with published precision. Stale-finding detection. Scale design to 5 million lines. New sections: web UI, agent access (MCP and CLI), continuous mode. New phases EXL3-ui, EXL12, EXL13 |
| 0.3 | 20 Nov 2026 | Agent access revised: CLI with a skill file first, remote MCP second; five tools in place of ten; token budget (L-G12) |
| 0.4 | 20 Nov 2026 | Client keys (BYOK) and model route per stage from a qualified catalogue (section 8.7). Organisation and tenant model (section 8.8). Pricing (section 17). Guardrails L-G13 to L-G15. Public self-serve sign-up deferred. New phase EXL14. Phases added to `PHASES.md` |

## 1. Summary

The Legacy Analyser reads a legacy code base and writes a specification in plain language. Each statement in the specification links to a file, a line range and a commit in the client's code. A deterministic verifier checks every link before a statement becomes a finding. A statement that fails the check is not stored. It goes to the "gaps" list. A person accepts each finding, or the finding stays labelled "inferred".

When the code changes, the analyser finds the findings whose code changed, marks them "stale", and sends only those back to review. The specification shows how fresh it is at every commit.

The analyser is the engine behind the **Assess** stage on the website and in the capability deck: a traceable specification, a system map, a risk register, target architecture options and a roadmap, in 3 to 4 weeks at a fixed price. After the assessment, continuous mode keeps the specification current as a recurring service.

The analyser is a third product track on the Exaktiv core. It reuses the core contract: no value without a source (G1), abstain and do not guess (G2), validate before storage (G4), review queue (EXK6) and evidence pack (EXK8). The only new idea for the core is a new location type: a **code span** in place of a page area. Durable workflows run on **DBOS Transact** (decision of 20 November 2026, section 19).

## 2. Why now

| Driver | What it needs from the analyser | Where it is recorded |
|---|---|---|
| A European software vendor asked for a legacy modernisation proposal | A sample output to show on the discovery call, and a tool to deliver the Assess stage | Capability deck, slides 4 to 6 (`docs/sales/`) |
| Website claim `findings-sourced` ("Every finding links to its source") | "A demo output from our legacy analyser that shows file and line links". The claim is `to_confirm`. The EXD5 build refuses its footnote until it is `ready` | `site/claims.yaml`, PRD-W §6, EXW3 |
| Sample finding on the site and in the deck (`billing/Invoice.java:142`) | Today it is invented code. The analyser can make it a real output on our own synthetic code | `site/pages/legacy-modernisation.html.j2` |
| EU rules for software vendors (CRA, Data Act, NIS2) | A dependency inventory, an SBOM and an evidence trail as Assess outputs | PRD-W §5, deck slide 7 |

## 3. Goals and non-goals

### Goals (v1)

1. Turn a code base snapshot into a traceable specification. Every statement cites file, lines, commit and a hash of the cited text.
2. Collect structural facts without a model: inventory, modules, entry points, call and dependency graph, data access, external integrations, SBOM.
3. Use models only to explain and to extract rules, and only on top of the facts.
4. Label each statement **confirmed**, **inferred** or **gap** with rules in code. The model does not choose its own label.
5. Review by tiers: a person reviews every finding of the critical kinds, and a random sample of the other kinds. Publish the measured precision with its sample size and confidence bound.
6. Produce the Assess deliverables: traceable specification, system map, risk register, dependency inventory with SBOM, open questions, evidence pack.
7. Keep the specification current when the code changes (continuous mode).
8. Give the same accepted findings to people in a web UI, and to coding agents (Claude Code, Codex, Cursor and others) through a CLI with a skill file (default) and a remote MCP server (second option), within a token budget.
9. Scale to 5 million lines per tenant with incremental runs.
10. Run in our EU region, or inside the client's own environment.
11. Let client admins use their own provider keys (BYOK) and choose a qualified model route per model stage.
12. Support several tenants inside one client organisation, with full isolation between tenants.

### Non-goals (v1)

- No automatic code change, refactor or migration. Stage 2 (Pilot) is a separate track (EXL9). Coding agents can change code; the analyser tells them what the code does today.
- No "fully automated modernisation" claim (banned in PRD-W §6).
- No binary or black-box reverse engineering (no source code). Possible later.
- No model training or fine-tuning on client code.
- No languages beyond Java and Kotlin with full depth in v1. Other languages get "structure only" through tree-sitter until a language pack exists (EXL11).
- No public self-serve sign-up (deferred, decision of 20 November 2026). The team sets up each organisation and engagement. After set-up, client admins manage their own tenants, repositories, keys, model routes and reviewers.
- No promise that a specification is "always up to date". The promise is that every finding shows the commit it was verified at, and that changed code is flagged fast (section 9.3).

## 4. Users

| User | Need |
|---|---|
| Exaktiv delivery lead (today: one founder) | Produce an Assess report in 3 to 4 weeks with most effort on judgement, not on reading code |
| Client engineer (reviewer and system owner) | Check a statement in the code in seconds: the statement on one side, the highlighted lines on the other. Answer open questions |
| Client developer with a coding agent | Before a change: ask which accepted rules a file holds. After a change: see which rules the diff touches |
| Client engineering leader (buyer) | A clear system map, a risk register and options, with evidence. Freshness of the specification over time |
| Client security reviewer | Proof that the code stayed in region, was not used for training, was deleted on time, and that only named people saw it |
| Client CI pipeline | A read-only check per push that reports touched and stale findings |

## 5. What the research says, and the design choice it drives

| Finding | Design choice |
|---|---|
| An industry pipeline on 3.4M lines of COBOL put deterministic parsing first. LLM-only trials gave more hallucinations, higher token cost and weaker structural coverage. It reported a speed-up of about 3.2 to 3.3 times and 93% agreement with manual rule analysis, and it still needed human correction | Facts first (EXL3), model second (EXL5). The model gets graph facts and code, not the whole repository |
| The same pipeline checks that every program, paragraph and data item the model names exists in the symbol tables | Verifier check V5: every identifier in a statement must exist in the cited span |
| A 2026 framework (Reversa) labels each claim confirmed, inferred or gap, and writes `questions.md` and `gaps.md`. Its own confidence index was not an independent audit | Same three labels, but computed by the verifier and by rules in code (L-G3), plus an independent precision measure (L-G9) |
| A study of citation-grounded code comprehension found models that invent files and cite line ranges past the end of a file. Mechanical citation checks catch these | Verifier checks V1 to V3 run on every statement. A failed check drops the statement (L-G1) |
| Tree-sitter based code graphs in SQLite or Postgres are enough for agent queries over large repositories; heavy graph databases are not necessary | Code graph in Postgres tables with recursive queries. No Neo4j (cost limit, stack rule) |
| scip-java gives precise definitions and references, but it runs as a compiler plugin: the build must work. It does not support Java 7 or Ant builds | SCIP when the build works, in a sandbox. Tree-sitter as the fallback for every file. Record which source each edge came from |
| Characterisation (golden master) tests pin what legacy code does today, and are a standard way to prove old and new behave the same | Stage 2 pilot kit (EXL9) generates characterisation tests from accepted findings, and uses mutation testing to prove the tests can fail |
| MCP is the common protocol for coding agents. Claude Code, Codex CLI, Cursor and VS Code with Copilot connect to remote MCP servers with OAuth | One MCP server serves all agent clients (section 9.2). No plugin per IDE in v1 |
| MCP tool definitions and results cost context tokens on each request; a CLI costs nothing until called. Lazy loading in current clients makes the gap smaller | CLI with a skill file is the default agent entry point; MCP is the second option; five tools; token budget L-G12 |

## 6. Position and differentiators (corrected 20 November 2026)

Version 0.1 said that no public tool sells a citation per statement. That is wrong. AWS Transform maps each extracted rule to exact source lines, and DeepWiki (Cognition, the makers of Devin) answers with line-level citations. **Citations are table stakes.** The difference is what happens after the citation.

| Competitor | What it is | Where it pulls the client |
|---|---|---|
| Kiro, with AWS Transform | AWS's spec-driven agentic IDE. AWS Transform does the reverse engineering, with source-line traceability per rule | AWS |
| Devin, with DeepWiki | Autonomous agent at very large scale. Customers used DeepWiki on 5 million lines of COBOL | AWS (strategic agreement since September 2026) |
| IBM Bob | Agentic development partner. Java package for version upgrades, UI modernisation and moves to WebSphere Liberty | IBM runtimes |

Our five differentiators:

1. **Verified, labelled and accepted.** Code checks every citation (V1 to V8). Rules set confirmed, inferred or gap. A named person accepts each critical finding. We publish the measured precision of each report with its sample size and confidence bound (L-G9). The report shows what we do not know.
2. **Independent from any platform.** We sell no runtime and no cloud. Our target architecture options can be neutral.
3. **Evidence the client can pass on.** The evidence pack (snapshot hash, model calls, checks, acceptances) supports the client's own answers to NIS2 supply-chain questions and CRA documentation duties.
4. **Findings that know when they are out of date.** A finding becomes stale when its cited code changes (section 9.3). A regenerated wiki cannot show what changed after a person reviewed it.
5. **A fixed-price outcome, not a tool to adopt.** We deliver the assessment. The analyser can run inside the client's environment with an open model.

**Where we do not compete:** raw scale of autonomous change, code transformation, migration execution. Position these tools as the next step: our accepted specification, our CLI and our MCP server can feed Kiro, Devin, Bob, Claude Code or Cursor in Stage 2. "Use any tool to change the code. Use us to know what the code does, with proof."

## 7. Inputs and outputs

### Inputs

- A code snapshot: a git bundle (preferred, gives history) or an archive of the source tree, with the commit SHA. Upload by the client, or a read-only connection to the client's git host. No write access to the client's repository.
- For continuous mode: a read-only webhook, a CI step (`exaktiv sync`) or a scheduled pull (section 9.3).
- Optional: build files and a build command for the SCIP index, database schema (DDL), API specifications, existing documents. Documents are supporting evidence only (L-G2).
- Engagement configuration: tenant, region, retention period, reviewers, scope (modules in and out), review tiers.

### Outputs (map to deck slide 6)

| Output | Content | Built from |
|---|---|---|
| Traceable specification | Per module: purpose, entry points, business rules, validations, calculations, state changes, error handling, integrations. Each statement with its citation, label and the commit it was verified at | Accepted findings |
| System map | Modules, dependencies, data flows, external systems, third-party components | Code graph (deterministic) plus accepted integration findings |
| Risk register | Untested areas, complexity hot spots, high-churn files, knowledge held by few people (counts only, no names), outdated or vulnerable dependencies, dead code candidates | Deterministic signals plus accepted risk findings |
| Dependency inventory and SBOM | CycloneDX JSON, with licences and known vulnerabilities | cdxgen or Syft, plus a vulnerability scan |
| Questions and gaps | Each gap with the code it concerns and the question for the client | Gap list |
| Target options and roadmap | Two or three options with trade-offs, and a staged roadmap | Written by the delivery lead from the outputs above. The analyser gives inputs only |
| Precision statement | Measured precision per finding kind, with sample size and confidence bound | Tiered review (section 10.4) |
| Behaviour change report (continuous mode) | Per release or per period: which accepted rules changed, were added or were removed | Specification versions (section 9.3) |
| Evidence pack | Snapshot hash, every model call, every check result, every review action | Core event log (EXK1) and EXK8 |

## 8. How it works

### 8.1 Pipeline (one DBOS workflow per snapshot)

```
S0 Ingest      snapshot → object storage (SHA-256 per file and per tree), manifest, line index
S1 Facts       tree-sitter on all files; SCIP index in a sandbox if the build works;
               entry points, data access, integrations, SBOM, git signals  →  code graph tables
S2 Partition   modules from packages and build modules, refined by communities in the call graph
S3 Explain     bottom-up: symbol → file → module summaries; each sentence cites spans      [model]
S4 Extract     per module: rules, validations, calculations, state changes, integrations  [model]
               schema-constrained JSON; kinds and limits come from config/legacy/
S5 Verify      deterministic checks V1–V8 on every statement; second independent pass for
               cross-check; label confirmed / inferred / gap by rule
S6 Review      core review queue (EXK6) with a code-span screen; tiered by kind
S7 Synthesise  system map, module specs, cross-module flows from accepted findings only
S8 Render      HTML and PDF report (EXD4), SBOM, questions, precision statement, evidence pack
```

Each stage is a DBOS step. Each module in S3 to S5 runs as its own child workflow on a DBOS durable queue. A failed step resumes from the last completed step. The workflow state lives in the same Postgres database (Neon Frankfurt for EU).

### 8.2 Finding record (extends FR-EXT-3 with a code location)

| Field | Content |
|---|---|
| `finding_id`, `tenant_id`, `job_id` | Core identifiers |
| `snapshot_id` | Snapshot of one commit: commit SHA plus tree manifest hash |
| `kind` | From `config/legacy/finding_kinds.yaml` (for example `business_rule`, `validation`, `calculation`, `state_transition`, `entry_point`, `integration`, `data_access`, `error_handling`, `security_control`, `risk_signal`) |
| `tier` | `critical` or `sampled`, from configuration per kind |
| `statement` | Plain language, length limit from configuration |
| `spans[]` | `path`, `start_line`, `end_line`, `span_sha256` (of the normalised text), `symbol_id` (SCIP or tree-sitter qualified name), `role` (`primary` or `supporting`) |
| `identifiers[]` | Code names the statement uses (class, method, field, table, constant) |
| `label` | `confirmed`, `inferred` or `gap`, set by rules (L-G3) |
| `status` | `candidate`, `accepted`, `rejected`, `stale`, `superseded` |
| `verified_at_commit` | The last commit at which V1 to V8 passed for this finding |
| `lineage` | The finding this one supersedes, if any |
| `model_id`, `model_version`, `route_version`, `prompt_version`, `raw_output_ref` | Model metadata (G1) |
| `checks[]` | Result of V1 to V8 with reasons |
| `confidence`, `calibration_version` | Core EXK5 fields |

### 8.3 Verifier (deterministic, runs before storage and on every new commit)

| Check | Rule | On failure |
|---|---|---|
| V1 | The path exists in the snapshot manifest | Drop the statement. Record the reason |
| V2 | The line range is inside the file, and not longer than the limit in configuration | Drop |
| V3 | The hash of the cited lines, read again from the original in object storage, equals `span_sha256` | Drop (new statement) or mark `stale` (existing finding) |
| V4 | The cited symbol's definition overlaps the span | Drop |
| V5 | Each identifier in `identifiers[]` and in the statement text appears in the cited spans or in their direct graph neighbours | Drop |
| V6 | `kind` is in the configured list. Fields match the schema | Drop |
| V7 | A statement about a call, a dependency or a data flow matches an edge in the code graph | Label `inferred` at best |
| V8 | Re-anchor: on a new commit, if the cited text moved (same normalised hash, same symbol, other line numbers), move the span and keep the finding | If no match: `stale` |

Label rules (in code, not in prompts):

- **Confirmed**: V1 to V8 pass, and either the fact comes from the graph, or a second independent pass (other prompt and, where possible, other model provider) gives the same rule with overlapping spans.
- **Inferred**: V1 to V6 pass, but there is only one pass, or V7 fails, or the evidence is names or comments only, or a finding of the `sampled` tier was not in the review sample.
- **Gap**: the system cannot answer safely. It records the question and the code area. A gap is a deliverable, not a failure.

### 8.4 Data store

Postgres tables (Alembic revisions on top of EXK1): `legacy_snapshots`, `legacy_files` (content-addressed by hash), `legacy_symbols`, `legacy_edges` (with `source` = `scip` or `tree_sitter`), `legacy_findings`, `legacy_finding_spans`, `legacy_checks`, `legacy_spec_versions`. Every table has `tenant_id` (G6). Large tables are partitioned by tenant. Object storage: original snapshot, SCIP index, rendered reports. Search: Postgres full text plus graph expansion in v1. Embeddings (pgvector) only if EXL8 shows a recall gain. DBOS keeps its workflow state in its own schema in the same database.

### 8.5 Models and regions

All calls go through the core gateway (EXK2). No second model path.

| Route | Use | Notes |
|---|---|---|
| EU primary | Explain and extract (S3, S4) | A frontier model through an EU endpoint. Candidate: Claude through Amazon Bedrock in an EU region (in-region where the model is offered, else the EU geographic profile, which keeps prompts and outputs inside the EU) |
| EU cross-check | Second pass (S5) | A different provider where possible. Candidate: Mistral through its EU regional endpoint with zero data retention |
| Client environment | All model steps | The client's own endpoint, or an open model under Apache 2.0 (for example Qwen3-Coder-30B-A3B or Devstral Small 2) on the client's hardware |
| India | Later | Only when an India client exists (EXK0c) |

Each route, its data terms and its licence go into the model endpoint register (open item in the build plan) and `LICENCES.md` (G12).

### 8.6 Scale design (target: 5 million lines per tenant)

| Limit | Design |
|---|---|
| Model tokens | Content-addressed cache: a symbol whose hash did not change is not sent to a model again. Batch API where the provider offers it. Prompt caching for shared context |
| Wall-clock time | One child workflow per module on a DBOS queue, with a concurrency limit per tenant and per model route |
| Database size | Partitions by tenant; graph queries limited by depth; old snapshots compacted to the files that changed |
| Compute | The $15 EU server runs jobs up to about 500,000 lines. Larger first runs use a burst EU server or the client's environment (EXL10) |
| Human review | Tiered review with sampling (section 10.4). Review is the true limit, not compute |

### 8.7 Client keys (BYOK) and model route per stage

After the team sets up the engagement, a client admin enters the client's own provider keys and chooses a model route for each model stage. BYOK is the default. The client pays its provider directly, so model cost is not part of the Exaktiv price (section 17). The provider is the client's own sub-processor, not ours.

Only three stages use a model. All other stages, the verifier V1 to V8 and the label rules use no model and are not configurable (G3).

| Stage | Model use | Client choice |
|---|---|---|
| S3 Explain | Summaries with citations | One qualified route |
| S4 Extract | Rules and other findings, schema-constrained | One qualified route |
| S5 Verify, cross-check pass | Second independent pass | One qualified route from a **different provider** than S4 (L-G14) |

Rules:

- **Qualified catalogue (L-G13).** A route is a model, a provider endpoint and a version. A route is "qualified" when it passed the EXL8 evaluation on the test corpus for that stage. The catalogue shows its measured precision, its cost per 1,000 lines and its date. The client can also choose an unqualified route. Then the run and the report say "unqualified route", and the precision statement uses only that tenant's own review sample (L-G9).
- **Route change = gate record (G10).** A new route for a tenant needs a passed gate record for that tenant before a report uses it.
- **Region (G7).** The gateway accepts only endpoints on the region allowlist of the tenant's region (for example the Bedrock EU regions or the Mistral EU endpoint). An unknown endpoint is refused. The client declares the endpoint region; the gateway checks the endpoint address against the allowlist.
- **No fallback.** If the client's key fails, is revoked or hits its quota, the task fails and retries later. It never uses our key or another route.
- **Cost control.** Before a run, the UI shows a cost estimate per stage from the tokens per line measured in EXL8. Each run has a budget cap. The workflow pauses at the cap and waits for a client admin.
- **Keys (L-G15).** Keys are stored encrypted per tenant in a key vault (choice in the EXL14 spec: encrypted columns in Postgres with a key per tenant, or OpenBao; licence check G12). Keys are write-only in the UI: never shown again, never in logs, metrics or events. Rotation and revocation are supported. Every key use writes an event with the key ID, never the key.
- **Managed models (add-on).** A client without a provider contract can use Exaktiv-managed routes. Then Exaktiv's key is used, and model cost is billed at cost plus a margin.

### 8.8 Organisation and tenant model

```
Organisation ── tenants (workspaces) ── engagements ── repositories
```

| Level | Holds |
|---|---|
| Organisation | Users, org admins, billing, default keys and default model routes, configuration templates (review tiers, retention). Single sign-on later |
| Tenant | Its own region, key overrides, model routes, retention, reviewers and all data. One tenant per business unit or product line |
| Engagement | Repositories, runs, findings, specification versions |

Rules:

- **G6 holds inside the organisation.** Data, findings, corrections and evaluation sets never cross tenants. There is no search across tenants.
- **Org admins see totals only** across tenants: freshness, open reviews, run count, model cost.
- **Roles are per tenant.** One person can be a reviewer in one tenant and a viewer in another.
- **Each tenant has its own region.** Two tenants of one organisation can be in different regions.
- **API keys (EXK11) are scoped to organisation and tenant.** A CLI key for tenant A cannot read tenant B.
- The organisation table is a core change: it goes into EXK1 (tables) and EXK11 (key scopes) before they are built.

## 9. Product surfaces (new in version 0.2, for review)

### 9.1 Web UI

The UI is part of the one Exaktiv React app (`ui/`), built on the EXD3 components and the brand rules in `brand/README.md`. The brand rule "no monospace anywhere, also not for code" applies to the code viewer too: code shows in Instrument Sans with tabular figures for line numbers. EXL6 must test that indentation stays readable (open item, section 20).

Roles: **Exaktiv lead** (all actions), **org admin** (tenants, defaults, totals), **client admin** per tenant (connect the repository, set retention, enter keys, choose model routes, invite people), **client reviewer** (review findings, answer gaps), **client viewer** (read only).

| Screen | What the user sees | What the user can do |
|---|---|---|
| Engagements | List of engagements per tenant: region, last commit analysed, freshness, open review count | Open an engagement. Create one (Exaktiv lead only) |
| Ingest and runs | Each run: commit, stage S0 to S8 with progress, files parsed, parse errors, build result (SCIP or tree-sitter only), model cost (Exaktiv lead only) | Upload a git bundle or archive. Connect a repository read-only. Set scope and exclude patterns. Start, pause or cancel a run |
| System map | Module-level graph: modules, dependencies, external systems, data stores. Size and colour by lines, churn or risk | Zoom into one module. Filter by kind of edge. Open a module's specification |
| Code graph explorer | For one symbol: callers, callees, data access, entry points, up to 2 hops. The source of each edge (SCIP or tree-sitter) | Search a class, method or table. Jump to the code. See the findings on that symbol |
| Specification reader | Module specification in plain language. Each statement with its label, its footnote citation and its verified commit. Stale findings marked | Click a citation: the code opens beside the statement with the lines highlighted. Export the module |
| Review queue | Statement, kind, tier, label, check results, cited code with highlight, the model's alternatives | Accept, correct (statement or span), reject, change to gap. Keyboard-first |
| Gaps and questions | Each open question with the code area | Answer a question. The answer is stored as "client statement" evidence: supporting only (L-G2) |
| Risk register and SBOM | Risks with evidence. Dependencies, licences, known vulnerabilities | Filter. Export CycloneDX |
| Changes and freshness | Per commit: new, changed, stale and removed findings; share of accepted findings verified at the latest commit | Compare two specification versions. Open the behaviour change report |
| Reports | Assess report (HTML, PDF), precision statement, evidence pack | Download. Approve for release to the client (L-G8) |
| Settings | Region, retention, provider keys (write-only), model route per stage with its qualified status, precision and cost, run budget cap, review tiers, people and roles, repository connections, CLI, MCP and API keys | Change the settings the role allows. Client admins enter keys and choose routes |
| Organisation | Tenants and their regions, users and roles per tenant, default keys and routes, totals across tenants | Org admins create tenants and set defaults |

The UI never edits the client's code and never starts a migration.

### 9.2 Agent access: CLI first, MCP second (revised 20 November 2026)

Yes, a client developer can use the analyser from Claude Code, Codex, Cursor, VS Code with Copilot and other agents. There are two thin entry points over the same core public API (EXK11): a **CLI with a skill file** (the default for coding agents) and a **remote MCP server** (the second option). Both have the same five tools and the same result shape.

Why two entry points: an MCP server costs context tokens on the client's agent. Tool definitions go to the model on each request, and tool results can cost more than the definitions. A CLI costs no tokens until the agent calls it. MCP still has a place: standard OAuth login, central control and audit, and clients that cannot run a shell. Current agent clients load MCP tool definitions only when needed, which makes the gap smaller, but not zero.

| Entry point | Use for | Notes |
|---|---|---|
| **CLI `exaktiv` + skill file (default)** | Claude Code, Codex and Cursor on a developer's machine; CI pipelines | One package. The skill file (also an `AGENTS.md` snippet) is short and tells the agent which command to run before a change and before a pull request. No context cost until the agent runs a command |
| **Remote MCP server (second option)** | Clients that cannot install a CLI; clients that need OAuth, central control and audit; chat clients and agent platforms without a shell | One endpoint per region. Tools marked for lazy loading where the client supports it |

Design rules (both entry points):

- **Return findings and citations, not code.** The developer's agent already has the code locally. A result gives IDs, one-line statements, labels, `path:start-end` citations and the verified commit. The agent reads the lines itself. This keeps client code out of results and keeps results small.
- **Compact by default, detail on request.** Every list has a limit and pages. `get` returns full detail for one ID only.
- **No model call on the read path.** Read tools answer from accepted findings and the code graph. This keeps cost low and keeps the answer the same as the reviewed specification.
- **Agents propose, people accept (L-G10).** No tool accepts a finding, changes a label or releases a report.
- **Region.** Our API and MCP server run in the tenant's region. The developer's own agent and its model are the client's choice and outside our region promise. We say so in the security pack. For strict clients, the CLI and MCP server point to an API inside their environment (EXL10).
- **Auth.** CLI: scoped API key per tenant from the secret store of the client's machine or CI. MCP: OAuth 2.1, or a scoped API key. Read-only scope by default.
- **Token budget (L-G12).** All MCP tool definitions together: 2,000 tokens or less. A typical result: 1,500 tokens or less. The skill file: 800 tokens or less. EXL12 tests measure all three and fail above the budget.

The five tools (same names in the CLI as sub-commands, for example `exaktiv rules src/billing --format compact`):

| Tool | Kind | What it returns or does |
|---|---|---|
| `rules_for_paths` | Read | Accepted and inferred findings whose spans are in the given files or folders. Use before a change |
| `impact_of_diff` | Read | For a diff or a branch: the findings whose spans the diff touches, and the findings one graph hop away. Deterministic, no model call. Use before a pull request |
| `search` | Read | Findings, modules or gaps that match a query, a kind or a module. Compact list |
| `get` | Read | Full detail for one ID: a finding, a module specification, the system map to a given depth, or a gap |
| `propose` | Propose | One write tool with a `type`: `correction` (new statement or span for a finding), `change_intent` ("this diff changes rule X on purpose", with the new statement), or `gap_answer` (client answer as supporting evidence). Each creates a review task only |

The CLI has two more commands for CI only, not given to agents by the skill file: `exaktiv sync` (start an incremental run, scope `sync`) and `exaktiv check` (the pull-request status check output, L-G11).

### 9.3 Continuous mode: keep the specification current

Yes, with one honest limit. Code changes all the time. No system can keep a reviewed specification "always" current, because a person must accept a changed rule. The analyser makes staleness **visible, fast and small**: it finds exactly which findings a change affects, re-checks them, and sends only those to review.

Flow per new commit (one DBOS workflow, incremental):

1. **Trigger.** A read-only webhook from the client's git host, a CI step (`exaktiv sync`), or a scheduled pull. Default branch, and optionally release branches.
2. **Delta.** Store only the files that changed (content-addressed). Re-parse only those files. Update the code graph.
3. **Re-anchor (V8).** For each finding whose file changed: if the cited text only moved, move the span and keep the finding. If the text changed, mark the finding `stale`.
4. **Impact.** Mark findings one hop away in the graph "to check" when a dependency they cite changed (for example a constant that a rule uses).
5. **Re-extract.** Run S3 to S5 only on changed and new symbols. Compare each new statement with the stale one it replaces.
6. **Re-confirm or review.** If the new statement matches the old one (same kind, overlapping identifiers, second pass agrees), and the kind is in the `sampled` tier, the finding is re-confirmed automatically and enters the review sample pool. Every `critical` finding that changed goes to the review queue. A changed rule never stays "accepted" without a person (L-G10).
7. **Version.** Write a new specification version. Keep the old one. Produce the behaviour change report.
8. **Report back.** The freshness view in the UI updates. With a standing approval record from the client (L-G11), a read-only status check on the pull request lists touched and stale findings. The specification can also be exported to the client's repository as Markdown through a pull request that the client merges.

Agent loop that prevents staleness at the source: the developer's agent calls `rules_for_paths` before a change, and `impact_of_diff` and `propose` (type `change_intent`) before the pull request, through the CLI or MCP. The review task for the changed rule then exists before the merge.

Promise in the contract: each finding shows its verified commit; a finding whose code changed is marked stale within 15 minutes of the push (target, measured in EXL13); critical changed findings reach the review queue within the same time; the review time is a service level per contract.

## 10. Functional requirements

### 10.1 Ingest

- FR-LEG-ING-1: Accept a git bundle or a source archive with a commit SHA. Store it unchanged with SHA-256 per file and a tree manifest hash.
- FR-LEG-ING-2: Exclude vendored and generated folders by configurable patterns. Record what was excluded.
- FR-LEG-ING-3: Reject a snapshot above the tenant size limit, with the reason.
- FR-LEG-ING-4: Write one event per state change (core event log).
- FR-LEG-ING-5: Accept a read-only repository connection for continuous mode. Never request write access to the client's repository.

### 10.2 Facts

- FR-LEG-FCT-1: Parse every file with tree-sitter. Record parse errors per file. A parse error never stops the job.
- FR-LEG-FCT-2: For Java and Kotlin, try the SCIP index in the build sandbox (L-G5). If the build fails, continue with tree-sitter only and record the reason.
- FR-LEG-FCT-3: Detect entry points by rules in `config/legacy/` (for example `main` methods, HTTP controllers, scheduled jobs, message listeners, servlets).
- FR-LEG-FCT-4: Detect data access (JPA entities, SQL strings, stored procedure calls) and external integrations (HTTP clients, message queues, file transfer, mail).
- FR-LEG-FCT-5: Produce a CycloneDX SBOM and a vulnerability report.
- FR-LEG-FCT-6: From git history, compute churn and knowledge concentration per module. Store counts and shares only. Never store or show author names or e-mail addresses (G11).
- FR-LEG-FCT-7: Process only changed files on a new commit. A symbol whose content hash did not change keeps its facts.

### 10.3 Explain and extract

- FR-LEG-EXT-1: Prompts ask for explanation and extraction only. Kinds, limits, thresholds, tiers and labels live in `config/legacy/` and in code (G3).
- FR-LEG-EXT-2: The model returns JSON against a fixed schema per kind. Invalid JSON goes to retry once, then to "failed" (FR-RTR-5).
- FR-LEG-EXT-3: The model receives the code of the unit, its graph neighbours and the summaries of its callees. It does not receive the whole repository.
- FR-LEG-EXT-4: Every statement carries at least one span. A statement with no valid span is dropped (L-G1).
- FR-LEG-EXT-5: Do not send a symbol to a model again if its content hash and its neighbours' hashes did not change.

### 10.4 Verify, label, review

- FR-LEG-VER-1: Run V1 to V8 on every statement before storage (G4), and on every existing finding whose file changed.
- FR-LEG-VER-2: Set the label by the rules in section 8.3 (L-G3).
- FR-LEG-REV-1: Tiers. Each kind has a tier in configuration. A person reviews every `critical` finding (default kinds: `calculation`, `state_transition`, `security_control`, `business_rule`). For `sampled` kinds, the system draws a random sample per kind and per run; a person reviews the sample.
- FR-LEG-REV-2: Sample size: enough to state precision with a 95% confidence interval no wider than ±5 points, or all findings of the kind if there are fewer. The method and the numbers go into the precision statement (L-G9).
- FR-LEG-REV-3: A `sampled` finding outside the sample keeps the label "inferred" in the report, with the precision of its kind beside it.
- FR-LEG-REV-4: The review screen shows the statement, the label, the tier, the check results and the cited lines with a highlight. Actions: accept, correct (statement or span), reject, change to gap. Each action records user, time, old and new value.
- FR-LEG-REV-5: A correction re-runs V1 to V8.
- FR-LEG-REV-6: The core rule FR-CNF-5 (all values to review until 200 reviewed) applies to auto-accept. Tiered review replaces it only for the "accepted or inferred" label in reports, never for auto-accept.

### 10.5 Deliverables

- FR-LEG-OUT-1: Render the deliverables in section 7 from accepted findings, plus clearly labelled inferred findings and gaps.
- FR-LEG-OUT-2: Each statement in the report shows its citation as a footnote (the Trace in `brand/README.md`) and its verified commit. A statement with no citation is not rendered.
- FR-LEG-OUT-3: Export the evidence pack (EXK8) per snapshot.
- FR-LEG-OUT-4: Delete the snapshot, index and findings at the end of the retention period. Write a deletion record (L-G6).
- FR-LEG-OUT-5: Export the specification as Markdown with citations, for the client's repository.

### 10.6 UI, agent access, continuous mode

- FR-LEG-UI-1: Provide the screens in section 9.1, with the role rights stated there.
- FR-LEG-UI-2: The system map shows modules first; a symbol-level graph shows at most 2 hops around one symbol.
- FR-LEG-MCP-1: Provide the CLI `exaktiv` and a skill file as the default agent entry point, and a remote MCP server as the second entry point, both over the core API (EXK11), with the five tools in section 9.2.
- FR-LEG-MCP-2: Read tools return findings and citations, never code text, and make no model call. Results are compact by default, with a limit and paging.
- FR-LEG-MCP-3: The write tool `propose` creates review tasks only (L-G10).
- FR-LEG-MCP-4: The CLI also provides `sync` and `check` for CI.
- FR-LEG-MCP-5: Meet the token budget in L-G12, measured in tests.
- FR-LEG-CNT-1: Run the flow in section 9.3 for each new commit on the configured branches.
- FR-LEG-CNT-2: Keep every specification version. Produce a behaviour change report between any two versions.
- FR-LEG-CNT-3: Show freshness: the share of accepted findings verified at the latest commit, per module and in total.
- FR-LEG-CNT-4: Post a pull-request status check only with a standing approval record (L-G11).

### 10.7 Keys, model routes, organisation

- FR-LEG-KEY-1: Client admins enter provider keys per tenant, with an organisation default. Keys are stored as in section 8.7 (L-G15).
- FR-LEG-KEY-2: Client admins choose one route per model stage from the catalogue. The UI shows qualified status, precision, cost per 1,000 lines and date per route.
- FR-LEG-KEY-3: Refuse an S5 route from the same provider as the S4 route (L-G14).
- FR-LEG-KEY-4: Refuse an endpoint outside the tenant's region allowlist (G7).
- FR-LEG-KEY-5: Show a cost estimate before each run. Pause the run at the budget cap.
- FR-LEG-KEY-6: Label every finding, report and precision statement with the route used and its qualified status (L-G13).
- FR-LEG-ORG-1: Model organisations, tenants, engagements and repositories as in section 8.8. Scope every API key to one organisation and one tenant.
- FR-LEG-ORG-2: Org admins see totals across tenants only.

## 11. Legacy guardrails (in addition to core G1–G13)

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

## 12. Source of record additions

| Data | Authoritative source | Cross-check |
|---|---|---|
| Code content | Snapshot original in object storage, by SHA-256 | Hash check on every read (V3) |
| Structural facts | Code graph tables, with the source of each edge | Re-run on the same snapshot gives the same graph |
| Finding (candidate) | `legacy_findings` with spans and model metadata | Verifier results |
| Accepted finding | Review action record | Evidence log |
| Freshness of a finding | `verified_at_commit` | Re-check on the next commit |
| Specification version | `legacy_spec_versions` | Behaviour change report |
| Finding kinds, tiers, limits, entry-point rules, exclude patterns | Versioned files in `config/legacy/` | Unit tests per rule |
| Workflow state | DBOS system tables in Postgres | Event log |

## 13. Data for the build and the tests (G8)

| Set | Purpose | Licence action |
|---|---|---|
| **Synthetic legacy repository** we write: a small Java 8 billing and order system (about 5,000 to 10,000 lines), an old Maven or Ant build, mixed styles, dead code, misleading comments, 40 seeded business rules, 5 deliberately ambiguous rules, and a scripted series of later commits that change 10 rules | Answer key for recall and precision. Test of continuous mode. Source of the real sample finding for the site and the deck | Our own code. `SOURCE.md` |
| Spring PetClinic | Smoke test for a modern build and the SCIP path | Record in `LICENCES.md` (datasets) |
| Apache OFBiz (subset of about 100,000 lines) | Cost and time per thousand lines on a real legacy-style ERP | Record in `LICENCES.md` |
| A large public code base, toward 5 million lines (choose in EXL8) | Scale test of incremental runs, queue and database | Record before use |
| One public C# or C++ project | Only when a language pack is in scope (EXL11) | Record before use |

## 14. Metrics and pass rules

### Demo gate (closes the evidence for claim `findings-sourced`)

On the synthetic repository, after review:

- 100% of rendered statements have a citation that passes V1 to V6 (by construction, and tested).
- Statement precision 90% or more, stated with sample size and 95% confidence interval (L-G9).
- Recall of seeded rules 80% or more.
- Each of the 5 ambiguous rules is labelled inferred or gap, never confirmed.
- Baseline: the same frontier model with whole files and no verifier. Record its rate of invalid citations. The comparison goes into the sales material only with its numbers.

### Assess-ready gate (before the first paid Assess)

On the OFBiz subset:

- Model cost and wall-clock time per 1,000 lines recorded.
- Median reviewer time per finding recorded. Proposed target: 60 seconds or less.
- Review hours for the tiered plan recorded. Proposed target: 40 hours or less per 100,000 lines.
- Gap rate and label distribution recorded.
- Evidence pack complete for the run.

### Scale gate (EXL8)

- A first run on the large public code base finishes with the burst server or a documented client-environment setup.
- A re-run after a commit that changes 1% of files costs 5% or less of the first run.

### Continuous mode gate (EXL13)

On the scripted commit series of the synthetic repository:

- Every changed rule is marked stale. No unchanged rule is marked stale only because its lines moved (V8).
- Stale marking within 15 minutes of the push.
- Every changed `critical` finding reaches the review queue; none stays "accepted" without a person.

### Ongoing

- Re-run the baseline every month (as EXK7). A drop of more than 1 point in precision blocks a route or prompt change (G10).

## 15. Cost estimate (first measured in EXL2, 20 Nov 2026)

- **EXL2 result.** At $2 / $10 per million tokens (Claude Sonnet 5.5): S4 extract $0.10–0.15 per 1,000 lines, S3 explain about $0.08, S5 about as much as S4. Source code costs 11–18 tokens per line. See the EXL2 notes in `EXAKTIV_PHASE_SPECS.md`. The figures below are the earlier assumption.

- **Who pays.** With BYOK (default) the client pays the model cost to its provider. The figures below are for the cost estimate the UI shows, and for the managed-models add-on.
- **First run, model cost.** Assumption: about 10 to 12 tokens per line of Java, and about 4 to 5 reads of each line across S3 to S5 with context. At an assumed list price of 3 US dollars per million input tokens and 15 per million output tokens: about 120 to 140 US dollars for 500,000 lines, and about 1,200 to 1,400 US dollars for 5 million lines, before batch discounts.
- **Continuous mode.** Only changed symbols go to a model. For a commit stream that changes about 1% of the code per week, the weekly cost is a small share of the first run.
- **Server.** One permanent EU server at up to 15 US dollars per month for the analyser (decision of 19 November 2026). Burst servers for large first runs are billed per job and recorded per engagement.
- **Workflow engine.** DBOS Transact is an MIT-licensed library on Postgres. It needs no extra server.

## 16. Proposed phases

Prefix **EXL** (Legacy). Estimates are founder hours, to check against real phases.

| Phase | Objective | Depends on | Gate | Est. hours |
|---|---|---|---|---|
| **EXL0** | Scope gate. No code. Record the accepted employment risk (section 19). L-G1 to L-G15 added to `CLAUDE.md`. Decision on any earlier analyser code. Corpus licences recorded | — | Nothing else in EXL starts before it | 4 |
| **EXL1** | Test corpus: synthetic legacy repository with answer key and scripted commit series, public sets with `SOURCE.md` | EXL0 | Gates EXL2, EXL8, EXL13 | 24 |
| **EXL2** | Probe, time-boxed to 5 working days: tree-sitter facts, one model route, a prototype verifier on the corpus. Measure tokens per line, invalid-citation rate, precision on seeded rules. Record results in the spec implementation notes. Probe code is not merged | EXL1 | Decisions on SCIP, model routes and cost | 20 |
| **EXL3** | Snapshot ingest and code facts: S0 to S2 as DBOS workflows, content-addressed files, code graph tables, sandboxed SCIP, entry points, data access, integrations, SBOM, git signals without names | EXK1, EXL2 | L-G5 test; FCT tests | 30 |
| **EXL3-ui** | Engagements, ingest and run screens | EXL3, EXD3 | Upload, scope, run progress | 16 |
| **EXL4** | Finding contract and verifier: record of section 8.2, checks V1 to V8, label rules, stale status | EXK3, EXK4, EXL3 | L-G1, L-G2, L-G3 tests; re-anchor test. Independent subagent review | 24 |
| **EXL5** | Explain and extract: S3 to S5 through the gateway, schemas per kind, second pass, hash cache | EXK2, EXK5, EXL4 | G3 grep check; L-G4 log test | 30 |
| **EXL6** | Code-span review screen on the core queue, tiers and sampling | EXK6, EXK6-ui, EXL5 | Review actions with audit; correction re-runs checks; sample-size test | 24 |
| **EXL7-p1** | Specification reader, system map, code graph explorer, gaps and questions | EXL6, EXD3 | **Demo gate** (section 14). Then set claim `findings-sourced` to `ready` and replace the invented sample finding with a real one | 24 |
| **EXL7-p2** | PDF report, precision statement, risk register and SBOM views, evidence pack, retention job | EXL7-p1, EXD4, EXK8 | L-G6, L-G8, L-G9 tests | 20 |
| **EXL8** | Analyser evaluation, baseline and scale test | EXL7-p1, EXK7 | **Assess-ready gate** and **scale gate** | 24 |
| **EXL9** | Pilot kit (Stage 2): characterisation tests from accepted findings, mutation check that the tests can fail | EXL7-p2 | Gates the first Pilot offer | 30 |
| **EXL10** | Client-environment bundle: compose file, the client's own model endpoint or an Apache 2.0 open model, MCP server inside the client's network, offline mode | EXL5, EXL12 | Runs end to end with no outbound call except the configured model | 24 |
| **EXL11** | Second language pack (C# or C++, choose after the first client call) | EXL5 | Facts and verifier tests for the new language | 30 |
| **EXL12** | Agent access, CLI first: CLI `exaktiv` with the five tools plus `sync` and `check`, skill file and `AGENTS.md` snippet; then the remote MCP server with the same five tools | EXL7-p1, EXK11 | L-G10 test; result test (no code text); L-G12 token budget test; setup tested with Claude Code, Codex CLI and Cursor, CLI path and MCP path | 24 |
| **EXL14** | Client keys and model route per stage: key vault, route catalogue with qualified status, per-tenant gate records, region allowlist, cost estimate and budget cap, organisation defaults | EXL8, EXK9-p2, EXK11 | L-G13, L-G14, L-G15 tests; no-fallback test; independent subagent review | 30 |
| **EXL13** | Continuous mode: commit sync, re-anchor, impact, re-confirm, specification versions, behaviour change report, freshness view, pull-request status check, Markdown export | EXL8, EXL12 | **Continuous mode gate** (section 14); L-G11 test | 30 |

### Order and the fast lane

```
EXL0 → EXL1 → EXL2 (probe)
EXK1 ─┐
EXK2 ─┼→ EXK3 → EXK4 → EXK5 → EXK6 ─────────────────────┐
      └→ EXL3 → EXL4 → EXL5 ──────────────────────────────┼→ EXL6 → EXL7-p1 → EXL7-p2 → EXL9
          └→ EXL3-ui (with EXD3)          EXD3 → EXK6-ui ─┘          ├→ EXL8 → EXL13
                                                                      └→ EXL12 CLI, then MCP (with EXK11) → EXL10
                                                     EXL5 → EXL11
                                     EXL8 + EXK9-p2 + EXK11 → EXL14 (BYOK, model routes)
```

- The analyser needs the core up to EXK6. That is the "build the core once" rule. Build only the slices the analyser needs first: in EXK1, tenants, jobs, files, hashes and the event log (page split can wait as EXK1-p2 for Claims and Product Data).
- The core moves from Temporal to DBOS before EXK1 (phase EXK0-dbos, section 19). The only Temporal code today is the EXK0 smoke workflow.
- EXK1 adds the organisation table (section 8.8) and EXK11 scopes keys to organisation and tenant. Both changes go in before these phases are built.
- **EXL2 gives a private sample output in about 2 to 3 weeks.** It can go to the discovery call only if it is labelled "prototype output on public or synthetic code". The public site claim waits for EXL7-p1. The EXD5 build gate already enforces this.
- Rough total to the demo gate: about 300 hours (EXL0 to EXL7-p1, EXL3-ui and the core slices). That is about 15 weeks at 20 hours per week, or about 8 weeks with both founders. EXL12, EXL13 and EXL14 add about 84 hours after that. Until EXL14, every run uses Exaktiv-managed routes on synthetic or public code, or a route the team configures for the client.

### Fit with the proposal timeline

1. Discovery call: show the method, the deck and, if ready, the labelled probe output. Ask for language, size, build tool, git host, target state and data region.
2. Proposal: offer Assess at a fixed price. State that the analyser runs in the EU region or in the client's environment. Offer continuous mode as an option after Assess.
3. If the client signs before EXL8, deliver Assess with the analyser at its current phase and more human review. Do not sell a capability the analyser does not have yet.

## 17. Pricing and business scale

With BYOK, model cost is not part of our price. We price the value, not the tokens:

| Item | Price basis |
|---|---|
| Assess | Fixed fee per engagement (service) |
| Platform | Monthly fee per tenant, by size tier: lines under analysis |
| Continuous mode | Monthly retainer; price depends on who reviews (Exaktiv or the client's engineers) |
| Pilot | Separate offer after Assess |
| Managed models (add-on) | Model cost plus a margin, only for clients without their own provider contract |

Open: guardrail G5 ("bill only accepted units") was written for Claims and Product Data. For the analyser, the billing unit must be defined. Proposal: "lines under analysis per month" for the platform fee. Decision needed (section 20).

Business stages:

1. **Year one: services.** Assess and Pilot, delivered by the founders. The team sets up each organisation.
2. **Then: continuous mode as a retainer**, and client admins manage their own tenants, keys and routes.
3. **Then: a licence for partners.** Consultancies and partner agencies run the analyser, the CLI and the MCP server in their own client environments (EXL10).
4. **Deferred: public self-serve sign-up and a public demo.** Gates before any start: 3 paying clients, metering in production, a hardened sandbox, a price per 1,000 lines, and a decision on certification.

## 18. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| A founder's employment contract conflicts with work in this service line | The work or the site may have to stop | Risk accepted by the user on 19 November 2026 (section 19). Clean room (L-G7) stays in force |
| The client's build does not compile in our sandbox (old JDK, Ant, private repositories) | No SCIP index, weaker call graph | Tree-sitter fallback for every file. Label calls from the fallback as "inferred". Ask for the build command on the call |
| The verifier passes a statement whose meaning is wrong | A wrong rule with a valid citation | The citation proves where, not what. Review of every critical finding, sampled review of the rest, published precision (L-G9) |
| Too many findings for one reviewer in 3 to 4 weeks | Assess overruns | Tiered review. Scope by module |
| Automatic re-confirm in continuous mode hides a real change | A stale rule looks current | Only `sampled` kinds re-confirm automatically, and they enter the review sample pool. Critical kinds always go to a person (L-G10) |
| The developer's own agent sends code to a model outside the region | The client's region promise breaks on their side | CLI and MCP results hold no code. Security pack states the boundary. MCP server in the client's environment for strict clients (EXL10) |
| Competitors add verification and labels | Differentiator 1 weakens | Keep the other four: independence, evidence pack, stale findings, fixed-price outcome. Publish precision numbers first |
| The model provider changes terms or region support | In-region promise at risk | Endpoint register with terms. Second provider. Client-environment option with an open model |
| Client code leaks through logs, tool results or support tickets | Loss of trust, legal exposure | L-G4 tests. No code in logs, CLI or MCP results. Retention job |
| Running client build scripts executes hostile code | Host compromise | L-G5 sandbox: no network, no secrets, throw-away container |
| DBOS is younger than Temporal | Fewer operators know it; fewer tools | The library is small and on Postgres. Workflows stay plain Python steps, so a later move stays possible |
| One founder delivers alone | Slow build | Small phases. Fast lane. Probe first |

## 19. Decisions log

| Date | Decision | By |
|---|---|---|
| 19 Nov 2026 | Employment check: risk accepted. Move forward. EXL0 records the acceptance in place of a contract check. Clean room (L-G7) stays | User |
| 19 Nov 2026 | Analyser server: a new permanent EU server at up to 15 US dollars per month is acceptable | User |
| 20 Nov 2026 | Workflow engine: DBOS Transact (MIT, on Postgres) replaces Temporal for all Exaktiv workflows. Update `CLAUDE.md` stack and the build plan | User |
| 20 Nov 2026 | Agent access: CLI with a skill file is the default entry point for coding agents; remote MCP server is the second option; five tools; token budget L-G12 | User |
| 20 Nov 2026 | BYOK is the default: client admins enter their own provider keys and choose a qualified route per model stage. Model cost is not part of the Exaktiv price. Managed models as an add-on | User |
| 20 Nov 2026 | Several tenants inside one client organisation, with full isolation (G6) | User |
| 20 Nov 2026 | Public self-serve sign-up deferred. The team sets up each organisation and engagement | User |
| 20 Nov 2026 | PRD changes approved: corrected positioning, tiered review with published precision, stale findings, scale design | User |
| 20 Nov 2026 | Earlier LangGraph analyser build: start clean. No earlier code enters the repository (EXL0 record) | User |
| 20 Nov 2026 | Model route for build and test: Claude through the Anthropic API, synthetic and public code only. Claude through OpenRouter EU for production, after all build phases are done. This replaces the Bedrock EU and Mistral EU proposal in section 8.5 until EXL5 or EXL14 confirms data terms and L-G14 | User |
| 21 Nov 2026 | OpenRouter EU terms agreed and signed. Retention and region details are read from the signed terms in EXL5 or EXL14 | User |
| 21 Nov 2026 | Region allowlist (EU region): tenant runs may call `eu.openrouter.ai` only; the gateway refuses any other host, with no fallback (G7). The OpenRouter region "Europe" covers the EU/EEA, the UK and Switzerland: the user accepts this scope. The security pack states it. `api.anthropic.com` is allowed for build and test only, on synthetic and public data (G8). EXL14 keeps the list in config | User |
| 21 Nov 2026 | L-G14 reading: "provider" means the upstream model vendor, not the gateway. OpenRouter is one shared sub-processor for S4 and S5: the user accepts the risk that one router outage or term change hits both. Enforcement: each request pins the vendor (`provider.only`), sets `allow_fallbacks: false` and `zdr: true`; the run records the vendor from each response and fails if the S5 vendor equals the S4 vendor | User |

## 20. Open questions

| Item | Blocks | Proposal |
|---|---|---|
| EU primary and cross-check model routes | EXL5, EXL14 | ✅ Route decided 20 Nov 2026, terms signed 21 Nov 2026, L-G14 reading decided 21 Nov 2026 (section 19). Still to do in EXL5 or EXL14: record the signed terms in the endpoint register and choose the S5 vendor |
| Default retention for client code after handover | EXL7-p2 | 30 days, set per contract |
| First client's languages, build tools and git host | EXL11, EXL13 | Ask on the discovery call. Java and Kotlin first |
| Do we show the probe output to a prospect before the demo gate? | EXL2 | Yes, privately, labelled as a prototype on public or synthetic code |
| Code viewer without monospace (brand rule) | EXL6 | Test readability of indentation in EXL6. If it fails, ask the user for a code-viewer exception |
| Graph rendering library for the system map and explorer | EXL7-p1 | Choose in the EXL7-p1 spec; licence check (G12) |
| Review service level in continuous mode | EXL13, contracts | Proposed: critical changed findings reviewed within 2 business days |
| Who reviews in continuous mode: Exaktiv or the client's engineers | EXL13, pricing | Offer both; price the retainer by who reviews |
| Billing unit for the analyser under G5 | EXK10, pricing | "Lines under analysis per month" for the platform fee |
| Key vault: encrypted Postgres columns or OpenBao | EXL14 | Choose in the EXL14 spec; licence check (G12) |
| ~~Region allowlist of provider endpoints per region~~ | EXL14 | ✅ Decided 21 Nov 2026: `eu.openrouter.ai` only for the EU region, scope Europe (EU/EEA, UK, Switzerland). Section 19 |
| Public demo (one public repository, one module) | Deferred | Revisit with public self-serve |

## Sources

- Industry COBOL and PL/I requirements pipeline, ACL 2026 Industry Track: https://aclanthology.org/2026.acl-industry.4.pdf
- Reversa framework (confirmed, inferred, gap labels): https://www.alphaxiv.org/abs/2605.18684
- Citation-grounded code comprehension and mechanical citation checks: https://arxiv.org/abs/2512.12117v1
- Codebase-Memory, tree-sitter knowledge graph via MCP: https://arxiv.org/abs/2603.27277
- scip-java (Apache 2.0, compiler plugin, build tool support): https://sourcegraph.github.io/scip-java/docs/getting-started.html
- AWS Transform custom codebase analysis, general availability (Frankfurt): https://aws.amazon.com/about-aws/whats-new/2026/03/transform-custom-new-codebase-analysis
- AWS Transform and Kiro, spec-driven mainframe modernisation with source-line traceability: https://aws.amazon.com/blogs/migration-and-modernization/from-mainframes-to-microservices-specification-driven-mainframe-modernization-with-ai-agents/
- Kiro for modernisation (vFunction): https://vfunction.com/blog/kiro-for-modernization/
- Devin and DeepWiki at scale: https://cognition.com/blog/devin-annual-performance-review-2025
- Cognition and AWS strategic collaboration: https://press.aboutamazon.com/aws/2026/9/cognition-and-aws-sign-multi-year-strategic-collaboration-agreement
- DeepWiki guide (line-level citations): https://codersera.com/blog/deepwiki-complete-guide-2026/amp/
- IBM Bob Premium Package for Java Modernization: https://www.ibm.com/new/announcements/announcing-ibm-bob-premium-package-for-java-modernization
- MCP client compatibility (Claude Code, Codex CLI, Cursor, VS Code): https://zuplo.com/learn/mcp/compatibility
- MCP vs CLI vs skills, context cost: https://openrouter.ai/blog/insights/mcp-vs-cli-vs-skills
- MCP vs CLI token cost after lazy loading: https://www.checklyhq.com/blog/mcp-vs-cli-token-efficiency/
- MCP vs CLI, inner and outer loop: https://firecrawl.dev/blog/mcp-vs-cli
- Tool search and deferred loading (Anthropic): https://www.anthropic.com/engineering/advanced-tool-use
- DBOS Transact (MIT, durable workflows on Postgres): https://github.com/dbos-inc/dbos-transact-py
- Temporal self-hosted licence and costs: https://apis.io/plans/temporal-io/temporal-io-plans-pricing/
- Bedrock inference options and data residency: https://docs.aws.amazon.com/bedrock/latest/userguide/models-region-compatibility.html
- Mistral regional inference and zero data retention: https://mistral.ai/cloud/inference/
- Apache 2.0 open coding models: https://www.morphllm.com/qwen3-coder and https://community.groq.com/t/new-model-family-devstral-2/827
- cdxgen (CycloneDX generator): https://github.com/cdxgen/cdxgen
- Characterisation testing: https://en.wikipedia.org/wiki/Characterization_test
- Prospect job advert (Kotlin or Java, Spring, Hibernate, SQL): https://jobleads.com/de/job/e13e3a736351cbfaf9d5e4f80f9083d0e
