# PRD-00 — Exaktiv Core Engine

Version 1.0 · 4 November 2026 · Status: draft for the build-phase kit · Written in ASD-STE100

## 1. Summary

Exaktiv Core is the shared engine for all Exaktiv products. It takes messy inputs (scanned PDFs, phone photos, handwriting, datasheets, spreadsheets). It extracts structured values. It gives each value a source link and a confidence score. It sends low-confidence values to a human reviewer. It records each human correction and uses the corrections to improve the models. It counts only accepted values for billing.

The engine is not a general AI platform. It serves two products in v1: Exaktiv Claims (PRD-A) and Exaktiv Product Data (PRD-B1). Each product supplies its own document types, schemas, validation rules and reviewer screens.

## 2. Problem

Frontier models are cheap and good on clean inputs. They are weak on hard inputs:

- Handwriting: the best model reads handwritten fields at about 75% accuracy (IDP leaderboard, 2026).
- Hard attributes: a cheaper model at Instacart lost 60% accuracy on hard attributes.
- Domain value lists: an output must match an allowed list (for example, an ETIM value code or an ICD-10 code format), and frontier models do not check this.

Buyers in regulated or standardised work also need proof: where each value came from, who approved it, and which model version made it. Generic tools do not give this per value.

## 3. Goals and non-goals

### Goals (v1)

1. Extract values from mixed inputs with a source link per value.
2. Route each task to the right model: a frontier model in the tenant's region by default, and a fine-tuned open model where accuracy or residency needs it.
3. Give a calibrated confidence per value. Send values below the threshold to review.
4. Give a reviewer queue that a product can extend with its own screens.
5. Store every correction as labelled data for the tenant.
6. Run an evaluation harness that compares the pipeline with a frontier baseline on the same inputs.
7. Produce an evidence log (Exaktiv Proof) per job.
8. Count accepted units for billing.

### Non-goals (v1)

- No general chat or agent product.
- No automatic final decisions (a claim decision, a data-pool publish) without a human approval step.
- No model training on one tenant's data for another tenant.
- No self-serve sign-up. Tenants are set up by the team.
- No mobile app.
- No Kafka in v1. Temporal handles the workflows. Add Kafka when event volume needs it.

## 4. Users

| User | Need |
|---|---|
| Reviewer (claims processor, product-data editor) | See low-confidence values next to the source page. Approve or correct fast. |
| Team lead at the customer | See throughput, accuracy and the review backlog. |
| Customer security or compliance officer | See where data lives, who accessed it, and the audit trail. |
| Exaktiv engineer | Add a document type, a schema or a model without changes to the core. |

## 5. Functional requirements

### 5.1 Ingestion

- FR-ING-1: Accept PDF (scanned and digital), JPEG, PNG, HEIC, TIFF, CSV, XLSX and BMEcat XML.
- FR-ING-2: Store each input file unchanged in object storage, with a SHA-256 hash, the tenant ID, the upload time and the uploader.
- FR-ING-3: Split each file into pages. Make a normalised image of each page (deskew, rotate, contrast). Keep the original.
- FR-ING-4: Group files into a **job** (a claim file, or a batch of SKUs).
- FR-ING-5: Reject files above a size limit per tenant (default 50 MB per file). Tell the user why.

### 5.2 Classification and extraction

- FR-EXT-1: Classify each page into a document type that the product defines (for example "discharge summary" or "product datasheet").
- FR-EXT-2: Extract the fields of the product schema for each document type.
- FR-EXT-3: Each extracted value carries: field ID, value, unit (if any), source file ID, page number, bounding box or text span, model ID, model version, prompt or adapter version, raw model output, confidence, timestamp.
- FR-EXT-4: If the model gives a value with no source location, the engine drops the value and marks the field "not found". It does not guess.
- FR-EXT-5: Support OCR text plus page image as model input. The product decides which one a task uses.

### 5.3 Model router

- FR-RTR-1: Each tenant has a region (India or EU in v1). The router uses only model endpoints in that region.
- FR-RTR-2: Each task type has a route: frontier model, fine-tuned open model, or both (for comparison during evaluation).
- FR-RTR-3: Routes live in configuration with a version. A route change is logged.
- FR-RTR-4: All model calls go through one gateway that records cost, latency, model and token counts per call.
- FR-RTR-5: If a model endpoint fails, the router retries once, then marks the task "failed" and sends it to review. It does not fall back to a model outside the region.

### 5.4 Validation

- FR-VAL-1: Each value passes schema validation (type, format, required).
- FR-VAL-2: Each value passes the product's domain validation (for example: an allowed ETIM value code, a unit from the allowed list, a date in a valid range, an amount that sums correctly).
- FR-VAL-3: A value that fails validation goes to review with the reason. It is never stored as accepted.
- FR-VAL-4: Validation rules live in code or versioned configuration, not in prompts.

### 5.5 Confidence and abstention

- FR-CNF-1: Each value gets a confidence score from model signals plus validation results.
- FR-CNF-2: Calibrate the score per tenant and per field on reviewed data. Store the calibration version.
- FR-CNF-3: Each field has an auto-accept threshold. Below the threshold, the value goes to review.
- FR-CNF-4: A field can be set to "always review" (for example, a claimed amount above a limit).
- FR-CNF-5: Until a field has 200 or more reviewed values, every value of that field goes to review.

### 5.6 Review queue

- FR-REV-1: A queue of review tasks per tenant, sorted by job priority and age.
- FR-REV-2: Each task shows the value, the source page with the area marked, the reason for review, and the model's alternatives if any.
- FR-REV-3: The reviewer can accept, correct or mark "not present". Each action records user, time and old and new value.
- FR-REV-4: Keyboard-first operation. Target: a median of 8 seconds or less per simple field.
- FR-REV-5: A job is "complete" only when all its required fields are accepted or marked "not present".
- FR-REV-6: The product can add its own screens (a case view, a SKU view) on top of the core queue.

### 5.7 Corrections and learning

- FR-LRN-1: Store each accepted value and each correction as a labelled example for the tenant.
- FR-LRN-2: Build a training set per tenant and per task from labelled examples, with a frozen evaluation split.
- FR-LRN-3: Train a private adapter (LoRA) per tenant and task on an open base model, when the tenant has enough examples (product sets the number).
- FR-LRN-4: A cross-tenant base model may use labelled data only from tenants that gave written consent, and only after anonymisation.

### 5.8 Evaluation harness

- FR-EVL-1: Run the pipeline and a frontier baseline on the same frozen evaluation set.
- FR-EVL-2: Report per field: precision, recall, exact-match accuracy, abstention rate, cost per unit, latency.
- FR-EVL-3: Report hard-subset results separately (for example, handwritten fields, or features with value lists).
- FR-EVL-4: Export the report as HTML and JSON for sales use.

### 5.9 Model registry and release gate

- FR-REG-1: Register each model, adapter, prompt and route with a version.
- FR-REG-2: A new version is promoted only if it passes the regression gate: no field drops more than 1 point of accuracy on the frozen set, and the overall accuracy does not drop.
- FR-REG-3: Rollback to the previous version in one step.

### 5.10 Evidence log (Exaktiv Proof)

- FR-PRF-1: For each job, store: input hashes, all model calls (model, version, route, time), all values with sources, all review actions, validation results and the final output.
- FR-PRF-2: Export an evidence pack per job (PDF and JSON). It lists each value with its source page image crop.
- FR-PRF-3: The evidence log is append-only. Edits make new entries.
- FR-PRF-4: The product maps the evidence to its regulations (for example IRDAI, DPDP, FREE-AI, EU AI Act).

### 5.11 Metering

- FR-MTR-1: Count accepted units per tenant per month (a claim file, or an accepted SKU). The product defines the unit.
- FR-MTR-2: A unit counts once. Re-processing does not count again.
- FR-MTR-3: Export monthly usage for invoicing.

### 5.12 API

- FR-API-1: REST API to create a job, upload files, get job status, get results and get the evidence pack.
- FR-API-2: Webhook when a job is complete.
- FR-API-3: API keys per tenant, with scopes.

## 6. Core guardrails (non-negotiable)

Each guardrail must be checkable by a reviewer who was not in the design discussion.

| ID | Guardrail | How to check |
|---|---|---|
| G1 | **No value without a source.** Every stored value carries file ID, page, location, model ID and version. A value without these is dropped and the field is marked "not found". | A test inserts a model output with no location and confirms that nothing is stored. |
| G2 | **Abstain, do not guess.** Below the threshold or after a validation failure, the value goes to review. The engine never fills a default or an estimate. | A test with a low-confidence value confirms a review task and no accepted value. |
| G3 | **Rules in code, not in prompts.** Thresholds, validation rules, business rules and value lists live in code or versioned configuration. Prompts only ask for extraction. | Code review: no threshold or business rule appears in a prompt file. |
| G4 | **Validate before storage.** Every model output passes schema and domain validation before it is stored as a candidate. | A test with an invalid unit or code confirms rejection with a reason. |
| G5 | **Bill only accepted units.** Billing counts units that are accepted by a human or by auto-accept with a calibrated threshold. | A test confirms that a job with open review tasks counts zero units. |
| G6 | **Tenant isolation.** Data, adapters, corrections and evaluation sets never cross tenants. Cross-tenant training needs written consent and anonymisation. | Integration test: a tenant A key cannot read tenant B data. Training jobs log their tenant sources. |
| G7 | **Region stays fixed.** A tenant's files, values and model calls stay in the tenant's region. No fallback to a model outside the region. No plaintext access from outside the region for EU tenants. | Router test with a region mismatch confirms failure, not fallback. Access logs show no out-of-region reads. |
| G8 | **No real customer data in development.** Development and tests use synthetic or public data only. No data from any past employer of the founders. | Test fixtures carry a source note. A pre-commit check blocks files from customer buckets. |
| G9 | **Secrets in the secret manager only.** No secret in git, in a prompt or in a log. | Secret scanning in CI. |
| G10 | **Release gate.** No model, adapter, prompt or route change goes live without the regression gate (FR-REG-2). | The registry refuses promotion without a passed gate record. |
| G11 | **Personal data minimisation.** Logs and metrics never contain personal data in plaintext. Mask names, IDs and phone numbers in logs. | Log-scan test with synthetic personal data. |
| G12 | **Licences.** Base models: Apache 2.0 or MIT only. Datasets: licence recorded before use. No model with a revenue cap or a non-production licence. | A licence file lists each model and dataset with its licence. |
| G13 | **Human approval before any external action.** The engine never submits, publishes or decides on behalf of the customer without an approval step. | No API call to an external system exists without an approval record. |

## 7. Source of record

| Data | Authoritative source | Cross-check |
|---|---|---|
| Input file content | Object storage original, by SHA-256 | Hash checked on every read |
| Extracted value (candidate) | Engine value store, with model metadata | Validation rules (FR-VAL) |
| Accepted value | Review action record, or auto-accept record with calibration version | Evidence log |
| Validation rules and value lists | Versioned configuration in the repository (product-specific) | Unit tests per rule |
| Model and route versions | Model registry | Gate record |
| Usage for billing | Metering table (accepted units only) | Reconcile with job completion records every month |
| Tenant region | Tenant configuration | Router check on every call |

## 8. Stack and constraints (Proposed)

| Item | Proposal | Reason |
|---|---|---|
| Services and workflows | Kotlin, Spring Boot 3, Temporal | Pratima's main skills. Temporal makes long, multi-step jobs reliable. |
| Model service | Python 3.12, FastAPI | Ved's main skills. Model and ML libraries are in Python. |
| Model gateway | LiteLLM (pin the image by digest; do not use a floating tag) | One place for cost, latency and model logs. |
| Fine-tuning | PEFT/LoRA on an Apache 2.0 base model (for example Qwen family, or other Apache/MIT models) | Cheap adapters per tenant. |
| OCR | A local OCR engine plus the model's own vision input | Handwriting needs both. |
| Datastore | PostgreSQL 16 | Values, reviews, registry, metering. |
| Object storage | S3-compatible, per region | Original files and page images. |
| Reviewer UI | React + TypeScript, Personal Design System tokens (teal accent, Inter + Lora + JetBrains Mono, dark default with a light mirror) | One UI codebase for both products. |
| Cloud | AWS: Mumbai (ap-south-1) for India tenants, Frankfurt (eu-central-1) for EU tenants | Data residency per region. |
| Secrets | AWS Secrets Manager, injected at runtime | G9. |
| CI | GitHub Actions: lint, type check, unit tests, integration tests, secret scan, licence check | |
| Commands | To confirm in the build-phase interview: Gradle for Kotlin (`./gradlew check`), `uv` + `pytest` + `ruff` + `mypy` for Python, `pnpm` + `vitest` + `eslint` for the UI | |

Scale targets for v1:

- Claims: up to 2,000 claim files per day per tenant, 10–40 pages per file.
- Product Data: up to 50,000 SKUs per batch.
- One claim file processed (before review) in under 2 minutes.
- Review screen opens in under 1 second.

## 9. Metrics

| Metric | Target for the first pilot |
|---|---|
| Field accuracy after review | 99% or more |
| Field accuracy at auto-accept | Equal to or better than the calibrated target per field (set per product) |
| Gain over the frontier baseline on the hard subset | Product-specific (Claims: 5 points or more on handwritten fields; Product Data: 95% or more feature accuracy) |
| Median reviewer time per simple field | 8 seconds or less |
| Share of values with a source link | 100% |

## 10. Proposed core phases

| Phase | Objective | Gate |
|---|---|---|
| EXK0 | Foundation: repositories, CI, secrets, both regions, one passing smoke test | Nothing else starts before EXK0 passes |
| EXK1 | Ingestion and storage: jobs, files, hashes, page split, normalised images | Gates all extraction |
| EXK2 | Model gateway and router with region check | G7 test must pass before any model call reaches real data |
| EXK3 | Extraction contract: value record with source metadata, drop values without a source | G1 test |
| EXK4 | Validation layer: schema and domain rules as versioned configuration | G3, G4 tests; gates storage of candidates |
| EXK5 | Confidence, thresholds and abstention | G2 test; gates any auto-accept |
| EXK6 | Review queue backend and core reviewer UI (EXK6-ui) | A job can reach "complete" only through EXK6 |
| EXK7 | Evaluation harness and baseline report | Gates every sales demo |
| EXK8 | Evidence log and evidence pack export (Exaktiv Proof) | Gates the first pilot on real data |
| EXK9 | Corrections store, training sets, LoRA adapter pipeline, model registry and regression gate | G10; gates any fine-tuned model in production |
| EXK10 | Metering and usage export | G5; gates the first invoice |

## 11. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Frontier models close the gap on hard inputs | The accuracy claim weakens | The moat is the labelled correction data and the evidence log, not one model. Re-run the baseline every month. |
| The router is set up wrong and data leaves the region | Legal and trust damage | G7 test in CI. Region check on every call. No fallback. |
| Model gateway supply-chain compromise | Data leak | Pin images by digest. Review each upgrade. Keep the gateway inside the private network. |
| Reviewers do not trust the confidence score | Everything goes to review, so no labour saving | Calibrate per field. Show the source next to each value. Track reviewer overrides. |
| Two founders at 20 hours per week each | Slow build | Keep each phase to one small PR. Build the core once for both products. |
| Licence problem with a base model | Forced model change | G12. Apache/MIT only. |

## 12. Open questions

1. Which open base model and size give the best accuracy per GPU cost for handwriting and for datasheet tables? Decide after the EXK7 baseline.
2. Self-hosted GPU or a managed inference endpoint in each region?
3. Do EU tenants need EU-only engineering access from day 1, or only for personal data? (Product Data has little personal data.)
4. ISO 27001 start date (proposed: month 4).
