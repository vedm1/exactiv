# Exaktiv — PRD set

Version 1.0 · 4 November 2026 · Written in ASD-STE100 (Simplified Technical English)

## What Exaktiv is

Exaktiv extracts data from messy inputs (scans, photos, handwriting, mixed languages, datasheets). It gives each value a source link, a confidence score and a human review path. It sells accepted results, priced per accepted unit, against the cost of human work.

One engine serves two products:

| Product | First market | Buyer | Unit of price |
|---|---|---|---|
| **Exaktiv Claims** (Option A) | India | Mid-size health insurers and TPAs | Per claim file |
| **Exaktiv Product Data** (Option B1) | Netherlands, Belgium, then DACH | Long-tail manufacturers, importers and agents that publish ETIM data | Per accepted SKU, plus yearly upkeep |
| **Exaktiv Proof** | All | Feature of both products | Included |
| **Exaktiv Underwrite** | India, later | Life insurers | Per case (after Claims v1) |

## Files

| File | Content |
|---|---|
| `PRD-00-exaktiv-core.md` | The shared engine: architecture, guardrails, source-of-record table, stack, core phases |
| `PRD-A-exaktiv-claims.md` | Exaktiv Claims: health-claim file extraction for Indian TPAs and insurers |
| `PRD-B1-exaktiv-product-data.md` | Exaktiv Product Data: ETIM feature fill that passes data-pool checks |
| `PRD-W-exaktiv-website.md` | The Exaktiv capability website: pages, claims register, contact form, EU security and privacy, launch gate (build phases EXD5 and EXW) |

Read the core PRD first. The product PRDs refer to it and do not repeat it.

## How to use these files with the build-phase kit

1. Make a new, empty project folder (for example `exaktiv`).
2. Copy these files into a `docs/prd/` folder in that project.
3. Open the project in a new session and say: "Scaffold this PRD. Read docs/prd/README.md and the three PRD files."
4. The kit asks interview questions. Most answers are already in the PRDs:
   - Round 1 (product shape): section 1 and 3 of each PRD.
   - Round 2 (stack and constraints): core PRD section 8.
   - Round 3 (guardrails): core PRD section 6 and 7, plus the product-specific guardrails in each product PRD.
   - Round 4 (risks): section "Risks" in each PRD.
5. The kit then proposes a phase list. Section 10 of the core PRD and the "Proposed phases" section of each product PRD give a starting list. Approve or change it there.

## Proposed shortcode and build order

- Project shortcode: **EXK** (core), with prefixes **EXC** (Claims) and **EXP** (Product Data). If the kit allows only one shortcode, use EXK for all rows and keep the product prefix in the phase title.
- Build order:
  1. EXK0–EXK7: foundation and the shared engine (about 3–4 weeks at 2 × 20 hours per week).
  2. EXC1–EXC7: the Claims PoC on synthetic and public documents (about 5 weeks).
  3. EXP1–EXP6: the Product Data test build (about 3 weeks). It can run in parallel with step 2 after EXK5.
  4. EXK8–EXK10: corrections, fine-tuning and metering, before the first paid pilot.

## Decisions to confirm in the build-phase interview

These are proposals. The PRDs mark each one as "Proposed".

1. Stack split: Kotlin (Spring Boot) for services and workflows, Python (FastAPI) for the model service.
2. Workflow engine: Temporal. Kafka is not in v1; add it when event volume needs it.
3. Cloud and regions: AWS Mumbai (ap-south-1) for Claims; AWS Frankfurt (eu-central-1) for Product Data.
4. Default frontier model per region, and the open base model for fine-tuning (Apache 2.0 or MIT licence only).
5. Reviewer UI framework: React + TypeScript, with the Exaktiv brand package (`brand/`). The Personal Design System is retired (18 Nov 2026).

## Source documents

These PRDs come from the research and challenge rounds of 2–3 November 2026 (report "Competing with iris8"). All market numbers are desk estimates. Buyer calls and paid pilots must confirm them.
